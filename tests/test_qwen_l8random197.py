"""No GPU/server: independent native contract, sparse storage and fail-closed queue."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'experiments/records/20260921-sc2-policy-credit-v1'))
import qwen_l8random197 as m
import qwen_l8random_eval197 as e
import qwen_l8random_plan as plan
import qwen_l8random_retention as retention
from test_qwen_l7same_fresh197 import QwenNativeContractTests
from agent_system.sc2_policy_resume import sha256,verify_contract


class RandomNativeContractTests(QwenNativeContractTests):
    def test_l8_random_requires_correct_model_difficulty_group_and_native_state(self):
        c=self.native_qwen();c['version']='accepted-qwen-l8-random-full-state-prefix-v1'
        path=self.parent/'deployment.json';cfg=json.loads(path.read_text())
        cfg.update(difficulty='CheatVision',seed_protocol=m.PROTOCOL,seed_group_mode=m.GROUP)
        path.write_text(json.dumps(cfg));c['files']={n:sha256(self.parent/n) for n in c['files']}
        verify_contract(c)
        for key,value in [('version','accepted-qwen-random-prefix-v1'),('version','accepted-qwen-l8-same-full-state-prefix-v1'),
                          ('driver_rng_unavailable_accepted',True),('target_step',192)]:
            bad=copy.deepcopy(c);bad[key]=value
            with self.assertRaises(ValueError):verify_contract(bad)
        for key,value in [('model_kind','spb'),('difficulty','VeryHard'),('seed_protocol','same_uniform101'),('seed_group_mode','same')]:
            badcfg=copy.deepcopy(cfg);badcfg[key]=value;path.write_text(json.dumps(badcfg))
            bad=copy.deepcopy(c);bad['files']={n:sha256(self.parent/n) for n in c['files']}
            with self.assertRaises(ValueError):verify_contract(bad)
        path.write_text(json.dumps(cfg))
        (self.parent/'runs/train2/checkpoints/global_step_2/sc2_state.pt').unlink()
        with self.assertRaises(FileNotFoundError):verify_contract(c)


class RandomQueueTests(unittest.TestCase):
    def setUp(self):
        for module in (m,e,e.common,m.fresh,m.fresh.queue_impl,m.f,m.a,m.f.previous,m.storage,retention):
            guard=patch.dict(vars(module),{});guard.start();self.addCleanup(guard.stop)

    def cfg(self,index):
        return dict(runtime_sha='test',controller_sha='test',controller_source='/source/code',
            environment={'LONG_DEPENDENCY_PATH':'/deps'},training_seeds=[m.ablation_seeds(m.PROTOCOL,0,i,1,8) for i in range(96)],
            model_kind='qwen',model_mount='/assets/qwen',seed_protocol=m.PROTOCOL,seed_group_mode=m.GROUP,
            difficulty='CheatVision',run_prefix='test',worker_hook='l7_followup_hook.install',
            stages=['pre','train2','post'] if index==0 else ['train96','eval96'],
            host=dict(model='/original-qwen',venv='/venv',sc2='/sc2',image='fixed-image'))

    def resolved(self,stage='train2'):
        return dict(trainer=dict(val_only=stage in ('pre','post','eval96'),n_gpus_per_node=8),
            algorithm=dict(sc2_policy_credit=dict(seed_group_mode=m.GROUP)),
            ray_init=dict(runtime_env=dict(worker_process_setup_hook='l7_followup_hook.install',env_vars={
                'SC2PATH':'/assets/StarCraftII','SC2_DIFFICULTY':'CheatVision','SC2_EXPECTED_DIFFICULTY':'CheatVision',
                'SC2_L8_RENDEZVOUS_LOW_PORT':'1','SC2_ACCEPTANCE_STAGE':stage,'SC2_TRAIN_SEED_PROTOCOL':m.PROTOCOL,
                'PYTHONPATH':'/source:/deps','SC2_EVAL_SEEDS_LOG_PATH':'/seeds','SC2_RUNTIME_LOG_ROOT':'/logs'})))

    def test_fresh_original_native_own_cp2_and_exact_independent_schedule(self):
        m.configure()
        for index,stage in ((0,'pre'),(0,'train2'),(0,'post'),(1,'train96'),(1,'eval96')):
            with patch.object(m.a,'read',return_value=self.cfg(index)):
                cfg=m.f.select(index);args,env,_=m.invocation(cfg,stage,True)
            self.assertEqual(env['SC2_DIFFICULTY'],'CheatVision')
            self.assertIn('algorithm.sc2_policy_credit.seed_group_mode=mixed_seed_ablation',args)
            self.assertIn("+ray_init.runtime_env.env_vars.SC2_TRAIN_SEED_PROTOCOL='independent_uniform101'",args)
            if stage in ('pre','train2'): self.assertFalse(any(x.startswith('trainer.resume_from_path=') for x in args))
            if stage=='train96':
                self.assertIn('trainer.save_freq=32',args);self.assertNotIn('trainer.save_freq=8',args)
                self.assertIn('+trainer.sc2_import_legacy_final=False',args)
                self.assertIn('trainer.resume_from_path='+str(m.ROOT/m.PARTS[0]/'runs/train2/checkpoints/global_step_2'),args)
        self.assertEqual(cfg['training_seeds'][:3],[[49,97,53,5,33,65,62,51],[100,38,61,45,74,27,64,17],[36,17,96,12,79,32,68,90]])
        with self.assertRaises(ValueError):m.parent_for(2)
        wrong=self.cfg(0);wrong['seed_protocol']='same_uniform101'
        with self.assertRaises(ValueError):m.invocation(wrong,'pre')

    def test_full_runtime_preservation_and_reject_wrong_seed(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'cfg.json';cfg=self.resolved();path.write_text(json.dumps(cfg))
            actual,proof=m.runtime_environment(path,'/tmp/probe-ray')
            expected=copy.deepcopy(cfg['ray_init']['runtime_env']);expected['env_vars'].update(TMPDIR='/tmp/probe-ray',RAY_TMPDIR='/tmp/probe-ray')
            self.assertEqual(actual,expected);self.assertEqual(proof['resolved_config_sha256'],sha256(path))
            cfg['ray_init']['runtime_env']['env_vars']['SC2_TRAIN_SEED_PROTOCOL']='same_uniform101';path.write_text(json.dumps(cfg))
            with self.assertRaises(ValueError):m.runtime_environment(path,'/tmp/probe-ray')

    def test_docker_actual_cli_cpu_no_gpu_readonly_comparator(self):
        m.configure()
        def read(p):return self.resolved() if str(p).endswith('resolved_config.json') else self.cfg(0)
        with patch.object(m.a,'read',side_effect=read):
            cpu=m.docker('cpu',0);hook=m.docker('cpu-hook',0,'train2');check=m.docker('checkpoint-cpu',1)
            gpu=m.docker('gpu-preflight',0,'train2');stage=m.docker('stage',0,'pre')
        for x in (cpu,hook,check):self.assertNotIn('--gpus',x);self.assertIn('CUDA_VISIBLE_DEVICES=',x)
        self.assertEqual(check[-2:],['checkpoint-cpu','1'])
        self.assertEqual(hook[-3:],['cpu-hook','0','train2'])
        for x in (gpu,stage):self.assertEqual(x[:2],['docker','create']);self.assertIn('--read-only',x);self.assertNotIn('--rm',x)
        self.assertIn(f'{m.BASE_CONFIG}:{m.BASE_CONFIG}:ro',cpu)
        self.assertNotIn(f'{m.BASE}:{m.BASE}:ro',cpu)
        self.assertFalse(any(str(m.PRIOR_ROOT) in x for x in stage))

    def test_historical_symlink_target_is_explicit_hash_bound_readonly_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            old=Path(tmp)/'same-r1/cpu/train2';old.mkdir(parents=True)
            cfg=old/'resolved_config.json';cfg.write_text(json.dumps({'historical':True}))
            new=Path(tmp)/'same-r2/cpu';new.mkdir(parents=True);(new/'train2').symlink_to(old)
            with patch.object(m,'BASE',new.parent),patch.object(m,'BASE_CONFIG',cfg),\
                 patch.object(m,'BASE_CONFIG_SHA256',sha256(cfg)):
                self.assertEqual((m.BASE/'cpu/train2/resolved_config.json').resolve(),m.BASE_CONFIG.resolve())
                self.assertEqual(m.baseline_config(),{'historical':True})
                with patch.object(m.a,'read',return_value=self.cfg(0)):
                    m.configure();args=m.docker('cpu',0)
                self.assertIn(f'{cfg}:{cfg}:ro',args)
                self.assertNotIn(f'{new.parent}:{new.parent}:ro',args)
                cfg.write_text('changed')
                with self.assertRaisesRegex(RuntimeError,'file/hash'):m.baseline_config()

    def test_model_regression_receipt_inside_actual_writable_owner_not_readonly_suite(self):
        m.configure()
        with patch.object(m.a,'read',return_value=self.cfg(0)):
            args=m.docker('regressions',0)
        mounts=[args[i+1].split(':') for i,x in enumerate(args[:-1]) if x=='-v']
        writable=[Path(x[1]) for x in mounts if x[-1]!='ro']
        receipt=m.regression_receipt(False)
        self.assertEqual(receipt,m.ROOT/m.PARTS[0]/'regressions.json')
        self.assertTrue(any(receipt.is_relative_to(p) for p in writable))
        self.assertFalse(any((m.ROOT/'regressions.json').is_relative_to(p) for p in writable))
        self.assertEqual(m.regression_receipt(True),m.ROOT/'host-regressions.json')

    def test_complete_roots_budgets_no_legacy_retries(self):
        x=m.accounts(123);self.assertEqual([r['limit']//m.a.GIB for r in x],[256,32,8,288])
        self.assertEqual(x[-1]['roots'],[m.OLD_ROOT,m.OLD_EVAL_ROOT,m.OLD_SOURCE_PARENT,m.R2_ROOT,m.R2_EVAL_ROOT,m.R2_SOURCE_PARENT,m.ROOT,m.EVAL_ROOT,m.SOURCE_PARENT])
        self.assertEqual(len(set(x[-1]['roots'])),9)
        self.assertEqual(set(x[0]['roots']),{m.OLD_ROOT,m.OLD_SOURCE_PARENT,m.R2_ROOT,m.R2_SOURCE_PARENT,m.ROOT,m.SOURCE_PARENT})
        self.assertTrue(all(p.is_relative_to(plan.ROOT) and not p.is_relative_to(plan.R2_ROOT) for p in plan.SELECTION_CHECKPOINTS.values()))
        self.assertTrue(all(r['deadline']==123 for r in x))
        self.assertEqual((m.TRAIN_SECONDS,m.EVAL_SECONDS,m.SUITE_SECONDS),(57600,21600,79200))
        with tempfile.TemporaryDirectory() as tmp,patch.object(m,'ROOT',Path(tmp)):
            with self.assertRaisesRegex(RuntimeError,'Fresh exact'):m.prepare()

    def fixture(self,tmp):
        m.ROOT=Path(tmp)/'train';m.EVAL_ROOT=Path(tmp)/'eval';m.ROOT.mkdir();m.EVAL_ROOT.mkdir()
        m.configure()
        for index,part in enumerate(m.PARTS):
            owner=m.ROOT/part;owner.mkdir(parents=True)
            m.a.save(owner/'deployment.json',self.cfg(index),lock_root=m.ROOT)
        m.a.save(m.ROOT/m.PARTS[1]/'parent-readiness.json',{'actual_parent_verified':True},lock_root=m.ROOT)

    def test_failed_predecessor_blocks_all_new_dispatch_and_no_requeue(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.fixture(tmp)
            with patch.object(m,'check_cpu'),patch.object(m,'predecessor_complete',side_effect=RuntimeError('L10 failed')),patch.object(m.h,'run_stages') as run:
                with self.assertRaisesRegex(RuntimeError,'L10 failed'):m.queue()
                run.assert_not_called();self.assertFalse((m.ROOT/'dispatch.json').exists())
                with self.assertRaisesRegex(RuntimeError,'Already queued'):m.queue()

    def test_predecessor_running_waits_without_gpu_and_no_old_writes(self):
        with patch.object(m.receipts,'small',return_value={'phase':'running-unverified'}),patch.object(m.a,'cmd') as cmd:
            self.assertFalse(m.predecessor_complete());cmd.assert_not_called()

    def run_fixture(self,tmp,side_effect):
        self.fixture(tmp)
        self.stack=[]
        for target,name,kwargs in [(m,'check_cpu',{}),(m,'predecessor_complete',{'return_value':True}),
            (m,'resources_ready',{'return_value':True}),(m.h,'sample',{}),
            (m.fresh.queue_impl.host,'writers_clear',{}),(m,'contract_for',{'return_value':{}}),
            (m.sp,'run',{}),(m,'docker',{'return_value':['noop']}),
            (e,'run_selection',{}),(retention,'prune',{}),
            (e,'run_after_training',{}),(m.h,'sample',{}),(m.h,'run_stages',{'side_effect':side_effect})]:
            p=patch.object(target,name,**kwargs);self.stack.append(p);p.start();self.addCleanup(p.stop)

    def test_real_admission_receipts_unique_success_clocks_and_eval_after_long(self):
        with tempfile.TemporaryDirectory() as tmp:
            calls=[]
            def run(stages,command,verify,accounts,owner,supervision,lock,deadline,admit):
                calls.append(list(stages))
                for s in stages:admit(s)
                return dict(phase='completed',exit_code=0,completed=stages,deadline=deadline)
            self.run_fixture(tmp,run);m.queue()
            self.assertEqual(calls,[['gpu-preflight'],['pre','train2','post'],['train96','eval96']])
            dispatch=m.a.read(m.ROOT/'dispatch.json')
            self.assertEqual(dispatch['deadline']-dispatch['start'],57600)
            self.assertEqual(dispatch['suite_deadline']-dispatch['start'],79200)
            e.run_selection.assert_called_once()
            self.assertEqual(e.run_selection.call_args.args[0],dispatch['deadline'])
            retention.prune.assert_called_once()
            e.run_after_training.assert_called_once()
            self.assertEqual(e.run_after_training.call_args.args[0],dispatch['suite_deadline'])
            files=list(m.ROOT.rglob('fsync-*'));self.assertEqual(len(files),7)
            self.assertEqual(m.a.read(m.ROOT/'queue-state.json')['phase'],'completed')

    def test_each_failure_blocks_remaining_stages(self):
        for position in (0,1,2):
            with self.subTest(position=position),tempfile.TemporaryDirectory() as tmp:
                effects=[{}]*position+[RuntimeError('stage failed')]
                self.run_fixture(tmp,effects)
                with self.assertRaisesRegex(RuntimeError,'stage failed'):m.queue()
                e.run_after_training.assert_not_called()
                e.run_selection.assert_not_called()
                for p in reversed(self.stack):p.stop()

    def test_selection_or_retention_failure_blocks_primary_test(self):
        for target,name in ((e,'run_selection'),(retention,'prune')):
            with self.subTest(stage=name),tempfile.TemporaryDirectory() as tmp:
                self.run_fixture(tmp,lambda *args,**kwargs:dict(phase='completed',exit_code=0))
                with patch.object(target,name,side_effect=RuntimeError('selection/retention failed')):
                    with self.assertRaisesRegex(RuntimeError,'selection/retention'):m.queue()
                e.run_after_training.assert_not_called()
                self.assertEqual(m.a.read(m.ROOT/'queue-state.json')['phase'],'failed')
                for p in reversed(self.stack):p.stop()

    def test_selection_runs_all_fixed_stages_with_capped_clock(self):
        with tempfile.TemporaryDirectory() as tmp:
            e.ROOT=Path(tmp)/'selection';e.ROOT.mkdir();e.TRAIN_ROOT=Path(tmp)
            e.STAGES=plan.SELECTION_STAGES;calls=[]
            def run(stages,command,verify,accounts,owner,supervision,lock,deadline,admit):
                calls.append((list(stages),deadline))
                for stage in stages: verify(stage)
                return dict(phase='completed',exit_code=0,completed=list(stages),deadline=deadline)
            with patch.object(e,'configure'),patch.object(retention,'require_published'),\
                 patch.object(e.common.receipts,'validate_terminal'),patch.object(e.common.receipts,'terminal_container'),\
                 patch.object(e.common,'verify'),patch.object(e.common,'verify_probe'),\
                 patch.object(retention,'update_best') as best,patch.object(e.h,'run_stages',side_effect=run),\
                 patch.object(e.time,'time',return_value=100):
                e.run_selection(1000,lambda _:[],lambda *args:None)
            self.assertEqual(calls,[(['gpu-preflight'],1000),(plan.SELECTION_STAGES,1000)])
            self.assertEqual([x.args[0] for x in best.call_args_list],list(plan.SELECTION_ARMS))
            self.assertEqual(e.a.read(e.ROOT/'dispatch.json')['new_games'],128)
            self.assertEqual(e.a.read(e.ROOT/'state.json')['phase'],'completed')

    def test_seed_plan_unique_and_fixed_zero_update_pairs(self):
        plan.validate();self.assertEqual(len(plan.STAGES),24)
        for b in range(8):
            specs=[plan.stage_spec(s) for s in plan.STAGES[b*3:b*3+3]]
            self.assertEqual({s['arm'] for s in specs},set(plan.ARMS))
            self.assertTrue(all(s['seeds']==specs[0]['seeds'] for s in specs))
        zero=plan.paired_statistics([1]*64,[1]*64)
        self.assertEqual(zero['difference'],0);self.assertEqual(zero['exact_two_sided_mcnemar'],1)
        self.assertEqual(zero['paired_bootstrap_95'],[0,0])
        with self.assertRaises(ValueError):plan.paired_statistics([1]*8,[1]*8)

    def test_long_requires_actual_finite_ppo_exact_seed_and_final_only_inventory(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.fixture(tmp);m.f.select(1);out=m.a.ROOT/'runs/train96';(out/'checkpoints').mkdir(parents=True)
            result=dict(start_step=2,last_global_step=96,completed_steps=94,checkpoint_complete=True,
                        metrics_precision='binary64-v1',checkpoint_files={})
            for step in (32,64,96):
                for name in m.checkpoint_names():
                    rel=f'checkpoints/global_step_{step}/'+name;path=out/rel;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(b'x')
                    if step==96:result['checkpoint_files'][rel]={'bytes':1}
            def save(name,value):(out/name).write_text(json.dumps(value))
            save('result.json',result);save('manifest.json',{'metrics_precision':'binary64-v1'})
            save('checkpoints/resume_state.json',dict(from_checkpoint=str(m.ROOT/m.PARTS[0]/'runs/train2/checkpoints/global_step_2'),
                global_step=2,next_reset_index=2,source='checkpoint',next_seeds=m.ablation_seeds(m.PROTOCOL,0,2,1,8),model_optimizer_dataloader_load_returned=True))
            metrics=[{'step':i,'actor/grad_norm':.25,'timing_s/update_actor':1.,'policy_credit/invalid_advantage_max':0.} for i in range(3,97)]
            save('metrics.json',metrics)
            ledgers={'checkpoints/sc2_policy_credit_audit.jsonl':[dict(pending_global_step=i,decision='accept',real_answers=8,valid_answers=8) for i in range(3,97)],
                'training_seeds.jsonl':[dict(reset_index=i,base_seed=0,seed_protocol=m.PROTOCOL,seeds=m.ablation_seeds(m.PROTOCOL,0,i,1,8)) for i in range(2,96)],
                'episode_outcomes.jsonl':[dict(reset_index=i,env_index=e,terminated=True,truncated=False) for i in range(2,96) for e in range(8)]}
            for name,rows in ledgers.items():(out/name).write_text(''.join(json.dumps(r)+'\n' for r in rows))
            for i in range(752):
                path=out/f'sc2-logs/{i}/Flat128_CheatVision_Air/replay.SC2Replay';path.parent.mkdir(parents=True);path.write_bytes(b'replay')
            with patch.object(m.a,'verify_common',return_value=(result,{})):
                m.verify('train96',False)
                for key,value in [('actor/grad_norm',0.),('timing_s/update_actor',0.),('policy_credit/invalid_advantage_max',float('nan'))]:
                    bad=copy.deepcopy(metrics);bad[0][key]=value;save('metrics.json',bad)
                    with self.assertRaises(RuntimeError):m.verify('train96',False)
                save('metrics.json',metrics)
                path=out/'training_seeds.jsonl';rows=ledgers['training_seeds.jsonl'];rows[0]['seeds']=[53]*8
                path.write_text(''.join(json.dumps(r)+'\n' for r in rows))
                with self.assertRaisesRegex(RuntimeError,'independent seed'):m.verify('train96',False)
                rows[0]['seeds']=m.ablation_seeds(m.PROTOCOL,0,2,1,8);path.write_text(''.join(json.dumps(r)+'\n' for r in rows))
                (out/'checkpoints/global_step_32/sc2_state.pt').unlink()
                with self.assertRaises(FileNotFoundError):m.verify('train96',False)

    def test_evaluation_three_load_modes_no_future_cp_directory_creation(self):
        cfg=self.cfg(0);cfg['worker_hook']='qwen_l8random_eval_hook.install';cfg['stages']=plan.STAGES
        with patch.object(m.a,'read',return_value=cfg):
            e.configure()
            for stage in plan.STAGES[:3]:
                args,env,_=e.common.invocation(cfg,stage,True)
                spec=plan.stage_spec(stage)
                self.assertIn('trainer.val_only=True',args);self.assertIn('trainer.save_freq=-1',args)
                self.assertEqual(env['SC2_CHECKPOINT_RESUME'],'False')
                if spec['checkpoint']:self.assertIn('trainer.resume_from_path='+str(spec['checkpoint']),args)
            args=e.docker('cpu')
        self.assertNotIn('--gpus',args)
        self.assertFalse(any(x==f'{plan.CHECKPOINTS["random96"]}:{plan.CHECKPOINTS["random96"]}:ro' for x in args))
        self.assertIn(f'{e.TRAIN_ROOT}:{e.TRAIN_ROOT}:ro',args)

    def test_selection_configs_separated_from_test_and_no_uncreated_cp_mounts(self):
        plan.validate();self.assertFalse(set(plan.SELECTION_SEEDS)&set(plan.SEEDS))
        self.assertEqual(len(plan.SELECTION_STAGES),16)
        cfg=self.cfg(0);cfg['worker_hook']='qwen_l8random_eval_hook.install'
        with patch.object(m.a,'read',return_value=cfg):
            e.configure(True)
            self.assertEqual(len(e.HOOK_STAGES),4)
            for stage in plan.SELECTION_STAGES:
                args,env,out=e.common.invocation(cfg,stage,True);spec=plan.stage_spec(stage)
                self.assertEqual(out,plan.SELECTION_ROOT/'cpu'/stage)
                self.assertIn('trainer.val_only=True',args)
                self.assertIn('trainer.save_freq=-1',args)
                self.assertIn('trainer.resume_from_path='+str(spec['checkpoint']),args)
                self.assertEqual(spec['seeds'],plan.SELECTION_SEEDS[spec['batch']*8:spec['batch']*8+8])
            args=e.docker('cpu')
            self.assertEqual(args[-2:],['cpu','--selection'])
            self.assertNotIn('--gpus',args)
            self.assertNotIn(f'{plan.CHECKPOINTS["same96"]}:{plan.CHECKPOINTS["same96"]}:ro',args)
            e.configure(False)
            self.assertEqual(e.ROOT,plan.EVAL_ROOT)

    def test_selection_failure_blocks_pruning_and_primary_test(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.run_fixture(tmp,lambda *args,**kwargs:dict(phase='completed',exit_code=0))
            e.run_selection.side_effect=RuntimeError('selection failed')
            with self.assertRaisesRegex(RuntimeError,'selection failed'):m.queue()
            retention.prune.assert_not_called();e.run_after_training.assert_not_called()


if __name__=='__main__':unittest.main()
