"""Sep30 explicitly approved failed-r2 artifact evaluation; never training recovery."""
from pathlib import Path
from acceptance_hook import EVAL_SEEDS
import spb_l8random_plan as old

ROOT = Path('/var/jfsCache/sc2-spb-l8random-recovery264-197-20260930-r1')
SOURCE_PARENT = Path('/var/jfsCache/sc2-spb-l8random-recovery264-197-source-20260930-r1')
OLD_ROOT = old.ROOT
OLD_SHA = '12f3600ca8e6e8edabc460de70860baeef2b5146'
OLD_CID = 'cb1a5950be537f2561c6efad3aafd4645b4bccf1312fd7ed3f467c8d57aa0da8'
OLD_OWNER = OLD_ROOT/'spb-random/long'
CHECKPOINTS = dict(old.SELECTION_CHECKPOINTS)
RETAINED_ROOTS = [old.OLD_ROOT, old.OLD_EVAL_ROOT, old.OLD_SOURCE_PARENT,
    old.ROOT, old.EVAL_ROOT, old.SOURCE_PARENT,
    Path('/var/jfsCache/sc2-terminal-storage-cpu-20260929-r1'),
    Path('/var/jfsCache/sc2-terminal-storage-cpu-source-20260929-r1')]
WALL_SECONDS = 8*3600
STAGES = ['diagnostic-cp96'] + ['sel-'+s for s in old.SELECTION_STAGES] + ['test-'+s for s in old.STAGES]
HOOK_STAGES = ['diagnostic-cp96'] + ['sel-b00-cp'+str(s) for s in (2,32,64,96)] + ['test-b00-original','test-b00-random96']
WORKER_HOOK = 'spb_l8random_recovery_hook.install'
CONTRACT_VERSION = 'approved-failed-spb-l8-r2-evaluation-only-v1'
AUTHORIZATION = ('Sep30 user explicitly approves failed-r2 artifact adoption: diagnosticCP96 eight + '
    'selectionCP2/32/64/96 each32 + primary original/CP96 each64 =264 new natural games/0PPO; '
    '197 eightGPU serial; first GPU operation8wallh/64GPUh/45s cleanup; new two roots32GiB; '
    'all ten roots352GiB; no deletion/copy/retry/training/CP192; old failed status and clocks retained')


def validate():
    old.validate()
    if len(STAGES)!=33 or len(set(STAGES))!=33 or len(set(RETAINED_ROOTS))!=8:
        raise ValueError('Exact approved plan required')
    if set(old.SELECTION_SEEDS)&set(old.SEEDS):
        raise ValueError('Validation/test seeds must remain disjoint')


def stage_spec(stage):
    if stage not in STAGES: raise ValueError('Undeclared recovery stage')
    if stage=='diagnostic-cp96':
        return dict(group='diagnostic',batch=0,arm='cp96',seeds=list(EVAL_SEEDS),
            expected_step=96,checkpoint=CHECKPOINTS['cp96'])
    spec=old.stage_spec(stage.split('-',1)[1])
    return dict(spec,group='selection' if stage.startswith('sel-') else 'primary')


def paired_predecessors(stage):
    spec=stage_spec(stage)
    return [s for s in STAGES[:STAGES.index(stage)]
        if stage_spec(s)['group']==spec['group'] and stage_spec(s)['batch']==spec['batch']]
