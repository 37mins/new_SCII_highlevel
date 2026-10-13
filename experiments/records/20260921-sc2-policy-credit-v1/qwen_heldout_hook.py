"""Only select declared eval seeds and install existing read-only observers."""
import os
from qwen_heldout_plan import stage_spec


def install():
    from feedback_eval import install as evaluate
    spec = stage_spec(os.environ['SC2_HELDOUT_STAGE'])
    evaluate(expected_step=spec['expected_step'], game_seeds=spec['seeds'],
             expected_temperature=0.8, answer_description='online Qwen; no replay or replacement')
