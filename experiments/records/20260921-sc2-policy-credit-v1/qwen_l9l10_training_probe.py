"""Exact L9/L10 environments; reuse the tested CPU/GPU probe implementation."""
import copy
import hashlib
import json
from pathlib import Path


def runtime_environment(resolved_config, ray_tmp):
    path = Path(resolved_config)
    if path.stat().st_size > 1024**2:
        raise ValueError('Small resolved Hydra config required')
    raw = path.read_bytes(); cfg = json.loads(raw)
    env = copy.deepcopy(cfg['ray_init']['runtime_env']); ev = env['env_vars']
    stage = ev.get('SC2_ACCEPTANCE_STAGE')
    difficulty = ev.get('SC2_DIFFICULTY')
    if (stage not in ('pre', 'train2', 'post', 'train96', 'eval96')
            or difficulty not in ('CheatMoney', 'CheatInsane')
            or ev.get('SC2_EXPECTED_DIFFICULTY') != difficulty
            or env.get('worker_process_setup_hook') != 'l7_followup_hook.install'
            or ev.get('SC2PATH') != '/assets/StarCraftII'
            or str(ev.get('SC2_L8_RENDEZVOUS_LOW_PORT')) != '1'
            or ev.get('SC2_TRAIN_SEED_PROTOCOL') != 'same_uniform101'
            or not all(ev.get(k) for k in ('PYTHONPATH', 'SC2_EVAL_SEEDS_LOG_PATH', 'SC2_RUNTIME_LOG_ROOT'))
            or cfg['trainer']['val_only'] != (stage in ('pre', 'post', 'eval96'))
            or cfg['trainer']['n_gpus_per_node'] != 8):
        raise ValueError('Complete matching L9/L10 training environment required')
    ev.update(TMPDIR=str(ray_tmp), RAY_TMPDIR=str(ray_tmp))
    return env, dict(resolved_config_sha256=hashlib.sha256(raw).hexdigest(),
        env_sha256=hashlib.sha256(json.dumps(env, sort_keys=True).encode()).hexdigest(),
        env_var_names=sorted(ev), overridden_env_vars=['RAY_TMPDIR', 'TMPDIR'],
        worker_process_setup_hook=env['worker_process_setup_hook'], stage=stage,
        required_worker_module='refinery_order_eval')
