"""Bounded Qwen matrix, exact seed modes and inherited predecessor gates."""
import copy
import json
import os
from pathlib import Path
import sys
import subprocess
import tempfile
import unittest
from unittest.mock import patch

RECORD = Path(__file__).resolve().parents[1] / 'experiments/records/20260921-sc2-policy-credit-v1'
sys.path.insert(0, str(RECORD))
import qwen_seed197 as q


class QwenAcceptanceTests(unittest.TestCase):
    def setUp(self):
        context = patch.multiple(q, ARMS=list(q.DEFAULT_ARMS), WALL_SECONDS=8*3600,
                                 REUSED_ARM_ROOT=None)
        context.start()
        self.addCleanup(context.stop)

    def test_host_entry_import_outside_repository_without_pythonpath(self):
        env = dict(os.environ)
        env.pop('PYTHONPATH', None)
        code = (f'import sys; sys.path.insert(0, {str(RECORD)!r}); '
                'import qwen_seed197 as q; '
                'assert q.arm_config(dict(environment={},host={}),0)["training_seeds"] == [[49]*8,[97]*8]')
        result = subprocess.run([sys.executable, '-B', '-c', code], cwd='/tmp', env=env,
                                capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)

    def base(self):
        return dict(environment={'LONG_DEPENDENCY_PATH': '/deps'}, host={'model': '/old'},
                    runtime_sha='sha', controller_sha='sha')

    def test_four_independent_arms_and_paired_difficulty_seeds(self):
        base = self.base()
        arms = [q.arm_config(base, i) for i in range(4)]
        self.assertEqual(base['host']['model'], '/old')
        self.assertEqual([a['difficulty'] for a in arms], ['Harder']*2+['VeryHard']*2)
        self.assertEqual(arms[0]['training_seeds'], [[49]*8, [97]*8])
        self.assertEqual(arms[1]['training_seeds'], [[49,97,53,5,33,65,62,51], [100,38,61,45,74,27,64,17]])
        self.assertEqual(arms[0]['training_seeds'], arms[2]['training_seeds'])
        self.assertEqual(arms[1]['training_seeds'], arms[3]['training_seeds'])
        self.assertEqual(sum(a['gpu_hours'] for a in arms), 64)
        self.assertEqual(sum(sum(a['games']) for a in arms), 128)

    def test_all_twelve_launches_exact_model_protocol_and_own_checkpoint(self):
        for index in range(4):
            cfg = q.arm_config(self.base(), index)
            with patch.object(q.engine, 'ROOT', q.SUITE/q.ARMS[index][0]):
                for stage in cfg['stages']:
                    args, env, out = q.engine.invocation(cfg, stage, dry=True)
                    settings = dict(x.split('=',1) for x in args if '=' in x)
                    self.assertTrue(args[1].endswith('/run_qwen_seed_arm.sh'))
                    self.assertEqual(settings['algorithm.sc2_policy_credit.seed_group_mode'], cfg['seed_group_mode'])
                    self.assertEqual(settings['actor_rollout_ref.rollout.top_p'], '1.0')
                    self.assertEqual(env['SC2_DIFFICULTY'], cfg['difficulty'])
                    self.assertEqual(env['MODEL_PATH'], '/assets/qwen')
                    self.assertEqual(settings['trainer.total_training_steps'], '2')
                    self.assertEqual(settings['trainer.val_only'], str(stage != 'train2'))
                    for role in ('actor','rollout','ref'):
                        self.assertEqual(settings[f'+actor_rollout_ref.{role}.sc2_action_tokenizer_path'], '/assets/qwen')
                    if stage == 'post':
                        self.assertEqual(settings['trainer.resume_from_path'], str(q.engine.ROOT/'runs/train2/checkpoints/global_step_2'))
                    else:
                        self.assertNotIn('trainer.resume_from_path', settings)

    def test_same_random_only_seed_differences_in_launch_configuration(self):
        pairs = [q.engine.invocation(q.arm_config(self.base(), i), 'train2') for i in (0,1)]
        settings = [dict(x.split('=',1) for x in args if '=' in x) for args,_,_ in pairs]
        differences = {key for key in settings[0] if settings[0][key] != settings[1][key]}
        self.assertEqual(differences, {'algorithm.sc2_policy_credit.seed_group_mode',
                                      '+ray_init.runtime_env.env_vars.SC2_TRAIN_SEED_PROTOCOL'})

    def test_predecessor_pending_and_failure_do_not_dispatch(self):
        attrs = {key:getattr(q.engine,key) for key in ('ROOT','RUNTIME_SHA','TRAIN_SEEDS','TOKENIZER_SHA','MASK_SHA')}
        try:
            with patch.object(q, 'read', return_value={'phase':'waiting-predecessor'}):
                self.assertFalse(q.predecessor_complete())
            with patch.object(q, 'read', return_value={'phase':'failed'}):
                with self.assertRaises(RuntimeError): q.predecessor_complete()
        finally:
            for key,value in attrs.items(): setattr(q.engine,key,value)

    def test_budget_failure_not_zero_and_exact_eight_hour_ceiling(self):
        self.assertEqual(q.WALL_SECONDS, 8*3600)
        with patch.object(q.time,'time',return_value=100), patch.object(q,'cmd') as command:
            with self.assertRaises(TimeoutError): q.budget(145)
            command.assert_not_called()
        with patch.object(q.engine,'measure_budget',side_effect=TimeoutError('measurement failed')):
            with self.assertRaises(TimeoutError): q.budget()

    def test_duplicate_queue_rejected_before_predecessor_or_gpu(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root/'queue-state.json').write_text('{}')
            proof = dict(passed=True, skips=0, cuda_initialized=False, qwen_arm_verified=True, runtime_sha='sha',
                         controller_sha='sha', tokenizer_sha256='tokenizer', mask_sha256='mask')
            with patch.object(q,'SUITE',root), patch.object(q,'clean'), \
                 patch.object(q,'read',return_value=proof), patch.object(q,'select_arm',return_value=proof), \
                 patch.object(q,'predecessor_complete') as predecessor:
                with self.assertRaisesRegex(RuntimeError,'Already queued'): q.queue()
                predecessor.assert_not_called()


if __name__ == '__main__': unittest.main()
