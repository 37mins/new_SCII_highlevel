"""CPU-only storage watchdog regressions; never dispatch or inspect a GPU."""
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import Mock, patch

RECORD = Path(__file__).resolve().parents[1] / 'experiments/records/20260921-sc2-policy-credit-v1'
sys.path.insert(0, str(RECORD))
import acceptance197 as a


class StorageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'run'
        self.source = Path(self.temp.name) / 'source' / 'code'
        self.root.mkdir()
        self.source.mkdir(parents=True)
        self.context = patch.multiple(a, ROOT=self.root, SOURCE=self.source, STORAGE_LOCK_ROOT=None)
        self.context.start()
        self.addCleanup(self.context.stop)

    def output(self, first=10, second=20):
        return f'{first}\t{self.root}\0{second}\t{self.source.parent}\0'

    def completed(self, stdout=None, stderr='', code=0):
        return subprocess.CompletedProcess(['du'], code,
                                           self.output() if stdout is None else stdout, stderr)

    def failure(self):
        files = list(self.root.glob('storage-failure-*.json'))
        self.assertEqual(len(files), 1)
        return json.loads(files[0].read_text())

    def test_complete_measurement_is_exact_and_bounded(self):
        with patch.object(a.time, 'time', return_value=100), \
             patch.object(a.sp, 'run', return_value=self.completed()) as command:
            a.budget(1000)
        args, kwargs = command.call_args
        self.assertEqual(args[0], ['du', '-sb', '--null', '--', str(self.root), str(self.source.parent)])
        self.assertGreater(kwargs['timeout'], 14)
        self.assertLessEqual(kwargs['timeout'], 15)
        self.assertFalse(kwargs['check'])
        state = json.loads((self.root / 'storage-state.json').read_text())
        self.assertEqual(state['bytes'], 30)
        self.assertEqual(state['status'], 'measured')
        self.assertEqual(state['limit'], 128 * 1024**3)
        self.assertEqual(state['deadline'], 1000)

    def test_nonzero_exit_preserves_stderr_and_does_not_accept_partial_totals(self):
        detail = 'du: cannot access run/tmp/vanished: No such file or directory\n'
        with patch.object(a.time, 'time', return_value=100), \
             patch.object(a.sp, 'run', return_value=self.completed(stderr=detail, code=1)) as command:
            with self.assertRaisesRegex(RuntimeError, 'Storage measurement failed'):
                a.budget(1000)
            self.assertEqual(command.call_count, 1)  # No hidden measurement retry.
        proof = self.failure()
        self.assertEqual(proof['returncode'], 1)
        self.assertEqual(proof['stderr']['tail'], detail)
        self.assertIsNone(proof['bytes'])
        self.assertFalse((self.root / 'storage-state.json').exists())

    def test_timeout_preserves_partial_output_and_is_not_zero(self):
        error = subprocess.TimeoutExpired(['du'], 15, output=b'partial', stderr=b'stalled')
        with patch.object(a.time, 'time', return_value=100), patch.object(a.sp, 'run', side_effect=error):
            with self.assertRaisesRegex(RuntimeError, 'Storage measurement failed'):
                a.budget(1000)
        proof = self.failure()
        self.assertEqual(proof['error_type'], 'TimeoutExpired')
        self.assertEqual(proof['stdout']['tail'], 'partial')
        self.assertEqual(proof['stderr']['tail'], 'stalled')
        self.assertIsNone(proof['returncode'])
        self.assertIsNone(proof['bytes'])

    def test_missing_executable_is_recorded(self):
        with patch.object(a.time, 'time', return_value=100), \
             patch.object(a.sp, 'run', side_effect=FileNotFoundError('du unavailable')):
            with self.assertRaisesRegex(RuntimeError, 'Storage measurement failed'):
                a.budget(1000)
        self.assertEqual(self.failure()['error_type'], 'FileNotFoundError')

    def test_malformed_missing_duplicate_or_unexpected_root_fails_closed(self):
        malformed = ['', f'10\t{self.root}\0', self.output().rstrip('\0'),
                     f'10\t{self.root}\0{20}\t{self.root}\0',
                     f'10\t{self.root}\0{20}\t/wrong/root\0',
                     self.output() + '1\t/extra\0', self.output(first=-1),
                     self.output(first='nan'), self.output(first='1.0')]
        for value in malformed:
            with self.subTest(value=value), patch.object(a.time, 'time', return_value=100), \
                 patch.object(a.sp, 'run', return_value=self.completed(stdout=value)):
                with self.assertRaisesRegex(RuntimeError, 'Storage measurement failed'):
                    a.budget(1000)
        self.assertEqual(len(list(self.root.glob('storage-failure-*.json'))), len(malformed))
        self.assertFalse((self.root / 'storage-state.json').exists())

    def test_success_exit_with_stderr_is_not_silently_trusted(self):
        with patch.object(a.time, 'time', return_value=100), \
             patch.object(a.sp, 'run', return_value=self.completed(stderr='unexpected warning')):
            with self.assertRaisesRegex(RuntimeError, 'Storage measurement failed'):
                a.budget(1000)
        self.assertEqual(self.failure()['returncode'], 0)

    def test_limit_inclusive_and_recorded(self):
        with patch.object(a.time, 'time', return_value=100), \
             patch.object(a.sp, 'run', return_value=self.completed(stdout=self.output(a.LIMIT - 20))):
            with self.assertRaisesRegex(RuntimeError, '128GiB output ceiling'):
                a.budget(1000)
        proof = self.failure()
        self.assertEqual(proof['bytes'], a.LIMIT)
        self.assertEqual(proof['status'], 'limit-exceeded')

    def test_deadline_checked_before_and_after_measurement(self):
        with patch.object(a.time, 'time', return_value=100), patch.object(a.sp, 'run') as command:
            with self.assertRaises(TimeoutError):
                a.budget(145)
            command.assert_not_called()
        with patch.object(a.time, 'time', side_effect=[100, 101]), \
             patch.object(a.sp, 'run', return_value=self.completed()) as command:
            with self.assertRaises(TimeoutError):
                a.budget(146)
            self.assertGreater(command.call_args.kwargs['timeout'], 0)
            self.assertLessEqual(command.call_args.kwargs['timeout'], 1)
        self.assertEqual(self.failure()['status'], 'deadline-exceeded')

    def test_bounded_evidence_and_last_good_state_not_relabelled(self):
        (self.root / 'storage-state.json').write_text('{"bytes":123,"checked_at":1}')
        detail = 'x' * 40000 + ' final error'
        with patch.object(a.time, 'time', return_value=100), \
             patch.object(a.sp, 'run', return_value=self.completed(stderr=detail, code=1)):
            with self.assertRaises(RuntimeError):
                a.budget(1000)
        proof = self.failure()
        self.assertTrue(proof['stderr']['truncated'])
        self.assertEqual(proof['stderr']['characters'], len(detail))
        self.assertLessEqual(len(proof['stderr']['tail']), 8192)
        self.assertTrue(proof['stderr']['tail'].endswith(' final error'))
        self.assertEqual(json.loads((self.root / 'storage-state.json').read_text()),
                         {'bytes': 123, 'checked_at': 1})

    def test_receipt_write_failure_still_stops_and_reports_both_errors(self):
        with patch.object(a.time, 'time', return_value=100), \
             patch.object(a.sp, 'run', return_value=self.completed(stderr='Permission denied', code=1)), \
             patch.object(a, 'save', side_effect=OSError('disk unavailable')), \
             patch('sys.stderr') as stderr:
            with self.assertRaisesRegex(RuntimeError, 'Storage measurement failed'):
                a.budget(1000)
        printed = ''.join(call.args[0] for call in stderr.write.call_args_list)
        self.assertIn('Permission denied', printed)
        self.assertIn('disk unavailable', printed)

    def test_concurrent_state_writers_have_distinct_temporary_files(self):
        # Both writers finish fsync before either rename. The former shared .tmp
        # deterministically loses one rename and may publish the wrong writer.
        barrier = threading.Barrier(2)
        original_fsync = os.fsync
        def synced(fd):
            original_fsync(fd)
            barrier.wait(timeout=5)
        path = self.root / 'storage-state.json'
        with patch.object(a.os, 'fsync', side_effect=synced), ThreadPoolExecutor(2) as pool:
            futures = [pool.submit(a.save, path, {'writer': i, 'payload': str(i) * 1000}) for i in (0, 1)]
            for future in futures:
                future.result(timeout=6)
        result = json.loads(path.read_text())
        self.assertEqual(result['payload'], str(result['writer']) * 1000)
        self.assertEqual(set(self.root.iterdir()), {path, self.root / '.storage.lock'})

    def test_host_watchdog_failure_stops_only_via_owned_path_without_retry(self):
        process = Mock()
        process.poll.return_value = None
        cfg = dict(controller_sha='fixture', passed=True, cuda_initialized=False)
        with patch.object(a, 'read', return_value=cfg), patch.object(a, 'clean'), \
             patch.object(a, 'predecessor_complete', return_value=True), \
             patch.object(a, 'resources_ready', return_value=True), \
             patch.object(a, 'docker', return_value=['fixture-no-docker']), \
             patch.object(a, 'stop_owned') as stop, \
             patch.object(a.sp, 'Popen', return_value=process) as launch, \
             patch.object(a.time, 'time', return_value=100), \
             patch.object(a.sp, 'run', side_effect=[self.completed(),
                               self.completed(stderr='Permission denied', code=1)]) as measure:
            with self.assertRaisesRegex(RuntimeError, 'Storage measurement failed'):
                a.queue()
        launch.assert_called_once()
        stop.assert_called_once_with()
        self.assertEqual(measure.call_count, 2)  # Admission + one failing sample.
        state = json.loads((self.root / 'queue-state.json').read_text())
        self.assertEqual(state['phase'], 'failed')
        self.assertIn('storage-failure-', state['error'])
        self.assertEqual(json.loads((self.root / 'dispatch.json').read_text())['deadline'], 7300)
        self.assertIsNone(self.failure()['bytes'])

    def test_child_failure_stops_its_process_group_before_next_stage(self):
        process = Mock(pid=12345)
        process.poll.return_value = None
        cfg = dict(controller_sha='fixture', stages=['pre', 'train2', 'post'],
                   environment={'LONG_DEPENDENCY_PATH': '/fixture'})
        def read(path):
            return {'deadline': 1000} if Path(path).name == 'dispatch.json' else cfg
        with patch.object(a, 'read', side_effect=read), patch.object(a, 'clean'), \
             patch.object(a.sp, 'Popen', return_value=process) as launch, \
             patch.object(a.os, 'killpg') as stop, patch.object(a, 'verify') as verify, \
             patch.object(a.time, 'time', return_value=100), \
             patch.object(a.sp, 'run', side_effect=[self.completed(), self.completed(code=1)]):
            with self.assertRaisesRegex(RuntimeError, 'Storage measurement failed'):
                a.execute()
        launch.assert_called_once()
        stop.assert_called_once_with(12345, a.signal.SIGINT)
        verify.assert_not_called()
        self.assertEqual(json.loads((self.root / 'state.json').read_text())['phase'], 'failed')
        self.assertFalse((self.root / 'launch-train2.json').exists())

    @unittest.skipUnless(sys.platform.startswith('linux'), 'Actual GNU du acceptance runs on node197 CPU')
    def test_real_gnu_du_accepts_both_fixture_roots(self):
        (self.root / 'payload').write_bytes(b'x' * 4096)
        with patch.object(a.time, 'time', return_value=100):
            a.budget(1000)
        state = json.loads((self.root / 'storage-state.json').read_text())
        self.assertGreaterEqual(state['bytes'], 4096)
        self.assertEqual(state['returncode'], 0)

    @unittest.skipUnless(sys.platform.startswith('linux'), 'Actual GNU du acceptance runs on node197 CPU')
    def test_real_gnu_du_missing_root_preserves_actual_failure(self):
        with patch.object(a, 'SOURCE', self.source.parent / 'missing' / 'code'), \
             patch.object(a.time, 'time', return_value=100):
            with self.assertRaisesRegex(RuntimeError, 'Storage measurement failed'):
                a.budget(1000)
        proof = self.failure()
        self.assertEqual(proof['returncode'], 1)
        self.assertIn('No such file or directory', proof['stderr']['tail'])
        self.assertIn('missing', proof['stderr']['tail'])
        self.assertIsNone(proof['bytes'])


if __name__ == '__main__':
    unittest.main()
