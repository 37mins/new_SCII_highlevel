"""No server/GPU: approved two-level scope, clocks, queue and native contracts."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'experiments/records/20260921-sc2-policy-credit-v1'))
import qwen_l9l10_same197 as m
from test_qwen_l7same_fresh197 import QwenNativeContractTests
from agent_system.sc2_policy_resume import sha256, verify_contract


class HigherLevelContractTests(QwenNativeContractTests):
    def test_level_bound_contract_and_no_legacy_or_cross_level(self):
        for level,difficulty in m.DIFFICULTIES.items():
            c = self.native_qwen(); c['version']=f'accepted-qwen-l{level}-same-full-state-prefix-v1'
            path=self.parent/'deployment.json';cfg=json.loads(path.read_text());cfg['difficulty']=difficulty
            path.write_text(json.dumps(cfg)); c['files']={n:sha256(self.parent/n) for n in c['files']}
            verify_contract(c)
            for key,value in [('version',f'accepted-qwen-l{19-level}-same-full-state-prefix-v1'),
                              ('driver_rng_unavailable_accepted',True),('target_step',192)]:
                bad=copy.deepcopy(c);bad[key]=value
                with self.assertRaises(ValueError):verify_contract(bad)


class HigherLevelQueueTests(unittest.TestCase):
    def setUp(self):
        for module in (m,m.fresh,m.fresh.queue_impl,m.f,m.a,m.f.previous):
            guard=patch.dict(vars(module),{});guard.start();self.addCleanup(guard.stop)

    def cfg(self,index,level):
        return dict(runtime_sha='test',controller_sha='test',controller_source='/source/code',
            environment={'LONG_DEPENDENCY_PATH':'/deps'},training_seeds=[[49]*8,[97]*8],
            model_kind='qwen',model_mount='/assets/qwen',seed_protocol='same_uniform101',seed_group_mode='same',
            difficulty=m.DIFFICULTIES[level],run_prefix='test',worker_hook='l7_followup_hook.install',
            stages=['pre','train2','post'] if index==0 else ['train96','eval96'],
            host=dict(model='/original-qwen',venv='/venv',sc2='/sc2',image='fixed-image'))

    def resolved(self,level=9,stage='train2'):
        return dict(trainer=dict(val_only=stage in ('pre','post','eval96'),n_gpus_per_node=8),
            ray_init=dict(runtime_env=dict(worker_process_setup_hook='l7_followup_hook.install',env_vars={
                'SC2PATH':'/assets/StarCraftII','SC2_DIFFICULTY':m.DIFFICULTIES[level],
                'SC2_EXPECTED_DIFFICULTY':m.DIFFICULTIES[level],'SC2_L8_RENDEZVOUS_LOW_PORT':'1',
                'SC2_ACCEPTANCE_STAGE':stage,'SC2_TRAIN_SEED_PROTOCOL':'same_uniform101','PYTHONPATH':'/source:/deps',
                'SC2_EVAL_SEEDS_LOG_PATH':'/seeds','SC2_RUNTIME_LOG_ROOT':'/logs','PRESERVE_ME':'yes'})))

    def test_each_level_fresh_start_own_cp2_sparse_saves(self):
        for level in (9,10):
            m.configure(level)
            for index,stage in ((0,'pre'),(0,'train2'),(0,'post'),(1,'train96'),(1,'eval96')):
                with patch.object(m.a,'read',return_value=self.cfg(index,level)):
                    cfg=m.f.select(index);args,env,_=m.invocation(cfg,stage,True)
                self.assertEqual(env['SC2_DIFFICULTY'],m.DIFFICULTIES[level])
                self.assertEqual(m.a.STORAGE_LOCK_ROOT,m.ROOTS[9])
                self.assertIn('algorithm.sc2_policy_credit.seed_group_mode=same',args)
                self.assertTrue(env['RAY_TMPDIR'].startswith(f'/tmp/l{level}-'))
                if stage in ('pre','train2'):
                    self.assertFalse(any(x.startswith('trainer.resume_from_path=') for x in args))
                if stage=='train96':
                    self.assertIn('trainer.save_freq=32',args);self.assertNotIn('trainer.save_freq=8',args)
                    self.assertIn('+trainer.sc2_import_legacy_final=False',args)
                    self.assertIn('trainer.resume_from_path='+str(m.ROOTS[level]/m.PARTS[0]/'runs/train2/checkpoints/global_step_2'),args)
            wrong=self.cfg(0,19-level)
            with self.assertRaises(ValueError):m.invocation(wrong,'pre')

    def test_full_runtime_environment_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'cfg.json'
            for level in (9,10):
                for stage in ('pre','train2','post','train96','eval96'):
                    cfg=self.resolved(level,stage);path.write_text(json.dumps(cfg))
                    actual,proof=m.runtime_environment(path,'/tmp/probe-ray')
                    expected=copy.deepcopy(cfg['ray_init']['runtime_env'])
                    expected['env_vars'].update(TMPDIR='/tmp/probe-ray',RAY_TMPDIR='/tmp/probe-ray')
                    self.assertEqual(actual,expected);self.assertEqual(proof['resolved_config_sha256'],sha256(path))
            cfg['ray_init']['runtime_env']['env_vars']['SC2_EXPECTED_DIFFICULTY']='CheatVision'
            path.write_text(json.dumps(cfg))
            with self.assertRaises(ValueError):m.runtime_environment(path,'/tmp/probe-ray')

    def test_cpu_gpu_docker_cli_and_shared_lock(self):
        for level in (9,10):
            m.configure(level)
            def read(path):
                return self.resolved(level) if str(path).endswith('resolved_config.json') else self.cfg(0,level)
            with patch.object(m.a,'read',side_effect=read):
                cpu=m.docker('cpu',0);hook=m.docker('cpu-hook',0,'train2')
                gpu=m.docker('gpu-preflight',0,'train2');stage=m.docker('stage',0,'pre')
            self.assertEqual(cpu[-3:],['cpu',str(level),'0'])
            self.assertEqual(hook[-4:],['cpu-hook',str(level),'0','train2'])
            self.assertEqual(gpu[-4:],['gpu-preflight',str(level),'0','train2'])
            self.assertEqual(stage[-4:],['stage',str(level),'0','pre'])
            for x in (cpu,hook):
                self.assertNotIn('--gpus',x);self.assertIn('CUDA_VISIBLE_DEVICES=',x)
            for x in (gpu,stage):
                self.assertEqual(x[:2],['docker','create']);self.assertNotIn('--rm',x);self.assertIn('--gpus',x)
            self.assertIn(f'{m.ROOTS[9]}/.storage.lock:{m.ROOTS[9]}/.storage.lock',stage)
            if level==10:self.assertIn(f'{m.ROOTS[9]}:{m.ROOTS[9]}:ro',stage)

    def test_budgets_exact_roots_no_exclusions(self):
        accounts=m.accounts(123)
        self.assertEqual(len(accounts),3)
        for level,item in zip((9,10),accounts):
            self.assertEqual(item['roots'],[m.ROOTS[level],m.SOURCE_PARENT]);self.assertEqual(item['limit'],256*m.a.GIB)
        self.assertEqual(accounts[2]['roots'],[*m.ROOTS.values(),m.SOURCE_PARENT])
        self.assertEqual(accounts[2]['limit'],512*m.a.GIB)
        self.assertTrue(all(x['deadline']==123 for x in accounts))
        self.assertEqual(m.ARM_SECONDS,12*3600);self.assertEqual(m.SUITE_SECONDS,24*3600)
        self.assertEqual([m.disk_gate(x) for x in ('first','arm','train2','train96','pre','post','eval96')],
                         [576,320,320,320,128,128,128])

    def fixture(self,tmp):
        m.ROOTS={9:Path(tmp)/'l9',10:Path(tmp)/'l10'}
        for level,root in m.ROOTS.items():
            root.mkdir()
            m.a.save(root/'deployment.json',{'first_dispatch_by':10**12},lock_root=root)
            for index,part in enumerate(m.PARTS):
                owner=root/part;owner.mkdir(parents=True)
                m.a.save(owner/'deployment.json',self.cfg(index,level),lock_root=root)

    def test_failed_predecessor_blocks_gpu_and_no_requeue(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.fixture(tmp)
            with patch.object(m,'check_cpu'),patch.object(m,'predecessor_complete',side_effect=RuntimeError('prior failed')), \
                    patch.object(m.h,'run_stages') as run:
                with self.assertRaisesRegex(RuntimeError,'prior failed'):m.queue()
                run.assert_not_called();self.assertFalse((m.ROOTS[9]/'dispatch.json').exists())
                with self.assertRaisesRegex(RuntimeError,'Already queued'):m.queue()

    def test_probe_failure_blocks_all_games(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.fixture(tmp)
            with patch.object(m,'check_cpu'),patch.object(m,'predecessor_complete',return_value=True), \
                    patch.object(m,'admit'),patch.object(m.h,'run_stages',side_effect=RuntimeError('probe failed')) as run:
                with self.assertRaisesRegex(RuntimeError,'probe failed'):m.queue()
                self.assertEqual(run.call_count,1);self.assertEqual(run.call_args.args[0],['gpu-preflight'])
                arm=m.a.read(m.ROOTS[9]/'dispatch.json');suite=m.a.read(m.ROOTS[9]/'suite-dispatch.json')
                self.assertEqual(arm['deadline']-arm['start'],12*3600)
                self.assertEqual(suite['deadline']-suite['start'],24*3600)
                self.assertFalse((m.ROOTS[10]/'dispatch.json').exists())

    def test_short_failure_blocks_long_and_l10(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.fixture(tmp)
            with patch.object(m,'check_cpu'),patch.object(m,'predecessor_complete',return_value=True), \
                    patch.object(m,'admit'),patch.object(m.h,'run_stages',side_effect=[{},RuntimeError('short failed')]) as run, \
                    patch.object(m,'contract_for') as contract:
                with self.assertRaisesRegex(RuntimeError,'short failed'):m.queue()
                self.assertEqual(run.call_count,2);contract.assert_not_called()
                self.assertFalse((m.ROOTS[10]/'dispatch.json').exists())

    def test_long_failure_blocks_l10(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.fixture(tmp)
            m.a.save(m.ROOTS[9]/m.PARTS[1]/'parent-readiness.json',{'actual_parent_verified':True},lock_root=m.ROOTS[9])
            with patch.object(m,'check_cpu'),patch.object(m,'predecessor_complete',return_value=True),patch.object(m,'admit'), \
                    patch.object(m.h,'run_stages',side_effect=[{},{},RuntimeError('long failed')]) as run, \
                    patch.object(m,'contract_for',return_value={}),patch.object(m.sp,'run'),patch.object(m,'docker',return_value=['noop']):
                with self.assertRaisesRegex(RuntimeError,'long failed'):m.queue()
                self.assertEqual(run.call_count,3);self.assertFalse((m.ROOTS[10]/'dispatch.json').exists())

    def test_success_serial_order_fixed_clocks(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.fixture(tmp)
            for root in m.ROOTS.values():m.a.save(root/m.PARTS[1]/'parent-readiness.json',{'actual_parent_verified':True},lock_root=root)
            with patch.object(m,'check_cpu'),patch.object(m,'predecessor_complete',return_value=True),patch.object(m,'admit'), \
                    patch.object(m.h,'run_stages',return_value={}) as run,patch.object(m,'contract_for',return_value={}), \
                    patch.object(m.sp,'run'),patch.object(m,'docker',return_value=['noop']):
                m.queue()
            self.assertEqual([x.args[0] for x in run.call_args_list],
                [['gpu-preflight'],['pre','train2','post'],['train96','eval96']]*2)
            suite=m.a.read(m.ROOTS[9]/'suite-dispatch.json')
            for level,root in m.ROOTS.items():
                arm=m.a.read(root/'dispatch.json')
                self.assertEqual(arm['deadline'],min(arm['start']+12*3600,suite['deadline']))
                for part in m.PARTS:self.assertEqual(m.a.read(root/part/'dispatch.json')['deadline'],arm['deadline'])
            self.assertEqual(m.a.read(m.ROOTS[9]/'queue-state.json')['phase'],'completed')

    def test_replay_training_schema_no_replays_key(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp);m.configure(10)
            for i in range(16):
                p=out/f'sc2-logs/{i}/Flat128_CheatInsane_Air/replay.SC2Replay'
                p.parent.mkdir(parents=True);p.write_bytes(b'replay')
            m.replay_evidence(out,'train2')
            m.configure(9)
            with self.assertRaises(RuntimeError):m.replay_evidence(out,'train2')

    def long_receipts(self,tmp):
        self.fixture(tmp);m.configure(9);m.f.select(1)
        out=m.a.ROOT/'runs/train96';(out/'checkpoints').mkdir(parents=True)
        result=dict(start_step=2,last_global_step=96,completed_steps=94,checkpoint_complete=True,
                    metrics_precision='binary64-v1',checkpoint_files={})
        for step in (32,64,96):
            for name in m.checkpoint_names():
                rel=f'checkpoints/global_step_{step}/'+name;path=out/rel
                path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(b'x')
                result['checkpoint_files'][rel]={'bytes':1}
        def save(name,value):
            (out/name).write_text(json.dumps(value))
        save('manifest.json',{'metrics_precision':'binary64-v1'});save('result.json',result)
        save('checkpoints/resume_state.json',dict(from_checkpoint=str(m.ROOTS[9]/m.PARTS[0]/'runs/train2/checkpoints/global_step_2'),
             global_step=2,next_reset_index=2,source='checkpoint',next_seeds=m.ablation_seeds('same_uniform101',0,2,1,8),
             model_optimizer_dataloader_load_returned=True))
        metrics=[{'step':i,'actor/grad_norm':.25,'timing_s/update_actor':1.,'policy_credit/invalid_advantage_max':0.} for i in range(3,97)]
        save('metrics.json',metrics)
        ledgers={
            'checkpoints/sc2_policy_credit_audit.jsonl':[dict(pending_global_step=i,decision='accept',real_answers=8,valid_answers=8) for i in range(3,97)],
            'training_seeds.jsonl':[dict(reset_index=i,base_seed=0,seed_protocol='same_uniform101',seeds=m.ablation_seeds('same_uniform101',0,i,1,8)) for i in range(2,96)],
            'episode_outcomes.jsonl':[dict(reset_index=i,env_index=e,terminated=True,truncated=False) for i in range(2,96) for e in range(8)]}
        for name,rows in ledgers.items():(out/name).write_text(''.join(json.dumps(r)+'\n' for r in rows))
        return out,result,metrics

    def test_long_verifier_requires_returned_finite_ppo_not_only_audits(self):
        with tempfile.TemporaryDirectory() as tmp:
            out,result,metrics=self.long_receipts(tmp)
            with patch.object(m.a,'verify_common',return_value=(result,{})),patch.object(m,'replay_evidence'):
                m.verify('train96',write=False)
                for key,value in [('actor/grad_norm',0.),('timing_s/update_actor',0.),('policy_credit/invalid_advantage_max',float('nan'))]:
                    bad=copy.deepcopy(metrics);bad[0][key]=value;(out/'metrics.json').write_text(json.dumps(bad))
                    with self.assertRaises(RuntimeError):m.verify('train96',write=False)

    def test_actual_recorder_final_only_inventory_and_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            out,result,_=self.long_receipts(tmp)
            result['checkpoint_files']={k:v for k,v in result['checkpoint_files'].items() if '/global_step_96/' in k}
            with patch.object(m.a,'verify_common',return_value=(result,{})),patch.object(m,'replay_evidence'):
                m.verify('train96',write=False)
                proof=m.checkpoint_inventory(out,result,[32,64,96])
                self.assertEqual(len(proof),78)
                self.assertEqual(proof['checkpoints/global_step_32/data.pt']['source'],'independent-stat')
                p=out/'checkpoints/global_step_32/actor/model_world_size_8_rank_0.pt'
                p.write_bytes(b'xx')
                with self.assertRaisesRegex(RuntimeError,'shard size'):m.verify('train96',write=False)
                p.write_bytes(b'x')
                key='checkpoints/global_step_96/data.pt';del result['checkpoint_files'][key]
                with self.assertRaisesRegex(RuntimeError,'inventory'):m.verify('train96',write=False)

    def test_long_verifier_rejects_missing_native_state_extra_cp_and_wrong_seed(self):
        with tempfile.TemporaryDirectory() as tmp:
            out,result,metrics=self.long_receipts(tmp)
            with patch.object(m.a,'verify_common',return_value=(result,{})),patch.object(m,'replay_evidence'):
                p=out/'checkpoints/global_step_32/sc2_state.pt';p.unlink()
                with self.assertRaises(FileNotFoundError):m.verify('train96',write=False)
                p.write_bytes(b'x');extra=out/'checkpoints/global_step_8';extra.mkdir()
                with self.assertRaisesRegex(RuntimeError,'cadence'):m.verify('train96',write=False)
                extra.rmdir();p=out/'training_seeds.jsonl';rows=[json.loads(x) for x in p.read_text().splitlines()]
                rows[0]['seeds'][0]+=1;p.write_text(''.join(json.dumps(r)+'\n' for r in rows))
                with self.assertRaisesRegex(RuntimeError,'seed ledger'):m.verify('train96',write=False)


if __name__=='__main__':unittest.main()
