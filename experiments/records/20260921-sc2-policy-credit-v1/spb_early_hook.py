"""Supply only frozen seeds/expected load to the existing evaluation observer."""
import os
from spb_early_plan import stage_spec


def install():
    from feedback_eval import install as evaluate
    spec = stage_spec(os.environ['SC2_MATRIX_STAGE'])
    evaluate(expected_step=spec['expected_step'], game_seeds=spec['seeds'],
             expected_temperature=.8, answer_description='online spb; no replay or replacement')
