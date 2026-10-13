"""Approved original-SpB L8 random96; reused Qwen benchmark, not an unseen test."""
from pathlib import Path
import qwen_l8random_plan as reference

OLD_ROOT=Path('/var/jfsCache/sc2-spb-l8random96-197-20260928-r1')
OLD_EVAL_ROOT=Path('/var/jfsCache/sc2-spb-l8random-paired128-197-20260928-r1')
OLD_SOURCE_PARENT=Path('/var/jfsCache/sc2-spb-l8random96-197-source-20260928-r1')
ROOT=Path('/var/jfsCache/sc2-spb-l8random96-197-20260929-r2')
EVAL_ROOT=Path('/var/jfsCache/sc2-spb-l8random-paired128-197-20260929-r2')
SOURCE_PARENT=Path('/var/jfsCache/sc2-spb-l8random96-197-source-20260929-r2')
SELECTION_ROOT=ROOT/'selection'
EVAL_STORAGE_ROOTS=(OLD_EVAL_ROOT,OLD_SOURCE_PARENT,EVAL_ROOT,SOURCE_PARENT)
PARTS=('spb-random/short','spb-random/long')
ARMS=('original','random96')
CHECKPOINTS={'random96':ROOT/PARTS[1]/'runs/train96/checkpoints/global_step_96'}
SEEDS,SEED_SHA256=list(reference.SEEDS),reference.SEED_SHA256
SELECTION_SEEDS,SELECTION_SHA256=list(reference.SELECTION_SEEDS),reference.SELECTION_SHA256
SAVED_STEPS=(2,32,64,96)
SELECTION_ARMS=tuple('cp'+str(s) for s in SAVED_STEPS)
SELECTION_CHECKPOINTS={'cp'+str(s):ROOT/PARTS[0 if s==2 else 1]/
    ('runs/train2' if s==2 else 'runs/train96')/f'checkpoints/global_step_{s}' for s in SAVED_STEPS}
STAGES=[f'b{b:02d}-{arm}' for b in range(8) for arm in ARMS[b%2:]+ARMS[:b%2]]
SELECTION_STAGES=[f'b{b:02d}-{arm}' for arm in SELECTION_ARMS for b in range(4)]
ANALYSIS_SEED,BOOTSTRAP_SAMPLES=2026092801,100000


def validate():
    reference.validate()
    if (SEEDS!=reference.SEEDS or SELECTION_SEEDS!=reference.SELECTION_SEEDS
            or SEED_SHA256!=reference.SEED_SHA256 or SELECTION_SHA256!=reference.SELECTION_SHA256):
        raise ValueError('Identical registered Qwen benchmark/validation seeds required')


def stage_spec(stage):
    validate()
    if stage not in STAGES+SELECTION_STAGES: raise ValueError('Undeclared SpB evaluation stage')
    batch=int(stage[1:3]);arm=stage[4:]
    if stage in SELECTION_STAGES:
        return dict(batch=batch,arm=arm,seeds=SELECTION_SEEDS[8*batch:8*batch+8],
                    expected_step=int(arm[2:]),checkpoint=SELECTION_CHECKPOINTS[arm])
    return dict(batch=batch,arm=arm,seeds=SEEDS[8*batch:8*batch+8],
                expected_step=0 if arm=='original' else 96,checkpoint=CHECKPOINTS.get(arm))
