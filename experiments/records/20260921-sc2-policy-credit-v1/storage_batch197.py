"""Opt-in: all exact quota traversals under one verified pause and one 15s budget.

The old single-account sampler and old frozen runs are unchanged. All writers
must belong to the exact guardian container or hold the shared metadata lock;
other accounted roots must be immutable. A failed batch publishes no success.
"""
from contextlib import nullcontext
from pathlib import Path
import math
import subprocess as sp
import time

import acceptance197 as a


def sample(accounts, lock_root, guardian=None, *, terminal_intent=None):
    if not accounts or any(not math.isfinite(x['deadline']) for x in accounts):
        raise ValueError('Explicit finite account deadlines required')
    started=time.time();deadline=min(x['deadline'] for x in accounts)
    allowance=min(15,deadline-45-started)
    if allowance<=0: raise TimeoutError('Original absolute deadline; no extension')
    until=time.monotonic()+allowance
    batch=dict(version='terminal-drain-batch-v1' if terminal_intent else 'single-pause-batch-v1',started_at=started,deadline=deadline,
               bytes=None,status='measurement-failed',samples=[])
    current=None
    try:
        # Acquire BEFORE freezing: a container holding a shared lock must be
        # allowed to release it. No metadata publication during any traversal.
        with a.storage_guard(lock_root,exclusive=True,timeout=allowance):
            if guardian is not None and terminal_intent is not None:
                import terminal_storage197
                quiet=terminal_storage197.quiesce(guardian,terminal_intent,until,batch)
            else:
                quiet=nullcontext() if guardian is None else guardian.quiesce(until,batch)
            with quiet:
                for item in accounts:
                    roots=list(map(str,item['roots']))
                    if not roots or len(roots)!=len(set(roots)) or item['limit']<=0:
                        raise ValueError('Unique exact roots and positive quota required')
                    args=['du','-sb','--null','--',*roots]
                    current=dict(command=args,roots=roots,deadline=item['deadline'],limit=item['limit'],
                        bytes=None,returncode=None,stdout=a.storage_output(''),stderr=a.storage_output(''))
                    batch['samples'].append(current)
                    remaining=until-time.monotonic()
                    if remaining<=0: raise TimeoutError('Original batch allowance exhausted')
                    result=sp.run(args,capture_output=True,text=True,encoding='utf-8',errors='replace',
                        env=dict(a.os.environ,LC_ALL='C'),timeout=remaining,check=False)
                    current.update(returncode=result.returncode,stdout=a.storage_output(result.stdout),
                                   stderr=a.storage_output(result.stderr),measured_at=time.time())
                    if result.returncode or result.stderr:
                        raise ValueError('du failed or emitted diagnostics; no partial totals')
                    rows=result.stdout.split('\0');sizes={}
                    if len(rows)!=len(roots)+1 or rows[-1]!='':
                        raise ValueError('All exact terminated root records required')
                    for row in rows[:-1]:
                        count,separator,path=row.partition('\t')
                        if (not separator or not count.isascii() or not count.isdecimal()
                                or path not in roots or path in sizes):
                            raise ValueError('du root identity or byte count mismatch')
                        sizes[path]=int(count)
                    if set(sizes)!=set(roots): raise ValueError('du omitted a required root')
                    current.update(bytes=sum(sizes.values()),root_bytes=sizes)
                    if current['bytes']>=item['limit']:
                        raise RuntimeError('Inclusive storage quota exceeded; no retry')
            if time.monotonic()>=until or time.time()>=deadline-45:
                raise TimeoutError('Original pause/measurement/recovery allowance exceeded')
        # A success is visible only after EVERY account and unpause passed.
        checked=time.time()
        for item,proof in zip(accounts,batch['samples']):
            proof.update(status='measured',started_at=started,checked_at=checked,
                         sampling_version=batch['version'],batch_accounts=len(accounts))
            if 'quiescence' in batch: proof['quiescence']=batch['quiescence']
            a.save(Path(item['receipt_root'])/'storage-state.json',proof,lock_root=lock_root)
    except (OSError,sp.TimeoutExpired,ValueError,RuntimeError) as exc:
        if isinstance(exc,sp.TimeoutExpired) and current is not None:
            current['exception_output']=dict(stdout=a.storage_output(exc.stdout),stderr=a.storage_output(exc.stderr))
        batch.update(error_type=type(exc).__name__,error=str(exc),checked_at=time.time())
        receipt=a.storage_failure(batch,Path(accounts[-1]['receipt_root']),lock_root)
        raise RuntimeError('Storage batch failed; no retry; '+receipt) from exc
