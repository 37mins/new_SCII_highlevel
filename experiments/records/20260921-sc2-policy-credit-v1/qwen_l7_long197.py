"""One approved Qwen L7 same-seed step2→96 continuation; no retry or successor."""
import argparse
import copy
import json
import math
import os
from pathlib import Path
import shutil
import subprocess as sp
import sys
import time

import acceptance197 as a

HERE, SOURCE = a.HERE, a.SOURCE
sys.path.insert(0, str(SOURCE))
from agent_system.sc2_policy_resume import prefix_files, sha256, verify_contract
from agent_system.sc2_seed_protocol import ablation_seeds

ROOT = Path('/var/jfsCache/sc2-qwen-l7same96-197-20260922-r1')
PARENT = Path('/var/jfsCache/sc2-qwen-seeds197-20260922-r4/l7-same')
PARENT_SHA = '2f95c9fd505bd4529070ff4988c5c9efcb111b53'
CHECKPOINT = PARENT / 'runs/train2/checkpoints/global_step_2'
CONTAINER = 'sc2-qwen-l7same96-197-20260922-r1'
QUEUE_EXPIRES = 1790071200  # Sep22 18:00 Beijing, bounded admission, not ETA.
WALL_SECONDS = 48 * 3600
LIMIT = 1024 * a.GIB
CPU_MODEL = Path('/data/yangjinyue/new-scii-qwen-instruct2507-level5-v1/staging/Qwen3-4B-Instruct-2507-download-cdbee75')
SPB_METADATA = Path('/var/jfsCache/sc2-generation-tokens-cpu-20260921.2O3Eqc/spb-metadata')
BASE_INVOCATION, BASE_DOCKER = a.invocation, a.docker


def configure():
    a.ROOT = ROOT
    a.STORAGE_LOCK_ROOT = ROOT
    a.RUNTIME_SHA = a.read(ROOT/'deployment.json')['runtime_sha'] if (ROOT/'deployment.json').exists() else a.cmd(['git','-C',SOURCE,'rev-parse','HEAD'])
    a.CONTAINER = CONTAINER
    a.DOCKER_SCRIPT = HERE/'qwen_l7_long197.py'
    a.QUEUE_EXPIRES, a.WALL_SECONDS, a.LIMIT = QUEUE_EXPIRES, WALL_SECONDS, LIMIT
    a.invocation, a.verify, a.budget = invocation, verify, budget
    a.resources_ready, a.predecessor_complete, a.docker = resources_ready, predecessor_complete, docker


def parent_contract():
    contract = dict(version='accepted-same-seed-prefix-v1', parent=str(PARENT),
        checkpoint=str(CHECKPOINT), parent_sha=PARENT_SHA, start_step=2, target_step=96,
        driver_rng_unavailable_accepted=True,
        files={name: sha256(PARENT/name) for name in prefix_files()})
    verify_contract(contract)
    metrics = a.read(PARENT/'runs/train2/metrics.json')
    audits = [json.loads(x) for x in (PARENT/'runs/train2/checkpoints/sc2_policy_credit_audit.jsonl').read_text().splitlines()]
    seeds = [json.loads(x) for x in (PARENT/'runs/train2/training_seeds.jsonl').read_text().splitlines()]
    if (len(metrics) != 2 or [x['pending_global_step'] for x in audits] != [1,2]
            or any(x['decision'] != 'accept' for x in audits)
            or any(not math.isfinite(x['actor/grad_norm']) or x['actor/grad_norm'] <= 0 for x in metrics)
            or [x['seeds'] for x in seeds] != [[49]*8, [97]*8]):
        raise RuntimeError('Parent PPO/seed evidence mismatch')
    proof = a.read(PARENT/'runs/post/checkpoint_evaluation.json')
    if (proof['checkpoint'] != str(CHECKPOINT) or proof['loaded_global_step'] != 2
            or not proof['checkpoint_load_returned'] or proof['optimizer_updates'] != 0
            or proof['game_seeds'] != a.EVAL_SEEDS):
        raise RuntimeError('Parent checkpoint was not actually evaluated')
    return contract


def prepare():
    if ROOT.exists():
        raise RuntimeError('Fresh exact root required; no overwrite or retry')
    sha = a.cmd(['git','-C',SOURCE,'rev-parse','HEAD'])
    a.clean(SOURCE, sha)
    a.clean(a.ORCH, a.ORCH_SHA)
    contract = parent_contract()
    cfg = copy.deepcopy(a.read(PARENT/'deployment.json'))
    for old in ('prior_failed_root',):
        cfg.pop(old, None)
    cfg.update(runtime_sha=sha, controller_sha=sha, controller_source=str(SOURCE),
        predecessor=str(PARENT), stages=['train96','eval96'], games=[752,8], updates=[94,0],
        training_seeds=[ablation_seeds('same_uniform101',0,i,1,8) for i in range(2,96)],
        start_step=2, target_step=96, wall_seconds=WALL_SECONDS, gpu_hours=384,
        output_limit_bytes=LIMIT, storage_roots=[str(ROOT),str(SOURCE.parent),str(PARENT)],
        queue_expires=QUEUE_EXPIRES, no_long_training=False, successors_authorized=False,
        no_retry=True, run_prefix='qwen-l7same96-197-r1', worker_hook='qwen_l7_long_hook.install',
        resource_check='eight empty GPUs/no compute PIDs, >=600GiB RAM, >=1084GiB NVMe, fsync passed',
        authorization='User approved one Qwen Level7 same-seed step2 to total96, <=48h/384GPUh/1TiB; '
            'then explicitly accepted ledger-restored SC2 counters and unavailable driver RNG/non-bitwise replay; '
            'no short-arm rerun, weights-only restart, retries or successors')
    ROOT.mkdir()
    for name in ('runs','cpu','tmp'):
        (ROOT/name).mkdir()
    a.cmd(['git','clone','--quiet','--shared',SOURCE,ROOT/'runtime'])
    a.cmd(['git','-C',ROOT/'runtime','checkout','--quiet','--detach',sha])
    a.save(ROOT/'resume-contract.json', contract)
    a.save(ROOT/'deployment.json', cfg)


def invocation(cfg, stage, dry=False):
    if stage not in ('train96','eval96'):
        raise ValueError('Undeclared long stage')
    template = 'train2' if stage == 'train96' else 'post'
    args, env, old = BASE_INVOCATION(cfg, template, dry)
    out = ROOT/('cpu' if dry else 'runs')/stage
    args = [item.replace(str(old), str(out)) for item in args]
    # Preserve all inherited policy/action/reward settings; replace only stage
    # controls, resume location and observer stage. No duplicate +Hydra keys.
    settings = {
        '+ray_init.runtime_env.env_vars.SC2_ACCEPTANCE_STAGE': repr(stage),
        'trainer.total_training_steps': '96',
        'trainer.total_epochs': '96' if stage == 'train96' else '1',
        'trainer.save_freq': '8' if stage == 'train96' else '-1',
        'trainer.resume_mode': 'resume_path',
        'trainer.resume_from_path': str(CHECKPOINT if stage == 'train96' else ROOT/'runs/train96/checkpoints/global_step_96'),
    }
    args = [x for x in args if x.split('=',1)[0] not in settings]
    args += [key+'='+value for key,value in settings.items()]
    if stage == 'train96':
        args += ['+trainer.sc2_import_legacy_final=True',
                 f'+trainer.sc2_policy_credit_resume_contract={ROOT}/resume-contract.json']
    env.update(OUTPUT_DIR=str(out), RUN_ID=cfg['run_prefix']+'-'+stage,
        SC2_CHECKPOINT_RESUME=str(stage=='train96'), RAY_TMPDIR='/tmp/ql7-'+stage)
    return args, env, out


def budget(deadline):
    a.measure_budget([ROOT,SOURCE.parent,PARENT],ROOT,LIMIT,deadline,
        '48h/384GPUh ceiling; no extension', '1TiB inclusive new outputs/source and parent ceiling')


def predecessor_complete():
    verify_contract(a.read(ROOT/'resume-contract.json'))
    return True


def resources_ready():
    # Reuse the stricter complete eight-card ownership/RAM check, then enforce
    # the long run's disk headroom (not the short run's 140GiB).
    rows = a.cmd(['nvidia-smi','--query-gpu=index,memory.used,utilization.gpu','--format=csv,noheader,nounits'])
    if len(rows.splitlines()) != 8:
        raise RuntimeError('Expected eight GPUs')
    if any(float(v.strip()) > 0 for row in rows.splitlines() for v in row.split(',')[1:]):
        return False
    if a.cmd(['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader']):
        return False
    mem = dict(line.split(':',1) for line in Path('/proc/meminfo').read_text().splitlines())
    return int(mem['MemAvailable'].split()[0])*1024 >= 600*a.GIB and shutil.disk_usage(ROOT).free >= 1084*a.GIB


def docker(mode):
    args = BASE_DOCKER('execute' if mode == 'execute' else 'cpu')
    args[2:2] = ['-v',f'{PARENT}:{PARENT}:ro',
                 '-v',f'{PARENT.parent}/runtime:{PARENT.parent}/runtime:ro']
    if mode != 'execute':
        model = a.read(ROOT/'deployment.json')['host']['model']
        args[args.index(f'{model}:/assets/qwen:ro')] = f'{CPU_MODEL}:/assets/qwen:ro'
    if mode == 'regressions':
        args[args.index('--name')+1] += '-regressions'
        args[2:2] = ['-v',f'{SPB_METADATA}:/metadata/spb:ro',
            '-e','SC2_TEST_SPB_METADATA_PATH=/metadata/spb', '-e','SC2_TEST_QWEN_METADATA_PATH=/assets/qwen',
            '-e','SC2_TEST_TOKENIZER_PATH=/assets/qwen','-e','OMP_NUM_THREADS=2',
            '-e','TOKENIZERS_PARALLELISM=false']
    args[-1] = mode
    return args


def cpu():
    import torch
    import numpy as np
    from types import SimpleNamespace
    from unittest.mock import patch
    from agent_system.sc2_resume import legacy_environment_state, restore_environment
    from hydra import compose, initialize_config_dir
    from omegaconf import OmegaConf
    from verl.trainer.ppo.sc2_policy_credit import validate_config as credit_config
    from verl.utils.sc2_action_support import validate_config as support_config
    from ray._private.utils import validate_socket_filepath
    sys.path.insert(0,str(a.ORCH/a.REC))
    from seed_ray_paths import socket_path
    cfg = a.read(ROOT/'deployment.json')
    a.clean(SOURCE,cfg['controller_sha'])
    check = sp.run(['sha256sum','-c','configs/system-v1.sha256'],cwd=ROOT/'runtime',text=True,capture_output=True,timeout=30)
    (ROOT/'cpu/source-check.log').write_text(check.stdout+check.stderr)
    if check.returncode:
        raise RuntimeError('Source manifest mismatch')
    # Only small extra-state/data files; never load production model/optimizer
    # shards for a CPU diagnostic. The actual GPU loader must still return.
    ranks = []
    for rank in range(8):
        extra = torch.load(CHECKPOINT/f'actor/extra_state_world_size_8_rank_{rank}.pt',
                           map_location='cpu',weights_only=False)
        if extra['lr_scheduler']['last_epoch'] != 2 or not extra['rng']:
            raise RuntimeError('Missing saved scheduler/rank RNG at step2')
        ranks.append(dict(rank=rank,scheduler_last_epoch=2,rng_keys=sorted(extra['rng'])))
    raw = SimpleNamespace(seed=0,env_num=1,group_n=8,is_train=True,reset_index=0,
        training_rng=np.random.RandomState(0),validation_rng=np.random.RandomState(0))
    manager = SimpleNamespace(envs=raw,memory=None,_terminal_by_env=[],_episode_reset_index=-1,_step_index=0)
    with patch.dict(os.environ,SC2_TRAIN_SEED_PROTOCOL='same_uniform101',SC2_ORIGINAL_GAME_SEEDS='0'):
        state = legacy_environment_state(manager,PARENT/'runs/train2',2)
        restore_environment(manager,state)
    if raw.reset_index != 2 or manager._episode_reset_index != 1:
        raise RuntimeError('Actual parent closed-game ledger does not restore step2')
    a.save(ROOT/'cpu/parent-small-state.json',dict(rank_states=ranks,next_reset_index=raw.reset_index,
        episode_reset_index=manager._episode_reset_index,next_step_index=manager._step_index,
        next_seeds=ablation_seeds('same_uniform101',0,raw.reset_index,1,8),
        driver_rng='unavailable; accepted non-bitwise continuation',cuda_initialized=torch.cuda.is_initialized()))
    # Verify the relocated data and BO are byte-identical to the accepted prefix.
    for name in ('data/train.parquet','data/test.parquet',
        'agent_system/environments/env_package/sc2_online_restored/SC2ArenaDyStrategy/knowledge/BO/replay_observations_Flat128_d4_TvT_Macro_g2_Result.Victory_twobase.json'):
        if sha256(ROOT/'runtime'/name) != sha256(PARENT/'runtime'/name):
            raise RuntimeError('Changed data/BO: '+name)
    for stage in cfg['stages']:
        args,env,out = invocation(cfg,stage,True)
        p = sp.run(args,env=env,cwd=ROOT/'runtime',capture_output=True,text=True,timeout=90)
        (ROOT/'cpu'/f'{stage}.log').write_text(p.stdout+p.stderr)
        if p.returncode:
            raise RuntimeError('Actual dry launcher failed: '+stage)
        command = a.read(out/'effective_config.json')['command']
        with initialize_config_dir(config_dir=str(ROOT/'runtime/verl/trainer/config'),version_base=None):
            c = compose(config_name='ppo_trainer',overrides=command[command.index('verl.trainer.main_ppo')+1:])
        credit_config(c)
        support_config(c)
        if (c.trainer.val_only != (stage=='eval96') or c.trainer.total_training_steps != 96
                or c.trainer.n_gpus_per_node != 8 or c.actor_rollout_ref.actor.optim.lr != 1e-6
                or c.actor_rollout_ref.actor.optim.warmup_style != 'constant'
                or c.actor_rollout_ref.actor.optim.lr_warmup_steps_ratio != 0):
            raise RuntimeError('Unexpected long configuration/scheduler')
        a.save(out/'resolved_config.json',OmegaConf.to_container(c,resolve=True))
        validate_socket_filepath(socket_path(env['RAY_TMPDIR']))
    if torch.cuda.is_initialized():
        raise RuntimeError('CPU validation initialized CUDA')
    a.save(ROOT/'readiness.json',dict(passed=True,cuda_initialized=False,controller_sha=cfg['controller_sha'],
        runtime_sha=cfg['runtime_sha'],actual_entries_and_hydra_configs=True,checked_at=time.time()))


def regressions():
    import unittest
    import torch
    sys.path[:0] = [str(SOURCE/'tests'),str(SOURCE/'scripts')]
    names = ['test_sc2_checkpoint_resume','test_qwen_l7_long197','test_sc2_policy_resume',
        'test_sc2_action_support','test_sc2_policy_credit','test_sc2_task_signal',
        'test_sc2_no_thinking_torch','test_thinking_action_boundary','test_r6_format_reward',
        'test_original_bo_segment','test_original_game_seeds','test_sc2_generation_tokens',
        'test_policy_credit_acceptance197','test_policy_credit_storage197',
        'test_policy_credit_storage_coordination197','test_qwen_seed_acceptance197',
        'test_qwen_seed_acceptance197_r3','test_qwen_seed_acceptance197_r4']
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromNames(names))
    passed = result.wasSuccessful() and not result.skipped and not torch.cuda.is_initialized()
    a.save(ROOT/'regressions.json',dict(passed=passed,tests=result.testsRun,skips=len(result.skipped),
        cuda_initialized=torch.cuda.is_initialized(),runtime_sha=a.read(ROOT/'deployment.json')['runtime_sha'],
        checked_at=time.time()),lock_root=ROOT)
    if not passed:
        raise RuntimeError('Actual CPU regressions failed')


def verify(stage, write=True):
    out = ROOT/'runs'/stage
    result,evidence = a.verify_common(out,stage,752 if stage=='train96' else 8)
    if stage == 'train96':
        if (result['start_step'],result['last_global_step'],result['completed_steps']) != (2,96,94) or not result['checkpoint_complete']:
            raise RuntimeError('Expected exactly 94 new updates to96')
        rows = [json.loads(x) for x in (out/'training_seeds.jsonl').read_text().splitlines()]
        if (len(rows)!=94 or any(row['reset_index']!=i or row['seed_protocol']!='same_uniform101'
                or row['seeds']!=ablation_seeds('same_uniform101',0,i,1,8) for i,row in enumerate(rows,2))):
            raise RuntimeError('Resume seed sequence mismatch')
        resume = a.read(out/'checkpoints/resume_state.json')
        if (resume['from_checkpoint']!=str(CHECKPOINT) or resume['global_step']!=2
                or resume['next_reset_index']!=2 or resume['next_seeds']!=[53]*8
                or not resume['model_optimizer_dataloader_load_returned']
                or resume['source']!='verified legacy ledger; driver RNG unavailable, not bitwise replay'):
            raise RuntimeError('Missing actual complete checkpoint load/ledger restoration')
        audit = [json.loads(x) for x in (out/'checkpoints/sc2_policy_credit_audit.jsonl').read_text().splitlines()]
        metrics = a.read(out/'metrics.json')
        if ([x['pending_global_step'] for x in audit]!=list(range(3,97))
                or any(x['decision']!='accept' for x in audit) or len(metrics)!=94
                or any(not math.isfinite(x['actor/grad_norm']) or x['actor/grad_norm']<=0
                       or x['policy_credit/invalid_advantage_max']>0 for x in metrics)):
            raise RuntimeError('Actual PPO/audit/gradient acceptance failed')
        names = ['data.pt','sc2_state.pt']+[f'actor/{kind}_world_size_8_rank_{r}.pt'
            for kind in ('model','optim','extra_state') for r in range(8)]
        for step in range(8,97,8):
            for name in names:
                if (out/f'checkpoints/global_step_{step}'/name).stat().st_size<=0:
                    raise RuntimeError('Incomplete periodic checkpoint')
        evidence.update(resume=resume,ppo_updates=94,checkpoints=list(range(8,97,8)))
    elif stage == 'eval96':
        proof = a.read(out/'checkpoint_evaluation.json')
        seeds = [json.loads(x)['seeds'] for x in (out/'evaluation_seeds.jsonl').read_text().splitlines()]
        if (result['training_updates']!=0 or not proof['val_only'] or proof['optimizer_updates']!=0
                or proof['loaded_global_step']!=96 or not proof['checkpoint_load_returned']
                or proof['checkpoint']!=str(ROOT/'runs/train96/checkpoints/global_step_96')
                or proof['game_seeds']!=a.EVAL_SEEDS or seeds!=[a.EVAL_SEEDS]):
            raise RuntimeError('Final paired eval/load evidence mismatch')
        for rank in range(8):
            if not paired_rng_matches(a.read(out/f'sampling-rank{rank}.json'),
                                      a.read(PARENT/f'runs/post/sampling-rank{rank}.json'),rank):
                raise RuntimeError('Paired rank sampling RNG differs')
    else:
        raise ValueError('Undeclared verification stage')
    if write:
        a.save(ROOT/f'acceptance-{stage}.json',dict(result=result,evidence=evidence,checked_at=time.time()))


def paired_rng_matches(current, parent, rank):
    keys = ('rank','seed','cpu_rng_sha256','cuda_rng_sha256')
    return (current['rank']==rank and current['seed']==rank
            and all(current[key]==parent[key] for key in keys))  # PID must change across processes.


def queue():
    proof = a.read(ROOT/'regressions.json')
    if not proof['passed'] or proof['skips'] or proof['runtime_sha'] != a.RUNTIME_SHA:
        raise RuntimeError('Full CPU regressions required before queue')
    a.queue()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',choices=['prepare','cpu','regressions','cpu-command','regressions-command','queue','execute'])
    mode = parser.parse_args().mode
    # Regression fixtures exercise the original short engine as well. Do not
    # replace its globals with the long-run callbacks in this test-only process.
    if mode != 'regressions':
        configure()
    if mode.endswith('-command'):
        print(json.dumps(docker(mode.removesuffix('-command'))))
    elif mode=='execute':
        a.execute()
    else:
        globals()[mode]()
