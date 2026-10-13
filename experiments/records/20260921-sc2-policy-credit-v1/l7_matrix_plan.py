"""Four missing L7 evaluation arms; reuse the outcome-independent 64 seeds."""
from pathlib import Path
from qwen_heldout_plan import SEEDS, stage_spec as original_spec

BASE = Path('/var/jfsCache')
ARMS = ('spb-original', 'spb-same', 'spb-random', 'qwen-random')
PARENTS = {
    'qwen-random': BASE/'sc2-qwen-random-cp8-197-20260923-r2',
    'spb-same': BASE/'sc2-l7-followup197-20260922-r4/spb-same/long',
    'spb-random': BASE/'sc2-spb-l7random96-197-20260923-r1/spb-random/long',
}
CHECKPOINTS = {k: v/'runs/train96/checkpoints/global_step_96' for k,v in PARENTS.items()}
# Rotate four positions twice, fixed before collecting any new-arm outcomes.
STAGES = [f'b{b:02d}-{arm}' for b in range(8)
          for arm in ARMS[b % 4:]+ARMS[:b % 4]]


def stage_spec(stage):
    if stage not in STAGES:
        raise ValueError('Undeclared matrix stage')
    batch = int(stage[1:3]); arm = stage[4:]
    seeds = original_spec(f'b{batch:02d}-original')['seeds']
    return dict(batch=batch, arm=arm, seeds=seeds,
                model='qwen' if arm.startswith('qwen') else 'spb',
                expected_step=0 if arm == 'spb-original' else 96,
                checkpoint=CHECKPOINTS.get(arm))
