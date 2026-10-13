"""Bounded continuation launcher contracts; no actual GPU or process stop."""
import json
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

REC = Path(__file__).resolve().parents[1]/'experiments/records/20260921-sc2-policy-credit-v1'
sys.path.insert(0,str(REC))
import qwen_l7_long197 as long
import acceptance197 as engine


class Long197Tests(unittest.TestCase):
    def config(self):
        return dict(environment={'LONG_DEPENDENCY_PATH':'/deps'},model_kind='qwen',
                    model_mount='/assets/qwen',difficulty='VeryHard',run_prefix='ql7',
                    seed_protocol='same_uniform101',seed_group_mode='same',
                    worker_hook='qwen_l7_long_hook.install')

    def test_only_two_stages_and_exact_resume_budgets(self):
        with patch.object(engine,'ROOT',long.ROOT):
            for stage in ('train96','eval96'):
                args,env,out=long.invocation(self.config(),stage)
                settings=dict(x.split('=',1) for x in args if '=' in x)
                self.assertEqual(settings['trainer.total_training_steps'],'96')
                self.assertEqual(settings['trainer.resume_mode'],'resume_path')
                self.assertEqual(settings['trainer.val_only'],str(stage=='eval96'))
                self.assertEqual(env['SC2_CHECKPOINT_RESUME'],str(stage=='train96'))
                self.assertEqual(env['OUTPUT_DIR'],str(out))
                self.assertEqual(out,long.ROOT/'runs'/stage)
                self.assertEqual(settings['trainer.save_freq'],'8' if stage=='train96' else '-1')
                self.assertEqual(settings['trainer.resume_from_path'],str(long.CHECKPOINT if stage=='train96' else long.ROOT/'runs/train96/checkpoints/global_step_96'))
                self.assertEqual(settings['actor_rollout_ref.rollout.top_p'],'1.0')
                self.assertEqual(settings['+ray_init.runtime_env.env_vars.SC2_TRAIN_SEED_PROTOCOL'],"'same_uniform101'")
                self.assertIn("'"+stage+"'",settings['+ray_init.runtime_env.env_vars.SC2_ACCEPTANCE_STAGE'])
        self.assertEqual(long.WALL_SECONDS,172800)
        self.assertEqual(long.LIMIT,1024**4)
        for bad in ('pre','train2','post','l7-random'):
            with self.assertRaises(ValueError):long.invocation(self.config(),bad)

    def test_storage_counts_parent_and_new_roots_no_exclusions(self):
        with patch.object(engine,'measure_budget') as measure:
            long.budget(123)
        self.assertEqual(measure.call_args.args[0],[long.ROOT,long.SOURCE.parent,long.PARENT])
        self.assertEqual(measure.call_args.args[2:4],(1024**4,123))

    def test_busy_gpu_waits_no_reservation(self):
        with patch.object(engine,'cmd',return_value='\n'.join(f'{i}, {1 if i==0 else 0}, 0' for i in range(8))):
            self.assertFalse(long.resources_ready())

    def test_no_prepare_over_existing_root(self):
        with patch.object(Path,'exists',return_value=True):
            with self.assertRaisesRegex(RuntimeError,'Fresh exact root'):
                long.prepare()

    def test_queue_needs_actual_regression_receipt(self):
        with patch.object(engine,'read',return_value=dict(passed=False,skips=0)),patch.object(engine,'queue') as q:
            with self.assertRaises(RuntimeError):long.queue()
            q.assert_not_called()

    def test_shell_preserves_default_and_honors_full_resume_manifest_key(self):
        script=(REC/'run_qwen_seed_arm.sh').read_text()
        self.assertIn('+trainer.sc2_checkpoint_resume="${SC2_CHECKPOINT_RESUME:-False}"',script)
        self.assertNotIn('++trainer.sc2_checkpoint_resume',script)

    def test_final_paired_rng_compares_state_not_process_identity(self):
        old=dict(rank=2,seed=2,cpu_rng_sha256='cpu',cuda_rng_sha256='gpu',pid=10)
        new=dict(old,pid=20)
        self.assertTrue(long.paired_rng_matches(new,old,2))
        self.assertFalse(long.paired_rng_matches(new,old,3))
        new['cuda_rng_sha256']='changed'
        self.assertFalse(long.paired_rng_matches(new,old,2))
