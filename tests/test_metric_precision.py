"""Actual logger -> recorder -> unchanged positive-gradient gate, CPU only."""
import contextlib
import argparse
import hashlib
import importlib.util
import io
import json
import math
from pathlib import Path
import random
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT / 'experiments/records/20260921-sc2-policy-credit-v1'))
import run_record as record
from diagnose_ppo_metrics import diagnose, inspect_run
from l7_followup197 import verify_updates

# Import the shipped logger directly: no Torch, Ray, model or GPU dependency.
spec = importlib.util.spec_from_file_location('metric_logger', ROOT / 'verl/utils/logger/aggregate_logger.py')
logger = importlib.util.module_from_spec(spec)
spec.loader.exec_module(logger)


class MetricPrecisionTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)

    def line(self, value, step=1):
        return logger.concat_dict_to_str({'actor/grad_norm': value,
            'episode/success_rate': 1., 'policy_credit/invalid_advantage_max': 0.}, step)

    def parse(self, line, precision=record.METRIC_PRECISION):
        path = self.root / 'console.log'
        path.write_text(line + '\n')
        return record.metric_rows(path, precision)

    def fixture(self, value, precision=record.METRIC_PRECISION):
        manifest = dict(target_steps=1, world_size=1)
        if precision is not None:
            manifest['metrics_precision'] = precision
        (self.root / 'manifest.json').write_text(json.dumps(manifest))
        (self.root / 'console.log').write_text(self.line(value) + '\n')
        cp = self.root / 'checkpoints/global_step_1'
        (cp / 'actor').mkdir(parents=True)
        (cp / 'data.pt').write_bytes(b'fixture')
        for kind in ('model', 'optim', 'extra_state'):
            (cp / 'actor' / f'{kind}_world_size_1_rank_0.pt').write_bytes(b'fixture')

    def test_original_rounding_bug_and_fixed_actual_gate(self):
        self.assertEqual(f'{0.:.3f}', f'{0.0004:.3f}')
        self.fixture(0.0004)
        result = record.finish(self.root, 0)
        metrics = json.loads((self.root / 'metrics.json').read_text())
        self.assertEqual(metrics[0]['actor/grad_norm'], 0.0004)
        self.assertEqual(result['metrics_precision'], logger.METRIC_PRECISION)
        self.assertEqual(result['status'], 'completed')
        verify_updates([dict(pending_global_step=1, decision='accept')], metrics, 1, 1)

    def test_actual_start_declares_precision_and_hashes_logger_and_recorder(self):
        args = argparse.Namespace(output=self.root, config=ROOT/'configs/system-v1.env',
            bo=ROOT/'data/rush_bo.json', bo_profile='rush', model_source=self.root/'model',
            model_manifest=ROOT/'configs/qwen3-4b.sha256', model_id='fixture',
            model_revision='fixture', dry_run=True, command=['trainer.total_epochs=1',
                'trainer.n_gpus_per_node=1', 'trainer.nnodes=1'])
        def git(command, **kwargs):
            return '' if 'status' in command else 'fixture-sha'
        with patch.object(record.subprocess, 'check_output', side_effect=git):
            record.start(args)
        manifest = json.loads((self.root/'manifest.json').read_text())
        self.assertEqual(manifest['metrics_precision'], logger.METRIC_PRECISION)
        for name in ('scripts/run_record.py', 'verl/utils/logger/aggregate_logger.py'):
            self.assertEqual(manifest['source_files_sha256'][name],
                             hashlib.sha256((ROOT/name).read_bytes()).hexdigest())

    def test_new_finish_refuses_unmarked_log_without_publishing_success(self):
        self.fixture(0.0004)
        log = self.root/'console.log'
        log.write_text(log.read_text().replace(' - metrics_precision:binary64-v1', ''))
        with self.assertRaisesRegex(ValueError, 'rounded fallback'):
            record.finish(self.root, 0)
        self.assertFalse((self.root/'.done').exists())
        self.assertFalse((self.root/'result.json').exists())

    def test_true_zero_still_rejected_by_actual_gate(self):
        metrics = list(self.parse(self.line(0.)).values())
        with self.assertRaisesRegex(RuntimeError, 'PPO'):
            verify_updates([dict(pending_global_step=1, decision='accept')], metrics, 1, 1)

    def test_binary64_roundtrip_including_subnormal_and_exponents(self):
        rng = random.Random(7)
        values = [5e-324, sys.float_info.max, -0., 1e-6, -1e-100, math.pi]
        values += [math.ldexp(rng.uniform(-1., 1.), rng.randrange(-1022, 1024)) for _ in range(200)]
        for value in values:
            with self.subTest(value=value):
                recovered = self.parse(self.line(value))[1]['actor/grad_norm']
                self.assertEqual(recovered.hex(), value.hex())

    def test_actual_local_logger_flush_path_and_ray_prefix(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            logger.LocalLogger(print_to_console=True).log({'actor/grad_norm': 1e-7,
                'episode/success_rate': 1., 'policy_credit/invalid_advantage_max': 0.}, 3)
        text = '(TaskRunner pid=123) ' + output.getvalue().splitlines()[-1]
        self.assertEqual(self.parse(text)[3]['actor/grad_norm'], 1e-7)

    def test_nonfinite_recorded_without_silent_drop_and_gate_still_rejects(self):
        for value in (float('nan'), float('inf'), -float('inf')):
            with self.subTest(value=value):
                metrics = list(self.parse(self.line(value)).values())
                self.assertFalse(math.isfinite(metrics[0]['actor/grad_norm']))
                with self.assertRaises(RuntimeError):
                    verify_updates([dict(pending_global_step=1, decision='accept')], metrics, 1, 1)
        self.fixture(float('nan'))
        result = record.finish(self.root, 0)
        self.assertFalse(result['metrics_finite'])
        self.assertEqual(result['status'], 'failed')
        self.assertEqual(json.loads((self.root / 'metrics.json').read_text())[0]['actor/grad_norm'], 'nan')

    def test_positive_tiny_invalid_credit_is_not_rounded_to_zero(self):
        line = logger.concat_dict_to_str({'actor/grad_norm': 1.,
            'episode/success_rate': 1., 'policy_credit/invalid_advantage_max': 1e-9}, 1)
        metrics = list(self.parse(line).values())
        self.assertEqual(metrics[0]['policy_credit/invalid_advantage_max'], 1e-9)
        with self.assertRaises(RuntimeError):
            verify_updates([dict(pending_global_step=1, decision='accept')], metrics, 1, 1)

    def test_new_run_rejects_missing_or_wrong_marker_and_mixed_rows(self):
        good = self.line(0.0004)
        for bad in (good.replace(' - metrics_precision:binary64-v1', ''),
                    good.replace('binary64-v1', 'rounded-v0')):
            with self.assertRaisesRegex(ValueError, 'rounded fallback'):
                self.parse(bad)
            with self.assertRaises(ValueError):
                self.parse(good + '\n' + bad.replace('step:1', 'step:2'))
        with self.assertRaisesRegex(ValueError, 'Unsupported'):
            self.parse(good, 'unknown')

    def test_duplicate_new_ppo_step_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            self.parse(self.line(0.0004) + '\n' + self.line(0.0006))

    def test_legacy_parsing_is_labelled_not_upgraded(self):
        self.fixture(0., precision=None)
        old = 'step:1 - actor/grad_norm:0.000 - episode/success_rate:1.000'
        self.parse(old, precision=None)
        result = record.finish(self.root, 0)
        self.assertEqual(result['metrics_precision'], 'legacy-console-unverified')
        report = inspect_run(self.root)
        self.assertFalse(report['precision_declared'])
        self.assertFalse(report['acceptance_granted'])
        self.assertEqual(report['nonpositive_or_nonfinite_gradient_steps'], [1])

    def test_diagnostic_read_only_and_mismatched_receipt_fails(self):
        self.fixture(0.0004)
        record.finish(self.root, 0)
        before = {f.name: f.read_bytes() for f in self.root.iterdir() if f.is_file()}
        report = inspect_run(self.root)
        self.assertTrue(report['precision_declared'])
        self.assertFalse(report['acceptance_granted'])
        self.assertEqual(before, {f.name: f.read_bytes() for f in self.root.iterdir() if f.is_file()})
        (self.root / 'manifest.json').write_text('{}')
        with self.assertRaisesRegex(ValueError, 'mismatch'):
            inspect_run(self.root)

    def test_diagnostic_missing_nonfinite_fields_and_one_mib_limit(self):
        report = diagnose([{'step': 7}, {'step': 9, 'actor/grad_norm': 'nan',
            'policy_credit/invalid_advantage_max': 1e-9}], 'legacy-console-unverified')
        self.assertEqual(report['nonpositive_or_nonfinite_gradient_steps'], [7, 9])
        self.assertEqual(report['positive_or_nonfinite_invalid_credit_steps'], [7, 9])
        (self.root / 'metrics.json').write_bytes(b' ' * (1024 * 1024 + 1))
        with self.assertRaisesRegex(ValueError, '1MiB'):
            inspect_run(self.root)

    def test_evaluation_precision_and_zero_update_rule(self):
        (self.root / 'manifest.json').write_text(json.dumps({'mode': 'evaluation',
            'metrics_precision': record.METRIC_PRECISION}))
        (self.root / 'sc2-logs').mkdir()
        (self.root / 'sc2-logs/replay.SC2Replay').write_bytes(b'fixture')
        log = self.root / 'console.log'
        line = logger.concat_dict_to_str({'val/score': 0.0004}, 96)
        log.write_text(line)
        result = record.finish_evaluation(self.root, 0)
        self.assertEqual(result['metrics']['val/score'], 0.0004)
        self.assertEqual(result['training_updates'], 0)
        self.assertEqual(result['status'], 'completed')
        log.write_text(line + '\n' + self.line(0.0004))
        self.assertEqual(record.finish_evaluation(self.root, 0)['status'], 'failed')
        log.write_text('step:96 - val/score:0.000')
        with self.assertRaisesRegex(ValueError, 'rounded fallback'):
            record.finish_evaluation(self.root, 0)


if __name__ == '__main__':
    unittest.main()
