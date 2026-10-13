"""Synthetic small-receipt recovery gates; never load model/optimizer shards."""
from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'experiments/records/20260921-sc2-policy-credit-v1'))
import qwen_random_cp8_197 as run
import agent_system.sc2_policy_resume as policy
from agent_system.sc2_seed_protocol import ablation_seeds


class RecoveryContractTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.parent=Path(self.tmp.name);self.cp=self.parent/'runs/train96/checkpoints/global_step_8'
        for name in policy.recovered_prefix_files():self.save(name,{})
        for name in policy.checkpoint_names():
            path=self.cp/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(b'fixture-not-checkpoint')
        self.save('state.json',dict(phase='failed'))
        self.save('deployment.json',dict(runtime_sha='9cb291ea5f50de205c5d88371e08ce229b7d9d04',
            model_kind='qwen',difficulty='VeryHard',seed_protocol='independent_uniform101',seed_group_mode='mixed_seed_ablation'))
        self.save('resume-contract.json',dict(version='accepted-qwen-random-prefix-v1',checkpoint='/accepted/CP2'))
        r=dict(status='failed',process_exit_code=1,start_step=2,last_global_step=13,completed_steps=11,
            metrics_precision='binary64-v1',empty_policy_batches=[])
        for n in ('result.json','.done'):self.save('runs/train96/'+n,r)
        self.save('runs/train96/manifest.json',dict(metrics_precision='binary64-v1',dirty=False,world_size=8,
            source_commit='9cb291ea5f50de205c5d88371e08ce229b7d9d04'))
        self.save('runs/train96/checkpoints/resume_state.json',dict(from_checkpoint='/accepted/CP2',global_step=2,
            next_reset_index=2,model_optimizer_dataloader_load_returned=True,
            source='verified legacy ledger; driver RNG unavailable, not bitwise replay'))
        self.lines('training_seeds.jsonl',[dict(reset_index=i,base_seed=0,seed_protocol='independent_uniform101',
            seeds=ablation_seeds('independent_uniform101',0,i,1,8)) for i in range(2,14)])
        self.lines('episode_outcomes.jsonl',[dict(reset_index=i,env_index=e,terminated=True,truncated=False) for i in range(2,13) for e in range(8)])
        self.metrics=[dict(step=i,**{'actor/grad_norm':.1,'policy_credit/invalid_advantage_max':0,'timing_s/update_actor':1}) for i in range(3,14)]
        self.save('runs/train96/metrics.json',self.metrics)
        self.lines('checkpoints/sc2_policy_credit_audit.jsonl',[dict(pending_global_step=i,decision='accept',real_answers=8,valid_answers=8) for i in range(3,14)])
        self.lines('prompt_response.jsonl',[dict(policy_action_applied=True,semantic_action_evaluable=True,
            semantic_action_valid=True,is_action_valid=True,llm_response='fixture')])
        self.save('cpu/train96/resolved_config.json',dict(ray_init=dict(runtime_env=dict(env_vars={'SC2_RESET_RETRIES':'1'}))))
        self.contract=dict(version='recovered-qwen-random-native-cp8-v1',parent=str(self.parent),checkpoint=str(self.cp),
            parent_sha='9cb291ea5f50de205c5d88371e08ce229b7d9d04',start_step=8,target_step=96,
            driver_rng_unavailable_accepted=False,checkpoint_bytes={n:(self.cp/n).stat().st_size for n in policy.checkpoint_names()})
        self.rehash()

    def save(self,name,value):
        path=self.parent/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value))

    def lines(self,name,rows):
        (self.parent/'runs/train96'/name).write_text(''.join(json.dumps(x)+'\n' for x in rows))

    def rehash(self):self.contract['files']={n:policy.sha256(self.parent/n) for n in policy.recovered_prefix_files()}

    def verify(self):
        # Existing accepted-prefix regressions separately validate the ancestor;
        # this fixture isolates CP8's *additional* failed-run gates.
        with patch.object(policy,'verify_contract',return_value={}) as ancestor:
            value=policy.verify_recovered_cp8(self.contract)
            ancestor.assert_called_once_with(json.loads((self.parent/'resume-contract.json').read_text()))
            return value

    def test_closed_prefix_allows_only_explicit_startup_change(self):
        self.assertEqual(self.verify()['ray_init']['runtime_env']['env_vars'],{'SC2_RESET_RETRIES':'1','SC2_RESET_CONCURRENCY':'1'})
        self.assertNotIn('SC2_RESET_CONCURRENCY',json.loads((self.parent/'cpu/train96/resolved_config.json').read_text())['ray_init']['runtime_env']['env_vars'])

    def test_changed_hash_is_rejected(self):
        self.save('state.json',{'phase':'completed'})
        with self.assertRaisesRegex(ValueError,'evidence changed'):self.verify()

    def test_failed_parent_cannot_be_relabelled_completed(self):
        self.save('state.json',{'phase':'completed'});self.rehash()
        with self.assertRaisesRegex(ValueError,'Unexpected failed'):self.verify()

    def test_no_weights_only_or_legacy_fallback(self):
        self.contract['driver_rng_unavailable_accepted']=True
        with self.assertRaises(ValueError):self.verify()
        self.contract['driver_rng_unavailable_accepted']=False
        (self.cp/'actor/optim_world_size_8_rank_7.pt').unlink()
        with self.assertRaises(FileNotFoundError):self.verify()

    def test_original_six_updates_must_have_positive_finite_gradient(self):
        for value in (0,-1,float('nan'),float('inf')):
            with self.subTest(value=value):
                self.metrics[2]['actor/grad_norm']=value;self.save('runs/train96/metrics.json',self.metrics);self.rehash()
                with self.assertRaisesRegex(ValueError,'prefix PPO'):self.verify()

    def test_no_waiver_for_invalid_credit_or_update_time(self):
        for key,value in [('policy_credit/invalid_advantage_max',.1),('policy_credit/invalid_advantage_max',float('nan')),('timing_s/update_actor',0)]:
            values=deepcopy(self.metrics);values[0][key]=value;self.save('runs/train96/metrics.json',values);self.rehash()
            with self.assertRaisesRegex(ValueError,'prefix PPO'):self.verify()

    def test_seed_counter_and_closed_games_are_bound(self):
        self.lines('training_seeds.jsonl',[]);self.rehash()
        with self.assertRaisesRegex(ValueError,'seed ledger'):self.verify()

    def test_no_thinking_or_invalid_consumption(self):
        self.lines('prompt_response.jsonl',[dict(policy_action_applied=True,semantic_action_evaluable=True,
            semantic_action_valid=True,is_action_valid=True,llm_response='<THINK>bad')]);self.rehash()
        with self.assertRaisesRegex(ValueError,'consumed-answer'):self.verify()

    def test_retry_protocol_not_silently_changed(self):
        self.save('cpu/train96/resolved_config.json',dict(ray_init=dict(runtime_env=dict(env_vars={'SC2_RESET_RETRIES':'2'}))));self.rehash()
        with self.assertRaisesRegex(ValueError,'startup protocol'):self.verify()


class RecoveryLauncherTests(unittest.TestCase):
    def config(self):
        return dict(environment={'LONG_DEPENDENCY_PATH':'/deps'},model_kind='qwen',model_mount='/assets/qwen',
            difficulty='VeryHard',run_prefix='qr8',seed_protocol='independent_uniform101',
            seed_group_mode='mixed_seed_ablation',worker_hook='l7_followup_hook.install')

    def test_native_training_and_own_eval_only(self):
        with patch.object(run.a,'ROOT',run.ROOT):
            for stage in run.STAGES:
                args,env,out=run.invocation(self.config(),stage)
                settings=dict(x.split('=',1) for x in args if '=' in x)
                self.assertEqual(settings['trainer.total_training_steps'],'96')
                self.assertEqual(settings['trainer.resume_from_path'],str(run.CHECKPOINT if stage=='train96' else run.ROOT/'runs/train96/checkpoints/global_step_96'))
                self.assertEqual(env['SC2_CHECKPOINT_RESUME'],str(stage=='train96'))
                self.assertEqual(settings['trainer.val_only'],str(stage=='eval96'))
                self.assertEqual(settings['actor_rollout_ref.rollout.top_p'],'1.0')
                self.assertEqual(settings['algorithm.sc2_policy_credit.seed_group_mode'],'mixed_seed_ablation')
                if stage=='train96':self.assertEqual(settings['+trainer.sc2_import_legacy_final'],'False')
        with self.assertRaises(ValueError):run.invocation(self.config(),'pre')

    def test_fixed_clocks_and_all_old_new_storage_roots(self):
        arm,suite=run.accounts()
        self.assertEqual(arm['deadline'],1790308720.0467553)
        self.assertEqual(suite['deadline'],1790420762.305692)
        self.assertEqual((arm['limit'],suite['limit']),(1024**4,2*1024**4))
        self.assertEqual(len(arm['roots']),15);self.assertEqual(len(suite['roots']),15)
        self.assertTrue(set(run.CPU_PREPARATION)<=set(arm['roots']))
        self.assertEqual(set(arm['roots'])-{run.old.ROOT/'qwen-random'},set(suite['roots'])-{run.old.ROOT})
        self.assertIn(run.ANCESTOR,arm['roots']);self.assertIn(run.ROOT,arm['roots'])

    def test_reprepare_and_unaccepted_cpu_block_queue(self):
        with patch.object(Path,'exists',return_value=True):
            with self.assertRaisesRegex(RuntimeError,'Fresh exact'):run.prepare()
        with patch.object(run.a,'clean'),patch.object(run.a,'read',side_effect=[{'controller_sha':'x','runtime_sha':'x'},{'passed':False}]),patch.object(run.h,'run_stages') as stages:
            with self.assertRaisesRegex(RuntimeError,'CPU acceptance'):run.queue()
            stages.assert_not_called()

    def test_gpu_command_has_only_accounted_writable_mounts(self):
        cfg=dict(self.config(),host=dict(venv='/venv',model='/model',sc2='/sc2',image='sha256:fixture'))
        with patch.object(run.a,'ROOT',run.ROOT),patch.object(run.a,'CONTAINER',run.CONTAINER),patch.object(run.a,'read',return_value=cfg):
            args=run.docker('stage','train96')
        self.assertEqual(args[:2],['docker','create']);self.assertIn('--read-only',args)
        self.assertIn('--gpus',args);self.assertNotIn('--rm',args)
        self.assertEqual(args[args.index('--name')+1],run.CONTAINER+'-train96')
        self.assertIn('sc2.acceptance.root='+str(run.ROOT),args)
        self.assertEqual(args[-2:],['stage','train96'])
