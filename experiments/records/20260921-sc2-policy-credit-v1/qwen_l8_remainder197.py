"""One-shot continuation of the approved L8 screen; only the eight unrun stages."""
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

import acceptance197 as a
import host_stage197 as h
import l7_matrix256197 as matrix
import qwen_l8_pilot197 as pilot
from qwen_l8_plan import ARMS, SEEDS, STAGES as ALL_STAGES, stage_spec

PRIOR = Path('/var/jfsCache/sc2-qwen-l8-pilot96-197-20260925-r1')
PRIOR_SOURCE = Path('/var/jfsCache/sc2-qwen-l8-pilot96-197-source-20260925-r1')
ROOT = Path('/var/jfsCache/sc2-qwen-l8-pilot96-197-20260925-r2')
SOURCE_PARENT = Path('/var/jfsCache/sc2-qwen-l8-pilot96-197-source-20260925-r2')
PREFIX = 'sc2-qwen-l8-pilot96-197-20260925-r2'
ORIGINAL_SHA = '9f8def125acf984dc98b6b797d5a8b02da7eae29'
ORIGINAL_START = 1790329988.5255494
DEADLINE = 1790344388.5255494
STAGES = ALL_STAGES[4:]
LIMIT = 32*a.GIB
BASE_INVOCATION = pilot.invocation


def accounts(deadline=DEADLINE):
    if deadline != DEADLINE:
        raise RuntimeError('L8 original absolute deadline cannot be reset')
    return [dict(roots=[PRIOR, PRIOR_SOURCE, ROOT, SOURCE_PARENT],
                 receipt_root=ROOT, limit=LIMIT, deadline=DEADLINE)]


def invocation(deployment, stage, dry=False):
    args, env, out = BASE_INVOCATION(deployment, stage, dry)
    if stage not in STAGES:
        raise RuntimeError('Only the eight remaining L8 stages are authorized')
    args.append("+ray_init.runtime_env.env_vars.SC2_L8_RENDEZVOUS_LOW_PORT='1'")
    return args, env, out


def configure():
    pilot.ROOT, pilot.SOURCE_PARENT, pilot.PREFIX = ROOT, SOURCE_PARENT, PREFIX
    pilot.STAGES, pilot.PRIOR_ACCEPTANCE_ROOT = STAGES, PRIOR
    pilot.accounts, pilot.invocation = accounts, invocation
    pilot.configure()
    a.DOCKER_SCRIPT = a.HERE/'qwen_l8_remainder197.py'


def accepted_prefix():
    """Read only small terminal evidence; never rehabilitate the failed r1 queue."""
    old = matrix.small(PRIOR/'deployment.json')
    dispatch = matrix.small(PRIOR/'dispatch.json')
    queue = matrix.small(PRIOR/'queue-state.json')
    host = matrix.small(PRIOR/'host-supervision/state.json')
    if (old['runtime_sha'] != ORIGINAL_SHA or old['stages'] != ALL_STAGES
            or old['eval_seeds'] != SEEDS or old['new_updates'] != 0
            or old['difficulty'] != 'CheatVision'
            or dispatch['start'] != ORIGINAL_START or dispatch['deadline'] != DEADLINE
            or dispatch['new_games'] != 96 or dispatch['gpu_hours'] != 32
            or queue['phase'] != 'failed' or host['phase'] != 'failed'
            or host['completed'] != ALL_STAGES[:4] or host['stage'] != ALL_STAGES[4]
            or host['deadline'] != DEADLINE):
        raise RuntimeError('Original failed queue/accepted prefix identity mismatch')
    a.clean(PRIOR/'runtime', ORIGINAL_SHA)
    hashes = {}
    for stage in ALL_STAGES[:4]:
        matrix.terminal_container(PRIOR, stage, DEADLINE)
        out = PRIOR/'runs'/stage
        result = matrix.small(out/'result.json')
        acceptance = matrix.small(PRIOR/f'acceptance-{stage}.json')
        manifest = matrix.small(out/'manifest.json')
        load = matrix.small(out/'checkpoint_evaluation.json')
        spec = stage_spec(stage)
        if (result != matrix.small(out/'.done') or acceptance['result'] != result
                or result['status'] != 'completed' or result['process_exit_code'] != 0
                or result['training_updates'] != 0 or not result['metrics_finite']
                or result['metrics_precision'] != 'binary64-v1'
                or result['episode_outcomes']['natural_games'] != 8
                or result['episode_outcomes']['truncated'] != 0
                or result['evaluable_action_count'] <= 0
                or result['evaluable_action_count'] != result['valid_evaluable_action_count']
                or manifest['dirty'] or manifest['source_commit'] != ORIGINAL_SHA
                or manifest['world_size'] != 8 or manifest['metrics_precision'] != 'binary64-v1'
                or acceptance['seeds'] != spec['seeds'] or len(acceptance['rng']) != 8
                or load['game_seeds'] != spec['seeds'] or not load['val_only']
                or load['optimizer_updates'] != 0
                or load['loaded_global_step'] != spec['expected_step']):
            raise RuntimeError('Original stage no longer matches accepted L8 evidence: '+stage)
        for rel in (f'runs/{stage}/result.json', f'runs/{stage}/.done',
                    f'acceptance-{stage}.json',
                    f'host-supervision/{stage}-guardian.json'):
            hashes[rel] = matrix.digest(PRIOR/rel)
    failed = matrix.small(PRIOR/'runs'/ALL_STAGES[4]/'result.json')
    if (failed != matrix.small(PRIOR/'runs'/ALL_STAGES[4]/'.done')
            or failed['status'] != 'failed' or failed['process_exit_code'] != 1
            or failed['episode_outcomes']['natural_games'] != 0
            or (PRIOR/f'acceptance-{ALL_STAGES[4]}.json').exists()):
        raise RuntimeError('Failed stage must contain no accepted natural games')
    return dict(passed=True, original_root=str(PRIOR), original_runtime_sha=ORIGINAL_SHA,
                failed_stage=ALL_STAGES[4], accepted_stages=ALL_STAGES[:4],
                accepted_games=32, receipt_sha256=hashes,
                original_dispatch_sha256=matrix.digest(PRIOR/'dispatch.json'),
                checked_at=time.time())


def check_prefix(expected):
    proof = accepted_prefix()
    if (proof['receipt_sha256'] != expected['receipt_sha256']
            or proof['original_dispatch_sha256'] != expected['original_dispatch_sha256']):
        raise RuntimeError('Accepted 32-game prefix changed')


def prepare():
    if ROOT.exists() or a.SOURCE != SOURCE_PARENT/'code' or time.time() >= DEADLINE-45:
        raise RuntimeError('Fresh r2 roots and unexpired original deadline required')
    sha = a.cmd(['git', '-C', a.SOURCE, 'rev-parse', 'HEAD'])
    a.clean(a.SOURCE, sha)
    a.clean(a.ORCH, a.ORCH_SHA)
    prefix = accepted_prefix()
    parents = pilot.parents()
    source = matrix.small(pilot.PARENTS['same-cp96']/'qwen-same/short/deployment.json')
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
        (ROOT/name).mkdir()
    a.cmd(['git', 'clone', '--quiet', '--shared', a.SOURCE, ROOT/'runtime'])
    a.cmd(['git', '-C', ROOT/'runtime', 'checkout', '--quiet', '--detach', sha])
    a.save(ROOT/'deployment.json', dict(runtime_sha=sha, controller_sha=sha,
        controller_source=str(a.SOURCE), orchestration_sha=a.ORCH_SHA, arms=arms,
        stages=STAGES, games=[8]*len(STAGES), updates=[0]*len(STAGES),
        eval_seeds=SEEDS, original_dispatch_start=ORIGINAL_START,
        deadline=DEADLINE, gpu_hours_total=32, output_limit_bytes=LIMIT,
        storage_roots=[str(x) for x in accounts()[0]['roots']],
        previous_accepted_games=32, new_games=64, new_updates=0,
        no_retry=True, no_training=True, successors_authorized=False,
        level='L8', difficulty='CheatVision', port_mitigation='opt-in low non-ephemeral port ledger',
        authorization='Sep25 user: once-only continuation of remaining 64 L8 games, existing 21:53:08.526 cutoff, aggregate 32GPUh/32GiB, no retry or L8 training',
        seed_plan_sha256=matrix.digest(a.HERE/'qwen_l8_plan.py')))
    a.save(ROOT/'original-prefix-acceptance.json', prefix)
    a.save(ROOT/'parent-acceptance.json', parents)


def cpu():
    pilot.cpu()
    for stage in STAGES:
        eff = matrix.small(ROOT/'cpu'/stage/'effective_config.json')['command']
        if "+ray_init.runtime_env.env_vars.SC2_L8_RENDEZVOUS_LOW_PORT='1'" not in eff:
            raise RuntimeError('R2 port mitigation missing from real launcher')


def regressions(host_only=False):
    sys.path[:0] = [str(a.SOURCE/'tests'), str(a.SOURCE/'scripts')]
    if host_only:
        if Path('/.dockerenv').exists():
            raise RuntimeError('Actual host tests required')
        names = ['test_l7_host_continuation197', 'test_host_stage197',
                 'test_storage_quiescent197', 'test_policy_credit_storage197',
                 'test_policy_credit_storage_coordination197']
    else:
        import torch
        names = ['test_qwen_l8_remainder197', 'test_qwen_heldout128197',
                 'test_feedback_eval', 'test_metric_precision',
                 'test_sc2_no_thinking_torch', 'test_sc2_action_support',
                 'test_sc2_reset_startup', 'test_sc2_generation_tokens',
                 'test_policy_credit_acceptance197']
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromNames(names))
    cuda = False if host_only else torch.cuda.is_initialized()
    proof = dict(passed=result.wasSuccessful() and not result.skipped and not cuda,
                 tests=result.testsRun, skips=len(result.skipped), cuda_initialized=cuda,
                 host_only=host_only, runtime_sha=matrix.small(ROOT/'deployment.json')['runtime_sha'],
                 checked_at=time.time())
    a.save(ROOT/('host-regressions.json' if host_only else 'regressions.json'), proof)
    if not proof['passed']:
        raise RuntimeError('Zero-skip CPU tests required')


def check_cpu():
    pilot.check_cpu()
    prefix = matrix.small(ROOT/'original-prefix-acceptance.json')
    check_prefix(prefix)
    cfg = matrix.small(ROOT/'deployment.json')
    if (cfg['stages'] != STAGES or cfg['deadline'] != DEADLINE
            or cfg['storage_roots'] != [str(x) for x in accounts()[0]['roots']]
            or cfg['new_games'] != 64 or cfg['previous_accepted_games'] != 32
            or not cfg['no_retry'] or not cfg['no_training']
            or cfg['successors_authorized']):
        raise RuntimeError('R2 exact continuation deployment mismatch')


def verify(stage):
    check_prefix(matrix.small(ROOT/'original-prefix-acceptance.json'))
    pilot.verify(stage)


def queue():
    check_cpu()
    with (ROOT/'queue.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (ROOT/'queue-state.json').exists() or (ROOT/'dispatch.json').exists():
            raise RuntimeError('Already queued/dispatched; no retry')
        state = dict(phase='checking-parents', completed=[], previous_accepted_games=32,
                     new_games=64, new_updates=0, deadline=DEADLINE)
        try:
            a.save(ROOT/'queue-state.json', state)
            a.save(ROOT/'parent-admission.json', pilot.parents())
            check_prefix(matrix.small(ROOT/'original-prefix-acceptance.json'))
            pilot.admit('first', DEADLINE)
            a.save(ROOT/'dispatch.json', dict(start=ORIGINAL_START, deadline=DEADLINE,
                continuation_at=time.time(), gpu_hours_total=32,
                previous_accepted_games=32, new_games=64, new_updates=0))
            state['phase'] = 'running-unverified'
            a.save(ROOT/'queue-state.json', state)
            terminal = h.run_stages(STAGES, lambda s:pilot.docker('stage', s),
                verify, accounts(), ROOT, ROOT/'host-supervision', ROOT, DEADLINE,
                admit=lambda s:pilot.admit(s, DEADLINE))
            a.save(ROOT/'state.json', terminal)
            state.update(phase='completed', exit_code=0, completed=STAGES,
                         finished_at=time.time())
            a.save(ROOT/'queue-state.json', state)
        except BaseException as exc:
            state.update(phase='failed', error_type=type(exc).__name__,
                         error=str(exc), finished_at=time.time())
            a.save(ROOT/'queue-state.json', state)
            raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['prepare', 'cpu', 'regressions',
        'host-regressions', 'cpu-command', 'regressions-command', 'queue', 'stage'])
    parser.add_argument('stage', nargs='?')
    cli = parser.parse_args()
    configure()
    if cli.mode.endswith('-command'):
        print(json.dumps(pilot.docker(cli.mode.removesuffix('-command'))))
    elif cli.mode == 'host-regressions':
        regressions(True)
    elif cli.mode == 'stage':
        pilot.child_stage(cli.stage)
    else:
        globals()[cli.mode]()
