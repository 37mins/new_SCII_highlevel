"""Sep30 approved original SpB L9 random96; no L8 checkpoint transfer."""
from pathlib import Path
import qwen_l8random_plan as reference

ROOT=Path('/var/jfsCache/sc2-spb-l9random96-197-20260930-r1')
EVAL_ROOT=Path('/var/jfsCache/sc2-spb-l9random-paired128-197-20260930-r1')
SOURCE_PARENT=Path('/var/jfsCache/sc2-spb-l9random96-197-source-20260930-r1')
SELECTION_ROOT=ROOT/'selection'
EVAL_STORAGE_ROOTS=(EVAL_ROOT,SOURCE_PARENT)
PARTS=('spb-random/short','spb-random/long')
ARMS=('original','random96')
SAVED_STEPS=(2,32,64,96)
SELECTION_ARMS=tuple('cp'+str(s) for s in SAVED_STEPS)
SELECTION_CHECKPOINTS={'cp'+str(s):ROOT/PARTS[0 if s==2 else 1]/
    ('runs/train2' if s==2 else 'runs/train96')/f'checkpoints/global_step_{s}' for s in SAVED_STEPS}
CHECKPOINTS={'random96':SELECTION_CHECKPOINTS['cp96']}
SEEDS,SEED_SHA256=list(reference.SEEDS),reference.SEED_SHA256
SELECTION_SEEDS,SELECTION_SHA256=list(reference.SELECTION_SEEDS),reference.SELECTION_SHA256
STAGES=[f'b{b:02d}-{arm}' for b in range(8) for arm in ARMS[b%2:]+ARMS[:b%2]]
SELECTION_STAGES=[f'b{b:02d}-{arm}' for arm in SELECTION_ARMS for b in range(4)]
ANALYSIS_SEED,BOOTSTRAP_SAMPLES=2026092801,100000


def validate():
    reference.validate()
    if (SEEDS!=reference.SEEDS or SELECTION_SEEDS!=reference.SELECTION_SEEDS
            or SEED_SHA256!=reference.SEED_SHA256 or SELECTION_SHA256!=reference.SELECTION_SHA256):
        raise ValueError('Frozen disjoint benchmark and selection lists required')


def stage_spec(stage):
    validate()
    if stage not in STAGES+SELECTION_STAGES: raise ValueError('Undeclared L9 SpB evaluation stage')
    batch=int(stage[1:3]);arm=stage[4:]
    if stage in SELECTION_STAGES:
        return dict(batch=batch,arm=arm,seeds=SELECTION_SEEDS[8*batch:8*batch+8],
            expected_step=int(arm[2:]),checkpoint=SELECTION_CHECKPOINTS[arm])
    return dict(batch=batch,arm=arm,seeds=SEEDS[8*batch:8*batch+8],
        expected_step=0 if arm=='original' else 96,checkpoint=CHECKPOINTS.get(arm))
