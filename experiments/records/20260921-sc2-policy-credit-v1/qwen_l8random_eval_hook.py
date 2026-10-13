"""Only a frozen seed/arm adapter to the accepted common64 evaluation contract."""
import os
from qwen_l8random_plan import stage_spec


def install():
    from feedback_eval import install as evaluate
    spec=stage_spec(os.environ['SC2_ACCEPTANCE_STAGE'])
    evaluate(expected_step=spec['expected_step'],game_seeds=spec['seeds'],expected_temperature=.8,
             answer_description='online Qwen L8; no replay or replacement')


def runtime_environment(resolved_config, ray_tmp, *, stage_resolver=stage_spec,
                        worker_hook='qwen_l8random_eval_hook.install', difficulty='CheatVision'):
    import copy
    import hashlib
    import json
    from pathlib import Path
    path=Path(resolved_config)
    if not 0<path.stat().st_size<1024**2: raise ValueError('Small resolved config required')
    raw=path.read_bytes();cfg=json.loads(raw);env=copy.deepcopy(cfg['ray_init']['runtime_env']);ev=env['env_vars']
    spec=stage_resolver(ev['SC2_ACCEPTANCE_STAGE']);t=cfg['trainer']
    if (env.get('worker_process_setup_hook')!=worker_hook
            or ev.get('SC2PATH')!='/assets/StarCraftII' or ev.get('SC2_DIFFICULTY')!=difficulty
            or ev.get('SC2_EXPECTED_DIFFICULTY')!=difficulty or str(ev.get('SC2_L8_RENDEZVOUS_LOW_PORT'))!='1'
            or not all(ev.get(k) for k in ('PYTHONPATH','SC2_EVAL_SEEDS_LOG_PATH','SC2_RUNTIME_LOG_ROOT'))
            or not t['val_only'] or not t['val_before_train'] or t['save_freq']!=-1
            or t['n_gpus_per_node']!=8 or t['sc2_checkpoint_resume']
            or t['resume_mode']!=('resume_path' if spec['checkpoint'] else 'disable')
            or (spec['checkpoint'] and t['resume_from_path']!=str(spec['checkpoint']))):
        raise ValueError('Matching frozen L8 paired evaluation config required')
    ev.update(TMPDIR=str(ray_tmp),RAY_TMPDIR=str(ray_tmp))
    return env,dict(resolved_config_sha256=hashlib.sha256(raw).hexdigest(),
        env_sha256=hashlib.sha256(json.dumps(env,sort_keys=True).encode()).hexdigest(),
        env_var_names=sorted(ev),overridden_env_vars=['RAY_TMPDIR','TMPDIR'],
        worker_process_setup_hook=env['worker_process_setup_hook'],stage=ev['SC2_ACCEPTANCE_STAGE'],
        required_worker_module='feedback_eval')
