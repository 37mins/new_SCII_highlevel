"""Approved native L8 CP96->192: 784 new games, 12h/96GPUh/384GiB, no retry."""
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

import acceptance197 as a
import host_stage197 as h
import qwen_l7_long197 as previous
import qwen_l8_cuda_probe_v2 as probe
from qwen_l8_cp192_hook import runtime_environment
from agent_system.sc2_policy_resume import (completed_l8_files, checkpoint_names,
    sha256, verify_contract, normalized_protocol)
from agent_system.sc2_seed_protocol import ablation_seeds

ROOT = Path('/var/jfsCache/sc2-qwen-l8same192-197-20260926-r2')
SOURCE_PARENT = Path('/var/jfsCache/sc2-qwen-l8same192-197-source-20260926-r2')
RETAINED_CPU_ROOTS = [Path('/var/jfsCache/sc2-qwen-l8same192-197-20260926-r1'),
    Path('/var/jfsCache/sc2-qwen-l8same192-197-source-20260926-r1')]
PARENT_ROOT = Path('/var/jfsCache/sc2-qwen-l8same96-197-20260926-r2')
PARENT = PARENT_ROOT / 'qwen-same/long'
CHECKPOINT = PARENT / 'runs/train96/checkpoints/global_step_96'
ANCESTORS = [PARENT_ROOT, Path('/var/jfsCache/sc2-qwen-l8same96-197-source-20260926-r2'),
    Path('/var/jfsCache/sc2-qwen-l8same96-197-20260926-r1'),
    Path('/var/jfsCache/sc2-qwen-l8same96-197-source-20260926-r1')]
PARENT_SHA = 'eef0f049bb09b7a51188ae67a6c35436a3bf055f'
PARENT_CONTROLLER = 'db60d075879750cabf30a38c555d1c3aaaf104c1'
PREFIX = ROOT.name
STAGES = ('pre96', 'train192', 'eval192')
SAVED_STEPS = list(range(112, 193, 16))
WALL_SECONDS, LIMIT = 12 * 3600, 384 * a.GIB
AUTHORIZATION = ('Sep26 user explicitly approves own completed L8 CP96 to192, 96new PPO/'
    '768train+8pre+8post natural games; 197 eightGPU serial,12wallh/96GPUh; '
    'separately approves save every16 at112..192,384GiB new output/source cap,448GiB '
    'training admission. After r1 CPU-only harness failure, explicitly approves corrected r2 '
    'single dispatch with all four r1+r2 source/output roots inside384GiB. '
    'No old deletion, old queue edits, automatic retry or successor.')


def configure():
    a.ROOT = a.STORAGE_LOCK_ROOT = ROOT
    a.CONTAINER = PREFIX
    a.DOCKER_SCRIPT = a.HERE / 'qwen_l8_cp192_197.py'
    a.RUNTIME_SHA = (a.read(ROOT/'deployment.json')['runtime_sha'] if (ROOT/'deployment.json').exists()
                     else a.cmd(['git', '-C', a.SOURCE, 'rev-parse', 'HEAD']))


def accounts(deadline):
    return [dict(roots=[*RETAINED_CPU_ROOTS, ROOT, SOURCE_PARENT], receipt_root=ROOT, limit=LIMIT, deadline=deadline)]


def contract_for():
    value = dict(version='accepted-qwen-l8-cp96-to192-v1', parent=str(PARENT),
        checkpoint=str(CHECKPOINT), parent_sha=PARENT_SHA, start_step=96, target_step=192,
        driver_rng_unavailable_accepted=False,
        files={name: sha256(PARENT/name) for name in completed_l8_files()},
        checkpoint_bytes={name: (CHECKPOINT/name).stat().st_size for name in checkpoint_names()})
    verify_contract(value)
    return value


def parent_terminal():
    cfg = a.read(PARENT_ROOT/'deployment.json'); q = a.read(PARENT_ROOT/'queue-state.json')
    if (cfg['runtime_sha'] != PARENT_SHA or cfg['controller_sha'] != PARENT_CONTROLLER
            or q['phase'] != 'completed' or q['exit_code'] != 0
            or q['completed'] != ['qwen-same/short', 'qwen-same/long']):
        raise RuntimeError('Exact accepted L8 parent chain required')
    a.clean(PARENT_ROOT/'runtime', PARENT_SHA)
    a.clean(Path(cfg['controller_source']), PARENT_CONTROLLER)
    proofs = {}
    for stage in ('train96', 'eval96'):
        g = a.read(PARENT/f'host-supervision/{stage}-guardian.json')
        status = json.loads(a.cmd(['docker', 'inspect', '--format',
            '{"id":"{{.Id}}","owner":"{{index .Config.Labels "sc2.acceptance.root"}}","state":{{json .State}}}',
            g['container_id']]))
        if (status['id'] != g['container_id'] or status['owner'] != str(PARENT)
                or g['owner_root'] != str(PARENT) or g['phase'] != 'completed'
                or g['deadline'] != cfg['deadline']):
            raise RuntimeError('Parent container/guardian identity mismatch')
        for s in (status['state'], g['final_state']):
            if s['Running'] or s['Paused'] or s['ExitCode'] != 0 or s['OOMKilled'] or s['Error']:
                raise RuntimeError('Parent container must be exited0')
        proofs[stage] = dict(container_id=status['id'], owner=str(PARENT), exited0=True)
    return proofs


def prepare():
    if ROOT.exists() or a.SOURCE != SOURCE_PARENT/'code':
        raise RuntimeError('Fresh exact root/source required; no overwrite/retry')
    sha = a.cmd(['git', '-C', a.SOURCE, 'rev-parse', 'HEAD'])
    a.clean(a.SOURCE, sha); a.clean(a.ORCH, a.ORCH_SHA)
    terminal = parent_terminal(); contract = contract_for()
    # Re-run the frozen parent's final stage verifier once at launch, read-only.
    old_source = Path(a.read(PARENT_ROOT/'deployment.json')['controller_source'])
    code = (f'import sys;sys.path[:0]=[{str(old_source/a.HERE.relative_to(a.SOURCE))!r},{str(old_source)!r}];'
        'import qwen_l8same_continue197 as m;m.configure();m.f.select(1);'
        "[m.m.verify(s,write=False) for s in ('train96','eval96')]")
    sp.run([sys.executable, '-B', '-c', code], check=True, timeout=240)
    ROOT.mkdir()
    for name in ('runs', 'cpu', 'tmp', 'tmp/task-home', 'tmp/cache', 'tmp/cuda-cache'):
        (ROOT/name).mkdir()
    sp.run(['git', 'clone', '--quiet', '--no-local', str(a.SOURCE), str(ROOT/'runtime')], check=True, timeout=120)
    a.cmd(['git', '-C', ROOT/'runtime', 'checkout', '--quiet', '--detach', sha])
    cfg = copy.deepcopy(a.read(PARENT/'deployment.json'))
    cfg.update(runtime_sha=sha, controller_sha=sha, controller_source=str(a.SOURCE),
        orchestration_sha=a.ORCH_SHA, stages=STAGES, games=[8, 768, 8], updates=[0, 96, 0],
        start_step=96, target_step=192, saved_steps=SAVED_STEPS, run_prefix=PREFIX,
        worker_hook='qwen_l8_cp192_hook.install', predecessor=str(PARENT),
        wall_seconds=WALL_SECONDS, gpu_hours=96, output_limit_bytes=LIMIT,
        first_dispatch_by=time.time()+4*3600, no_retry=True, successors_authorized=False,
        training_seeds=[ablation_seeds('same_uniform101', 0, i, 1, 8) for i in range(96,192)],
        storage_roots=[str(p) for p in accounts(0)[0]['roots']], train_admission_free_gib=448,
        evaluation_admission_free_gib=128, new_games=784, new_updates=96,
        authorization=AUTHORIZATION, parent_terminal=terminal,
        limitation='Additional online PPO steps, not96 dataset epochs; reused8 evaluation seeds; no causal learning claim')
    for key in ('original_start', 'fixed_deadline', 'retained_prefix', 'prior_failed_root'):
        cfg.pop(key, None)
    cfg['queue_expires'] = cfg['first_dispatch_by']
    a.save(ROOT/'deployment.json', cfg)
    a.save(ROOT/'resume-contract.json', contract)


def invocation(cfg, stage, dry=False):
    if stage not in STAGES or cfg['difficulty'] != 'CheatVision' or cfg['model_kind'] != 'qwen':
        raise ValueError('Only authorized Qwen L8 stages')
    training = stage == 'train192'
    args, env, base = a.invocation(cfg, 'train2' if training else 'post', dry)
    out = ROOT/('cpu' if dry else 'runs')/stage
    args = [x.replace(str(base), str(out)) for x in args]
    settings = {'+ray_init.runtime_env.env_vars.SC2_ACCEPTANCE_STAGE': repr(stage),
        'trainer.total_training_steps':'192', 'trainer.total_epochs':'192' if training else '1',
        'trainer.save_freq':'16' if training else '-1', 'trainer.resume_mode':'resume_path',
        'trainer.resume_from_path':str(ROOT/'runs/train192/checkpoints/global_step_192' if stage=='eval192' else CHECKPOINT)}
    args = [x for x in args if x.split('=', 1)[0] not in settings]
    args += [k+'='+v for k,v in settings.items()]
    args += ["+ray_init.runtime_env.env_vars.SC2_L8_RENDEZVOUS_LOW_PORT='1'"]
    if training:
        args += ['+trainer.sc2_import_legacy_final=False',
                 f'+trainer.sc2_policy_credit_resume_contract={ROOT}/resume-contract.json']
    env.update(OUTPUT_DIR=str(out), RUN_ID=PREFIX+'-'+stage,
               SC2_CHECKPOINT_RESUME=str(training), RAY_TMPDIR='/tmp/c192-'+stage)
    return args, env, out


def docker(mode, stage=None):
    gpu = mode in ('stage', 'gpu-preflight')
    args = a.docker('execute' if gpu else 'cpu')
    args[2:2] = ['--read-only', '--log-driver', 'none', '-e', 'HOME=/tmp/task-home',
        '-e', 'XDG_CACHE_HOME=/tmp/cache', '-e', 'CUDA_CACHE_PATH=/tmp/cuda-cache', '-e', 'TMPDIR=/tmp']
    for path in ANCESTORS:
        args[2:2] = ['-v', f'{path}:{path}:ro']
    if not gpu:
        cfg = a.read(ROOT/'deployment.json')
        args[args.index(f'{cfg["host"]["model"]}:/assets/qwen:ro')] = f'{previous.CPU_MODEL}:/assets/qwen:ro'
        args[2:2] = ['-v', f'{previous.SPB_METADATA}:/metadata/spb:ro',
            '-e', 'SC2_TEST_SPB_METADATA_PATH=/metadata/spb', '-e', 'SC2_TEST_QWEN_METADATA_PATH=/assets/qwen',
            '-e', 'SC2_TEST_TOKENIZER_PATH=/assets/qwen', '-e', 'OMP_NUM_THREADS=2',
            '-e', 'TOKENIZERS_PARALLELISM=false']
        if mode == 'cpu-hook': args[args.index('--memory')+1] = '16g'
    writable = [tuple(args[i+1].split(':')[:2]) for i,x in enumerate(args[:-1])
                if x == '-v' and args[i+1].split(':')[-1] != 'ro']
    if writable != [(str(ROOT), str(ROOT)), (str(ROOT/'tmp'), '/tmp')]:
        raise RuntimeError('Unexpected writable mount')
    if mode in ('cpu-hook', 'gpu-preflight'):
        if stage not in STAGES: raise ValueError('Exact probe stage required')
        ev = a.read(ROOT/f'cpu/{stage}/resolved_config.json')['ray_init']['runtime_env']['env_vars']
        for i,x in enumerate(args):
            if x.startswith('PYTHONPATH='): args[i] = 'PYTHONPATH='+ev['PYTHONPATH']
    args[args.index('--name')+1] = PREFIX+'-'+mode+('-'+stage if stage else '')
    args[-1:] = [mode]+([stage] if stage else [])
    if gpu:
        if mode == 'stage' and stage not in STAGES: raise ValueError('Unknown stage')
        args[1] = 'create'
    return args


def small_state():
    import numpy as np
    import random
    import torch
    from types import SimpleNamespace
    from unittest.mock import patch
    from agent_system.sc2_resume import restore_environment
    verify_contract(a.read(ROOT/'resume-contract.json'))
    def small(name):
        path = CHECKPOINT/name
        if not 0 < path.stat().st_size < 1024**2: raise ValueError('Small native state required')
        return torch.load(path, map_location='cpu', weights_only=False)
    state = small('sc2_state.pt')
    if state['global_step'] != 96 or state['empty_policy_batches']: raise ValueError('Closed CP96 required')
    py, nr, tr = state['driver_rng']
    random.Random().setstate(py); np.random.RandomState().set_state(nr); torch.Generator().set_state(tr)
    for label in ('train_env', 'val_env'):
        saved = state[label]
        raw = SimpleNamespace(**{k:saved[k] for k in ('seed','env_num','group_n','is_train')},
            reset_index=0, training_rng=np.random.RandomState(0), validation_rng=np.random.RandomState(0))
        manager = SimpleNamespace(envs=raw, memory=None)
        with patch.dict(os.environ, SC2_TRAIN_SEED_PROTOCOL='same_uniform101'):
            restore_environment(manager, saved)
        if label == 'train_env' and (raw.reset_index, raw.seed, raw.group_n, raw.env_num) != (96,0,8,1):
            raise ValueError('Native environment position differs')
    ranks = []
    for rank in range(8):
        extra = small(f'actor/extra_state_world_size_8_rank_{rank}.pt'); rng = extra['rng']
        if extra['lr_scheduler']['last_epoch'] != 96: raise ValueError('Scheduler must continue from96')
        for key in ('cpu','cuda'):
            if not isinstance(rng[key],torch.Tensor) or rng[key].numel() == 0: raise ValueError('Missing rank RNG')
        torch.Generator().set_state(rng['cpu']); random.Random().setstate(rng['random'])
        np.random.RandomState().set_state(rng['numpy'])
        ranks.append(dict(rank=rank, scheduler_epoch=96, rng_keys=sorted(rng)))
    if not small('data.pt') or torch.cuda.is_initialized(): raise ValueError('Dataloader or noCUDA gate failed')
    return dict(passed=True, global_step=96, next_reset_index=96, native_driver_rng=True,
        next_seeds=ablation_seeds('same_uniform101',0,96,1,8), ranks=ranks, cuda_initialized=False,
        actual_gpu_load_not_yet_claimed=True)


def cpu():
    import torch
    from hydra import compose, initialize_config_dir
    from omegaconf import OmegaConf
    from verl.trainer.ppo.sc2_policy_credit import validate_config as credit_config
    from verl.utils.sc2_action_support import validate_config as support_config
    from ray._private.utils import validate_socket_filepath
    sys.path.insert(0, str(a.ORCH/a.REC))
    from seed_ray_paths import socket_path
    cfg = a.read(ROOT/'deployment.json')
    a.clean(a.SOURCE,cfg['runtime_sha']); a.clean(ROOT/'runtime',cfg['runtime_sha'])
    check = sp.run(['sha256sum','-c','configs/system-v1.sha256'],cwd=ROOT/'runtime',capture_output=True,text=True,timeout=30)
    (ROOT/'cpu/source-check.log').write_text(check.stdout+check.stderr)
    if check.returncode: raise RuntimeError('Source manifest failed')
    a.save(ROOT/'parent-readiness.json',small_state())
    for name in ('data/train.parquet','data/test.parquet',
        'agent_system/environments/env_package/sc2_online_restored/SC2ArenaDyStrategy/knowledge/BO/replay_observations_Flat128_d4_TvT_Macro_g2_Result.Victory_twobase.json'):
        if sha256(ROOT/'runtime'/name) != sha256(PARENT_ROOT/'runtime'/name): raise RuntimeError('Data/BO changed')
    for stage in STAGES:
        args,env,out = invocation(cfg,stage,True)
        proc = sp.run(args,env=env,cwd=ROOT/'runtime',capture_output=True,text=True,timeout=90)
        (ROOT/'cpu'/f'{stage}.log').write_text(proc.stdout+proc.stderr)
        if proc.returncode: raise RuntimeError('Actual dry launcher failed: '+stage)
        command = a.read(out/'effective_config.json')['command']
        with initialize_config_dir(config_dir=str(ROOT/'runtime/verl/trainer/config'),version_base=None):
            c = compose(config_name='ppo_trainer',overrides=command[command.index('verl.trainer.main_ppo')+1:])
        credit_config(c); support_config(c)
        if (c.trainer.val_only != (stage != 'train192') or c.trainer.total_training_steps != 192
                or c.trainer.save_freq != (16 if stage=='train192' else -1)
                or c.trainer.n_gpus_per_node != 8 or c.env.rollout.n != 8
                or c.data.max_response_length != 192 or c.actor_rollout_ref.actor.optim.lr != 1e-6
                or c.actor_rollout_ref.actor.optim.warmup_style != 'constant'
                or c.actor_rollout_ref.actor.optim.lr_warmup_steps_ratio != 0):
            raise RuntimeError('Unexpected actual resolved configuration')
        a.save(out/'resolved_config.json',OmegaConf.to_container(c,resolve=True))
        runtime_environment(out/'resolved_config.json','/tmp/probe-ray')
        validate_socket_filepath(socket_path(env['RAY_TMPDIR']))
    if torch.cuda.is_initialized(): raise RuntimeError('CPU initialized CUDA')
    a.save(ROOT/'readiness.json',dict(passed=True,runtime_sha=cfg['runtime_sha'],cuda_initialized=False,
        actual_parent_verified=True,actual_entries_and_hydra_configs=True,checked_at=time.time()))


def regressions(host_only=False):
    # Do not relocate old controllers' PARTS just to choose a receipt location:
    # their regression fixtures intentionally exercise both original parts.
    sys.path[:0] = [str(a.SOURCE/'tests'), str(a.SOURCE/'scripts')]
    if host_only:
        if Path('/.dockerenv').exists(): raise RuntimeError('Host tests require the actual host')
        names = ['test_l7_host_continuation197','test_host_stage197','test_storage_quiescent197',
                 'test_policy_credit_storage197','test_policy_credit_storage_coordination197']
    else:
        import torch
        names = ['test_metric_precision','test_l7_precision_continuation197','test_l7_followup197',
            'test_sc2_checkpoint_resume','test_qwen_l7_long197','test_sc2_policy_resume',
            'test_sc2_action_support','test_sc2_policy_credit','test_sc2_task_signal',
            'test_sc2_no_thinking_torch','test_thinking_action_boundary','test_r6_format_reward',
            'test_original_bo_segment','test_original_game_seeds','test_sc2_generation_tokens',
            'test_policy_credit_acceptance197','test_policy_credit_storage197','test_policy_credit_storage_coordination197',
            'test_qwen_seed_acceptance197','test_qwen_seed_acceptance197_r3','test_qwen_seed_acceptance197_r4',
            'test_sc2_reset_startup','test_qwen_random_cp8_197','test_spb_l7_random197',
            'test_qwen_l8_cp192_197','test_qwen_l8same_fresh197','test_qwen_l8_probe_env',
            'test_qwen_l8_remainder3_197','test_qwen_l8same_continue197']
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromNames(names))
    cuda = False if host_only else torch.cuda.is_initialized()
    proof = dict(passed=result.wasSuccessful() and not result.skipped and not cuda,
        tests=result.testsRun,skips=len(result.skipped),cuda_initialized=cuda,host_only=host_only,
        cp192_tests=0 if host_only else unittest.defaultTestLoader.loadTestsFromName('test_qwen_l8_cp192_197').countTestCases(),
        runtime_sha=a.read(ROOT/'deployment.json')['runtime_sha'],checked_at=time.time())
    a.save(ROOT/('host-regressions.json' if host_only else 'regressions.json'),proof,lock_root=ROOT)
    if not proof['passed']: raise RuntimeError('Actual zero-skip regression gates required')


def check_cpu():
    cfg = a.read(ROOT/'deployment.json')
    a.clean(a.SOURCE,cfg['controller_sha']); a.clean(ROOT/'runtime',cfg['runtime_sha']); a.clean(a.ORCH,a.ORCH_SHA)
    for name in ('readiness.json','regressions.json','host-regressions.json'):
        p = a.read(ROOT/name)
        if not p['passed'] or p.get('skips',0) or p.get('cuda_initialized',False) or p['runtime_sha'] != cfg['runtime_sha']:
            raise RuntimeError('Actual zero-skip CPU/source gates required')
    if a.read(ROOT/'regressions.json').get('cp192_tests',0) <= 0: raise RuntimeError('New tests required')
    for stage in STAGES:
        p=a.read(ROOT/f'cpu/hook-{stage}/cpu-hook-preflight.json')
        if (not p['passed'] or p['worker']['cuda_initialized'] or p['worker']['cuda_device_count']
                or p['model_loaded'] or p['natural_games'] or p['optimizer_updates']
                or p['runtime_environment']['resolved_config_sha256'] != sha256(ROOT/f'cpu/{stage}/resolved_config.json')):
            raise RuntimeError('Full-environment actual CPU hook required')


def verify_probe(stage):
    p = a.read(ROOT/'gpu-preflight/gpu-preflight.json')
    if (stage != 'gpu-preflight' or not p['passed'] or len(p['ranks'])!=8
            or len({r['cuda_uuid'] for r in p['ranks']})!=8 or p['nccl_sums']!=[28.0]*8
            or p['model_loaded'] or p['natural_games'] or p['optimizer_updates']
            or p['runtime_environment']['resolved_config_sha256'] != sha256(ROOT/'cpu/train192/resolved_config.json')):
        raise RuntimeError('Distinct eight-GPU/NCCL proof required')


def verify(stage, write=True):
    if stage not in STAGES: raise ValueError('Undeclared verification')
    out=ROOT/'runs'/stage; training=stage=='train192'
    result,evidence=a.verify_common(out,stage,768 if training else 8)
    if any(a.read(out/n).get('metrics_precision')!='binary64-v1' for n in ('manifest.json','result.json')):
        raise RuntimeError('Full-precision metrics required')
    if training:
        if (result['start_step'],result['last_global_step'],result['completed_steps'])!=(96,192,96) or not result['checkpoint_complete']:
            raise RuntimeError('Expected96 actual returned new updates')
        metrics=a.read(out/'metrics.json')
        audits=[json.loads(x) for x in (out/'checkpoints/sc2_policy_credit_audit.jsonl').read_text().splitlines()]
        seeds=[json.loads(x) for x in (out/'training_seeds.jsonl').read_text().splitlines()]
        if ([x['step'] for x in metrics]!=list(range(97,193))
                or [x['pending_global_step'] for x in audits]!=list(range(97,193))
                or any(x['decision']!='accept' or x['real_answers']<=0 or x['real_answers']!=x['valid_answers'] for x in audits)
                or any(not math.isfinite(x[k]) or x[k]<=0 for x in metrics for k in ('actor/grad_norm','timing_s/update_actor'))
                or any(not math.isfinite(x['policy_credit/invalid_advantage_max']) or x['policy_credit/invalid_advantage_max']>0 for x in metrics)):
            raise RuntimeError('Returned finite positive PPO/credit evidence required')
        if len(seeds)!=96 or any(x['reset_index']!=i or x['base_seed']!=0 or x['seed_protocol']!='same_uniform101'
                or x['seeds']!=ablation_seeds('same_uniform101',0,i,1,8) for i,x in enumerate(seeds,96)):
            raise RuntimeError('Exact native seed continuation required')
        resume=a.read(out/'checkpoints/resume_state.json')
        if (resume['from_checkpoint']!=str(CHECKPOINT) or resume['global_step']!=96 or resume['next_reset_index']!=96
                or resume['source']!='checkpoint' or not resume['model_optimizer_dataloader_load_returned']
                or resume['next_seeds']!=ablation_seeds('same_uniform101',0,96,1,8)):
            raise RuntimeError('Actual native CP96 restore missing')
        if sorted(int(p.name.split('_')[-1]) for p in (out/'checkpoints').glob('global_step_*')) != SAVED_STEPS:
            raise RuntimeError('Exact approved checkpoint cadence required')
        for step in SAVED_STEPS:
            for name in checkpoint_names():
                rel=f'checkpoints/global_step_{step}/'+name
                if ((out/rel).stat().st_size<=0 or (step == 192
                        and (out/rel).stat().st_size!=result['checkpoint_files'][rel]['bytes'])):
                    raise RuntimeError('Complete checkpoint inventory required')
        evidence.update(resume=resume,new_ppo_updates=96,saved_steps=SAVED_STEPS)
    else:
        proof=a.read(out/'checkpoint_evaluation.json'); step=96 if stage=='pre96' else 192
        cp=CHECKPOINT if stage=='pre96' else ROOT/'runs/train192/checkpoints/global_step_192'
        seeds=[json.loads(x)['seeds'] for x in (out/'evaluation_seeds.jsonl').read_text().splitlines()]
        if (result['training_updates']!=0 or proof['optimizer_updates']!=0 or not proof['val_only']
                or not proof['checkpoint_load_returned'] or proof['loaded_global_step']!=step
                or proof['checkpoint']!=str(cp) or proof['game_seeds']!=a.EVAL_SEEDS or seeds!=[a.EVAL_SEEDS]):
            raise RuntimeError('Actual paired checkpoint evaluation required')
        reference=PARENT/'runs/eval96' if stage=='pre96' else ROOT/'runs/pre96'
        for rank in range(8):
            if not previous.paired_rng_matches(a.read(out/f'sampling-rank{rank}.json'),a.read(reference/f'sampling-rank{rank}.json'),rank):
                raise RuntimeError('Paired rank CPU/CUDA RNG mismatch')
    replays=sorted((out/'sc2-logs').rglob('*.SC2Replay'))
    if (len(replays)!=(768 if training else 8) or len({p.resolve() for p in replays})!=len(replays)
            or any('/Flat128_CheatVision_Air/' not in str(p) or p.stat().st_size<=0
                   or not p.resolve().is_relative_to(out.resolve()) for p in replays)):
        raise RuntimeError('L8 natural replay inventory mismatch')
    if not training and result['replays']!={str(p.relative_to(out)):sha256(p) for p in replays}:
        raise RuntimeError('Evaluation replay digests differ')
    if write:a.save(ROOT/f'acceptance-{stage}.json',dict(result=result,evidence=evidence,checked_at=time.time()))


def resources_ready(stage):
    rows=a.cmd(['nvidia-smi','--query-gpu=index,memory.used,utilization.gpu','--format=csv,noheader,nounits']).splitlines()
    if len(rows)!=8 or sorted(int(r.split(',')[0]) for r in rows)!=list(range(8)):raise RuntimeError('Eight GPUs required')
    if any(float(v.strip())>0 for r in rows for v in r.split(',')[1:]):return False
    if a.cmd(['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader']):return False
    mem=dict(line.split(':',1) for line in Path('/proc/meminfo').read_text().splitlines())
    return int(mem['MemAvailable'].split()[0])*1024>=600*a.GIB and shutil.disk_usage(ROOT).free>=disk_gate(stage)*a.GIB


def disk_gate(stage):
    if stage not in (*STAGES,'first','gpu-preflight'):raise ValueError('Unknown admission')
    return 128 if stage in ('pre96','eval192') else 448


def admit(stage,deadline):
    import l7_followup197_r4 as host
    while True:
        if time.time()>=deadline-45:raise TimeoutError('Fixed admission deadline reached')
        h.sample(accounts(deadline),ROOT);host.writers_clear(accounts(deadline)[0]['roots'])
        if resources_ready(stage):break
        a.save(ROOT/'admission-wait.json',dict(stage=stage,deadline=deadline,checked_at=time.time()))
        time.sleep(min(30,deadline-45-time.time()))
    path=ROOT/('fsync-'+stage)
    with path.open('xb') as s:s.write(b'cp192\n');s.flush();os.fsync(s.fileno())
    if path.read_bytes()!=b'cp192\n':raise RuntimeError('Fsync readback failed')
    a.save(ROOT/f'admission-{stage}.json',dict(passed=True,checked_at=time.time(),deadline=deadline,
        eight_idle_gpus=True,ram_gib_min=600,nvme_gib_min=disk_gate(stage),fsync=True))


def queue():
    check_cpu();parent_terminal();verify_contract(a.read(ROOT/'resume-contract.json'))
    with (ROOT/'queue.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (ROOT/'queue-state.json').exists() or (ROOT/'dispatch.json').exists():raise RuntimeError('Already queued; no retry')
        state=dict(phase='waiting-admission',completed=[],new_games=784,new_updates=96)
        try:
            a.save(ROOT/'queue-state.json',state)
            admit('first',a.read(ROOT/'deployment.json')['first_dispatch_by'])
            start=time.time();deadline=start+WALL_SECONDS
            a.save(ROOT/'dispatch.json',dict(start=start,deadline=deadline,gpu_hours=96,
                new_games=784,new_updates=96,includes_gpu_preflight=True))
            state.update(phase='gpu-preflight',deadline=deadline);a.save(ROOT/'queue-state.json',state)
            h.run_stages(['gpu-preflight'],lambda _:docker('gpu-preflight','train192'),verify_probe,
                accounts(deadline),ROOT,ROOT/'gpu-preflight-supervision',ROOT,deadline,
                admit=lambda _:admit('gpu-preflight',deadline))
            state.update(phase='running-unverified');a.save(ROOT/'queue-state.json',state)
            result=h.run_stages(STAGES,lambda s:docker('stage',s),verify,accounts(deadline),ROOT,
                ROOT/'host-supervision',ROOT,deadline,admit=lambda s:admit(s,deadline))
            a.save(ROOT/'state.json',result);a.save(ROOT/'queue-state.json',result)
        except BaseException as exc:
            state.update(phase='failed',error_type=type(exc).__name__,error=str(exc))
            a.save(ROOT/'state.json',state);a.save(ROOT/'queue-state.json',state)
            raise


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode',choices=['prepare','cpu','cpu-command','regressions','host-regressions',
        'regressions-command','cpu-hook','cpu-hook-command','gpu-preflight','queue','stage'])
    p.add_argument('stage',nargs='?',choices=STAGES);arg=p.parse_args()
    if arg.mode in ('regressions','host-regressions'):
        regressions(arg.mode=='host-regressions');return
    configure()
    if arg.mode.endswith('-command'):print(json.dumps(docker(arg.mode.removesuffix('-command'),arg.stage)))
    elif arg.mode in ('prepare','cpu','queue'):globals()[arg.mode]()
    elif arg.mode in ('cpu-hook','gpu-preflight'):
        if arg.stage not in STAGES:raise ValueError('Exact stage required')
        config=ROOT/f'cpu/{arg.stage}/resolved_config.json'
        if arg.mode=='cpu-hook':probe.check_hook_cpu(ROOT/f'cpu/hook-{arg.stage}',Path('/tmp/hook-'+arg.stage),config,environment_loader=runtime_environment)
        elif arg.stage=='train192':probe.run(ROOT/'gpu-preflight',Path('/tmp/probe-ray'),config,environment_loader=runtime_environment)
        else:raise ValueError('Training environment preflight only')
    else:
        cfg=a.read(ROOT/'deployment.json');a.clean(a.SOURCE,cfg['runtime_sha']);a.clean(ROOT/'runtime',cfg['runtime_sha'])
        args,env,_=invocation(cfg,arg.stage)
        fd=os.open(ROOT/(arg.stage+'-entry.log'),os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
        os.dup2(fd,1);os.dup2(fd,2);os.close(fd)
        os.chdir(ROOT/'runtime');os.execvpe(args[0],args,env)


if __name__=='__main__':main()
