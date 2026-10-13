"""One-shot authorized 8+16+8 game repair acceptance after the existing 197 panel."""
import argparse
from contextlib import contextmanager, nullcontext
import fcntl
import json
import math
import os
from pathlib import Path
import shutil
import signal
import subprocess as sp
import sys
import time
import uuid

from acceptance_hook import EVAL_SEEDS

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parents[2]
ROOT = Path('/var/jfsCache/sc2-policy-credit197-20260921-r1')
PANEL = Path('/var/jfsCache/sc2-panel197-20260921-r2')
ORCH = Path('/var/jfsCache/sc2-c197-eval96-20260920-r1/orchestration')
REC = Path('experiments/records/20260916-combat-result-reward-v1')
RUNTIME_SHA = '0172fb9b334cea91f1e92c0c545f721afe281671'
ORCH_SHA = '9a7b0faca5b145a891ad211f189121e4949f0eab'
CONTAINER = 'sc2-policy-credit197-20260921-r1'
GIB = 1024**3
LIMIT = 128 * GIB
WALL_SECONDS = 7200
# Panel's existing effective cutoff + one hour of resource wait, not a new panel budget.
QUEUE_EXPIRES = 1790018140.699252
MASK_SHA = '63a9546dd5fb39a64c6e2a2ad13f31101aacaade9bac07258d0e415480181e0d'
TOKENIZER_SHA = 'a63080b4b30dc861fe1b0e420c53a241304dc81aff3d9bb315e6e33e2a1ab794'
TRAIN_SEEDS = [[2732]*8, [43567]*8]
DOCKER_SCRIPT = HERE / 'acceptance197.py'
# One stable inode shared by every controller that traverses overlapping roots.
# Qwen sets this to its suite root; standalone SpB uses ROOT. Never unlink it.
STORAGE_LOCK_ROOT = None


def read(path):
    return json.loads(Path(path).read_text())


@contextmanager
def storage_guard(lock_root=None, *, exclusive=False, timeout=15):
    root = lock_root or STORAGE_LOCK_ROOT or ROOT
    until = time.monotonic() + timeout
    with (Path(root) / '.storage.lock').open('a') as lock:
        mode = fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH
        while True:
            try:
                fcntl.flock(lock, mode | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                remaining = until - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError('Storage coordination lock timed out')
                time.sleep(min(0.02, remaining))
        yield  # Closing the descriptor releases the lock even on exceptions.


def save(path, data, *, lock_root=None, timeout=15):
    # Writers may coexist (unique temp names), but no du walker may see their
    # temporary names disappear. Hold from before creation through replacement.
    with storage_guard(lock_root, timeout=timeout):
        atomic_save(path, data)


def atomic_save(path, data):
    path = Path(path)
    # Host watchdog and container share this directory (and may share PID1).
    # Never let two writers truncate/rename the same temporary inode.
    tmp = path.with_name(f'.{path.name}.{uuid.uuid4().hex}.tmp')
    with tmp.open('x') as stream:
        json.dump(data, stream, indent=2, allow_nan=False)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(tmp, path)


def cmd(args):
    return sp.run(list(map(str, args)), text=True, capture_output=True,
                  timeout=15, check=True).stdout.strip()


def clean(path, sha):
    if cmd(['git', '-C', path, 'rev-parse', 'HEAD']) != sha or cmd(
            ['git', '-C', path, 'status', '--porcelain']):
        raise RuntimeError('Frozen source identity/cleanliness mismatch: ' + str(path))


def storage_output(value):
    """Small diagnostic tails only; timeout output can be bytes even in text mode."""
    if isinstance(value, bytes):
        value = value.decode('utf-8', errors='replace')
    value = value or ''
    return dict(tail=value[-8192:], characters=len(value), truncated=len(value) > 8192)


def storage_failure(proof, receipt_root=None, lock_root=None):
    """Keep each failure, even if another writer later publishes a good sample."""
    path = (ROOT if receipt_root is None else receipt_root) / f'storage-failure-{uuid.uuid4().hex}.json'
    try:
        # If coordination itself failed, don't spend another lock timeout trying
        # to report it. The bounded stderr receipt below remains authoritative.
        save(path, proof, lock_root=lock_root, timeout=0)
    except OSError as exc:
        # Storage itself may be unavailable: report to the existing controller
        # log, and still fail closed. Never replace unknown usage with zero.
        print(json.dumps(dict(storage_failure=proof, receipt_write_error=str(exc))),
              file=sys.stderr, flush=True)
        return f'receipt unavailable ({exc}); see controller stderr'
    return str(path)


def budget(deadline):
    measure_budget([ROOT, SOURCE.parent], ROOT, LIMIT, deadline,
                   'Two-hour / sixteen-GPU-hour ceiling; no extension', '128GiB output ceiling')


def measure_budget(roots, receipt_root, limit, deadline, time_error, size_error, *, lock_root=None,
                   quiesce=None):
    """Exact bounded traversal shared by the arm and whole-suite watchdogs."""
    started = time.time()
    remaining = 15 if deadline is None else deadline - 45 - started
    if remaining <= 0:
        raise TimeoutError(time_error)
    # Lock waiting consumes the existing 15s/remaining-time allowance; it does
    # not grant a fresh timeout to du or reset any experiment deadline.
    until = time.monotonic() + min(15, remaining)
    roots = list(map(str, roots))
    args = ['du', '-sb', '--null', '--', *roots]
    proof = dict(command=args, roots=roots, started_at=started, deadline=deadline,
                 limit=limit, bytes=None, returncode=None, status='measurement-failed',
                 stdout=storage_output(''), stderr=storage_output(''))
    try:
        with storage_guard(lock_root, exclusive=True, timeout=min(15, remaining)):
            # Opt-in host-side candidate only. Acquire the metadata lock BEFORE
            # freezing writers, so a frozen child cannot strand a shared lock.
            quiet = nullcontext() if quiesce is None else quiesce(until, proof)
            with quiet:
                remaining = until - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError('Storage measurement allowance exhausted waiting for lock/pause')
                result = sp.run(args, capture_output=True, text=True, encoding='utf-8', errors='replace',
                                env=dict(os.environ, LC_ALL='C'), timeout=remaining, check=False)
                # Preserve the du outcome even if subsequent unpause fails.
                proof.update(returncode=result.returncode, stdout=storage_output(result.stdout),
                             stderr=storage_output(result.stderr))
                if quiesce is not None:
                    proof['measured_at'] = time.time()
            if quiesce is not None and time.monotonic() >= until:
                raise TimeoutError('Storage pause/measurement/recovery exceeded the original allowance')
        proof.update(returncode=result.returncode, stdout=storage_output(result.stdout),
                     stderr=storage_output(result.stderr))
        if result.returncode or result.stderr:
            raise ValueError('du failed or emitted diagnostics; partial totals are not trusted')
        # NUL records preserve whitespace/newlines in paths. Require exactly
        # one nonnegative byte count for each requested root, never an empty or
        # partial success. No exclusions, ENOENT filtering, fallback or retry.
        rows = result.stdout.split('\0')
        if len(rows) != len(roots) + 1 or rows[-1] != '':
            raise ValueError('du did not return all exact terminated root records')
        sizes = {}
        for row in rows[:-1]:
            count, separator, path = row.partition('\t')
            if (not separator or not count.isascii() or not count.isdecimal()
                    or path not in roots or path in sizes):
                raise ValueError('du root identity or byte count mismatch')
            sizes[path] = int(count)
        if set(sizes) != set(roots):
            raise ValueError('du omitted a required root')
        proof.update(bytes=sum(sizes.values()), root_bytes=sizes)
    except (OSError, sp.TimeoutExpired, ValueError, RuntimeError) as exc:
        if isinstance(exc, sp.TimeoutExpired):
            if proof['returncode'] is None:
                proof.update(stdout=storage_output(exc.stdout), stderr=storage_output(exc.stderr))
            else:
                proof['exception_output'] = dict(stdout=storage_output(exc.stdout),
                                               stderr=storage_output(exc.stderr))
        proof.update(error_type=type(exc).__name__, error=str(exc), checked_at=time.time())
        receipt = storage_failure(proof, receipt_root, lock_root)
        raise RuntimeError(f'Storage measurement failed; no retry; {receipt}') from exc
    proof['checked_at'] = time.time()
    if deadline is not None and proof['checked_at'] >= deadline - 45:
        proof['status'] = 'deadline-exceeded'
        receipt = storage_failure(proof, receipt_root, lock_root)
        raise TimeoutError(f'{time_error}; {receipt}')
    if proof['bytes'] >= limit:
        proof['status'] = 'limit-exceeded'
        receipt = storage_failure(proof, receipt_root, lock_root)
        raise RuntimeError(f'{size_error}; {receipt}')
    proof['status'] = 'measured'
    save(receipt_root / 'storage-state.json', proof, lock_root=lock_root)


def prepare():
    if ROOT.exists():
        raise RuntimeError('Fresh exact root required; never overwrite or retry')
    clean(ORCH, ORCH_SHA)
    source_sha = cmd(['git', '-C', SOURCE, 'rev-parse', 'HEAD'])
    clean(SOURCE, source_sha)
    ROOT.mkdir()
    for name in ('runs', 'cpu', 'tmp'):
        (ROOT / name).mkdir()
    cfg = read(PANEL / 'deployment.json')
    cmd(['git', 'clone', '--quiet', '--shared', SOURCE, ROOT / 'runtime'])
    cmd(['git', '-C', ROOT / 'runtime', 'checkout', '--quiet', '--detach', RUNTIME_SHA])
    clean(ROOT / 'runtime', RUNTIME_SHA)
    save(ROOT / 'deployment.json', dict(runtime_sha=RUNTIME_SHA, controller_sha=source_sha,
         controller_source=str(SOURCE), orchestration_sha=ORCH_SHA,
         host=cfg['host'], environment=cfg['environment'], predecessor=str(PANEL),
         stages=['pre', 'train2', 'post'], games=[8, 16, 8], updates=[0, 2, 0],
         eval_seeds=EVAL_SEEDS, training_seeds=[[2732]*8, [43567]*8],
         difficulty='Harder', queue_expires=QUEUE_EXPIRES, wall_seconds=WALL_SECONDS,
         gpu_hours=16, output_limit_bytes=LIMIT, no_retry=True, no_long_training=True,
         authorization='User approved 8 zero-update games -> 2 PPO steps/16 games -> 8 paired games; '
                       'after current panel and eight idle GPUs; at most two hours / sixteen GPU-hours'))


def invocation(cfg, stage, dry=False):
    if stage not in ('pre', 'train2', 'post'):
        raise ValueError('Unknown stage')
    out = ROOT / ('cpu' if dry else 'runs') / stage
    env = dict(os.environ, **cfg['environment'])
    env.pop('RAY_ADDRESS', None)
    env.update(SOURCE_SHA=RUNTIME_SHA, SC2_COMBAT_LONG_AUTHORIZED='1',
               SC2_CHECKPOINT_RESUME='False', SC2_DIFFICULTY=cfg.get('difficulty', 'Harder'),
               OUTPUT_DIR=str(out), RUN_ID=f"{cfg.get('run_prefix', 'policy-credit197-r1')}-{stage}",
               RAY_TMPDIR=f'/tmp/pc197-{stage}', PYTHONDONTWRITEBYTECODE='1',
               LONG_DEPENDENCY_PATH=str(HERE)+':'+cfg['environment']['LONG_DEPENDENCY_PATH'])
    if dry:
        env.update(DRY_RUN='1', VERIFY_ASSETS='0', CUDA_VISIBLE_DEVICES='')
    args = ['bash', str(ORCH / REC / 'run_seed_group_arm.sh'), str(ROOT / 'runtime'),
            'algorithm.sc2_policy_credit.enabled=True',
            'algorithm.sc2_policy_credit.invalid_advantage_penalty=0.1',
            'algorithm.sc2_policy_credit.min_valid_ratio=0.5',
            "++ray_init.runtime_env.env_vars.SC2_ORIGINAL_GAME_SEEDS='0'",
            "++ray_init.runtime_env.env_vars.SC2_PLANNER_PROTOCOL='legacy'",
            "++ray_init.runtime_env.env_vars.SC2_ORIGINAL_BO_SEGMENT='1'",
            f"+ray_init.runtime_env.env_vars.SC2_ACCEPTANCE_STAGE='{stage}'",
            f'+ray_init.runtime_env.env_vars.SC2_EVAL_SEEDS_LOG_PATH={out}/evaluation_seeds.jsonl',
            f'+ray_init.runtime_env.env_vars.SC2_COMMAND_TRACE_DIR={out}/logs',
            f"+ray_init.runtime_env.worker_process_setup_hook={cfg.get('worker_hook', 'acceptance_hook.install')}",
            '+data.sc2_no_thinking=True', 'actor_rollout_ref.rollout.top_p=1.0',
            'actor_rollout_ref.rollout.top_k=0', 'actor_rollout_ref.rollout.val_kwargs.top_p=1.0',
            'actor_rollout_ref.rollout.val_kwargs.top_k=0',
            'actor_rollout_ref.rollout.val_kwargs.temperature=0.8',
            'actor_rollout_ref.rollout.val_kwargs.do_sample=True',
            'actor_rollout_ref.rollout.val_kwargs.n=8', '+env.val_rollout_n=8',
            '++env.prompt_response_log_train_only=False',
            'trainer.total_epochs=2', 'trainer.total_training_steps=2', 'trainer.save_freq=2',
            'trainer.val_only=False', 'trainer.val_before_train=False', 'trainer.test_freq=-1']
    if cfg.get('model_kind') == 'qwen':
        args[1] = str(HERE / 'run_qwen_seed_arm.sh')
        args += [f"algorithm.sc2_policy_credit.seed_group_mode={cfg['seed_group_mode']}",
                 f"+ray_init.runtime_env.env_vars.SC2_TRAIN_SEED_PROTOCOL='{cfg['seed_protocol']}'"]
    model_path = cfg.get('model_mount', '/assets/spb')
    for role in ('actor', 'rollout', 'ref'):
        args += [f'+actor_rollout_ref.{role}.no_thinking_tokenizer_path={model_path}',
                 f'+actor_rollout_ref.{role}.sc2_action_tokenizer_path={model_path}',
                 f'+actor_rollout_ref.{role}.sc2_action_response_length=192']
    if stage != 'train2':
        args += ['trainer.val_only=True', 'trainer.val_before_train=True',
                 'trainer.total_epochs=1', 'trainer.save_freq=-1']
    if stage == 'post':
        args += ['trainer.resume_mode=resume_path',
                 f'trainer.resume_from_path={ROOT}/runs/train2/checkpoints/global_step_2']
    return args, env, out


def cpu():
    import torch
    from hydra import compose, initialize_config_dir
    from omegaconf import OmegaConf
    from ray._private.utils import validate_socket_filepath
    sys.path.insert(0, str(ORCH / REC))
    from seed_ray_paths import socket_path
    from verl.trainer.ppo.sc2_policy_credit import validate_config as credit_config
    from verl.utils.sc2_action_support import validate_config as support_config
    cfg = read(ROOT / 'deployment.json')
    # DRY_RUN skips assets, so check source hashes explicitly before accepting it.
    source_check = sp.run(['sha256sum', '-c', 'configs/system-v1.sha256'],
                          cwd=ROOT / 'runtime', capture_output=True, text=True, timeout=30)
    (ROOT / 'cpu' / 'source-check.log').write_text(source_check.stdout + source_check.stderr)
    if source_check.returncode:
        raise RuntimeError('Source manifest verification failed before CPU launcher acceptance')
    for stage in cfg['stages']:
        args, env, out = invocation(cfg, stage, True)
        proc = sp.run(args, env=env, cwd=ROOT / 'runtime', capture_output=True, text=True, timeout=90)
        (ROOT / 'cpu' / f'{stage}.log').write_text(proc.stdout + proc.stderr)
        if proc.returncode:
            raise RuntimeError(f'{stage} dry entry failed: {proc.stderr[-1200:]}')
        command = read(out / 'effective_config.json')['command']
        overrides = command[command.index('verl.trainer.main_ppo') + 1:]
        with initialize_config_dir(config_dir=str(ROOT / 'runtime/verl/trainer/config'), version_base=None):
            effective = compose(config_name='ppo_trainer', overrides=overrides)
        credit_config(effective)
        support_config(effective)
        if (effective.trainer.val_only != (stage != 'train2')
                or effective.trainer.n_gpus_per_node != 8
                or effective.trainer.total_training_steps != 2
                or effective.env.rollout.n != 8 or effective.data.train_batch_size != 1
                or effective.actor_rollout_ref.rollout.response_length != 192
                or not effective.data.sc2_no_thinking):
            raise RuntimeError('Unexpected resolved acceptance configuration')
        save(out / 'resolved_config.json', OmegaConf.to_container(effective, resolve=True))
        validate_socket_filepath(socket_path(env['RAY_TMPDIR']))
    if torch.cuda.is_initialized():
        raise RuntimeError('CPU acceptance initialized CUDA')
    save(ROOT / 'readiness.json', dict(passed=True, cuda_initialized=False,
         controller_sha=cfg['controller_sha'], runtime_sha=RUNTIME_SHA,
         actual_entries_and_hydra_configs=True, checked_at=time.time()))


def verify_common(out, stage, expected_games=None):
    result = read(out / 'result.json')
    manifest = read(out / 'manifest.json')
    if (result != read(out / '.done') or result['status'] != 'completed'
            or result['process_exit_code'] != 0 or not result['metrics_finite']
            or manifest['dirty'] or manifest['world_size'] != 8
            or manifest['source_commit'] != RUNTIME_SHA
            or result['episode_outcomes']['natural_games'] != (expected_games if expected_games is not None else (16 if stage == 'train2' else 8))
            or result['episode_outcomes']['truncated'] != 0):
        raise RuntimeError('Actual completion/provenance/game evidence mismatch')
    answers = [json.loads(line) for line in (out / 'prompt_response.jsonl').read_text().splitlines()]
    consumed = [row for row in answers if row.get('policy_action_applied')]
    if not consumed or not all(row['semantic_action_evaluable'] and row['is_action_valid']
                               and row['semantic_action_valid'] for row in consumed):
        raise RuntimeError('Canonical candidate requires nonempty, 100% valid consumed answers')
    if any('<think' in row['llm_response'].lower() or '</think' in row['llm_response'].lower() for row in answers):
        raise RuntimeError('No-thinking output contract failed')
    trace_files = list((out / 'logs').glob('*-command-trace.jsonl'))
    plans = queues = commands = 0
    for trace in trace_files:
        for line in trace.open():
            row = json.loads(line)
            if row['event'] == 'parsed_plan':
                plans += 1
                if any(item['selection_source'] != 'validated_answer' for item in row['origins']):
                    raise RuntimeError('Model plan underwent salvage/fallback')
            if row['event'] == 'executor_queue':
                queues += sum(item['selection_source'] == 'validated_answer' for item in row['origins'])
            if row['event'] == 'local_command':
                commands += int(row['origin'].get('selection_source') == 'validated_answer'
                                and row['locally_queued'])
    if not plans or not queues or not commands:
        raise RuntimeError('Missing actual validated plan/queue/Depot-or-Marine command evidence')
    log = (out / 'console.log').read_text(errors='replace')
    if ('SC2_NO_THINKING {' not in log or MASK_SHA not in log
            or 'SC2_ACTION_SUPPORT {' not in log or TOKENIZER_SHA not in log):
        raise RuntimeError('Missing real worker support-mask evidence')
    return result, dict(consumed_answers=len(consumed), valid_consumed_answers=len(consumed),
                        parsed_plans=plans, validated_queue_entries=queues,
                        validated_locally_queued_commands=commands,
                        execution_scope='local Depot/Marine commands, not production completion or causal wins')


def verify(stage, write=True):
    out = ROOT / 'runs' / stage
    result, evidence = verify_common(out, stage)
    if stage == 'train2':
        if (result['completed_steps'] != 2 or result['last_global_step'] != 2
                or result['start_step'] != 0 or not result['checkpoint_complete']):
            raise RuntimeError('Exactly two fresh updates and complete checkpoint required')
        seeds = [json.loads(line)['seeds'] for line in (out / 'training_seeds.jsonl').read_text().splitlines()]
        if seeds != TRAIN_SEEDS:
            raise RuntimeError('Actual same-seed training dispatch differs')
        audit = [json.loads(line) for line in (out / 'checkpoints/sc2_policy_credit_audit.jsonl').read_text().splitlines()]
        if [x['pending_global_step'] for x in audit] != [1, 2] or any(x['decision'] != 'accept' for x in audit):
            raise RuntimeError('Missing pre-update quality gates')
        metrics = read(out / 'metrics.json')
        if len(metrics) != 2 or any(not math.isfinite(row['actor/grad_norm']) or row['actor/grad_norm'] <= 0
                                  or row['policy_credit/invalid_advantage_max'] > 0 for row in metrics):
            raise RuntimeError('Nonfinite/zero update or positive invalid credit')
    else:
        proof = read(out / 'checkpoint_evaluation.json')
        step = 0 if stage == 'pre' else 2
        checkpoint = None if stage == 'pre' else str(ROOT / 'runs/train2/checkpoints/global_step_2')
        seeds = [json.loads(line)['seeds'] for line in (out / 'evaluation_seeds.jsonl').read_text().splitlines()]
        if (result['training_updates'] != 0 or not proof['val_only'] or proof['optimizer_updates'] != 0
                or proof['loaded_global_step'] != step or proof['checkpoint'] != checkpoint
                or proof['checkpoint_load_returned'] != bool(step)
                or proof['game_seeds'] != EVAL_SEEDS or seeds != [EVAL_SEEDS]):
            raise RuntimeError('Actual eval load/seed/zero-update evidence mismatch')
        for rank in range(8):
            rng = read(out / f'sampling-rank{rank}.json')
            if (rng['rank'], rng['seed']) != (rank, rank):
                raise RuntimeError('Paired model-sampling RNG mismatch')
    if write:
        save(ROOT / f'acceptance-{stage}.json', dict(result=result, evidence=evidence, checked_at=time.time()))


def execute():
    cfg = read(ROOT / 'deployment.json')
    dispatch = read(ROOT / 'dispatch.json')
    clean(SOURCE, cfg['controller_sha'])
    clean(ROOT / 'runtime', RUNTIME_SHA)
    state = dict(phase='starting', completed=[], deadline=dispatch['deadline'])
    process = None
    try:
        for stage in cfg['stages']:
            budget(dispatch['deadline'])
            args, env, out = invocation(cfg, stage)
            save(ROOT / f'launch-{stage}.json', dict(command=args, runtime_sha=RUNTIME_SHA,
                 controller_sha=cfg['controller_sha'], deadline=dispatch['deadline']))
            state.update(phase='running-unverified', stage=stage, run=str(out))
            save(ROOT / 'state.json', state)
            with (ROOT / f'{stage}.log').open('x') as log:
                process = sp.Popen(args, env=env, cwd=ROOT / 'runtime', stdout=log,
                                   stderr=sp.STDOUT, start_new_session=True)
                while process.poll() is None:
                    budget(dispatch['deadline'])
                    time.sleep(15)
            if process.returncode:
                raise RuntimeError(f'{stage} exit{process.returncode}; no retry or successor')
            verify(stage)
            state['completed'].append(stage)
            state['phase'] = 'stage-completed'
            save(ROOT / 'state.json', state)
            release = min(dispatch['deadline']-30, time.time()+120)
            while cmd(['nvidia-smi', '--query-compute-apps=pid', '--format=csv,noheader']):
                if time.time() >= release:
                    raise RuntimeError('Workers did not release; no forced shared cleanup')
                time.sleep(5)
        state.update(phase='completed', exit_code=0, learning_validated=False)
        save(ROOT / 'state.json', state)
    except BaseException as exc:
        state.update(phase='failed', error=str(exc))
        try:
            save(ROOT / 'state.json', state)
        finally:
            # A disk/coordination failure must not skip the existing owned stop.
            if process and process.poll() is None:
                os.killpg(process.pid, signal.SIGINT)
        raise


def docker(mode):
    cfg = read(ROOT / 'deployment.json')
    host = cfg['host']
    args = ['docker', 'run', '--name', CONTAINER + ('-cpu' if mode == 'cpu' else ''),
            '--label', f'sc2.acceptance.root={ROOT}', '--shm-size', '128g',
            '--entrypoint', '/runtime/bin/python']
    for source, target, ro in [(ROOT, ROOT, False), (ROOT / 'tmp', '/tmp', False),
            (ROOT / 'runtime', ROOT / 'runtime', True), (SOURCE.parent, SOURCE.parent, True),
            (ORCH, ORCH, True), (host['venv'], '/runtime', True),
            (host['model'], cfg.get('model_mount', '/assets/spb'), True), (host['sc2'], '/assets/StarCraftII', True),
            ('/var/jfsCache/sc2-c197-20260919-r1/dependencies',
             '/var/jfsCache/sc2-c197-20260919-r1/dependencies', True)]:
        args += ['-v', f'{source}:{target}' + (':ro' if ro else '')]
    args += ['-w', str(ROOT / 'runtime'), '-e', 'PYTHONDONTWRITEBYTECODE=1',
             '-e', f'PYTHONPATH={ROOT}/runtime:{HERE}:/var/jfsCache/sc2-c197-20260919-r1/dependencies:/runtime/lib/python3.12/site-packages',
             '-e', f"CONTAINER_IMAGE_ID={host['image']}"]
    args += ['--gpus', 'all'] if mode == 'execute' else ['--cpus', '2', '--memory', '6g', '-e', 'CUDA_VISIBLE_DEVICES=']
    return args + [host['image'], '-B', str(DOCKER_SCRIPT), mode]


def predecessor_complete():
    state = read(PANEL / 'state.json')
    if state['phase'] == 'failed':
        raise RuntimeError('Predecessor failed; no automatic repair acceptance')
    if state['phase'] != 'completed':
        return False
    expected = {(arm, batch) for batch in range(8) for arm in ('original', 'D96', 'C96')}
    if {(row['arm'], row['batch']) for row in state['completed']} != expected or state['training_updates'] != 0:
        raise RuntimeError('Predecessor completion list mismatch')
    for arm, batch in sorted(expected):
        tag = f'b{batch:02d}-{arm}'
        result = read(PANEL / 'runs' / tag / 'result.json')
        if (result != read(PANEL / 'runs' / tag / '.done')
                or result != read(PANEL / f'acceptance-{tag}.json')
                or result['status'] != 'completed' or result['process_exit_code'] != 0
                or result['training_updates'] != 0 or result['episode_outcomes']['natural_games'] != 8):
            raise RuntimeError('Predecessor actual batch acceptance mismatch')
    return True


def resources_ready():
    rows = cmd(['nvidia-smi', '--query-gpu=index,memory.used,utilization.gpu', '--format=csv,noheader,nounits'])
    if len(rows.splitlines()) != 8:
        raise RuntimeError('Expected eight GPUs')
    if any(float(value.strip()) > 0 for row in rows.splitlines() for value in row.split(',')[1:]):
        return False
    if cmd(['nvidia-smi', '--query-compute-apps=pid', '--format=csv,noheader']):
        return False
    mem = dict(row.split(':', 1) for row in Path('/proc/meminfo').read_text().splitlines())
    return int(mem['MemAvailable'].split()[0])*1024 >= 600*GIB and shutil.disk_usage(ROOT).free >= 140*GIB


def stop_owned():
    record = json.loads(cmd(['docker', 'inspect', CONTAINER]))[0]
    if record['Config']['Labels'].get('sc2.acceptance.root') != str(ROOT):
        raise RuntimeError('Container ownership mismatch; refusing stop')
    if record['State']['Running']:
        cmd(['docker', 'stop', '--time', '10', CONTAINER])


def queue():
    cfg = read(ROOT / 'deployment.json')
    clean(SOURCE, cfg['controller_sha'])
    clean(ROOT / 'runtime', RUNTIME_SHA)
    clean(ORCH, ORCH_SHA)
    proof = read(ROOT / 'readiness.json')
    if not proof['passed'] or proof['cuda_initialized'] or proof['controller_sha'] != cfg['controller_sha']:
        raise RuntimeError('Frozen CPU acceptance required')
    with (ROOT / 'queue.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if (ROOT / 'queue-state.json').exists() or (ROOT / 'dispatch.json').exists():
            raise RuntimeError('Already queued/dispatched; no restart')
        process = None
        try:
            save(ROOT / 'queue-state.json', dict(phase='waiting-predecessor', expires=QUEUE_EXPIRES))
            while True:
                if time.time() >= QUEUE_EXPIRES:
                    raise TimeoutError('Queue expired; no rescheduling')
                if predecessor_complete():
                    save(ROOT / 'queue-state.json', dict(phase='waiting-resources', expires=QUEUE_EXPIRES))
                    if resources_ready():
                        break
                time.sleep(60)
            with (ROOT / 'fsync-probe').open('xb') as stream:
                stream.write(b'policy-credit197\n')
                stream.flush()
                os.fsync(stream.fileno())
            if (ROOT / 'fsync-probe').read_bytes() != b'policy-credit197\n':
                raise RuntimeError('NVMe fsync readback failed')
            start = time.time()
            deadline = start + WALL_SECONDS
            budget(deadline)
            args = docker('execute')
            save(ROOT / 'dispatch.json', dict(command=args, start=start, deadline=deadline,
                 resource_check=cfg.get('resource_check', 'eight empty GPUs, no compute PIDs, >=600GiB RAM, >=140GiB disk, fsync passed')))
            save(ROOT / 'queue-state.json', dict(phase='dispatched', deadline=deadline))
            with (ROOT / 'container.log').open('x') as log:
                process = sp.Popen(args, stdout=log, stderr=sp.STDOUT)
                while process.poll() is None:
                    budget(deadline)
                    time.sleep(15)
            if process.returncode or read(ROOT / 'state.json')['phase'] != 'completed':
                raise RuntimeError(f'Acceptance failed, container exit{process.returncode}; no retry')
            save(ROOT / 'queue-state.json', dict(phase='completed', exit_code=0))
        except BaseException as exc:
            try:
                save(ROOT / 'queue-state.json', dict(phase='failed', error=str(exc)))
            finally:
                if process is not None:
                    stop_owned()
            raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['prepare', 'cpu', 'cpu-command', 'queue', 'execute'])
    mode = parser.parse_args().mode
    if mode == 'cpu-command':
        print(json.dumps(docker('cpu')))
    else:
        globals()[mode]()
