"""Bounded opt-in terminal drain before the unchanged exact-root du batch.

Caller MUST hold the same exclusive storage lock used by terminal publication
and retain it through this context. No intent: normal verified pause. Intent:
wait for this exact container's exit0, never pause teardown or measure it live.
Waiting and du share the original 15s allowance; timeout remains fatal.
"""
from contextlib import contextmanager
import json
from pathlib import Path
import time

import storage_quiescent197 as q
from storage_guardian197 import exited_ok

VERSION = 'terminal-drain-v1'


def validate_intent(intent):
    path = Path(intent['path'])
    if path.is_symlink() or path.stat().st_size > 4096:
        raise ValueError('Invalid terminal intent file')
    value = json.loads(path.read_text())
    expected = dict(version=VERSION, output=str(path.parent),
                    run_id=intent['run_id'], source_commit=intent['source_commit'],
                    task_fit_returned=True, experiment_accepted=False)
    if any(value.get(k) != v for k, v in expected.items()):
        raise ValueError('Terminal intent identity/version mismatch')
    return value


@contextmanager
def quiesce(guardian, intent, until, proof):
    path = Path(intent['path'])
    if not path.exists() and not path.is_symlink():
        with guardian.quiesce(until, proof):
            yield
        return
    validate_intent(intent)
    evidence = proof['quiescence'] = dict(version=VERSION, mode='draining-unverified',
        container_id=guardian.cid, owner_root=str(guardian.owner),
        intent=str(path), paused_verified=False, cleanup='guardian-recovery-required')
    while True:
        if time.monotonic() >= until:
            raise TimeoutError('Terminal drain consumed original measurement allowance')
        state = q.inspect_owned(guardian.cid, guardian.owner, until)
        if exited_ok(state):
            evidence.update(mode='exited-zero', cleanup='verified-exited-zero',
                            exited_at=time.time(), final_state=state)
            break
        if not state['Running'] or state['Paused'] or state.get('Dead') or state.get('Restarting'):
            raise RuntimeError('Terminal container not running/unpaused or exited nonzero')
        time.sleep(max(0, min(.05, until-time.monotonic())))
    yield  # Exact container is now stopped, not merely "PPO returned".
