"""Opt-in CPU candidate: one strict du sample with the owned container frozen.

No launcher uses this candidate yet. Call from the host, never inside the target
container. The caller must establish that all other counted roots are immutable
and every active non-controller writer belongs to this one container. See
storage-quiescence-fix.md for the remaining GPU-integration gate.
"""
from contextlib import contextmanager
from functools import partial
from pathlib import Path
import re
import subprocess
import time

import acceptance197 as a


def docker(args, until):
    remaining = until - time.monotonic()
    if remaining <= 0:
        raise TimeoutError('Owned-container storage allowance exhausted')
    result = subprocess.run(['docker', *args], text=True, capture_output=True,
                            timeout=remaining, check=False)
    if result.returncode or result.stderr:
        raise RuntimeError('Owned-container command failed: ' + str(args[0]) + ': '
                           + a.storage_output(result.stderr)['tail'])
    return result.stdout


def inspect_owned(container_id, owner_root, until):
    import json
    # Deliberately omit environment, command, credentials and unrelated fields.
    template = ('{"id":{{json .Id}},"labels":{{json .Config.Labels}},'
                '"state":{{json .State}}}')
    value = json.loads(docker(['inspect', '--format', template, container_id], until))
    if (value['id'] != container_id or
            (value.get('labels') or {}).get('sc2.acceptance.root') != str(owner_root)):
        raise RuntimeError('Container identity/ownership mismatch; refusing pause/unpause')
    return value['state']


@contextmanager
def paused_owned(container_id, owner_root, until, proof):
    evidence = proof['quiescence'] = dict(version='owned-container-pause-v1',
        container_id=container_id, owner_root=str(owner_root), pause_attempted=False,
        paused_verified=False, cleanup='not-needed')
    before = inspect_owned(container_id, owner_root, until)
    if not before['Running'] or before['Paused'] or before.get('Restarting') or before.get('Dead'):
        raise RuntimeError('Expected owned running, unpaused container; refusing state takeover')
    evidence['initial_state'] = before
    # A timed-out pause may have reached the daemon. Always inspect/restore the
    # pinned ID after ANY attempted pause, including an interrupted client call.
    evidence['pause_attempted'] = True
    try:
        docker(['pause', container_id], until)
        paused = inspect_owned(container_id, owner_root, until)
        if not paused['Running'] or not paused['Paused']:
            raise RuntimeError('Docker did not confirm quiescence; du forbidden')
        evidence.update(paused_verified=True, paused_at=time.time())
        yield
    finally:
        # Bounded recovery only, never more sampling or extra experiment time.
        # At most 10s of the existing 45s terminal-cleanup reserve is used.
        cleanup_until = time.monotonic() + 10
        try:
            state = inspect_owned(container_id, owner_root, cleanup_until)
            if state['Paused']:
                docker(['unpause', container_id], cleanup_until)
                state = inspect_owned(container_id, owner_root, cleanup_until)
            if state['Paused']:
                raise RuntimeError('Owned container remains paused; operator recovery required')
            evidence.update(cleanup='verified-unpaused', resumed_at=time.time(), final_state=state)
            if not state['Running']:
                raise RuntimeError('Owned container exited during sample; no acceptance')
        except BaseException as exc:
            evidence.update(cleanup='failed', cleanup_error_type=type(exc).__name__,
                            cleanup_error=str(exc))
            raise


def measure_owned_budget(container_id, owner_root, roots, receipt_root, limit, deadline,
                         time_error, size_error, *, lock_root):
    """One inclusive sample; no filter, exclusion, retry or last-good fallback.

    Inputs are explicit immutable Docker ID, ownership label root, exact storage
    roots, original quota/deadline and shared metadata lock. Output is the existing
    storage-state/failure receipt, augmented with pause and restoration evidence.
    """
    if not re.fullmatch(r'[0-9a-f]{64}', container_id):
        raise ValueError('Full immutable Docker ID required, not a reusable container name')
    owner_root, roots = Path(owner_root), list(map(Path, roots))
    if not owner_root.is_absolute() or not any(owner_root == p or p in owner_root.parents for p in roots):
        raise ValueError('Owned writable root must be covered by the exact accounting roots')
    if Path('/.dockerenv').exists():
        raise RuntimeError('Host-only sampler; never pause the container running this sampler')
    a.measure_budget(roots, Path(receipt_root), limit, deadline, time_error, size_error,
        lock_root=Path(lock_root), quiesce=partial(paused_owned, container_id, owner_root))
