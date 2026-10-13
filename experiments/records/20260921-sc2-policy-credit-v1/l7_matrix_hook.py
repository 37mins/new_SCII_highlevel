"""Select frozen matrix seeds; reuse read-only actual-load/RNG/game observers."""
import os
from l7_matrix_plan import stage_spec


def install():
    from feedback_eval import install as evaluate
    spec = stage_spec(os.environ['SC2_MATRIX_STAGE'])
    evaluate(expected_step=spec['expected_step'], game_seeds=spec['seeds'],
             expected_temperature=0.8,
             answer_description='online '+spec['model']+'; no replay or replacement')
