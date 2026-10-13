"""Approved fresh Qwen same-seed short+96; reuse the existing one-shot host queue."""
import argparse
import copy
import json
import math
from pathlib import Path
import subprocess as sp
import sys
import time

import spb_l7_random197 as queue_impl
from agent_system.sc2_policy_resume import prefix_files, sha256, verify_contract
from agent_system.sc2_seed_protocol import ablation_seeds

a, f, h = queue_impl.a, queue_impl.f, queue_impl.h
ROOT = Path('/var/jfsCache/sc2-qwen-l7same96-197-20260924-r1')
PARTS = ('qwen-same/short', 'qwen-same/long')
PREFIX = 'sc2-qwen-l7same96-197-20260924-r1-'
BASE = Path('/var/jfsCache/sc2-qwen-seeds197-20260922-r4/l7-same')
PREDECESSOR = Path('/var/jfsCache/sc2-spb-l7random96-197-20260923-r1')
PREDECESSOR_SHA = '83f3530765babe048035524ddf1651291810818a'
PREDECESSOR_DEADLINE = 1790356959.0174987
FIRST_DISPATCH_BY = PREDECESSOR_DEADLINE + 3600
WALL_SECONDS = 48 * 3600
LIMIT = 1024 * a.GIB
BASE_INVOCATION, BASE_VERIFY, BASE_DOCKER = f.invocation, f.verify, queue_impl.BASE_DOCKER
BASE_CHECK_CPU = queue_impl.check_cpu


def parent_for(index):
    if index != 1:
        raise ValueError('Only own fresh native Qwen CP2 is authorized')
    return ROOT / PARTS[0]


def configure():
    # Reuse only the tested one-shot orchestration; no changes to frozen predecessors.
    queue_impl.ROOT, queue_impl.PARTS, queue_impl.PREFIX = ROOT, PARTS, PREFIX
    queue_impl.PREDECESSOR = PREDECESSOR
    queue_impl.PREDECESSOR_SHA = PREDECESSOR_SHA
    queue_impl.PREDECESSOR_DEADLINE = PREDECESSOR_DEADLINE
    queue_impl.FIRST_DISPATCH_BY = FIRST_DISPATCH_BY
    queue_impl.parent_for = parent_for
    queue_impl.invocation, queue_impl.verify = invocation, verify
    queue_impl.docker, queue_impl.contract_for = docker, contract_for
    queue_impl.predecessor_complete = predecessor_complete
    queue_impl.check_cpu = check_cpu
    queue_impl.configure()
    f.DOCKER_SCRIPT = a.HERE / 'qwen_l7same_fresh197.py'


def prepare():
    if ROOT.exists():
        raise RuntimeError('Fresh root required; no overwrite/retry')
    sha = a.cmd(['git', '-C', a.SOURCE, 'rev-parse', 'HEAD'])
    a.clean(a.SOURCE, sha)
    a.clean(a.ORCH, a.ORCH_SHA)
    base = a.read(BASE / 'deployment.json')
    if base['model_kind'] != 'qwen' or base['seed_protocol'] != 'same_uniform101':
        raise RuntimeError('Wrong original Qwen same-seed configuration')
    authorization = ('Sep24 user approved fresh Qwen same-seed 792new natural games/96PPO/'
        '48wallh/384GPUh/1TiB, original weights, own nativeCP2, after SpB random acceptance; '
        'plotted old same intermediate shards separately pruned by exact authorized allowlist; '
        'no further deletion, retry, gate reduction, or other arm')
    ROOT.mkdir()
    a.STORAGE_LOCK_ROOT = ROOT
    a.cmd(['git', 'clone', '--quiet', '--shared', a.SOURCE, ROOT/'runtime'])
    a.cmd(['git', '-C', ROOT/'runtime', 'checkout', '--quiet', '--detach', sha])
    for index, part in enumerate(PARTS):
        owner = ROOT / part
        owner.mkdir(parents=True)
        for name in ('runs', 'cpu', 'tmp', 'tmp/task-home', 'tmp/cache', 'tmp/cuda-cache'):
            (owner/name).mkdir()
        (owner/'runtime').symlink_to(ROOT/'runtime', target_is_directory=True)
        cfg = copy.deepcopy(base)
        cfg.pop('prior_failed_root', None)
        cfg.update(runtime_sha=sha, controller_sha=sha, controller_source=str(a.SOURCE),
            orchestration_sha=a.ORCH_SHA, model_kind='qwen', model_mount='/assets/qwen',
            difficulty='VeryHard', seed_protocol='same_uniform101', seed_group_mode='same',
            training_seeds=[ablation_seeds('same_uniform101', 0, i, 1, 8) for i in range(96)],
            stages=['pre','train2','post'] if index == 0 else ['train96','eval96'],
            games=[8,16,8] if index == 0 else [752,8], updates=[0,2,0] if index == 0 else [94,0],
            run_prefix=PREFIX+('short' if index == 0 else 'long'), worker_hook='l7_followup_hook.install',
            wall_seconds=WALL_SECONDS, gpu_hours=384, output_limit_bytes=LIMIT,
            first_dispatch_by=FIRST_DISPATCH_BY, queue_expires=FIRST_DISPATCH_BY,
            no_retry=True, no_long_training=False, successors_authorized=index == 0,
            predecessor=str(PREDECESSOR if index == 0 else ROOT/PARTS[0]),
            authorization=authorization, storage_supervision='host-guardian-v1',
            host_stage_entry_log=True, container_rootfs_read_only=True, startup_concurrency=1,
            limitation='Not bitwise replay of old same run: startup timing and complete native CP2 differ; no learning claim')
        a.save(owner/'deployment.json', cfg, lock_root=ROOT)
    a.save(ROOT/'deployment.json', dict(runtime_sha=sha, controller_sha=sha,
        controller_source=str(a.SOURCE), orchestration_sha=a.ORCH_SHA, parts=PARTS,
        predecessor=str(PREDECESSOR), predecessor_sha=PREDECESSOR_SHA,
        predecessor_deadline=PREDECESSOR_DEADLINE, first_dispatch_by=FIRST_DISPATCH_BY,
        wall_seconds=WALL_SECONDS, gpu_hours=384, output_limit_bytes=LIMIT,
        storage_roots=[str(ROOT), str(a.SOURCE.parent)], new_games=792, new_updates=96,
        short_included=True, no_retry=True, successors_authorized=False,
        authorization=authorization), lock_root=ROOT)


def invocation(cfg, stage, dry=False):
    # Qwen's pinned launcher already sets concurrency=1; do not duplicate Hydra '+'.
    return BASE_INVOCATION(cfg, stage, dry)


def docker(mode, index, stage=None):
    cfg = f.select(index)
    args = BASE_DOCKER('execute' if mode == 'stage' else 'cpu')
    args[2:2] = ['--read-only', '--log-driver', 'none', '-e', 'HOME=/tmp/task-home',
        '-e', 'XDG_CACHE_HOME=/tmp/cache', '-e', 'CUDA_CACHE_PATH=/tmp/cuda-cache',
        '-e', 'TMPDIR=/tmp', '-v', f'{ROOT}:{ROOT}:ro',
        '-v', f'{ROOT}/.storage.lock:{ROOT}/.storage.lock']
    if mode != 'stage':
        mount = cfg.get('model_mount', '/assets/qwen')
        metadata = f.previous.SPB_METADATA if cfg.get('model_kind') == 'spb' else f.previous.CPU_MODEL
        args[args.index(f'{cfg["host"]["model"]}:{mount}:ro')] = f'{metadata}:{mount}:ro'
        args[2:2] = ['-v', f'{f.previous.SPB_METADATA}:/metadata/spb:ro',
            '-v', f'{f.previous.CPU_MODEL}:/metadata/qwen:ro',
            '-e', 'SC2_TEST_SPB_METADATA_PATH=/metadata/spb', '-e', 'SC2_TEST_QWEN_METADATA_PATH=/metadata/qwen',
            '-e', 'SC2_TEST_TOKENIZER_PATH=/metadata/qwen', '-e', 'OMP_NUM_THREADS=2',
            '-e', 'TOKENIZERS_PARALLELISM=false']
    owner = ROOT/PARTS[index]
    writable = [tuple(args[i+1].split(':')[:2]) for i, value in enumerate(args[:-1])
                if value == '-v' and args[i+1].split(':')[-1] != 'ro']
    expected = {(str(owner), str(owner)), (str(owner/'tmp'), '/tmp'),
                (str(ROOT/'.storage.lock'), str(ROOT/'.storage.lock'))}
    if len(writable) != 3 or set(writable) != expected:
        raise RuntimeError('Unexpected writable bind')
    args[args.index('--name')+1] = PREFIX+('short' if index == 0 else 'long')+'-'+(stage or mode)
    args[-1:] = [mode, str(index)]
    if mode == 'stage':
        if stage not in cfg['stages']:
            raise ValueError('Undeclared stage')
        args[1] = 'create'
        args.append(stage)
    return args


def cpu(index):
    f.cpu(index)
    for stage in a.read(a.ROOT/'deployment.json')['stages']:
        cfg = a.read(a.ROOT/f'cpu/{stage}/resolved_config.json')
        ev = cfg['ray_init']['runtime_env']['env_vars']
        if (str(ev['SC2_RESET_CONCURRENCY']) != '1' or str(ev['SC2_RESET_RETRIES']) != '1'
                or str(ev['SC2_TRAIN_SEED_PROTOCOL']) != 'same_uniform101'
                or cfg['algorithm']['sc2_policy_credit']['seed_group_mode'] != 'same'):
            raise RuntimeError('Same seed/startup protocol mismatch')


def verify(stage, write=True):
    out = a.ROOT/'runs'/stage
    if any(a.read(out/name).get('metrics_precision') != 'binary64-v1'
           for name in ('manifest.json', 'result.json')):
        raise RuntimeError('Full precision required')
    BASE_VERIFY(stage, False)
    if stage in ('train2', 'train96'):
        lo, hi = (1, 2) if stage == 'train2' else (3, 96)
        metrics = a.read(out/'metrics.json')
        if ([row['step'] for row in metrics] != list(range(lo, hi+1))
                or any(not math.isfinite(row[key]) or row[key] <= 0
                       for row in metrics for key in ('actor/grad_norm', 'timing_s/update_actor'))
                or any(not math.isfinite(row['policy_credit/invalid_advantage_max'])
                       or row['policy_credit/invalid_advantage_max'] > 0 for row in metrics)):
            raise RuntimeError('Returned finite positive PPO evidence required')
        seeds = [json.loads(row) for row in (out/'training_seeds.jsonl').read_text().splitlines()]
        if len(seeds) != hi-lo+1 or any(row['reset_index'] != i or row['base_seed'] != 0
                or row['seed_protocol'] != 'same_uniform101'
                or row['seeds'] != ablation_seeds('same_uniform101', 0, i, 1, 8)
                for i, row in enumerate(seeds, lo-1)):
            raise RuntimeError('Exact same-seed ledger required')
    if write:
        BASE_VERIFY(stage, True)


def contract_for():
    parent = ROOT/PARTS[0]
    contract = dict(version='accepted-qwen-same-full-state-prefix-v1', parent=str(parent),
        checkpoint=str(parent/'runs/train2/checkpoints/global_step_2'),
        parent_sha=a.read(parent/'deployment.json')['runtime_sha'], start_step=2, target_step=96,
        driver_rng_unavailable_accepted=False,
        files={name: sha256(parent/name) for name in prefix_files()})
    verify_contract(contract)
    return contract


def check_cpu():
    BASE_CHECK_CPU()
    proof = a.read(ROOT/PARTS[0]/'regressions.json')
    if proof.get('fresh_qwen_tests', 0) <= 0:
        raise RuntimeError('Fresh Qwen regression evidence required')


def predecessor_complete():
    state = a.read(PREDECESSOR/'queue-state.json')
    if state['phase'] == 'failed':
        raise RuntimeError('SpB predecessor failed; no new Qwen dispatch')
    if state['phase'] != 'completed':
        return False
    if (state.get('exit_code') != 0 or state['completed'] != ['spb-random/short', 'spb-random/long']
            or state['deadline'] != PREDECESSOR_DEADLINE):
        raise RuntimeError('SpB predecessor queue mismatch')
    cfg = a.read(PREDECESSOR/'deployment.json')
    if cfg['runtime_sha'] != PREDECESSOR_SHA:
        raise RuntimeError('Wrong predecessor runtime')
    a.clean(PREDECESSOR/'runtime', PREDECESSOR_SHA)
    a.clean(Path(cfg['controller_source']), PREDECESSOR_SHA)
    for part, stages in [('short', ['pre','train2','post']), ('long', ['train96','eval96'])]:
        owner = PREDECESSOR/'spb-random'/part
        for name in ('state.json', 'host-supervision/state.json'):
            terminal = a.read(owner/name)
            if (terminal['phase'] != 'completed' or terminal.get('exit_code') != 0
                    or terminal['completed'] != stages or terminal['deadline'] != PREDECESSOR_DEADLINE):
                raise RuntimeError('SpB predecessor part incomplete')
        for stage in stages:
            name = 'sc2-spb-l7random96-197-20260923-r1-'+part+'-'+stage
            status = json.loads(a.cmd(['docker', 'inspect', '--format',
                '{"id":"{{.Id}}","owner":"{{index .Config.Labels "sc2.acceptance.root"}}","state":{{json .State}}}', name]))
            s = status['state']
            receipt = a.read(owner/f'host-supervision/{stage}-guardian.json')
            if (s['Running'] or s['Paused'] or s['ExitCode'] != 0 or s['OOMKilled'] or s['Error']
                    or status['owner'] != str(owner) or receipt['container_id'] != status['id']
                    or receipt['owner_root'] != str(owner) or receipt['phase'] != 'completed'
                    or receipt['deadline'] != PREDECESSOR_DEADLINE
                    or receipt['final_state']['ExitCode'] != 0 or receipt['final_state']['Running']
                    or receipt['final_state']['Paused']):
                raise RuntimeError('SpB predecessor container/guardian mismatch')
    script = Path(cfg['controller_source'])/a.HERE.relative_to(a.SOURCE)
    code = (f"import sys;sys.path.insert(0,{str(script)!r});import spb_l7_random197 as m;"
            "m.configure();m.f.select(0);"
            "[m.verify(s,write=False) for s in ('pre','train2','post')];"
            "m.f.select(1);[m.verify(s,write=False) for s in ('train96','eval96')]")
    sp.run([sys.executable, '-B', '-c', code], check=True, timeout=180)
    return True


def regressions(host_only=False):
    # Do not install Qwen callbacks while testing the original SpB wrapper.
    import unittest
    sys.path[:0] = [str(a.SOURCE/'tests'), str(a.SOURCE/'scripts')]
    queue_impl.ROOT, queue_impl.PARTS = ROOT, PARTS
    if not host_only:
        result = unittest.TextTestRunner(verbosity=2).run(
            unittest.defaultTestLoader.loadTestsFromName('test_qwen_l7same_fresh197'))
        if not result.wasSuccessful() or result.skipped:
            raise RuntimeError('Fresh Qwen CPU tests failed; no dispatch')
    queue_impl.regressions(host_only)
    if not host_only:
        path = ROOT/PARTS[0]/'regressions.json'
        proof = a.read(path)
        proof['tests'] += result.testsRun
        proof['fresh_qwen_tests'] = result.testsRun
        a.save(path, proof, lock_root=ROOT)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['prepare','queue','cpu','cpu-command',
        'regressions-command','regressions','host-regressions','parent-cpu','stage'])
    parser.add_argument('index', type=int, nargs='?', choices=(0,1))
    parser.add_argument('stage', nargs='?')
    arg = parser.parse_args()
    if arg.mode in ('regressions', 'host-regressions'):
        regressions(arg.mode == 'host-regressions')
    else:
        configure()
        if arg.mode == 'prepare': prepare()
        elif arg.mode == 'queue': queue_impl.queue()
        elif arg.index is None: parser.error('Exact short/long index required')
        elif arg.mode.endswith('-command'): print(json.dumps(docker(arg.mode.removesuffix('-command'), arg.index)))
        elif arg.mode == 'cpu': cpu(arg.index)
        elif arg.mode == 'parent-cpu': f.parent_cpu(arg.index)
        else: queue_impl.child_stage(arg.index, arg.stage)
