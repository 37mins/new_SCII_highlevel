"""One authorized new RUN with host-only supervision and original fixed clocks."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import subprocess as sp
import time

import acceptance197 as a
import host_stage197 as h
import l7_followup197 as f
import l7_followup197_r3 as old

ROOT = Path('/var/jfsCache/sc2-l7-followup197-20260922-r4')
SPB_DEADLINE = 1790247962.305692
SUITE_DEADLINE = 1790420762.305692
ORIGINAL_START = 1790075162.305692
RETAINED = [*old.RETAINED, old.ROOT,
    Path('/var/jfsCache/sc2-l7-followup197-source-20260922-r3'),
    Path('/var/jfsCache/sc2-storage-quiescence-cpu-20260922.4LzwSM'),
    Path('/var/jfsCache/sc2-host-supervision-cpu-20260922.7lJiIO')]
BASE_DOCKER = f.docker


def configure():
    f.SUITE = ROOT
    f.RETAINED_PREPARATION = RETAINED
    f.PREDECESSOR = old.e.ROOT
    f.CONTAINER_PREFIX = 'sc2-l7-followup197-20260922-r4-'
    f.RUN_PREFIX = 'l7-followup197-r4-'
    f.DOCKER_SCRIPT = a.HERE/'l7_followup197_r4.py'
    f.docker = docker


def accounts(index, deadline):
    arm = [ROOT/('spb-same' if index < 2 else 'qwen-random'), a.SOURCE.parent, *RETAINED]
    if index == 2:
        arm.append(f.RANDOM_PARENT)
    return [dict(roots=arm,receipt_root=ROOT/f.PARTS[index],limit=1024*a.GIB,deadline=deadline),
        dict(roots=[ROOT,a.SOURCE.parent,f.RANDOM_PARENT,*RETAINED],receipt_root=ROOT,
             limit=2048*a.GIB,deadline=SUITE_DEADLINE)]


def docker(mode,index):
    args = BASE_DOCKER(mode,index)
    # Only selected part/tmp and the stable coordination inode are writable.
    # All source, ancestors, assets and failed preparations stay read-only.
    args[args.index(f'{ROOT}:{ROOT}')] = f'{ROOT}:{ROOT}:ro'
    args[2:2] = ['--read-only','--log-driver','none',
        '-e','HOME=/tmp/task-home','-e','XDG_CACHE_HOME=/tmp/cache',
        '-e','CUDA_CACHE_PATH=/tmp/cuda-cache','-e','TMPDIR=/tmp']
    owner = ROOT/f.PARTS[index]
    writable = []
    for pos,value in enumerate(args[:-1]):
        if value != '-v':
            continue
        spec=args[pos+1].split(':')
        if len(spec)==3 and spec[2]=='ro':
            continue
        source,target=map(Path,spec[:2])
        if (source,target) not in [(owner,owner),(owner/'tmp',Path('/tmp')),
                                  (ROOT/'.storage.lock',ROOT/'.storage.lock')]:
            raise RuntimeError('Unaccounted writable bind refused')
        writable.append(str(source))
    if len(writable)!=3:
        raise RuntimeError('Expected exactly part, tmp and lock writable binds')
    return args


def prepare():
    f.prepare()  # Fresh roots only; existing runtime/records are never changed.
    for root in [ROOT,*[ROOT/p for p in f.PARTS]]:
        cfg=a.read(root/'deployment.json')
        cfg.update(storage_supervision='host-guardian-v1',
            authorization='User: 快按方案续排实验; fresh SpB short+96 then accepted Qwen-random ownCP2+96; '
                'eight prior interrupted pre slots counted, max1560 cumulative dispatch slots; '
                'no GPU-hour or absolute deadline extension, no accepted evaluation replay',
            original_spb_start=ORIGINAL_START,spb_deadline=SPB_DEADLINE,suite_deadline=SUITE_DEADLINE,
            prior_interrupted_slots=8,cumulative_dispatch_slots=1560,
            host_stage_entry_log=True,container_rootfs_read_only=True,
            all_writer_contract='One fresh stage container; all persistent writable binds in exact accounting; '
                'host metadata shares stable lock; detached guardian terminal inode never renamed; '
                'old containers stopped and retained roots immutable; no nested watchdog',
            operational_limit='Whole-container quiescence counts toward wall clock; GPU/SC2/Ray/NCCL timing unverified')
        a.save(root/'deployment.json',cfg,lock_root=ROOT)
    for part in f.PARTS:
        for name in ('task-home','cache','cuda-cache'):
            (ROOT/part/'tmp'/name).mkdir()


def check_cpu():
    cfg=a.read(ROOT/'deployment.json')
    a.clean(a.SOURCE,cfg['controller_sha']);a.clean(ROOT/'runtime',cfg['runtime_sha']);a.clean(a.ORCH,a.ORCH_SHA)
    for name in ('regressions.json','host-regressions.json'):
        proof=a.read(ROOT/f.PARTS[0]/name)
        if not proof['passed'] or proof['skips'] or proof['runtime_sha']!=cfg['runtime_sha']:
            raise RuntimeError('Complete zero-skip CPU regressions required')
    for part in f.PARTS:
        proof=a.read(ROOT/part/'readiness.json')
        if not proof['passed'] or proof['cuda_initialized'] or proof['runtime_sha']!=cfg['runtime_sha']:
            raise RuntimeError('All seven actual launcher/Hydra stages required')


def admit(index,stage,deadline):
    part=ROOT/f.PARTS[index]
    f.previous.ROOT=part
    while True:
        if time.time()>=deadline-45:
            raise TimeoutError('Original cutoff reached while waiting resources')
        h.sample(accounts(index,deadline),ROOT)
        writers_clear(accounts(index,deadline)[1]['roots'])
        if f.previous.resources_ready():
            break
        a.save(ROOT/'queue-state.json',dict(phase='waiting-resources',part=f.PARTS[index],
            stage=stage,deadline=SUITE_DEADLINE,arm_deadline=deadline),lock_root=ROOT)
        time.sleep(min(30,max(0,deadline-45-time.time())))
    probe=part/('fsync-'+stage)
    with probe.open('xb') as stream:
        stream.write(b'l7-r4\n');stream.flush();os.fsync(stream.fileno())
    if probe.read_bytes()!=b'l7-r4\n':
        raise RuntimeError('Fsync readback failed')
    a.save(part/('admission-'+stage+'.json'),dict(passed=True,checked_at=time.time(),
        deadline=deadline,eight_idle_gpus=True,ram_gib_min=600,nvme_gib_min=1084,fsync=True),lock_root=ROOT)


def writers_clear(roots):
    """Admission only: no stage is live yet; refuse any active bind writer."""
    ids=a.cmd(['docker','ps','-q','--no-trunc']).splitlines()
    for cid in ids:
        mounts=json.loads(a.cmd(['docker','inspect','--format','{{json .Mounts}}',cid]))
        for mount in mounts:
            if not mount.get('RW') or not mount.get('Source'):
                continue
            source=Path(mount['Source']).resolve()
            if any(source==Path(p).resolve() or source in Path(p).resolve().parents
                   or Path(p).resolve() in source.parents for p in roots):
                raise RuntimeError('Active container writes an accounted root; no adoption or stop')


def queue():
    check_cpu()
    with (ROOT/'queue.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (ROOT/'queue-state.json').exists() or (ROOT/'dispatch.json').exists():
            raise RuntimeError('Already queued/dispatched; no retry')
        state=dict(phase='checking-predecessor',completed=[],deadline=SUITE_DEADLINE,
                   original_start=ORIGINAL_START,spb_deadline=SPB_DEADLINE)
        try:
            a.save(ROOT/'queue-state.json',state,lock_root=ROOT)
            if not old.predecessor_complete():
                raise RuntimeError('Previously accepted CP96-only evaluation not terminal')
            # Static retained writers must be stopped. Never stop/adopt these jobs.
            for name in ('sc2-l7-followup197-20260922-r3-spb-same-short',):
                status=json.loads(a.cmd(['docker','inspect','--format','{{json .State}}',name]))
                if status['Running'] or status['Paused']:
                    raise RuntimeError('Retained writer is active; refuse continuation')
            a.save(ROOT/'predecessor-acceptance.json',dict(passed=True,root=str(old.e.ROOT),
                checked_at=time.time(),accepted_evaluation_not_replayed=True),lock_root=ROOT)
            a.save(ROOT/'dispatch.json',dict(start=ORIGINAL_START,resumed_at=time.time(),
                deadline=SUITE_DEADLINE,original_clock_preserved=True,gpu_hours=768),lock_root=ROOT)
            for index,part in enumerate(f.PARTS):
                f.select(index)
                if index==1:
                    a.save(a.ROOT/'resume-contract.json',f.contract_for(1),lock_root=ROOT)
                    with (a.ROOT/'parent-cpu.log').open('x') as log:
                        sp.run(docker('parent-cpu',1),stdout=log,stderr=sp.STDOUT,check=True,
                               timeout=min(600,SPB_DEADLINE-45-time.time()))
                    if not a.read(a.ROOT/'parent-readiness.json')['actual_parent_verified']:
                        raise RuntimeError('Native SpB parent not verified')
                elif index==2:
                    f.verify_contract(a.read(a.ROOT/'resume-contract.json'))
                deadline=SPB_DEADLINE if index<2 else min(time.time()+f.ARM_SECONDS,SUITE_DEADLINE)
                # Qwen clock begins at its first admission, not a refreshed clock for eval.
                admit(index,'part',deadline)
                if index==2:
                    deadline=min(time.time()+f.ARM_SECONDS,SUITE_DEADLINE)
                a.save(a.ROOT/'dispatch.json',dict(start=ORIGINAL_START if index<2 else time.time(),
                    resumed_at=time.time(),deadline=deadline,host_supervision=True),lock_root=ROOT)
                state.update(phase='running-unverified',part=part,arm_deadline=deadline)
                a.save(ROOT/'queue-state.json',state,lock_root=ROOT)
                h.supervise_part(index,accounts(index,deadline),deadline,
                    lambda stage:admit(index,stage,deadline))
                for stage in a.read(a.ROOT/'deployment.json')['stages']:
                    old.verify(stage,write=False)
                state['completed'].append(part)
                state['phase']='part-completed'
                a.save(ROOT/'queue-state.json',state,lock_root=ROOT)
            state.update(phase='completed',exit_code=0,learning_validated=False)
            a.save(ROOT/'queue-state.json',state,lock_root=ROOT)
        except BaseException as exc:
            state.update(phase='failed',error_type=type(exc).__name__,error=str(exc))
            a.save(ROOT/'queue-state.json',state,lock_root=ROOT)
            raise


def host_regressions():
    import unittest
    import sys
    sys.path.insert(0,str(a.SOURCE/'tests'))
    names=['test_l7_host_continuation197','test_host_stage197','test_storage_quiescent197',
           'test_policy_credit_storage197','test_policy_credit_storage_coordination197']
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromNames(names))
    proof=dict(passed=result.wasSuccessful() and not result.skipped,tests=result.testsRun,
        skips=len(result.skipped),runtime_sha=a.read(ROOT/'deployment.json')['runtime_sha'],checked_at=time.time())
    a.save(ROOT/f.PARTS[0]/'host-regressions.json',proof,lock_root=ROOT)
    if not proof['passed']:
        raise RuntimeError('Host continuation regressions failed')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',choices=['prepare','queue','cpu-command','regressions-command',
        'host-regressions','cpu','regressions','parent-cpu'])
    parser.add_argument('index',type=int,nargs='?',choices=range(3))
    args=parser.parse_args();configure()
    if args.mode in ('prepare','queue','host-regressions'):
        globals()[args.mode.replace('-','_')]()
    elif args.index is None:parser.error('Part index required')
    elif args.mode.endswith('-command'):print(json.dumps(docker(args.mode.removesuffix('-command'),args.index)))
    elif args.mode=='cpu':f.cpu(args.index)
    elif args.mode=='regressions':f.regressions(args.index)
    else:f.parent_cpu(args.index)
