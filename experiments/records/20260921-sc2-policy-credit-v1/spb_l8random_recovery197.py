"""One-shot approved264 evaluation, preserving failed-r2 provenance and strict terminal gates."""
import argparse
import copy
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess as sp
import sys
import time
import unittest
import zipfile

import qwen_l8_common64_197 as common
import qwen_l7same_fresh197 as fresh
import storage_batch197
import spb_l8random_recovery_plan as p
from spb_l8random_recovery_hook import runtime_environment
from agent_system.sc2_policy_resume import checkpoint_names, sha256

a,h=common.a,common.h
ROOT=p.ROOT
BASE_INVOCATION=common.invocation
BASE_DOCKER=fresh.BASE_DOCKER
AUDIT=a.HERE/'spb-l8random-r2-recovery-audit-20260930.json'
RNG_KEYS=('rank','seed','cpu_rng_sha256','cuda_rng_sha256')


def configure():
    for name,value in dict(ROOT=ROOT,SOURCE_PARENT=p.SOURCE_PARENT,PREFIX=ROOT.name,
            MODEL_KIND='spb',STAGES=p.STAGES,HOOK_STAGES=p.HOOK_STAGES,
            CHECKPOINTS=p.CHECKPOINTS,ARMS=(),stage_spec=p.stage_spec,
            runtime_environment=runtime_environment,accounts=accounts,invocation=invocation).items():
        setattr(common,name,value)
    common.configure()
    a.DOCKER_SCRIPT=a.HERE/'spb_l8random_recovery197.py'
    a.invocation=fresh.f.BASE_INVOCATION
    h.sample=storage_batch197.sample


def accounts(deadline):
    return [dict(roots=[ROOT,p.SOURCE_PARENT],receipt_root=ROOT/'new-storage',limit=32*a.GIB,deadline=deadline),
        dict(roots=p.RETAINED_ROOTS+[ROOT,p.SOURCE_PARENT],receipt_root=ROOT/'suite-storage',limit=352*a.GIB,deadline=deadline)]


def invocation(cfg,stage,dry=False):
    args,env,out=BASE_INVOCATION(cfg,stage,dry)
    h.terminal_launch(cfg,args,env,ROOT)
    # Short fixed paths keep Ray's Unix sockets below the 107-byte limit.
    env['RAY_TMPDIR']='/tmp/rec-'+str(p.STAGES.index(stage))
    return args,env,out


def failed_parent():
    """Allow this one explicit failed source, not the accepted-parent training API."""
    cfg=a.read(p.OLD_ROOT/'deployment.json')
    part=a.read(p.OLD_OWNER/'deployment.json')
    if (cfg['runtime_sha']!=p.OLD_SHA or part['runtime_sha']!=p.OLD_SHA
            or part['model_kind']!='spb' or part['difficulty']!='CheatVision'
            or part['seed_protocol']!='independent_uniform101'
            or a.read(p.OLD_ROOT/'queue-state.json')['phase']!='failed'
            or a.read(p.OLD_OWNER/'host-supervision/state.json')['phase']!='failed'):
        raise RuntimeError('Exact failed SpB r2 provenance required')
    raw=json.loads(a.cmd(['docker','inspect','--format',
        '{"id":"{{.Id}}","owner":{{json (index .Config.Labels "sc2.acceptance.root")}},"state":{{json .State}}}',p.OLD_CID]))
    s=raw['state']
    if (raw['id']!=p.OLD_CID or raw['owner']!=str(p.OLD_OWNER) or s['Status']!='exited'
            or s['ExitCode']!=137 or s['Running'] or s['Paused'] or s['OOMKilled']):
        raise RuntimeError('Exact old exited137/noOOM container required')
    if any((p.OLD_OWNER/'runs/train96'/n).exists() for n in ('result.json','.done','metrics.json')):
        raise RuntimeError('Do not adopt rewritten old long terminal artifacts')
    a.clean(p.OLD_ROOT/'runtime',p.OLD_SHA)
    return raw


def file_identity(path):
    stat=path.stat()
    if path.is_symlink() or not path.is_file() or stat.st_size<=0:
        raise ValueError('Nonempty regular immutable file required: '+str(path))
    return dict(bytes=stat.st_size,mtime_ns=stat.st_mtime_ns,inode=stat.st_ino,device=stat.st_dev)


def stream_hash(path,until):
    digest=hashlib.sha256()
    with path.open('rb') as stream:
        while block:=stream.read(1024**2):
            if time.monotonic()>=until:raise TimeoutError('Checkpoint integrity deadline reached')
            digest.update(block)
    return digest.hexdigest()


def inspect_checkpoint(cp,expected,small_hashes,until=None):
    """Bounded host streaming hashes of all26 files, model ZIP CRC, no pickle execution."""
    files={};until=time.monotonic()+1800 if until is None else until
    for name in checkpoint_names():
        path=cp/name;identity=file_identity(path)
        if identity['bytes']!=expected[name]: raise RuntimeError('Retained checkpoint inventory changed')
        digest=stream_hash(path,until)
        if name in small_hashes and digest!=small_hashes[name]:
            raise RuntimeError('Previously verified native small state changed')
        if name.startswith('actor/model_'):
            with zipfile.ZipFile(path) as archive:
                if not archive.namelist():raise RuntimeError('Empty model ZIP')
                # Reading every member checks ZIP CRC without materializing tensor bytes.
                for member in archive.infolist():
                    with archive.open(member) as stream:
                        while stream.read(1024**2):
                            if time.monotonic()>=until:raise TimeoutError('Model CRC deadline reached')
        if identity!=file_identity(path): raise RuntimeError('Checkpoint changed during hashing')
        files[name]=dict(identity,sha256=digest,model_zip_crc_checked=name.startswith('actor/model_'))
    return dict(checkpoint=str(cp),files=files)


def adopt():
    failed=failed_parent();audit=a.read(AUDIT)
    # CPU audit binds the small native RNG/scheduler state; this new gate adds tensor-file integrity.
    if (audit['host']['source_sha']!=p.OLD_SHA or audit['host']['result']['strict_training_accepted']
            or not audit['small_state']['result']['passed'] or audit['small_state']['result']['cuda_initialized']
            or not audit['host']['result']['accepted_short_prefix']['terminal_agreement']
            or audit['host']['result']['accepted_short_prefix']['contract_files_matched']!=19):
        raise RuntimeError('Wrong forensic source')
    expected=audit['host']['result']['checkpoints']
    small=audit['small_state']['result']['checkpoints']
    cps={};until=time.monotonic()+1800
    for arm,cp in p.CHECKPOINTS.items():
        step=str(int(arm[2:]))
        if expected[step]['path']!=str(cp):raise RuntimeError('Wrong audited checkpoint path')
        cps[arm]=inspect_checkpoint(cp,expected[step]['required_files'],small[step]['small_file_sha256'],until)
        print('integrity-complete '+arm,flush=True)
    bindings={}
    for path in [p.OLD_ROOT/'deployment.json',p.OLD_ROOT/'queue-state.json',p.OLD_ROOT/'dispatch.json',
            p.OLD_OWNER/'deployment.json',p.OLD_OWNER/'host-supervision/state.json',
            p.OLD_OWNER/'resume-contract.json']:
        bindings[str(path)]=sha256(path)
    post=p.OLD_ROOT/'spb-random/short/runs/post'
    for path in [post/'result.json',post/'.done',post/'checkpoint_evaluation.json',
                 *[post/f'sampling-rank{r}.json' for r in range(8)]]:
        bindings[str(path)]=sha256(path)
    proof=dict(version=p.CONTRACT_VERSION,authorization=p.AUTHORIZATION,source_root=str(p.OLD_ROOT),
        source_sha=p.OLD_SHA,source_status='failed',old_container=failed,old_strict_acceptance=False,
        evaluation_only=True,new_updates=0,new_games=264,checkpoint_files=cps,bindings=bindings,
        forensic_audit_sha256=sha256(AUDIT),checked_at=time.time(),
        limitations=['New hashes establish recovery identity, not a pre-failure tensor checksum comparison.',
            'ZIP CRC is file integrity, not model quality; actual GPU loads and all stage gates remain mandatory.'])
    a.save(ROOT/'recovery-contract.json',proof)
    return proof


def check_contract():
    failed_parent();proof=a.read(ROOT/'recovery-contract.json')
    if (proof['version']!=p.CONTRACT_VERSION or proof['source_root']!=str(p.OLD_ROOT)
            or proof['source_sha']!=p.OLD_SHA or proof['source_status']!='failed'
            or proof['old_strict_acceptance'] or not proof['evaluation_only']
            or proof['new_updates']!=0 or proof['new_games']!=264
            or proof['forensic_audit_sha256']!=sha256(AUDIT)
            or set(proof['checkpoint_files'])!=set(p.CHECKPOINTS)):
        raise RuntimeError('Exact approved failed-artifact contract required')
    for path,digest in proof['bindings'].items():
        if sha256(Path(path))!=digest: raise RuntimeError('Failed source evidence changed')
    for arm,cp in p.CHECKPOINTS.items():
        item=proof['checkpoint_files'][arm]
        if item['checkpoint']!=str(cp) or set(item['files'])!=set(checkpoint_names()):
            raise RuntimeError('Checkpoint contract path/name drift')
        for name,entry in item['files'].items():
            if file_identity(cp/name)!={k:entry[k] for k in ('bytes','mtime_ns','inode','device')}:
                raise RuntimeError('Read-only checkpoint identity changed')
    return proof


def prepare():
    if Path('/.dockerenv').exists() or ROOT.exists() or a.SOURCE!=p.SOURCE_PARENT/'code':
        raise RuntimeError('Host-only fresh exact source/output required')
    p.validate();sha=a.cmd(['git','-C',a.SOURCE,'rev-parse','HEAD'])
    a.clean(a.SOURCE,sha);a.clean(a.ORCH,a.ORCH_SHA);failed_parent()
    common.writers_clear(p.RETAINED_ROOTS)
    ROOT.mkdir()
    for name in ('runs','cpu','tmp','tmp/task-home','tmp/cache','tmp/cuda-cache','new-storage','suite-storage'):
        (ROOT/name).mkdir()
    (ROOT/'runtime').symlink_to(a.SOURCE,target_is_directory=True)
    cfg=copy.deepcopy(a.read(p.OLD_ROOT/'spb-random/short/deployment.json'))
    for key in ('prior_failed_root','retained_prefix','fixed_deadline','original_start','deadline',
                'training_seeds','saved_steps','retention','predecessor','original_weights'):
        cfg.pop(key,None)
    cfg.update(runtime_sha=sha,controller_sha=sha,controller_source=str(a.SOURCE),orchestration_sha=a.ORCH_SHA,
        stages=p.STAGES,games=[8]*33,updates=[0]*33,run_prefix=ROOT.name,worker_hook=p.WORKER_HOOK,
        terminal_handoff='terminal-drain-v1',checkpoints={k:str(v) for k,v in p.CHECKPOINTS.items()},
        wall_seconds=p.WALL_SECONDS,gpu_hours=64,new_games=264,new_updates=0,no_training=True,
        no_retry=True,successors_authorized=False,authorization=p.AUTHORIZATION,
        first_dispatch_by=time.time()+4*3600,output_limit_bytes=32*a.GIB,suite_limit_bytes=352*a.GIB,
        storage_roots=[str(x) for x in accounts(0)[-1]['roots']],recovery_contract=p.CONTRACT_VERSION,
        selection_seeds=p.old.SELECTION_SEEDS,selection_sha256=p.old.SELECTION_SHA256,
        eval_seeds=p.old.SEEDS,seed_sha256=p.old.SEED_SHA256,
        limitation='Failed-run weight evaluation only; old strict training failure unchanged; no architecture claim')
    cfg['queue_expires']=cfg['first_dispatch_by']
    a.save(ROOT/'deployment.json',cfg)
    adopt();h.sample(accounts(cfg['first_dispatch_by']),ROOT)


def docker(mode,stage=None):
    configure();gpu=mode in ('stage','gpu-preflight')
    if stage is not None:p.stage_spec(stage)
    args=BASE_DOCKER('execute' if gpu else 'cpu')
    args[2:2]=['--read-only','--log-driver','none','-e','HOME=/tmp/task-home',
        '-e','XDG_CACHE_HOME=/tmp/cache','-e','CUDA_CACHE_PATH=/tmp/cuda-cache','-e','TMPDIR=/tmp',
        '-v',f'{p.OLD_ROOT}:{p.OLD_ROOT}:ro']
    if not gpu:
        cfg=a.read(ROOT/'deployment.json');mount=cfg['model_mount']
        args[args.index(f'{cfg["host"]["model"]}:{mount}:ro')]=f'{common.previous.SPB_METADATA}:{mount}:ro'
        args[2:2]=['-v',f'{common.previous.SPB_METADATA}:/metadata/spb:ro','-e','SC2_TEST_SPB_METADATA_PATH=/metadata/spb',
            '-v',f'{common.previous.CPU_MODEL}:/metadata/qwen:ro','-e','SC2_TEST_QWEN_METADATA_PATH=/metadata/qwen',
            '-e','SC2_TEST_TOKENIZER_PATH=/metadata/qwen','-e','OMP_NUM_THREADS=2','-e','TOKENIZERS_PARALLELISM=false']
        if mode=='cpu-hook':args[args.index('--memory')+1]='16g'
    writable=[tuple(args[i+1].split(':')[:2]) for i,x in enumerate(args[:-1]) if x=='-v' and args[i+1].split(':')[-1]!='ro']
    if writable!=[(str(ROOT),str(ROOT)),(str(ROOT/'tmp'),'/tmp')]:
        raise RuntimeError('Only new root/tmp may be writable')
    if mode in ('cpu-hook','gpu-preflight'):
        ev=a.read(ROOT/f'cpu/{stage}/resolved_config.json')['ray_init']['runtime_env']['env_vars']
        for i,x in enumerate(args):
            if x.startswith('PYTHONPATH='):args[i]='PYTHONPATH='+ev['PYTHONPATH']
    args[args.index('--name')+1]=ROOT.name+'-'+(stage if mode=='stage' else mode+('-'+stage if stage else ''))
    args[-1:]=[mode]+([stage] if stage else [])
    if gpu:args[1]='create'
    return args


def rng_at(out):
    return [{k:a.read(out/f'sampling-rank{rank}.json')[k] for k in RNG_KEYS} for rank in range(8)]


def verify(stage):
    spec=p.stage_spec(stage);rng=rng_at(ROOT/'runs'/stage)
    pairs=[]
    if stage=='diagnostic-cp96':
        post=p.OLD_ROOT/'spb-random/short/runs/post'
        if rng!=rng_at(post) or a.read(post/'checkpoint_evaluation.json')['game_seeds']!=spec['seeds']:
            raise RuntimeError('Diagnostic must pair with original own CP2post RNG/seeds')
        pairs.append(str(post))
    for other in p.paired_predecessors(stage):
        receipt=a.read(ROOT/f'acceptance-{other}.json')
        if receipt['rng']!=rng or receipt['seeds']!=spec['seeds']:
            raise RuntimeError('Exact within-group/batch paired RNG mismatch')
        pairs.append(other)
    common.verify(stage)  # Unchanged full consumed-action, replay, load, seed, finite/zero-update gates.
    path=ROOT/f'acceptance-{stage}.json';value=a.read(path)
    value.update(paired_with=pairs,group=spec['group'],recovery_contract_sha256=sha256(ROOT/'recovery-contract.json'),
        original_strict_training_accepted=False)
    a.save(path,value)


def regressions(host=False):
    sys.path[:0]=[str(a.SOURCE/'tests'),str(a.SOURCE/'scripts')]
    names=['test_spb_l8random_recovery197','test_terminal_storage197','test_host_stage197',
        'test_storage_batch197','test_storage_quiescent197','test_l7_host_continuation197',
        'test_policy_credit_storage197','test_policy_credit_storage_coordination197'] if host else [
        'test_spb_l8random_recovery197','test_feedback_eval','test_sc2_policy_resume',
        'test_sc2_checkpoint_resume','test_metric_precision','test_sc2_action_support',
        'test_sc2_policy_credit','test_sc2_no_thinking_torch','test_sc2_reset_startup','test_sc2_generation_tokens',
        'test_policy_credit_acceptance197','test_qwen_l8_probe_env']
    if host and Path('/.dockerenv').exists():raise RuntimeError('Actual host required')
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromNames(names))
    cuda=False
    if not host:
        import torch
        cuda=torch.cuda.is_initialized()
    proof=dict(passed=result.wasSuccessful() and not result.skipped and not cuda,tests=result.testsRun,
        skips=len(result.skipped),cuda_initialized=cuda,host_only=host,
        runtime_sha=a.read(ROOT/'deployment.json')['runtime_sha'],checked_at=time.time())
    a.save(ROOT/('host-regressions.json' if host else 'regressions.json'),proof,lock_root=ROOT)
    if not proof['passed']:raise RuntimeError('Actual zero-skip CPU gates required')


def prepare_cpu():
    configure();prepare()
    state=dict(status='running',no_gpu=True,jobs=[],started_at=time.time())
    try:
        commands=[('host-regressions',[sys.executable,'-B',str(a.DOCKER_SCRIPT),'host-regressions']),
                  ('model-regressions',docker('regressions')),('configs',docker('cpu'))]
        for label,command in commands:
            run_cpu_job(state,label,command)
        for stage in p.HOOK_STAGES:run_cpu_job(state,'hook-'+stage,docker('cpu-hook',stage))
        common.check_cpu();check_contract();state.update(status='passed',finished_at=time.time(),
            recovery_contract_sha256=sha256(ROOT/'recovery-contract.json'))
    except BaseException as exc:
        state.update(status='failed',error=str(exc),finished_at=time.time());raise
    finally:a.save(ROOT/'preparation.json',state)


def run_cpu_job(state,label,command):
    item=dict(label=label,started_at=time.time());state['jobs'].append(item)
    a.save(ROOT/'preparation.json',state)
    with (ROOT/f'prepare-{label}.log').open('x') as stream:
        result=sp.run(command,stdout=stream,stderr=sp.STDOUT,timeout=900)
    item.update(exit_code=result.returncode,finished_at=time.time())
    if command[0]=='docker':
        name=command[command.index('--name')+1]
        info=json.loads(a.cmd(['docker','inspect','--format',
            '{"id":"{{.Id}}","state":{{json .State}},"device_requests":{{json .HostConfig.DeviceRequests}}}',name]))
        item.update(container=info,name=name)
        if info['device_requests'] or info['state']['Running'] or info['state']['ExitCode']!=0 or info['state']['OOMKilled']:
            raise RuntimeError('CPU container failed: '+label)
    if result.returncode:raise RuntimeError('CPU gate failed: '+label)
    a.save(ROOT/'preparation.json',state)


def queue():
    common.check_cpu();check_contract()
    prep=a.read(ROOT/'preparation.json')
    if prep['status']!='passed' or prep['recovery_contract_sha256']!=sha256(ROOT/'recovery-contract.json'):
        raise RuntimeError('Complete CPU preparation and unchanged contract required')
    with (ROOT/'queue.lock').open('x') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (ROOT/'queue-state.json').exists() or (ROOT/'dispatch.json').exists():raise RuntimeError('No repeated queue/dispatch')
        state=dict(phase='waiting-admission',completed=[],new_games=264,new_updates=0)
        try:
            cfg=a.read(ROOT/'deployment.json');a.save(ROOT/'queue-state.json',state)
            common.admit('first',cfg['first_dispatch_by'])
            start=time.time();deadline=start+p.WALL_SECONDS
            a.save(ROOT/'dispatch.json',dict(start=start,deadline=deadline,gpu_hours=64,new_games=264,new_updates=0,includes_gpu_preflight=True))
            state.update(phase='gpu-preflight',deadline=deadline);a.save(ROOT/'queue-state.json',state)
            h.run_stages(['gpu-preflight'],lambda _:docker('gpu-preflight',p.STAGES[0]),common.verify_probe,
                accounts(deadline),ROOT,ROOT/'gpu-preflight-supervision',ROOT,deadline,
                admit=lambda _:common.admit('gpu-preflight',deadline))
            state.update(phase='running-unverified');a.save(ROOT/'queue-state.json',state)
            def admission(stage):
                if prep['recovery_contract_sha256']!=sha256(ROOT/'recovery-contract.json'):
                    raise RuntimeError('Recovery contract changed after CPU admission')
                check_contract()
                if stage!=p.STAGES[0] and not (ROOT/'acceptance-diagnostic-cp96.json').exists():
                    raise RuntimeError('Mandatory first8 diagnostic not accepted')
                common.admit(stage,deadline)
            terminal=h.run_stages(p.STAGES,lambda s:docker('stage',s),verify,accounts(deadline),ROOT,
                ROOT/'host-supervision',ROOT,deadline,admit=admission,
                **h.terminal_options(cfg,ROOT,ROOT/'host-supervision',deadline))
            a.save(ROOT/'state.json',terminal);a.save(ROOT/'queue-state.json',terminal)
        except BaseException as exc:
            state.update(phase='failed',error_type=type(exc).__name__,error=str(exc),finished_at=time.time())
            a.save(ROOT/'state.json',state);a.save(ROOT/'queue-state.json',state);raise


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',choices=['prepare-cpu','cpu','cpu-command','regressions','host-regressions',
        'regressions-command','cpu-hook','cpu-hook-command','gpu-preflight','queue','stage'])
    parser.add_argument('stage',nargs='?',choices=p.STAGES);v=parser.parse_args()
    if v.mode in ('regressions','host-regressions'):
        # Leave fixture globals untouched; ROOT is a fixed recovery output.
        regressions(v.mode=='host-regressions');return
    configure()
    if v.mode.endswith('-command'):print(json.dumps(docker(v.mode.removesuffix('-command'),v.stage)))
    elif v.mode=='prepare-cpu':prepare_cpu()
    elif v.mode=='cpu':common.cpu()
    elif v.mode=='queue':queue()
    elif v.mode in ('cpu-hook','gpu-preflight'):
        p.stage_spec(v.stage);config=ROOT/f'cpu/{v.stage}/resolved_config.json'
        if v.mode=='cpu-hook':common.probe.check_hook_cpu(ROOT/f'cpu/hook-{v.stage}',Path('/tmp/hook-'+str(p.STAGES.index(v.stage))),config,environment_loader=runtime_environment)
        elif v.stage==p.STAGES[0]:common.probe.run(ROOT/'gpu-preflight',Path('/tmp/probe-ray'),config,environment_loader=runtime_environment)
        else:raise ValueError('Only first stage may probe GPUs')
    else:
        cfg=a.read(ROOT/'deployment.json');a.clean(a.SOURCE,cfg['runtime_sha']);a.clean(ROOT/'runtime',cfg['runtime_sha'])
        args,env,_=invocation(cfg,v.stage)
        fd=os.open(ROOT/(v.stage+'-entry.log'),os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
        os.dup2(fd,1);os.dup2(fd,2);os.close(fd);os.chdir(ROOT/'runtime');os.execvpe(args[0],args,env)


if __name__=='__main__':main()
