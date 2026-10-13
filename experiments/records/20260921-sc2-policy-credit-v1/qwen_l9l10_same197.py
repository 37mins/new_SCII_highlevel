"""Approved L9 then L10 fresh Qwen same96; 1584 games/192 PPO, no retry."""
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
import qwen_l8_cuda_probe_v2 as probe
import l7_matrix256197 as receipts
from agent_system.sc2_policy_resume import checkpoint_names, prefix_files, sha256, verify_contract
from agent_system.sc2_seed_protocol import ablation_seeds
from qwen_l8_common64_plan import STAGES as PRIOR_STAGES, stage_spec as prior_spec
from qwen_l9l10_training_probe import runtime_environment

a, f, h = fresh.a, fresh.f, fresh.h
BASE_SELECT = f.select
ROOTS = {n: Path(f'/var/jfsCache/sc2-qwen-l{n}same96-197-20260927-r1') for n in (9, 10)}
SOURCE_PARENT = Path('/var/jfsCache/sc2-qwen-l9l10same96-197-source-20260927-r1')
PARTS = ('qwen-same/short', 'qwen-same/long')
DIFFICULTIES = {9: 'CheatMoney', 10: 'CheatInsane'}
BASE = Path('/var/jfsCache/sc2-qwen-l8same96-197-20260926-r2/qwen-same/short')
PREDECESSOR = Path('/var/jfsCache/sc2-qwen-l8-common192-197-20260927-r1')
PREDECESSOR_SHA = 'e01594ecd3ea7b43d2296b371fd340f9d575ab3a'
PREDECESSOR_DEADLINE = 1790495189.9456112
ARM_SECONDS, SUITE_SECONDS, ARM_LIMIT, SUITE_LIMIT = 12*3600, 24*3600, 256*a.GIB, 512*a.GIB
CPU_PROBES = ((0, 'pre'), (0, 'train2'), (1, 'train96'))
LEVEL = 9
AUTHORIZATION = ('Sep27 user explicitly approved L9 then L10 independent original Qwen same96, '
    '792games/96PPO each; 197 eightGPU serial after accepted L8common64; each12h/96GPUh/256GiB, '
    'combined24h/192GPUh/512GiB; CP2/32/64/96 only; no deletion/retry/other successor')


def configure(level):
    global LEVEL
    if level not in DIFFICULTIES: raise ValueError('Only approved L9/L10')
    LEVEL = level
    fresh.ROOT, fresh.PARTS, fresh.PREFIX = ROOTS[level], PARTS, ROOTS[level].name+'-'
    fresh.configure()
    f.select = select
    f.invocation, f.verify = invocation, verify
    f.DOCKER_SCRIPT = a.HERE/'qwen_l9l10_same197.py'


def select(index):
    cfg = BASE_SELECT(index)
    a.STORAGE_LOCK_ROOT = ROOTS[9]
    return cfg


def accounts(deadline):
    # Shared source is conservatively charged to BOTH arms, but once to suite.
    return [dict(roots=[root, SOURCE_PARENT], receipt_root=root/'arm-storage',
                 limit=ARM_LIMIT, deadline=deadline) for root in ROOTS.values()] + [
        dict(roots=[*ROOTS.values(), SOURCE_PARENT], receipt_root=ROOTS[9]/'suite-storage',
             limit=SUITE_LIMIT, deadline=deadline)]


def prepare():
    if any(p.exists() for p in ROOTS.values()) or a.SOURCE != SOURCE_PARENT/'code':
        raise RuntimeError('Fresh exact roots required; no overwrite/retry')
    sha = a.cmd(['git', '-C', a.SOURCE, 'rev-parse', 'HEAD'])
    a.clean(a.SOURCE, sha); a.clean(a.ORCH, a.ORCH_SHA)
    base = a.read(BASE/'deployment.json')
    if (base['model_kind'], base['seed_protocol'], base['model_mount'], base['difficulty']) != (
            'qwen', 'same_uniform101', '/assets/qwen', 'CheatVision'):
        raise RuntimeError('Exact original-Qwen L8 template required')
    first_by = time.time()+24*3600
    for level, root in ROOTS.items():
        root.mkdir(); a.STORAGE_LOCK_ROOT = root
        (root/'arm-storage').mkdir()
        if level == 9: (root/'suite-storage').mkdir()
        sp.run(['git', 'clone', '--quiet', '--no-local', str(a.SOURCE), str(root/'runtime')], check=True, timeout=120)
        a.cmd(['git', '-C', root/'runtime', 'checkout', '--quiet', '--detach', sha])
        for index, part in enumerate(PARTS):
            owner = root/part; owner.mkdir(parents=True)
            for name in ('runs', 'cpu', 'tmp', 'tmp/task-home', 'tmp/cache', 'tmp/cuda-cache'): (owner/name).mkdir()
            (owner/'runtime').symlink_to(root/'runtime', target_is_directory=True)
            cfg = copy.deepcopy(base)
            for key in ('prior_failed_root', 'retained_prefix', 'fixed_deadline', 'original_start', 'deadline'):
                cfg.pop(key, None)
            cfg.update(runtime_sha=sha, controller_sha=sha, controller_source=str(a.SOURCE),
                orchestration_sha=a.ORCH_SHA, difficulty=DIFFICULTIES[level], level=f'L{level}',
                training_seeds=[ablation_seeds('same_uniform101', 0, i, 1, 8) for i in range(96)],
                stages=['pre', 'train2', 'post'] if index == 0 else ['train96', 'eval96'],
                games=[8,16,8] if index == 0 else [752,8], updates=[0,2,0] if index == 0 else [94,0],
                run_prefix=root.name+('-short' if index == 0 else '-long'), worker_hook='l7_followup_hook.install',
                wall_seconds=ARM_SECONDS, gpu_hours=96, output_limit_bytes=ARM_LIMIT, saved_steps=[2,32,64,96],
                first_dispatch_by=first_by, queue_expires=first_by, no_retry=True, no_long_training=False,
                predecessor=str(root/PARTS[0]) if index else str(PREDECESSOR if level == 9 else ROOTS[9]),
                successors_authorized=(level == 9 or index == 0), authorization=AUTHORIZATION,
                storage_supervision='host-guardian-v1', host_stage_entry_log=True,
                container_rootfs_read_only=True, startup_concurrency=1, original_weights=True,
                limitation='Independent released weights; sparse checkpoints, same seed protocol; no learning claim')
            a.save(owner/'deployment.json', cfg, lock_root=root)
        a.save(root/'deployment.json', dict(runtime_sha=sha, controller_sha=sha, controller_source=str(a.SOURCE),
            orchestration_sha=a.ORCH_SHA, level=level, difficulty=DIFFICULTIES[level], parts=PARTS,
            first_dispatch_by=first_by, wall_seconds=ARM_SECONDS, gpu_hours=96, output_limit_bytes=ARM_LIMIT,
            suite_wall_seconds=SUITE_SECONDS, suite_gpu_hours=192, suite_output_limit_bytes=SUITE_LIMIT,
            storage_roots=[str(p) for p in [*ROOTS.values(), SOURCE_PARENT]],
            arm_storage_roots=[str(root), str(SOURCE_PARENT)], new_games=792, new_updates=96,
            suite_new_games=1584, suite_new_updates=192, no_retry=True, original_weights=True,
            saved_steps=[2,32,64,96], gpu_preflight_required=True, cpu_hook_probes=CPU_PROBES,
            first_free_gib=576, train_free_gib=320, eval_free_gib=128, successors_authorized=level==9,
            authorization=AUTHORIZATION), lock_root=root)
    h.sample(accounts(first_by), ROOTS[9])


def invocation(cfg, stage, dry=False):
    if cfg['difficulty'] != DIFFICULTIES[LEVEL] or cfg['model_kind'] != 'qwen':
        raise ValueError('Wrong level/model for this arm')
    args, env, out = fresh.BASE_INVOCATION(cfg, stage, dry)
    if stage == 'train96':
        args = [x for x in args if not x.startswith('trainer.save_freq=')]+['trainer.save_freq=32']
    args += ["+ray_init.runtime_env.env_vars.SC2_L8_RENDEZVOUS_LOW_PORT='1'"]
    env['RAY_TMPDIR'] = f'/tmp/l{LEVEL}-'+stage
    return args, env, out


def docker(mode, index, stage=None):
    gpu = mode in ('stage', 'gpu-preflight')
    args = fresh.docker('stage' if gpu else ('cpu' if mode=='cpu-hook' else mode), index, stage if gpu else None)
    cfg = a.read(a.ROOT/'deployment.json')
    if mode in ('cpu-hook', 'gpu-preflight'):
        if stage not in cfg['stages']: raise ValueError('Undeclared probe stage')
        args[args.index('--name')+1] = ROOTS[LEVEL].name+('-short-' if index==0 else '-long-')+mode+'-'+stage
        ev = a.read(a.ROOT/f'cpu/{stage}/resolved_config.json')['ray_init']['runtime_env']['env_vars']
        for i, value in enumerate(args):
            if value.startswith('PYTHONPATH='): args[i] = 'PYTHONPATH='+ev['PYTHONPATH']
        if not gpu: args[args.index('--memory')+1] = '16g'
    # Fresh adapter's final argv is [script, mode, index, optional stage].
    tail = 3 if gpu else 2
    args[-tail:] = [mode, str(LEVEL), str(index)] + ([stage] if stage is not None else [])
    if LEVEL == 10:
        old = f'{ROOTS[10]}/.storage.lock:{ROOTS[10]}/.storage.lock'
        args[args.index(old)] = f'{ROOTS[9]}/.storage.lock:{ROOTS[9]}/.storage.lock'
        args[2:2] = ['-v', f'{ROOTS[9]}:{ROOTS[9]}:ro']
    return args


def cpu(index):
    fresh.cpu(index)
    # Resolved environment and actual enum are checked without GPU/model/game.
    from sc2.data import Difficulty
    if Difficulty[DIFFICULTIES[LEVEL]].value != LEVEL: raise RuntimeError('Installed SC2 difficulty mapping changed')
    for stage in a.read(a.ROOT/'deployment.json')['stages']:
        path = a.ROOT/f'cpu/{stage}/resolved_config.json'
        runtime_environment(path, '/tmp/probe-ray')
        cfg = a.read(path)
        if stage == 'train96' and cfg['trainer']['save_freq'] != 32: raise RuntimeError('Sparse CP cadence required')


def regressions(host_only=False):
    # No configure() before testing historical controllers; preserve their fixtures.
    sys.path[:0] = [str(a.SOURCE/'tests'), str(a.SOURCE/'scripts')]
    if host_only:
        if Path('/.dockerenv').exists(): raise RuntimeError('Actual host required')
        names = ['test_l7_host_continuation197','test_host_stage197','test_storage_quiescent197',
                 'test_policy_credit_storage197','test_policy_credit_storage_coordination197']
    else:
        import torch
        names = ['test_qwen_l9l10_same197','test_qwen_l8same_fresh197','test_qwen_l7same_fresh197',
            'test_l7_followup197','test_sc2_policy_resume','test_sc2_checkpoint_resume',
            'test_qwen_l8_probe_env','test_qwen_l8_remainder3_197','test_qwen_l8_common64_197',
            'test_metric_precision','test_sc2_action_support','test_sc2_policy_credit',
            'test_sc2_no_thinking_torch','test_sc2_reset_startup','test_sc2_generation_tokens',
            'test_policy_credit_acceptance197']
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromNames(names))
    cuda = False if host_only else torch.cuda.is_initialized()
    proof = dict(passed=result.wasSuccessful() and not result.skipped and not cuda, tests=result.testsRun,
        skips=len(result.skipped), cuda_initialized=cuda, host_only=host_only,
        runtime_sha=a.read(ROOTS[9]/'deployment.json')['runtime_sha'], checked_at=time.time())
    a.save(ROOTS[9]/('host-regressions.json' if host_only else PARTS[0]+'/regressions.json'),proof,lock_root=ROOTS[9])
    if not proof['passed']: raise RuntimeError('Zero-skip CPU regressions required')


def check_cpu():
    cfg = a.read(ROOTS[9]/'deployment.json'); sha = cfg['runtime_sha']
    a.clean(a.SOURCE, sha); a.clean(a.ORCH, a.ORCH_SHA)
    for path in (ROOTS[9]/'host-regressions.json', ROOTS[9]/PARTS[0]/'regressions.json'):
        p = a.read(path)
        if not p['passed'] or p['skips'] or p['cuda_initialized'] or p['runtime_sha'] != sha:
            raise RuntimeError('Actual matching zero-skip regressions required')
    for root in ROOTS.values():
        a.clean(root/'runtime', sha)
        for part in PARTS:
            p = a.read(root/part/'readiness.json')
            if not p['passed'] or p['cuda_initialized'] or p['runtime_sha'] != sha:
                raise RuntimeError('All ten launcher/source/Hydra gates required')
        for index, stage in CPU_PROBES:
            owner = root/PARTS[index]; p = a.read(owner/f'cpu/hook-{stage}/cpu-hook-preflight.json')
            if (not p['passed'] or p['worker']['cuda_initialized'] or p['worker']['cuda_device_count']
                    or p['model_loaded'] or p['natural_games'] or p['optimizer_updates']
                    or p['runtime_environment']['resolved_config_sha256'] != sha256(owner/f'cpu/{stage}/resolved_config.json')):
                raise RuntimeError('Actual full-environment no-GPU hook required')


def verify_probe(stage):
    owner = ROOTS[LEVEL]/PARTS[0]; p = a.read(owner/'gpu-preflight/gpu-preflight.json')
    if (stage != 'gpu-preflight' or not p['passed'] or len(p['ranks']) != 8
            or len({r['cuda_uuid'] for r in p['ranks']}) != 8 or p['nccl_sums'] != [28.0]*8
            or p['model_loaded'] or p['natural_games'] or p['optimizer_updates']
            or p['runtime_environment']['resolved_config_sha256'] != sha256(owner/'cpu/train2/resolved_config.json')):
        raise RuntimeError('Eight distinct GPU/NCCL proof required')


def replay_evidence(out, stage):
    expected = {'pre':8,'train2':16,'post':8,'train96':752,'eval96':8}[stage]
    files = sorted((out/'sc2-logs').rglob('*.SC2Replay'))
    names = [str(p.relative_to(out)) for p in files]
    if (len(files) != expected or len({p.resolve() for p in files}) != expected
            or any(f'/Flat128_{DIFFICULTIES[LEVEL]}_Air/' not in n for n in names)
            or any(p.stat().st_size<=0 or not p.resolve().is_relative_to(out.resolve()) for p in files)):
        raise RuntimeError('Exact natural replay count/difficulty required')
    if stage in ('pre','post','eval96') and a.read(out/'result.json')['replays'] != {n:sha256(p) for n,p in zip(names,files)}:
        raise RuntimeError('Evaluation replay digests differ')


def checkpoint_inventory(out, result, steps):
    """Recorder covers the final CP only; inspect every declared CP explicitly.

    Never invent result entries for intermediate CPs. Large shards must match
    the corresponding final shard size; small state files get fresh digests.
    Payload/native-state inspection is a separate CPU gate in continuation.
    """
    names = checkpoint_names()
    if sorted(p.name for p in (out/'checkpoints').glob('global_step_*')) != sorted(f'global_step_{s}' for s in steps):
        raise RuntimeError('Unexpected checkpoint cadence')
    final = {f'checkpoints/global_step_{steps[-1]}/'+name for name in names}
    all_keys = {f'checkpoints/global_step_{step}/'+name for step in steps for name in names}
    recorded = result['checkpoint_files']
    if not final <= recorded.keys() or not recorded.keys() <= all_keys:
        raise RuntimeError('Final checkpoint inventory missing or unexpected')
    inventory = {}
    for step in steps:
        for name in names:
            rel = f'checkpoints/global_step_{step}/'+name
            path = out/rel; size = path.stat().st_size
            if not path.is_file() or size <= 0:
                raise RuntimeError('Incomplete native checkpoint')
            if rel in recorded and recorded[rel]['bytes'] != size:
                raise RuntimeError('Checkpoint size differs from result')
            large = name.startswith(('actor/model_', 'actor/optim_'))
            if large and recorded[f'checkpoints/global_step_{steps[-1]}/'+name]['bytes'] != size:
                raise RuntimeError('Checkpoint shard size differs from final shard')
            if not large and size > 1024**2:
                raise RuntimeError('Expected small checkpoint state')
            inventory[rel] = dict(bytes=size, sha256=None if large else sha256(path),
                                  source='result-and-stat' if rel in recorded else 'independent-stat')
    return inventory


def verify(stage, write=True):
    out = a.ROOT/'runs'/stage
    result, evidence = a.verify_common(out, stage, 752 if stage=='train96' else (16 if stage=='train2' else 8))
    if any(a.read(out/n).get('metrics_precision')!='binary64-v1' for n in ('manifest.json','result.json')):
        raise RuntimeError('Full precision required')
    if f.INDEX == 0:
        fresh.verify(stage, write=False)
    elif stage == 'train96':
        if (result['start_step'],result['last_global_step'],result['completed_steps']) != (2,96,94) or not result['checkpoint_complete']:
            raise RuntimeError('Exactly94 native continuation updates required')
        resume = a.read(out/'checkpoints/resume_state.json')
        if (resume['from_checkpoint'] != str(ROOTS[LEVEL]/PARTS[0]/'runs/train2/checkpoints/global_step_2')
                or resume['global_step']!=2 or resume['next_reset_index']!=2 or resume['source']!='checkpoint'
                or resume['next_seeds']!=ablation_seeds('same_uniform101',0,2,1,8)
                or not resume['model_optimizer_dataloader_load_returned']):
            raise RuntimeError('Own CP2 native actual load evidence required')
        evidence['resume'] = resume
    elif stage == 'eval96':
        p = a.read(out/'checkpoint_evaluation.json')
        seeds = [json.loads(x)['seeds'] for x in (out/'evaluation_seeds.jsonl').read_text().splitlines()]
        if (result['training_updates']!=0 or not p['val_only'] or p['optimizer_updates']!=0
                or p['loaded_global_step']!=96 or not p['checkpoint_load_returned']
                or p['checkpoint']!=str(a.ROOT/'runs/train96/checkpoints/global_step_96')
                or p['game_seeds']!=a.EVAL_SEEDS or seeds!=[a.EVAL_SEEDS]):
            raise RuntimeError('Own CP96 paired zero-update evaluation required')
        for rank in range(8):
            if not f.previous.paired_rng_matches(a.read(out/f'sampling-rank{rank}.json'),
                    a.read(ROOTS[LEVEL]/PARTS[0]/f'runs/post/sampling-rank{rank}.json'),rank):
                raise RuntimeError('Paired CPU/CUDA RNG mismatch')
    else: raise ValueError('Undeclared stage')
    if stage in ('train2','train96'):
        lo, hi = (1,2) if stage=='train2' else (3,96)
        metrics = a.read(out/'metrics.json')
        audits = [json.loads(x) for x in (out/'checkpoints/sc2_policy_credit_audit.jsonl').read_text().splitlines()]
        f.verify_updates(audits, metrics, lo, hi)
        if ([r['step'] for r in metrics]!=list(range(lo,hi+1))
                or any(not math.isfinite(r[k]) or r[k]<=0 for r in metrics for k in ('actor/grad_norm','timing_s/update_actor'))
                or any(not math.isfinite(r['policy_credit/invalid_advantage_max']) or r['policy_credit/invalid_advantage_max']>0 for r in metrics)
                or any(r['real_answers']<=0 or r['real_answers']!=r['valid_answers'] for r in audits)):
            raise RuntimeError('Actual finite positive PPO required')
        rows = [json.loads(x) for x in (out/'training_seeds.jsonl').read_text().splitlines()]
        if len(rows)!=hi-lo+1 or any(r['reset_index']!=i or r['base_seed']!=0
                or r['seed_protocol']!='same_uniform101' or r['seeds']!=ablation_seeds('same_uniform101',0,i,1,8)
                for i,r in enumerate(rows,lo-1)): raise RuntimeError('Exact same-seed ledger required')
        outcomes = [json.loads(x) for x in (out/'episode_outcomes.jsonl').read_text().splitlines()]
        if (len(outcomes)!=(hi-lo+1)*8 or {(r['reset_index'],r['env_index']) for r in outcomes} !=
                {(i,e) for i in range(lo-1,hi) for e in range(8)}
                or any(not r['terminated'] or r['truncated'] for r in outcomes)):
            raise RuntimeError('Complete unique natural training outcomes required')
        steps = [2] if stage=='train2' else [32,64,96]
        evidence.update(ppo_updates=hi-lo+1,checkpoints=steps,
                        checkpoint_inventory=checkpoint_inventory(out,result,steps))
    replay_evidence(out,stage)
    if write: a.save(a.ROOT/f'acceptance-{stage}.json',dict(result=result,evidence=evidence,checked_at=time.time()))


def contract_for():
    parent = ROOTS[LEVEL]/PARTS[0]
    contract = dict(version=f'accepted-qwen-l{LEVEL}-same-full-state-prefix-v1',parent=str(parent),
        checkpoint=str(parent/'runs/train2/checkpoints/global_step_2'),
        parent_sha=a.read(parent/'deployment.json')['runtime_sha'],start_step=2,target_step=96,
        driver_rng_unavailable_accepted=False,files={n:sha256(parent/n) for n in prefix_files()})
    verify_contract(contract)
    return contract


def predecessor_complete():
    queue = receipts.small(PREDECESSOR/'queue-state.json')
    host = receipts.small(PREDECESSOR/'host-supervision/state.json')
    if any(x['phase']=='failed' for x in (queue,host)): raise RuntimeError('L8 predecessor failed; stop successors')
    if queue['phase']!='completed': return False
    cfg = receipts.small(PREDECESSOR/'deployment.json')
    if cfg['runtime_sha']!=PREDECESSOR_SHA or cfg['controller_sha']!=PREDECESSOR_SHA:
        raise RuntimeError('Wrong L8 predecessor provenance')
    a.clean(PREDECESSOR/'runtime',PREDECESSOR_SHA); a.clean(Path(cfg['controller_source']),PREDECESSOR_SHA)
    receipts.validate_terminal(PREDECESSOR,list(PRIOR_STAGES),PREDECESSOR_DEADLINE,queue=True)
    batch_rng = {}
    for stage in PRIOR_STAGES:
        spec = prior_spec(stage); out = PREDECESSOR/'runs'/stage
        accepted = receipts.small(PREDECESSOR/f'acceptance-{stage}.json'); r = receipts.small(out/'result.json')
        manifest = receipts.small(out/'manifest.json'); load = receipts.small(out/'checkpoint_evaluation.json')
        if (r!=receipts.small(out/'.done') or r!=accepted['result'] or r['status']!='completed'
                or r['process_exit_code']!=0 or not r['metrics_finite'] or r['training_updates']!=0
                or r['episode_outcomes']['natural_games']!=8 or r['episode_outcomes']['truncated']
                or r['metrics_precision']!='binary64-v1' or manifest['metrics_precision']!='binary64-v1'
                or manifest['dirty'] or manifest['world_size']!=8 or manifest['source_commit']!=PREDECESSOR_SHA
                or accepted['evidence']['consumed_answers']<=0
                or accepted['evidence']['consumed_answers']!=accepted['evidence']['valid_consumed_answers']
                or accepted['difficulty']!='CheatVision' or accepted['seeds']!=spec['seeds']
                or load['loaded_global_step']!=spec['expected_step'] or load['optimizer_updates']!=0
                or load['checkpoint_load_returned']!=bool(spec['expected_step']) or not load['val_only']
                or load['checkpoint']!=(str(spec['checkpoint']) if spec['checkpoint'] else None)
                or load['game_seeds']!=spec['seeds']):
            raise RuntimeError('L8 actual stage acceptance mismatch')
        if spec['batch'] in batch_rng and batch_rng[spec['batch']]!=accepted['rng']:
            raise RuntimeError('L8 paired RNG mismatch')
        batch_rng[spec['batch']] = accepted['rng']
        receipts.terminal_container(PREDECESSOR,stage,PREDECESSOR_DEADLINE)
    return True


def resources_ready(stage):
    rows = a.cmd(['nvidia-smi','--query-gpu=index,memory.used,utilization.gpu','--format=csv,noheader,nounits']).splitlines()
    if len(rows)!=8 or sorted(int(r.split(',')[0]) for r in rows)!=list(range(8)): raise RuntimeError('Exact eight GPUs required')
    if any(float(v.strip())>0 for r in rows for v in r.split(',')[1:]): return False
    if a.cmd(['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader']): return False
    mem = dict(r.split(':',1) for r in Path('/proc/meminfo').read_text().splitlines())
    return int(mem['MemAvailable'].split()[0])*1024>=600*a.GIB and shutil.disk_usage(ROOTS[LEVEL]).free>=disk_gate(stage)*a.GIB


def disk_gate(stage):
    return 576 if stage=='first' else (128 if stage in ('pre','post','eval96') else 320)


def admit(index,stage,deadline,*,receipt_name=None):
    owner = ROOTS[LEVEL]/PARTS[index]
    receipt_name = stage if receipt_name is None else receipt_name
    while True:
        if time.time()>=deadline-45: raise TimeoutError('Fixed admission/deadline expired')
        h.sample(accounts(deadline),ROOTS[9])
        fresh.queue_impl.host.writers_clear([*ROOTS.values(),SOURCE_PARENT])
        if resources_ready(stage): break
        a.save(owner/'admission-wait.json',dict(stage=stage,deadline=deadline,checked_at=time.time()),lock_root=ROOTS[9])
        time.sleep(min(30,deadline-45-time.time()))
    path = owner/('fsync-'+receipt_name)
    with path.open('xb') as stream: stream.write(b'l9l10\n'); stream.flush(); os.fsync(stream.fileno())
    if path.read_bytes()!=b'l9l10\n': raise RuntimeError('Fsync/readback failed')
    a.save(owner/f'admission-{receipt_name}.json',dict(passed=True,stage=stage,receipt_name=receipt_name,deadline=deadline,checked_at=time.time(),
        eight_idle_gpus=True,ram_gib_min=600,nvme_gib_min=disk_gate(stage),fsync=True),lock_root=ROOTS[9])


def queue():
    check_cpu(); master = ROOTS[9]
    with (master/'queue.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (master/'queue-state.json').exists() or any((r/'dispatch.json').exists() for r in ROOTS.values()):
            raise RuntimeError('Already queued/dispatched; no retry')
        state = dict(phase='waiting-predecessor',completed=[],new_games=1584,new_updates=192)
        try:
            first_by = a.read(master/'deployment.json')['first_dispatch_by']
            a.save(master/'queue-state.json',state,lock_root=master)
            while not predecessor_complete():
                if time.time()>=first_by-45: raise TimeoutError('Predecessor admission expired')
                h.sample(accounts(first_by),master); time.sleep(30)
            a.save(master/'predecessor-acceptance.json',dict(passed=True,root=str(PREDECESSOR),
                runtime_sha=PREDECESSOR_SHA,method='frozen completed host acceptance plus small terminal/load/RNG receipts',
                full_logs_or_weights_reread=False,checked_at=time.time()),lock_root=master)
            total_deadline = None
            for level,root in ROOTS.items():
                configure(level)
                admit(0,'first' if level==9 else 'arm',first_by if total_deadline is None else total_deadline)
                start = time.time()
                if total_deadline is None:
                    total_deadline = start+SUITE_SECONDS
                    a.save(master/'suite-dispatch.json',dict(start=start,deadline=total_deadline,gpu_hours=192,
                        new_games=1584,new_updates=192,includes_gpu_preflight=True),lock_root=master)
                deadline = min(start+ARM_SECONDS,total_deadline)
                a.save(root/'dispatch.json',dict(start=start,deadline=deadline,suite_deadline=total_deadline,
                    gpu_hours=96,new_games=792,new_updates=96,includes_gpu_preflight=True),lock_root=master)
                state.update(phase='gpu-preflight',level=level,deadline=total_deadline,arm_deadline=deadline)
                a.save(master/'queue-state.json',state,lock_root=master)
                owner = root/PARTS[0]
                h.run_stages(['gpu-preflight'],lambda _:docker('gpu-preflight',0,'train2'),verify_probe,
                    accounts(deadline),owner,owner/'gpu-preflight-supervision',master,deadline,
                    admit=lambda _:admit(0,'gpu-preflight',deadline))
                for index,part in enumerate(PARTS):
                    cfg = f.select(index)
                    if index==1:
                        a.save(a.ROOT/'resume-contract.json',contract_for(),lock_root=master)
                        with (a.ROOT/'parent-cpu.log').open('x') as log:
                            sp.run(docker('parent-cpu',1),stdout=log,stderr=sp.STDOUT,check=True,
                                   timeout=min(600,deadline-45-time.time()))
                        if not a.read(a.ROOT/'parent-readiness.json')['actual_parent_verified']:
                            raise RuntimeError('Own complete nativeCP2 not verified')
                    a.save(a.ROOT/'dispatch.json',dict(start=start,deadline=deadline,clock_shared_with_short=True),lock_root=master)
                    state.update(phase='running-unverified',part=part)
                    a.save(master/'queue-state.json',state,lock_root=master)
                    terminal = h.run_stages(cfg['stages'],lambda s:docker('stage',index,s),verify,
                        accounts(deadline),a.ROOT,a.ROOT/'host-supervision',master,deadline,
                        admit=lambda s:admit(index,s,deadline))
                    a.save(a.ROOT/'state.json',terminal,lock_root=master)
                    state['completed'].append(f'L{level}/'+part)
                    a.save(master/'queue-state.json',state,lock_root=master)
                a.save(root/'arm-state.json',dict(phase='completed',exit_code=0,completed=PARTS,deadline=deadline,
                    learning_validated=False,finished_at=time.time()),lock_root=master)
            state.update(phase='completed',exit_code=0,learning_validated=False,finished_at=time.time())
            a.save(master/'queue-state.json',state,lock_root=master)
        except BaseException as exc:
            state.update(phase='failed',error_type=type(exc).__name__,error=str(exc),finished_at=time.time())
            a.save(master/'queue-state.json',state,lock_root=master); raise


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode',choices=['prepare','queue','cpu','cpu-command','regressions','host-regressions',
        'regressions-command','parent-cpu','stage','cpu-hook','cpu-hook-command','gpu-preflight'])
    p.add_argument('level',type=int,nargs='?',choices=(9,10)); p.add_argument('index',type=int,nargs='?',choices=(0,1))
    p.add_argument('stage',nargs='?'); arg = p.parse_args()
    if arg.mode in ('regressions','host-regressions'): regressions(arg.mode=='host-regressions'); return
    if arg.mode in ('prepare','queue'): globals()[arg.mode](); return
    if arg.level is None or arg.index is None: p.error('Exact level and short/long index required')
    configure(arg.level)
    if arg.mode.endswith('-command'): print(json.dumps(docker(arg.mode.removesuffix('-command'),arg.index,arg.stage)))
    elif arg.mode=='cpu': cpu(arg.index)
    elif arg.mode=='parent-cpu': f.parent_cpu(arg.index)
    elif arg.mode in ('cpu-hook','gpu-preflight'):
        cfg = f.select(arg.index)
        if arg.stage not in cfg['stages']: raise ValueError('Undeclared probe')
        config = a.ROOT/f'cpu/{arg.stage}/resolved_config.json'
        if arg.mode=='cpu-hook':
            probe.check_hook_cpu(a.ROOT/f'cpu/hook-{arg.stage}',Path('/tmp/hook-'+arg.stage),config,environment_loader=runtime_environment)
        elif arg.index==0 and arg.stage=='train2':
            probe.run(a.ROOT/'gpu-preflight',Path('/tmp/probe-ray'),config,environment_loader=runtime_environment)
        else: raise ValueError('One GPU probe per arm only')
    else:
        cfg = f.select(arg.index); a.clean(a.SOURCE,cfg['controller_sha']); a.clean(a.ROOT/'runtime',cfg['runtime_sha'])
        args,env,_ = invocation(cfg,arg.stage)
        fd = os.open(a.ROOT/(arg.stage+'-entry.log'),os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
        os.dup2(fd,1);os.dup2(fd,2);os.close(fd);os.chdir(a.ROOT/'runtime');os.execvpe(args[0],args,env)


if __name__=='__main__': main()
