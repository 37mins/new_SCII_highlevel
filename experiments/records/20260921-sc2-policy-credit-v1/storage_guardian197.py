"""Host-only per-stage guardian. No queue, GPU allocation or experiment defaults.

The guardian alone starts/pauses/resumes the newly created, exact-ID container.
EOF, missed lease, pause timeout or stage deadline restores and stops that owned
container. The supervisor never delegates an in-container storage watchdog.
"""
import argparse
from contextlib import contextmanager
import json
import math
import os
from pathlib import Path
import re
import socket
import subprocess
import sys
import time

import acceptance197 as a
import storage_quiescent197 as q


def valid_identity(cid, owner):
    if not re.fullmatch(r'[0-9a-f]{64}', cid) or not Path(owner).is_absolute():
        raise ValueError('Exact immutable ID and absolute owned root required')
    if Path('/.dockerenv').exists():
        raise RuntimeError('Guardian and supervisor must run on host')


def receive(stream):
    line = stream.readline(8193)
    if not line:
        raise EOFError('Supervisor disconnected')
    if len(line) > 8192 or not line.endswith(b'\n'):
        raise ValueError('Invalid bounded guardian message')
    return json.loads(line)


def send(sock, value):
    sock.sendall((json.dumps(value, allow_nan=False) + '\n').encode())


def exited_ok(state):
    return (state.get('Status') == 'exited' and not state['Running']
            and not state['Paused'] and state['ExitCode'] == 0)


def recover(cid, owner, pause_attempted, until):
    """One restore and one stop attempt, then inspect; no name/kill/retry fallback."""
    evidence = dict(errors=[])
    state = q.inspect_owned(cid, owner, until)
    if state['Paused']:
        if not pause_attempted:
            raise RuntimeError('Foreign/pre-existing pause; operator recovery required')
        try:
            q.docker(['unpause', cid], min(until, time.monotonic()+10))
        except (OSError, RuntimeError, subprocess.TimeoutExpired) as exc:
            evidence['errors'].append(dict(operation='unpause', error=str(exc)))
    # A failed unpause must not skip the single owned stop attempt.
    state = q.inspect_owned(cid, owner, until)
    if state['Running']:
        try:
            q.docker(['stop', '--time', '10', cid], min(until, time.monotonic()+20))
        except (OSError, RuntimeError, subprocess.TimeoutExpired) as exc:
            evidence['errors'].append(dict(operation='stop', error=str(exc)))
    state = q.inspect_owned(cid, owner, until)
    evidence.update(state=state, stopped_verified=not state['Running'] and not state['Paused'])
    return evidence


def serve(sock, cid, owner, deadline, receipt, lock_root, lease_seconds=45):
    valid_identity(cid, owner)
    if (not math.isfinite(deadline) or not 0 < lease_seconds <= 45
            or deadline-45 <= time.time()):
        raise ValueError('Invalid/expired original deadline or guardian lease')
    receipt = Path(receipt)
    if receipt.exists():
        raise RuntimeError('New guardian receipt required; no overwrite/restart')
    # Create once BEFORE start/du. Terminal publication writes this same inode,
    # without rename/unlink or a lock the lost supervisor may still hold. Empty
    # or partial content is never success; caller waits for guardian exit first.
    terminal = receipt.open('x')
    proof = dict(version='host-guardian-v1', container_id=cid, owner_root=str(owner),
        deadline=deadline, lease_seconds=lease_seconds, phase='starting', events=[],
        pause_attempted=False, started_at=time.time())
    controlled = success = False
    stop_at = time.monotonic() + deadline-45-time.time()
    lease_at = min(stop_at, time.monotonic()+lease_seconds)
    pause_at = None
    try:
        initial = q.inspect_owned(cid, owner, min(stop_at,time.monotonic()+10))
        # Never adopt an already-started, previously-exited or pre-paused job.
        if initial.get('Status') != 'created' or initial['Running'] or initial['Paused']:
            raise RuntimeError('Guardian requires a newly created, never started container')
        controlled = True
        proof['initial_state'] = initial
        send(sock, dict(ok=True, event='ready'))
        with sock.makefile('rb') as stream:
            while True:
                until = min(stop_at, lease_at, pause_at if pause_at is not None else stop_at)
                remaining = until-time.monotonic()
                if remaining <= 0:
                    raise TimeoutError('Guardian lease/pause/original stage deadline exhausted')
                sock.settimeout(remaining)
                request = receive(stream)
                op = request['op']
                details = {}
                proof['pending_operation'] = dict(op=op, at=time.time())
                if op == 'start':
                    if proof['phase'] != 'starting':
                        raise RuntimeError('Stage start is one-shot')
                    q.docker(['start', cid], until)
                    proof['phase'] = 'running'
                elif op == 'pause':
                    requested = float(request['until'])
                    if (proof['phase'] != 'running' or pause_at is not None
                            or not math.isfinite(requested) or requested <= time.monotonic()
                            or requested > min(stop_at,time.monotonic()+15)):
                        raise RuntimeError('Invalid or duplicate bounded pause request')
                    state = q.inspect_owned(cid, owner, min(until,requested))
                    if exited_ok(state):
                        details['quiescence'] = 'exited-zero'
                    elif not state['Running'] or state['Paused'] or state.get('Restarting') or state.get('Dead'):
                        raise RuntimeError('Stage not running/unpaused at sampling boundary')
                    else:
                        proof['pause_attempted'] = True  # Before an ambiguous daemon call.
                        pause_at = min(until, requested)
                        try:
                            q.docker(['pause', cid], pause_at)
                        except RuntimeError as exc:
                            # A stage may exit between inspect and pause. Settle
                            # by one exact-ID terminal observation, never retry.
                            details['pause_command_error'] = str(exc)
                            proof['pending_operation'].update(details)
                        state = q.inspect_owned(cid, owner, pause_at)
                        proof['pending_operation']['observed_state'] = state
                        if exited_ok(state):
                            pause_at = None
                            details['quiescence'] = 'exited-zero'
                        elif state['Running'] and state['Paused'] and 'pause_command_error' not in details:
                            details['quiescence'] = 'paused'
                        else:
                            raise RuntimeError('Pause not verified; measurement forbidden')
                elif op == 'resume':
                    if pause_at is None:
                        raise RuntimeError('No active owned pause')
                    q.docker(['unpause', cid], until)
                    state = q.inspect_owned(cid, owner, until)
                    if state['Paused'] or (not state['Running'] and not exited_ok(state)):
                        raise RuntimeError('Resume not verified')
                    details['quiescence'] = 'exited-zero' if exited_ok(state) else 'running'
                    pause_at = None
                elif op == 'pulse':
                    if pause_at is not None:
                        raise RuntimeError('Pulse cannot extend a pause allowance')
                elif op == 'finish':
                    if pause_at is not None or proof['phase'] != 'running':
                        raise RuntimeError('Cannot finish while paused or before start')
                    state = q.inspect_owned(cid, owner, until)
                    if state['Running'] or state['Paused'] or state['ExitCode'] != 0:
                        raise RuntimeError('Stage container has not exited successfully')
                    proof.update(phase='completed', final_state=state)
                    success = True
                    break
                else:
                    raise ValueError('Unknown guardian operation')
                now = time.monotonic()
                if now >= until:
                    raise TimeoutError('Guardian operation exceeded original allowance')
                proof['events'].append(dict(op=op, at=time.time(), **details))
                proof.pop('pending_operation', None)
                # A pulse extends only the liveness lease, never either deadline.
                lease_at = min(stop_at, now+lease_seconds)
                send(sock, dict(ok=True, event=op, at=time.time(), **details))
    except BaseException as exc:
        proof.update(phase='failed', error_type=type(exc).__name__, error=str(exc))
        # Notify BEFORE bounded recovery; otherwise a 10s stop masks the
        # original pause failure as a supervisor socket timeout.
        try:
            send(sock,dict(ok=False,event='failed',error_type=type(exc).__name__,error=str(exc),
                           operation=proof.get('pending_operation')))
        except OSError:
            pass
    finally:
        if controlled and not success:
            try:
                proof['recovery'] = recover(cid, owner, proof['pause_attempted'], time.monotonic()+35)
            except BaseException as exc:
                proof['recovery'] = dict(stopped_verified=False,error_type=type(exc).__name__,error=str(exc))
        proof['finished_at'] = time.time()
        # No rename means no disappearing entry for the sampler. Normal finish
        # is followed by a complete static sample; on failure nothing is accepted.
        # Cleanup does not depend on the supervisor's metadata lock.
        try:
            json.dump(proof,terminal,allow_nan=False)
            terminal.flush();os.fsync(terminal.fileno())
        except BaseException as exc:
            success = False
            print(json.dumps(dict(guardian_failure=proof,receipt_error=str(exc))), file=sys.stderr, flush=True)
        finally:
            terminal.close()
        try:
            send(sock,dict(ok=success,event='finish' if success else 'failed',receipt=str(receipt)))
        except OSError:
            pass  # EOF is expected after supervisor loss; receipt is retained.
        sock.close()
    return 0 if success else 1


class Guardian:
    """Detached guardian with a close-on-exec liveness socket, not a PID guess."""
    def __init__(self, cid, owner, deadline, receipt, lock_root, *, lease_seconds=45):
        valid_identity(cid, owner)
        self.cid, self.owner = cid, Path(owner)
        self.deadline, self.receipt, self.lock_root = deadline, Path(receipt), Path(lock_root)
        self.lease_seconds = lease_seconds
        self.finished = False
        self.pause_attempted = False
        self.armed = False

    def __enter__(self):
        self.sock, child = socket.socketpair()
        self.sock.settimeout(12)
        self.stream = self.sock.makefile('rb')
        args = [sys.executable,'-B',__file__,str(child.fileno()),self.cid,str(self.owner),
                str(self.deadline),str(self.receipt),str(self.lock_root),str(self.lease_seconds)]
        try:
            self.process = subprocess.Popen(args,pass_fds=(child.fileno(),),start_new_session=True)
        finally:
            child.close()
        try:
            if receive(self.stream) != dict(ok=True,event='ready'):
                raise RuntimeError('Guardian was not armed')
            self.armed = True
        except BaseException:
            self.__exit__(*sys.exc_info())
            raise
        return self

    def request(self, op, *, until=None):
        allowance = min(12, self.deadline-45-time.time()) if until is None else until-time.monotonic()
        if allowance <= 0:
            raise TimeoutError('Original guardian request allowance exhausted')
        self.sock.settimeout(allowance)
        value = dict(op=op)
        if until is not None:
            value['until'] = until
        send(self.sock,value)
        result = receive(self.stream)
        if not result.get('ok') or result.get('event') != op:
            raise RuntimeError('Guardian rejected operation: '+op+': '+json.dumps(result,allow_nan=False))
        return result

    @contextmanager
    def quiesce(self, until, proof):
        evidence = proof['quiescence'] = dict(version='host-guardian-v1',container_id=self.cid,
            owner_root=str(self.owner),guardian_pid=self.process.pid,paused_verified=False,cleanup='pending')
        self.pause_attempted = True
        exited = False
        acknowledged = False
        try:
            result = self.request('pause',until=until)
            acknowledged = True
            exited = result.get('quiescence') == 'exited-zero'
            evidence.update(paused_verified=not exited,paused_at=result['at'],mode=result.get('quiescence'))
            if 'pause_command_error' in result:
                evidence['pause_command_error'] = result['pause_command_error']
            yield
        finally:
            try:
                if not acknowledged:
                    # Pause may have reached Docker, but the socket state is
                    # ambiguous. EOF/guardian recovery owns unpause+stop; do
                    # not send another request or mask the first exception.
                    evidence.update(cleanup='guardian-recovery-required')
                elif exited:
                    evidence.update(cleanup='verified-exited-zero')
                else:
                    result = self.request('resume',until=until)
                    evidence.update(cleanup='verified-exited-zero' if result.get('quiescence')=='exited-zero'
                                    else 'verified-unpaused',resumed_at=result['at'])
            except BaseException as exc:
                evidence.update(cleanup='guardian-recovery-required',error_type=type(exc).__name__,error=str(exc))
                raise

    def finish(self):
        self.request('finish')
        self.process.wait(timeout=3)
        proof = a.read(self.receipt)
        if self.process.returncode != 0 or proof['phase'] != 'completed':
            raise RuntimeError('Guardian terminal acceptance failed')
        self.finished = True

    def __exit__(self, *exc):
        self.stream.close()
        self.sock.close()  # EOF releases the guardian even if the parent was killed.
        if not self.finished:
            cleanup_until = time.monotonic()+40  # Within existing 45s reserve.
            try:
                self.process.wait(timeout=36)
            finally:
                if self.armed:
                    status = recover(self.cid,self.owner,self.pause_attempted,cleanup_until)
                    if not status['stopped_verified']:
                        raise RuntimeError('Guardian recovery unverified; operator action required')
        # If the guardian itself failed, do not leave this stage running. This
        # fallback never adopts pre-existing jobs: guardian's ready handshake
        # and the supervisor's created-ID check precede any call to start.
        return False


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('fd',type=int)
    parser.add_argument('cid');parser.add_argument('owner');parser.add_argument('deadline',type=float)
    parser.add_argument('receipt');parser.add_argument('lock_root');parser.add_argument('lease',type=float)
    args = parser.parse_args()
    sys.exit(serve(socket.socket(fileno=args.fd),args.cid,Path(args.owner),args.deadline,
                   Path(args.receipt),Path(args.lock_root),args.lease))
