"""Synthetic guards for the authorized r5 L8 remainder and Ray hook parity."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] /
    'experiments/records/20260921-sc2-policy-credit-v1'))
import qwen_l8_remainder5_197 as r5
from qwen_l8_plan import STAGES


class L8Remainder5Tests(unittest.TestCase):
    def test_exact_remaining_scope_and_ten_root_budget(self):
        self.assertEqual(r5.STAGES, STAGES[4:])
        self.assertEqual(r5.WALL_SECONDS, 4 * 3600)
        self.assertEqual(r5.accounts(123), [dict(
            roots=[r5.r2.PRIOR, r5.r2.PRIOR_SOURCE, r5.r2.ROOT,
                   r5.r2.SOURCE_PARENT, r5.r3.ROOT, r5.r3.SOURCE_PARENT,
                   r5.r4.ROOT, r5.r4.SOURCE_PARENT, r5.ROOT, r5.SOURCE_PARENT],
            receipt_root=r5.ROOT, limit=32 * 1024**3, deadline=123)])

    def test_pythonpath_is_taken_from_resolved_real_launcher(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(r5, 'ROOT', Path(tmp)):
            config = Path(tmp) / 'cpu' / r5.STAGES[0] / 'resolved_config.json'
            config.parent.mkdir(parents=True)
            valid = ':'.join([str(Path(tmp) / 'runtime'),
                              str(Path(tmp) / 'runtime' / r5.FEEDBACK), str(r5.a.HERE)])
            config.write_text(json.dumps({'ray_init': {'runtime_env': {
                'env_vars': {'PYTHONPATH': valid}}}}))
            self.assertEqual(r5.probe_pythonpath(), valid)
            config.write_text(json.dumps({'ray_init': {'runtime_env': {
                'env_vars': {'PYTHONPATH': str(Path(tmp) / 'runtime')}}}}))
            with self.assertRaisesRegex(RuntimeError, 'lacks required'):
                r5.probe_pythonpath()

    def test_probe_and_cpu_hook_use_new_owned_containers(self):
        sample = ['docker', 'create', '--name', 'old-name', 'image', '-B', 'script',
                  'stage', r5.STAGES[0]]
        with patch.object(r5.pilot, 'docker', return_value=sample):
            args = r5.probe_docker()
        self.assertEqual(args[args.index('--name') + 1], r5.PREFIX + '-gpu-preflight')
        self.assertEqual(args[-1], 'gpu-preflight')

    def test_failed_preflight_cannot_dispatch_games_or_retry(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(r5, 'ROOT', Path(tmp)), \
                patch.object(r5, 'check_cpu'), \
                patch.object(r5.pilot, 'parents', return_value={'passed': True}), \
                patch.object(r5, 'previous_failures', return_value={'passed': True}), \
                patch.object(r5.pilot, 'admit'), \
                patch.object(r5.h, 'run_stages', side_effect=RuntimeError('GPU probe failed')) as run:
            with patch.object(r5.a, 'STORAGE_LOCK_ROOT', Path(tmp)):
                r5.a.save(Path(tmp) / 'deployment.json', {'first_dispatch_by': 10**12})
                with self.assertRaisesRegex(RuntimeError, 'GPU probe failed'):
                    r5.queue()
                self.assertEqual(run.call_count, 1)
                self.assertEqual(run.call_args.args[0], ['gpu-preflight'])
                self.assertEqual(r5.a.read(Path(tmp) / 'queue-state.json')['phase'], 'failed')
                with self.assertRaisesRegex(RuntimeError, 'Already queued'):
                    r5.queue()


if __name__ == '__main__':
    unittest.main()
