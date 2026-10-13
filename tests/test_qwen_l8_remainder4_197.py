"""Synthetic guards for the single authorized r4 L8 remainder attempt."""
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] /
    'experiments/records/20260921-sc2-policy-credit-v1'))
import qwen_l8_remainder4_197 as r4
from qwen_l8_plan import STAGES


class L8Remainder4Tests(unittest.TestCase):
    def test_exact_scope_eight_roots_and_short_socket(self):
        self.assertEqual(r4.STAGES, STAGES[4:])
        self.assertEqual(r4.WALL_SECONDS, 4 * 3600)
        self.assertEqual(r4.accounts(123), [dict(
            roots=[r4.r2.PRIOR, r4.r2.PRIOR_SOURCE, r4.r2.ROOT,
                   r4.r2.SOURCE_PARENT, r4.r3.ROOT, r4.r3.SOURCE_PARENT,
                   r4.ROOT, r4.SOURCE_PARENT],
            receipt_root=r4.ROOT, limit=32 * 1024**3, deadline=123)])
        self.assertLess(len('/tmp/probe-ray/session_latest/sockets/plasma_store'), 107)

    def test_probe_is_new_retained_container(self):
        sample = ['docker', 'create', '--name', 'old-name', 'image', '-B', 'script',
                  'stage', r4.STAGES[0]]
        with patch.object(r4.pilot, 'docker', return_value=sample):
            args = r4.probe_docker()
        self.assertEqual(args[args.index('--name') + 1], r4.PREFIX + '-gpu-preflight')
        self.assertEqual(args[-1], 'gpu-preflight')

    def test_failed_preflight_cannot_dispatch_games_or_retry(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(r4, 'ROOT', Path(tmp)), \
                patch.object(r4, 'check_cpu'), \
                patch.object(r4.pilot, 'parents', return_value={'passed': True}), \
                patch.object(r4, 'previous_failures', return_value={'passed': True}), \
                patch.object(r4.pilot, 'admit'), \
                patch.object(r4.h, 'run_stages', side_effect=RuntimeError('GPU probe failed')) as run:
            with patch.object(r4.a, 'STORAGE_LOCK_ROOT', Path(tmp)):
                r4.a.save(Path(tmp) / 'deployment.json', {'first_dispatch_by': 10**12})
                with self.assertRaisesRegex(RuntimeError, 'GPU probe failed'):
                    r4.queue()
                self.assertEqual(run.call_count, 1)
                self.assertEqual(run.call_args.args[0], ['gpu-preflight'])
                self.assertEqual(r4.a.read(Path(tmp) / 'queue-state.json')['phase'], 'failed')
                with self.assertRaisesRegex(RuntimeError, 'Already queued'):
                    r4.queue()


if __name__ == '__main__':
    unittest.main()
