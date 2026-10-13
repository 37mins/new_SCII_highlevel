"""Own-r3 host-only latest2+validation-best; never scan or prune old runs.

Keep native serialization unchanged. Raw trainer output is unpublished to this
controller until stage exit0, full acceptance, small-state validation and fsync.
Only then atomically publish a manifest. No reader/pruner uses partial output.
For the approved four-point schedule, the only possible deletion is own CP32.
"""
import json
import os
from pathlib import Path
import stat
import time

import acceptance197 as a
import l7_matrix256197 as receipts
from agent_system.sc2_policy_resume import checkpoint_names, sha256
from qwen_l8random_plan import ROOT, PARTS, SELECTION_ROOT, SAVED_STEPS, SELECTION_ARMS, SELECTION_STAGES
from qwen_l8random_plan import SELECTION_CHECKPOINTS, SELECTION_SEEDS, SELECTION_SHA256


def fsync_directory(path):
    fd=os.open(path,os.O_RDONLY|os.O_DIRECTORY)
    try: os.fsync(fd)
    finally: os.close(fd)


def atomic(path,value):
    a.atomic_save(path,value)
    fsync_directory(Path(path).parent)


def inventory(cp):
    cp=Path(cp)
    if cp not in SELECTION_CHECKPOINTS.values() or not cp.is_relative_to(ROOT):
        raise ValueError('Only exact new-run checkpoints')
    for p in [cp,*cp.parents]:
        if p.is_symlink(): raise ValueError('Symlink checkpoint ancestor')
        if p==ROOT: break
    if cp.resolve()!=cp: raise ValueError('Noncanonical checkpoint path')
    names={}
    for p in sorted(cp.rglob('*')):
        st=p.lstat()
        if stat.S_ISLNK(st.st_mode) or not (stat.S_ISDIR(st.st_mode) or stat.S_ISREG(st.st_mode)):
            raise ValueError('Only regular checkpoint files/directories')
        if stat.S_ISREG(st.st_mode):
            if st.st_size<=0: raise ValueError('Empty checkpoint file')
            names[str(p.relative_to(cp))]=dict(bytes=st.st_size,
                sha256=sha256(p) if st.st_size<1024**2 else None)
    if not set(checkpoint_names())<=names.keys(): raise ValueError('Incomplete native checkpoint')
    return names


def publish(index):
    owner=ROOT/PARTS[index];stage='train2' if index==0 else 'train96'
    accepted=a.read(owner/f'acceptance-{stage}.json')
    result=a.read(owner/f'runs/{stage}/result.json')
    ready=a.read(owner/'checkpoint-readiness.json')
    sha=a.read(ROOT/'deployment.json')['runtime_sha']
    steps=[2] if index==0 else [32,64,96]
    if (accepted['result']!=result or result!=a.read(owner/f'runs/{stage}/.done')
            or result['process_exit_code']!=0 or result['status']!='completed'
            or not ready['passed'] or ready['cuda_initialized'] or ready['runtime_sha']!=sha
            or ready['steps']!=steps):
        raise RuntimeError('Accepted stage and actual native-state gate required')
    receipts.terminal_container(owner,stage,a.read(owner/'dispatch.json')['deadline'])
    directory=ROOT/'retention';directory.mkdir(exist_ok=True)
    with a.storage_guard(ROOT,exclusive=True):
        for step in steps:
            target=directory/f'cp{step}.json'
            if target.exists(): raise RuntimeError('Checkpoint already published; no retry')
            cp=SELECTION_CHECKPOINTS['cp'+str(step)];files=inventory(cp)
            for name in checkpoint_names():
                prior=ready['inventory'][f'checkpoints/global_step_{step}/'+name]
                current=files[name]
                if prior['bytes']!=current['bytes'] or (prior['sha256'] is not None and prior['sha256']!=current['sha256']):
                    raise RuntimeError('Native validation inventory changed')
            for rel in files:
                fd=os.open(cp/rel,os.O_RDONLY|os.O_NOFOLLOW)
                try: os.fsync(fd)
                finally: os.close(fd)
            for p in [*sorted((x for x in cp.rglob('*') if x.is_dir()),reverse=True),cp]: fsync_directory(p)
            atomic(target,dict(version='accepted-native-publication-v1',step=step,checkpoint=str(cp),
                runtime_sha=sha,files=files,acceptance_sha256=sha256(owner/f'acceptance-{stage}.json'),
                readiness_sha256=sha256(owner/'checkpoint-readiness.json'),
                published_after_stage_exit_and_verification=True,checked_at=time.time()))
            atomic(directory/'latest.json',dict(step=step,checkpoint=str(cp),publication=str(target)))


def require_published(steps=SAVED_STEPS):
    for step in steps:
        cp=SELECTION_CHECKPOINTS['cp'+str(step)];p=a.read(ROOT/f'retention/cp{step}.json')
        if (p['step']!=step or p['checkpoint']!=str(cp)
                or p['runtime_sha']!=a.read(ROOT/'deployment.json')['runtime_sha']
                or p['files']!=inventory(cp)):
            raise RuntimeError('Unpublished or changed native checkpoint')


def score(arm):
    if arm not in SELECTION_ARMS: raise ValueError('Selection candidates only')
    wins=0;digests={}
    for batch in range(4):
        stage=f'b{batch:02d}-{arm}';owner=SELECTION_ROOT;out=owner/'runs'/stage
        accepted=a.read(owner/f'acceptance-{stage}.json');result=a.read(out/'result.json')
        outcomes=result['episode_outcomes']
        if (result!=accepted['result'] or result!=a.read(out/'.done')
                or result['status']!='completed' or result['process_exit_code']!=0
                or result['training_updates']!=0 or outcomes['natural_games']!=8 or outcomes['truncated']
                or accepted['seeds']!=SELECTION_SEEDS[batch*8:batch*8+8]
                or type(outcomes['wins']) is not int or not 0<=outcomes['wins']<=8):
            raise RuntimeError('Exactly32 accepted natural validation outcomes required')
        wins+=outcomes['wins'];digests[stage]=sha256(owner/f'acceptance-{stage}.json')
    return dict(step=int(arm[2:]),wins=wins,games=32,seed_sha256=SELECTION_SHA256,receipts=digests)


def update_best(arm):
    candidates=SELECTION_ARMS[:SELECTION_ARMS.index(arm)+1]
    scored=[score(x) for x in candidates]
    best=max(scored,key=lambda x:(x['wins'],-x['step']))
    with a.storage_guard(ROOT,exclusive=True):
        atomic(ROOT/'retention/best.json',dict(best=best,scored=scored,
            checkpoint=str(SELECTION_CHECKPOINTS['cp'+str(best['step'])]),
            metric='independent validation32 wins; ties retain earlier step',test_used=False,checked_at=time.time()))


def retained_steps(best):
    if best not in SAVED_STEPS: raise ValueError('Undeclared best checkpoint')
    return sorted(set(SAVED_STEPS[-2:])|{2,96,best})


def readers_clear():
    for cid in a.cmd(['docker','ps','-q','--no-trunc']).splitlines():
        for mount in json.loads(a.cmd(['docker','inspect','--format','{{json .Mounts}}',cid])):
            if not mount.get('Source'): continue
            source=Path(mount['Source']).resolve()
            if source==ROOT or source in ROOT.parents or ROOT in source.parents:
                raise RuntimeError('Active container reader/writer uses new run; no stop or deletion')


def prune():
    """One terminal, hash-bound, exact-own-CP32 prune; no cleanup retries."""
    directory=ROOT/'retention'
    if (directory/'prune-intent.json').exists() or (directory/'prune-receipt.json').exists():
        raise RuntimeError('Retention already attempted; no retry')
    deadline=a.read(SELECTION_ROOT/'dispatch.json')['deadline']
    if time.time()>=deadline-45: raise TimeoutError('Selection/retention deadline expired')
    receipts.validate_terminal(SELECTION_ROOT,SELECTION_STAGES,deadline)
    for stage in SELECTION_STAGES: receipts.terminal_container(SELECTION_ROOT,stage,deadline)
    require_published()
    best=a.read(directory/'best.json');scored=[score(arm) for arm in SELECTION_ARMS]
    winner=max(scored,key=lambda x:(x['wins'],-x['step']))
    if best['scored']!=scored or best['best']!=winner or best['test_used']: raise RuntimeError('Best evidence mismatch')
    keep=retained_steps(winner['step']);drop=sorted(set(SAVED_STEPS)-set(keep))
    if drop not in ([],[32]): raise RuntimeError('Only own CP32 may be pruned in this fixed schedule')
    # Queue calls writers_clear before this function. Recheck all Docker readers,
    # including read-only bind mounts, before unlinking any checkpoint file.
    readers_clear()
    with a.storage_guard(ROOT,exclusive=True):
        files=inventory(SELECTION_CHECKPOINTS['cp32']) if drop else {}
        target=SELECTION_CHECKPOINTS['cp32']
        intent=dict(retained=keep,removed=drop,best=winner['step'],files=files,
            target=str(target) if drop else None,irreversible=True,authorized_scope=ROOT.name+' CP32 only',
            best_sha256=sha256(directory/'best.json'),checked_at=time.time())
        atomic(directory/'prune-intent.json',intent)
        if drop:
            if inventory(target)!=a.read(directory/'cp32.json')['files']: raise RuntimeError('Prune inventory changed')
            # No shell/glob/rmtree: unlink only the validated exact file list.
            for rel in files:
                if time.time()>=deadline-45: raise TimeoutError('Prune deadline expired; no retry')
                p=target/rel
                if p.is_symlink() or not p.is_file() or p.stat().st_size!=files[rel]['bytes']:
                    raise RuntimeError('Prune target changed')
                p.unlink()
            for p in sorted((x for x in target.rglob('*') if x.is_dir()),key=lambda p:len(p.parts),reverse=True): p.rmdir()
            target.rmdir();fsync_directory(target.parent)
        require_published(keep)
        atomic(directory/'prune-receipt.json',dict(**intent,completed_at=time.time(),
            bytes_removed=sum(x['bytes'] for x in files.values()),metrics_and_evidence_retained=True))
