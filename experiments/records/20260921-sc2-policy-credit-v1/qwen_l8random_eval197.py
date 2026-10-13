"""Frozen three-arm192 evaluator, callable only after this suite's full training acceptance."""
import argparse
import copy
import json
import os
from pathlib import Path
import subprocess as sp
import time

import qwen_l8_common64_197 as common
import qwen_l7same_fresh197 as fresh
from agent_system.sc2_policy_resume import checkpoint_names, sha256
from qwen_l8random_plan import ROOT as TRAIN_ROOT, EVAL_ROOT as ROOT, SOURCE_PARENT, PARTS, ARMS, CHECKPOINTS, SEEDS, SEED_SHA256, STAGES, stage_spec
from qwen_l8random_eval_hook import runtime_environment
import qwen_l8random_plan as plan

a,h=common.a,common.h
IS_SELECTION=False
HOOK_STAGES=STAGES[:3]
MODEL_KIND='qwen'
DIFFICULTY='CheatVision'
TERMINAL_HANDOFF=False
ENTRY_SCRIPT='qwen_l8random_eval197.py'
WORKER_HOOK='qwen_l8random_eval_hook.install'
SELECTION_SECONDS=4*3600


def configure(selection=None):
    global IS_SELECTION,ROOT,ARMS,CHECKPOINTS,SEEDS,SEED_SHA256,STAGES,HOOK_STAGES
    if selection is not None: IS_SELECTION=selection
    ROOT=plan.SELECTION_ROOT if IS_SELECTION else plan.EVAL_ROOT
    ARMS=plan.SELECTION_ARMS if IS_SELECTION else plan.ARMS
    CHECKPOINTS=plan.SELECTION_CHECKPOINTS if IS_SELECTION else plan.CHECKPOINTS
    SEEDS=plan.SELECTION_SEEDS if IS_SELECTION else plan.SEEDS
    SEED_SHA256=plan.SELECTION_SHA256 if IS_SELECTION else plan.SEED_SHA256
    STAGES=plan.SELECTION_STAGES if IS_SELECTION else plan.STAGES
    HOOK_STAGES=[f'b00-{arm}' for arm in ARMS]
    common.MODEL_KIND=MODEL_KIND
    common.DIFFICULTY=DIFFICULTY
    common.ROOT,common.SOURCE_PARENT=ROOT,SOURCE_PARENT
    common.PREFIX=TRAIN_ROOT.name+'-select' if IS_SELECTION else ROOT.name
    common.ARMS,common.CHECKPOINTS,common.SEEDS,common.SEED_SHA256,common.STAGES=ARMS,CHECKPOINTS,SEEDS,SEED_SHA256,STAGES
    common.HOOK_STAGES=HOOK_STAGES;common.stage_spec=stage_spec;common.runtime_environment=runtime_environment
    common.configure()
    a.STORAGE_LOCK_ROOT=TRAIN_ROOT
    a.DOCKER_SCRIPT=a.HERE/ENTRY_SCRIPT
    a.invocation=fresh.f.BASE_INVOCATION


def prepare(base,sha,selection=False):
    # No configure() here: deployment does not exist until this function ends.
    root=plan.SELECTION_ROOT if selection else plan.EVAL_ROOT
    stages=plan.SELECTION_STAGES if selection else plan.STAGES
    seeds=plan.SELECTION_SEEDS if selection else plan.SEEDS
    seed_sha=plan.SELECTION_SHA256 if selection else plan.SEED_SHA256
    checkpoints=plan.SELECTION_CHECKPOINTS if selection else plan.CHECKPOINTS
    seconds,games,gpuh,limit=(4*3600,128,32,8*a.GIB) if selection else (6*3600,192,48,32*a.GIB)
    _prepare(base,sha,root,stages,seeds,seed_sha,checkpoints,seconds,games,gpuh,limit,selection)


def _prepare(base,sha,root,stages,seeds,seed_sha,checkpoints,seconds,games,gpuh,limit,selection):
    ROOT=root
    if ROOT.exists(): raise RuntimeError('Fresh evaluation root required')
    ROOT.mkdir()
    for name in ('runs','cpu','tmp','tmp/task-home','tmp/cache','tmp/cuda-cache','eval-storage'): (ROOT/name).mkdir()
    # Shared immutable runtime/source counted once in suite, conservatively in both components.
    (ROOT/'runtime').symlink_to(TRAIN_ROOT/'runtime',target_is_directory=True)
    cfg=copy.deepcopy(base)
    for key in ('prior_failed_root','retained_prefix','fixed_deadline','original_start','deadline','training_seeds'): cfg.pop(key,None)
    cfg.update(runtime_sha=sha,controller_sha=sha,controller_source=str(a.SOURCE),orchestration_sha=a.ORCH_SHA,
        stages=stages,games=[8]*len(stages),updates=[0]*len(stages),
        run_prefix=(TRAIN_ROOT.name+'-select' if selection else ROOT.name),worker_hook=WORKER_HOOK,
        eval_seeds=seeds,seed_sha256=seed_sha,checkpoints={k:str(v) for k,v in checkpoints.items()},
        wall_seconds=seconds,gpu_hours=gpuh,output_limit_bytes=limit,
        storage_roots=([str(ROOT)] if selection else [str(p) for p in (getattr(plan,'EVAL_STORAGE_ROOTS',None) or
            (plan.OLD_EVAL_ROOT,plan.OLD_SOURCE_PARENT,plan.R2_EVAL_ROOT,plan.R2_SOURCE_PARENT,ROOT,SOURCE_PARENT))]),
        new_games=games,new_updates=0,no_training=True,no_retry=True,successors_authorized=False,
        predecessor=str(TRAIN_ROOT),evaluation_admission_free_gib=128,
        authorization='Sep28 explicit r3 selection128 plus primary192; r1/r2 retained and counted; only own rolling pruning; no CP192/retry',
        selection=selection,limitation='Validation best only; primary test remains CP96; no architecture claim')
    a.save(ROOT/'deployment.json',cfg,lock_root=TRAIN_ROOT)


def docker(mode,stage=None):
    configure();gpu=mode in ('stage','gpu-preflight')
    if mode in ('stage','gpu-preflight','cpu-hook'): stage_spec(stage)
    args=fresh.BASE_DOCKER('execute' if gpu else 'cpu')
    args[2:2]=['--read-only','--log-driver','none','-e','HOME=/tmp/task-home',
        '-e','XDG_CACHE_HOME=/tmp/cache','-e','CUDA_CACHE_PATH=/tmp/cuda-cache','-e','TMPDIR=/tmp',
        '-v',f'{TRAIN_ROOT}:{TRAIN_ROOT}:ro','-v',f'{TRAIN_ROOT}/.storage.lock:{TRAIN_ROOT}/.storage.lock']
    # Only an already-existing comparator is mounted separately; own future CP is inside TRAIN_ROOT.
    if not IS_SELECTION and 'same96' in CHECKPOINTS: args[2:2]=['-v',f'{CHECKPOINTS["same96"]}:{CHECKPOINTS["same96"]}:ro']
    if not gpu:
        cfg=a.read(ROOT/'deployment.json')
        mount=cfg.get('model_mount','/assets/qwen')
        metadata=fresh.f.previous.SPB_METADATA if MODEL_KIND=='spb' else fresh.f.previous.CPU_MODEL
        args[args.index(f'{cfg["host"]["model"]}:{mount}:ro')]=f'{metadata}:{mount}:ro'
        args[2:2]=['-v',f'{fresh.f.previous.SPB_METADATA}:/metadata/spb:ro','-e','SC2_TEST_SPB_METADATA_PATH=/metadata/spb',
            '-v',f'{fresh.f.previous.CPU_MODEL}:/metadata/qwen:ro',
            '-e','SC2_TEST_QWEN_METADATA_PATH=/metadata/qwen','-e','SC2_TEST_TOKENIZER_PATH=/metadata/qwen',
            '-e','OMP_NUM_THREADS=2','-e','TOKENIZERS_PARALLELISM=false']
        if mode=='cpu-hook': args[args.index('--memory')+1]='16g'
    writable=[tuple(args[i+1].split(':')[:2]) for i,x in enumerate(args[:-1]) if x=='-v' and args[i+1].split(':')[-1]!='ro']
    if set(writable)!={(str(ROOT),str(ROOT)),(str(ROOT/'tmp'),'/tmp'),(str(TRAIN_ROOT/'.storage.lock'),str(TRAIN_ROOT/'.storage.lock'))} or len(writable)!=3:
        raise RuntimeError('Unexpected writable eval bind')
    if mode in ('cpu-hook','gpu-preflight'):
        ev=a.read(ROOT/f'cpu/{stage}/resolved_config.json')['ray_init']['runtime_env']['env_vars']
        for i,x in enumerate(args):
            if x.startswith('PYTHONPATH='): args[i]='PYTHONPATH='+ev['PYTHONPATH']
    prefix=TRAIN_ROOT.name+'-select' if IS_SELECTION else ROOT.name
    args[args.index('--name')+1]=prefix+'-'+(stage if mode=='stage' else mode+('-'+stage if stage else ''))
    args[-1:]=[mode]+([stage] if stage else [])+(['--selection'] if IS_SELECTION else [])
    if gpu: args[1]='create'
    return args


def check_cpu(sha,selection=False):
    configure(selection)
    p=a.read(ROOT/'readiness.json')
    if not p['passed'] or p['cuda_initialized'] or p['runtime_sha']!=sha or p['stages']!=STAGES:
        raise RuntimeError('All declared actual evaluation launchers required')
    for stage in HOOK_STAGES:
        p=a.read(ROOT/f'cpu/hook-{stage}/cpu-hook-preflight.json')
        if (not p['passed'] or p['worker']['cuda_initialized'] or p['worker']['cuda_device_count']
                or p['model_loaded'] or p['natural_games'] or p['optimizer_updates']
                or p['runtime_environment']['resolved_config_sha256']!=sha256(ROOT/f'cpu/{stage}/resolved_config.json')):
            raise RuntimeError('Actual no-GPU eval worker imports required')


def parents():
    proof={}
    for arm,cp in CHECKPOINTS.items():
        owner=cp.parents[3];clock=a.read(owner/'dispatch.json')
        cfg=a.read(owner/'deployment.json')
        expected_sha=('eef0f049bb09b7a51188ae67a6c35436a3bf055f' if arm=='same96'
                      else a.read(TRAIN_ROOT/'deployment.json')['runtime_sha'])
        if (cfg['runtime_sha']!=expected_sha or cfg['model_kind']!=MODEL_KIND or cfg['difficulty']!=DIFFICULTY
                or cfg['seed_protocol']!=('same_uniform101' if arm=='same96' else 'independent_uniform101')):
            raise RuntimeError('Wrong fixed evaluation parent provenance')
        common.receipts.validate_terminal(owner,['train96','eval96'],clock['deadline'])
        for stage in ('train96','eval96'):
            common.receipts.terminal_container(owner,stage,clock['deadline'])
            r=a.read(owner/f'runs/{stage}/result.json');accepted=a.read(owner/f'acceptance-{stage}.json')
            manifest=a.read(owner/f'runs/{stage}/manifest.json')
            if (r!=a.read(owner/f'runs/{stage}/.done') or r!=accepted['result'] or r['status']!='completed'
                    or r['process_exit_code']!=0 or not r['metrics_finite'] or r['metrics_precision']!='binary64-v1'
                    or manifest['source_commit']!=expected_sha or manifest['dirty'] or manifest['world_size']!=8
                    or accepted['evidence']['consumed_answers']<=0
                    or accepted['evidence']['consumed_answers']!=accepted['evidence']['valid_consumed_answers']):
                raise RuntimeError('Fully accepted correct parent required')
        load=a.read(owner/'runs/eval96/checkpoint_evaluation.json')
        if (load['checkpoint']!=str(cp) or load['loaded_global_step']!=96 or not load['checkpoint_load_returned']
                or not load['val_only'] or load['optimizer_updates']!=0): raise RuntimeError('CP96 actual load receipt required')
        r=a.read(owner/'runs/train96/result.json')
        inventory={n:(cp/n).stat().st_size for n in checkpoint_names()}
        if any(size<=0 or size!=r['checkpoint_files']['checkpoints/global_step_96/'+n]['bytes'] for n,size in inventory.items()):
            raise RuntimeError('Full CP96 inventory changed')
        proof[arm]=dict(root=str(owner),checkpoint=str(cp),checkpoint_bytes=inventory,
            train_acceptance_sha256=sha256(owner/'acceptance-train96.json'),eval_acceptance_sha256=sha256(owner/'acceptance-eval96.json'))
    return dict(passed=True,parents=proof,checked_at=time.time(),weights_read=False)


def terminal_options(deadline):
    if not TERMINAL_HANDOFF: return {}
    return h.terminal_options(a.read(ROOT/'deployment.json'),ROOT,ROOT/'host-supervision',deadline)


def run_after_training(suite_deadline,accounts,admit):
    configure(False)
    if (ROOT/'dispatch.json').exists() or (ROOT/'state.json').exists(): raise RuntimeError('Eval already dispatched; no retry')
    proof=parents();a.save(ROOT/'parent-acceptance.json',proof,lock_root=TRAIN_ROOT)
    admit(ROOT,'first',suite_deadline,128)
    start=time.time();deadline=min(start+6*3600,suite_deadline)
    a.save(ROOT/'dispatch.json',dict(start=start,deadline=deadline,suite_deadline=suite_deadline,
        gpu_hours=48,new_games=len(STAGES)*8,new_updates=0,includes_gpu_preflight=True),lock_root=TRAIN_ROOT)
    h.run_stages(['gpu-preflight'],lambda _:docker('gpu-preflight',STAGES[0]),common.verify_probe,
        accounts(deadline),ROOT,ROOT/'gpu-preflight-supervision',TRAIN_ROOT,deadline,
        admit=lambda _:admit(ROOT,'gpu-preflight',deadline,128))
    terminal=h.run_stages(STAGES,lambda s:docker('stage',s),common.verify,accounts(deadline),ROOT,
        ROOT/'host-supervision',TRAIN_ROOT,deadline,admit=lambda s:admit(ROOT,s,deadline,128),
        **terminal_options(deadline))
    a.save(ROOT/'state.json',terminal,lock_root=TRAIN_ROOT)


def run_selection(training_deadline,accounts,admit):
    configure(True)
    if (ROOT/'dispatch.json').exists() or (ROOT/'state.json').exists(): raise RuntimeError('Selection already dispatched; no retry')
    import qwen_l8random_retention as retention
    retention.require_published()
    for index in (0,1):
        owner=TRAIN_ROOT/PARTS[index]
        stages=['pre','train2','post'] if index==0 else ['train96','eval96']
        common.receipts.validate_terminal(owner,stages,training_deadline)
        for stage in stages: common.receipts.terminal_container(owner,stage,training_deadline)
    admit(ROOT,'first',training_deadline,128)
    start=time.time();deadline=min(start+SELECTION_SECONDS,training_deadline)
    a.save(ROOT/'dispatch.json',dict(start=start,deadline=deadline,training_deadline=training_deadline,
        gpu_hours=SELECTION_SECONDS*8/3600,new_games=128,new_updates=0,includes_gpu_preflight=True),lock_root=TRAIN_ROOT)
    h.run_stages(['gpu-preflight'],lambda _:docker('gpu-preflight',STAGES[0]),common.verify_probe,
        accounts(deadline),ROOT,ROOT/'gpu-preflight-supervision',TRAIN_ROOT,deadline,
        admit=lambda _:admit(ROOT,'gpu-preflight',deadline,128))
    def verify(stage):
        common.verify(stage)
        if stage.startswith('b03-'): retention.update_best(stage[4:])
    terminal=h.run_stages(STAGES,lambda s:docker('stage',s),verify,accounts(deadline),ROOT,
        ROOT/'host-supervision',TRAIN_ROOT,deadline,admit=lambda s:admit(ROOT,s,deadline,128),
        **terminal_options(deadline))
    a.save(ROOT/'state.json',terminal,lock_root=TRAIN_ROOT)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode',choices=['cpu','cpu-command','cpu-hook','cpu-hook-command','gpu-preflight','stage'])
    p.add_argument('stage',nargs='?',choices=plan.STAGES+plan.SELECTION_STAGES)
    p.add_argument('--selection',action='store_true');arg=p.parse_args();configure(arg.selection)
    if arg.stage is not None and arg.stage not in STAGES: p.error('Stage belongs to other evaluation group')
    if arg.mode.endswith('-command'): print(json.dumps(docker(arg.mode.removesuffix('-command'),arg.stage)))
    elif arg.mode=='cpu': common.cpu()
    elif arg.mode in ('cpu-hook','gpu-preflight'):
        stage_spec(arg.stage);config=ROOT/f'cpu/{arg.stage}/resolved_config.json'
        if arg.mode=='cpu-hook': common.probe.check_hook_cpu(ROOT/f'cpu/hook-{arg.stage}',Path('/tmp/hook-'+arg.stage),config,environment_loader=runtime_environment)
        elif arg.stage==STAGES[0]: common.probe.run(ROOT/'gpu-preflight',Path('/tmp/probe-ray'),config,environment_loader=runtime_environment)
        else: raise ValueError('One eval GPU probe only')
    else:
        cfg=a.read(ROOT/'deployment.json');a.clean(a.SOURCE,cfg['runtime_sha']);a.clean(ROOT/'runtime',cfg['runtime_sha'])
        args,env,_=common.invocation(cfg,arg.stage)
        fd=os.open(ROOT/(arg.stage+'-entry.log'),os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
        os.dup2(fd,1);os.dup2(fd,2);os.close(fd);os.chdir(ROOT/'runtime');os.execvpe(args[0],args,env)


if __name__=='__main__': main()
