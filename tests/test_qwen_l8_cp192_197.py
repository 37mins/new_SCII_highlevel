"""Closed-parent, scope, native resume and actual environment regression gates."""
from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'experiments/records/20260921-sc2-policy-credit-v1'))
import qwen_l8_cp192_197 as m
import qwen_l8_cp192_hook as hook
import agent_system.sc2_policy_resume as policy
from agent_system.sc2_seed_protocol import ablation_seeds


class CompletedContractTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        self.parent=Path(tmp.name);self.cp=self.parent/'runs/train96/checkpoints/global_step_96'
        for n in policy.completed_l8_files():self.save(n,{})
        for n in policy.checkpoint_names():
            p=self.cp/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b'fixture')
        for n in ('state.json','host-supervision/state.json'):
            self.save(n,dict(phase='completed',exit_code=0,completed=['train96','eval96']))
        self.save('deployment.json',dict(runtime_sha=m.PARENT_SHA,model_kind='qwen',difficulty='CheatVision',
            seed_protocol='same_uniform101',seed_group_mode='same'))
        self.save('resume-contract.json',dict(version='accepted-qwen-l8-same-full-state-prefix-v1',checkpoint='/accepted/CP2'))
        for stage,games in (('train96',752),('eval96',8)):
            r=dict(status='completed',process_exit_code=0,metrics_finite=True,
                metrics_precision='binary64-v1',episode_outcomes=dict(natural_games=games,truncated=0),
                training_updates=0,start_step=2,last_global_step=96,completed_steps=94,checkpoint_complete=True,
                checkpoint_files={'checkpoints/global_step_96/'+n:{'bytes':7} for n in policy.checkpoint_names()})
            for n in ('result.json','.done'):self.save(f'runs/{stage}/{n}',r)
            self.save(f'runs/{stage}/manifest.json',dict(source_commit=m.PARENT_SHA,dirty=False,
                world_size=8,metrics_precision='binary64-v1'))
            self.save(f'acceptance-{stage}.json',dict(result=r,evidence=dict(consumed_answers=8,valid_consumed_answers=8)))
        self.save('runs/train96/checkpoints/resume_state.json',dict(from_checkpoint='/accepted/CP2',global_step=2,
            next_reset_index=2,source='checkpoint',model_optimizer_dataloader_load_returned=True))
        self.metrics=[dict(step=i,**{'actor/grad_norm':.1,'timing_s/update_actor':1.,'policy_credit/invalid_advantage_max':0.}) for i in range(3,97)]
        self.save('runs/train96/metrics.json',self.metrics)
        self.lines('training_seeds.jsonl',[dict(reset_index=i,base_seed=0,seed_protocol='same_uniform101',
            seeds=ablation_seeds('same_uniform101',0,i,1,8)) for i in range(2,96)])
        self.lines('episode_outcomes.jsonl',[dict(reset_index=i,env_index=e,terminated=True,truncated=False) for i in range(2,96) for e in range(8)])
        self.lines('checkpoints/sc2_policy_credit_audit.jsonl',[dict(pending_global_step=i,decision='accept',real_answers=8,valid_answers=8) for i in range(3,97)])
        self.contract=dict(version='accepted-qwen-l8-cp96-to192-v1',parent=str(self.parent),checkpoint=str(self.cp),
            parent_sha=m.PARENT_SHA,start_step=96,target_step=192,driver_rng_unavailable_accepted=False,
            checkpoint_bytes={n:7 for n in policy.checkpoint_names()})
        self.rehash()

    def save(self,n,obj):
        p=self.parent/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(obj))

    def lines(self,n,rows):
        (self.parent/'runs/train96'/n).write_text(''.join(json.dumps(r)+'\n' for r in rows))

    def rehash(self):self.contract['files']={n:policy.sha256(self.parent/n) for n in policy.completed_l8_files()}

    def verify(self):
        with patch.object(policy,'verify_contract',return_value={}) as ancestor:
            value=policy.verify_completed_l8_cp96(self.contract)
            ancestor.assert_called_once()
            return value

    def test_exact_completed_native_parent(self):self.assertEqual(self.verify(),{})

    def test_receipts_cannot_change(self):
        self.save('state.json',{});
        with self.assertRaisesRegex(ValueError,'evidence changed'):self.verify()

    def test_no_failed_parent(self):
        self.save('state.json',dict(phase='failed'));self.rehash()
        with self.assertRaisesRegex(ValueError,'not fully completed'):self.verify()

    def test_no_missing_optimizer_or_native_state(self):
        (self.cp/'actor/optim_world_size_8_rank_7.pt').unlink()
        with self.assertRaises(FileNotFoundError):self.verify()

    def test_only_explicit_target_and_native_permission(self):
        original=deepcopy(self.contract)
        for key,value in [('target_step',288),('start_step',8),('driver_rng_unavailable_accepted',True),('parent_sha','different')]:
            self.contract=deepcopy(original);self.contract[key]=value
            with self.assertRaises(ValueError):self.verify()

    def test_all_parent_ppo_steps_have_finite_positive_gradients(self):
        for bad in (0.,-1.,float('nan'),float('inf')):
            self.metrics[-1]['actor/grad_norm']=bad;self.save('runs/train96/metrics.json',self.metrics);self.rehash()
            with self.assertRaisesRegex(ValueError,'PPO'):self.verify()

    def test_no_positive_invalid_credit(self):
        self.metrics[0]['policy_credit/invalid_advantage_max']=.01
        self.save('runs/train96/metrics.json',self.metrics);self.rehash()
        with self.assertRaisesRegex(ValueError,'PPO'):self.verify()

    def test_seed_counter_not_reset(self):
        self.lines('training_seeds.jsonl',[]);self.rehash()
        with self.assertRaisesRegex(ValueError,'evidence changed|seed ledger'):self.verify()

    def test_all_natural_games_required(self):
        self.lines('episode_outcomes.jsonl',[dict(reset_index=2,env_index=0,terminated=True,truncated=False)]);self.rehash()
        with self.assertRaisesRegex(ValueError,'natural-game'):self.verify()

    def test_weights_only_parent_is_rejected(self):
        self.save('runs/train96/checkpoints/resume_state.json',dict(from_checkpoint='/accepted/CP2',global_step=2,
            next_reset_index=2,source='legacy',model_optimizer_dataloader_load_returned=True));self.rehash()
        with self.assertRaisesRegex(ValueError,'native restoration'):self.verify()


class LauncherTests(unittest.TestCase):
    def cfg(self):
        return dict(environment={'LONG_DEPENDENCY_PATH':'/deps'},model_kind='qwen',model_mount='/assets/qwen',
            difficulty='CheatVision',run_prefix=m.PREFIX,seed_protocol='same_uniform101',seed_group_mode='same',
            worker_hook='qwen_l8_cp192_hook.install',host=dict(model='/model',venv='/venv',sc2='/sc2',image='fixture'))

    def test_native_target192_and_approved_six_checkpoints(self):
        with patch.object(m.a,'ROOT',m.ROOT):
            for stage in m.STAGES:
                args,env,out=m.invocation(self.cfg(),stage,True)
                settings=dict(x.split('=',1) for x in args if '=' in x)
                self.assertEqual(settings['trainer.total_training_steps'],'192')
                self.assertEqual(settings['trainer.save_freq'],'16' if stage=='train192' else '-1')
                self.assertEqual(settings['trainer.val_only'],str(stage!='train192'))
                self.assertEqual(env['SC2_CHECKPOINT_RESUME'],str(stage=='train192'))
                cp=m.ROOT/'runs/train192/checkpoints/global_step_192' if stage=='eval192' else m.CHECKPOINT
                self.assertEqual(settings['trainer.resume_from_path'],str(cp))
                self.assertEqual(env['RUN_ID'],m.PREFIX+'-'+stage)
                self.assertEqual(out,m.ROOT/'cpu'/stage)
                self.assertNotIn('l7_followup_hook.install',' '.join(args))
        self.assertEqual(m.SAVED_STEPS,[112,128,144,160,176,192])

    def test_new_budget_does_not_count_or_delete_old_parent(self):
        account=m.accounts(1234)[0]
        self.assertEqual(account['roots'],[*m.RETAINED_CPU_ROOTS,m.ROOT,m.SOURCE_PARENT])
        self.assertEqual(len(set(account['roots'])),4)
        self.assertNotIn(m.PARENT_ROOT,account['roots'])
        self.assertEqual(account['limit'],384*1024**3)
        self.assertEqual(account['deadline'],1234)
        self.assertEqual(m.WALL_SECONDS,43200)
        self.assertEqual(m.disk_gate('train192'),448)
        self.assertEqual(m.disk_gate('first'),448)
        self.assertEqual(m.disk_gate('eval192'),128)
        with self.assertRaises(ValueError):m.disk_gate('unknown')

    def test_gpu_mounts_are_immutable_except_new_output_and_tmp(self):
        with patch.object(m.a,'ROOT',m.ROOT),patch.object(m.a,'read',return_value=self.cfg()):
            args=m.docker('stage','train192')
        self.assertEqual(args[:2],['docker','create'])
        self.assertIn('--read-only',args);self.assertIn('--gpus',args)
        self.assertNotIn('--rm',args);self.assertNotIn('--restart',args)
        for p in m.ANCESTORS:self.assertIn(f'{p}:{p}:ro',args)
        self.assertEqual(args[-2:],['stage','train192'])

    def test_cpu_has_no_gpu_request(self):
        with patch.object(m.a,'ROOT',m.ROOT),patch.object(m.a,'read',return_value=self.cfg()):
            args=m.docker('cpu')
        self.assertEqual(args[:2],['docker','run']);self.assertNotIn('--gpus',args)
        self.assertIn('CUDA_VISIBLE_DEVICES=',args)

    def test_regression_receipt_does_not_change_old_controller_parts(self):
        import spb_l7_random197 as old
        before = (old.ROOT, old.PARTS)
        result=SimpleNamespace(wasSuccessful=lambda:True, skipped=[],testsRun=123)
        fake_torch=SimpleNamespace(cuda=SimpleNamespace(is_initialized=lambda:False))
        with patch.dict(sys.modules,torch=fake_torch),patch.object(m.a,'read',return_value={'runtime_sha':'fixture'}),\
                patch.object(m.a,'save') as save,patch.object(m.unittest.defaultTestLoader,'loadTestsFromNames') as load,\
                patch.object(m.unittest,'TextTestRunner') as runner:
            runner.return_value.run.return_value=result
            m.regressions(False)
            self.assertEqual((old.ROOT,old.PARTS),before)
            self.assertIn('test_spb_l7_random197',load.call_args.args[0])
            self.assertIn('test_qwen_l8_cp192_197',load.call_args.args[0])
            self.assertEqual(save.call_args.args[0],m.ROOT/'regressions.json')
            self.assertTrue(save.call_args.args[1]['passed'])

    def test_reprepare_and_cpu_failure_never_dispatch(self):
        with patch.object(Path,'exists',return_value=True):
            with self.assertRaisesRegex(RuntimeError,'Fresh exact'):m.prepare()
        with patch.object(m,'check_cpu',side_effect=RuntimeError('no CPU')),patch.object(m.h,'run_stages') as run:
            with self.assertRaises(RuntimeError):m.queue()
            run.assert_not_called()

    def test_environment_proof_preserves_actual_variables(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'resolved.json'
            for stage in m.STAGES:
                cfg=dict(trainer=dict(val_only=stage!='train192',n_gpus_per_node=8,total_training_steps=192),
                    ray_init=dict(runtime_env=dict(worker_process_setup_hook='qwen_l8_cp192_hook.install',env_vars=dict(
                        SC2_ACCEPTANCE_STAGE=stage,SC2PATH='/assets/StarCraftII',SC2_DIFFICULTY='CheatVision',
                        SC2_EXPECTED_DIFFICULTY='CheatVision',SC2_L8_RENDEZVOUS_LOW_PORT='1',
                        SC2_TRAIN_SEED_PROTOCOL='same_uniform101',PYTHONPATH='/deps',
                        SC2_EVAL_SEEDS_LOG_PATH='/seeds',SC2_RUNTIME_LOG_ROOT='/logs',EXTRA='preserve'))))
                path.write_text(json.dumps(cfg));env,proof=hook.runtime_environment(path,'/tmp/probe-ray')
                self.assertEqual(env['env_vars']['EXTRA'],'preserve')
                self.assertEqual(proof['stage'],stage)
                self.assertEqual(proof['resolved_config_sha256'],policy.sha256(path))
                cfg['trainer']['val_only']=not cfg['trainer']['val_only'];path.write_text(json.dumps(cfg))
                with self.assertRaises(ValueError):hook.runtime_environment(path,'/tmp/probe-ray')


if __name__=='__main__':unittest.main()
