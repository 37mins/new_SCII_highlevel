"""Thin two-arm SpB adapter to the accepted L8 evaluator and retention controller."""
import qwen_l8random_eval197 as shared
import qwen_l8random_retention as retention
import spb_l8random_plan as plan
from spb_l8random_eval_hook import runtime_environment


def configure_profile():
    shared.plan=plan
    shared.TRAIN_ROOT=plan.ROOT
    shared.SOURCE_PARENT=plan.SOURCE_PARENT
    shared.PARTS=plan.PARTS
    shared.stage_spec=plan.stage_spec
    shared.runtime_environment=runtime_environment
    shared.MODEL_KIND='spb'
    shared.ENTRY_SCRIPT='spb_l8random_eval197.py'
    shared.WORKER_HOOK='spb_l8random_eval_hook.install'
    shared.SELECTION_SECONDS=6*3600
    for name in ('ROOT','PARTS','SELECTION_ROOT','SAVED_STEPS','SELECTION_ARMS',
                 'SELECTION_STAGES','SELECTION_CHECKPOINTS','SELECTION_SEEDS','SELECTION_SHA256'):
        setattr(retention,name,getattr(plan,name))


def prepare(base,sha,selection=False):
    configure_profile()
    root=plan.SELECTION_ROOT if selection else plan.EVAL_ROOT
    stages=plan.SELECTION_STAGES if selection else plan.STAGES
    seeds=plan.SELECTION_SEEDS if selection else plan.SEEDS
    digest=plan.SELECTION_SHA256 if selection else plan.SEED_SHA256
    checkpoints=plan.SELECTION_CHECKPOINTS if selection else plan.CHECKPOINTS
    shared._prepare(base,sha,root,stages,seeds,digest,checkpoints,6*3600,128,48,
                    (8 if selection else 32)*shared.a.GIB,selection)
    cfg=shared.a.read(root/'deployment.json')
    cfg['authorization']='Sep29 approved r2 SpB L8 original/random96 paired128 and validation128; old+new six roots352GiB; no retry/CP192/old deletion'
    shared.a.save(root/'deployment.json',cfg,lock_root=plan.ROOT)


if __name__=='__main__':
    configure_profile()
    shared.main()
