"""Exact approved SpB profile; no GPU/server or large tensor reads."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'experiments/records/20260921-sc2-policy-credit-v1'))
import spb_l8random197 as m
import spb_l8random_plan as p
import spb_l8random_eval197 as adapter
import qwen_l8random197 as q
import qwen_l8random_eval197 as e
import qwen_l8random_retention as r
from test_qwen_l7same_fresh197 import QwenNativeContractTests
from agent_system.sc2_policy_resume import sha256,verify_contract


class SpbNativeTests(QwenNativeContractTests):
    def test_spb_l8_native_rejects_other_model_difficulty_and_legacy(self):
        c=self.native_qwen();c['version']='accepted-spb-l8-random-full-state-prefix-v1'
        path=self.parent/'deployment.json';cfg=json.loads(path.read_text())
        cfg.update(model_kind='spb',difficulty='CheatVision',seed_protocol='independent_uniform101',seed_group_mode='mixed_seed_ablation')
        path.write_text(json.dumps(cfg));c['files']={n:sha256(self.parent/n) for n in c['files']}
        verify_contract(c)
        for key,value in [('driver_rng_unavailable_accepted',True),('target_step',192),
                          ('version','accepted-spb-random-full-state-prefix-v1')]:
            bad=copy.deepcopy(c);bad[key]=value
            with self.assertRaises(ValueError): verify_contract(bad)
        for key,value in [('model_kind','qwen'),('difficulty','VeryHard'),('seed_protocol','same_uniform101')]:
            badcfg=copy.deepcopy(cfg);badcfg[key]=value;path.write_text(json.dumps(badcfg))
            bad=copy.deepcopy(c);bad['files']={n:sha256(self.parent/n) for n in c['files']}
            with self.assertRaises(ValueError): verify_contract(bad)


class SpbProfileTests(unittest.TestCase):
    def setUp(self):
        for module in (q,e,e.common,q.h,q.fresh,q.fresh.queue_impl,q.f,q.a,q.f.previous,q.storage,r):
            guard=patch.dict(vars(module),{});guard.start();self.addCleanup(guard.stop)
        m.configure()

    def cfg(self,index=0):
        return dict(runtime_sha='test',controller_sha='test',controller_source='/new/code',
            environment={'LONG_DEPENDENCY_PATH':'/deps'},model_kind='spb',model_mount='/assets/spb',
            difficulty='CheatVision',seed_protocol=q.PROTOCOL,seed_group_mode=q.GROUP,
            training_seeds=[q.ablation_seeds(q.PROTOCOL,0,i,1,8) for i in range(96)],
            run_prefix='new-spb',worker_hook='l7_followup_hook.install',
            stages=['pre','train2','post'] if index==0 else ['train96','eval96'],
            host=dict(model='/original-spb',venv='/venv',sc2='/sc2',image='image'))

    def test_exact_budget_roots_and_shared_clock_limits(self):
        x=m.accounts(123)
        self.assertEqual([a['limit']//m.a.GIB for a in x],[320,32,8,352])
        self.assertEqual(x[-1]['roots'],[p.OLD_ROOT,p.OLD_EVAL_ROOT,p.OLD_SOURCE_PARENT,p.ROOT,p.EVAL_ROOT,p.SOURCE_PARENT])
        self.assertEqual(x[0]['roots'],[p.OLD_ROOT,p.OLD_SOURCE_PARENT,p.ROOT,p.SOURCE_PARENT])
        self.assertEqual(x[1]['roots'],list(p.EVAL_STORAGE_ROOTS))
        self.assertIs(q.h.sample,m.storage_batch197.sample)
        self.assertTrue(all(a['deadline']==123 for a in x))
        self.assertEqual((q.TRAIN_SECONDS,q.SUITE_SECONDS,q.NEW_GAMES,q.TRAIN_FREE_GIB),(86400,108000,1048,416))
        self.assertEqual((q.TRAIN_GPU_HOURS,q.SUITE_GPU_HOURS),(192,240))

    def test_training_uses_original_spb_then_only_own_native_cp2(self):
        for index,stage in ((0,'pre'),(0,'train2'),(0,'post'),(1,'train96'),(1,'eval96')):
            with patch.object(m.a,'read',return_value=self.cfg(index)):
                cfg=m.f.select(index);args,env,out=q.invocation(cfg,stage,True)
            self.assertIn('run_seed_group_arm.sh',args[1]);self.assertEqual(env['SC2_DIFFICULTY'],'CheatVision')
            self.assertEqual(args.count("+ray_init.runtime_env.env_vars.SC2_RESET_CONCURRENCY='1'"),1)
            self.assertIn('algorithm.sc2_policy_credit.seed_group_mode=mixed_seed_ablation',args)
            if stage in ('pre','train2'): self.assertFalse(any(v.startswith('trainer.resume_from_path=') for v in args))
            if stage=='train96':
                self.assertIn('trainer.save_freq=32',args)
                self.assertIn('trainer.resume_from_path='+str(p.SELECTION_CHECKPOINTS['cp2']),args)
                self.assertIn('+trainer.sc2_import_legacy_final=False',args)

    def test_cpu_mounts_metadata_gpu_original_readonly_and_correct_entry(self):
        with patch.object(m.a,'read',return_value=self.cfg()):
            cpu=q.docker('cpu',0);gpu=q.docker('stage',0,'pre')
        self.assertNotIn('--gpus',cpu)
        self.assertIn(str(m.a.HERE/'spb_l8random197.py'),gpu)
        self.assertIn('/original-spb:/assets/spb:ro',gpu)
        self.assertIn(str(q.f.previous.SPB_METADATA)+':/assets/spb:ro',cpu)
        self.assertIn(str(m.BASE_CONFIG)+':'+str(m.BASE_CONFIG)+':ro',cpu)
        self.assertEqual(gpu[-3:],['stage','0','pre'])
        self.assertFalse(any('qwen-l8random96-197-20260928-r3:' in v for v in gpu))

    def test_two_primary_arms_four_selection_arms_and_no_future_cp_mounts(self):
        p.validate();self.assertEqual(len(p.STAGES),16);self.assertEqual(len(p.SELECTION_STAGES),16)
        for selection in (False,True):
            cfg=self.cfg();cfg['worker_hook']='spb_l8random_eval_hook.install'
            with patch.object(m.a,'read',return_value=cfg):
                e.configure(selection);self.assertEqual(len(e.HOOK_STAGES),4 if selection else 2)
                for stage in e.STAGES:
                    args,env,out=e.common.invocation(cfg,stage,True);s=p.stage_spec(stage)
                    self.assertIn('trainer.val_only=True',args)
                    self.assertIn('trainer.save_freq=-1',args)
                    if s['checkpoint']: self.assertIn('trainer.resume_from_path='+str(s['checkpoint']),args)
                    self.assertIn('+ray_init.runtime_env.worker_process_setup_hook=spb_l8random_eval_hook.install',args)
                cpu=e.docker('cpu')
            self.assertNotIn('--gpus',cpu)
            self.assertFalse(any(v.endswith('/global_step_96:ro') for v in cpu))
        self.assertEqual(e.SELECTION_SECONDS,21600)

    def test_retention_cannot_target_old_qwen_or_l7_and_ties_keep_cp2(self):
        self.assertEqual(r.ROOT,p.ROOT)
        self.assertTrue(all(cp.is_relative_to(p.ROOT) for cp in r.SELECTION_CHECKPOINTS.values()))
        self.assertEqual(r.retained_steps(2),[2,64,96])
        self.assertEqual(r.retained_steps(32),[2,32,64,96])
        with self.assertRaises(ValueError): r.inventory(m.PRIOR/'qwen-random/long/runs/train96/checkpoints/global_step_96')

    def test_failed_predecessor_and_existing_new_root_block_dispatch(self):
        with patch.object(q.receipts,'small',return_value={'phase':'failed'}):
            with self.assertRaises(RuntimeError):m.predecessor_complete()
        with tempfile.TemporaryDirectory() as tmp,patch.object(m,'ROOT',Path(tmp)):
            with self.assertRaisesRegex(RuntimeError,'Fresh exact'):m.prepare()

    def test_profile_queue_clock_and_failure_does_not_start_successors(self):
        for failure in (False,True):
            with self.subTest(failure=failure),tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp);train=root/'train';primary=root/'eval';train.mkdir();primary.mkdir()
                # Use the installed queue, but isolate all files and expensive operations.
                with patch.object(q,'configure'),patch.object(q,'ROOT',train),patch.object(q,'EVAL_ROOT',primary),\
                     patch.object(q,'SOURCE_PARENT',root/'source'),patch.object(q,'check_cpu'),\
                     patch.object(q,'predecessor_complete',return_value=True),patch.object(q,'admit'),\
                     patch.object(q,'contract_for',return_value={}),patch.object(q,'docker',return_value=['noop']),\
                     patch.object(q.sp,'run'),patch.object(q.h,'sample'),\
                     patch.object(q.fresh.queue_impl.host,'writers_clear'),\
                     patch.object(e,'run_selection') as selection,patch.object(r,'prune') as prune,\
                     patch.object(e,'run_after_training') as primary_run:
                    for i,part in enumerate(p.PARTS):
                        owner=train/part;owner.mkdir(parents=True)
                        q.a.save(owner/'deployment.json',self.cfg(i),lock_root=train)
                        q.a.save(owner/'parent-readiness.json',{'actual_parent_verified':True},lock_root=train)
                    def select(i):
                        q.a.ROOT=train/p.PARTS[i]
                        return self.cfg(i)
                    def run(stages,*args,**kwargs):
                        if failure: raise RuntimeError('bounded stage failure')
                        return dict(phase='completed',exit_code=0,completed=stages)
                    with patch.object(q.f,'select',side_effect=select),patch.object(q.h,'run_stages',side_effect=run):
                        if failure:
                            with self.assertRaisesRegex(RuntimeError,'bounded'):q.queue()
                            selection.assert_not_called();prune.assert_not_called();primary_run.assert_not_called()
                        else:
                            q.queue();selection.assert_called_once();prune.assert_called_once();primary_run.assert_called_once()
                    d=q.a.read(train/'dispatch.json')
                    self.assertEqual(d['deadline']-d['start'],86400)
                    self.assertEqual(d['suite_deadline']-d['start'],108000)
                    self.assertEqual(d['suite_gpu_hours'],240)
                    self.assertEqual(q.a.read(train/'queue-state.json')['new_games'],1048)
                    with self.assertRaisesRegex(RuntimeError,'Already queued'):q.queue()


if __name__=='__main__':unittest.main()
