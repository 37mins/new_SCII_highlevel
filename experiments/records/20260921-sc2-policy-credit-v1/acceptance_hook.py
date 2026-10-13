"""Only paired evaluation seeds/RNG and read-only game observers; no answer intervention."""
import hashlib
import os


# Preregistered independently of all game results. Training uses native RandomState(0).
EVAL_SEEDS = [int.from_bytes(hashlib.sha256(
    f'sc2-policy-credit-acceptance-20260921-v1:{i}'.encode()).digest()[:4], 'big')
    for i in range(8)]


def install():
    from feedback_eval import install as install_feedback
    from refinery_order_eval import install_game_observers
    stage = os.environ['SC2_ACCEPTANCE_STAGE']
    if stage == 'train2':
        install_game_observers()
    elif stage in ('pre', 'post'):
        install_feedback(expected_step=0 if stage == 'pre' else 2,
                         game_seeds=EVAL_SEEDS, expected_temperature=0.8)
    else:
        raise ValueError('Undeclared acceptance stage')
