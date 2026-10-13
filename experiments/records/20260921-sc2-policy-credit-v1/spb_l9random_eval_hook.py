"""L9 model/seed adapter: live SpB answers, never replayed actions."""
import os
from spb_l9random_plan import stage_spec
from qwen_l8random_eval_hook import runtime_environment as shared_environment


def install():
    from feedback_eval import install as evaluate
    spec=stage_spec(os.environ['SC2_ACCEPTANCE_STAGE'])
    evaluate(expected_step=spec['expected_step'],game_seeds=spec['seeds'],expected_temperature=.8,
        answer_description='online original SpB or own L9 checkpoint; no replay or replacement')


def runtime_environment(resolved_config,ray_tmp):
    return shared_environment(resolved_config,ray_tmp,stage_resolver=stage_spec,
        worker_hook='spb_l9random_eval_hook.install',difficulty='CheatMoney')
