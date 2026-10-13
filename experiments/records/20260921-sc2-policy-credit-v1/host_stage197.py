"""Opt-in host stage supervision; deliberately no prepare/queue/GPU launch CLI.

run_stages integrates unchanged stage launchers with one host storage owner and
an independent guardian. The future approved queue supplies frozen accounts,
original absolute deadlines, resource/admission gates and acceptance callback.
"""
import argparse
import fcntl
import math
import os
from pathlib import Path
import re
import subprocess
import sys
import time

import acceptance197 as a
import storage_quiescent197 as q
from storage_guardian197 import Guardian


def sample(accounts, lock_root, guardian=None):
    for item in accounts:
        a.measure_budget(item['roots'],Path(item['receipt_root']),item['limit'],item['deadline'],
            'Original absolute deadline; no extension','Inclusive storage quota; no retry',
            lock_root=lock_root,quiesce=None if guardian is None else guardian.quiesce)


def run_stages(stages, command_for, verify, accounts, owner_root, control_root,
               lock_root, deadline, *, admit, interval=15, terminal_intent_for=None,
               finalize=None):
    """One newly allocated container per stage; exit0 AND verifier required.

    command_for(stage) returns docker CREATE argv for one unchanged launcher,
    never an execute/queue controller. All writable mounts and control_root must
    be included by the supplied accounting roots; admission is caller-owned.
    No background sampler, shell, retry, predecessor bypass or new clock here.
    """
    owner_root,control_root,lock_root = map(Path,(owner_root,control_root,lock_root))
    if (terminal_intent_for is None) != (finalize is None):
        raise ValueError('Terminal intent and deferred recorder must be enabled together')
    if Path('/.dockerenv').exists():
        raise RuntimeError('Stage supervisor must run on host')
    if not math.isfinite(deadline) or deadline <= time.time()+45 or not 0 < interval <= 15:
        raise ValueError('Original unexpired deadline and bounded interval required')
    if not stages or len(set(stages)) != len(stages) or any(not re.fullmatch(r'[a-z0-9-]+',s) for s in stages):
        raise ValueError('Unique declared stage names required')
    if (not accounts or any(x['deadline'] is None or not math.isfinite(x['deadline']) for x in accounts)
            or min(x['deadline'] for x in accounts) != deadline):
        raise ValueError('Stage deadline must be the earliest unchanged accounting clock')
    for path in (owner_root,control_root):
        if not path.is_absolute() or not any(path == Path(p) or Path(p) in path.parents for x in accounts for p in x['roots']):
            raise ValueError('All writable supervision roots must be accounted')
    control_root.mkdir()  # Refuse restart/overwrite even before Docker creation.
    with (control_root/'supervisor.lock').open('x') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        state = dict(version='host-guardian-v1',phase='starting',completed=[],deadline=deadline,
                     learning_validated=False,started_at=time.time())
        cid = None
        try:
            for stage in stages:
                def measure(guard):
                    if terminal_intent_for is None:
                        return sample(accounts,lock_root,guard)
                    import storage_batch197
                    return storage_batch197.sample(accounts,lock_root,guard,
                        terminal_intent=terminal_intent_for(stage))
                sample(accounts,lock_root)  # No live stage writer at this boundary.
                admit(stage)  # Caller must recheck resources/fsync for EACH stage.
                if time.time() >= deadline-45:
                    raise TimeoutError('Admission consumed original stage allowance')
                args = command_for(stage)
                if args[:2] != ['docker','create'] or '--rm' in args or '--restart' in args:
                    raise ValueError('Fresh retained one-shot docker create command required')
                label = 'sc2.acceptance.root='+str(owner_root)
                if '--label' not in args or label not in args:
                    raise ValueError('Exact stage ownership label required')
                # No inherited control socket reaches docker/launcher children.
                cid = q.docker(args[1:],time.monotonic()+min(15,deadline-45-time.time())).strip()
                if not re.fullmatch(r'[0-9a-f]{64}',cid):
                    raise RuntimeError('Docker create did not return an immutable ID')
                state.update(phase='running-unverified',stage=stage,container_id=cid)
                a.save(control_root/'state.json',state,lock_root=lock_root)
                with Guardian(cid,owner_root,deadline,control_root/(stage+'-guardian.json'),lock_root) as guard:
                    guard.request('start')
                    while True:
                        guard.request('pulse')
                        status = q.inspect_owned(cid,owner_root,time.monotonic()+min(10,deadline-45-time.time()))
                        if not status['Running']:
                            if status['Paused'] or status['ExitCode'] != 0:
                                raise RuntimeError('Stage container failed; no retry/successor')
                            break
                        measure(guard)
                        guard.request('pulse')
                        remaining = deadline-45-time.time()
                        if remaining <= 0:
                            raise TimeoutError('Original stage deadline reached')
                        time.sleep(min(interval,remaining))
                    guard.finish()
                # Exit0 is not experiment acceptance. The unchanged frozen
                # verifier must validate real outcomes/updates/seed/load/CP.
                sample(accounts,lock_root)
                if finalize is not None:
                    finalize(stage,cid)
                    sample(accounts,lock_root)
                verify(stage)
                sample(accounts,lock_root)  # Verification cannot extend the clock.
                state['completed'].append(stage)
                state.update(phase='stage-completed')
                a.save(control_root/'state.json',state,lock_root=lock_root)
                cid = None
            state.update(phase='completed',exit_code=0,finished_at=time.time())
            a.save(control_root/'state.json',state,lock_root=lock_root)
        except BaseException as exc:
            state.update(phase='failed',error_type=type(exc).__name__,error=str(exc),finished_at=time.time())
            a.save(control_root/'state.json',state,lock_root=lock_root)
            raise
        return state


def finalize_record(cfg, stage, cid, owner, control, deadline):
    """CPU-only recorder after exact exit0 AND completed guardian, never recovery.

No failed/existing run can use this to manufacture a missing result. Frozen
recorder/verification semantics and the original absolute deadline are retained.
"""
    from storage_guardian197 import exited_ok
    owner,control=Path(owner),Path(control)
    proof=a.read(control/(stage+'-guardian.json'))
    if (proof.get('phase')!='completed' or proof.get('container_id')!=cid
            or proof.get('owner_root')!=str(owner) or proof.get('deadline')!=deadline
            or not proof.get('final_state') or not exited_ok(proof['final_state'])):
        raise RuntimeError('Completed exact guardian required before deferred recorder')
    remaining=deadline-45-time.time()
    if remaining<=0: raise TimeoutError('Original finalization deadline expired')
    state=q.inspect_owned(cid,owner,time.monotonic()+min(10,remaining))
    if not exited_ok(state): raise RuntimeError('Deferred recorder requires actual exited0 container')
    out=owner/'runs'/stage
    manifest=a.read(out/'manifest.json')
    if (cfg.get('terminal_handoff')!='terminal-drain-v1'
            or manifest.get('finalization_mode')!='terminal-drain-v1'
            or manifest.get('source_commit')!=cfg['runtime_sha']
            or manifest.get('dirty') is not False):
        raise RuntimeError('Exact frozen opt-in recorder manifest required')
    if any((out/n).exists() for n in ('metrics.json','result.json','.done')):
        raise RuntimeError('Deferred recorder refuses existing result artifacts')
    from terminal_storage197 import validate_intent
    validate_intent(dict(path=out/'terminal-intent.json',
        run_id=cfg['run_prefix']+'-'+stage,source_commit=cfg['runtime_sha']))
    remaining=deadline-45-time.time()
    if remaining<=0: raise TimeoutError('Original finalization deadline expired')
    # Use the run's already-checked frozen runtime, not the development tree.
    subprocess.run([sys.executable,'-B',str(owner/'runtime/scripts/run_record.py'),
        'finish','--output',str(out),'--exit-code','0'],check=True,
        timeout=remaining,stdout=subprocess.DEVNULL)
    if time.time()>=deadline-45: raise TimeoutError('Recorder exceeded original deadline')


def terminal_options(cfg, owner, control, deadline):
    terminal=cfg.get('terminal_handoff')
    if terminal is None:
        return {}
    if terminal!='terminal-drain-v1':
        raise ValueError('Unknown terminal handoff version')
    owner,control=Path(owner),Path(control)
    return dict(terminal_intent_for=lambda stage:dict(
        path=owner/'runs'/stage/'terminal-intent.json',
        run_id=cfg['run_prefix']+'-'+stage,source_commit=cfg['runtime_sha']),
        finalize=lambda stage,cid:finalize_record(cfg,stage,cid,owner,control,deadline))


def terminal_launch(cfg, args, env, lock_root):
    terminal=cfg.get('terminal_handoff')
    if terminal not in (None,'terminal-drain-v1'):
        raise ValueError('Unknown terminal handoff version')
    env.pop('SC2_FINALIZATION_MODE',None)
    if terminal is not None:
        env['SC2_FINALIZATION_MODE']=terminal
        override='+trainer.sc2_terminal_handoff_lock_root='+str(lock_root)
        if override not in args:
            args.append(override)


def docker_stage(index,stage,dry=False):
    """Adapt existing frozen launcher construction; no controller runs inside."""
    import l7_followup197 as f
    cfg = f.select(index)
    if stage not in cfg['stages']:
        raise ValueError('Undeclared stage')
    args = f.docker('cpu' if dry else 'execute',index)
    args[1] = 'create'
    args[args.index('--name')+1] += '-'+stage
    args[-3:] = [str(Path(__file__).resolve()),'stage-dry' if dry else 'stage',str(index),stage,str(f.SUITE)]
    return args


def supervise_part(index,accounts,deadline,admit):
    """Integration boundary for a future separately authorized frozen queue.

    Never call from the old failed queue. This has no allocation/admission
    bypass: the caller supplies the original clocks/roots and per-stage gate.
    """
    import l7_followup197 as f
    cfg = f.select(index)
    if cfg.get('storage_supervision') != 'host-guardian-v1' or (a.ROOT/'state.json').exists():
        raise RuntimeError('New explicit deployment with no prior state required')
    a.clean(Path(cfg['controller_source']),cfg['controller_sha'])
    a.clean(a.ROOT/'runtime',cfg['runtime_sha'])
    def verify(stage):
        for name in ('manifest.json','result.json'):
            if a.read(a.ROOT/'runs'/stage/name).get('metrics_precision') != 'binary64-v1':
                raise RuntimeError('New stage requires full-precision evidence')
        f.verify(stage)  # Native CP2/seed/PPO/actions/load gates unchanged.
    control = a.ROOT/'host-supervision'
    try:
        state = run_stages(cfg['stages'],lambda stage:docker_stage(index,stage),verify,
            accounts,a.ROOT,control,f.SUITE,deadline,admit=admit,
            **terminal_options(cfg,a.ROOT,control,deadline))
    except BaseException:
        if (control/'state.json').exists():
            a.save(a.ROOT/'state.json',a.read(control/'state.json'),lock_root=f.SUITE)
        raise
    a.save(a.ROOT/'state.json',state,lock_root=f.SUITE)
    return state


def child_stage(index,stage,suite,dry):
    import l7_followup197 as f
    f.SUITE = Path(suite)
    cfg = f.select(index)
    if cfg.get('storage_supervision') != 'host-guardian-v1':
        raise RuntimeError('New explicit host-supervised deployment required; old deployments refused')
    a.clean(a.ROOT/'runtime',cfg['runtime_sha'])
    a.clean(Path(cfg['controller_source']),cfg['controller_sha'])
    args,env,out = f.invocation(cfg,stage,dry)
    terminal_launch(cfg,args,env,f.SUITE)
    if not dry and cfg.get('host_stage_entry_log'):
        # With Docker logging disabled, retain early launcher errors inside the
        # accounted part, before the recorder's own console log exists.
        descriptor=os.open(a.ROOT/(stage+'-entry.log'),os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
        os.dup2(descriptor,1);os.dup2(descriptor,2);os.close(descriptor)
    # The exact same launch command/env enters the same recorder/trainer. No
    # execute(), budget(), watchdog or GPU-release loop runs in this container.
    os.chdir(a.ROOT/'runtime')
    os.execvpe(args[0],args,env)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode',choices=['stage','stage-dry'])
    p.add_argument('index',type=int,choices=range(3))
    p.add_argument('stage');p.add_argument('suite')
    v = p.parse_args()
    child_stage(v.index,v.stage,v.suite,v.mode=='stage-dry')
