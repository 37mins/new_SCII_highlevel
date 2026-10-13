"""CPU-only deterministic publication/traversal races, no experiment dispatch."""
import ast
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
import json
import os
from pathlib import Path
import select
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import Mock, patch

REPO = Path(__file__).resolve().parents[1]
RECORD = REPO / 'experiments/records/20260921-sc2-policy-credit-v1'
sys.path.insert(0, str(RECORD))
import acceptance197 as a
import qwen_seed197 as q


class CoordinationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.fixture = Path(self.temp.name)
        self.root = self.fixture / 'suite'
        self.arm = self.root / 'arm'
        self.source = self.fixture / 'source'
        self.arm.mkdir(parents=True)
        self.source.mkdir()
        context = patch.multiple(a, ROOT=self.arm, SOURCE=self.source / 'code',
                                 STORAGE_LOCK_ROOT=self.root)
        context.start()
        self.addCleanup(context.stop)

    def holder(self, exclusive):
        code = (f'import sys; from pathlib import Path; sys.path.insert(0,{str(RECORD)!r}); '
                'import acceptance197 as a\n'
                f'with a.storage_guard(Path(sys.argv[1]), exclusive={exclusive!r}):\n'
                ' print("locked",flush=True)\n sys.stdin.readline()\n')
        process = subprocess.Popen([sys.executable, '-B', '-c', code, str(self.root)],
                                   stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   text=True)
        self.addCleanup(lambda: process.communicate('\n', timeout=5) if process.poll() is None else None)
        self.assertTrue(select.select([process.stdout], [], [], 5)[0], 'lock holder failed to start')
        self.assertEqual(process.stdout.readline().strip(), 'locked')
        return process

    def measure(self):
        a.measure_budget([self.root, self.source], self.root, 1024**2, time.time()+120,
                         'time ceiling', 'size ceiling')

    def completed(self):
        return subprocess.CompletedProcess(['du'], 0,
                    f'20\t{self.root}\0{30}\t{self.source}\0', '')

    def test_scanner_blocks_writer_before_temporary_file_creation_across_processes(self):
        holder = self.holder(True)
        inode = (self.root / '.storage.lock').stat().st_ino
        with ThreadPoolExecutor(1) as pool:
            write = pool.submit(a.save, self.arm / 'state.json', {'ok': True})
            time.sleep(0.1)
            self.assertFalse(write.done())
            self.assertEqual(list(self.arm.iterdir()), [])
            holder.communicate('\n', timeout=5)
            write.result(timeout=5)
        self.assertEqual(json.loads((self.arm/'state.json').read_text()), {'ok': True})
        self.assertEqual((self.root/'.storage.lock').stat().st_ino, inode)

    def test_writer_blocks_scanner_before_du_across_processes(self):
        holder = self.holder(False)
        with patch.object(a.sp, 'run', return_value=self.completed()) as du, ThreadPoolExecutor(1) as pool:
            scan = pool.submit(self.measure)
            time.sleep(0.1)
            du.assert_not_called()
            holder.communicate('\n', timeout=5)
            scan.result(timeout=5)
            du.assert_called_once()

    def test_lock_wait_consumes_du_allowance(self):
        clock = [0]
        @contextmanager
        def guard(*args, **kwargs):
            if kwargs.get('exclusive'):
                clock[0] += 2
            yield
        with patch.object(a, 'storage_guard', guard), \
             patch.object(a.time, 'monotonic', side_effect=lambda: clock[0]), \
             patch.object(a.sp, 'run', return_value=self.completed()) as du:
            self.measure()
        self.assertEqual(du.call_args.kwargs['timeout'], 13)

    def test_lock_timeout_stops_without_du_or_reusing_old_total(self):
        old = '{"bytes":123,"checked_at":1}'
        (self.root/'storage-state.json').write_text(old)
        holder = self.holder(True)
        with patch.object(a.sp, 'run') as du, patch('sys.stderr') as stderr:
            start = time.monotonic()
            with self.assertRaisesRegex(RuntimeError, 'Storage measurement failed'):
                a.measure_budget([self.root], self.root, 1000, time.time()+45.1, 'time', 'size')
            self.assertLess(time.monotonic()-start, 1)
            du.assert_not_called()
        printed = ''.join(c.args[0] for c in stderr.write.call_args_list)
        self.assertIn('Storage coordination lock timed out', printed)
        self.assertIn('"bytes": null', printed)
        self.assertEqual((self.root/'storage-state.json').read_text(), old)
        holder.communicate('\n', timeout=5)

    def test_failed_measurement_releases_lock_for_failure_evidence_and_writers(self):
        with patch.object(a.sp, 'run', side_effect=FileNotFoundError('du missing')):
            with self.assertRaises(RuntimeError):
                self.measure()
        self.assertEqual(len(list(self.root.glob('storage-failure-*.json'))), 1)
        a.save(self.arm/'state.json', {'after_failure': True}, timeout=0)

    def fail_only_terminal_save(self, path, data, **kwargs):
        if data.get('phase') == 'failed':
            raise TimeoutError('fixture terminal publication lock timeout')
        self.original_save(path, data, **kwargs)

    def test_host_still_stops_owned_job_when_terminal_state_cannot_be_published(self):
        self.original_save = a.save
        process = Mock()
        process.poll.return_value = None
        cfg = dict(controller_sha='fixture', passed=True, cuda_initialized=False)
        with patch.object(a, 'read', return_value=cfg), patch.object(a, 'clean'), \
             patch.object(a, 'predecessor_complete', return_value=True), \
             patch.object(a, 'resources_ready', return_value=True), \
             patch.object(a, 'docker', return_value=['fixture-no-docker']), \
             patch.object(a, 'stop_owned') as stop, patch.object(a.sp, 'Popen', return_value=process), \
             patch.object(a.time, 'time', return_value=100), \
             patch.object(a, 'budget', side_effect=[None, RuntimeError('fixture failed measurement')]), \
             patch.object(a, 'save', side_effect=self.fail_only_terminal_save):
            with self.assertRaisesRegex(TimeoutError, 'terminal publication'):
                a.queue()
        stop.assert_called_once_with()

    def test_child_still_stops_process_group_when_terminal_state_cannot_be_published(self):
        self.original_save = a.save
        process = Mock(pid=12345)
        process.poll.return_value = None
        cfg = dict(controller_sha='fixture', stages=['pre','train2','post'],
                   environment={'LONG_DEPENDENCY_PATH':'/fixture'})
        def read(path):
            return {'deadline':1000} if Path(path).name == 'dispatch.json' else cfg
        with patch.object(a, 'read', side_effect=read), patch.object(a, 'clean'), \
             patch.object(a.sp, 'Popen', return_value=process), patch.object(a.os, 'killpg') as stop, \
             patch.object(a, 'verify') as verify, \
             patch.object(a, 'budget', side_effect=[None, RuntimeError('fixture failed measurement')]), \
             patch.object(a, 'save', side_effect=self.fail_only_terminal_save):
            with self.assertRaisesRegex(TimeoutError, 'terminal publication'):
                a.execute()
        stop.assert_called_once_with(12345, a.signal.SIGINT)
        verify.assert_not_called()

    def test_qwen_still_stops_active_arm_when_terminal_state_cannot_be_published(self):
        self.original_save = a.save
        model = self.fixture/'assets/model'
        model.parent.mkdir()
        (model.parent/'VERIFIED.sha256').touch()
        (model.parent/'manifest.sha256').write_bytes(b'fixture')
        (self.source/'configs').mkdir()
        (self.source/'configs/qwen3-4b-instruct-2507.sha256').write_bytes(b'fixture')
        cfg = dict(controller_sha='fixture', runtime_sha='fixture', passed=True,
                   skips=0, cuda_initialized=False, qwen_arm_verified=True,
                   tokenizer_sha256='fixture', mask_sha256='fixture')
        process = Mock()
        process.poll.return_value = None
        with patch.multiple(q, SUITE=self.root, SOURCE=self.source, MODEL=model), \
             patch.object(q, 'read', return_value=cfg), patch.object(q, 'clean'), \
             patch.object(q, 'select_arm', return_value=cfg), \
             patch.object(q, 'predecessor_complete', return_value=True), \
             patch.object(a, 'resources_ready', return_value=True), \
             patch.object(q.shutil, 'disk_usage', return_value=Mock(free=1024**4)), \
             patch.object(q, 'docker', return_value=['fixture-no-docker']), \
             patch.object(a, 'stop_owned') as stop, patch.object(q.sp, 'Popen', return_value=process), \
             patch.object(q.time, 'time', return_value=100), \
             patch.object(q, 'budget', side_effect=[None, RuntimeError('fixture failed measurement')]), \
             patch.object(a, 'save', side_effect=self.fail_only_terminal_save):
            with self.assertRaisesRegex(TimeoutError, 'terminal publication'):
                q.queue()
        stop.assert_called_once_with()

    def test_qwen_writers_share_suite_lock_even_in_predecessor_context(self):
        with patch.object(q, 'SUITE', self.root), patch.object(a, 'ROOT', self.fixture/'old-spb'), \
             patch.object(a, 'STORAGE_LOCK_ROOT', None):
            q.save(self.root/'queue-state.json', {'phase': 'fixture'})
        self.assertTrue((self.root/'.storage.lock').is_file())
        self.assertFalse((self.fixture/'old-spb').exists())
        cfg = dict(runtime_sha='fixture', training_seeds=[])
        with patch.object(q, 'SUITE', self.root), patch.object(q, 'read', return_value=cfg), \
             patch.multiple(a, ROOT=a.ROOT, RUNTIME_SHA=a.RUNTIME_SHA, CONTAINER=a.CONTAINER,
                            TRAIN_SEEDS=a.TRAIN_SEEDS, MASK_SHA=a.MASK_SHA, TOKENIZER_SHA=a.TOKENIZER_SHA):
            for index in range(len(q.ARMS)):
                q.select_arm(index)
                self.assertEqual(a.STORAGE_LOCK_ROOT, self.root)

    @unittest.skipUnless(sys.platform.startswith('linux'), 'Actual GNU du race needs Linux CPU')
    def test_historical_save_reproduces_real_gnu_du_disappearing_temp_error(self):
        # Execute the exact uncoordinated save() from the failed frozen commit.
        raw = subprocess.check_output(['git','show',
              '019a8b3a60aa093d61fccfb4293625e300a2894e:experiments/records/20260921-sc2-policy-credit-v1/acceptance197.py'],
              cwd=REPO, text=True, timeout=5)
        tree = ast.parse(raw)
        function = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'save')
        scope = dict(Path=Path, json=json, os=os, uuid=a.uuid)
        exec(compile(ast.Module(body=[function], type_ignores=[]), '<frozen019a8b3.save>', 'exec'), scope)
        library = self.fixture/'pause.so'
        subprocess.run(['cc','-shared','-fPIC','-O2','-o',str(library),
                        str(REPO/'tests/fixtures/storage_du_pause.c'),'-ldl'], check=True,
                       capture_output=True, timeout=10)
        writer_ready, release_writer = threading.Event(), threading.Event()
        fsync = os.fsync
        def paused(fd):
            fsync(fd)
            writer_ready.set()
            if not release_writer.wait(5): raise TimeoutError('fixture writer not released')
        ready, release = self.fixture/'du-ready', self.fixture/'du-release'
        with patch.object(os, 'fsync', side_effect=paused), ThreadPoolExecutor(2) as pool:
            writer = pool.submit(scope['save'], self.arm/'storage-state.json', {'fixture': True})
            self.assertTrue(writer_ready.wait(5))
            temporary = next(self.arm.glob('.storage-state.json.*.tmp'))
            env = dict(LD_PRELOAD=str(library), SC2_DU_PAUSE_NAME=temporary.name,
                       SC2_DU_PAUSE_READY=str(ready), SC2_DU_PAUSE_RELEASE=str(release))
            try:
                with patch.dict(os.environ, env):
                    scan = pool.submit(self.measure)
                    until = time.monotonic()+5
                    while not ready.exists() and time.monotonic()<until: time.sleep(0.01)
                    self.assertTrue(ready.exists(), 'real du did not reach transient entry')
                    release_writer.set()
                    writer.result(timeout=5)
                    self.assertFalse(temporary.exists())
                    release.touch()
                    with self.assertRaisesRegex(RuntimeError, 'Storage measurement failed'):
                        scan.result(timeout=5)
            finally:
                release_writer.set()
                release.touch()
        proof = json.loads(next(self.root.glob('storage-failure-*.json')).read_text())
        self.assertEqual(proof['returncode'], 1)
        self.assertIn(temporary.name, proof['stderr']['tail'])
        self.assertIn('No such file or directory', proof['stderr']['tail'])
        self.assertIsNone(proof['bytes'])
        print('FROZEN_019A8B3_REAL_DU_REPRODUCTION', json.dumps(proof), flush=True)

    @unittest.skipUnless(sys.platform.startswith('linux'), 'Actual GNU du acceptance needs Linux CPU')
    def test_fixed_publication_finishes_before_real_du_traversal(self):
        writer_ready, release_writer = threading.Event(), threading.Event()
        fsync = os.fsync
        def paused(fd):
            fsync(fd)
            writer_ready.set()
            if not release_writer.wait(5): raise TimeoutError('fixture writer not released')
        run = subprocess.run
        with patch.object(os, 'fsync', side_effect=paused), \
             patch.object(a.sp, 'run', wraps=run) as du, ThreadPoolExecutor(2) as pool:
            writer = pool.submit(a.save, self.arm/'storage-state.json', {'fixture': True})
            try:
                self.assertTrue(writer_ready.wait(5))
                scan = pool.submit(self.measure)
                time.sleep(0.1)
                du.assert_not_called()
            finally:
                release_writer.set()
            writer.result(timeout=5)
            scan.result(timeout=5)
            du.assert_called_once()
        proof = json.loads((self.root/'storage-state.json').read_text())
        self.assertEqual((proof['returncode'], proof['stderr']['tail']), (0,''))
        self.assertEqual(set(proof['root_bytes']), {str(self.root), str(self.source)})
        self.assertEqual(list(self.arm.glob('*.tmp')), [])
        print('COORDINATED_REAL_DU_ACCEPTANCE', json.dumps(proof), flush=True)


if __name__ == '__main__': unittest.main()
