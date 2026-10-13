"""Approved CP2/CP8 diagnostic on the existing development seed benchmark."""
from pathlib import Path
from qwen_heldout_plan import SEEDS

PARENT = Path('/var/jfsCache/sc2-l7-followup197-20260922-r4/spb-same')
ARMS = ('cp2', 'cp8')
CHECKPOINTS = {'cp2': PARENT/'short/runs/train2/checkpoints/global_step_2',
               'cp8': PARENT/'long/runs/train96/checkpoints/global_step_8'}
STAGES = [f'b{b:02d}-{arm}' for b in range(8)
          for arm in (ARMS if b % 2 == 0 else ARMS[::-1])]


def stage_spec(stage):
    if stage not in STAGES:
        raise ValueError('Undeclared early-checkpoint stage')
    batch = int(stage[1:3]); arm = stage[4:]
    return dict(batch=batch, arm=arm, model='spb', expected_step=int(arm[2:]),
                checkpoint=CHECKPOINTS[arm], seeds=SEEDS[batch*8:(batch+1)*8])
