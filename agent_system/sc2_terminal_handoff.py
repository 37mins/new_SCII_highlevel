"""Opt-in terminal intent, not an experiment-success or checkpoint receipt.

Publish before TaskRunner locals/Ray actors are torn down. The shared lock is
the same stable inode the host holds exclusively across check/pause/du/resume.
Thus teardown cannot begin between a host's intent check and its freeze call.
"""
import fcntl
import json
import os
from pathlib import Path
import time

VERSION = 'terminal-drain-v1'


def publish(output, lock_root, run_id, *, timeout=15):
    output, lock_root = Path(output), Path(lock_root)
    if (not output.is_absolute() or not lock_root.is_absolute()
            or not 0 < timeout <= 15):
        raise ValueError('Explicit absolute paths and bounded lock wait required')
    manifest = json.loads((output / 'manifest.json').read_text())
    if manifest.get('finalization_mode') != VERSION:
        raise RuntimeError('Host-deferred finalization must be declared before training')
    until = time.monotonic() + timeout
    # Open the pre-existing inode: a typo must not create a second coordination lock.
    with (lock_root / '.storage.lock').open('r+') as lock:
        while True:
            try:
                fcntl.flock(lock, fcntl.LOCK_SH | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                remaining = until - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError('Terminal intent could not acquire storage lock')
                time.sleep(min(.01, remaining))
        proof = dict(version=VERSION, run_id=run_id, output=str(output),
                     source_commit=manifest['source_commit'], task_fit_returned=True,
                     experiment_accepted=False, pid=os.getpid(), at=time.time())
        # Exclusive creation; partial/malformed content fails closed on the host.
        with (output / 'terminal-intent.json').open('x') as stream:
            json.dump(proof, stream, allow_nan=False)
            stream.flush()
            os.fsync(stream.fileno())
    return proof


def publish_from_config(config):
    lock_root = config.trainer.get('sc2_terminal_handoff_lock_root')
    if lock_root is None:
        return  # Existing frozen/default launch paths are unchanged.
    checkpoints = Path(config.trainer.default_local_dir)
    if checkpoints.name != 'checkpoints':
        raise ValueError('Exact SC2 recorder checkpoint directory required')
    return publish(checkpoints.parent, lock_root, config.trainer.experiment_name)
