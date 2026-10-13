"""L9 fixed-weight evaluation adapter with bounded terminal drain."""
import qwen_l8random_eval197 as shared
import qwen_l8random_retention as retention
import spb_l9random_plan as plan
from spb_l9random_eval_hook import runtime_environment

BASE_INVOCATION=shared.common.invocation


def invocation(cfg,stage,dry=False):
    args,env,out=BASE_INVOCATION(cfg,stage,dry)
    shared.h.terminal_launch(cfg,args,env,plan.ROOT)
    return args,env,out


def configure_profile():
    shared.plan=plan
    shared.TRAIN_ROOT,shared.SOURCE_PARENT,shared.PARTS=plan.ROOT,plan.SOURCE_PARENT,plan.PARTS
    shared.stage_spec,shared.runtime_environment=plan.stage_spec,runtime_environment
    shared.MODEL_KIND,shared.DIFFICULTY='spb','CheatMoney'
    shared.TERMINAL_HANDOFF=True
    shared.ENTRY_SCRIPT='spb_l9random_eval197.py'
    shared.WORKER_HOOK='spb_l9random_eval_hook.install'
    shared.SELECTION_SECONDS=6*3600
    shared.common.invocation=invocation
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
    shared._prepare(base,sha,root,stages,seeds,digest,checkpoints,21600,128,48,
        (8 if selection else 32)*shared.a.GIB,selection)
    cfg=shared.a.read(root/'deployment.json')
    cfg['authorization']='Sep30 approved L9 SpB validation128 + original/fixedCP96 paired128; no pruning/retry/CP192'
    shared.a.save(root/'deployment.json',cfg,lock_root=plan.ROOT)


if __name__=='__main__':
    configure_profile()
    shared.main()
