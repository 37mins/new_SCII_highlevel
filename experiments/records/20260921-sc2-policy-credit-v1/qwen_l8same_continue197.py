"""Explicit Sep26 r2 continuation: retain pre/train2, run post then steps3..96."""
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

import qwen_l8same_fresh197 as m
from agent_system.sc2_policy_resume import checkpoint_names, sha256

a, f, h = m.a, m.f, m.h
OLD = Path('/var/jfsCache/sc2-qwen-l8same96-197-20260926-r1')
OLD_SOURCE = Path('/var/jfsCache/sc2-qwen-l8same96-197-source-20260926-r1')
ROOT = Path('/var/jfsCache/sc2-qwen-l8same96-197-20260926-r2')
SOURCE_PARENT = Path('/var/jfsCache/sc2-qwen-l8same96-197-source-20260926-r2')
RUNTIME_SHA = 'eef0f049bb09b7a51188ae67a6c35436a3bf055f'
START, DEADLINE = 1790358122.7417548, 1790530922.7417548
PARTS = m.PARTS
PREFIX = 'sc2-qwen-l8same96-197-20260926-r2-'
CPU_PROBES = ((0, 'post'), (1, 'train96'), (1, 'eval96'))
AUTHORIZATION = ('Sep26 user explicitly permits corrected acceptance and controlled continuation '
    'after complete CP2 verification, retaining 24 games/2 PPO; only remaining768 games/94 PPO; '
    'original deadline and384GPUh/1TiB inclusive r1+r2; no deletion, replay, or automatic retry.')


def configure():
    m.ROOT, m.SOURCE_PARENT, m.PREFIX = ROOT, SOURCE_PARENT, PREFIX
    m.configure()
    m.accounts = accounts
    f.DOCKER_SCRIPT = a.HERE / 'qwen_l8same_continue197.py'


def accounts(deadline):
    if deadline != DEADLINE:
        raise ValueError('Original deadline must not change')
    return [dict(roots=[OLD, OLD_SOURCE, ROOT, SOURCE_PARENT], receipt_root=ROOT,
                 limit=m.LIMIT, deadline=DEADLINE)]


def old_terminal():
    dispatch = a.read(OLD / 'dispatch.json')
    q = a.read(OLD / 'queue-state.json')
    owner = OLD / PARTS[0]
    state = a.read(owner / 'host-supervision/state.json')
    if (dispatch['start'] != START or dispatch['deadline'] != DEADLINE
            or q['phase'] != 'failed' or q['error_type'] != 'KeyError' or q['error'] != "'replays'"
            or state['phase'] != 'failed' or state['stage'] != 'train2'
            or state['completed'] != ['pre'] or state['error'] != "'replays'"
            or (owner / 'runs/post').exists() or (OLD / PARTS[1] / 'dispatch.json').exists()):
        raise RuntimeError('Only exact stopped r1 pre/train2 may be retained')
    a.clean(OLD / 'runtime', RUNTIME_SHA); a.clean(OLD_SOURCE / 'code', RUNTIME_SHA)
    proofs = {}
    for stage in ('pre', 'train2'):
        cid = a.read(owner / f'host-supervision/{stage}-guardian.json')['container_id']
        status = json.loads(a.cmd(['docker', 'inspect', '--format',
            '{"id":"{{.Id}}","owner":"{{index .Config.Labels "sc2.acceptance.root"}}","state":{{json .State}}}', cid]))
        g = a.read(owner / f'host-supervision/{stage}-guardian.json')
        for s in (status['state'], g['final_state']):
            if s['Running'] or s['Paused'] or s['ExitCode'] != 0 or s['OOMKilled'] or s['Error']:
                raise RuntimeError('Retained stage must have exited0')
        if (status['id'] != cid or status['owner'] != str(owner) or g['owner_root'] != str(owner)
                or g['deadline'] != DEADLINE or g['phase'] != 'completed'):
            raise RuntimeError('Retained owner/guardian mismatch')
        proofs[stage] = dict(container_id=cid, owner=str(owner), exited0=True)
    return proofs


def prepare():
    if ROOT.exists() or a.SOURCE != SOURCE_PARENT / 'code':
        raise RuntimeError('Fresh exact continuation source/output required')
    if time.time() >= DEADLINE - 45:
        raise TimeoutError('Original budget expired')
    terminal = old_terminal()
    commit = a.cmd(['git', '-C', a.SOURCE, 'rev-parse', 'HEAD'])
    a.clean(a.SOURCE, commit); a.clean(a.ORCH, a.ORCH_SHA)
    ROOT.mkdir(); a.STORAGE_LOCK_ROOT = ROOT
    # No model/runtime changes: only the corrected controller is a new SHA.
    (ROOT / 'runtime').symlink_to(OLD / 'runtime', target_is_directory=True)
    for index, part in enumerate(PARTS):
        owner = ROOT / part; owner.mkdir(parents=True)
        for name in ('runs', 'cpu', 'tmp', 'tmp/task-home', 'tmp/cache', 'tmp/cuda-cache'):
            (owner / name).mkdir()
        (owner / 'runtime').symlink_to(ROOT / 'runtime', target_is_directory=True)
        cfg = copy.deepcopy(a.read(OLD / part / 'deployment.json'))
        cfg.update(controller_sha=commit, controller_source=str(a.SOURCE),
            runtime_sha=RUNTIME_SHA, stages=['post'] if index == 0 else ['train96', 'eval96'],
            games=[8] if index == 0 else [752, 8], updates=[0] if index == 0 else [94, 0],
            run_prefix=PREFIX + ('short' if index == 0 else 'long'),
            predecessor=str(OLD if index == 0 else ROOT / PARTS[0]),
            authorization=AUTHORIZATION, first_dispatch_by=DEADLINE, queue_expires=DEADLINE,
            original_start=START, fixed_deadline=DEADLINE, retained_prefix=str(OLD / PARTS[0]))
        a.save(owner / 'deployment.json', cfg, lock_root=ROOT)
    short = ROOT / PARTS[0]
    for stage in ('pre', 'train2'):
        (short / 'runs' / stage).symlink_to(OLD / PARTS[0] / 'runs' / stage, target_is_directory=True)
        (short / 'cpu' / stage).symlink_to(OLD / PARTS[0] / 'cpu' / stage, target_is_directory=True)
    a.save(ROOT / 'deployment.json', dict(runtime_sha=RUNTIME_SHA, controller_sha=commit,
        controller_source=str(a.SOURCE), parts=PARTS, original_start=START, deadline=DEADLINE,
        wall_seconds=48*3600, gpu_hours=384, output_limit_bytes=m.LIMIT,
        storage_roots=[str(p) for p in accounts(DEADLINE)[0]['roots']],
        retained_games=24, retained_updates=2, new_games=768, new_updates=94,
        no_retry=True, authorization=AUTHORIZATION, terminal=terminal), lock_root=ROOT)


def docker(mode, index, stage=None):
    if mode == 'prefix-cpu':
        args = m.docker('cpu', 0)
        args[args.index('--name') + 1] = PREFIX + 'short-prefix-cpu'
        args[-2:] = [mode, '0']
    else:
        args = m.docker(mode, index, stage)
    # Symlinked retained evidence and the unchanged runtime remain read-only.
    args[2:2] = ['-v', f'{OLD}:{OLD}:ro', '-v', f'{OLD_SOURCE}:{OLD_SOURCE}:ro']
    return args


def verify_retained(write=False):
    terminal = old_terminal()
    f.select(0)
    for stage in ('pre', 'train2'):
        m.verify(stage, write=write)
    run = a.ROOT / 'runs/train2'; result = a.read(run / 'result.json')
    for name in checkpoint_names():
        rel = 'checkpoints/global_step_2/' + name
        if (run / rel).stat().st_size <= 0 or (run / rel).stat().st_size != result['checkpoint_files'][rel]['bytes']:
            raise RuntimeError('CP2 inventory differs from completed result')
    paths = ['queue-state.json', 'dispatch.json', PARTS[0] + '/host-supervision/state.json']
    proof = dict(passed=True, retained_games=24, retained_updates=2, terminal=terminal,
        old_terminal_hashes={name: sha256(OLD / name) for name in paths},
        verifier_sha=a.read(ROOT / 'deployment.json')['controller_sha'], checked_at=time.time())
    if write:
        a.save(ROOT / 'retained-acceptance.json', proof, lock_root=ROOT)
    return proof


def prefix_cpu():
    """Inspect only small native state, never load large model/optimizer shards."""
    import numpy as np
    import random
    import torch
    from types import SimpleNamespace
    from unittest.mock import patch
    from agent_system.sc2_resume import restore_environment
    f.select(0)
    cp = a.ROOT / 'runs/train2/checkpoints/global_step_2'
    def small(name):
        path = cp / name
        if not 0 < path.stat().st_size < 1024**2:
            raise ValueError('Expected small CP2 state file')
        return torch.load(path, map_location='cpu', weights_only=False)
    state = small('sc2_state.pt')
    if state['global_step'] != 2 or state['empty_policy_batches']:
        raise ValueError('Closed complete global2 required')
    py, nr, tr = state['driver_rng']
    random.Random().setstate(py); np.random.RandomState().set_state(nr)
    torch.Generator().set_state(tr)
    for label in ('train_env', 'val_env'):
        saved = state[label]
        raw = SimpleNamespace(**{k: saved[k] for k in ('seed', 'env_num', 'group_n', 'is_train')},
            reset_index=0, training_rng=np.random.RandomState(0), validation_rng=np.random.RandomState(0))
        manager = SimpleNamespace(envs=raw, memory=None)
        with patch.dict(os.environ, SC2_TRAIN_SEED_PROTOCOL='same_uniform101'):
            restore_environment(manager, saved)
        if label == 'train_env' and (raw.reset_index != 2 or raw.seed != 0 or raw.group_n != 8 or raw.env_num != 1):
            raise ValueError('Native CP2 environment position mismatch')
    ranks = []
    for rank in range(8):
        extra = small(f'actor/extra_state_world_size_8_rank_{rank}.pt')
        rng = extra['rng']
        if extra['lr_scheduler']['last_epoch'] != 2 or not rng:
            raise ValueError('CP2 scheduler/rank RNG missing')
        # Native checkpoint format checked against the frozen checkpoint manager.
        for name in ('cpu', 'cuda'):
            if name not in rng or not isinstance(rng[name], torch.Tensor) or rng[name].numel() == 0:
                raise ValueError('CP2 CPU/CUDA RNG missing')
        torch.Generator().set_state(rng['cpu'])
        random.Random().setstate(rng['random']); np.random.RandomState().set_state(rng['numpy'])
        ranks.append(dict(rank=rank, scheduler_epoch=2, rng_keys=sorted(rng)))
    data = small('data.pt')
    if not data or torch.cuda.is_initialized():
        raise ValueError('Dataloader state missing or CPU check initialized CUDA')
    a.save(a.ROOT / 'prefix-readiness.json', dict(passed=True, cuda_initialized=False,
        global_step=2, next_reset_index=2, next_seeds=m.ablation_seeds('same_uniform101', 0, 2, 1, 8),
        ranks=ranks, native_driver_rng=True, dataloader_state_present=True,
        actual_gpu_load_not_yet_claimed=True, checked_at=time.time()), lock_root=ROOT)


def regressions(host_only=False):
    m.regressions(host_only)
    if not host_only:
        result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromName(
            'test_qwen_l8same_continue197'))
        if not result.wasSuccessful() or result.skipped:
            raise RuntimeError('Continuation tests failed')
        path = ROOT / PARTS[0] / 'regressions.json'; proof = a.read(path)
        proof['tests'] += result.testsRun; proof['continuation_tests'] = result.testsRun
        a.save(path, proof, lock_root=ROOT)


def check_cpu():
    m.fresh.BASE_CHECK_CPU()
    proof = a.read(ROOT / PARTS[0] / 'regressions.json')
    if proof.get('continuation_tests', 0) <= 0:
        raise RuntimeError('Continuation regressions required')
    prefix = a.read(ROOT / PARTS[0] / 'prefix-readiness.json')
    if not prefix['passed'] or prefix['cuda_initialized'] or not prefix['native_driver_rng']:
        raise RuntimeError('Native CP2 CPU proof required before post')
    for index, stage in CPU_PROBES:
        owner = ROOT / PARTS[index]; p = a.read(owner / f'cpu/hook-{stage}/cpu-hook-preflight.json')
        if (not p['passed'] or p['worker']['cuda_initialized'] or p['worker']['cuda_device_count']
                or p['model_loaded'] or p['natural_games'] or p['optimizer_updates']
                or p['runtime_environment']['resolved_config_sha256'] != sha256(owner / f'cpu/{stage}/resolved_config.json')):
            raise RuntimeError('Actual complete-environment CPU hooks required')


def verify_probe(stage):
    p = a.read(ROOT / PARTS[0] / 'gpu-preflight/gpu-preflight.json')
    if (stage != 'gpu-preflight' or not p['passed'] or len(p['ranks']) != 8
            or len({r['cuda_uuid'] for r in p['ranks']}) != 8 or p['nccl_sums'] != [28.0]*8
            or p['natural_games'] or p['optimizer_updates'] or p['model_loaded']
            or p['runtime_environment']['resolved_config_sha256'] != sha256(ROOT / PARTS[0] / 'cpu/post/resolved_config.json')):
        raise RuntimeError('Exact eight-GPU post-environment probe required')


def queue():
    check_cpu()
    with (ROOT / 'queue.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if (ROOT / 'queue-state.json').exists() or (ROOT / 'dispatch.json').exists():
            raise RuntimeError('Already queued; no retry')
        state = dict(phase='verifying-retained-prefix', completed=[], retained_games=24,
                     retained_updates=2, new_games=768, new_updates=94, deadline=DEADLINE)
        try:
            a.save(ROOT / 'queue-state.json', state, lock_root=ROOT)
            verify_retained(write=True)
            m.admit(0, 'first', DEADLINE)
            a.save(ROOT / 'dispatch.json', dict(start=START, deadline=DEADLINE,
                resumed_at=time.time(), gpu_hours=384, clock_inherited=True,
                retained_games=24, new_games=768, new_updates=94), lock_root=ROOT)
            h.run_stages(['gpu-preflight'], lambda _: docker('gpu-preflight', 0, 'post'), verify_probe,
                accounts(DEADLINE), ROOT / PARTS[0], ROOT / PARTS[0] / 'gpu-preflight-supervision',
                ROOT, DEADLINE, admit=lambda _: m.admit(0, 'gpu-preflight', DEADLINE))
            for index, part in enumerate(PARTS):
                cfg = f.select(index)
                if index == 1:
                    a.save(a.ROOT / 'resume-contract.json', m.contract_for(), lock_root=ROOT)
                    with (a.ROOT / 'parent-cpu.log').open('x') as log:
                        sp.run(docker('parent-cpu', 1), stdout=log, stderr=sp.STDOUT,
                               check=True, timeout=min(600, DEADLINE-45-time.time()))
                    if not a.read(a.ROOT / 'parent-readiness.json')['actual_parent_verified']:
                        raise RuntimeError('Complete native CP2 prefix required')
                a.save(a.ROOT / 'dispatch.json', dict(start=START, deadline=DEADLINE,
                    clock_inherited=True), lock_root=ROOT)
                state.update(phase='running-unverified', part=part)
                a.save(ROOT / 'queue-state.json', state, lock_root=ROOT)
                result = h.run_stages(cfg['stages'], lambda s: docker('stage', index, s), m.verify,
                    accounts(DEADLINE), a.ROOT, a.ROOT / 'host-supervision', ROOT, DEADLINE,
                    admit=lambda s: m.admit(index, s, DEADLINE))
                if index == 0:
                    result = dict(result, completed=['pre', 'train2', 'post'],
                        newly_executed=['post'], retained_from=str(OLD / PARTS[0]),
                        retained_acceptance=sha256(ROOT / 'retained-acceptance.json'))
                a.save(a.ROOT / 'state.json', result, lock_root=ROOT)
                state['completed'].append(part)
                a.save(ROOT / 'queue-state.json', state, lock_root=ROOT)
            state.update(phase='completed', exit_code=0, learning_validated=False)
            a.save(ROOT / 'queue-state.json', state, lock_root=ROOT)
        except BaseException as exc:
            state.update(phase='failed', error_type=type(exc).__name__, error=str(exc))
            a.save(ROOT / 'queue-state.json', state, lock_root=ROOT)
            raise


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode', choices=['prepare', 'queue', 'verify-retained', 'cpu', 'cpu-command',
        'prefix-cpu', 'prefix-cpu-command', 'regressions', 'host-regressions', 'regressions-command',
        'parent-cpu', 'stage', 'cpu-hook', 'cpu-hook-command', 'gpu-preflight'])
    p.add_argument('index', type=int, nargs='?', choices=(0, 1)); p.add_argument('stage', nargs='?')
    arg = p.parse_args()
    # Regression modules must retain their own callbacks while testing.
    if arg.mode in ('regressions', 'host-regressions'):
        m.ROOT = ROOT; m.SOURCE_PARENT = SOURCE_PARENT
        regressions(arg.mode == 'host-regressions'); return
    configure()
    if arg.mode in ('prepare', 'queue'): globals()[arg.mode]()
    elif arg.mode == 'verify-retained': print(json.dumps(verify_retained(False)))
    elif arg.index is None: p.error('Exact part required')
    elif arg.mode.endswith('-command'):
        print(json.dumps(docker(arg.mode.removesuffix('-command'), arg.index, arg.stage)))
    elif arg.mode == 'cpu': m.cpu(arg.index)
    elif arg.mode == 'prefix-cpu': prefix_cpu()
    elif arg.mode == 'parent-cpu': f.parent_cpu(arg.index)
    elif arg.mode in ('cpu-hook', 'gpu-preflight'):
        f.select(arg.index)
        config = a.ROOT / f'cpu/{arg.stage}/resolved_config.json'
        if arg.mode == 'cpu-hook':
            m.probe.check_hook_cpu(a.ROOT / f'cpu/hook-{arg.stage}', Path('/tmp/hook-' + arg.stage), config)
        elif (arg.index, arg.stage) == (0, 'post'):
            m.probe.run(a.ROOT / 'gpu-preflight', Path('/tmp/probe-ray'), config)
        else: raise ValueError('Only the post preflight is authorized')
    else:
        cfg = f.select(arg.index)
        a.clean(a.SOURCE, cfg['controller_sha']); a.clean(a.ROOT / 'runtime', cfg['runtime_sha'])
        args, env, _ = m.invocation(cfg, arg.stage)
        fd = os.open(a.ROOT / (arg.stage + '-entry.log'), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        os.dup2(fd, 1); os.dup2(fd, 2); os.close(fd)
        os.chdir(a.ROOT / 'runtime'); os.execvpe(args[0], args, env)


if __name__ == '__main__': main()
