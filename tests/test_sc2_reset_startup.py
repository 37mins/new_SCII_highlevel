"""CPU-only startup admission checks; no SC2, Ray, CUDA or model imports."""
import ast
import errno
import fcntl
import multiprocessing as mp
import os
from pathlib import Path
import socket
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from test_r6_natural_termination import ROOT, method

ENV = ROOT / "agent_system/environments/env_package/sc2_online_restored/envSC2.py"


def admission(clock=time):
    return method(ENV, "SC2Env", "_acquire_reset_slot", os=os, time=clock, fcntl=fcntl)


def release(fd):
    method(ENV, "SC2Env", "_release_reset_slot", os=os, fcntl=fcntl)(None, fd)


def pick_free(ports):
    """Deterministically expose the pick/close/bind window, not real portpicker."""
    for port in ports:
        with socket.socket() as probe:
            try:
                probe.bind(("127.0.0.1", port))
            except OSError as exc:
                if exc.errno == errno.EADDRINUSE:
                    continue
                raise
            return port
    raise RuntimeError("Test port pool exhausted")


def fake_game(lock_dir, ports, pipe, finish):
    # Real cross-process flock, then a small TCP listener standing in for SC2.
    # Hold the listener after first observation / lease release: games overlap.
    try:
        os.environ["SC2_RESET_LOCK_DIR"] = lock_dir
        env = SimpleNamespace(reset_concurrency=1, reset_attempt_timeout=10)
        fd = admission()(env)
        try:
            port = pick_free(ports)
            with socket.socket() as listener:
                time.sleep(0.02)  # Deliberate pick-to-bind race window.
                listener.bind(("127.0.0.1", port))
                listener.listen()
                release(fd)
                fd = None
                pipe.send(("ready", port))
                if not finish.wait(10):
                    raise TimeoutError("CPU test parent did not finish")
        finally:
            release(fd)
    except BaseException as exc:
        pipe.send(("error", repr(exc)))
        raise
    finally:
        pipe.close()


class StartupAdmissionTests(unittest.TestCase):
    def test_timeout_is_fail_closed_not_unlocked_admission(self):
        with tempfile.TemporaryDirectory() as root, patch.dict(os.environ, {"SC2_RESET_LOCK_DIR": root}):
            env = SimpleNamespace(reset_concurrency=1, reset_attempt_timeout=10)
            owner = admission()(env)
            try:
                clock = SimpleNamespace(monotonic=Mock(side_effect=[0, 10]), sleep=Mock())
                with self.assertRaisesRegex(TimeoutError, "no child launched"):
                    admission(clock)(env)
                clock.sleep.assert_not_called()
            finally:
                release(owner)

    def test_metadata_write_failure_releases_descriptor_and_lock(self):
        with tempfile.TemporaryDirectory() as root, patch.dict(os.environ, {"SC2_RESET_LOCK_DIR": root}):
            env = SimpleNamespace(reset_concurrency=1, reset_attempt_timeout=10)
            with patch.object(os, "write", side_effect=OSError("disk error")), \
                    patch.object(os, "close", wraps=os.close) as close:
                with self.assertRaisesRegex(OSError, "disk error"):
                    admission()(env)
                close.assert_called_once()
            fd = admission()(env)
            release(fd)

    def test_explicit_disabled_admission_stays_disabled(self):
        self.assertIsNone(admission()(SimpleNamespace(reset_concurrency=0)))

    def reset_env(self):
        tree = ast.parse(ENV.read_text())
        cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "SC2Env")
        cls.body = [n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == "reset"]
        class Base:
            def reset(self):
                pass
        child = Mock(return_value=SimpleNamespace(start=Mock()))
        event = SimpleNamespace(set=lambda: None, wait=lambda **_: True)
        scope = dict(gym=SimpleNamespace(Env=Base), socket=socket, TimeoutException=TimeoutError,
                     mp=SimpleNamespace(Event=lambda: event, Process=child), get_unused_port=lambda: 12345)
        exec(compile(ast.Module(body=[cls], type_ignores=[]), str(ENV), "exec"), scope)
        env = scope["SC2Env"]()
        env.reset_retries = 1
        env.reset_attempt_timeout = 10
        env.fail_fast_on_env_error = True
        env.accept_timeout = 1
        for name in ("_cleanup_resources", "_setup_server", "_start_env_a_process",
                     "_send_to_a", "_clear_reset_alarm", "_mark_terminal_if_done"):
            setattr(env, name, Mock())
        env._acquire_reset_slot = Mock(return_value=7)
        env._release_reset_slot = Mock()
        env._arm_reset_alarm = Mock(return_value=False)
        env.server_socket = SimpleNamespace(settimeout=Mock(), accept=lambda: (None, None))
        env._receive_from_a = Mock(return_value={"obs": "first observation"})
        return env, child

    def test_no_child_or_retry_after_admission_timeout(self):
        env, child = self.reset_env()
        env._acquire_reset_slot.side_effect = TimeoutError("admission failed")
        with self.assertRaisesRegex(TimeoutError, "admission failed"):
            env.reset(seed=36)
        env._acquire_reset_slot.assert_called_once()
        child.assert_not_called()
        env._release_reset_slot.assert_not_called()

    def test_lease_held_through_first_observation_then_released(self):
        env, child = self.reset_env()
        def observe():
            env._release_reset_slot.assert_not_called()
            return {"obs": "first observation"}
        env._receive_from_a.side_effect = observe
        self.assertEqual(env.reset(seed=36), "first observation")
        self.assertEqual(child.call_args.kwargs["args"][0], 36)
        env._release_reset_slot.assert_called_once_with(7)

    def test_every_startup_error_releases_lease_without_extra_attempt(self):
        for name in ("_arm_reset_alarm", "_receive_from_a", "_clear_reset_alarm"):
            with self.subTest(name=name):
                env, child = self.reset_env()
                getattr(env, name).side_effect = RuntimeError("CPU injected error")
                with self.assertRaises(RuntimeError):
                    env.reset(seed=36)
                env._release_reset_slot.assert_called_once_with(7)
                self.assertLessEqual(child.call_count, 1)

    def test_candidate_launcher_keeps_one_attempt_and_serializes_startup(self):
        script = (ROOT / "experiments/records/20260921-sc2-policy-credit-v1/run_qwen_seed_arm.sh").read_text()
        self.assertIn("+ray_init.runtime_env.env_vars.SC2_RESET_RETRIES='1'", script)
        self.assertIn("+ray_init.runtime_env.env_vars.SC2_RESET_CONCURRENCY='1'", script)
        self.assertIn("SC2_ROLLOUT_N=8", script)

    def test_pick_close_bind_can_reproduce_port_collision(self):
        with socket.socket() as probe:
            probe.bind(("127.0.0.1", 0))
            ports = [probe.getsockname()[1]]
        first, second = pick_free(ports), pick_free(ports)
        self.assertEqual(first, second)
        with socket.socket() as one, socket.socket() as two:
            one.bind(("127.0.0.1", first))
            one.listen()
            with self.assertRaises(OSError) as error:
                two.bind(("127.0.0.1", second))
            self.assertEqual(error.exception.errno, errno.EADDRINUSE)

    def test_eight_process_startups_keep_eight_live_games_on_distinct_ports(self):
        context = mp.get_context("fork")
        holders = [socket.socket() for _ in range(8)]
        try:
            for holder in holders:
                holder.bind(("127.0.0.1", 0))
            ports = [holder.getsockname()[1] for holder in holders]
        finally:
            for holder in holders:
                holder.close()
        finish = context.Event()
        processes, readers = [], []
        with tempfile.TemporaryDirectory() as root:
            try:
                for _ in range(8):
                    reader, writer = context.Pipe(duplex=False)
                    process = context.Process(target=fake_game, args=(root, ports, writer, finish))
                    process.start()
                    writer.close()
                    processes.append(process)
                    readers.append(reader)
                ready_ports = []
                for reader in readers:
                    self.assertTrue(reader.poll(10), "CPU child timed out")
                    status, value = reader.recv()
                    self.assertEqual(status, "ready", value)
                    ready_ports.append(value)
                self.assertEqual(len(set(ready_ports)), 8)
                self.assertTrue(all(p.is_alive() for p in processes))
                for port in ready_ports:
                    with socket.create_connection(("127.0.0.1", port), timeout=1):
                        pass
            finally:
                finish.set()
                for process in processes:
                    process.join(2)
                    if process.is_alive():
                        process.terminate()  # Only exact children owned by this CPU test.
                        process.join(2)
                for reader in readers:
                    reader.close()
            self.assertEqual([p.exitcode for p in processes], [0]*8)


if __name__ == "__main__":
    unittest.main()
