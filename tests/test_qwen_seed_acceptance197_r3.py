"""Authorized replacement queue, r4 predecessor and bounded whole-suite storage."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

RECORD = Path(__file__).resolve().parents[1] / 'experiments/records/20260921-sc2-policy-credit-v1'
sys.path.insert(0, str(RECORD))
import qwen_seed197 as q
import qwen_seed197_r3 as r3


class QwenReplacementTests(unittest.TestCase):
    def setUp(self):
        names = ('SUITE', 'SPB', 'SPB_RUNTIME', 'RUN_PREFIX', 'CONTAINER_PREFIX',
                 'DOCKER_SCRIPT', 'PRIOR_ROOTS', 'ARMS', 'WALL_SECONDS', 'LIMIT',
                 'FIRST_DISPATCH_BY', 'REUSED_ARM_ROOT')
        saved = {name: getattr(q, name) for name in names}
        self.addCleanup(lambda: [setattr(q, name, value) for name, value in saved.items()])
        engine_saved = {name: getattr(q.engine, name) for name in
                        ('ROOT', 'RUNTIME_SHA', 'TRAIN_SEEDS', 'TOKENIZER_SHA', 'MASK_SHA', 'STORAGE_LOCK_ROOT')}
        self.addCleanup(lambda: [setattr(q.engine, name, value) for name, value in engine_saved.items()])
        q.ARMS, q.WALL_SECONDS, q.LIMIT = list(q.DEFAULT_ARMS), 28800, 512*1024**3
        q.FIRST_DISPATCH_BY, q.REUSED_ARM_ROOT = 1790028940.699252, None
        r3.configure()

    def test_identity_and_original_unused_budget_preserved(self):
        self.assertEqual(q.SUITE.name, 'sc2-qwen-seeds197-20260922-r3')
        self.assertEqual(q.SPB.name, 'sc2-policy-credit197-20260921-r4')
        self.assertEqual(q.SPB_RUNTIME, 'ce8b938341cd5b881b4dea8446ad570ed7509f78')
        self.assertEqual((q.WALL_SECONDS, q.LIMIT, q.FIRST_DISPATCH_BY),
                         (28800, 512*1024**3, 1790028940.699252))
        for i in range(4):
            cfg = q.arm_config(dict(host={}, environment={}), i)
            self.assertEqual(cfg['run_prefix'], 'qwen-seeds197-r3-'+q.ARMS[i][0])
            self.assertEqual((cfg['gpu_hours'], cfg['games'], cfg['updates']), (16, [8,16,8], [0,2,0]))

    def test_r4_completion_requires_three_actual_stages_and_panel(self):
        result = {'fixture': 'actual-result'}
        def read(path):
            self.assertTrue(str(path).startswith(str(q.SPB)))
            if path.name == 'queue-state.json': return {'phase': 'completed'}
            if path.name == 'state.json': return {'phase': 'completed', 'completed': ['pre','train2','post']}
            if path.name.startswith('acceptance-'): return {'result': result}
            return result
        with patch.object(q, 'read', side_effect=read), \
             patch.object(q.engine, 'predecessor_complete', return_value=True) as panel, \
             patch.object(q.engine, 'verify') as verify:
            self.assertTrue(q.predecessor_complete())
            panel.assert_called_once_with()
            self.assertEqual([call.args for call in verify.call_args_list], [('pre',),('train2',),('post',)])
            self.assertTrue(all(call.kwargs == {'write': False} for call in verify.call_args_list))
            self.assertEqual(q.engine.RUNTIME_SHA, q.SPB_RUNTIME)
        with patch.object(q, 'read', return_value={'phase': 'failed'}), \
             patch.object(q.engine, 'verify') as verify:
            with self.assertRaisesRegex(RuntimeError, 'successors blocked'): q.predecessor_complete()
            verify.assert_not_called()

    def test_container_uses_new_wrapper_and_cpu_has_no_gpu_request(self):
        args = ['docker','run','--name',q.CONTAINER_PREFIX+'l6-same-cpu',
                '-v',f'{q.MODEL}:/assets/qwen:ro','image','-B','old.py','cpu']
        with patch.object(q, 'select_arm'), patch.object(q.engine, 'docker', return_value=args):
            command = q.docker('regressions', 0)
        self.assertEqual(command[-3:], [str(q.DOCKER_SCRIPT), 'arm-regressions', '0'])
        self.assertNotIn('--gpus', command)
        self.assertIn('SC2_TEST_QWEN_METADATA_PATH=/assets/qwen', command)
        self.assertIn(f'type=bind,src={q.SUITE}/.storage.lock,dst={q.SUITE}/.storage.lock', command)

    def test_suite_counts_retained_r1_r2_and_uses_strict_measurement(self):
        with patch.object(q.time, 'time', return_value=100), \
             patch.object(Path, 'exists', return_value=True), \
             patch.object(q.engine, 'measure_budget') as measure:
            q.budget(10000)
        roots, receipt, limit, deadline, _, _ = measure.call_args.args
        self.assertEqual(roots[:3], [q.SUITE, q.SOURCE.parent, q.MODEL.parent])
        self.assertTrue(set(q.PRIOR_ROOTS).issubset(set(roots)))
        self.assertEqual((receipt, limit, deadline), (q.SUITE, 512*1024**3, 10000))
        self.assertEqual(measure.call_args.kwargs['lock_root'], q.SUITE)

    def test_failed_multiroot_measurement_not_zero_or_retry(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            failure = subprocess.CompletedProcess(['du'], 1, f'10\t{root}\0', 'Permission denied')
            with patch.object(q, 'SUITE', root), patch.object(q.engine.sp, 'run', return_value=failure) as command:
                with self.assertRaisesRegex(RuntimeError, 'Storage measurement failed'): q.budget()
                self.assertEqual(command.call_count, 1)
            proof = json.loads(next(root.glob('storage-failure-*.json')).read_text())
            self.assertIsNone(proof['bytes'])
            self.assertIn('Permission denied', proof['stderr']['tail'])
            self.assertEqual(proof['limit'], q.LIMIT)
            self.assertFalse((root/'storage-state.json').exists())


if __name__ == '__main__': unittest.main()
