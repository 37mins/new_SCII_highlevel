"""Sep27 authorized r3: retain L9 training, only eval8 then fresh L10; old clocks."""
import argparse
import copy
import fcntl
import json
import os
from pathlib import Path
import subprocess as sp
import sys
import time
import unittest

import qwen_l9l10_same197 as m

a, f, h = m.a, m.f, m.h
OLD_ROOTS = {n: Path(f'/var/jfsCache/sc2-qwen-l{n}same96-197-20260927-r1') for n in (9,10)}
OLD_SOURCE = Path('/var/jfsCache/sc2-qwen-l9l10same96-197-source-20260927-r1')
FAILED_ROOTS = {n: Path(f'/var/jfsCache/sc2-qwen-l{n}same96-197-20260927-r2') for n in (9,10)}
FAILED_SOURCE = Path('/var/jfsCache/sc2-qwen-l9l10same96-197-source-20260927-r2')
FAILED_SHA = '5261ff5d6fee665fec78a97de4c5bfd9a79b4fc5'
ROOTS = {n: Path(f'/var/jfsCache/sc2-qwen-l{n}same96-197-20260927-r3') for n in (9,10)}
SOURCE_PARENT = Path('/var/jfsCache/sc2-qwen-l9l10same96-197-source-20260927-r3')
RUNTIME_SHA = '1c6cf60b111570ef13f9817d0b1b16fb774546f5'
START = 1790482308.224269
L9_DEADLINE = 1790525508.224269
SUITE_DEADLINE = 1790568708.224269
PARTS = m.PARTS
CPU_PROBES = ((9,1,'eval96'),(10,0,'pre'),(10,0,'train2'),(10,1,'train96'))
AUTHORIZATION = ('Sep27 user explicitly permits r3 admission receipt naming correction and controlled '
    'remaining L9 eval8 then L10 fresh792games/96PPO; retain completed L9 784games/96PPO; '
    'old L9/suite deadlines, total192GPUh/512GiB, arm96GPUh/256GiB inclusive r1+r2+r3; '
    'no repeated training, deletion, automatic retry, new budget or successor')


def configure(level):
    m.ROOTS, m.SOURCE_PARENT = ROOTS, SOURCE_PARENT
    m.configure(level)
    m.accounts = accounts
    f.DOCKER_SCRIPT = a.HERE/'qwen_l9l10_continue197.py'


def accounts(deadline):
    if deadline > SUITE_DEADLINE: raise ValueError('Original suite deadline required')
    shared = [OLD_SOURCE,FAILED_SOURCE,SOURCE_PARENT]
    return [dict(roots=[OLD_ROOTS[n],FAILED_ROOTS[n],ROOTS[n],*shared],receipt_root=ROOTS[n]/'arm-storage',
                 limit=m.ARM_LIMIT,deadline=deadline) for n in (9,10)] + [
        dict(roots=[*OLD_ROOTS.values(),*FAILED_ROOTS.values(),*ROOTS.values(),*shared],receipt_root=ROOTS[9]/'suite-storage',
             limit=m.SUITE_LIMIT,deadline=deadline)]


def old_terminal():
    old = OLD_ROOTS[9]; owner = old/PARTS[1]
    q, d, suite = [a.read(old/name) for name in ('queue-state.json','dispatch.json','suite-dispatch.json')]
    host = a.read(owner/'host-supervision/state.json')
    if (d['start']!=START or d['deadline']!=L9_DEADLINE or suite['start']!=START
            or suite['deadline']!=SUITE_DEADLINE or q['phase']!='failed'
            or q['error_type']!='KeyError' or q['error']!="'checkpoints/global_step_32/data.pt'"
            or q['completed']!=['L9/qwen-same/short'] or host['phase']!='failed'
            or host['stage']!='train96' or host['error']!=q['error']
            or (owner/'runs/eval96').exists() or (OLD_ROOTS[10]/'dispatch.json').exists()):
        raise RuntimeError('Only exact stopped L9 train96 and never-dispatched L10 may be retained')
    for root in OLD_ROOTS.values(): a.clean(root/'runtime',RUNTIME_SHA)
    a.clean(OLD_SOURCE/'code',RUNTIME_SHA)
    m.receipts.validate_terminal(old/PARTS[0],['pre','train2','post'],L9_DEADLINE)
    terminal = {}
    for index, stages in ((0,('pre','train2','post')),(1,('train96',))):
        for stage in stages:
            terminal[stage] = m.receipts.terminal_container(old/PARTS[index],stage,L9_DEADLINE,
                '37951982a4996f684b1f5e2ca8e81dae60b937b69760eed96c1f959bb96ff2ef' if stage=='train96' else None)
    return terminal


def failed_r2_terminal():
    """Only the exact pre-game admission failure is eligible for this handoff."""
    root=FAILED_ROOTS[9];owner=root/PARTS[1]
    error=f"[Errno 17] File exists: '{owner}/fsync-eval96'"
    for p in (root/'queue-state.json',owner/'host-supervision/state.json'):
        d=a.read(p)
        if d['phase']!='failed' or d['error_type']!='FileExistsError' or d['error']!=error or d['completed']:
            raise RuntimeError('Exact pre-game r2 admission failure required')
    if ((owner/'runs/eval96').exists() or (owner/'eval96-entry.log').exists()
            or (FAILED_ROOTS[10]/'dispatch.json').exists()):
        raise RuntimeError('r2 must contain no new evaluation or L10 dispatch')
    d=a.read(root/'dispatch.json');suite=a.read(root/'suite-dispatch.json')
    if d['start']!=START or d['deadline']!=L9_DEADLINE or suite['deadline']!=SUITE_DEADLINE:
        raise RuntimeError('Original r2 clocks required')
    control=owner/'gpu-preflight-supervision';state=a.read(control/'state.json')
    guardian=a.read(control/'gpu-preflight-guardian.json')
    cid='4ef0996c8aee36a782df0003218ae573dec3e137b3c64007e2b5989d4c8e23f1'
    obj=json.loads(a.cmd(['docker','inspect','--format',
        '{"id":"{{.Id}}","owner":"{{index .Config.Labels "sc2.acceptance.root"}}","state":{{json .State}}}',cid]))
    if (state['phase']!='completed' or state['exit_code']!=0 or state['completed']!=['gpu-preflight']
            or state['deadline']!=L9_DEADLINE or state['container_id']!=cid
            or guardian['container_id']!=cid or guardian['owner_root']!=str(owner)
            or guardian['phase']!='completed' or guardian['deadline']!=L9_DEADLINE
            or obj['id']!=cid or obj['owner']!=str(owner)
            or any(s['Running'] or s['Paused'] or s['ExitCode']!=0 or s.get('OOMKilled') or s.get('Error')
                   for s in (obj['state'],guardian['final_state']))):
        raise RuntimeError('Exact exited r2 GPU preflight required')
    retained=root/'retained-acceptance.json'
    if m.sha256(retained)!='f9cf19d822ef78bfea8a30dfdc503cc7e1cc51566a3aaab5cda53a21209ff7a4':
        raise RuntimeError('Frozen r2 retained acceptance changed')
    a.clean(FAILED_SOURCE/'code',FAILED_SHA)
    return dict(passed=True,failed_queue_sha256=m.sha256(root/'queue-state.json'),gpu_preflight_id=cid,
                retained_acceptance_sha256=m.sha256(retained),new_games=0,new_updates=0)


def prepare():
    if any(r.exists() for r in ROOTS.values()) or a.SOURCE!=SOURCE_PARENT/'code':
        raise RuntimeError('Fresh exact r3 roots required; no overwrite')
    if time.time()>=L9_DEADLINE-45: raise TimeoutError('Original L9 budget expired')
    terminal = old_terminal();prior_failure=failed_r2_terminal()
    sha = a.cmd(['git','-C',a.SOURCE,'rev-parse','HEAD'])
    a.clean(a.SOURCE,sha); a.clean(a.ORCH,a.ORCH_SHA)
    for level,root in ROOTS.items():
        root.mkdir(); (root/'arm-storage').mkdir()
        if level==9: (root/'suite-storage').mkdir()
        (root/'runtime').symlink_to(OLD_ROOTS[level]/'runtime',target_is_directory=True)
        for index,part in enumerate(PARTS):
            owner = root/part; owner.mkdir(parents=True)
            for sub in ('runs','cpu','tmp','tmp/task-home','tmp/cache','tmp/cuda-cache'): (owner/sub).mkdir()
            (owner/'runtime').symlink_to(root/'runtime',target_is_directory=True)
            cfg = copy.deepcopy(a.read(OLD_ROOTS[level]/part/'deployment.json'))
            stages = ([] if index==0 else ['eval96']) if level==9 else cfg['stages']
            cfg.update(controller_sha=sha,controller_source=str(a.SOURCE),runtime_sha=RUNTIME_SHA,
                stages=stages,games=([8] if index else []) if level==9 else cfg['games'],
                updates=([0] if index else []) if level==9 else cfg['updates'],
                run_prefix=root.name+('-short' if index==0 else '-long'),authorization=AUTHORIZATION,
                first_dispatch_by=L9_DEADLINE if level==9 else SUITE_DEADLINE,
                queue_expires=L9_DEADLINE if level==9 else SUITE_DEADLINE,
                predecessor=str(OLD_ROOTS[9] if level==9 else ROOTS[9]))
            a.save(owner/'deployment.json',cfg,lock_root=root)
        a.save(root/'deployment.json',dict(runtime_sha=RUNTIME_SHA,controller_sha=sha,
            controller_source=str(a.SOURCE),authorization=AUTHORIZATION,level=level,parts=PARTS,
            original_start=START,suite_deadline=SUITE_DEADLINE,
            fixed_deadline=L9_DEADLINE if level==9 else None,
            new_games=8 if level==9 else 792,new_updates=0 if level==9 else 96,
            output_limit_bytes=m.ARM_LIMIT,suite_output_limit_bytes=m.SUITE_LIMIT,
            retained_games=784 if level==9 else 0,retained_updates=96 if level==9 else 0,
            no_retry=True,terminal=terminal if level==9 else {},prior_failure=prior_failure,
            storage_roots=[str(p) for p in accounts(SUITE_DEADLINE)[-1]['roots']]),lock_root=root)
    short = ROOTS[9]/PARTS[0]; long = ROOTS[9]/PARTS[1]
    for stage in ('pre','train2','post'):
        (short/'runs'/stage).symlink_to(OLD_ROOTS[9]/PARTS[0]/'runs'/stage,target_is_directory=True)
        (short/'cpu'/stage).symlink_to(OLD_ROOTS[9]/PARTS[0]/'cpu'/stage,target_is_directory=True)
    (long/'runs/train96').symlink_to(OLD_ROOTS[9]/PARTS[1]/'runs/train96',target_is_directory=True)
    (long/'cpu/train96').symlink_to(OLD_ROOTS[9]/PARTS[1]/'cpu/train96',target_is_directory=True)
    h.sample(accounts(L9_DEADLINE),ROOTS[9])


def docker(mode,index,stage=None):
    special = mode in ('checkpoint-cpu','retained-cpu')
    args = m.docker('cpu' if special else mode,index,None if special else stage)
    if special:
        args[-3:] = [mode,str(m.LEVEL),str(index)]
        args[args.index('--name')+1] = ROOTS[m.LEVEL].name+('-short-' if index==0 else '-long-')+mode
    args[2:2] = sum((['-v',f'{p}:{p}:ro'] for p in [*OLD_ROOTS.values(),*FAILED_ROOTS.values(),OLD_SOURCE,FAILED_SOURCE]),[])
    return args


def native_cpu():
    """Bounded native state check; never deserialize model/Adam shards."""
    import numpy as np
    import random
    import torch
    from types import SimpleNamespace
    from unittest.mock import patch
    from agent_system.sc2_resume import restore_environment
    out = a.ROOT/'runs/train96'; proof = []
    result = a.read(out/'result.json')
    inventory = m.checkpoint_inventory(out,result,[32,64,96])
    for step in (32,64,96):
        cp = out/f'checkpoints/global_step_{step}'
        def small(name):
            p = cp/name
            if not 0<p.stat().st_size<1024**2: raise ValueError('Small native state only')
            return torch.load(p,map_location='cpu',weights_only=False)
        state = small('sc2_state.pt')
        if state['global_step']!=step or state['empty_policy_batches']: raise ValueError('Closed native step required')
        py,nr,tr = state['driver_rng']
        random.Random().setstate(py);np.random.RandomState().set_state(nr);torch.Generator().set_state(tr)
        for label in ('train_env','val_env'):
            saved=state[label]
            raw=SimpleNamespace(**{k:saved[k] for k in ('seed','env_num','group_n','is_train')},reset_index=0,
                training_rng=np.random.RandomState(0),validation_rng=np.random.RandomState(0))
            with patch.dict(os.environ,SC2_TRAIN_SEED_PROTOCOL='same_uniform101'):
                restore_environment(SimpleNamespace(envs=raw,memory=None),saved)
            if label=='train_env' and (raw.reset_index!=step or raw.seed!=0 or raw.group_n!=8 or raw.env_num!=1):
                raise ValueError('Wrong native seed position')
        for rank in range(8):
            extra=small(f'actor/extra_state_world_size_8_rank_{rank}.pt');rng=extra['rng']
            if extra['lr_scheduler']['last_epoch']!=step: raise ValueError('Wrong native scheduler step')
            for name in ('cpu','cuda'):
                if not isinstance(rng[name],torch.Tensor) or not rng[name].numel(): raise ValueError('Missing rank RNG')
            torch.Generator().set_state(rng['cpu']);random.Random().setstate(rng['random']);np.random.RandomState().set_state(rng['numpy'])
        if not small('data.pt'): raise ValueError('Missing dataloader state')
        proof.append(dict(step=step,driver_rng=True,rank_rng=8,scheduler_step=step,next_reset_index=step))
    if torch.cuda.is_initialized(): raise RuntimeError('CPU initialized CUDA')
    a.save(a.ROOT/'checkpoint-readiness.json',dict(passed=True,cuda_initialized=False,
        steps=proof,inventory=inventory,runtime_sha=RUNTIME_SHA,checked_at=time.time()),lock_root=ROOTS[9])


def verify_retained(write=False):
    terminal=old_terminal();prior_failure=failed_r2_terminal()
    try:
        m.ROOTS=OLD_ROOTS; m.configure(9)
        for index,stages in ((0,('pre','train2','post')),(1,('train96',))):
            m.f.select(index)
            for stage in stages: m.verify(stage,write=False)
        out=a.ROOT/'runs/train96'
        result=a.read(out/'result.json')
        inv=m.checkpoint_inventory(out,result,[32,64,96])
    finally:
        configure(9);f.select(1)
    ready=a.read(ROOTS[9]/PARTS[1]/'checkpoint-readiness.json')
    if not ready['passed'] or ready['cuda_initialized'] or ready['inventory']!=inv:
        raise RuntimeError('Retained native CPU inventory differs')
    proof=dict(passed=True,retained_games=784,retained_updates=96,terminal=terminal,prior_failure=prior_failure,
        checkpoint_inventory=inv,verifier_sha=a.read(ROOTS[9]/'deployment.json')['controller_sha'],
        old_failed_state_sha256=m.sha256(OLD_ROOTS[9]/'queue-state.json'),checked_at=time.time())
    if write: a.save(ROOTS[9]/'retained-acceptance.json',proof,lock_root=ROOTS[9])
    return proof


def regressions(host_only=False):
    m.ROOTS=ROOTS
    m.regressions(host_only)
    if not host_only:
        r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromName('test_qwen_l9l10_continue197'))
        if not r.wasSuccessful() or r.skipped: raise RuntimeError('Continuation tests failed')
    p=ROOTS[9]/('host-regressions.json' if host_only else PARTS[0]+'/regressions.json')
    proof=a.read(p);proof['controller_sha']=a.read(ROOTS[9]/'deployment.json')['controller_sha']
    if not host_only: proof['continuation_tests']=r.testsRun;proof['tests']+=r.testsRun
    a.save(p,proof,lock_root=ROOTS[9])


def check_cpu():
    cfg=a.read(ROOTS[9]/'deployment.json')
    a.clean(a.SOURCE,cfg['controller_sha']);a.clean(a.ORCH,a.ORCH_SHA)
    for p in (ROOTS[9]/'host-regressions.json',ROOTS[9]/PARTS[0]/'regressions.json'):
        proof=a.read(p)
        if not proof['passed'] or proof['skips'] or proof['cuda_initialized'] or proof['controller_sha']!=cfg['controller_sha']:
            raise RuntimeError('Matching actual CPU regressions required')
        if p.name=='regressions.json' and proof.get('continuation_tests',0)<=0:
            raise RuntimeError('Continuation regression evidence required')
    for root in ROOTS.values():
        a.clean(root/'runtime',RUNTIME_SHA)
        for part in PARTS:
            p=a.read(root/part/'readiness.json')
            if not p['passed'] or p['cuda_initialized'] or p['runtime_sha']!=RUNTIME_SHA: raise RuntimeError('All actual launcher gates required')
    for level,index,stage in CPU_PROBES:
        owner=ROOTS[level]/PARTS[index];p=a.read(owner/f'cpu/hook-{stage}/cpu-hook-preflight.json')
        if (not p['passed'] or p['worker']['cuda_initialized'] or p['worker']['cuda_device_count']
                or p['model_loaded'] or p['natural_games'] or p['optimizer_updates']
                or p['runtime_environment']['resolved_config_sha256']!=m.sha256(owner/f'cpu/{stage}/resolved_config.json')):
            raise RuntimeError('Actual no-GPU full runtime hook required')


def verify_probe(stage):
    if m.LEVEL==10: return m.verify_probe(stage)
    owner=ROOTS[9]/PARTS[1];p=a.read(owner/'gpu-preflight/gpu-preflight.json')
    if (stage!='gpu-preflight' or not p['passed'] or len(p['ranks'])!=8
            or len({r['cuda_uuid'] for r in p['ranks']})!=8 or p['nccl_sums']!=[28.0]*8
            or p['model_loaded'] or p['natural_games'] or p['optimizer_updates']
            or p['runtime_environment']['resolved_config_sha256']!=m.sha256(owner/'cpu/eval96/resolved_config.json')):
        raise RuntimeError('Exact eval eight-GPU preflight required')


def verify(stage):
    if stage=='train96':
        deadline=a.read(ROOTS[m.LEVEL]/'dispatch.json')['deadline']
        with (a.ROOT/'checkpoint-cpu.log').open('x') as log:
            sp.run(docker('checkpoint-cpu',1),stdout=log,stderr=sp.STDOUT,check=True,timeout=min(300,deadline-45-time.time()))
    m.verify(stage,write=True)


def queue():
    check_cpu(); master=ROOTS[9]
    with (master/'queue.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (master/'queue-state.json').exists() or any((r/'dispatch.json').exists() for r in ROOTS.values()):
            raise RuntimeError('Already queued; no retry')
        state=dict(phase='verifying-retained',completed=[],retained_games=784,retained_updates=96,
                   new_games=800,new_updates=96,deadline=SUITE_DEADLINE)
        try:
            a.save(master/'queue-state.json',state,lock_root=master)
            if time.time()>=L9_DEADLINE-45: raise TimeoutError('Original L9 budget expired')
            verify_retained(write=True)
            a.save(master/'suite-dispatch.json',dict(start=START,deadline=SUITE_DEADLINE,gpu_hours=192,
                resumed_at=time.time(),clock_inherited=True),lock_root=master)
            for level,root in ROOTS.items():
                configure(level); first_index=1 if level==9 else 0
                m.admit(first_index,'eval96' if level==9 else 'arm',L9_DEADLINE if level==9 else SUITE_DEADLINE,receipt_name='arm')
                start=START if level==9 else time.time()
                deadline=L9_DEADLINE if level==9 else min(start+m.ARM_SECONDS,SUITE_DEADLINE)
                a.save(root/'dispatch.json',dict(start=start,deadline=deadline,suite_deadline=SUITE_DEADLINE,
                    gpu_hours=96,clock_inherited=level==9,new_games=8 if level==9 else 792,
                    new_updates=0 if level==9 else 96,resumed_at=time.time()),lock_root=master)
                state.update(phase='gpu-preflight',level=level,arm_deadline=deadline)
                a.save(master/'queue-state.json',state,lock_root=master)
                owner=root/PARTS[first_index];probe_stage='eval96' if level==9 else 'train2'
                h.run_stages(['gpu-preflight'],lambda _:docker('gpu-preflight',first_index,probe_stage),verify_probe,
                    accounts(deadline),owner,owner/'gpu-preflight-supervision',master,deadline,
                    admit=lambda _:m.admit(first_index,'gpu-preflight',deadline))
                for index in ([1] if level==9 else [0,1]):
                    cfg=f.select(index)
                    if index==1 and level==10:
                        a.save(a.ROOT/'resume-contract.json',m.contract_for(),lock_root=master)
                        with (a.ROOT/'parent-cpu.log').open('x') as log:
                            sp.run(docker('parent-cpu',1),stdout=log,stderr=sp.STDOUT,check=True,timeout=min(600,deadline-45-time.time()))
                        if not a.read(a.ROOT/'parent-readiness.json')['actual_parent_verified']: raise RuntimeError('Own native CP2 required')
                    a.save(a.ROOT/'dispatch.json',dict(start=start,deadline=deadline,clock_shared=True),lock_root=master)
                    state.update(phase='running-unverified',part=PARTS[index]);a.save(master/'queue-state.json',state,lock_root=master)
                    terminal=h.run_stages(cfg['stages'],lambda s:docker('stage',index,s),verify,
                        accounts(deadline),a.ROOT,a.ROOT/'host-supervision',master,deadline,
                        admit=lambda s:m.admit(index,s,deadline))
                    a.save(a.ROOT/'state.json',terminal,lock_root=master)
                    state['completed'].append(f'L{level}/'+PARTS[index]);a.save(master/'queue-state.json',state,lock_root=master)
                a.save(root/'arm-state.json',dict(phase='completed',exit_code=0,deadline=deadline,
                    retained_acceptance=m.sha256(master/'retained-acceptance.json') if level==9 else None,
                    newly_executed=['eval96'] if level==9 else ['pre','train2','post','train96','eval96'],
                    learning_validated=False,finished_at=time.time()),lock_root=master)
            state.update(phase='completed',exit_code=0,learning_validated=False,finished_at=time.time())
            a.save(master/'queue-state.json',state,lock_root=master)
        except BaseException as exc:
            state.update(phase='failed',error_type=type(exc).__name__,error=str(exc),finished_at=time.time())
            a.save(master/'queue-state.json',state,lock_root=master);raise


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode',choices=['prepare','queue','verify-retained','cpu','cpu-command','regressions','host-regressions',
        'regressions-command','retained-cpu','retained-cpu-command','checkpoint-cpu','parent-cpu','stage',
        'cpu-hook','cpu-hook-command','gpu-preflight'])
    p.add_argument('level',type=int,nargs='?',choices=(9,10));p.add_argument('index',type=int,nargs='?',choices=(0,1));p.add_argument('stage',nargs='?')
    arg=p.parse_args()
    if arg.mode in ('regressions','host-regressions'): regressions(arg.mode=='host-regressions');return
    if arg.mode=='prepare': prepare();return
    configure(arg.level or 9)
    if arg.mode=='queue': queue();return
    if arg.mode=='verify-retained': print(json.dumps(verify_retained()));return
    if arg.level is None or arg.index is None:p.error('Exact level and part required')
    if arg.mode.endswith('-command'):print(json.dumps(docker(arg.mode.removesuffix('-command'),arg.index,arg.stage)));return
    if arg.mode=='cpu':m.cpu(arg.index)
    elif arg.mode=='parent-cpu':f.parent_cpu(arg.index)
    elif arg.mode in ('checkpoint-cpu','retained-cpu'):f.select(arg.index);native_cpu()
    elif arg.mode in ('cpu-hook','gpu-preflight'):
        cfg=f.select(arg.index)
        if arg.stage not in cfg['stages']:raise ValueError('Undeclared probe')
        config=a.ROOT/f'cpu/{arg.stage}/resolved_config.json'
        if arg.mode=='cpu-hook':m.probe.check_hook_cpu(a.ROOT/f'cpu/hook-{arg.stage}',Path('/tmp/hook-'+arg.stage),config,environment_loader=m.runtime_environment)
        elif (arg.level,arg.index,arg.stage) in ((9,1,'eval96'),(10,0,'train2')):
            m.probe.run(a.ROOT/'gpu-preflight',Path('/tmp/probe-ray'),config,environment_loader=m.runtime_environment)
        else:raise ValueError('Undeclared GPU probe')
    else:
        cfg=f.select(arg.index);a.clean(a.SOURCE,cfg['controller_sha']);a.clean(a.ROOT/'runtime',cfg['runtime_sha'])
        args,env,_=m.invocation(cfg,arg.stage)
        fd=os.open(a.ROOT/(arg.stage+'-entry.log'),os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
        os.dup2(fd,1);os.dup2(fd,2);os.close(fd);os.chdir(a.ROOT/'runtime');os.execvpe(args[0],args,env)


if __name__=='__main__':main()
