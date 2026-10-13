"""Approved L8 random96 then three-arm paired64; never mutate the L10 predecessor."""
import argparse
import copy
import fcntl
import json
import math
import os
from pathlib import Path
import shutil
import subprocess as sp
import sys
import time
import unittest

import qwen_l7same_fresh197 as fresh
import qwen_l9l10_same197 as storage
import l7_matrix256197 as receipts
import qwen_l8_cuda_probe_v2 as probe
from agent_system.sc2_policy_resume import checkpoint_names, normalized_protocol, prefix_files, sha256, verify_contract
from agent_system.sc2_seed_protocol import ablation_seeds
from qwen_l8random_plan import ROOT, EVAL_ROOT, SOURCE_PARENT, PARTS, SEEDS, SEED_SHA256, validate
from qwen_l8random_plan import OLD_ROOT, OLD_EVAL_ROOT, OLD_SOURCE_PARENT, SELECTION_ROOT, SELECTION_SEEDS, SELECTION_SHA256
from qwen_l8random_plan import R2_ROOT, R2_EVAL_ROOT, R2_SOURCE_PARENT

a,f,h=fresh.a,fresh.f,fresh.h
PROTOCOL='independent_uniform101'
GROUP='mixed_seed_ablation'
BASE=Path('/var/jfsCache/sc2-qwen-l8same96-197-20260926-r2/qwen-same/short')
BASE_SHA='eef0f049bb09b7a51188ae67a6c35436a3bf055f'
BASE_CONFIG=Path('/var/jfsCache/sc2-qwen-l8same96-197-20260926-r1/qwen-same/short/cpu/train2/resolved_config.json')
BASE_CONFIG_SHA256='77cd457af0cfc64f0ebe0aab690e33af5af7958e336b13cb396766bd0ac7efa6'
PRIOR_MASTER=Path('/var/jfsCache/sc2-qwen-l9same96-197-20260927-r3')
PRIOR_ROOT=Path('/var/jfsCache/sc2-qwen-l10same96-197-20260927-r3')
PRIOR_SHA='1c6cf60b111570ef13f9817d0b1b16fb774546f5'
PRIOR_CONTROLLER='5152bbb74def8d0bd54d172c70bf18dfa2fed90a'
PRIOR_DEADLINE=1790561940.3084953
PRIOR_SUITE_DEADLINE=1790568708.224269
TRAIN_SECONDS,EVAL_SECONDS,SUITE_SECONDS=16*3600,6*3600,22*3600
MODEL_KIND='qwen'
DIFFICULTY='CheatVision'
PRUNE_AFTER_SELECTION=True
NEW_GAMES=1112
TRAIN_GPU_HOURS,SUITE_GPU_HOURS,TRAIN_FREE_GIB=128,176,352
CPU_PROBES=((0,'pre'),(0,'train2'),(1,'train96'))
AUTHORIZATION=('Sep28 user approved controlled r3 fresh original-Qwen L8 independent-seed96 after unchanged L10; '
    'exact historical baseline-file readonly bind fix; 792 training-chain games/96PPO plus128 independent selection games and192 test games; '
    '197 eightGPU serial; train+selection16h/128GPUh/256GiB, test6h/48GPUh/32GiB, suite22h/176GPUh/288GiB; '
    'selection<=4h/32GPUh/8GiB within component; fullCP2/32/64/96; latest2+best+CP2/final protected; '
    'only own unprotected completed intermediate checkpoints may be pruned after all selection acceptance; '
    'nine r1/r2/r3 roots counted; admission352GiB train and128GiB eval; no old deletion/retry/CP192/successor')


def configure():
    fresh.ROOT,fresh.PARTS,fresh.PREFIX=ROOT,PARTS,ROOT.name+'-'
    f.SUITE,f.PARTS,f.CONTAINER_PREFIX=ROOT,PARTS,ROOT.name+'-'
    f.DOCKER_SCRIPT=a.HERE/'qwen_l8random197.py'
    f.parent_for=parent_for
    f.invocation,f.verify=invocation,verify


def parent_for(index):
    if index!=1: raise ValueError('Only own complete native CP2')
    return ROOT/PARTS[0]


def accounts(deadline):
    # Charge the shared source conservatively to both components, once to suite.
    return [dict(roots=[OLD_ROOT,OLD_SOURCE_PARENT,R2_ROOT,R2_SOURCE_PARENT,ROOT,SOURCE_PARENT],receipt_root=ROOT/'train-storage',limit=256*a.GIB,deadline=deadline),
        dict(roots=[OLD_EVAL_ROOT,OLD_SOURCE_PARENT,R2_EVAL_ROOT,R2_SOURCE_PARENT,EVAL_ROOT,SOURCE_PARENT],receipt_root=EVAL_ROOT/'eval-storage',limit=32*a.GIB,deadline=deadline),
        dict(roots=[SELECTION_ROOT],receipt_root=ROOT/'selection-storage',limit=8*a.GIB,deadline=deadline),
        dict(roots=[OLD_ROOT,OLD_EVAL_ROOT,OLD_SOURCE_PARENT,R2_ROOT,R2_EVAL_ROOT,R2_SOURCE_PARENT,ROOT,EVAL_ROOT,SOURCE_PARENT],receipt_root=ROOT/'suite-storage',limit=288*a.GIB,deadline=deadline)]


def prepare():
    if ROOT.exists() or EVAL_ROOT.exists() or a.SOURCE!=SOURCE_PARENT/'code':
        raise RuntimeError('Fresh exact roots required; no overwrite/retry')
    validate();sha=a.cmd(['git','-C',a.SOURCE,'rev-parse','HEAD'])
    a.clean(a.SOURCE,sha);a.clean(a.ORCH,a.ORCH_SHA)
    base=a.read(BASE/'deployment.json')
    if (base['runtime_sha'],base['model_kind'],base['difficulty'],base['seed_protocol'])!=(BASE_SHA,'qwen','CheatVision','same_uniform101'):
        raise RuntimeError('Exact accepted L8 same template required')
    if (BASE/'cpu/train2/resolved_config.json').resolve(strict=True)!=BASE_CONFIG:
        raise RuntimeError('Historical retained-prefix config link changed')
    baseline_config()
    ROOT.mkdir();(ROOT/'train-storage').mkdir();(ROOT/'suite-storage').mkdir();(ROOT/'selection-storage').mkdir()
    a.STORAGE_LOCK_ROOT=ROOT
    sp.run(['git','clone','--quiet','--no-local',str(a.SOURCE),str(ROOT/'runtime')],check=True,timeout=120)
    a.cmd(['git','-C',ROOT/'runtime','checkout','--quiet','--detach',sha])
    for index,part in enumerate(PARTS):
        owner=ROOT/part;owner.mkdir(parents=True)
        for name in ('runs','cpu','tmp','tmp/task-home','tmp/cache','tmp/cuda-cache'): (owner/name).mkdir()
        (owner/'runtime').symlink_to(ROOT/'runtime',target_is_directory=True)
        cfg=copy.deepcopy(base)
        for key in ('prior_failed_root','retained_prefix','fixed_deadline','original_start','deadline'): cfg.pop(key,None)
        cfg.update(runtime_sha=sha,controller_sha=sha,controller_source=str(a.SOURCE),
            orchestration_sha=a.ORCH_SHA,seed_protocol=PROTOCOL,seed_group_mode=GROUP,
            training_seeds=[ablation_seeds(PROTOCOL,0,i,1,8) for i in range(96)],
            stages=['pre','train2','post'] if index==0 else ['train96','eval96'],
            games=[8,16,8] if index==0 else [752,8],updates=[0,2,0] if index==0 else [94,0],
            run_prefix=ROOT.name+('-short' if index==0 else '-long'),worker_hook='l7_followup_hook.install',
            wall_seconds=TRAIN_SECONDS,gpu_hours=128,output_limit_bytes=256*a.GIB,saved_steps=[2,32,64,96],
            first_dispatch_by=PRIOR_DEADLINE+4*3600,queue_expires=PRIOR_DEADLINE+4*3600,
            no_retry=True,original_weights=True,no_long_training=False,successors_authorized=True,
            authorization=AUTHORIZATION,host_stage_entry_log=True,storage_supervision='host-guardian-v1',
            predecessor=str(PRIOR_ROOT if index==0 else ROOT/PARTS[0]),
            limitation='Mixed-seed advantage can mix scenario difficulty; sparse-save timing differs; no learning claim')
        a.save(owner/'deployment.json',cfg,lock_root=ROOT)
    a.save(ROOT/'deployment.json',dict(runtime_sha=sha,controller_sha=sha,controller_source=str(a.SOURCE),
        orchestration_sha=a.ORCH_SHA,authorization=AUTHORIZATION,parts=PARTS,predecessor=str(PRIOR_ROOT),
        predecessor_deadline=PRIOR_DEADLINE,train_seconds=TRAIN_SECONDS,eval_seconds=EVAL_SECONDS,
        suite_seconds=SUITE_SECONDS,gpu_hours=176,new_games=1112,new_updates=96,
        seed_sha256=SEED_SHA256,eval_seeds=SEEDS,saved_steps=[2,32,64,96],
        selection_seeds=SELECTION_SEEDS,selection_sha256=SELECTION_SHA256,selection_after_training=True,
        retention=dict(latest=2,protected=[2,96],best_metric='validation32 wins',tie='earlier step',
            no_training_or_test_selection=True,prune_after_selection=True),
        storage_roots=[str(p) for p in (OLD_ROOT,OLD_EVAL_ROOT,OLD_SOURCE_PARENT,R2_ROOT,R2_EVAL_ROOT,R2_SOURCE_PARENT,ROOT,EVAL_ROOT,SOURCE_PARENT)],
        no_retry=True,successors_authorized=False),lock_root=ROOT)
    import qwen_l8random_eval197 as evaluation
    evaluation.prepare(base,sha)
    evaluation.prepare(base,sha,selection=True)
    h.sample(accounts(PRIOR_DEADLINE+4*3600),ROOT)


def invocation(cfg,stage,dry=False):
    if (cfg['difficulty'],cfg['model_kind'],cfg['seed_protocol'],cfg['seed_group_mode'])!=(DIFFICULTY,MODEL_KIND,PROTOCOL,GROUP):
        raise ValueError('Exact L8 Qwen independent-seed protocol required')
    args,env,out=fresh.BASE_INVOCATION(cfg,stage,dry)
    if MODEL_KIND=='spb': args += ["+ray_init.runtime_env.env_vars.SC2_RESET_CONCURRENCY='1'"]
    if stage=='train96': args=[x for x in args if not x.startswith('trainer.save_freq=')]+['trainer.save_freq=32']
    args += ["+ray_init.runtime_env.env_vars.SC2_L8_RENDEZVOUS_LOW_PORT='1'"]
    env['RAY_TMPDIR']='/tmp/l8r-'+stage
    h.terminal_launch(cfg,args,env,ROOT)
    return args,env,out


def docker(mode,index,stage=None):
    gpu=mode in ('stage','gpu-preflight')
    special=mode in ('cpu-hook','checkpoint-cpu')
    args=fresh.docker('stage' if gpu else ('cpu' if special else mode),index,stage if gpu else None)
    if mode in ('cpu-hook','gpu-preflight'):
        cfg=a.read(a.ROOT/'deployment.json')
        if stage not in cfg['stages']: raise ValueError('Undeclared probe')
        ev=a.read(a.ROOT/f'cpu/{stage}/resolved_config.json')['ray_init']['runtime_env']['env_vars']
        for i,x in enumerate(args):
            if x.startswith('PYTHONPATH='): args[i]='PYTHONPATH='+ev['PYTHONPATH']
        if not gpu: args[args.index('--memory')+1]='16g'
    if special or mode=='gpu-preflight':
        args[args.index('--name')+1]=ROOT.name+('-short-' if index==0 else '-long-')+mode+('-'+stage if stage else '')
    tail=3 if gpu else 2
    args[-tail:]=[mode,str(index)]+([stage] if stage else [])
    # r2 same's train2 is a symlink to retained r1: bind its exact hash-pinned
    # real file, not a parent tree whose external symlink is absent in Docker.
    if mode=='cpu': args[2:2]=['-v',f'{BASE_CONFIG}:{BASE_CONFIG}:ro']
    return args


def runtime_environment(path,ray_tmp):
    path=Path(path)
    if not 0<path.stat().st_size<1024**2: raise ValueError('Small resolved config required')
    cfg=a.read(path);env=copy.deepcopy(cfg['ray_init']['runtime_env']);ev=env['env_vars']
    if (ev.get('SC2_ACCEPTANCE_STAGE') not in ('pre','train2','post','train96','eval96')
            or ev.get('SC2_DIFFICULTY')!=DIFFICULTY or ev.get('SC2_EXPECTED_DIFFICULTY')!=DIFFICULTY
            or ev.get('SC2_TRAIN_SEED_PROTOCOL')!=PROTOCOL or cfg['algorithm']['sc2_policy_credit']['seed_group_mode']!=GROUP
            or env.get('worker_process_setup_hook')!='l7_followup_hook.install' or ev.get('SC2PATH')!='/assets/StarCraftII'
            or str(ev.get('SC2_L8_RENDEZVOUS_LOW_PORT'))!='1'
            or not all(ev.get(k) for k in ('PYTHONPATH','SC2_EVAL_SEEDS_LOG_PATH','SC2_RUNTIME_LOG_ROOT'))
            or cfg['trainer']['n_gpus_per_node']!=8
            or cfg['trainer']['val_only']!=(ev['SC2_ACCEPTANCE_STAGE'] in ('pre','post','eval96'))):
        raise ValueError('Complete actual L8 random runtime required')
    ev.update(TMPDIR=str(ray_tmp),RAY_TMPDIR=str(ray_tmp))
    return env,dict(resolved_config_sha256=sha256(path),env_var_names=sorted(ev),
        overridden_env_vars=['RAY_TMPDIR','TMPDIR'],worker_process_setup_hook=env['worker_process_setup_hook'],
        stage=ev['SC2_ACCEPTANCE_STAGE'],required_worker_module='refinery_order_eval')


def baseline_config():
    if (not BASE_CONFIG.is_file() or BASE_CONFIG.is_symlink()
            or not 0<BASE_CONFIG.stat().st_size<1024**2
            or sha256(BASE_CONFIG)!=BASE_CONFIG_SHA256):
        raise RuntimeError('Exact historical same config file/hash required')
    return a.read(BASE_CONFIG)


def compare_same(config):
    baseline=normalized_protocol(baseline_config())
    expected=copy.deepcopy(baseline)
    expected['algorithm']['sc2_policy_credit']['seed_group_mode']=GROUP
    expected['ray_init']['runtime_env']['env_vars']['SC2_TRAIN_SEED_PROTOCOL']=PROTOCOL
    actual=normalized_protocol(config)
    if actual!=expected: raise RuntimeError('Unapproved difference versus frozen L8 same config')


def cpu(index):
    f.cpu(index)
    from sc2.data import Difficulty
    if getattr(Difficulty,DIFFICULTY).value!={'CheatVision':8,'CheatMoney':9}[DIFFICULTY]:
        raise RuntimeError('SC2 difficulty mapping changed')
    for stage in a.read(a.ROOT/'deployment.json')['stages']:
        p=a.ROOT/f'cpu/{stage}/resolved_config.json';cfg=a.read(p);runtime_environment(p,'/tmp/probe-ray')
        if stage in ('train2','train96'): compare_same(cfg)
        if stage=='train96' and cfg['trainer']['save_freq']!=32: raise RuntimeError('Approved full sparse cadence required')
    a.save(a.ROOT/'baseline-config-comparison.json',dict(passed=True,baseline=str(BASE),baseline_sha=BASE_SHA,
        config_source=str(BASE_CONFIG),config_sha256=BASE_CONFIG_SHA256,
        scientific_changes=['seed_protocol','seed_group_mode'],native_protocol_equal_otherwise=True,
        operational_changes=['checkpoint cadence','run/output/clock/resource controls'],checked_at=time.time()))


def verify(stage,write=True):
    out=a.ROOT/'runs'/stage
    result,evidence=a.verify_common(out,stage,752 if stage=='train96' else (16 if stage=='train2' else 8))
    if any(a.read(out/n).get('metrics_precision')!='binary64-v1' for n in ('manifest.json','result.json')):
        raise RuntimeError('Full precision required')
    if stage in ('train2','train96'):
        lo,hi=(1,2) if stage=='train2' else (3,96)
        if (result['start_step'],result['last_global_step'],result['completed_steps'])!=(lo-1,hi,hi-lo+1) or not result['checkpoint_complete']:
            raise RuntimeError('Exact returned PPO interval required')
        metrics=a.read(out/'metrics.json')
        audits=[json.loads(x) for x in (out/'checkpoints/sc2_policy_credit_audit.jsonl').read_text().splitlines()]
        f.verify_updates(audits,metrics,lo,hi)
        if (any(not math.isfinite(r[k]) or r[k]<=0 for r in metrics for k in ('actor/grad_norm','timing_s/update_actor'))
                or any(not math.isfinite(r['policy_credit/invalid_advantage_max']) or r['policy_credit/invalid_advantage_max']>0 for r in metrics)
                or any(r['real_answers']<=0 or r['real_answers']!=r['valid_answers'] for r in audits)):
            raise RuntimeError('Actual finite positive PPO/valid answers required')
        rows=[json.loads(x) for x in (out/'training_seeds.jsonl').read_text().splitlines()]
        if len(rows)!=hi-lo+1 or any(r['reset_index']!=i or r['base_seed']!=0 or r['seed_protocol']!=PROTOCOL
                or r['seeds']!=ablation_seeds(PROTOCOL,0,i,1,8) for i,r in enumerate(rows,lo-1)):
            raise RuntimeError('Exact independent seed ledger required')
        outcomes=[json.loads(x) for x in (out/'episode_outcomes.jsonl').read_text().splitlines()]
        if (len(outcomes)!=(hi-lo+1)*8 or {(r['reset_index'],r['env_index']) for r in outcomes}!=
                {(i,e) for i in range(lo-1,hi) for e in range(8)} or any(not r['terminated'] or r['truncated'] for r in outcomes)):
            raise RuntimeError('Unique natural training outcomes required')
        steps=[2] if stage=='train2' else [32,64,96]
        evidence.update(ppo_updates=hi-lo+1,checkpoints=steps,checkpoint_inventory=storage.checkpoint_inventory(out,result,steps))
        if stage=='train96':
            resume=a.read(out/'checkpoints/resume_state.json')
            if (resume['from_checkpoint']!=str(ROOT/PARTS[0]/'runs/train2/checkpoints/global_step_2')
                    or resume['global_step']!=2 or resume['next_reset_index']!=2 or resume['source']!='checkpoint'
                    or resume['next_seeds']!=ablation_seeds(PROTOCOL,0,2,1,8)
                    or not resume['model_optimizer_dataloader_load_returned']):
                raise RuntimeError('Own native independent CP2 actual load required')
            evidence['resume']=resume
    elif stage in ('pre','post','eval96'):
        step={'pre':0,'post':2,'eval96':96}[stage]
        cp=None if step==0 else str(ROOT/PARTS[0]/'runs/train2/checkpoints/global_step_2' if step==2 else a.ROOT/'runs/train96/checkpoints/global_step_96')
        p=a.read(out/'checkpoint_evaluation.json')
        seeds=[json.loads(x)['seeds'] for x in (out/'evaluation_seeds.jsonl').read_text().splitlines()]
        if (result['training_updates']!=0 or not p['val_only'] or p['optimizer_updates']!=0
                or p['loaded_global_step']!=step or p['checkpoint']!=cp or p['checkpoint_load_returned']!=bool(step)
                or p['game_seeds']!=a.EVAL_SEEDS or seeds!=[a.EVAL_SEEDS]): raise RuntimeError('Diagnostic eval load/RNG/zero-update required')
        for rank in range(8):
            rng=a.read(out/f'sampling-rank{rank}.json')
            if (rng['rank'],rng['seed'])!=(rank,rank): raise RuntimeError('Rank seed mismatch')
            reference=ROOT/PARTS[0]/f'runs/{"pre" if stage=="post" else "post"}/sampling-rank{rank}.json'
            if stage!='pre' and not f.previous.paired_rng_matches(rng,a.read(reference),rank): raise RuntimeError('Paired RNG mismatch')
    else: raise ValueError('Undeclared stage')
    files=sorted((out/'sc2-logs').rglob('*.SC2Replay'));names=[str(p.relative_to(out)) for p in files]
    expected=752 if stage=='train96' else (16 if stage=='train2' else 8)
    if (len(files)!=expected or len({p.resolve() for p in files})!=expected
            or any(f'/Flat128_{DIFFICULTY}_Air/' not in n for n in names)
            or any(p.stat().st_size<=0 or not p.resolve().is_relative_to(out.resolve()) for p in files)):
        raise RuntimeError('Exact L8 natural replays required')
    if stage in ('pre','post','eval96') and result['replays']!={n:sha256(p) for n,p in zip(names,files)}:
        raise RuntimeError('Diagnostic replay hashes differ')
    if write: a.save(a.ROOT/f'acceptance-{stage}.json',dict(result=result,evidence=evidence,checked_at=time.time()))


def contract_for():
    owner=ROOT/PARTS[0]
    c=dict(version='accepted-qwen-l8-random-full-state-prefix-v1',parent=str(owner),
        checkpoint=str(owner/'runs/train2/checkpoints/global_step_2'),parent_sha=a.read(owner/'deployment.json')['runtime_sha'],
        start_step=2,target_step=96,driver_rng_unavailable_accepted=False,files={n:sha256(owner/n) for n in prefix_files()})
    verify_contract(c);return c


def checkpoint_cpu(index):
    """Read only small native state; model/Adam shards are stat-only here."""
    import numpy as np
    import random
    import torch
    from types import SimpleNamespace
    from unittest.mock import patch
    from agent_system.sc2_resume import restore_environment
    f.select(index);stage='train2' if index==0 else 'train96'
    out=a.ROOT/'runs'/stage;steps=[2] if index==0 else [32,64,96]
    inventory=storage.checkpoint_inventory(out,a.read(out/'result.json'),steps)
    for step in steps:
        cp=out/f'checkpoints/global_step_{step}'
        def small(name):
            path=cp/name
            if not 0<path.stat().st_size<1024**2: raise ValueError('Small native state only')
            return torch.load(path,map_location='cpu',weights_only=False)
        state=small('sc2_state.pt')
        if state['global_step']!=step or state['empty_policy_batches']: raise ValueError('Closed native step required')
        py,nr,tr=state['driver_rng'];random.Random().setstate(py);np.random.RandomState().set_state(nr);torch.Generator().set_state(tr)
        for label in ('train_env','val_env'):
            saved=state[label]
            raw=SimpleNamespace(**{k:saved[k] for k in ('seed','env_num','group_n','is_train')},reset_index=0,
                training_rng=np.random.RandomState(0),validation_rng=np.random.RandomState(0))
            with patch.dict(os.environ,SC2_TRAIN_SEED_PROTOCOL=PROTOCOL): restore_environment(SimpleNamespace(envs=raw,memory=None),saved)
            if label=='train_env' and (raw.reset_index!=step or raw.seed!=0 or raw.group_n!=8 or raw.env_num!=1):
                raise ValueError('Wrong native independent seed position')
        for rank in range(8):
            extra=small(f'actor/extra_state_world_size_8_rank_{rank}.pt');rng=extra['rng']
            if extra['lr_scheduler']['last_epoch']!=step: raise ValueError('Native scheduler step mismatch')
            for name in ('cpu','cuda'):
                if not isinstance(rng[name],torch.Tensor) or not rng[name].numel(): raise ValueError('Missing rank RNG')
            torch.Generator().set_state(rng['cpu']);random.Random().setstate(rng['random']);np.random.RandomState().set_state(rng['numpy'])
        if not small('data.pt'): raise ValueError('Dataloader state missing')
    if torch.cuda.is_initialized(): raise RuntimeError('CPU initialized CUDA')
    a.save(a.ROOT/'checkpoint-readiness.json',dict(passed=True,cuda_initialized=False,steps=steps,
        inventory=inventory,runtime_sha=a.read(a.ROOT/'deployment.json')['runtime_sha'],checked_at=time.time()))


def verify_host(stage):
    if stage in ('train2','train96'):
        deadline=a.read(ROOT/'dispatch.json')['deadline'];index=0 if stage=='train2' else 1
        with (a.ROOT/'checkpoint-cpu.log').open('x') as log:
            sp.run(docker('checkpoint-cpu',index),stdout=log,stderr=sp.STDOUT,check=True,
                   timeout=min(300,deadline-45-time.time()))
        p=a.read(a.ROOT/'checkpoint-readiness.json')
        if not p['passed'] or p['cuda_initialized']: raise RuntimeError('Native small-state gate failed')
    verify(stage)
    if stage in ('train2','train96'):
        import qwen_l8random_retention as retention
        retention.publish(0 if stage=='train2' else 1)


def predecessor_complete():
    q=receipts.small(PRIOR_MASTER/'queue-state.json')
    if q['phase']=='failed': raise RuntimeError('L10 predecessor failed; no bypass or retry')
    if q['phase']!='completed': return False
    if (q.get('exit_code')!=0 or q['completed']!=['L9/qwen-same/long','L10/qwen-same/short','L10/qwen-same/long']
            or q['deadline']!=PRIOR_SUITE_DEADLINE): raise RuntimeError('Exact L9/L10 completed queue required')
    d=receipts.small(PRIOR_ROOT/'deployment.json');clock=receipts.small(PRIOR_ROOT/'dispatch.json')
    arm=receipts.small(PRIOR_ROOT/'arm-state.json')
    if (d['runtime_sha']!=PRIOR_SHA or d['controller_sha']!=PRIOR_CONTROLLER or clock['deadline']!=PRIOR_DEADLINE
            or arm['phase']!='completed' or arm['exit_code']!=0 or arm['deadline']!=PRIOR_DEADLINE):
        raise RuntimeError('Predecessor provenance or fixed clock mismatch')
    a.clean(PRIOR_ROOT/'runtime',PRIOR_SHA);a.clean(Path(d['controller_source']),PRIOR_CONTROLLER)
    for part,stages in [('short',['pre','train2','post']),('long',['train96','eval96'])]:
        owner=PRIOR_ROOT/'qwen-same'/part;receipts.validate_terminal(owner,stages,PRIOR_DEADLINE)
        for stage in stages:
            r=receipts.small(owner/f'runs/{stage}/result.json');accepted=receipts.small(owner/f'acceptance-{stage}.json')
            manifest=receipts.small(owner/f'runs/{stage}/manifest.json')
            if (r!=accepted['result'] or r!=receipts.small(owner/f'runs/{stage}/.done') or r['status']!='completed'
                    or r['process_exit_code']!=0 or not r['metrics_finite'] or r['metrics_precision']!='binary64-v1'
                    or r['episode_outcomes']['natural_games']!={'pre':8,'train2':16,'post':8,'train96':752,'eval96':8}[stage]
                    or r['episode_outcomes']['truncated']
                    or manifest['source_commit']!=PRIOR_SHA or manifest['dirty'] or manifest['world_size']!=8
                    or accepted['evidence']['consumed_answers']<=0
                    or accepted['evidence']['consumed_answers']!=accepted['evidence']['valid_consumed_answers']):
                raise RuntimeError('Predecessor accepted result changed')
            if stage in ('pre','post','eval96') and r['training_updates']!=0: raise RuntimeError('Predecessor eval updated weights')
            receipts.terminal_container(owner,stage,PRIOR_DEADLINE)
    return True


def resources_ready(gib):
    rows=a.cmd(['nvidia-smi','--query-gpu=index,memory.used,utilization.gpu','--format=csv,noheader,nounits']).splitlines()
    if len(rows)!=8 or sorted(int(r.split(',')[0]) for r in rows)!=list(range(8)): raise RuntimeError('Exact8 GPUs required')
    if any(float(v.strip())>0 for r in rows for v in r.split(',')[1:]): return False
    if a.cmd(['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader']): return False
    mem=dict(r.split(':',1) for r in Path('/proc/meminfo').read_text().splitlines())
    return int(mem['MemAvailable'].split()[0])*1024>=600*a.GIB and shutil.disk_usage(ROOT).free>=gib*a.GIB


def admit(owner,tag,deadline,gib):
    while True:
        if time.time()>=deadline-45: raise TimeoutError('Fixed admission/deadline expired')
        h.sample(accounts(deadline),ROOT)
        fresh.queue_impl.host.writers_clear(accounts(deadline)[-1]['roots'])
        if resources_ready(gib): break
        a.save(owner/'admission-wait.json',dict(stage=tag,deadline=deadline,checked_at=time.time()),lock_root=ROOT)
        time.sleep(min(30,deadline-45-time.time()))
    path=owner/('fsync-'+tag)
    with path.open('xb') as stream: stream.write(b'l8random\n');stream.flush();os.fsync(stream.fileno())
    if path.read_bytes()!=b'l8random\n': raise RuntimeError('Fsync/readback failed')
    a.save(owner/f'admission-{tag}.json',dict(passed=True,deadline=deadline,checked_at=time.time(),
        eight_idle_gpus=True,ram_gib_min=600,nvme_gib_min=gib,fsync=True),lock_root=ROOT)


def verify_probe(stage):
    owner=ROOT/PARTS[0];p=a.read(owner/'gpu-preflight/gpu-preflight.json')
    if (stage!='gpu-preflight' or not p['passed'] or len(p['ranks'])!=8
            or len({r['cuda_uuid'] for r in p['ranks']})!=8 or p['nccl_sums']!=[28.0]*8
            or p['model_loaded'] or p['natural_games'] or p['optimizer_updates']
            or p['runtime_environment']['resolved_config_sha256']!=sha256(owner/'cpu/train2/resolved_config.json')):
        raise RuntimeError('Exact8 GPU mapping/NCCL preflight required')


def regression_receipt(host_only):
    # Model tests run inside short's writable bind; suite root stays read-only.
    return ROOT/'host-regressions.json' if host_only else ROOT/PARTS[0]/'regressions.json'


def regressions(host_only=False):
    sys.path[:0]=[str(a.SOURCE/'tests'),str(a.SOURCE/'scripts')]
    if host_only:
        if Path('/.dockerenv').exists(): raise RuntimeError('Real host required')
        names=['test_l7_host_continuation197','test_host_stage197','test_storage_quiescent197',
               'test_policy_credit_storage197','test_policy_credit_storage_coordination197']
    else:
        import torch
        names=['test_qwen_l8random197','test_qwen_l8random_retention','test_qwen_l9l10_same197','test_qwen_l9l10_continue197',
            'test_qwen_l8_common64_197','test_qwen_l8same_fresh197','test_qwen_l7same_fresh197',
            'test_l7_followup197','test_sc2_policy_resume','test_sc2_checkpoint_resume',
            'test_qwen_l8_probe_env','test_qwen_l8_remainder3_197','test_metric_precision',
            'test_sc2_action_support','test_sc2_policy_credit','test_sc2_no_thinking_torch',
            'test_sc2_reset_startup','test_sc2_generation_tokens','test_policy_credit_acceptance197']
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromNames(names))
    cuda=False if host_only else torch.cuda.is_initialized()
    proof=dict(passed=result.wasSuccessful() and not result.skipped and not cuda,tests=result.testsRun,
        skips=len(result.skipped),cuda_initialized=cuda,host_only=host_only,
        runtime_sha=a.read(ROOT/'deployment.json')['runtime_sha'],checked_at=time.time())
    a.save(regression_receipt(host_only),proof,lock_root=ROOT)
    if not proof['passed']: raise RuntimeError('Zero-skip CPU regressions required')


def check_cpu():
    cfg=a.read(ROOT/'deployment.json');sha=cfg['runtime_sha']
    a.clean(a.SOURCE,sha);a.clean(ROOT/'runtime',sha);a.clean(a.ORCH,a.ORCH_SHA)
    for host_only in (False,True):
        p=a.read(regression_receipt(host_only))
        if not p['passed'] or p['skips'] or p['cuda_initialized'] or p['runtime_sha']!=sha: raise RuntimeError('Matching CPU regressions required')
    for part in PARTS:
        p=a.read(ROOT/part/'readiness.json')
        if not p['passed'] or p['cuda_initialized'] or p['runtime_sha']!=sha: raise RuntimeError('All five actual launchers required')
        if not a.read(ROOT/part/'baseline-config-comparison.json')['passed']: raise RuntimeError('Frozen same comparator required')
    for index,stage in CPU_PROBES:
        owner=ROOT/PARTS[index];p=a.read(owner/f'cpu/hook-{stage}/cpu-hook-preflight.json')
        if (not p['passed'] or p['worker']['cuda_initialized'] or p['worker']['cuda_device_count']
                or p['model_loaded'] or p['natural_games'] or p['optimizer_updates']
                or p['runtime_environment']['resolved_config_sha256']!=sha256(owner/f'cpu/{stage}/resolved_config.json')):
            raise RuntimeError('Actual no-GPU worker hook required')
    import qwen_l8random_eval197 as evaluation
    evaluation.check_cpu(sha)
    evaluation.check_cpu(sha,selection=True)


def queue():
    configure();check_cpu()
    with (ROOT/'queue.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (ROOT/'queue-state.json').exists() or (ROOT/'dispatch.json').exists(): raise RuntimeError('Already queued; no retry')
        state=dict(phase='waiting-predecessor',completed=[],new_games=NEW_GAMES,new_updates=96)
        try:
            a.save(ROOT/'queue-state.json',state,lock_root=ROOT)
            while not predecessor_complete():
                if time.time()>=PRIOR_DEADLINE: raise TimeoutError('L10 not accepted before its fixed deadline')
                h.sample(accounts(PRIOR_DEADLINE+4*3600),ROOT);time.sleep(30)
            a.save(ROOT/'predecessor-acceptance.json',dict(passed=True,root=str(PRIOR_ROOT),runtime_sha=PRIOR_SHA,
                controller_sha=PRIOR_CONTROLLER,method='accepted small terminal receipts and exact containers',checked_at=time.time()),lock_root=ROOT)
            owner=ROOT/PARTS[0]
            admit(owner,'first',time.time()+4*3600,TRAIN_FREE_GIB)
            start=time.time();deadline=start+TRAIN_SECONDS;suite=start+SUITE_SECONDS
            a.save(ROOT/'dispatch.json',dict(start=start,deadline=deadline,suite_deadline=suite,
                gpu_hours=TRAIN_GPU_HOURS,suite_gpu_hours=SUITE_GPU_HOURS,new_games=920,new_updates=96,includes_gpu_preflight=True),lock_root=ROOT)
            h.run_stages(['gpu-preflight'],lambda _:docker('gpu-preflight',0,'train2'),verify_probe,
                accounts(deadline),owner,owner/'gpu-preflight-supervision',ROOT,deadline,
                admit=lambda _:admit(owner,'gpu-preflight',deadline,TRAIN_FREE_GIB))
            for index,part in enumerate(PARTS):
                cfg=f.select(index);owner=a.ROOT
                if index==1:
                    a.save(owner/'resume-contract.json',contract_for(),lock_root=ROOT)
                    with (owner/'parent-cpu.log').open('x') as log:
                        sp.run(docker('parent-cpu',1),stdout=log,stderr=sp.STDOUT,check=True,timeout=min(600,deadline-45-time.time()))
                    if not a.read(owner/'parent-readiness.json')['actual_parent_verified']: raise RuntimeError('Own native CP2 required')
                a.save(owner/'dispatch.json',dict(start=start,deadline=deadline,clock_shared=True),lock_root=ROOT)
                state.update(phase='running-unverified',part=part,deadline=suite,component_deadline=deadline)
                a.save(ROOT/'queue-state.json',state,lock_root=ROOT)
                terminal=h.run_stages(cfg['stages'],lambda s:docker('stage',index,s),verify_host,accounts(deadline),
                    owner,owner/'host-supervision',ROOT,deadline,
                    admit=lambda s:admit(owner,s,deadline,TRAIN_FREE_GIB if s in ('train2','train96') else 128),
                    **h.terminal_options(cfg,owner,owner/'host-supervision',deadline))
                a.save(owner/'state.json',terminal,lock_root=ROOT);state['completed'].append(part)
                a.save(ROOT/'queue-state.json',state,lock_root=ROOT)
            a.save(ROOT/'train-state.json',dict(phase='completed',exit_code=0,deadline=deadline,completed=PARTS,
                learning_validated=False,finished_at=time.time()),lock_root=ROOT)
            import qwen_l8random_eval197 as evaluation
            state.update(part='selection32',phase='running-unverified')
            a.save(ROOT/'queue-state.json',state,lock_root=ROOT)
            evaluation.run_selection(deadline,accounts,admit)
            state['completed'].append('selection32')
            import qwen_l8random_retention as retention
            fresh.queue_impl.host.writers_clear([ROOT,EVAL_ROOT,SOURCE_PARENT])
            if PRUNE_AFTER_SELECTION:
                retention.prune()
            else:
                retention.require_published()
                a.save(ROOT/'retention/no-pruning.json',dict(retained_steps=[2,32,64,96],
                    deleted_files=0,best_reference_only=True,checked_at=time.time()),lock_root=ROOT)
            h.sample(accounts(deadline),ROOT)
            state.update(part='paired64')
            a.save(ROOT/'queue-state.json',state,lock_root=ROOT)
            evaluation.run_after_training(suite,accounts,admit)
            state['completed'].append('paired64');state.update(phase='completed',exit_code=0,learning_validated=False,finished_at=time.time())
            a.save(ROOT/'queue-state.json',state,lock_root=ROOT)
        except BaseException as exc:
            state.update(phase='failed',error_type=type(exc).__name__,error=str(exc),finished_at=time.time())
            a.save(ROOT/'queue-state.json',state,lock_root=ROOT);raise


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode',choices=['prepare','queue','cpu','cpu-command','regressions','host-regressions',
        'regressions-command','parent-cpu','checkpoint-cpu','stage','cpu-hook','cpu-hook-command','gpu-preflight'])
    p.add_argument('index',type=int,nargs='?',choices=(0,1));p.add_argument('stage',nargs='?');arg=p.parse_args()
    if arg.mode in ('regressions','host-regressions'): regressions(arg.mode=='host-regressions');return
    configure()
    if arg.mode in ('prepare','queue'): globals()[arg.mode]();return
    if arg.index is None: p.error('Exact short/long index required')
    if arg.mode.endswith('-command'): print(json.dumps(docker(arg.mode.removesuffix('-command'),arg.index,arg.stage)));return
    if arg.mode=='cpu': cpu(arg.index)
    elif arg.mode=='parent-cpu': f.parent_cpu(arg.index)
    elif arg.mode=='checkpoint-cpu': checkpoint_cpu(arg.index)
    elif arg.mode in ('cpu-hook','gpu-preflight'):
        cfg=f.select(arg.index)
        if arg.stage not in cfg['stages']: raise ValueError('Undeclared probe')
        config=a.ROOT/f'cpu/{arg.stage}/resolved_config.json'
        if arg.mode=='cpu-hook': probe.check_hook_cpu(a.ROOT/f'cpu/hook-{arg.stage}',Path('/tmp/hook-'+arg.stage),config,environment_loader=runtime_environment)
        elif arg.index==0 and arg.stage=='train2': probe.run(a.ROOT/'gpu-preflight',Path('/tmp/probe-ray'),config,environment_loader=runtime_environment)
        else: raise ValueError('One bounded train GPU probe only')
    else:
        cfg=f.select(arg.index);a.clean(a.SOURCE,cfg['controller_sha']);a.clean(a.ROOT/'runtime',cfg['runtime_sha'])
        args,env,_=invocation(cfg,arg.stage)
        fd=os.open(a.ROOT/(arg.stage+'-entry.log'),os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
        os.dup2(fd,1);os.dup2(fd,2);os.close(fd);os.chdir(a.ROOT/'runtime');os.execvpe(args[0],args,env)


if __name__=='__main__': main()
