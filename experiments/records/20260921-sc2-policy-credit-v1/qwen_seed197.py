"""Four authorized Qwen short arms, serial after the frozen SpB repair acceptance.

Reuses the bounded three-stage acceptance engine. Each GPU child selects exactly
one explicit arm context; no concurrent mutable contexts or historical edits.
"""
import argparse
import copy
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess as sp
import sys
import time

import acceptance197 as engine

HERE, SOURCE = engine.HERE, engine.SOURCE
sys.path.insert(0, str(SOURCE))  # Host entry must work outside the repository cwd.
SUITE = Path('/var/jfsCache/sc2-qwen-seeds197-20260921-r2')
SPB = Path('/var/jfsCache/sc2-policy-credit197-20260921-r2')
MODEL = Path('/var/jfsCache/sc2-qwen-instruct2507-cdbee75-20260921-r1/model')
CPU_MODEL = Path('/data/yangjinyue/new-scii-qwen-instruct2507-level5-v1/staging/Qwen3-4B-Instruct-2507-download-cdbee75')
SPB_RUNTIME = 'f211c0e94603468992baa514f00aaee5fd7780d6'
RUN_PREFIX = 'qwen-seeds197-r2'
CONTAINER_PREFIX = 'sc2-qwen-seeds197-20260921-r2-'
DOCKER_SCRIPT = HERE / 'qwen_seed197.py'
SPB_METADATA = Path('/var/jfsCache/sc2-generation-tokens-cpu-20260921.2O3Eqc/spb-metadata')
PRIOR_ROOTS = [Path('/var/jfsCache/sc2-qwen-seeds197-20260921-r1'),
               Path('/var/jfsCache/sc2-qwen-seeds197-source-20260921-r1')]
SPB_MASK, SPB_TOKENIZER = engine.MASK_SHA, engine.TOKENIZER_SHA
ARMS = [('l6-same', 'Harder', 'same_uniform101', 'same'),
        ('l6-random', 'Harder', 'independent_uniform101', 'mixed_seed_ablation'),
        ('l7-same', 'VeryHard', 'same_uniform101', 'same'),
        ('l7-random', 'VeryHard', 'independent_uniform101', 'mixed_seed_ablation')]
DEFAULT_ARMS = tuple(ARMS)
REUSED_ARM_ROOT = None
AUTHORIZATION = ('User approved four Qwen Level6/7 same/random-seed short acceptances; '
                 '32 games and <=2h/16GPUh each, total <=64GPUh; no long promotion')
# SpB latest queue admission + its 2h budget + 1h resource wait. No stale future launch.
FIRST_DISPATCH_BY = 1790028940.699252  # 2026-09-22 06:15:40 Beijing
WALL_SECONDS = 8 * 3600
LIMIT = 512 * engine.GIB
read, cmd, clean = engine.read, engine.cmd, engine.clean


def save(path, data):
    # Also correct before arm selection and while read-only predecessor checks
    # temporarily select the SpB context. Never write a lock into that old run.
    engine.save(path, data, lock_root=SUITE)


def arm_config(base, index):
    from agent_system.sc2_seed_protocol import ablation_seeds
    tag, difficulty, protocol, group_mode = ARMS[index]
    cfg = copy.deepcopy(base)
    cfg.update(model_kind='qwen', model_mount='/assets/qwen', difficulty=difficulty,
               run_prefix=f'{RUN_PREFIX}-{tag}', seed_protocol=protocol,
               seed_group_mode=group_mode, stages=['pre', 'train2', 'post'],
               games=[8, 16, 8], updates=[0, 2, 0], wall_seconds=7200, gpu_hours=16,
               output_limit_bytes=128*engine.GIB,
               training_seeds=[ablation_seeds(protocol, 0, step, 1, 8) for step in range(2)])
    cfg['environment']['MODEL_PATH'] = '/assets/qwen'
    cfg['host']['model'] = str(MODEL)
    return cfg


def select_arm(index):
    tag = ARMS[index][0]
    engine.ROOT = SUITE / tag
    engine.STORAGE_LOCK_ROOT = SUITE
    cfg = read(engine.ROOT / 'deployment.json')
    engine.RUNTIME_SHA = cfg['runtime_sha']
    engine.CONTAINER = CONTAINER_PREFIX + tag
    engine.TRAIN_SEEDS = cfg['training_seeds']
    engine.MASK_SHA = cfg.get('mask_sha256', SPB_MASK)
    engine.TOKENIZER_SHA = cfg.get('tokenizer_sha256', SPB_TOKENIZER)
    return cfg


def prepare():
    sha = cmd(['git', '-C', SOURCE, 'rev-parse', 'HEAD'])
    clean(SOURCE, sha)
    clean(engine.ORCH, engine.ORCH_SHA)
    if SUITE.exists():
        raise RuntimeError('Fresh suite root required; no overwrite or automatic retry')
    if not (CPU_MODEL / 'config.json').is_file():
        raise RuntimeError('Registered Instruct-2507 metadata required for CPU preparation')
    base = read(SPB / 'deployment.json')
    base.update(runtime_sha=sha, controller_sha=sha, controller_source=str(SOURCE),
                predecessor=str(SPB), eval_seeds=engine.EVAL_SEEDS,
                authorization=AUTHORIZATION)
    configs = [arm_config(base, index) for index in range(len(ARMS))]
    SUITE.mkdir()
    cmd(['git', 'clone', '--quiet', '--shared', SOURCE, SUITE / 'runtime'])
    cmd(['git', '-C', SUITE / 'runtime', 'checkout', '--quiet', '--detach', sha])
    clean(SUITE / 'runtime', sha)
    save(SUITE / 'deployment.json', dict(runtime_sha=sha, controller_sha=sha,
         controller_source=str(SOURCE), predecessor=str(SPB), arms=[x[0] for x in ARMS],
         games=32*len(ARMS), training_steps=2*len(ARMS), gpu_hours=16*len(ARMS), wall_seconds=WALL_SECONDS,
         output_limit_bytes=LIMIT, first_dispatch_by=FIRST_DISPATCH_BY,
         no_retry=True, no_long_training=True, authorization=base['authorization'],
         reused_completed_arm=str(REUSED_ARM_ROOT) if REUSED_ARM_ROOT else None))
    for index, (tag, *_) in enumerate(ARMS):
        root = SUITE / tag
        root.mkdir()
        for name in ('runs', 'cpu', 'tmp'):
            (root / name).mkdir()
        (root / 'runtime').symlink_to(SUITE / 'runtime', target_is_directory=True)
        save(root / 'deployment.json', configs[index])


def docker(mode, index):
    select_arm(index)
    args = engine.docker('cpu' if mode in ('cpu', 'regressions') else 'execute')
    if mode in ('cpu', 'regressions'):
        args[args.index(f'{MODEL}:/assets/qwen:ro')] = f'{CPU_MODEL}:/assets/qwen:ro'
    if mode == 'regressions':
        args[args.index('--name')+1] += '-regressions'
        args[2:2] = ['-v', f'{SPB_METADATA}:/metadata/spb:ro',
                     '-e', 'SC2_TEST_SPB_METADATA_PATH=/metadata/spb',
                     '-e', 'SC2_TEST_QWEN_METADATA_PATH=/assets/qwen',
                     '-e', 'OMP_NUM_THREADS=2', '-e', 'TOKENIZERS_PARALLELISM=false']
    # Engine has all common read-only mounts and exact owned-root labels.
    # Add only this suite's shared source snapshot, read-only for every child.
    # Bind only the stable coordination inode, not writable access to other arms.
    args[2:2] = ['-v', f'{SUITE}/runtime:{SUITE}/runtime:ro',
                 '--mount', f'type=bind,src={SUITE}/.storage.lock,dst={SUITE}/.storage.lock']
    args[-2:] = [str(DOCKER_SCRIPT), 'arm-' + mode, str(index)]
    return args


def regressions(index):
    import unittest
    import torch
    cfg = select_arm(index)
    sys.path.insert(0, str(SOURCE / 'tests'))
    os.environ['SC2_TEST_TOKENIZER_PATH'] = '/assets/qwen'
    names = ['test_sc2_action_support', 'test_sc2_policy_credit', 'test_sc2_task_signal',
             'test_sc2_no_thinking_torch', 'test_thinking_action_boundary',
             'test_r6_format_reward', 'test_original_bo_segment', 'test_original_game_seeds',
             'test_policy_credit_acceptance197', 'test_qwen_seed_acceptance197',
             'test_sc2_generation_tokens', 'test_policy_credit_storage197',
             'test_qwen_seed_acceptance197_r3', 'test_policy_credit_storage_coordination197',
             'test_qwen_seed_acceptance197_r4']
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromNames(names))
    passed = result.wasSuccessful() and not result.skipped and not torch.cuda.is_initialized()
    save(engine.ROOT / 'regressions.json', dict(passed=passed, tests=result.testsRun,
         skips=len(result.skipped), cuda_initialized=torch.cuda.is_initialized(),
         runtime_sha=cfg['runtime_sha'], checked_at=time.time()))
    if not passed:
        raise RuntimeError('CPU regressions failed; no queue')


def cpu(index):
    import torch
    from transformers import AutoConfig
    from verl.utils.sc2_action_support import load_support
    from verl.utils.sc2_no_thinking import load_constraint
    cfg = select_arm(index)
    model = '/assets/qwen'
    architecture = AutoConfig.from_pretrained(model, local_files_only=True)
    if architecture.architectures != ['Qwen3ForCausalLM']:
        raise RuntimeError('Wrong model architecture')
    support = load_support(model, 192)
    mask = load_constraint(model).proof()['support_mask_sha256']
    tokenizer_sha = hashlib.sha256(support.tokenizer.backend_tokenizer.to_str().encode()).hexdigest()
    # Hash metadata only here. Native launcher checks every registered weight at real preflight.
    for line in (SOURCE / 'configs/qwen3-4b-instruct-2507.sha256').read_text().splitlines():
        expected, name = line.split(None, 1)
        if not name.endswith('.safetensors'):
            if hashlib.sha256((Path(model) / name).read_bytes()).hexdigest() != expected:
                raise RuntimeError('Wrong Qwen metadata: ' + name)
    cfg.update(mask_sha256=mask, tokenizer_sha256=tokenizer_sha)
    save(engine.ROOT / 'deployment.json', cfg)  # preparation only, before frozen readiness/queue
    select_arm(index)
    engine.cpu()
    for stage in cfg['stages']:
        resolved = read(engine.ROOT / 'cpu' / stage / 'resolved_config.json')
        env = resolved['ray_init']['runtime_env']['env_vars']
        if (resolved['actor_rollout_ref']['model']['path'] != model
                or env['SC2_DIFFICULTY'] != cfg['difficulty']
                or env['SC2_TRAIN_SEED_PROTOCOL'] != cfg['seed_protocol']
                or resolved['algorithm']['sc2_policy_credit']['seed_group_mode'] != cfg['seed_group_mode']):
            raise RuntimeError('Qwen arm effective configuration mismatch')
    if torch.cuda.is_initialized():
        raise RuntimeError('CPU preflight initialized CUDA')
    proof = read(engine.ROOT / 'readiness.json')
    proof['qwen_arm_verified'] = True
    save(engine.ROOT / 'readiness.json', proof)


def predecessor_complete():
    # Restore original frozen acceptance context, only for read-only revalidation.
    engine.ROOT, engine.RUNTIME_SHA = SPB, SPB_RUNTIME
    engine.TRAIN_SEEDS = [[2732]*8, [43567]*8]
    engine.TOKENIZER_SHA, engine.MASK_SHA = SPB_TOKENIZER, SPB_MASK
    queue = read(SPB / 'queue-state.json')
    if queue['phase'] in ('failed', 'expired'):
        raise RuntimeError('SpB repair acceptance failed; Qwen successors blocked')
    if queue['phase'] != 'completed':
        return False
    state = read(SPB / 'state.json')
    if state['phase'] != 'completed' or state['completed'] != ['pre', 'train2', 'post']:
        raise RuntimeError('SpB repair completion mismatch')
    if not engine.predecessor_complete():
        raise RuntimeError('Original panel predecessor no longer verified')
    for stage in state['completed']:
        engine.verify(stage, write=False)
        if read(SPB / f'acceptance-{stage}.json')['result'] != read(SPB / 'runs' / stage / 'result.json'):
            raise RuntimeError('SpB repair acceptance record differs from result')
    if REUSED_ARM_ROOT is not None:
        verify_reused_arm()
    return True


def verify_reused_arm():
    cfg = read(REUSED_ARM_ROOT / 'deployment.json')
    state = read(REUSED_ARM_ROOT / 'state.json')
    if (state['phase'] != 'completed' or state.get('exit_code') != 0
            or state['completed'] != ['pre', 'train2', 'post']
            or cfg['runtime_sha'] != '019a8b3a60aa093d61fccfb4293625e300a2894e'
            or cfg['training_seeds'] != [[49]*8, [97]*8]):
        raise RuntimeError('Previously completed l6-same evidence mismatch; no duplicate run')
    engine.ROOT, engine.RUNTIME_SHA = REUSED_ARM_ROOT, cfg['runtime_sha']
    engine.TRAIN_SEEDS = cfg['training_seeds']
    engine.TOKENIZER_SHA, engine.MASK_SHA = cfg['tokenizer_sha256'], cfg['mask_sha256']
    for stage in state['completed']:
        engine.verify(stage, write=False)
        if read(REUSED_ARM_ROOT / f'acceptance-{stage}.json')['result'] != read(REUSED_ARM_ROOT / 'runs' / stage / 'result.json'):
            raise RuntimeError('Previously completed l6-same acceptance differs from result')


def budget(deadline=None):
    time_error = f'{WALL_SECONDS//3600}-hour / {16*len(ARMS)}-GPU-hour suite ceiling; no extension'
    if deadline is not None and time.time() >= deadline - 45:
        raise TimeoutError(time_error)
    assets = MODEL.parent if MODEL.parent.exists() else Path(str(MODEL.parent)+'-relay2-staging')
    retained = [path for path in (Path(str(MODEL.parent)+'-staging'),
                Path(str(MODEL.parent)+'-direct-staging'),
                *PRIOR_ROOTS) if path.exists()]
    engine.measure_budget([SUITE, SOURCE.parent, assets, *retained], SUITE, LIMIT, deadline,
                          time_error, f'{LIMIT//engine.GIB}GiB suite ceiling', lock_root=SUITE)


def queue():
    cfg = read(SUITE / 'deployment.json')
    clean(SOURCE, cfg['controller_sha'])
    clean(SUITE / 'runtime', cfg['runtime_sha'])
    regression = read(SUITE / ARMS[0][0] / 'regressions.json')
    if not regression['passed'] or regression['skips'] or regression['runtime_sha'] != cfg['runtime_sha']:
        raise RuntimeError('CPU regression acceptance required')
    for index in range(len(ARMS)):
        arm = select_arm(index)
        proof = read(engine.ROOT / 'readiness.json')
        if (not proof['passed'] or proof['cuda_initialized'] or not proof.get('qwen_arm_verified')
                or proof['runtime_sha'] != cfg['runtime_sha']
                or not arm.get('tokenizer_sha256') or not arm.get('mask_sha256')):
            raise RuntimeError('All twelve actual launcher/config CPU checks required')
    with (SUITE / 'queue.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if (SUITE / 'queue-state.json').exists() or (SUITE / 'dispatch.json').exists():
            raise RuntimeError('Already queued or dispatched; never restart')
        state = dict(phase='waiting-predecessor', completed=[], first_dispatch_by=FIRST_DISPATCH_BY)
        process, active_index, deadline = None, None, None
        try:
            save(SUITE / 'queue-state.json', state)
            while not predecessor_complete():
                if time.time() >= FIRST_DISPATCH_BY:
                    raise TimeoutError('First-dispatch admission expired')
                time.sleep(60)
            save(SUITE / 'predecessor-acceptance.json', dict(passed=True, checked_at=time.time(), predecessor=str(SPB),
                 reused_completed_arm=str(REUSED_ARM_ROOT) if REUSED_ARM_ROOT else None))
            state['phase'] = 'waiting-verified-model'
            save(SUITE / 'queue-state.json', state)
            while not (MODEL.parent / 'VERIFIED.sha256').is_file():
                if Path(str(MODEL.parent)+'-relay2-staging/FAILED.exit').exists():
                    raise RuntimeError('Approved model transfer failed; no GPU dispatch')
                if time.time() >= FIRST_DISPATCH_BY:
                    raise TimeoutError('Verified-model admission expired')
                time.sleep(60)
            if (MODEL.parent / 'manifest.sha256').read_bytes() != (SOURCE / 'configs/qwen3-4b-instruct-2507.sha256').read_bytes():
                raise RuntimeError('Transferred model manifest differs from registered snapshot')
            for index, (tag, *_) in enumerate(ARMS):
                arm = select_arm(index)
                state.update(phase='waiting-resources', arm=tag)
                save(SUITE / 'queue-state.json', state)
                while True:
                    budget(deadline)
                    if deadline is None and time.time() >= FIRST_DISPATCH_BY:
                        raise TimeoutError('First-dispatch admission expired')
                    if engine.resources_ready() and shutil.disk_usage(SUITE).free >= ((len(ARMS)-index)*128+12)*engine.GIB:
                        break
                    time.sleep(60)
                with (engine.ROOT / 'fsync-probe').open('xb') as stream:
                    stream.write(b'qwen-seeds197\n')
                    stream.flush()
                    os.fsync(stream.fileno())
                if (engine.ROOT / 'fsync-probe').read_bytes() != b'qwen-seeds197\n':
                    raise RuntimeError('NVMe fsync/readback failed')
                start = time.time()
                if deadline is None:
                    deadline = start + WALL_SECONDS
                    save(SUITE / 'dispatch.json', dict(start=start, deadline=deadline, gpu_hours=16*len(ARMS)))
                arm_deadline = min(start+7200, deadline)
                args = docker('execute', index)
                active_index = index
                save(engine.ROOT / 'dispatch.json', dict(start=start, deadline=arm_deadline, command=args))
                state.update(phase='running-unverified', arm=tag, deadline=deadline, arm_deadline=arm_deadline)
                save(SUITE / 'queue-state.json', state)
                with (engine.ROOT / 'container.log').open('x') as log:
                    process = sp.Popen(args, stdout=log, stderr=sp.STDOUT)
                    while process.poll() is None:
                        budget(deadline)
                        engine.budget(arm_deadline)
                        time.sleep(15)
                if process.returncode or read(engine.ROOT / 'state.json')['phase'] != 'completed':
                    raise RuntimeError(f'{tag} failed, exit{process.returncode}; stop successors, no retry')
                for stage in arm['stages']:
                    engine.verify(stage, write=False)
                state['completed'].append(tag)
                state['phase'] = 'arm-completed'
                save(SUITE / 'queue-state.json', state)
                process = None
            state.update(phase='completed', exit_code=0, learning_validated=False)
            save(SUITE / 'queue-state.json', state)
        except BaseException as exc:
            state.update(phase='failed', error=str(exc))
            try:
                save(SUITE / 'queue-state.json', state)
            finally:
                if process is not None:
                    select_arm(active_index)
                    engine.stop_owned()
            raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['prepare', 'queue', 'cpu-command', 'regressions-command', 'arm-cpu', 'arm-execute', 'arm-regressions'])
    parser.add_argument('index', type=int, nargs='?', choices=range(len(ARMS)))
    args = parser.parse_args()
    if args.mode in ('prepare', 'queue'):
        globals()[args.mode]()
    elif args.index is None:
        parser.error('An exact arm index is required')
    elif args.mode == 'cpu-command':
        print(json.dumps(docker('cpu', args.index)))
    elif args.mode == 'regressions-command':
        print(json.dumps(docker('regressions', args.index)))
    elif args.mode == 'arm-regressions':
        regressions(args.index)
    elif args.mode == 'arm-cpu':
        cpu(args.index)
    else:
        select_arm(args.index)
        engine.execute()


if __name__ == '__main__':
    main()
