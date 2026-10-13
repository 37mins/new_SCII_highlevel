"""Read-only training observers and paired CP96/192 evaluation, no policy edits."""
import copy
import hashlib
import json
import os
from pathlib import Path


def install():
    stage = os.environ['SC2_ACCEPTANCE_STAGE']
    if stage == 'train192':
        from refinery_order_eval import install_game_observers
        install_game_observers()
    elif stage in ('pre96', 'eval192'):
        from acceptance_hook import EVAL_SEEDS
        from feedback_eval import install as evaluate
        evaluate(expected_step=96 if stage == 'pre96' else 192,
                 game_seeds=EVAL_SEEDS, expected_temperature=0.8)
    else:
        raise ValueError('Undeclared CP96 to192 stage')


def runtime_environment(resolved_config, ray_tmp):
    path = Path(resolved_config)
    if not 0 < path.stat().st_size < 1024**2:
        raise ValueError('Small resolved config required')
    raw = path.read_bytes(); cfg = json.loads(raw)
    env = copy.deepcopy(cfg['ray_init']['runtime_env']); ev = env['env_vars']
    stage = ev.get('SC2_ACCEPTANCE_STAGE')
    if (stage not in ('pre96', 'train192', 'eval192')
            or env.get('worker_process_setup_hook') != 'qwen_l8_cp192_hook.install'
            or ev.get('SC2PATH') != '/assets/StarCraftII'
            or ev.get('SC2_DIFFICULTY') != 'CheatVision'
            or ev.get('SC2_EXPECTED_DIFFICULTY') != 'CheatVision'
            or str(ev.get('SC2_L8_RENDEZVOUS_LOW_PORT')) != '1'
            or ev.get('SC2_TRAIN_SEED_PROTOCOL') != 'same_uniform101'
            or not all(ev.get(k) for k in ('PYTHONPATH', 'SC2_EVAL_SEEDS_LOG_PATH', 'SC2_RUNTIME_LOG_ROOT'))
            or cfg['trainer']['val_only'] != (stage != 'train192')
            or cfg['trainer']['n_gpus_per_node'] != 8
            or cfg['trainer']['total_training_steps'] != 192):
        raise ValueError('Complete matching CP96 to192 environment required')
    ev.update(TMPDIR=str(ray_tmp), RAY_TMPDIR=str(ray_tmp))
    return env, dict(resolved_config_sha256=hashlib.sha256(raw).hexdigest(),
        env_sha256=hashlib.sha256(json.dumps(env, sort_keys=True).encode()).hexdigest(),
        env_var_names=sorted(ev), overridden_env_vars=['RAY_TMPDIR', 'TMPDIR'],
        worker_process_setup_hook=env['worker_process_setup_hook'], stage=stage,
        required_worker_module='refinery_order_eval')
