"""Approved fresh SpB random-seed short+96, only after Qwen CP8 train+eval passes."""
import argparse
import copy
import fcntl
import json
import math
import os
from pathlib import Path
import subprocess as sp
import sys
import time

import acceptance197 as a
import host_stage197 as h
import l7_followup197 as f
import l7_followup197_r4 as host
from agent_system.sc2_policy_resume import prefix_files, sha256, verify_contract
from agent_system.sc2_seed_protocol import ablation_seeds

ROOT = Path('/var/jfsCache/sc2-spb-l7random96-197-20260923-r1')
PARTS = ('spb-random/short', 'spb-random/long')
PREDECESSOR = Path('/var/jfsCache/sc2-qwen-random-cp8-197-20260923-r2')
PREDECESSOR_SHA = '34154283a8298ac4fbaab1c63770a6b81f7d375c'
PREDECESSOR_DEADLINE = 1790308720.0467553
FIRST_DISPATCH_BY = PREDECESSOR_DEADLINE + 3600
WALL_SECONDS = 48*3600
LIMIT = 1024*a.GIB
PREFIX = 'sc2-spb-l7random96-197-20260923-r1-'
BASE_INVOCATION, BASE_VERIFY = f.invocation, f.verify
BASE_DOCKER = a.docker


def configure():
    f.SUITE, f.PARTS = ROOT, PARTS
    f.CONTAINER_PREFIX = PREFIX
    f.DOCKER_SCRIPT = a.HERE/'spb_l7_random197.py'
    f.parent_for = parent_for
    f.invocation, f.verify = invocation, verify


def parent_for(index):
    if index != 1:
        raise ValueError('Only own native SpB short prefix can be resumed')
    return ROOT/PARTS[0]


def accounts(deadline):
    return [dict(roots=[ROOT,a.SOURCE.parent],receipt_root=ROOT,limit=LIMIT,deadline=deadline)]


def prepare():
    if ROOT.exists():
        raise RuntimeError('Fresh root required; no overwrite/retry')
    sha = a.cmd(['git','-C',a.SOURCE,'rev-parse','HEAD'])
    a.clean(a.SOURCE,sha);a.clean(a.ORCH,a.ORCH_SHA)
    ROOT.mkdir()
    a.STORAGE_LOCK_ROOT = ROOT
    a.cmd(['git','clone','--quiet','--shared',a.SOURCE,ROOT/'runtime'])
    a.cmd(['git','-C',ROOT/'runtime','checkout','--quiet','--detach',sha])
    base = a.read(f.SPB_BASE/'deployment.json')
    authorization = ('Sep23 user approved original SpB L7 per-game independent seed short+96 AFTER '
        'current Qwen nativeCP8 train+eval complete acceptance; 792new games/96PPO; '
        '<=48wallh/384GPUh/1TiB including short/loading/waits/CP/eval; no other arm or retry')
    for index,part in enumerate(PARTS):
        root = ROOT/part
        root.mkdir(parents=True)
        for name in ('runs','cpu','tmp','tmp/task-home','tmp/cache','tmp/cuda-cache'):
            (root/name).mkdir()
        (root/'runtime').symlink_to(ROOT/'runtime',target_is_directory=True)
        cfg = copy.deepcopy(base)
        cfg.update(runtime_sha=sha,controller_sha=sha,controller_source=str(a.SOURCE),
            orchestration_sha=a.ORCH_SHA,model_kind='spb',model_mount='/assets/spb',
            difficulty='VeryHard',seed_protocol='independent_uniform101',seed_group_mode='mixed_seed_ablation',
            training_seeds=[ablation_seeds('independent_uniform101',0,i,1,8) for i in range(96)],
            stages=['pre','train2','post'] if index==0 else ['train96','eval96'],
            games=[8,16,8] if index==0 else [752,8],updates=[0,2,0] if index==0 else [94,0],
            run_prefix='spb-l7random197-r1-'+str(index),worker_hook='l7_followup_hook.install',
            wall_seconds=WALL_SECONDS,gpu_hours=384,output_limit_bytes=LIMIT,
            first_dispatch_by=FIRST_DISPATCH_BY,queue_expires=FIRST_DISPATCH_BY,
            no_retry=True,no_long_training=False,successors_authorized=index==0,
            predecessor=str(PREDECESSOR if index==0 else ROOT/PARTS[0]),authorization=authorization,
            storage_supervision='host-guardian-v1',host_stage_entry_log=True,
            container_rootfs_read_only=True,startup_concurrency=1,
            limitation='Mixed-seed UID confounds scenario difficulty; startup/quiescence timing equivalence unproven')
        a.save(root/'deployment.json',cfg,lock_root=ROOT)
    a.save(ROOT/'deployment.json',dict(runtime_sha=sha,controller_sha=sha,controller_source=str(a.SOURCE),
        orchestration_sha=a.ORCH_SHA,parts=PARTS,predecessor=str(PREDECESSOR),
        predecessor_sha=PREDECESSOR_SHA,predecessor_deadline=PREDECESSOR_DEADLINE,
        first_dispatch_by=FIRST_DISPATCH_BY,wall_seconds=WALL_SECONDS,gpu_hours=384,
        output_limit_bytes=LIMIT,storage_roots=[str(ROOT),str(a.SOURCE.parent)],
        new_games=792,new_updates=96,short_included=True,no_retry=True,successors_authorized=False,
        authorization=authorization),lock_root=ROOT)


def invocation(cfg,stage,dry=False):
    args,env,out = BASE_INVOCATION(cfg,stage,dry)
    args += ["+ray_init.runtime_env.env_vars.SC2_RESET_CONCURRENCY='1'"]
    env['RAY_TMPDIR'] = '/tmp/sr197-'+stage
    return args,env,out


def docker(mode,index,stage=None):
    cfg=f.select(index)
    args=BASE_DOCKER('execute' if mode=='stage' else 'cpu')
    args[2:2]=['--read-only','--log-driver','none','-e','HOME=/tmp/task-home',
        '-e','XDG_CACHE_HOME=/tmp/cache','-e','CUDA_CACHE_PATH=/tmp/cuda-cache','-e','TMPDIR=/tmp',
        '-v',f'{ROOT}:{ROOT}:ro','-v',f'{ROOT}/.storage.lock:{ROOT}/.storage.lock']
    if mode!='stage':
        args[args.index(f'{cfg["host"]["model"]}:/assets/spb:ro')]=f'{f.previous.SPB_METADATA}:/assets/spb:ro'
        args[2:2]=['-v',f'{f.previous.CPU_MODEL}:/metadata/qwen:ro',
            '-e','SC2_TEST_SPB_METADATA_PATH=/assets/spb','-e','SC2_TEST_QWEN_METADATA_PATH=/metadata/qwen',
            '-e','SC2_TEST_TOKENIZER_PATH=/metadata/qwen','-e','OMP_NUM_THREADS=2','-e','TOKENIZERS_PARALLELISM=false']
    owner=ROOT/PARTS[index]
    writable=[]
    for i,value in enumerate(args[:-1]):
        if value=='-v':
            spec=args[i+1].split(':')
            if spec[-1]!='ro':writable.append(tuple(spec[:2]))
    expected={(str(owner),str(owner)),(str(owner/'tmp'),'/tmp'),(str(ROOT/'.storage.lock'),str(ROOT/'.storage.lock'))}
    if len(writable)!=3 or set(writable)!=expected:raise RuntimeError('Unexpected writable bind')
    args[args.index('--name')+1]=PREFIX+('short' if index==0 else 'long')+'-'+(stage or mode)
    args[-1:]=[mode,str(index)]
    if mode=='stage':
        if stage not in cfg['stages']:raise ValueError('Undeclared stage')
        args[1]='create';args.append(stage)
    return args


def cpu(index):
    f.cpu(index)
    for stage in a.read(a.ROOT/'deployment.json')['stages']:
        cfg=a.read(a.ROOT/f'cpu/{stage}/resolved_config.json')
        ev=cfg['ray_init']['runtime_env']['env_vars']
        if (str(ev['SC2_RESET_CONCURRENCY'])!='1' or str(ev['SC2_RESET_RETRIES'])!='1'
                or str(ev['SC2_TRAIN_SEED_PROTOCOL'])!='independent_uniform101'
                or cfg['algorithm']['sc2_policy_credit']['seed_group_mode']!='mixed_seed_ablation'):
            raise RuntimeError('Independent seeds/startup/quality contract changed')


def verify(stage,write=True):
    out=a.ROOT/'runs'/stage
    if any(a.read(out/n).get('metrics_precision')!='binary64-v1' for n in ('manifest.json','result.json')):
        raise RuntimeError('Full precision required')
    BASE_VERIFY(stage,False)
    if stage in ('train2','train96'):
        lo,hi=(1,2) if stage=='train2' else (3,96)
        metrics=a.read(out/'metrics.json')
        if ([x['step'] for x in metrics]!=list(range(lo,hi+1)) or any(
                not math.isfinite(x['timing_s/update_actor']) or x['timing_s/update_actor']<=0
                or not math.isfinite(x['policy_credit/invalid_advantage_max']) for x in metrics)):
            raise RuntimeError('Returned actual PPO evidence required')
        seeds=[json.loads(x) for x in (out/'training_seeds.jsonl').read_text().splitlines()]
        if len(seeds)!=hi-lo+1 or any(row['reset_index']!=i or row['base_seed']!=0
                or row['seed_protocol']!='independent_uniform101'
                or row['seeds']!=ablation_seeds('independent_uniform101',0,i,1,8)
                for i,row in enumerate(seeds,lo-1)):
            raise RuntimeError('Exact per-game independent seed ledger required')
    if write:BASE_VERIFY(stage,True)


def contract_for():
    parent=ROOT/PARTS[0]
    contract=dict(version='accepted-spb-random-full-state-prefix-v1',parent=str(parent),
        checkpoint=str(parent/'runs/train2/checkpoints/global_step_2'),
        parent_sha=a.read(parent/'deployment.json')['runtime_sha'],start_step=2,target_step=96,
        driver_rng_unavailable_accepted=False,files={p:sha256(parent/p) for p in prefix_files()})
    verify_contract(contract)
    return contract


def predecessor_complete():
    queue=a.read(PREDECESSOR/'queue-state.json')
    control=a.read(PREDECESSOR/'host-supervision/state.json')
    if any(x['phase']=='failed' for x in (queue,control)):
        raise RuntimeError('Qwen predecessor failed; no SpB dispatch')
    if queue['phase']!='completed':return False
    for obj in (queue,control,a.read(PREDECESSOR/'state.json')):
        if (obj['phase']!='completed' or obj.get('exit_code')!=0
                or obj['completed']!=['train96','eval96'] or obj['deadline']!=PREDECESSOR_DEADLINE):
            raise RuntimeError('Qwen predecessor terminal mismatch')
    cfg=a.read(PREDECESSOR/'deployment.json')
    if cfg['runtime_sha']!=PREDECESSOR_SHA:raise RuntimeError('Wrong Qwen predecessor runtime')
    a.clean(PREDECESSOR/'runtime',PREDECESSOR_SHA)
    a.clean(Path(cfg['controller_source']),PREDECESSOR_SHA)
    for stage in ('train96','eval96'):
        name='sc2-qwen-random-cp8-197-20260923-r2-'+stage
        status=json.loads(a.cmd(['docker','inspect','--format',
            '{"id":"{{.Id}}","owner":"{{index .Config.Labels "sc2.acceptance.root"}}","state":{{json .State}}}',name]))
        obj=status['state']
        if obj['Running'] or obj['Paused'] or obj['ExitCode']!=0 or obj['OOMKilled'] or obj['Error']:
            raise RuntimeError('Qwen stage not successfully exited')
        receipt=a.read(PREDECESSOR/f'host-supervision/{stage}-guardian.json')
        if (status['owner']!=str(PREDECESSOR) or receipt.get('container_id')!=status['id']
                or receipt.get('owner_root')!=str(PREDECESSOR) or receipt.get('phase')!='completed'
                or receipt.get('deadline')!=PREDECESSOR_DEADLINE
                or receipt['final_state']['Running'] or receipt['final_state']['Paused']
                or receipt['final_state']['ExitCode']!=0):
            raise RuntimeError('Qwen guardian terminal not successful')
    script=Path(cfg['controller_source'])/a.HERE.relative_to(a.SOURCE)
    code=f"import sys;sys.path.insert(0,{str(script)!r});import qwen_random_cp8_197 as m;m.configure();m.verify('train96',write=False);m.verify('eval96',write=False)"
    sp.run([sys.executable,'-B','-c',code],check=True,timeout=180)
    return True


def regressions(host_only=False):
    import unittest
    sys.path[:0]=[str(a.SOURCE/'tests'),str(a.SOURCE/'scripts')]
    if host_only:
        if Path('/.dockerenv').exists():raise RuntimeError('Host tests require actual host')
        names=['test_l7_host_continuation197','test_host_stage197','test_storage_quiescent197',
            'test_policy_credit_storage197','test_policy_credit_storage_coordination197']
    else:
        import torch
        names=['test_metric_precision','test_l7_precision_continuation197','test_l7_followup197',
            'test_sc2_checkpoint_resume','test_qwen_l7_long197','test_sc2_policy_resume',
            'test_sc2_action_support','test_sc2_policy_credit','test_sc2_task_signal',
            'test_sc2_no_thinking_torch','test_thinking_action_boundary','test_r6_format_reward',
            'test_original_bo_segment','test_original_game_seeds','test_sc2_generation_tokens',
            'test_policy_credit_acceptance197','test_policy_credit_storage197','test_policy_credit_storage_coordination197',
            'test_qwen_seed_acceptance197','test_qwen_seed_acceptance197_r3','test_qwen_seed_acceptance197_r4',
            'test_sc2_reset_startup','test_qwen_random_cp8_197','test_spb_l7_random197']
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromNames(names))
    cuda=False if host_only else torch.cuda.is_initialized()
    proof=dict(passed=result.wasSuccessful() and not result.skipped and not cuda,tests=result.testsRun,
        skips=len(result.skipped),cuda_initialized=cuda,host_only=host_only,
        runtime_sha=a.read(ROOT/'deployment.json')['runtime_sha'],checked_at=time.time())
    destination=ROOT/'host-regressions.json' if host_only else ROOT/PARTS[0]/'regressions.json'
    a.save(destination,proof,lock_root=ROOT)
    if not proof['passed']:raise RuntimeError('Zero-skip CPU regressions required')


def check_cpu():
    cfg=a.read(ROOT/'deployment.json')
    a.clean(a.SOURCE,cfg['controller_sha']);a.clean(ROOT/'runtime',cfg['runtime_sha']);a.clean(a.ORCH,a.ORCH_SHA)
    for path in [ROOT/PARTS[0]/'regressions.json',ROOT/'host-regressions.json',*[ROOT/p/'readiness.json' for p in PARTS]]:
        proof=a.read(path)
        if not proof['passed'] or proof.get('skips',0) or proof.get('cuda_initialized',False) or proof['runtime_sha']!=cfg['runtime_sha']:
            raise RuntimeError('All actual CPU/launcher/source gates required')


def admit(index,stage,deadline):
    owner=ROOT/PARTS[index]
    f.previous.ROOT=owner
    while True:
        if time.time()>=deadline-45:raise TimeoutError('Admission deadline reached')
        h.sample(accounts(deadline),ROOT)
        host.writers_clear(accounts(deadline)[0]['roots'])
        if f.previous.resources_ready():break
        time.sleep(min(30,deadline-45-time.time()))
    probe=owner/('fsync-'+stage)
    with probe.open('xb') as stream:
        stream.write(b'spb-random\n');stream.flush();os.fsync(stream.fileno())
    if probe.read_bytes()!=b'spb-random\n':raise RuntimeError('Fsync readback failed')
    a.save(owner/('admission-'+stage+'.json'),dict(passed=True,checked_at=time.time(),deadline=deadline,
        eight_idle_gpus=True,ram_gib_min=600,nvme_gib_min=1084,fsync=True),lock_root=ROOT)


def queue():
    check_cpu()
    with (ROOT/'queue.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (ROOT/'queue-state.json').exists() or (ROOT/'dispatch.json').exists():raise RuntimeError('Already queued; no retry')
        state=dict(phase='waiting-predecessor',completed=[],first_dispatch_by=FIRST_DISPATCH_BY)
        try:
            a.save(ROOT/'queue-state.json',state,lock_root=ROOT)
            while not predecessor_complete():
                if time.time()>=FIRST_DISPATCH_BY-45:raise TimeoutError('First admission expired')
                time.sleep(30)
            a.save(ROOT/'predecessor-acceptance.json',dict(passed=True,root=str(PREDECESSOR),
                runtime_sha=PREDECESSOR_SHA,checked_at=time.time()),lock_root=ROOT)
            admit(0,'part',FIRST_DISPATCH_BY)
            start=time.time();deadline=start+WALL_SECONDS
            a.save(ROOT/'dispatch.json',dict(start=start,deadline=deadline,gpu_hours=384,new_games=792,new_updates=96),lock_root=ROOT)
            for index,part in enumerate(PARTS):
                cfg=f.select(index)
                if index==1:
                    a.save(a.ROOT/'resume-contract.json',contract_for(),lock_root=ROOT)
                    with (a.ROOT/'parent-cpu.log').open('x') as log:
                        sp.run(docker('parent-cpu',1),stdout=log,stderr=sp.STDOUT,check=True,
                            timeout=min(600,deadline-45-time.time()))
                    if not a.read(a.ROOT/'parent-readiness.json')['actual_parent_verified']:
                        raise RuntimeError('Native own CP2/driver RNG not verified')
                a.save(a.ROOT/'dispatch.json',dict(start=start,deadline=deadline,clock_shared_with_short=True),lock_root=ROOT)
                state.update(phase='running-unverified',part=part,deadline=deadline)
                a.save(ROOT/'queue-state.json',state,lock_root=ROOT)
                result=h.run_stages(cfg['stages'],lambda stage:docker('stage',index,stage),verify,
                    accounts(deadline),a.ROOT,a.ROOT/'host-supervision',ROOT,deadline,
                    admit=lambda stage:admit(index,stage,deadline))
                a.save(a.ROOT/'state.json',result,lock_root=ROOT)
                state['completed'].append(part)
                a.save(ROOT/'queue-state.json',state,lock_root=ROOT)
            state.update(phase='completed',exit_code=0,learning_validated=False)
            a.save(ROOT/'queue-state.json',state,lock_root=ROOT)
        except BaseException as exc:
            state.update(phase='failed',error_type=type(exc).__name__,error=str(exc))
            a.save(ROOT/'queue-state.json',state,lock_root=ROOT)
            raise


def child_stage(index,stage):
    cfg=f.select(index)
    a.clean(a.SOURCE,cfg['controller_sha']);a.clean(a.ROOT/'runtime',cfg['runtime_sha'])
    args,env,_=invocation(cfg,stage)
    fd=os.open(a.ROOT/(stage+'-entry.log'),os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    os.dup2(fd,1);os.dup2(fd,2);os.close(fd)
    os.chdir(a.ROOT/'runtime');os.execvpe(args[0],args,env)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode',choices=['prepare','queue','cpu','cpu-command','regressions-command',
        'regressions','host-regressions','parent-cpu','stage'])
    p.add_argument('index',type=int,nargs='?',choices=(0,1));p.add_argument('stage',nargs='?')
    v=p.parse_args()
    if v.mode not in ('regressions','host-regressions'):configure()
    if v.mode in ('prepare','queue'):globals()[v.mode]()
    elif v.mode in ('regressions','host-regressions'):regressions(v.mode=='host-regressions')
    elif v.index is None:p.error('Exact short/long index required')
    elif v.mode.endswith('-command'):print(json.dumps(docker(v.mode.removesuffix('-command'),v.index)))
    elif v.mode=='cpu':cpu(v.index)
    elif v.mode=='parent-cpu':f.parent_cpu(v.index)
    else:child_stage(v.index,v.stage)
