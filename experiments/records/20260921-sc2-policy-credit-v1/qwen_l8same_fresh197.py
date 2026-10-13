"""Approved Sep26: original Qwen, L8 same-seed, fresh short then own CP2 to 96."""
import argparse
import copy
import fcntl
import json
import os
from pathlib import Path
import shutil
import subprocess as sp
import sys
import time
import unittest

import qwen_l7same_fresh197 as fresh
import qwen_l8_training_probe as probe
from agent_system.sc2_policy_resume import prefix_files, sha256, verify_contract
from agent_system.sc2_seed_protocol import ablation_seeds

a, f, h, orchestration = fresh.a, fresh.f, fresh.h, fresh.queue_impl
ROOT = Path('/var/jfsCache/sc2-qwen-l8same96-197-20260926-r1')
SOURCE_PARENT = Path('/var/jfsCache/sc2-qwen-l8same96-197-source-20260926-r1')
PREFIX = 'sc2-qwen-l8same96-197-20260926-r1-'
PARTS = ('qwen-same/short', 'qwen-same/long')
BASE = Path('/var/jfsCache/sc2-qwen-l7same96-197-20260924-r1/qwen-same/short')
WALL_SECONDS, LIMIT = 48 * 3600, 1024 * a.GIB
CPU_PROBES = ((0, 'pre'), (0, 'train2'), (1, 'train96'))
AUTHORIZATION = ('Sep26 user explicitly approved original Qwen L8 same96, 768 training '
    '+24 evaluation games/96 PPO, node197/eight GPUs, 48wallh/384GPUh/1TiB; '
    'no deletion, automatic retry, other arm or successor. Unfinished L8 eval64 not dispatched.')


def configure():
    fresh.ROOT, fresh.PARTS, fresh.PREFIX = ROOT, PARTS, PREFIX
    fresh.configure()
    f.invocation, f.verify = invocation, verify
    f.DOCKER_SCRIPT = a.HERE / 'qwen_l8same_fresh197.py'


def accounts(deadline):
    return [dict(roots=[ROOT, SOURCE_PARENT], receipt_root=ROOT, limit=LIMIT, deadline=deadline)]


def prepare():
    if ROOT.exists() or a.SOURCE != SOURCE_PARENT / 'code':
        raise RuntimeError('Fresh exact source/output required; no overwrite')
    commit = a.cmd(['git', '-C', a.SOURCE, 'rev-parse', 'HEAD'])
    a.clean(a.SOURCE, commit)
    a.clean(a.ORCH, a.ORCH_SHA)
    base = a.read(BASE / 'deployment.json')
    if (base['model_kind'], base['seed_protocol'], base['model_mount']) != (
            'qwen', 'same_uniform101', '/assets/qwen'):
        raise RuntimeError('Wrong released Qwen configuration template')
    ROOT.mkdir()
    a.STORAGE_LOCK_ROOT = ROOT
    # Independent objects: repeated --shared chains exceeded Git's recursion limit in r6.
    sp.run(['git', 'clone', '--quiet', '--no-local', str(a.SOURCE), str(ROOT / 'runtime')],
           check=True, timeout=120)
    a.cmd(['git', '-C', ROOT / 'runtime', 'checkout', '--quiet', '--detach', commit])
    first_dispatch_by = time.time() + 4 * 3600  # waiting consumes no GPU budget
    for index, part in enumerate(PARTS):
        owner = ROOT / part
        owner.mkdir(parents=True)
        for name in ('runs', 'cpu', 'tmp', 'tmp/task-home', 'tmp/cache', 'tmp/cuda-cache'):
            (owner / name).mkdir()
        (owner / 'runtime').symlink_to(ROOT / 'runtime', target_is_directory=True)
        cfg = copy.deepcopy(base)
        cfg.pop('prior_failed_root', None)
        cfg.update(runtime_sha=commit, controller_sha=commit, controller_source=str(a.SOURCE),
            orchestration_sha=a.ORCH_SHA, model_kind='qwen', model_mount='/assets/qwen',
            difficulty='CheatVision', seed_protocol='same_uniform101', seed_group_mode='same',
            training_seeds=[ablation_seeds('same_uniform101', 0, i, 1, 8) for i in range(96)],
            stages=['pre', 'train2', 'post'] if index == 0 else ['train96', 'eval96'],
            games=[8, 16, 8] if index == 0 else [752, 8], updates=[0, 2, 0] if index == 0 else [94, 0],
            run_prefix=PREFIX + ('short' if index == 0 else 'long'), worker_hook='l7_followup_hook.install',
            wall_seconds=WALL_SECONDS, gpu_hours=384, output_limit_bytes=LIMIT,
            first_dispatch_by=first_dispatch_by, queue_expires=first_dispatch_by,
            no_retry=True, no_long_training=False, successors_authorized=index == 0,
            predecessor=None if index == 0 else str(ROOT / PARTS[0]), authorization=AUTHORIZATION,
            storage_supervision='host-guardian-v1', host_stage_entry_log=True,
            container_rootfs_read_only=True, startup_concurrency=1, level='L8',
            limitation='Fresh released weights, not L7 CP96 continuation; no causal learning claim')
        a.save(owner / 'deployment.json', cfg, lock_root=ROOT)
    a.save(ROOT / 'deployment.json', dict(runtime_sha=commit, controller_sha=commit,
        controller_source=str(a.SOURCE), orchestration_sha=a.ORCH_SHA, parts=PARTS,
        first_dispatch_by=first_dispatch_by, wall_seconds=WALL_SECONDS, gpu_hours=384,
        output_limit_bytes=LIMIT, storage_roots=[str(ROOT), str(SOURCE_PARENT)],
        new_games=792, new_updates=96, short_included=True, no_retry=True,
        successors_authorized=False, original_weights=True, level='L8', difficulty='CheatVision',
        cpu_hook_probes=CPU_PROBES, gpu_preflight_required=True,
        train_admission_free_gib=1084, evaluation_admission_free_gib=128,
        authorization=AUTHORIZATION), lock_root=ROOT)


def invocation(cfg, stage, dry=False):
    if cfg['difficulty'] != 'CheatVision' or cfg['model_kind'] != 'qwen':
        raise RuntimeError('Only Qwen L8 is authorized')
    args, env, out = fresh.BASE_INVOCATION(cfg, stage, dry)
    args += ["+ray_init.runtime_env.env_vars.SC2_L8_RENDEZVOUS_LOW_PORT='1'"]
    env['RAY_TMPDIR'] = '/tmp/l8-' + stage
    return args, env, out


def docker(mode, index, stage=None):
    if mode not in ('cpu-hook', 'gpu-preflight'):
        return fresh.docker(mode, index, stage)
    cfg = f.select(index)
    if stage not in cfg['stages']:
        raise ValueError('Exact probe configuration stage required')
    gpu = mode == 'gpu-preflight'
    args = fresh.docker('stage' if gpu else 'cpu', index, stage if gpu else None)
    args[args.index('--name') + 1] = PREFIX + ('short-' if index == 0 else 'long-') + mode + '-' + stage
    if not gpu:
        args[args.index('--memory') + 1] = '16g'
        args[-2:] = [mode, str(index), stage]
    else:
        args[-3:] = [mode, str(index), stage]
    ev = a.read(a.ROOT / f'cpu/{stage}/resolved_config.json')['ray_init']['runtime_env']['env_vars']
    for i, arg in enumerate(args):
        if arg.startswith('PYTHONPATH='):
            args[i] = 'PYTHONPATH=' + ev['PYTHONPATH']
    return args


def cpu(index):
    fresh.cpu(index)
    for stage in a.read(a.ROOT / 'deployment.json')['stages']:
        probe.runtime_environment(a.ROOT / f'cpu/{stage}/resolved_config.json', '/tmp/probe-ray')


def run_probe(mode, index, stage):
    f.select(index)
    config = a.ROOT / f'cpu/{stage}/resolved_config.json'
    if mode == 'cpu-hook':
        probe.check_hook_cpu(a.ROOT / f'cpu/hook-{stage}', Path('/tmp/hook-' + stage), config)
    elif mode == 'gpu-preflight' and index == 0 and stage == 'train2':
        probe.run(a.ROOT / 'gpu-preflight', Path('/tmp/probe-ray'), config)
    else:
        raise ValueError('Unexpected probe dispatch')


def regressions(host_only=False):
    sys.path[:0] = [str(a.SOURCE / 'tests'), str(a.SOURCE / 'scripts')]
    orchestration.ROOT, orchestration.PARTS = ROOT, PARTS
    orchestration.regressions(host_only)
    if not host_only:
        result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromNames(
            ['test_qwen_l7same_fresh197', 'test_qwen_l8same_fresh197', 'test_qwen_l8_probe_env',
             'test_qwen_l8_remainder3_197']))
        if not result.wasSuccessful() or result.skipped:
            raise RuntimeError('L8 fresh regression failure')
        path = ROOT / PARTS[0] / 'regressions.json'
        proof = a.read(path)
        proof['tests'] += result.testsRun
        proof['l8_fresh_tests'] = result.testsRun
        a.save(path, proof, lock_root=ROOT)


def check_cpu():
    fresh.BASE_CHECK_CPU()
    if a.read(ROOT / PARTS[0] / 'regressions.json').get('l8_fresh_tests', 0) <= 0:
        raise RuntimeError('L8 regressions required')
    for index, stage in CPU_PROBES:
        owner = ROOT / PARTS[index]
        proof = a.read(owner / f'cpu/hook-{stage}/cpu-hook-preflight.json')
        if (not proof['passed'] or proof['natural_games'] or proof['optimizer_updates']
                or proof['model_loaded'] or proof['worker']['cuda_initialized']
                or proof['worker']['cuda_device_count']
                or proof['runtime_environment']['resolved_config_sha256'] !=
                    sha256(owner / f'cpu/{stage}/resolved_config.json')):
            raise RuntimeError('Actual full-environment CPU hook proof required')


def verify_probe(stage):
    proof = a.read(ROOT / PARTS[0] / 'gpu-preflight/gpu-preflight.json')
    if (stage != 'gpu-preflight' or not proof['passed'] or len(proof['ranks']) != 8
            or len({row['cuda_uuid'] for row in proof['ranks']}) != 8
            or proof['nccl_sums'] != [28.0] * 8 or proof['natural_games']
            or proof['optimizer_updates'] or proof['model_loaded']
            or proof['runtime_environment']['resolved_config_sha256'] !=
                sha256(ROOT / PARTS[0] / 'cpu/train2/resolved_config.json')):
        raise RuntimeError('Eight distinct GPUs and successful NCCL required')


def verify(stage, write=True):
    fresh.verify(stage, write=False)
    replay_evidence(a.ROOT / 'runs' / stage, stage)
    if write:
        fresh.verify(stage, write=True)


def replay_evidence(out, stage):
    """Training has no result.replays; check actual files for every stage."""
    expected = {'pre': 8, 'train2': 16, 'post': 8, 'train96': 752, 'eval96': 8}[stage]
    files = sorted((out / 'sc2-logs').rglob('*.SC2Replay'))
    names = [str(p.relative_to(out)) for p in files]
    if (len(files) != expected or len({p.resolve() for p in files}) != expected
            or any('/Flat128_CheatVision_Air/' not in name for name in names)
            or any(not p.is_file() or p.stat().st_size <= 0
                   or not p.resolve().is_relative_to(out.resolve()) for p in files)):
        raise RuntimeError('All natural replay paths must show actual L8 difficulty')
    result = a.read(out / 'result.json')
    if stage in ('pre', 'post', 'eval96'):
        if result.get('replays') != {name: sha256(p) for name, p in zip(names, files)}:
            raise RuntimeError('Evaluation replay digest inventory mismatch')
    return {name: p.stat().st_size for name, p in zip(names, files)}


def contract_for():
    parent = ROOT / PARTS[0]
    contract = dict(version='accepted-qwen-l8-same-full-state-prefix-v1', parent=str(parent),
        checkpoint=str(parent / 'runs/train2/checkpoints/global_step_2'),
        parent_sha=a.read(parent / 'deployment.json')['runtime_sha'], start_step=2, target_step=96,
        driver_rng_unavailable_accepted=False,
        files={name: sha256(parent / name) for name in prefix_files()})
    verify_contract(contract)
    return contract


def resources_ready(stage):
    rows = a.cmd(['nvidia-smi', '--query-gpu=index,memory.used,utilization.gpu',
                  '--format=csv,noheader,nounits']).splitlines()
    if len(rows) != 8 or sorted(int(row.split(',')[0]) for row in rows) != list(range(8)):
        raise RuntimeError('Expected exact eight GPUs')
    if any(float(v.strip()) > 0 for row in rows for v in row.split(',')[1:]):
        return False
    if a.cmd(['nvidia-smi', '--query-compute-apps=pid', '--format=csv,noheader']):
        return False
    mem = dict(line.split(':', 1) for line in Path('/proc/meminfo').read_text().splitlines())
    # New queue only: evaluations create no checkpoints. Old queue gates are untouched.
    disk_gib = 128 if stage in ('post', 'eval96') else 1084
    return (int(mem['MemAvailable'].split()[0]) * 1024 >= 600 * a.GIB
            and shutil.disk_usage(ROOT).free >= disk_gib * a.GIB)


def admit(index, stage, deadline):
    owner = ROOT / PARTS[index]
    while True:
        if time.time() >= deadline - 45:
            raise TimeoutError('Unchanged admission deadline reached')
        h.sample(accounts(deadline), ROOT)
        orchestration.host.writers_clear(accounts(deadline)[0]['roots'])
        if resources_ready(stage):
            break
        time.sleep(min(30, deadline - 45 - time.time()))
    with (owner / ('fsync-' + stage)).open('xb') as stream:
        stream.write(b'l8-fresh\n'); stream.flush(); os.fsync(stream.fileno())
    if (owner / ('fsync-' + stage)).read_bytes() != b'l8-fresh\n':
        raise RuntimeError('Fsync readback failed')
    a.save(owner / ('admission-' + stage + '.json'), dict(passed=True, checked_at=time.time(),
        deadline=deadline, eight_idle_gpus=True, ram_gib_min=600,
        nvme_gib_min=128 if stage in ('post', 'eval96') else 1084, fsync=True), lock_root=ROOT)


def queue():
    check_cpu()
    with (ROOT / 'queue.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if (ROOT / 'queue-state.json').exists() or (ROOT / 'dispatch.json').exists():
            raise RuntimeError('Already queued; no retry')
        state = dict(phase='waiting-admission', completed=[], new_games=792, new_updates=96)
        try:
            a.save(ROOT / 'queue-state.json', state, lock_root=ROOT)
            admit(0, 'first', a.read(ROOT / 'deployment.json')['first_dispatch_by'])
            start = time.time(); deadline = start + WALL_SECONDS
            a.save(ROOT / 'dispatch.json', dict(start=start, deadline=deadline, gpu_hours=384,
                new_games=792, new_updates=96, includes_gpu_preflight=True), lock_root=ROOT)
            state.update(phase='gpu-preflight', deadline=deadline)
            a.save(ROOT / 'queue-state.json', state, lock_root=ROOT)
            h.run_stages(['gpu-preflight'], lambda _: docker('gpu-preflight', 0, 'train2'), verify_probe,
                accounts(deadline), ROOT / PARTS[0], ROOT / PARTS[0] / 'gpu-preflight-supervision',
                ROOT, deadline, admit=lambda _: admit(0, 'gpu-preflight', deadline))
            for index, part in enumerate(PARTS):
                cfg = f.select(index)
                if index == 1:
                    a.save(a.ROOT / 'resume-contract.json', contract_for(), lock_root=ROOT)
                    with (a.ROOT / 'parent-cpu.log').open('x') as log:
                        sp.run(docker('parent-cpu', 1), stdout=log, stderr=sp.STDOUT, check=True,
                               timeout=min(600, deadline - 45 - time.time()))
                    if not a.read(a.ROOT / 'parent-readiness.json')['actual_parent_verified']:
                        raise RuntimeError('Own native CP2 and driver RNG must pass')
                a.save(a.ROOT / 'dispatch.json', dict(start=start, deadline=deadline,
                    clock_shared_with_short=True), lock_root=ROOT)
                state.update(phase='running-unverified', part=part)
                a.save(ROOT / 'queue-state.json', state, lock_root=ROOT)
                result = h.run_stages(cfg['stages'], lambda stage: docker('stage', index, stage), verify,
                    accounts(deadline), a.ROOT, a.ROOT / 'host-supervision', ROOT, deadline,
                    admit=lambda stage: admit(index, stage, deadline))
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
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['prepare', 'queue', 'cpu', 'cpu-command', 'regressions',
        'host-regressions', 'regressions-command', 'parent-cpu', 'stage', 'cpu-hook',
        'cpu-hook-command', 'gpu-preflight'])
    parser.add_argument('index', type=int, nargs='?', choices=(0, 1))
    parser.add_argument('stage', nargs='?')
    arg = parser.parse_args()
    if arg.mode in ('regressions', 'host-regressions'):
        regressions(arg.mode == 'host-regressions')
        return
    configure()
    if arg.mode in ('prepare', 'queue'):
        globals()[arg.mode]()
    elif arg.index is None:
        parser.error('Exact part required')
    elif arg.mode.endswith('-command'):
        print(json.dumps(docker(arg.mode.removesuffix('-command'), arg.index, arg.stage)))
    elif arg.mode == 'cpu':
        cpu(arg.index)
    elif arg.mode == 'parent-cpu':
        f.parent_cpu(arg.index)
    elif arg.mode in ('cpu-hook', 'gpu-preflight'):
        run_probe(arg.mode, arg.index, arg.stage)
    else:
        cfg = f.select(arg.index)
        a.clean(a.SOURCE, cfg['controller_sha']); a.clean(a.ROOT / 'runtime', cfg['runtime_sha'])
        args, env, _ = invocation(cfg, arg.stage)
        fd = os.open(a.ROOT / (arg.stage + '-entry.log'), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        os.dup2(fd, 1); os.dup2(fd, 2); os.close(fd)
        os.chdir(a.ROOT / 'runtime'); os.execvpe(args[0], args, env)


if __name__ == '__main__':
    main()
