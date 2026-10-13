"""Approved serial SpB L7 same96 then Qwen L7 random96; fail closed, never retry."""
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

import acceptance197 as a
import qwen_l7_long197 as previous

HERE, SOURCE = a.HERE, a.SOURCE
sys.path.insert(0, str(SOURCE))
from agent_system.sc2_policy_resume import prefix_files, sha256, verify_contract, normalized_protocol
from agent_system.sc2_seed_protocol import ablation_seeds

SUITE = Path('/var/jfsCache/sc2-l7-followup197-20260922-r2')
RETAINED_PREPARATION = [Path('/var/jfsCache/sc2-l7-followup197-20260922-r1'),
    Path('/var/jfsCache/sc2-l7-followup197-source-20260922-r1')]
PREDECESSOR = previous.ROOT
SPB_BASE = Path('/var/jfsCache/sc2-policy-credit197-20260921-r4')
RANDOM_PARENT = Path('/var/jfsCache/sc2-qwen-seeds197-20260922-r4/l7-random')
PARTS = ('spb-same/short', 'spb-same/long', 'qwen-random/long')
FIRST_DISPATCH_BY = 1790230726.5133374  # Existing predecessor deadline + one hour; Sep24 14:18:46 Beijing.
ARM_SECONDS = 48 * 3600
BASE_INVOCATION, BASE_DOCKER, BASE_VERIFY = a.invocation, a.docker, a.verify
INDEX = 0
CONTAINER_PREFIX = 'sc2-l7-followup197-20260922-r2-'
RUN_PREFIX = 'l7-followup197-r2-'
DOCKER_SCRIPT = HERE/'l7_followup197.py'


def select(index):
    global INDEX
    INDEX = index
    a.ROOT = SUITE / PARTS[index]
    a.STORAGE_LOCK_ROOT = SUITE
    cfg = a.read(a.ROOT/'deployment.json')
    a.RUNTIME_SHA = cfg['runtime_sha']
    a.CONTAINER = CONTAINER_PREFIX + PARTS[index].replace('/', '-')
    a.DOCKER_SCRIPT = DOCKER_SCRIPT
    a.TRAIN_SEEDS = cfg['training_seeds'][:2]
    a.invocation, a.verify, a.budget = invocation, verify, budget
    return cfg


def parent_for(index):
    return SUITE/'spb-same/short' if index == 1 else RANDOM_PARENT


def contract_for(index):
    parent = parent_for(index)
    cfg = a.read(parent/'deployment.json')
    contract = dict(version=('accepted-spb-same-full-state-prefix-v1' if index == 1
                             else 'accepted-qwen-random-prefix-v1'),
        parent=str(parent), checkpoint=str(parent/'runs/train2/checkpoints/global_step_2'),
        parent_sha=cfg['runtime_sha'], start_step=2, target_step=96,
        driver_rng_unavailable_accepted=index == 2,
        files={p:sha256(parent/p) for p in prefix_files()})
    verify_contract(contract)
    rows = [json.loads(x) for x in (parent/'runs/train2/training_seeds.jsonl').read_text().splitlines()]
    if len(rows) != 2 or any(row['reset_index'] != i or row['seed_protocol'] != cfg['seed_protocol']
            or row['seeds'] != ablation_seeds(cfg['seed_protocol'],0,i,1,8) for i,row in enumerate(rows)):
        raise RuntimeError('Accepted prefix seed sequence mismatch')
    audits = [json.loads(x) for x in (parent/'runs/train2/checkpoints/sc2_policy_credit_audit.jsonl').read_text().splitlines()]
    metrics = a.read(parent/'runs/train2/metrics.json')
    verify_updates(audits, metrics, 1, 2)
    proof = a.read(parent/'runs/post/checkpoint_evaluation.json')
    if (proof['checkpoint'] != contract['checkpoint'] or proof['loaded_global_step'] != 2
            or not proof['checkpoint_load_returned'] or proof['optimizer_updates'] != 0
            or proof['game_seeds'] != a.EVAL_SEEDS):
        raise RuntimeError('Parent CP2 actual evaluation missing')
    return contract


def prepare():
    if SUITE.exists():
        raise RuntimeError('Fresh suite required; no overwrite/retry')
    sha = a.cmd(['git','-C',SOURCE,'rev-parse','HEAD'])
    a.clean(SOURCE,sha)
    a.clean(a.ORCH,a.ORCH_SHA)
    contract = contract_for(2)
    SUITE.mkdir()
    a.STORAGE_LOCK_ROOT = SUITE
    a.cmd(['git','clone','--quiet','--shared',SOURCE,SUITE/'runtime'])
    a.cmd(['git','-C',SUITE/'runtime','checkout','--quiet','--detach',sha])
    for index, part in enumerate(PARTS):
        root = SUITE/part
        root.mkdir(parents=True)
        for folder in ('runs','cpu','tmp'):
            (root/folder).mkdir()
        (root/'runtime').symlink_to(SUITE/'runtime',target_is_directory=True)
        cfg = copy.deepcopy(a.read((SPB_BASE if index < 2 else RANDOM_PARENT)/'deployment.json'))
        protocol = 'same_uniform101' if index < 2 else 'independent_uniform101'
        cfg.update(runtime_sha=sha,controller_sha=sha,controller_source=str(SOURCE),
            model_kind='spb' if index < 2 else 'qwen', model_mount='/assets/spb' if index < 2 else '/assets/qwen',
            difficulty='VeryHard',seed_protocol=protocol,
            seed_group_mode='same' if index < 2 else 'mixed_seed_ablation',
            training_seeds=[ablation_seeds(protocol,0,i,1,8) for i in range(96)],
            stages=['pre','train2','post'] if index == 0 else ['train96','eval96'],
            games=[8,16,8] if index == 0 else [752,8],updates=[0,2,0] if index == 0 else [94,0],
            run_prefix=RUN_PREFIX+part.replace('/','-'),worker_hook='l7_followup_hook.install',
            wall_seconds=ARM_SECONDS,gpu_hours=384,output_limit_bytes=1024*a.GIB,
            no_long_training=False,no_retry=True,successors_authorized=index<2,
            authorization='Sep22 user explicitly approved current Qwen same96 -> original SpB L7 same short+96 -> Qwen L7 random ownCP2+96; '
                'each new model arm <=48wallh/384GPUh/1TiB, SpB short included; random legacy driver RNG gap accepted; no extra arms or retries',
            predecessor=str(PREDECESSOR if index==0 else SUITE/PARTS[index-1]))
        a.save(root/'deployment.json',cfg)
    a.save(SUITE/PARTS[2]/'resume-contract.json',contract)
    a.save(SUITE/'deployment.json',dict(runtime_sha=sha,controller_sha=sha,orchestration_sha=a.ORCH_SHA,
        parts=PARTS,predecessor=str(PREDECESSOR),first_dispatch_by=FIRST_DISPATCH_BY,
        wall_seconds=2*ARM_SECONDS,gpu_hours=768,output_limit_bytes=2048*a.GIB,
        arm_seconds=ARM_SECONDS,short_included_in_spb=True,no_retry=True,
        new_games=1552,new_updates=190,storage_roots=[str(p) for p in [SUITE,SOURCE.parent,RANDOM_PARENT,*RETAINED_PREPARATION]]))


def invocation(cfg,stage,dry=False):
    short = INDEX == 0
    if stage not in cfg['stages']:
        raise ValueError('Undeclared stage')
    template = stage if short else ('train2' if stage=='train96' else 'post')
    args,env,old = BASE_INVOCATION(cfg,template,dry)
    out = a.ROOT/('cpu' if dry else 'runs')/stage
    args = [x.replace(str(old),str(out)) for x in args]
    if cfg['model_kind']=='spb':
        args += [f"algorithm.sc2_policy_credit.seed_group_mode={cfg['seed_group_mode']}",
                 f"+ray_init.runtime_env.env_vars.SC2_TRAIN_SEED_PROTOCOL='{cfg['seed_protocol']}'"]
    if not short:
        settings = {'+ray_init.runtime_env.env_vars.SC2_ACCEPTANCE_STAGE':repr(stage),
            'trainer.total_training_steps':'96','trainer.total_epochs':'96' if stage=='train96' else '1',
            'trainer.save_freq':'8' if stage=='train96' else '-1','trainer.resume_mode':'resume_path',
            'trainer.resume_from_path':str(parent_for(INDEX)/'runs/train2/checkpoints/global_step_2'
                if stage=='train96' else a.ROOT/'runs/train96/checkpoints/global_step_96')}
        args = [x for x in args if x.split('=',1)[0] not in settings]
        args += [k+'='+v for k,v in settings.items()]
        if stage=='train96':
            args += [f'+trainer.sc2_import_legacy_final={INDEX==2}',
                     f'+trainer.sc2_policy_credit_resume_contract={a.ROOT}/resume-contract.json']
    env.update(OUTPUT_DIR=str(out),RUN_ID=cfg['run_prefix']+'-'+stage,
        SC2_CHECKPOINT_RESUME=str(stage in ('train2','train96')),RAY_TMPDIR='/tmp/fup-'+stage)
    return args,env,out


def budget(deadline):
    roots = [SUITE/'spb-same',SOURCE.parent] if INDEX < 2 else [SUITE/'qwen-random',SOURCE.parent,RANDOM_PARENT]
    a.measure_budget([*roots,*RETAINED_PREPARATION],a.ROOT,1024*a.GIB,deadline,'48h arm ceiling','1TiB inclusive arm ceiling',lock_root=SUITE)
    total = a.read(SUITE/'dispatch.json')['deadline'] if (SUITE/'dispatch.json').exists() else None
    a.measure_budget([SUITE,SOURCE.parent,RANDOM_PARENT,*RETAINED_PREPARATION],SUITE,2048*a.GIB,total,
        '96h total ceiling includes subsequent waiting','2TiB inclusive suite ceiling',lock_root=SUITE)


def docker(mode,index):
    cfg = select(index)
    args = BASE_DOCKER('execute' if mode=='execute' else 'cpu')
    args[2:2] = ['-v',f'{SUITE}:{SUITE}:ro','-v',f'{SUITE}/.storage.lock:{SUITE}/.storage.lock',
        '-v',f'{RANDOM_PARENT}:{RANDOM_PARENT}:ro',
        '-v',f'{RANDOM_PARENT.parent}/runtime:{RANDOM_PARENT.parent}/runtime:ro']
    for path in RETAINED_PREPARATION:
        args[2:2] = ['-v',f'{path}:{path}:ro']
    # Only the selected part is writable; stable shared lock coordinates all writers.
    if mode != 'execute':
        model = cfg['host']['model']
        metadata = previous.SPB_METADATA if index<2 else previous.CPU_MODEL
        args[args.index(f'{model}:{cfg["model_mount"]}:ro')] = f'{metadata}:{cfg["model_mount"]}:ro'
        args[args.index('--name')+1] += '-'+mode
        args[2:2] = ['-v',f'{previous.SPB_METADATA}:/metadata/spb:ro',
            '-v',f'{previous.CPU_MODEL}:/metadata/qwen:ro','-e','SC2_TEST_SPB_METADATA_PATH=/metadata/spb',
            '-e','SC2_TEST_QWEN_METADATA_PATH=/metadata/qwen','-e','SC2_TEST_TOKENIZER_PATH=/metadata/qwen',
            '-e','OMP_NUM_THREADS=2','-e','TOKENIZERS_PARALLELISM=false']
    # Suite receipts are written under the selected part, except coordinated watchdog.
    args[args.index(f'{SUITE}:{SUITE}:ro')] = f'{SUITE}:{SUITE}'
    args[-1:] = [mode,str(index)]
    return args


def cpu(index):
    import torch
    from hydra import compose, initialize_config_dir
    from omegaconf import OmegaConf
    from verl.trainer.ppo.sc2_policy_credit import validate_config as credit_config
    from verl.utils.sc2_action_support import validate_config as support_config
    from ray._private.utils import validate_socket_filepath
    sys.path.insert(0,str(a.ORCH/a.REC))
    from seed_ray_paths import socket_path
    cfg = select(index)
    check = sp.run(['sha256sum','-c','configs/system-v1.sha256'],cwd=a.ROOT/'runtime',capture_output=True,text=True,timeout=30)
    (a.ROOT/'cpu/source-check.log').write_text(check.stdout+check.stderr)
    if check.returncode: raise RuntimeError('Source manifest failed')
    for stage in cfg['stages']:
        args,env,out = invocation(cfg,stage,True)
        proc = sp.run(args,env=env,cwd=a.ROOT/'runtime',capture_output=True,text=True,timeout=90)
        (a.ROOT/'cpu'/f'{stage}.log').write_text(proc.stdout+proc.stderr)
        if proc.returncode: raise RuntimeError('Actual dry launcher failed: '+stage)
        command = a.read(out/'effective_config.json')['command']
        with initialize_config_dir(config_dir=str(a.ROOT/'runtime/verl/trainer/config'),version_base=None):
            c = compose(config_name='ppo_trainer',overrides=command[command.index('verl.trainer.main_ppo')+1:])
        deferred = index==1 and stage=='train96'
        if not deferred: credit_config(c)
        support_config(c)
        if (c.trainer.n_gpus_per_node!=8 or c.env.rollout.n!=8 or c.data.max_response_length!=192
                or c.actor_rollout_ref.actor.optim.lr!=1e-6
                or c.actor_rollout_ref.actor.optim.warmup_style!='constant'
                or c.actor_rollout_ref.actor.optim.lr_warmup_steps_ratio!=0
                or c.trainer.total_training_steps!=(2 if index==0 else 96)
                or str(c.ray_init.runtime_env.env_vars.SC2_TRAIN_SEED_PROTOCOL)!=cfg['seed_protocol']):
            raise RuntimeError('Unexpected resolved protocol/scheduler')
        a.save(out/'resolved_config.json',OmegaConf.to_container(c,resolve=True))
        validate_socket_filepath(socket_path(env['RAY_TMPDIR']))
    if index:
        if index==2:
            small_state(index)
        else:
            # Exact comparison excluding only the accepted relocation/restore keys.
            parent = a.read(SUITE/PARTS[0]/'cpu/train2/resolved_config.json')
            if normalized_protocol(a.read(a.ROOT/'cpu/train96/resolved_config.json'))!=normalized_protocol(parent):
                raise RuntimeError('Planned SpB short/long protocols differ')
    if torch.cuda.is_initialized(): raise RuntimeError('CPU initialized CUDA')
    a.save(a.ROOT/'readiness.json',dict(passed=True,
        runtime_sha=cfg['runtime_sha'],cuda_initialized=False,actual_entries_and_hydra_configs=True,
        actual_parent_verified=index!=1,
        deferred_gate='SpB actual CP2 and accepted prefix required before long GPU' if index==1 else None,
        checked_at=time.time()))


def parent_cpu(index):
    import torch
    from omegaconf import OmegaConf
    from verl.trainer.ppo.sc2_policy_credit import validate_config
    if index!=1: raise ValueError('Only the future SpB prefix has a deferred gate')
    cfg=select(index)
    validate_config(OmegaConf.create(a.read(a.ROOT/'cpu/train96/resolved_config.json')))
    small_state(index)
    if torch.cuda.is_initialized(): raise RuntimeError('Parent CPU gate initialized CUDA')
    a.save(a.ROOT/'parent-readiness.json',dict(passed=True,actual_parent_verified=True,
        runtime_sha=cfg['runtime_sha'],cuda_initialized=False,checked_at=time.time()))


def small_state(index):
    import torch
    import numpy as np
    from types import SimpleNamespace
    from unittest.mock import patch
    from agent_system.sc2_resume import legacy_environment_state,restore_environment
    cfg = a.read(a.ROOT/'deployment.json')
    parent = parent_for(index)
    contract = a.read(a.ROOT/'resume-contract.json')
    verify_contract(contract)
    cp = Path(contract['checkpoint'])
    ranks=[]
    for rank in range(8):
        extra=torch.load(cp/f'actor/extra_state_world_size_8_rank_{rank}.pt',map_location='cpu',weights_only=False)
        if extra['lr_scheduler']['last_epoch']!=2 or not extra['rng']: raise RuntimeError('Missing scheduler/rank RNG')
        ranks.append(dict(rank=rank,last_epoch=2,rng_keys=sorted(extra['rng'])))
    raw=SimpleNamespace(seed=0,env_num=1,group_n=8,is_train=True,reset_index=0,
        training_rng=np.random.RandomState(0),validation_rng=np.random.RandomState(0))
    manager=SimpleNamespace(envs=raw,memory=None,_terminal_by_env=[],_episode_reset_index=-1,_step_index=0)
    with patch.dict(os.environ,SC2_TRAIN_SEED_PROTOCOL=cfg['seed_protocol'],SC2_ORIGINAL_GAME_SEEDS='0'):
        if index==1:
            state=torch.load(cp/'sc2_state.pt',map_location='cpu',weights_only=False)
            if state['global_step']!=2 or not state['driver_rng']: raise RuntimeError('Missing native driver state')
            state=state['train_env']
        else: state=legacy_environment_state(manager,parent/'runs/train2',2)
        restore_environment(manager,state)
    if raw.reset_index!=2: raise RuntimeError('SC2 reset position mismatch')
    for name in ('data/train.parquet','data/test.parquet',
        'agent_system/environments/env_package/sc2_online_restored/SC2ArenaDyStrategy/knowledge/BO/replay_observations_Flat128_d4_TvT_Macro_g2_Result.Victory_twobase.json'):
        if sha256(a.ROOT/'runtime'/name)!=sha256(parent/'runtime'/name): raise RuntimeError('Changed data/BO')
    a.save(a.ROOT/'cpu/parent-small-state.json',dict(rank_states=ranks,next_reset_index=2,
        next_seeds=ablation_seeds(cfg['seed_protocol'],0,2,1,8),native_driver_rng=index==1,cuda_initialized=torch.cuda.is_initialized()))


def verify_updates(audits,metrics,start,end):
    if ([x['pending_global_step'] for x in audits]!=list(range(start,end+1))
            or any(x['decision']!='accept' for x in audits) or len(metrics)!=end-start+1
            or any(not math.isfinite(x['actor/grad_norm']) or x['actor/grad_norm']<=0
                   or x['policy_credit/invalid_advantage_max']>0 for x in metrics)):
        raise RuntimeError('Actual PPO/audit/gradient evidence mismatch')


def verify(stage,write=True):
    if INDEX==0:
        BASE_VERIFY(stage,write)
        if stage=='train2' and not (a.ROOT/'runs/train2/checkpoints/global_step_2/sc2_state.pt').is_file():
            raise RuntimeError('SpB short CP2 lacks native SC2 state')
        if stage=='post':
            for rank in range(8):
                if not previous.paired_rng_matches(a.read(a.ROOT/f'runs/post/sampling-rank{rank}.json'),
                        a.read(a.ROOT/f'runs/pre/sampling-rank{rank}.json'),rank):
                    raise RuntimeError('SpB short pre/post sampling RNG mismatch')
        return
    cfg=a.read(a.ROOT/'deployment.json')
    out=a.ROOT/'runs'/stage
    result,evidence=a.verify_common(out,stage,752 if stage=='train96' else 8)
    if stage=='train96':
        if (result['start_step'],result['last_global_step'],result['completed_steps'])!=(2,96,94) or not result['checkpoint_complete']:
            raise RuntimeError('Expected exactly 94 new updates')
        rows=[json.loads(x) for x in (out/'training_seeds.jsonl').read_text().splitlines()]
        if len(rows)!=94 or any(row['reset_index']!=i or row['seed_protocol']!=cfg['seed_protocol']
                or row['seeds']!=ablation_seeds(cfg['seed_protocol'],0,i,1,8) for i,row in enumerate(rows,2)):
            raise RuntimeError('Actual resumed seed sequence mismatch')
        resume=a.read(out/'checkpoints/resume_state.json')
        expected_source='checkpoint' if INDEX==1 else 'verified legacy ledger; driver RNG unavailable, not bitwise replay'
        if (resume['from_checkpoint']!=str(parent_for(INDEX)/'runs/train2/checkpoints/global_step_2')
                or resume['global_step']!=2 or resume['next_reset_index']!=2
                or resume['next_seeds']!=ablation_seeds(cfg['seed_protocol'],0,2,1,8)
                or not resume['model_optimizer_dataloader_load_returned'] or resume['source']!=expected_source):
            raise RuntimeError('Actual checkpoint/SC2 load evidence mismatch')
        verify_updates([json.loads(x) for x in (out/'checkpoints/sc2_policy_credit_audit.jsonl').read_text().splitlines()],
                       a.read(out/'metrics.json'),3,96)
        for step in range(8,97,8):
            for name in ['data.pt','sc2_state.pt']+[f'actor/{k}_world_size_8_rank_{r}.pt' for k in ('model','optim','extra_state') for r in range(8)]:
                if (out/f'checkpoints/global_step_{step}'/name).stat().st_size<=0: raise RuntimeError('Incomplete checkpoint')
        evidence.update(resume=resume,ppo_updates=94,checkpoints=list(range(8,97,8)))
    elif stage=='eval96':
        proof=a.read(out/'checkpoint_evaluation.json')
        seeds=[json.loads(x)['seeds'] for x in (out/'evaluation_seeds.jsonl').read_text().splitlines()]
        if (result['training_updates']!=0 or not proof['val_only'] or proof['optimizer_updates']!=0
                or proof['loaded_global_step']!=96 or not proof['checkpoint_load_returned']
                or proof['checkpoint']!=str(a.ROOT/'runs/train96/checkpoints/global_step_96')
                or proof['game_seeds']!=a.EVAL_SEEDS or seeds!=[a.EVAL_SEEDS]): raise RuntimeError('Final eval mismatch')
        for rank in range(8):
            if not previous.paired_rng_matches(a.read(out/f'sampling-rank{rank}.json'),
                    a.read(parent_for(INDEX)/f'runs/post/sampling-rank{rank}.json'),rank): raise RuntimeError('Paired RNG mismatch')
    else: raise ValueError('Undeclared long stage')
    if write: a.save(a.ROOT/f'acceptance-{stage}.json',dict(result=result,evidence=evidence,checked_at=time.time()))


def predecessor_complete():
    queue=a.read(PREDECESSOR/'queue-state.json')
    state=a.read(PREDECESSOR/'state.json')
    if queue['phase']=='failed' or state['phase']=='failed': raise RuntimeError('Predecessor failed; stop all successors')
    if queue['phase']!='completed': return False
    if queue.get('exit_code')!=0 or state.get('exit_code')!=0 or state['completed']!=['train96','eval96']:
        raise RuntimeError('Predecessor terminal evidence mismatch')
    docker_state=json.loads(a.cmd(['docker','inspect','--format','{{json .State}}','sc2-qwen-l7same96-197-20260922-r1']))
    if docker_state['Running'] or docker_state['ExitCode']!=0: raise RuntimeError('Predecessor container not successfully exited')
    # Invoke its frozen, already tested terminal verifier; no GPU/model loads.
    cfg=a.read(PREDECESSOR/'deployment.json')
    if cfg['runtime_sha']!='279d5496464de29e14c64924ccb829147351efbd': raise RuntimeError('Wrong predecessor runtime')
    script=Path(cfg['controller_source'])/'experiments/records/20260921-sc2-policy-credit-v1'
    code=f"import sys;sys.path.insert(0,{str(script)!r});import qwen_l7_long197 as m;m.configure();m.verify('train96',write=False);m.verify('eval96',write=False)"
    sp.run([sys.executable,'-B','-c',code],check=True,timeout=120)
    return True


def regressions(index,receipt_root=None):
    # Run the retained complete regression suite without replacing its globals.
    import unittest
    import torch
    sys.path[:0]=[str(SOURCE/'tests'),str(SOURCE/'scripts')]
    names=['test_metric_precision','test_l7_precision_continuation197','test_l7_followup197','test_sc2_checkpoint_resume','test_qwen_l7_long197','test_sc2_policy_resume',
        'test_sc2_action_support','test_sc2_policy_credit','test_sc2_task_signal','test_sc2_no_thinking_torch',
        'test_thinking_action_boundary','test_r6_format_reward','test_original_bo_segment','test_original_game_seeds',
        'test_sc2_generation_tokens','test_policy_credit_acceptance197','test_policy_credit_storage197',
        'test_policy_credit_storage_coordination197','test_qwen_seed_acceptance197','test_qwen_seed_acceptance197_r3','test_qwen_seed_acceptance197_r4']
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromNames(names))
    passed=result.wasSuccessful() and not result.skipped and not torch.cuda.is_initialized()
    destination = receipt_root if receipt_root is not None else SUITE/PARTS[index]
    identity = receipt_root if receipt_root is not None else SUITE
    a.save(destination/'regressions.json',dict(passed=passed,tests=result.testsRun,skips=len(result.skipped),
        cuda_initialized=torch.cuda.is_initialized(),runtime_sha=a.read(identity/'deployment.json')['runtime_sha'],checked_at=time.time()),lock_root=identity)
    if not passed: raise RuntimeError('Full CPU regressions failed')


def queue():
    cfg=a.read(SUITE/'deployment.json')
    a.clean(SOURCE,cfg['controller_sha']);a.clean(SUITE/'runtime',cfg['runtime_sha']);a.clean(a.ORCH,a.ORCH_SHA)
    regression=a.read(SUITE/PARTS[0]/'regressions.json')
    if not regression['passed'] or regression['skips'] or regression['runtime_sha']!=cfg['runtime_sha']:
        raise RuntimeError('Full zero-skip CPU regressions required')
    for index in range(3):
        select(index)
        proof=a.read(a.ROOT/'readiness.json')
        if not proof['passed'] or proof['cuda_initialized'] or proof['runtime_sha']!=cfg['runtime_sha']:
            raise RuntimeError('All seven launcher/Hydra stages must pass before queue')
    with (SUITE/'queue.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (SUITE/'queue-state.json').exists() or (SUITE/'dispatch.json').exists(): raise RuntimeError('Already queued/dispatched; no retry')
        state=dict(phase='waiting-predecessor',completed=[],first_dispatch_by=FIRST_DISPATCH_BY)
        process=None
        try:
            a.save(SUITE/'queue-state.json',state)
            while not predecessor_complete():
                if time.time()>=FIRST_DISPATCH_BY: raise TimeoutError('First admission expired')
                time.sleep(60)
            a.save(SUITE/'predecessor-acceptance.json',dict(passed=True,root=str(PREDECESSOR),checked_at=time.time()))
            total_deadline=arm_deadline=None
            for index,part in enumerate(PARTS):
                select(index)
                if index==1:
                    a.save(a.ROOT/'resume-contract.json',contract_for(index))
                    with (a.ROOT/'parent-cpu.log').open('x') as log:
                        sp.run(docker('parent-cpu',index),stdout=log,stderr=sp.STDOUT,check=True,
                               timeout=min(600,arm_deadline-45-time.time()))
                    if not a.read(a.ROOT/'parent-readiness.json')['actual_parent_verified']: raise RuntimeError('Native prefix not accepted')
                elif index==2:
                    verify_contract(a.read(a.ROOT/'resume-contract.json'))
                state.update(phase='waiting-resources',part=part)
                a.save(SUITE/'queue-state.json',state)
                while True:
                    deadline=arm_deadline if index==1 else total_deadline
                    budget(deadline)
                    if total_deadline is None and time.time()>=FIRST_DISPATCH_BY: raise TimeoutError('First admission expired')
                    previous.ROOT=a.ROOT
                    if previous.resources_ready(): break
                    time.sleep(60)
                with (a.ROOT/'fsync-probe').open('xb') as f:
                    f.write(b'l7-followup197\n');f.flush();os.fsync(f.fileno())
                if (a.ROOT/'fsync-probe').read_bytes()!=b'l7-followup197\n': raise RuntimeError('Fsync readback failed')
                start=time.time()
                if index==0:
                    total_deadline=start+2*ARM_SECONDS
                    a.save(SUITE/'dispatch.json',dict(start=start,deadline=total_deadline,gpu_hours=768))
                if index!=1: arm_deadline=min(start+ARM_SECONDS,total_deadline)
                args=docker('execute',index)
                a.save(a.ROOT/'dispatch.json',dict(start=start,deadline=arm_deadline,command=args))
                state.update(phase='running-unverified',part=part,deadline=total_deadline,arm_deadline=arm_deadline)
                a.save(SUITE/'queue-state.json',state)
                with (a.ROOT/'container.log').open('x') as log:
                    process=sp.Popen(args,stdout=log,stderr=sp.STDOUT)
                    while process.poll() is None:
                        budget(arm_deadline);time.sleep(15)
                if process.returncode or a.read(a.ROOT/'state.json')['phase']!='completed': raise RuntimeError('Part failed; no successor/retry')
                for stage in a.read(a.ROOT/'deployment.json')['stages']: verify(stage,write=False)
                state['completed'].append(part);state['phase']='part-completed'
                a.save(SUITE/'queue-state.json',state)
                process=None
            state.update(phase='completed',exit_code=0,learning_validated=False)
            a.save(SUITE/'queue-state.json',state)
        except BaseException as exc:
            try:
                state.update(phase='failed',error=str(exc));a.save(SUITE/'queue-state.json',state)
            finally:
                if process is not None: a.stop_owned()
            raise


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',choices=['prepare','queue','cpu-command','regressions-command','cpu','parent-cpu','regressions','execute'])
    parser.add_argument('index',type=int,nargs='?',choices=range(3))
    arg=parser.parse_args()
    if arg.mode in ('prepare','queue'): globals()[arg.mode]()
    elif arg.index is None: parser.error('Exact part index required')
    elif arg.mode.endswith('-command'): print(json.dumps(docker(arg.mode.removesuffix('-command'),arg.index)))
    elif arg.mode=='regressions': regressions(arg.index)
    elif arg.mode=='cpu': cpu(arg.index)
    elif arg.mode=='parent-cpu': parent_cpu(arg.index)
    else:
        select(arg.index);a.execute()
