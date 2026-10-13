"""Predeclared L8 Qwen dynamic-range screen; no training or successor."""
import random
from pathlib import Path

from qwen_heldout_plan import SEEDS as L7_HELDOUT_SEEDS
from acceptance_hook import EVAL_SEEDS as L7_ORIGINAL_EVAL_SEEDS

BASE = Path('/var/jfsCache')
ARMS = ('original', 'same-cp96', 'random-cp96')
PARENTS = {
    'same-cp96': BASE/'sc2-qwen-l7same96-197-20260924-r1',
    'random-cp96': BASE/'sc2-qwen-random-cp8-197-20260923-r2',
}
CHECKPOINTS = {
    'same-cp96': PARENTS['same-cp96']/'qwen-same/long/runs/train96/checkpoints/global_step_96',
    'random-cp96': PARENTS['random-cp96']/'runs/train96/checkpoints/global_step_96',
}
# Fixed before L8 outcomes; disjoint from the 64 L7 held-out seeds and 0..100 training draws.
SEEDS = random.Random(20260925).sample(range(65536, 2**32 - 1), 32)
assert (len(set(SEEDS)) == 32 and not set(SEEDS) & set(L7_HELDOUT_SEEDS)
        and not set(SEEDS) & set(L7_ORIGINAL_EVAL_SEEDS))
STAGES = [f'b{batch:02d}-{arm}' for batch in range(4)
          for arm in ARMS[batch % 3:]+ARMS[:batch % 3]]


def stage_spec(stage):
    if stage not in STAGES:
        raise ValueError('Undeclared L8 stage')
    batch = int(stage[1:3]); arm = stage[4:]
    return dict(batch=batch, arm=arm, seeds=SEEDS[8*batch:8*(batch+1)],
                expected_step=0 if arm == 'original' else 96,
                checkpoint=CHECKPOINTS.get(arm))
