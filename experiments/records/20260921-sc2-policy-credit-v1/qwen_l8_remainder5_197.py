"""One authorized r5 attempt of the 64 still-unrun Qwen L8 evaluation games."""
import argparse
import copy
import fcntl
import json
from pathlib import Path
import sys
import time
import unittest

import acceptance197 as a
import host_stage197 as h
import l7_matrix256197 as matrix
import qwen_l8_pilot197 as pilot
import qwen_l8_remainder197 as r2
import qwen_l8_remainder3_197 as r3
import qwen_l8_remainder4_197 as r4
from qwen_l8_plan import ARMS, SEEDS, STAGES as ALL_STAGES

ROOT = Path('/var/jfsCache/sc2-qwen-l8-pilot96-197-20260926-r5')
SOURCE_PARENT = Path('/var/jfsCache/sc2-qwen-l8-pilot96-197-source-20260926-r5')
PREFIX = 'sc2-qwen-l8-pilot96-197-20260926-r5'
STAGES = ALL_STAGES[4:]
WALL_SECONDS = 4 * 3600
LIMIT = 32 * a.GIB
R4_FAILURE_RECORD = a.HERE / 'qwen-l8-pilot-r4-failure-20260925.json'
FEEDBACK = 'experiments/records/20260911-execution-failure-feedback-v1'


def accounts(deadline):
    return [dict(roots=[r2.PRIOR, r2.PRIOR_SOURCE, r2.ROOT, r2.SOURCE_PARENT,
                        r3.ROOT, r3.SOURCE_PARENT, r4.ROOT, r4.SOURCE_PARENT,
                        ROOT, SOURCE_PARENT],
                 receipt_root=ROOT, limit=LIMIT, deadline=deadline)]


def configure():
    pilot.ROOT, pilot.SOURCE_PARENT, pilot.PREFIX = ROOT, SOURCE_PARENT, PREFIX
    pilot.STAGES, pilot.PRIOR_ACCEPTANCE_ROOT = STAGES, r2.PRIOR
    pilot.accounts, pilot.invocation = accounts, r3.invocation
    a.ROOT = a.STORAGE_LOCK_ROOT = ROOT
    a.CONTAINER = PREFIX
    a.DOCKER_SCRIPT = a.HERE / 'qwen_l8_remainder5_197.py'
    if (ROOT / 'deployment.json').exists():
        a.RUNTIME_SHA = matrix.small(ROOT / 'deployment.json')['runtime_sha']


def previous_failures():
    old = r4.previous_failures()  # The r1 32-game prefix; r2/r3 added zero.
    proof = matrix.small(R4_FAILURE_RECORD)
    deployment = matrix.small(r4.ROOT / 'deployment.json')
    queue = matrix.small(r4.ROOT / 'queue-state.json')
    supervisor = matrix.small(r4.ROOT / 'gpu-preflight-supervision/state.json')
    if (proof['runtime_sha'] != deployment['runtime_sha']
            or proof['root'] != str(r4.ROOT)
            or proof['scope']['r4_new_games'] != 0
            or proof['scope']['retained_r1_accepted_games'] != 32
            or queue['phase'] != 'failed' or supervisor['phase'] != 'failed'
            or supervisor['completed'] or (r4.ROOT / 'host-supervision').exists()
            or any((r4.ROOT / f'acceptance-{stage}.json').exists() for stage in STAGES)
            or any((r4.ROOT / 'runs' / stage / 'result.json').exists() for stage in STAGES)):
        raise RuntimeError('r4 zero-game preflight failure or prior prefix changed')
    a.clean(r4.ROOT / 'runtime', proof['runtime_sha'])
    a.clean(r4.SOURCE_PARENT / 'code', proof['runtime_sha'])
    for rel, expected in proof['terminal_sha256'].items():
        if matrix.digest(r4.ROOT / rel) != expected:
            raise RuntimeError('r4 terminal receipt changed: ' + rel)
    if matrix.digest(r4.ROOT / 'gpu-preflight/entry.log') != proof['preflight']['entry_log_sha256']:
        raise RuntimeError('r4 bounded entry diagnostic changed')
    cid = proof['preflight']['container_id']
    obj = json.loads(a.cmd(['docker', 'inspect', '--format',
        '{"id":"{{.Id}}","owner":"{{index .Config.Labels "sc2.acceptance.root"}}",'
        '"state":{{json .State}}}', cid]))
    state = obj['state']
    if (obj['id'] != cid or obj['owner'] != str(r4.ROOT)
            or state['Running'] or state['Paused'] or state['ExitCode'] != 1
            or state['OOMKilled']):
        raise RuntimeError('Exact r4 failed preflight container changed')
    return dict(passed=True, accepted_games=32, r2_new_games=0, r3_new_games=0,
                r4_new_games=0, r1_dispatch_sha256=old['r1_dispatch_sha256'],
                r2_failure_sha256=old['r2_failure_sha256'],
                r3_failure_sha256=old['r3_failure_sha256'],
                r4_failure_sha256=matrix.digest(R4_FAILURE_RECORD),
                checked_at=time.time())


def prepare():
    if ROOT.exists() or a.SOURCE != SOURCE_PARENT / 'code':
        raise RuntimeError('Fresh r5 source/output roots required; no overwrite')
    sha = a.cmd(['git', '-C', a.SOURCE, 'rev-parse', 'HEAD'])
    a.clean(a.SOURCE, sha)
    a.clean(a.ORCH, a.ORCH_SHA)
    history = previous_failures()
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
        arms=arms, stages=STAGES, games=[8] * len(STAGES), updates=[0] * len(STAGES),
        eval_seeds=SEEDS, wall_seconds=WALL_SECONDS, gpu_hours=32,
        output_limit_bytes=LIMIT, storage_roots=[str(x) for x in accounts(0)[0]['roots']],
        previous_accepted_games=32, r2_new_games=0, r3_new_games=0, r4_new_games=0,
        new_games=64, new_updates=0, first_dispatch_by=time.time() + 2 * 3600,
        no_retry=True, no_training=True, successors_authorized=False,
        gpu_preflight_required=True, cpu_ray_hook_preflight_required=True,
        gpu_preflight_natural_games=0, gpu_preflight_ray_tmp='/tmp/probe-ray',
        level='L8', difficulty='CheatVision',
        port_mitigation='deferred low-port allocation inside Ray actor constructor',
        authorization='Sep26 user: one new r5 attempt of remaining64 L8 games; '
                      '197 eight GPUs serial,zero updates,new4h/32GPUh,ten roots/32GiB; '
                      'no deletion,automatic retry or L8 RL'))
    a.save(ROOT / 'historical-boundary.json', history)
    a.save(ROOT / 'parent-acceptance.json', parents)


def probe_pythonpath():
    resolved = matrix.small(ROOT / 'cpu' / STAGES[0] / 'resolved_config.json')
    value = resolved['ray_init']['runtime_env']['env_vars']['PYTHONPATH']
    paths = value.split(':')
    if (paths[0] != str(ROOT / 'runtime')
            or str(ROOT / 'runtime' / FEEDBACK) not in paths
            or str(a.HERE) not in paths):
        raise RuntimeError('Actual launcher Ray PYTHONPATH lacks required frozen modules')
    return value


def cpu():
    pilot.cpu()
    for stage in STAGES:
        command = matrix.small(ROOT / 'cpu' / stage / 'effective_config.json')['command']
        if "+ray_init.runtime_env.env_vars.SC2_L8_RENDEZVOUS_LOW_PORT='1'" not in command:
            raise RuntimeError('Deferred low-port flag missing from real launcher')
    probe_pythonpath()


def regressions(host_only=False):
    sys.path[:0] = [str(a.SOURCE / 'tests'), str(a.SOURCE / 'scripts')]
    if host_only:
        if Path('/.dockerenv').exists():
            raise RuntimeError('Host-only tests cannot run inside container')
        names = ['test_l7_host_continuation197', 'test_host_stage197',
                 'test_storage_quiescent197', 'test_policy_credit_storage197',
                 'test_policy_credit_storage_coordination197']
    else:
        import torch
        names = ['test_qwen_l8_remainder5_197', 'test_qwen_l8_remainder4_197',
                 'test_qwen_l8_remainder3_197', 'test_qwen_l8_remainder197',
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


def cpu_hook():
    import qwen_l8_cuda_probe
    qwen_l8_cuda_probe.check_hook_cpu(ROOT / 'cpu/ray-hook', Path('/tmp/ray-hook'),
                                      probe_pythonpath())


def check_cpu():
    pilot.check_cpu()
    old = matrix.small(ROOT / 'historical-boundary.json')
    now = previous_failures()
    if any(old[key] != now[key] for key in
           ('r1_dispatch_sha256', 'r2_failure_sha256',
            'r3_failure_sha256', 'r4_failure_sha256')):
        raise RuntimeError('Historical boundary changed after preparation')
    cfg = matrix.small(ROOT / 'deployment.json')
    proof = matrix.small(ROOT / 'cpu/ray-hook/cpu-hook-preflight.json')
    if (cfg['stages'] != STAGES or cfg['storage_roots'] !=
            [str(x) for x in accounts(0)[0]['roots']]
            or cfg['new_games'] != 64 or cfg['previous_accepted_games'] != 32
            or any(cfg[f'r{n}_new_games'] != 0 for n in (2, 3, 4))
            or not cfg['no_retry'] or not cfg['no_training']
            or cfg['successors_authorized'] or not cfg['gpu_preflight_required']
            or not cfg['cpu_ray_hook_preflight_required']
            or cfg['gpu_preflight_ray_tmp'] != '/tmp/probe-ray'
            or not proof['passed'] or proof['natural_games'] or proof['optimizer_updates']
            or proof['model_loaded'] or proof['ray_pythonpath'] != probe_pythonpath()
            or proof['worker']['cuda_initialized'] or proof['worker']['cuda_device_count']):
        raise RuntimeError('Exact r5 CPU/Ray continuation proof mismatch')


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
    proof = matrix.small(ROOT / 'gpu-preflight/gpu-preflight.json')
    if (not proof['passed'] or len(proof['ranks']) != 8
            or len({row['cuda_uuid'] for row in proof['ranks']}) != 8
            or proof['nccl_sums'] != [28.0] * 8
            or proof['model_loaded'] or proof['natural_games'] or proof['optimizer_updates']):
        raise RuntimeError('Eight distinct GPUs and successful NCCL sum required')


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
            start = time.time(); deadline = start + WALL_SECONDS
            a.save(ROOT / 'dispatch.json', dict(start=start, deadline=deadline,
                gpu_hours=32, previous_accepted_games=32, new_games=64, new_updates=0))
            state.update(phase='running-unverified', deadline=deadline)
            a.save(ROOT / 'queue-state.json', state)
            h.run_stages(['gpu-preflight'], lambda _: probe_docker(), verify_probe,
                accounts(deadline), ROOT, ROOT / 'gpu-preflight-supervision', ROOT,
                deadline, admit=lambda _: pilot.admit('gpu-preflight', deadline))
            terminal = h.run_stages(STAGES, lambda s: pilot.docker('stage', s), verify,
                accounts(deadline), ROOT, ROOT / 'host-supervision', ROOT, deadline,
                admit=lambda s: pilot.admit(s, deadline))
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
        'host-regressions', 'cpu-command', 'regressions-command',
        'cpu-hook-command', 'cpu-hook', 'queue', 'stage', 'gpu-preflight'])
    parser.add_argument('stage', nargs='?')
    cli = parser.parse_args(); configure()
    if cli.mode.endswith('-command'):
        print(json.dumps(pilot.docker(cli.mode.removesuffix('-command'))))
    elif cli.mode == 'host-regressions':
        regressions(True)
    elif cli.mode == 'stage':
        pilot.child_stage(cli.stage)
    elif cli.mode == 'gpu-preflight':
        import qwen_l8_cuda_probe
        qwen_l8_cuda_probe.run(ROOT / 'gpu-preflight', Path('/tmp/probe-ray'),
                               probe_pythonpath())
    else:
        globals()[cli.mode]()
