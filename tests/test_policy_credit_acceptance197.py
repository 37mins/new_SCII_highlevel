"""Small pure-CPU tests of the one-shot acceptance's boundaries, not GPU success."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

RECORD = Path(__file__).resolve().parents[1] / 'experiments/records/20260921-sc2-policy-credit-v1'
sys.path.insert(0, str(RECORD))
import acceptance197 as a


class AcceptanceTests(unittest.TestCase):
    def test_fixed_disjoint_seeds(self):
        self.assertEqual(len(set(a.EVAL_SEEDS)), 8)
        self.assertTrue(all(65536 <= seed < 2**32-1 for seed in a.EVAL_SEEDS))
        self.assertFalse(set(a.EVAL_SEEDS) & {2732, 43567})

    def test_three_stage_overrides(self):
        cfg = {'environment': {'LONG_DEPENDENCY_PATH': '/deps'}}
        for stage in ('pre', 'train2', 'post'):
            with self.subTest(stage=stage):
                command, env, out = a.invocation(cfg, stage)
                settings = dict(x.split('=', 1) for x in command if '=' in x)
                self.assertEqual(settings['trainer.total_training_steps'], '2')
                self.assertEqual(settings['trainer.val_only'], str(stage != 'train2'))
                self.assertEqual(settings['actor_rollout_ref.rollout.top_p'], '1.0')
                self.assertEqual(settings['actor_rollout_ref.rollout.val_kwargs.top_p'], '1.0')
                self.assertEqual(settings["++ray_init.runtime_env.env_vars.SC2_ORIGINAL_GAME_SEEDS"], "'0'")
                self.assertEqual(settings['algorithm.sc2_policy_credit.enabled'], 'True')
                for role in ('actor', 'rollout', 'ref'):
                    self.assertEqual(settings[f'+actor_rollout_ref.{role}.sc2_action_response_length'], '192')
                self.assertEqual('trainer.resume_from_path' in settings, stage == 'post')
                self.assertEqual(env['SC2_CHECKPOINT_RESUME'], 'False')
                self.assertEqual(env['SC2_DIFFICULTY'], 'Harder')
        with self.assertRaises(ValueError):
            a.invocation(cfg, 'train96')

    def test_predecessor_pending_and_failed(self):
        with patch.object(a, 'read', return_value={'phase': 'launching-unverified'}):
            self.assertFalse(a.predecessor_complete())
        with patch.object(a, 'read', return_value={'phase': 'failed'}):
            with self.assertRaises(RuntimeError):
                a.predecessor_complete()

    def test_predecessor_claim_without_all_batches_rejected(self):
        with patch.object(a, 'read', return_value={'phase': 'completed', 'completed': [], 'training_updates': 0}):
            with self.assertRaises(RuntimeError):
                a.predecessor_complete()

    def test_predecessor_real_results_required(self):
        complete = [dict(arm=arm, batch=batch) for batch in range(8) for arm in ('original', 'D96', 'C96')]
        result = dict(status='completed', process_exit_code=0, training_updates=0,
                      episode_outcomes={'natural_games': 8})
        def read(path):
            if Path(path).name == 'state.json':
                return dict(phase='completed', completed=complete, training_updates=0)
            return result
        with patch.object(a, 'read', side_effect=read):
            self.assertTrue(a.predecessor_complete())
            result['training_updates'] = 1
            with self.assertRaises(RuntimeError):
                a.predecessor_complete()

    def test_busy_gpu_never_ready(self):
        rows = '\n'.join(f'{i}, {1024 if i == 7 else 0}, 0' for i in range(8))
        with patch.object(a, 'cmd', return_value=rows) as command:
            self.assertFalse(a.resources_ready())
            self.assertEqual(command.call_count, 1)

    def test_budget_expiry_precedes_measurement(self):
        with patch.object(a.time, 'time', return_value=100), patch.object(a.sp, 'run') as command:
            with self.assertRaises(TimeoutError):
                a.budget(145)
            command.assert_not_called()
        # Detailed failure/timeout/partial-output cases live in the storage
        # suite, which uses fixture roots and also runs real GNU du on Linux.

    def test_only_owned_container_can_stop(self):
        record = [{'Config': {'Labels': {'sc2.acceptance.root': '/another-run'}}, 'State': {'Running': True}}]
        with patch.object(a, 'cmd', return_value=json.dumps(record)) as command:
            with self.assertRaises(RuntimeError):
                a.stop_owned()
            self.assertEqual(command.call_count, 1)

    def test_existing_queue_cannot_restart(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'queue-state.json').write_text('{}')
            record = dict(controller_sha='frozen', passed=True, cuda_initialized=False)
            with patch.object(a, 'ROOT', root), patch.object(a, 'clean'), patch.object(a, 'read', return_value=record):
                with self.assertRaisesRegex(RuntimeError, 'Already queued'):
                    a.queue()


if __name__ == '__main__':
    unittest.main()
