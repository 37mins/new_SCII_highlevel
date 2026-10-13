"""Regression guards for the single approved L8 r6 continuation."""
import argparse
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] /
    'experiments/records/20260921-sc2-policy-credit-v1'))
import qwen_l8_remainder6_197 as r6
from qwen_l8_plan import STAGES


class L8Remainder6Tests(unittest.TestCase):
    def test_exact_remaining_scope_and_twelve_root_budget(self):
        self.assertEqual(r6.STAGES, STAGES[4:])
        self.assertEqual(r6.WALL_SECONDS, 4 * 3600)
        self.assertEqual(r6.accounts(123), [dict(
            roots=[r6.r2.PRIOR, r6.r2.PRIOR_SOURCE, r6.r2.ROOT,
                   r6.r2.SOURCE_PARENT, r6.r3.ROOT, r6.r3.SOURCE_PARENT,
                   r6.r4.ROOT, r6.r4.SOURCE_PARENT, r6.r5.ROOT,
                   r6.r5.SOURCE_PARENT, r6.ROOT, r6.SOURCE_PARENT],
            receipt_root=r6.ROOT, limit=32 * 1024**3, deadline=123)])

    def test_cpu_hook_cli_dispatches_to_function(self):
        # This failed in r5 as globals()['cpu-hook'] before Ray ran.
        with patch.object(r6, 'configure'), patch.object(r6, 'cpu_hook') as hook:
            r6.dispatch_cli(argparse.Namespace(mode='cpu-hook', stage=None))
        hook.assert_called_once_with()

    def test_queue_requires_cpu_gate_before_dispatch(self):
        with patch.object(r6, 'check_cpu', side_effect=RuntimeError('gate failed')):
            with self.assertRaisesRegex(RuntimeError, 'gate failed'):
                r6.queue()


if __name__ == '__main__':
    unittest.main()
