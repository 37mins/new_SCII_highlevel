"""L9 routing/budget/native contracts; synthetic files, no server/GPU."""
import copy
from contextlib import ExitStack
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'experiments/records/20260921-sc2-policy-credit-v1'))
import spb_l9random197 as m
import spb_l9random_plan as p
import qwen_l8random197 as q
import qwen_l8random_eval197 as e
import qwen_l8random_retention as r
from test_qwen_l7same_fresh197 import QwenNativeContractTests
from agent_system.sc2_policy_resume import sha256,verify_contract


class L9NativeTests(QwenNativeContractTests):
    def test_l9_native_contract_rejects_l8_transfer_and_legacy(self):
        c=self.native_qwen();c['version']='accepted-spb-l9-random-full-state-prefix-v1'
        path=self.parent/'deployment.json';cfg=json.loads(path.read_text())
        cfg.update(model_kind='spb',difficulty='CheatMoney',seed_protocol=q.PROTOCOL,seed_group_mode=q.GROUP)
        path.write_text(json.dumps(cfg));c['files']={n:sha256(self.parent/n) for n in c['files']}
        verify_contract(c)
        for key,value in [('driver_rng_unavailable_accepted',True),('target_step',192),
                ('version','accepted-spb-l8-random-full-state-prefix-v1')]:
            bad=copy.deepcopy(c);bad[key]=value
            with self.assertRaises(ValueError):verify_contract(bad)
        for key,value in [('model_kind','qwen'),('difficulty','CheatVision'),('seed_protocol','same_uniform101')]:
            badcfg=dict(cfg);badcfg[key]=value;path.write_text(json.dumps(badcfg))
            bad=copy.deepcopy(c);bad['files']={n:sha256(self.parent/n) for n in c['files']}
            with self.assertRaises(ValueError):verify_contract(bad)


class L9ProfileTests(unittest.TestCase):
    def setUp(self):
        for module in (q,e,e.common,q.h,q.fresh,q.fresh.queue_impl,q.f,q.a,q.f.previous,q.storage,r):
            guard=patch.dict(vars(module),{});guard.start();self.addCleanup(guard.stop)
        m.configure()

    def cfg(self,index=0):
        return dict(runtime_sha='test',controller_sha='test',controller_source='/new/code',
            environment={'LONG_DEPENDENCY_PATH':'/deps'},model_kind='spb',model_mount='/assets/spb',
            difficulty='CheatMoney',seed_protocol=q.PROTOCOL,seed_group_mode=q.GROUP,
            training_seeds=[q.ablation_seeds(q.PROTOCOL,0,i,1,8) for i in range(96)],
            run_prefix='new-l9',worker_hook='l7_followup_hook.install',terminal_handoff='terminal-drain-v1',
            stages=['pre','train2','post'] if index==0 else ['train96','eval96'],
            host=dict(model='/original-spb',venv='/venv',sc2='/sc2',image='image'))

    def test_budget_counts_only_three_new_whole_roots(self):
        x=m.accounts(123)
        self.assertEqual([a['limit']//m.a.GIB for a in x],[320,32,8,352])
        self.assertEqual(x[-1]['roots'],[p.ROOT,p.EVAL_ROOT,p.SOURCE_PARENT])
        self.assertTrue(all(a['deadline']==123 for a in x))
        self.assertEqual((q.TRAIN_SECONDS,q.SUITE_SECONDS,q.NEW_GAMES,q.TRAIN_FREE_GIB),(86400,108000,1048,416))
        self.assertEqual((q.TRAIN_GPU_HOURS,q.SUITE_GPU_HOURS),(192,240))
        self.assertFalse(q.PRUNE_AFTER_SELECTION)

    def test_five_train_launchers_l9_original_then_own_native_cp2(self):
        for index,stage in ((0,'pre'),(0,'train2'),(0,'post'),(1,'train96'),(1,'eval96')):
            with patch.object(m.a,'read',return_value=self.cfg(index)):
                cfg=m.f.select(index);args,env,out=q.invocation(cfg,stage,True)
            self.assertEqual(env['SC2_DIFFICULTY'],'CheatMoney')
            self.assertEqual(env['SC2_FINALIZATION_MODE'],'terminal-drain-v1')
            self.assertIn('+trainer.sc2_terminal_handoff_lock_root='+str(p.ROOT),args)
            self.assertIn('algorithm.sc2_policy_credit.seed_group_mode=mixed_seed_ablation',args)
            if stage in ('pre','train2'):self.assertFalse(any(v.startswith('trainer.resume_from_path=') for v in args))
            if stage=='train96':
                self.assertIn('trainer.save_freq=32',args)
                self.assertIn('trainer.resume_from_path='+str(p.SELECTION_CHECKPOINTS['cp2']),args)
                self.assertIn('+trainer.sc2_import_legacy_final=False',args)
        with self.assertRaises(ValueError):q.invocation(dict(self.cfg(),difficulty='CheatVision'),'pre')

    def test_cpu_no_gpu_readonly_original_and_exact_entry(self):
        with patch.object(m.a,'read',return_value=self.cfg()):
            cpu=q.docker('cpu',0);gpu=q.docker('stage',0,'pre')
        self.assertNotIn('--gpus',cpu)
        self.assertIn(str(m.a.HERE/'spb_l9random197.py'),gpu)
        self.assertIn('/original-spb:/assets/spb:ro',gpu)
        self.assertIn(str(q.f.previous.SPB_METADATA)+':/assets/spb:ro',cpu)
        self.assertIn(str(m.BASE_CONFIG)+':'+str(m.BASE_CONFIG)+':ro',cpu)

    def test_all32_evaluation_launchers_l9_terminal_and_disjoint_seeds(self):
        p.validate();self.assertEqual((len(p.STAGES),len(p.SELECTION_STAGES)),(16,16))
        self.assertFalse(set(p.SEEDS)&set(p.SELECTION_SEEDS))
        self.assertFalse((set(p.SEEDS)|set(p.SELECTION_SEEDS))&set(range(101)))
        for selection in (False,True):
            cfg=self.cfg();cfg['worker_hook']='spb_l9random_eval_hook.install'
            with patch.object(m.a,'read',return_value=cfg):
                e.configure(selection)
                for stage in e.STAGES:
                    args,env,out=e.common.invocation(cfg,stage,True);s=p.stage_spec(stage)
                    self.assertEqual(env['SC2_DIFFICULTY'],'CheatMoney')
                    self.assertEqual(env['SC2_FINALIZATION_MODE'],'terminal-drain-v1')
                    self.assertIn('+trainer.sc2_terminal_handoff_lock_root='+str(p.ROOT),args)
                    self.assertIn('trainer.val_only=True',args)
                    if s['checkpoint']:self.assertIn('trainer.resume_from_path='+str(s['checkpoint']),args)
                self.assertEqual(set(e.terminal_options(123)),{'terminal_intent_for','finalize'})
                cpu=e.docker('cpu')
                self.assertNotIn('--gpus',cpu)
                self.assertFalse(any(v.endswith('/global_step_96:ro') for v in cpu))
        self.assertEqual(e.SELECTION_SECONDS,21600)

    def test_runtime_hook_rejects_l8_or_same(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'cfg.json'
            env=dict(SC2_ACCEPTANCE_STAGE='train2',SC2_DIFFICULTY='CheatMoney',SC2_EXPECTED_DIFFICULTY='CheatMoney',
                SC2_TRAIN_SEED_PROTOCOL=q.PROTOCOL,SC2PATH='/assets/StarCraftII',SC2_L8_RENDEZVOUS_LOW_PORT='1',
                PYTHONPATH='/source',SC2_EVAL_SEEDS_LOG_PATH='/out/seed',SC2_RUNTIME_LOG_ROOT='/out/log')
            cfg=dict(ray_init=dict(runtime_env=dict(env_vars=env,worker_process_setup_hook='l7_followup_hook.install')),
                algorithm=dict(sc2_policy_credit=dict(seed_group_mode=q.GROUP)),trainer=dict(n_gpus_per_node=8,val_only=False))
            path.write_text(json.dumps(cfg));q.runtime_environment(path,'/tmp/probe-ray')
            for key,value in [('SC2_DIFFICULTY','CheatVision'),('SC2_TRAIN_SEED_PROTOCOL','same_uniform101')]:
                bad=copy.deepcopy(cfg);bad['ray_init']['runtime_env']['env_vars'][key]=value
                path.write_text(json.dumps(bad))
                with self.assertRaises(ValueError):q.runtime_environment(path,'/tmp/probe-ray')

    def test_active_predecessor_waits_failure_blocks_and_root_never_overwritten(self):
        with patch.object(q.receipts,'small',return_value={'phase':'running-unverified'}):
            self.assertFalse(m.predecessor_complete())
        with patch.object(q.receipts,'small',return_value={'phase':'failed'}):
            with self.assertRaises(RuntimeError):m.predecessor_complete()
        with tempfile.TemporaryDirectory() as tmp,patch.object(m,'ROOT',Path(tmp)):
            with self.assertRaisesRegex(RuntimeError,'Fresh exact'):m.prepare()

    def test_queue_one_clock_keeps_all_four_no_prune_and_blocks_on_failure(self):
        for failure in (False,True):
            with self.subTest(failure=failure),tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp);train=root/'train';primary=root/'eval';train.mkdir();primary.mkdir();(train/'retention').mkdir()
                with ExitStack() as stack:
                    for guard in (patch.object(q,'configure'),patch.object(q,'ROOT',train),patch.object(q,'EVAL_ROOT',primary),
                            patch.object(q,'SOURCE_PARENT',root/'source'),patch.object(q,'check_cpu'),
                            patch.object(q,'predecessor_complete',return_value=True),patch.object(q,'admit'),
                            patch.object(q,'contract_for',return_value={}),patch.object(q,'docker',return_value=['noop']),
                            patch.object(q.sp,'run'),patch.object(q.h,'sample'),patch.object(q.fresh.queue_impl.host,'writers_clear'),
                            patch.object(r,'require_published')):stack.enter_context(guard)
                    selection=stack.enter_context(patch.object(e,'run_selection'))
                    prune=stack.enter_context(patch.object(r,'prune'))
                    primary_run=stack.enter_context(patch.object(e,'run_after_training'))
                    for i,part in enumerate(p.PARTS):
                        owner=train/part;owner.mkdir(parents=True)
                        q.a.save(owner/'deployment.json',self.cfg(i),lock_root=train)
                        q.a.save(owner/'parent-readiness.json',{'actual_parent_verified':True},lock_root=train)
                    def select(i):
                        q.a.ROOT=train/p.PARTS[i];return self.cfg(i)
                    def run(stages,*args,**kwargs):
                        if failure:raise RuntimeError('bounded failure')
                        if stages!=['gpu-preflight']:self.assertIn('terminal_intent_for',kwargs)
                        return dict(phase='completed',exit_code=0,completed=stages)
                    with patch.object(q.f,'select',side_effect=select),patch.object(q.h,'run_stages',side_effect=run):
                        if failure:
                            with self.assertRaisesRegex(RuntimeError,'bounded'):q.queue()
                            selection.assert_not_called();primary_run.assert_not_called()
                        else:
                            q.queue();selection.assert_called_once();primary_run.assert_called_once()
                            self.assertEqual(q.a.read(train/'retention/no-pruning.json')['retained_steps'],[2,32,64,96])
                        prune.assert_not_called()
                    d=q.a.read(train/'dispatch.json')
                    self.assertEqual(d['deadline']-d['start'],86400)
                    self.assertEqual(d['suite_deadline']-d['start'],108000)
                    with self.assertRaisesRegex(RuntimeError,'Already queued'):q.queue()


if __name__=='__main__':unittest.main()
