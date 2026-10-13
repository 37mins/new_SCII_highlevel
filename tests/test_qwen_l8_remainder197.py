"""Synthetic continuation boundaries; no server or GPU access."""
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/
    'experiments/records/20260921-sc2-policy-credit-v1'))
import qwen_l8_remainder197 as r
from qwen_l8_hook import allocate_low_port
from qwen_l8_plan import STAGES


class L8RemainderTests(unittest.TestCase):
    def test_only_unrun_stages_and_aggregate_old_deadline(self):
        self.assertEqual(r.STAGES, STAGES[4:])
        self.assertEqual(len(r.STAGES), 8)
        self.assertEqual(r.accounts(), [dict(
            roots=[r.PRIOR, r.PRIOR_SOURCE, r.ROOT, r.SOURCE_PARENT],
            receipt_root=r.ROOT, limit=32*1024**3, deadline=r.DEADLINE)])
        with self.assertRaisesRegex(RuntimeError, 'cannot be reset'):
            r.accounts(r.DEADLINE+1)

    def test_port_allocator_is_distinct_and_below_ephemeral_range(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger, range_path = Path(tmp)/'ports', Path(tmp)/'range'
            range_path.write_text('32768 60999\n')
            # A sandboxed local test cannot bind sockets; allocation identity
            # is exercised independently of the real host-side bind gate.
            with patch('qwen_l8_hook.socket.socket'):
                first = allocate_low_port(ledger, range_path)
                second = allocate_low_port(ledger, range_path)
            self.assertNotEqual(first, second)
            self.assertTrue(20000 <= first < 30000)
            self.assertTrue(20000 <= second < 30000)
            self.assertEqual({int(x) for x in ledger.read_text().splitlines()},
                             {first, second})
            range_path.write_text('25000 60999\n')
            with self.assertRaisesRegex(RuntimeError, 'overlaps'):
                allocate_low_port(ledger, range_path)

    def test_invocation_disallows_completed_stages(self):
        with patch.object(r, 'BASE_INVOCATION', return_value=(['python'], {}, Path('/tmp'))):
            with self.assertRaisesRegex(RuntimeError, 'remaining'):
                r.invocation({}, STAGES[0])
            args, _, _ = r.invocation({}, r.STAGES[0])
            self.assertIn("+ray_init.runtime_env.env_vars.SC2_L8_RENDEZVOUS_LOW_PORT='1'", args)

    def test_failed_prefix_never_dispatches(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(r, 'ROOT', Path(tmp)), \
                patch.object(r, 'check_cpu', side_effect=RuntimeError('bad prefix')), \
                patch.object(r.h, 'run_stages') as run:
            with self.assertRaisesRegex(RuntimeError, 'bad prefix'):
                r.queue()
            run.assert_not_called()

    def test_one_shot_queue_uses_original_dispatch_clock(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(r, 'ROOT', Path(tmp)), \
                patch.object(r, 'check_cpu'), patch.object(r.pilot, 'parents', return_value={'passed': True}), \
                patch.object(r, 'check_prefix'), patch.object(r.pilot, 'admit'), \
                patch.object(r.h, 'run_stages', side_effect=RuntimeError('stage failed')) as run:
            with patch.object(r.a, 'STORAGE_LOCK_ROOT', Path(tmp)):
                r.a.save(Path(tmp)/'original-prefix-acceptance.json', {'passed': True})
                with self.assertRaisesRegex(RuntimeError, 'stage failed'):
                    r.queue()
                dispatch = r.a.read(Path(tmp)/'dispatch.json')
                self.assertEqual(dispatch['start'], r.ORIGINAL_START)
                self.assertEqual(dispatch['deadline'], r.DEADLINE)
                self.assertEqual(dispatch['new_games'], 64)
                self.assertEqual(run.call_count, 1)
                with self.assertRaisesRegex(RuntimeError, 'Already queued'):
                    r.queue()


if __name__ == '__main__':
    unittest.main()
