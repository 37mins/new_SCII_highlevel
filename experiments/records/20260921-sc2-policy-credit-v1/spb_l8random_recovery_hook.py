"""Frozen adapter: online SpB, declared seeds, real checkpoint load, zero updates."""
import os
from spb_l8random_recovery_plan import stage_spec, WORKER_HOOK, ROOT
from qwen_l8random_eval_hook import runtime_environment as base_environment


def install():
    from feedback_eval import install as evaluate
    spec=stage_spec(os.environ['SC2_ACCEPTANCE_STAGE'])
    evaluate(expected_step=spec['expected_step'],game_seeds=spec['seeds'],expected_temperature=.8,
        answer_description='online original SpB or explicitly adopted failed-r2 artifact; no replacement')


def runtime_environment(config,ray_tmp):
    import json
    from pathlib import Path
    env,proof=base_environment(config,ray_tmp,stage_resolver=stage_spec,worker_hook=WORKER_HOOK)
    cfg=json.loads(Path(config).read_text())
    if cfg['trainer'].get('sc2_terminal_handoff_lock_root')!=str(ROOT):
        raise ValueError('Explicit new-root terminal-drain control required')
    return env,proof
