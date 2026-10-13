"""Read-only observers and the existing eight-seed paired final evaluation."""
import os
from acceptance_hook import EVAL_SEEDS


def install():
    if os.environ['SC2_ACCEPTANCE_STAGE'] == 'train96':
        from refinery_order_eval import install_game_observers
        install_game_observers()
    elif os.environ['SC2_ACCEPTANCE_STAGE'] == 'eval96':
        from feedback_eval import install as evaluate
        evaluate(expected_step=96, game_seeds=EVAL_SEEDS, expected_temperature=0.8)
    else:
        raise ValueError('Undeclared Qwen long stage')
