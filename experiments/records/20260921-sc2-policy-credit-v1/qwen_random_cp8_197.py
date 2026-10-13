"""Approved one-shot native CP8 recovery; fixed old clocks, host-only guardian."""
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
import l7_followup197_r4 as old
import qwen_l7_long197 as previous

sys.path.insert(0, str(a.SOURCE))
from agent_system.sc2_policy_resume import (checkpoint_names, recovered_prefix_files,
    sha256, verify_contract)
from agent_system.sc2_seed_protocol import ablation_seeds

ROOT = Path('/var/jfsCache/sc2-qwen-random-cp8-197-20260923-r2')
CPU_PREPARATION = [Path('/var/jfsCache/sc2-qwen-random-cp8-197-20260923-r1'),
                   Path('/var/jfsCache/sc2-qwen-random-cp8-197-source-20260923-r1')]
PARENT = old.ROOT/'qwen-random/long'
ANCESTOR = Path('/var/jfsCache/sc2-qwen-seeds197-20260922-r4/l7-random')
CHECKPOINT = PARENT/'runs/train96/checkpoints/global_step_8'
OLD_SOURCE = Path('/var/jfsCache/sc2-l7-followup197-source-20260922-r4')
CONTAINER = 'sc2-qwen-random-cp8-197-20260923-r2'
DEADLINE = 1790308720.0467553
SUITE_DEADLINE = 1790420762.305692
ORIGINAL_START = 1790135920.0467653
STAGES = ['train96', 'eval96']


def configure():
    a.ROOT = ROOT
    a.STORAGE_LOCK_ROOT = ROOT
    a.CONTAINER = CONTAINER
    a.DOCKER_SCRIPT = a.HERE/'qwen_random_cp8_197.py'
    a.RUNTIME_SHA = (a.read(ROOT/'deployment.json')['runtime_sha'] if (ROOT/'deployment.json').exists()
                     else a.cmd(['git','-C',a.SOURCE,'rev-parse','HEAD']))
    previous.ROOT = ROOT


def accounts():
    retained = [OLD_SOURCE, ANCESTOR, *old.RETAINED, *CPU_PREPARATION]
    return [dict(roots=[ROOT,a.SOURCE.parent,old.ROOT/'qwen-random',*retained],
                 receipt_root=ROOT,limit=1024*a.GIB,deadline=DEADLINE),
            dict(roots=[ROOT,a.SOURCE.parent,old.ROOT,*retained],
                 receipt_root=ROOT/'suite-account',limit=2048*a.GIB,deadline=SUITE_DEADLINE)]


def contract_for():
    contract = dict(version='recovered-qwen-random-native-cp8-v1',parent=str(PARENT),
        checkpoint=str(CHECKPOINT),parent_sha='9cb291ea5f50de205c5d88371e08ce229b7d9d04',
        start_step=8,target_step=96,driver_rng_unavailable_accepted=False,
        files={name:sha256(PARENT/name) for name in recovered_prefix_files()},
        checkpoint_bytes={name:(CHECKPOINT/name).stat().st_size for name in checkpoint_names()})
    verify_contract(contract)
    return contract


def prepare():
    if ROOT.exists():
        raise RuntimeError('Fresh exact root required; no prepare retry')
    sha = a.cmd(['git','-C',a.SOURCE,'rev-parse','HEAD'])
    a.clean(a.SOURCE,sha);a.clean(a.ORCH,a.ORCH_SHA)
    contract = contract_for()
    cfg = copy.deepcopy(a.read(PARENT/'deployment.json'))
    cfg.update(runtime_sha=sha,controller_sha=sha,controller_source=str(a.SOURCE),
        predecessor=str(PARENT),stages=STAGES,games=[704,8],updates=[88,0],
        start_step=8,target_step=96,training_seeds=[ablation_seeds('independent_uniform101',0,i,1,8) for i in range(8,96)],
        original_start=ORIGINAL_START,deadline=DEADLINE,suite_deadline=SUITE_DEADLINE,
        wall_seconds=172800,gpu_hours=384,suite_gpu_hours=768,output_limit_bytes=1024*a.GIB,
        queue_expires=DEADLINE-45,no_retry=True,successors_authorized=False,
        no_long_training=False,run_prefix='qwen-random-cp8-197-r2',worker_hook='l7_followup_hook.install',
        prior_qwen_dispatched_slots=96,new_slots=712,cumulative_qwen_slots=808,
        added_slots_approved=48,cumulative_suite_slots=1608,
        storage_supervision='host-guardian-v1',host_stage_entry_log=True,container_rootfs_read_only=True,
        accounts=[dict(x,roots=list(map(str,x['roots'])),receipt_root=str(x['receipt_root'])) for x in accounts()],
        authorization='User explicitly approved +48 slots for own native CP8 to96 plus8 eval; '
            'no reset of original Qwen/suite deadlines, GPU-hour or storage limits; no other arms/retries',
        recovery_limit='Native CP8 driver/rank RNG required; historical CP2 ancestry remains non-bitwise; '
            'old failed r4 retained, global9..13 discarded but charged; timing equivalence unproven',
        startup_change='Only cooperating SC2 launches serialized through first observation; one reset attempt; eight games remain parallel')
    ROOT.mkdir()
    for name in ('runs','cpu','tmp','suite-account'):(ROOT/name).mkdir()
    for name in ('task-home','cache','cuda-cache'):(ROOT/'tmp'/name).mkdir()
    a.cmd(['git','clone','--quiet','--shared',a.SOURCE,ROOT/'runtime'])
    a.cmd(['git','-C',ROOT/'runtime','checkout','--quiet','--detach',sha])
    a.save(ROOT/'resume-contract.json',contract)
    a.save(ROOT/'deployment.json',cfg)


def invocation(cfg,stage,dry=False):
    if stage not in STAGES:raise ValueError('Undeclared recovery stage')
    args,env,base = a.invocation(cfg,'train2' if stage=='train96' else 'post',dry)
    out = ROOT/('cpu' if dry else 'runs')/stage
    args = [x.replace(str(base),str(out)) for x in args]
    settings = {'+ray_init.runtime_env.env_vars.SC2_ACCEPTANCE_STAGE':repr(stage),
        'trainer.total_training_steps':'96','trainer.total_epochs':'96' if stage=='train96' else '1',
        'trainer.save_freq':'8' if stage=='train96' else '-1','trainer.resume_mode':'resume_path',
        'trainer.resume_from_path':str(CHECKPOINT if stage=='train96' else ROOT/'runs/train96/checkpoints/global_step_96')}
    args = [x for x in args if x.split('=',1)[0] not in settings]
    args += [k+'='+v for k,v in settings.items()]
    if stage=='train96':
        args += ['+trainer.sc2_import_legacy_final=False',
                 f'+trainer.sc2_policy_credit_resume_contract={ROOT}/resume-contract.json']
    env.update(OUTPUT_DIR=str(out),RUN_ID=cfg['run_prefix']+'-'+stage,
        SC2_CHECKPOINT_RESUME=str(stage=='train96'),RAY_TMPDIR='/tmp/qr8-'+stage)
    return args,env,out


def docker(mode,stage=None):
    args = a.docker('execute' if mode=='stage' else 'cpu')
    args[2:2] = ['--read-only','--log-driver','none','-e','HOME=/tmp/task-home',
        '-e','XDG_CACHE_HOME=/tmp/cache','-e','CUDA_CACHE_PATH=/tmp/cuda-cache','-e','TMPDIR=/tmp']
    # All ancestors and their runtime symlink targets are immutable. No old CP copies.
    for path in [old.ROOT,OLD_SOURCE,ANCESTOR.parent,*(old.RETAINED)]:
        args[2:2] = ['-v',f'{path}:{path}:ro']
    if mode!='stage':
        model=a.read(ROOT/'deployment.json')['host']['model']
        args[args.index(f'{model}:/assets/qwen:ro')]=f'{previous.CPU_MODEL}:/assets/qwen:ro'
        args[args.index('--name')+1]=CONTAINER+'-'+mode
        args[2:2]=['-v',f'{previous.SPB_METADATA}:/metadata/spb:ro',
            '-e','SC2_TEST_SPB_METADATA_PATH=/metadata/spb','-e','SC2_TEST_QWEN_METADATA_PATH=/assets/qwen',
            '-e','SC2_TEST_TOKENIZER_PATH=/assets/qwen','-e','OMP_NUM_THREADS=2','-e','TOKENIZERS_PARALLELISM=false']
    writable=[]
    for i,x in enumerate(args[:-1]):
        if x=='-v':
            spec=args[i+1].split(':')
            if spec[-1]!='ro':writable.append(tuple(spec[:2]))
    if writable != [(str(ROOT),str(ROOT)),(str(ROOT/'tmp'),'/tmp')]:
        raise RuntimeError('Unexpected persistent writable mounts')
    args[-1]=mode
    if mode=='stage':
        if stage not in STAGES:raise ValueError('Undeclared stage')
        args[1]='create';args[args.index('--name')+1]+='-'+stage;args.append(stage)
    return args


def small_state():
    import random
    import numpy as np
    import torch
    from types import SimpleNamespace
    from unittest.mock import patch
    from agent_system.sc2_resume import restore_environment
    verify_contract(a.read(ROOT/'resume-contract.json'))
    ranks=[]
    for rank in range(8):
        extra=torch.load(CHECKPOINT/f'actor/extra_state_world_size_8_rank_{rank}.pt',map_location='cpu',weights_only=False)
        if extra['lr_scheduler']['last_epoch']!=8 or not extra['rng']:raise RuntimeError('Invalid native rank state')
        ranks.append(dict(rank=rank,scheduler_last_epoch=8,rng_keys=sorted(extra['rng'])))
    state=torch.load(CHECKPOINT/'sc2_state.pt',map_location='cpu',weights_only=False)
    data=torch.load(CHECKPOINT/'data.pt',map_location='cpu',weights_only=False)
    if state['global_step']!=8 or state['empty_policy_batches'] or not data:raise RuntimeError('Invalid native CP8 state')
    py_rng,np_rng,torch_rng=state['driver_rng']
    random.Random().setstate(py_rng);np.random.RandomState().set_state(np_rng)
    torch.Generator(device='cpu').set_state(torch_rng)
    restored=[]
    with patch.dict(os.environ,SC2_TRAIN_SEED_PROTOCOL='independent_uniform101',SC2_ORIGINAL_GAME_SEEDS='0'):
        for name in ('train_env','val_env'):
            saved=state[name]
            raw=SimpleNamespace(**{k:saved[k] for k in ('seed','env_num','group_n','is_train')},
                reset_index=0,training_rng=np.random.RandomState(0),validation_rng=np.random.RandomState(0))
            manager=SimpleNamespace(envs=raw,memory=None,_terminal_by_env=[],_episode_reset_index=-1,_step_index=0)
            restore_environment(manager,saved)
            restored.append(dict(kind=name,reset_index=raw.reset_index,episode_reset_index=manager._episode_reset_index,
                seed_protocol=saved['seed_protocol']))
    if restored[0]['reset_index']!=8 or restored[0]['episode_reset_index']!=7:raise RuntimeError('Native seed counter mismatch')
    return dict(passed=True,global_step=8,rank_states=ranks,environments=restored,driver_rng_restored_on_cpu=True,
        next_seeds=ablation_seeds('independent_uniform101',0,8,1,8),cuda_initialized=torch.cuda.is_initialized())


def cpu():
    import torch
    from hydra import compose,initialize_config_dir
    from omegaconf import OmegaConf
    from verl.trainer.ppo.sc2_policy_credit import validate_config as credit_config
    from verl.utils.sc2_action_support import validate_config as support_config
    from ray._private.utils import validate_socket_filepath
    sys.path.insert(0,str(a.ORCH/a.REC))
    from seed_ray_paths import socket_path
    cfg=a.read(ROOT/'deployment.json')
    a.clean(a.SOURCE,cfg['runtime_sha']);a.clean(ROOT/'runtime',cfg['runtime_sha'])
    check=sp.run(['sha256sum','-c','configs/system-v1.sha256'],cwd=ROOT/'runtime',text=True,capture_output=True,timeout=30)
    (ROOT/'cpu/source-check.log').write_text(check.stdout+check.stderr)
    if check.returncode:raise RuntimeError('Source manifest failed')
    a.save(ROOT/'cpu/parent-small-state.json',small_state())
    for name in ('data/train.parquet','data/test.parquet',
        'agent_system/environments/env_package/sc2_online_restored/SC2ArenaDyStrategy/knowledge/BO/replay_observations_Flat128_d4_TvT_Macro_g2_Result.Victory_twobase.json'):
        if sha256(ROOT/'runtime'/name)!=sha256(old.ROOT/'runtime'/name):raise RuntimeError('Data/BO changed')
    for stage in STAGES:
        args,env,out=invocation(cfg,stage,True)
        proc=sp.run(args,env=env,cwd=ROOT/'runtime',capture_output=True,text=True,timeout=90)
        (ROOT/'cpu'/f'{stage}.log').write_text(proc.stdout+proc.stderr)
        if proc.returncode:raise RuntimeError('Actual dry launcher failed: '+stage)
        command=a.read(out/'effective_config.json')['command']
        with initialize_config_dir(config_dir=str(ROOT/'runtime/verl/trainer/config'),version_base=None):
            c=compose(config_name='ppo_trainer',overrides=command[command.index('verl.trainer.main_ppo')+1:])
        credit_config(c);support_config(c)
        ev=c.ray_init.runtime_env.env_vars
        if (c.trainer.val_only!=(stage=='eval96') or c.trainer.total_training_steps!=96
            or c.trainer.n_gpus_per_node!=8 or c.env.rollout.n!=8 or c.data.max_response_length!=192
            or str(ev.SC2_RESET_CONCURRENCY)!='1' or str(ev.SC2_RESET_RETRIES)!='1'
            or c.actor_rollout_ref.actor.optim.lr!=1e-6 or c.actor_rollout_ref.actor.optim.warmup_style!='constant'
            or c.actor_rollout_ref.actor.optim.lr_warmup_steps_ratio!=0):raise RuntimeError('Unexpected recovery protocol')
        a.save(out/'resolved_config.json',OmegaConf.to_container(c,resolve=True))
        validate_socket_filepath(socket_path(env['RAY_TMPDIR']))
    if torch.cuda.is_initialized():raise RuntimeError('CPU initialized CUDA')
    a.save(ROOT/'readiness.json',dict(passed=True,runtime_sha=cfg['runtime_sha'],cuda_initialized=False,
        actual_parent_verified=True,actual_entries_and_hydra_configs=True,checked_at=time.time()))


def regressions():
    import unittest
    import torch
    sys.path[:0]=[str(a.SOURCE/'tests'),str(a.SOURCE/'scripts')]
    names=['test_metric_precision','test_l7_precision_continuation197','test_l7_followup197',
        'test_sc2_checkpoint_resume','test_qwen_l7_long197','test_sc2_policy_resume',
        'test_sc2_action_support','test_sc2_policy_credit','test_sc2_task_signal',
        'test_sc2_no_thinking_torch','test_thinking_action_boundary','test_r6_format_reward',
        'test_original_bo_segment','test_original_game_seeds','test_sc2_generation_tokens',
        'test_policy_credit_acceptance197','test_policy_credit_storage197','test_policy_credit_storage_coordination197',
        'test_qwen_seed_acceptance197','test_qwen_seed_acceptance197_r3','test_qwen_seed_acceptance197_r4',
        'test_sc2_reset_startup','test_qwen_random_cp8_197']
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromNames(names))
    proof=dict(passed=result.wasSuccessful() and not result.skipped and not torch.cuda.is_initialized(),
        tests=result.testsRun,skips=len(result.skipped),cuda_initialized=torch.cuda.is_initialized(),
        runtime_sha=a.read(ROOT/'deployment.json')['runtime_sha'],checked_at=time.time())
    a.save(ROOT/'regressions.json',proof,lock_root=ROOT)
    if not proof['passed']:raise RuntimeError('CPU regressions failed')


def host_regressions():
    import unittest
    if Path('/.dockerenv').exists():raise RuntimeError('Host tests require the actual host')
    sys.path.insert(0,str(a.SOURCE/'tests'))
    names=['test_l7_host_continuation197','test_host_stage197','test_storage_quiescent197',
        'test_policy_credit_storage197','test_policy_credit_storage_coordination197']
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromNames(names))
    proof=dict(passed=result.wasSuccessful() and not result.skipped,tests=result.testsRun,skips=len(result.skipped),
        runtime_sha=a.read(ROOT/'deployment.json')['runtime_sha'],host_only=True,checked_at=time.time())
    a.save(ROOT/'host-regressions.json',proof,lock_root=ROOT)
    if not proof['passed']:raise RuntimeError('Actual host regressions failed')


def verify(stage,write=True):
    out=ROOT/'runs'/stage
    result,evidence=a.verify_common(out,stage,704 if stage=='train96' else 8)
    if any(a.read(out/n).get('metrics_precision')!='binary64-v1' for n in ('manifest.json','result.json')):
        raise RuntimeError('Full precision required')
    if stage=='train96':
        if (result['start_step'],result['last_global_step'],result['completed_steps'])!=(8,96,88) or not result['checkpoint_complete']:
            raise RuntimeError('Expected88 actual new updates')
        rows=[json.loads(x) for x in (out/'training_seeds.jsonl').read_text().splitlines()]
        if len(rows)!=88 or any(x['reset_index']!=i or x['base_seed']!=0 or x['seed_protocol']!='independent_uniform101'
            or x['seeds']!=ablation_seeds('independent_uniform101',0,i,1,8) for i,x in enumerate(rows,8)):
            raise RuntimeError('Native continuation seed mismatch')
        resume=a.read(out/'checkpoints/resume_state.json')
        if (resume['from_checkpoint']!=str(CHECKPOINT) or resume['global_step']!=8 or resume['next_reset_index']!=8
            or resume['source']!='checkpoint' or not resume['model_optimizer_dataloader_load_returned']
            or resume['next_seeds']!=ablation_seeds('independent_uniform101',0,8,1,8)):
            raise RuntimeError('Actual native CP8 load missing')
        metrics=a.read(out/'metrics.json')
        audits=[json.loads(x) for x in (out/'checkpoints/sc2_policy_credit_audit.jsonl').read_text().splitlines()]
        if ([x['step'] for x in metrics]!=list(range(9,97)) or [x['pending_global_step'] for x in audits]!=list(range(9,97))
            or any(x['decision']!='accept' for x in audits)
            or any(not math.isfinite(x[k]) for x in metrics for k in ('actor/grad_norm','policy_credit/invalid_advantage_max','timing_s/update_actor'))
            or any(x['actor/grad_norm']<=0 or x['timing_s/update_actor']<=0 or x['policy_credit/invalid_advantage_max']>0 for x in metrics)):
            raise RuntimeError('Actual PPO/gradient/invalid credit gate failed')
        for step in range(16,97,8):
            for name in checkpoint_names():
                if (out/f'checkpoints/global_step_{step}'/name).stat().st_size<=0:raise RuntimeError('Incomplete native checkpoint')
        evidence.update(resume=resume,ppo_updates=88,checkpoints=list(range(16,97,8)),retained_parent_checkpoint=8)
    elif stage=='eval96':
        proof=a.read(out/'checkpoint_evaluation.json')
        seeds=[json.loads(x)['seeds'] for x in (out/'evaluation_seeds.jsonl').read_text().splitlines()]
        if (result['training_updates']!=0 or not proof['val_only'] or proof['optimizer_updates']!=0
            or proof['loaded_global_step']!=96 or not proof['checkpoint_load_returned']
            or proof['checkpoint']!=str(ROOT/'runs/train96/checkpoints/global_step_96')
            or proof['game_seeds']!=a.EVAL_SEEDS or seeds!=[a.EVAL_SEEDS]):raise RuntimeError('Paired eval96 load mismatch')
        for rank in range(8):
            if not previous.paired_rng_matches(a.read(out/f'sampling-rank{rank}.json'),a.read(ANCESTOR/f'runs/post/sampling-rank{rank}.json'),rank):
                raise RuntimeError('Paired rank RNG mismatch')
    else:raise ValueError('Undeclared verifier stage')
    if write:a.save(ROOT/f'acceptance-{stage}.json',dict(result=result,evidence=evidence,checked_at=time.time()))


def admit(stage):
    while True:
        if time.time()>=DEADLINE-45:raise TimeoutError('Original Qwen cutoff; no extension')
        h.sample(accounts(),ROOT);old.writers_clear(accounts()[1]['roots'])
        if previous.resources_ready():break
        a.save(ROOT/'queue-state.json',dict(phase='waiting-resources',stage=stage,deadline=DEADLINE))
        time.sleep(min(30,max(0,DEADLINE-45-time.time())))
    probe=ROOT/('fsync-'+stage)
    with probe.open('xb') as stream:
        stream.write(b'qr8\n');stream.flush();os.fsync(stream.fileno())
    if probe.read_bytes()!=b'qr8\n':raise RuntimeError('Fsync readback failed')
    a.save(ROOT/('admission-'+stage+'.json'),dict(passed=True,checked_at=time.time(),deadline=DEADLINE,
        eight_idle_gpus=True,ram_gib_min=600,nvme_gib_min=1084,fsync=True))


def queue():
    cfg=a.read(ROOT/'deployment.json')
    a.clean(a.SOURCE,cfg['controller_sha']);a.clean(ROOT/'runtime',cfg['runtime_sha']);a.clean(a.ORCH,a.ORCH_SHA)
    for name in ('readiness.json','regressions.json','host-regressions.json'):
        proof=a.read(ROOT/name)
        if not proof['passed'] or proof.get('skips',0) or proof.get('cuda_initialized',False) or proof['runtime_sha']!=cfg['runtime_sha']:
            raise RuntimeError('Actual zero-skip CPU acceptance required')
    with (ROOT/'queue.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (ROOT/'queue-state.json').exists() or (ROOT/'dispatch.json').exists():raise RuntimeError('Already queued; no retry')
        try:
            verify_contract(a.read(ROOT/'resume-contract.json'))
            a.save(ROOT/'queue-state.json',dict(phase='admitting',deadline=DEADLINE,completed=[]))
            def stage_admit(stage):
                admit(stage)
                if stage=='train96':
                    a.save(ROOT/'dispatch.json',dict(start=ORIGINAL_START,resumed_at=time.time(),deadline=DEADLINE,
                        suite_deadline=SUITE_DEADLINE,original_clock_preserved=True,gpu_hours=384,new_slots=712))
                a.save(ROOT/'queue-state.json',dict(phase='running-unverified',stage=stage,deadline=DEADLINE))
            state=h.run_stages(STAGES,lambda stage:docker('stage',stage),verify,accounts(),ROOT,
                ROOT/'host-supervision',ROOT,DEADLINE,admit=stage_admit)
            a.save(ROOT/'state.json',state);a.save(ROOT/'queue-state.json',state)
        except BaseException as exc:
            state=(a.read(ROOT/'host-supervision/state.json') if (ROOT/'host-supervision/state.json').exists() else {})
            state.update(phase='failed',error_type=type(exc).__name__,error=str(exc),deadline=DEADLINE)
            a.save(ROOT/'state.json',state);a.save(ROOT/'queue-state.json',state)
            raise


def child_stage(stage):
    cfg=a.read(ROOT/'deployment.json')
    a.clean(a.SOURCE,cfg['controller_sha']);a.clean(ROOT/'runtime',cfg['runtime_sha'])
    args,env,out=invocation(cfg,stage)
    fd=os.open(ROOT/(stage+'-entry.log'),os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    os.dup2(fd,1);os.dup2(fd,2);os.close(fd)
    os.chdir(ROOT/'runtime');os.execvpe(args[0],args,env)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',choices=['prepare','cpu','regressions','host-regressions','cpu-command','regressions-command','queue','stage'])
    parser.add_argument('stage',nargs='?',choices=STAGES)
    args=parser.parse_args()
    if args.mode not in ('regressions','host-regressions'):configure()
    if args.mode.endswith('-command'):print(json.dumps(docker(args.mode.removesuffix('-command'))))
    elif args.mode=='stage':child_stage(args.stage)
    else:globals()[args.mode.replace('-','_')]()
