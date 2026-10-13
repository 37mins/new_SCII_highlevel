"""Synthetic r3 scope, deferred CUDA import and one-shot GPU preflight guards."""
import inspect
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] /
    'experiments/records/20260921-sc2-policy-credit-v1'))
import qwen_l8_hook as hook
import qwen_l8_remainder3_197 as r3
from qwen_l8_plan import STAGES


class L8Remainder3Tests(unittest.TestCase):
    def test_exact_remaining_scope_and_six_root_budget(self):
        self.assertEqual(r3.STAGES, STAGES[4:])
        self.assertEqual(r3.WALL_SECONDS, 4*3600)
        self.assertEqual(r3.accounts(123), [dict(
            roots=[r3.r2.PRIOR, r3.r2.PRIOR_SOURCE, r3.r2.ROOT,
                   r3.r2.SOURCE_PARENT, r3.ROOT, r3.SOURCE_PARENT],
            receipt_root=r3.ROOT, limit=32*1024**3, deadline=123)])

    def test_setup_hook_defers_worker_import_until_actor_construction(self):
        self.assertNotIn('WorkerHelper', inspect.getsource(hook.install))
        source = (Path(__file__).resolve().parents[1] /
                  'verl/single_controller/base/worker.py').read_text()
        self.assertIn('SC2_L8_RENDEZVOUS_LOW_PORT', source)
        self.assertIn('from qwen_l8_hook import allocate_low_port', source)

    def test_invocation_changes_only_remaining_stage_and_port_flag(self):
        with patch.object(r3.r2, 'BASE_INVOCATION', return_value=(['python'], {}, Path('/tmp'))):
            with self.assertRaisesRegex(RuntimeError, 'unrun'):
                r3.invocation({}, STAGES[0])
            args, _, _ = r3.invocation({}, r3.STAGES[0])
            self.assertIn("+ray_init.runtime_env.env_vars.SC2_L8_RENDEZVOUS_LOW_PORT='1'", args)

    def test_probe_uses_fresh_retained_container(self):
        sample = ['docker', 'create', '--name', 'old-name', 'image', '-B', 'script',
                  'stage', r3.STAGES[0]]
        with patch.object(r3.pilot, 'docker', return_value=sample):
            args = r3.probe_docker()
        self.assertEqual(args[:2], ['docker', 'create'])
        self.assertEqual(args[args.index('--name')+1], r3.PREFIX+'-gpu-preflight')
        self.assertEqual(args[-1], 'gpu-preflight')

    def test_failed_preflight_never_dispatches_game_stage(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(r3, 'ROOT', Path(tmp)), \
                patch.object(r3, 'check_cpu'), patch.object(r3.pilot, 'parents', return_value={'passed': True}), \
                patch.object(r3, 'previous_failures', return_value={'passed': True}), \
                patch.object(r3.pilot, 'admit'), \
                patch.object(r3.h, 'run_stages', side_effect=RuntimeError('GPU probe failed')) as run:
            with patch.object(r3.a, 'STORAGE_LOCK_ROOT', Path(tmp)):
                r3.a.save(Path(tmp)/'deployment.json', {'first_dispatch_by': 10**12})
                with self.assertRaisesRegex(RuntimeError, 'GPU probe failed'):
                    r3.queue()
                self.assertEqual(run.call_count, 1)
                self.assertEqual(run.call_args.args[0], ['gpu-preflight'])
                self.assertEqual(r3.a.read(Path(tmp)/'queue-state.json')['phase'], 'failed')
                with self.assertRaisesRegex(RuntimeError, 'Already queued'):
                    r3.queue()


if __name__ == '__main__':
    unittest.main()
