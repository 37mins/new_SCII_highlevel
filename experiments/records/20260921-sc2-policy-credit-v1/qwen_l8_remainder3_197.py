"""Single authorized r3 continuation of only the 64 unrun Qwen L8 games."""
import argparse
import copy
import fcntl
import json
import os
from pathlib import Path
import sys
import time
import unittest

import acceptance197 as a
import host_stage197 as h
import l7_matrix256197 as matrix
import qwen_l8_pilot197 as pilot
import qwen_l8_remainder197 as r2
from qwen_l8_plan import ARMS, SEEDS, STAGES as ALL_STAGES

ROOT = Path('/var/jfsCache/sc2-qwen-l8-pilot96-197-20260925-r3')
SOURCE_PARENT = Path('/var/jfsCache/sc2-qwen-l8-pilot96-197-source-20260925-r3')
PREFIX = 'sc2-qwen-l8-pilot96-197-20260925-r3'
STAGES = ALL_STAGES[4:]
WALL_SECONDS = 4 * 3600
LIMIT = 32 * a.GIB
FAILURE_RECORD = a.HERE / 'qwen-l8-pilot-r2-failure-20260925.json'


def accounts(deadline):
    return [dict(roots=[r2.PRIOR, r2.PRIOR_SOURCE, r2.ROOT,
                        r2.SOURCE_PARENT, ROOT, SOURCE_PARENT],
                 receipt_root=ROOT, limit=LIMIT, deadline=deadline)]


def invocation(deployment, stage, dry=False):
    if stage not in STAGES:
        raise RuntimeError('Only the eight unrun L8 stages are authorized')
    args, env, out = r2.BASE_INVOCATION(deployment, stage, dry)
    args.append("+ray_init.runtime_env.env_vars.SC2_L8_RENDEZVOUS_LOW_PORT='1'")
    return args, env, out


def configure():
    pilot.ROOT, pilot.SOURCE_PARENT, pilot.PREFIX = ROOT, SOURCE_PARENT, PREFIX
    pilot.STAGES, pilot.PRIOR_ACCEPTANCE_ROOT = STAGES, r2.PRIOR
    pilot.accounts, pilot.invocation = accounts, invocation
    a.ROOT = a.STORAGE_LOCK_ROOT = ROOT
    a.CONTAINER = PREFIX
    a.DOCKER_SCRIPT = a.HERE / 'qwen_l8_remainder3_197.py'
    if (ROOT / 'deployment.json').exists():
        a.RUNTIME_SHA = matrix.small(ROOT / 'deployment.json')['runtime_sha']


def previous_failures():
    """Bind the 32 accepted r1 games and the zero-game r2 failure to r3."""
    first = r2.accepted_prefix()
    proof = matrix.small(FAILURE_RECORD)
    deployment = matrix.small(r2.ROOT / 'deployment.json')
    queue = matrix.small(r2.ROOT / 'queue-state.json')
    host = matrix.small(r2.ROOT / 'host-supervision/state.json')
    result = matrix.small(r2.ROOT / 'runs' / STAGES[0] / 'result.json')
    if (proof['runtime_sha'] != deployment['runtime_sha']
            or proof['old_root'] != str(r2.PRIOR)
            or proof['new_root'] != str(r2.ROOT)
            or proof['scope']['old_accepted_natural_games'] != 32
            or proof['scope']['new_natural_games'] != 0
            or queue['phase'] != 'failed' or host['phase'] != 'failed'
            or result != matrix.small(r2.ROOT / 'runs' / STAGES[0] / '.done')
            or result['status'] != 'failed' or result['process_exit_code'] != 1
            or result['episode_outcomes']['natural_games'] != 0
            or (r2.ROOT / f'acceptance-{STAGES[0]}.json').exists()
            or any((r2.ROOT / f'acceptance-{stage}.json').exists() for stage in STAGES[1:])):
        raise RuntimeError('r1/r2 historical boundary or r2 zero-game failure changed')
    a.clean(r2.ROOT / 'runtime', proof['runtime_sha'])
    a.clean(r2.SOURCE_PARENT / 'code', proof['runtime_sha'])
    for rel, expected in proof['terminal_sha256'].items():
        if rel == 'storage-state.json':
            continue  # May be resampled; terminal identity is checked above.
        if matrix.digest(r2.ROOT / rel) != expected:
            raise RuntimeError('r2 terminal receipt changed: ' + rel)
    cid = proof['first_stage']['container_id']
    obj = json.loads(a.cmd(['docker', 'inspect', '--format',
        '{"id":"{{.Id}}","owner":"{{index .Config.Labels "sc2.acceptance.root"}}",'
        '"state":{{json .State}}}', cid]))
    state = obj['state']
    if (obj['id'] != cid or obj['owner'] != str(r2.ROOT)
            or state['Running'] or state['Paused'] or state['ExitCode'] != 1
            or state['OOMKilled']):
        raise RuntimeError('Exact r2 failed container identity changed')
    return dict(passed=True, accepted_games=32, r2_new_games=0,
                r1_prefix_sha256=matrix.digest(r2.PRIOR / 'dispatch.json'),
                r2_failure_sha256=matrix.digest(FAILURE_RECORD),
                checked_at=time.time())


def prepare():
    if ROOT.exists() or a.SOURCE != SOURCE_PARENT / 'code':
        raise RuntimeError('Fresh r3 source/output roots required; no overwrite')
    sha = a.cmd(['git', '-C', a.SOURCE, 'rev-parse', 'HEAD'])
    a.clean(a.SOURCE, sha)
    a.clean(a.ORCH, a.ORCH_SHA)
    old = previous_failures()
    parents = pilot.parents()
    source = matrix.small(pilot.PARENTS['same-cp96'] / 'qwen-same/short/deployment.json')
    arms = {}
    for arm in ARMS:
        cfg = copy.deepcopy(source)
        cfg.update(runtime_sha=sha, controller_sha=sha, controller_source=str(a.SOURCE),
                   difficulty='CheatVision', run_prefix=PREFIX,
                   worker_hook='qwen_l8_hook.install', seed_protocol='same_uniform101',
                   seed_group_mode='same')
        arms[arm] = cfg
    ROOT.mkdir()
    for name in ('runs', 'cpu', 'tmp', 'tmp/task-home', 'tmp/cache', 'tmp/cuda-cache'):
        (ROOT / name).mkdir()
    a.cmd(['git', 'clone', '--quiet', '--shared', a.SOURCE, ROOT / 'runtime'])
    a.cmd(['git', '-C', ROOT / 'runtime', 'checkout', '--quiet', '--detach', sha])
    a.save(ROOT / 'deployment.json', dict(runtime_sha=sha, controller_sha=sha,
        controller_source=str(a.SOURCE), orchestration_sha=a.ORCH_SHA,
        arms=arms, stages=STAGES, games=[8]*len(STAGES), updates=[0]*len(STAGES),
        eval_seeds=SEEDS, wall_seconds=WALL_SECONDS, gpu_hours=32,
        output_limit_bytes=LIMIT, storage_roots=[str(x) for x in accounts(0)[0]['roots']],
        previous_accepted_games=32, r2_new_games=0, new_games=64, new_updates=0,
        first_dispatch_by=time.time()+2*3600, no_retry=True, no_training=True,
        successors_authorized=False, gpu_preflight_required=True,
        gpu_preflight_natural_games=0, level='L8', difficulty='CheatVision',
        port_mitigation='deferred low-port allocation inside Ray actor constructor',
        authorization='Sep25 user: one new 64-game r3 continuation; 197 eight GPUs serial, '
                      'zero updates, new 4h/32GPUh, six roots aggregate 32GiB; '
                      'no deletion, automatic retry or L8 RL'))
    a.save(ROOT / 'historical-boundary.json', old)
    a.save(ROOT / 'parent-acceptance.json', parents)


def cpu():
    pilot.cpu()
    for stage in STAGES:
        command = matrix.small(ROOT / 'cpu' / stage / 'effective_config.json')['command']
        if "+ray_init.runtime_env.env_vars.SC2_L8_RENDEZVOUS_LOW_PORT='1'" not in command:
            raise RuntimeError('Deferred low-port flag missing from real launcher')


def regressions(host_only=False):
    sys.path[:0] = [str(a.SOURCE / 'tests'), str(a.SOURCE / 'scripts')]
    if host_only:
        if Path('/.dockerenv').exists():
            raise RuntimeError('Host-only tests cannot run inside a container')
        names = ['test_l7_host_continuation197', 'test_host_stage197',
                 'test_storage_quiescent197', 'test_policy_credit_storage197',
                 'test_policy_credit_storage_coordination197']
    else:
        import torch
        names = ['test_qwen_l8_remainder3_197', 'test_qwen_l8_remainder197',
                 'test_qwen_heldout128197', 'test_feedback_eval',
                 'test_metric_precision', 'test_sc2_no_thinking_torch',
                 'test_sc2_action_support', 'test_sc2_reset_startup',
                 'test_sc2_generation_tokens', 'test_policy_credit_acceptance197']
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromNames(names))
    cuda = False if host_only else torch.cuda.is_initialized()
    cfg = matrix.small(ROOT / 'deployment.json')
    proof = dict(passed=result.wasSuccessful() and not result.skipped and not cuda,
        tests=result.testsRun, skips=len(result.skipped), cuda_initialized=cuda,
        host_only=host_only, runtime_sha=cfg['runtime_sha'], checked_at=time.time())
    a.save(ROOT / ('host-regressions.json' if host_only else 'regressions.json'), proof)
    if not proof['passed']:
        raise RuntimeError('Zero-skip CPU tests required')


def check_cpu():
    pilot.check_cpu()
    old = matrix.small(ROOT / 'historical-boundary.json')
    now = previous_failures()
    if (old['r1_prefix_sha256'] != now['r1_prefix_sha256']
            or old['r2_failure_sha256'] != now['r2_failure_sha256']):
        raise RuntimeError('Historical boundary changed after preparation')
    cfg = matrix.small(ROOT / 'deployment.json')
    if (cfg['stages'] != STAGES or cfg['storage_roots'] !=
            [str(x) for x in accounts(0)[0]['roots']]
            or cfg['new_games'] != 64 or cfg['previous_accepted_games'] != 32
            or cfg['r2_new_games'] != 0 or not cfg['no_retry']
            or not cfg['no_training'] or cfg['successors_authorized']
            or not cfg['gpu_preflight_required']):
        raise RuntimeError('Exact r3 continuation deployment mismatch')


def verify(stage):
    check_cpu()
    pilot.verify(stage)


def probe_docker():
    args = pilot.docker('stage', STAGES[0])
    args[args.index('--name') + 1] = PREFIX + '-gpu-preflight'
    args[-2:] = ['gpu-preflight']
    return args


def verify_probe(stage):
    if stage != 'gpu-preflight':
        raise RuntimeError('Unexpected GPU preflight stage')
    proof = matrix.small(ROOT / 'gpu-preflight' / 'gpu-preflight.json')
    if (not proof['passed'] or len(proof['ranks']) != 8
            or len({row['cuda_uuid'] for row in proof['ranks']}) != 8
            or proof['nccl_sums'] != [28.0] * 8
            or proof['model_loaded'] or proof['natural_games'] or proof['optimizer_updates']):
        raise RuntimeError('Eight distinct GPU identities and NCCL sum required')


def queue():
    check_cpu()
    with (ROOT / 'queue.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if (ROOT / 'queue-state.json').exists() or (ROOT / 'dispatch.json').exists():
            raise RuntimeError('Already queued/dispatched; no retry')
        state = dict(phase='checking-parents', completed=[], previous_accepted_games=32,
                     new_games=64, new_updates=0)
        try:
            a.save(ROOT / 'queue-state.json', state)
            a.save(ROOT / 'parent-admission.json', pilot.parents())
            previous_failures()
            pilot.admit('first', matrix.small(ROOT / 'deployment.json')['first_dispatch_by'])
            start = time.time()
            deadline = start + WALL_SECONDS
            a.save(ROOT / 'dispatch.json', dict(start=start, deadline=deadline,
                gpu_hours=32, previous_accepted_games=32, new_games=64, new_updates=0))
            state.update(phase='running-unverified', deadline=deadline)
            a.save(ROOT / 'queue-state.json', state)
            h.run_stages(['gpu-preflight'], lambda _: probe_docker(), verify_probe,
                accounts(deadline), ROOT, ROOT / 'gpu-preflight-supervision', ROOT,
                deadline, admit=lambda _: pilot.admit('gpu-preflight', deadline))
            terminal = h.run_stages(STAGES, lambda s: pilot.docker('stage', s),
                verify, accounts(deadline), ROOT, ROOT / 'host-supervision',
                ROOT, deadline, admit=lambda s: pilot.admit(s, deadline))
            a.save(ROOT / 'state.json', terminal)
            state.update(phase='completed', exit_code=0, completed=STAGES,
                         finished_at=time.time())
            a.save(ROOT / 'queue-state.json', state)
        except BaseException as exc:
            state.update(phase='failed', error_type=type(exc).__name__,
                         error=str(exc), finished_at=time.time())
            a.save(ROOT / 'queue-state.json', state)
            raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['prepare', 'cpu', 'regressions',
        'host-regressions', 'cpu-command', 'regressions-command', 'queue', 'stage',
        'gpu-preflight'])
    parser.add_argument('stage', nargs='?')
    cli = parser.parse_args()
    configure()
    if cli.mode.endswith('-command'):
        print(json.dumps(pilot.docker(cli.mode.removesuffix('-command'))))
    elif cli.mode == 'host-regressions':
        regressions(True)
    elif cli.mode == 'stage':
        pilot.child_stage(cli.stage)
    elif cli.mode == 'gpu-preflight':
        import qwen_l8_cuda_probe
        qwen_l8_cuda_probe.run(ROOT / 'gpu-preflight', ROOT / 'tmp/probe-ray')
    else:
        globals()[cli.mode]()
