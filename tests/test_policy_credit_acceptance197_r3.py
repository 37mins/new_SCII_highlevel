"""Fresh r3 identity/budget tests; no remote calls or GPU initialization."""
import importlib.util
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

RECORD = Path(__file__).resolve().parents[1] / 'experiments/records/20260921-sc2-policy-credit-v1'
sys.path.insert(0, str(RECORD))
import acceptance197 as engine


class AcceptanceR3Tests(unittest.TestCase):
    def test_r4_reuses_protocol_and_repaired_watchdog_only(self):
        original = {name: getattr(engine, name) for name in ('ROOT', 'CONTAINER', 'RUNTIME_SHA', 'DOCKER_SCRIPT')}
        with patch.multiple(engine, **original):
            spec = importlib.util.spec_from_file_location('r4_test', RECORD / 'spb_acceptance197_r4.py')
            wrapper = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(wrapper)
            self.assertEqual(engine.ROOT.name, 'sc2-policy-credit197-20260921-r4')
            self.assertEqual(engine.CONTAINER, engine.ROOT.name)
            self.assertEqual(engine.RUNTIME_SHA, 'ce8b938341cd5b881b4dea8446ad570ed7509f78')
            self.assertEqual((engine.WALL_SECONDS, engine.LIMIT, engine.QUEUE_EXPIRES),
                             (7200, 128 * 1024**3, 1790018140.699252))
            with patch.object(engine, 'prepare'), \
                 patch.object(engine, 'read', return_value={'environment': {'LONG_DEPENDENCY_PATH': '/deps'}}), \
                 patch.object(engine, 'save') as save:
                wrapper.prepare()
                cfg = save.call_args.args[1]
            self.assertFalse(cfg['successors_authorized'])
            self.assertTrue(cfg['prior_failed_root'].endswith('-r3'))
            for stage in ('pre', 'train2', 'post'):
                args, env, out = engine.invocation(cfg, stage)
                settings = dict(x.split('=', 1) for x in args if '=' in x)
                self.assertEqual(env['RUN_ID'], f'policy-credit197-r4-{stage}')
                self.assertEqual(env['SC2_DIFFICULTY'], 'Harder')
                self.assertEqual(settings['trainer.total_training_steps'], '2')
                self.assertEqual(settings['trainer.val_only'], str(stage != 'train2'))
                if stage == 'post':
                    self.assertEqual(settings['trainer.resume_from_path'],
                                     str(engine.ROOT / 'runs/train2/checkpoints/global_step_2'))

    def test_new_identity_unchanged_budget_and_stage_protocol(self):
        original = {name: getattr(engine, name) for name in ('ROOT', 'CONTAINER', 'RUNTIME_SHA', 'DOCKER_SCRIPT')}
        with patch.multiple(engine, **original):
            spec = importlib.util.spec_from_file_location('r3_test', RECORD / 'spb_acceptance197_r3.py')
            wrapper = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(wrapper)
            self.assertEqual(engine.ROOT.name, 'sc2-policy-credit197-20260921-r3')
            self.assertEqual(engine.CONTAINER, engine.ROOT.name)
            self.assertEqual(engine.RUNTIME_SHA, 'ce8b938341cd5b881b4dea8446ad570ed7509f78')
            self.assertEqual(engine.WALL_SECONDS, 7200)
            self.assertEqual(engine.LIMIT, 128 * 1024**3)
            self.assertEqual(engine.QUEUE_EXPIRES, 1790018140.699252)
            with patch.object(engine, 'prepare') as prepare, \
                 patch.object(engine, 'read', return_value={'environment': {'LONG_DEPENDENCY_PATH': '/deps'}}), \
                 patch.object(engine, 'save') as save:
                wrapper.prepare()
                prepare.assert_called_once_with()
                cfg = save.call_args.args[1]
                self.assertFalse(cfg['successors_authorized'])
                self.assertTrue(cfg['prior_failed_root'].endswith('-r2'))
            for stage in ('pre', 'train2', 'post'):
                args, env, out = engine.invocation(cfg, stage)
                settings = dict(x.split('=', 1) for x in args if '=' in x)
                self.assertEqual(env['RUN_ID'], f'policy-credit197-r3-{stage}')
                self.assertEqual(env['SC2_DIFFICULTY'], 'Harder')
                self.assertEqual(settings['trainer.total_training_steps'], '2')
                self.assertEqual(settings['trainer.val_only'], str(stage != 'train2'))
                self.assertEqual('trainer.resume_from_path' in settings, stage == 'post')
                if stage == 'post':
                    self.assertEqual(settings['trainer.resume_from_path'],
                                     str(engine.ROOT / 'runs/train2/checkpoints/global_step_2'))


if __name__ == '__main__':
    unittest.main()
