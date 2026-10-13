"""Approved fresh SpB L9 random96 after the complete L8 recovery evaluator.

Thin process-local profile of existing queue/strict verifiers. No retry, transfer,
checkpoint pruning, CP192, same-seed or L10 successor is authorized.
"""
import copy
from pathlib import Path
import subprocess as sp
import sys
import time
import unittest

import qwen_l8random197 as shared
import spb_l8random197 as reference
import spb_l9random_plan as plan
import spb_l9random_eval197 as evaluation
import spb_l8random_recovery_plan as predecessor
import storage_batch197
from agent_system.sc2_policy_resume import normalized_protocol,prefix_files,sha256,verify_contract

a,f,h=shared.a,shared.f,shared.h
ROOT,EVAL_ROOT,SOURCE_PARENT,PARTS=plan.ROOT,plan.EVAL_ROOT,plan.SOURCE_PARENT,plan.PARTS
BASE,BASE_SHA,BASE_CONFIG,BASE_CONFIG_SHA256=reference.BASE,reference.BASE_SHA,reference.BASE_CONFIG,reference.BASE_CONFIG_SHA256
PRIOR=predecessor.ROOT
PRIOR_SHA='d6932869ac75a34d6a244c8879c76ab61982d88a'
PRIOR_DEADLINE=1790759506.6293833
AUTHORIZATION=('Sep30 user approved original SpB L9 random96 after unchanged accepted L8 recovery264: '
    '1048 new natural games/96PPO; 197 eightGPU serial; train+selection24h/192GPUh/320GiB; '
    'selection6h/48GPUh/8GiB included; primary128games6h/48GPUh/32GiB; suite30h/240GPUh/352GiB; '
    'first GPU starts fixed clocks with45s cleanup; CP2/32/64/96 full retained, best reference only; '
    'no deletion/retry/transfer/CP192/same/L10/other nodes')


def configure():
    h.sample=storage_batch197.sample
    for name in ('ROOT','EVAL_ROOT','SOURCE_PARENT','PARTS','SELECTION_ROOT'):
        setattr(shared,name,getattr(plan,name))
    shared.BASE,shared.BASE_SHA=BASE,BASE_SHA
    shared.BASE_CONFIG,shared.BASE_CONFIG_SHA256=BASE_CONFIG,BASE_CONFIG_SHA256
    shared.MODEL_KIND,shared.DIFFICULTY='spb','CheatMoney'
    shared.PRUNE_AFTER_SELECTION=False
    shared.TRAIN_SECONDS,shared.EVAL_SECONDS,shared.SUITE_SECONDS=86400,21600,108000
    shared.TRAIN_GPU_HOURS,shared.SUITE_GPU_HOURS,shared.TRAIN_FREE_GIB=192,240,416
    shared.NEW_GAMES=1048
    shared.PRIOR_ROOT,shared.PRIOR_MASTER,shared.PRIOR_SHA,shared.PRIOR_CONTROLLER=PRIOR,PRIOR,PRIOR_SHA,PRIOR_SHA
    shared.PRIOR_DEADLINE=PRIOR_DEADLINE
    shared.prepare,shared.configure,shared.accounts=prepare,configure,accounts
    shared.contract_for,shared.predecessor_complete,shared.compare_same=contract_for,predecessor_complete,compare_baseline
    shared.cpu,shared.check_cpu=cpu,check_cpu
    shared.fresh.ROOT,shared.fresh.PARTS,shared.fresh.PREFIX=ROOT,PARTS,ROOT.name+'-'
    f.SUITE,f.PARTS,f.CONTAINER_PREFIX=ROOT,PARTS,ROOT.name+'-'
    f.DOCKER_SCRIPT=a.HERE/'spb_l9random197.py'
    f.parent_for=shared.parent_for
    f.invocation,f.verify=shared.invocation,shared.verify
    evaluation.configure_profile()


def accounts(deadline):
    return [dict(roots=[ROOT,SOURCE_PARENT],receipt_root=ROOT/'train-storage',limit=320*a.GIB,deadline=deadline),
        dict(roots=[EVAL_ROOT,SOURCE_PARENT],receipt_root=EVAL_ROOT/'eval-storage',limit=32*a.GIB,deadline=deadline),
        dict(roots=[plan.SELECTION_ROOT],receipt_root=ROOT/'selection-storage',limit=8*a.GIB,deadline=deadline),
        dict(roots=[ROOT,EVAL_ROOT,SOURCE_PARENT],receipt_root=ROOT/'suite-storage',limit=352*a.GIB,deadline=deadline)]


def prepare():
    if ROOT.exists() or EVAL_ROOT.exists() or a.SOURCE!=SOURCE_PARENT/'code':
        raise RuntimeError('Fresh exact L9 roots required; no overwrite/retry')
    plan.validate();sha=a.cmd(['git','-C',a.SOURCE,'rev-parse','HEAD'])
    a.clean(a.SOURCE,sha);a.clean(a.ORCH,a.ORCH_SHA)
    base=a.read(BASE/'deployment.json')
    if (base['runtime_sha'],base['model_kind'],base['difficulty'],base['seed_protocol'],
            base['host']['model'],base['model_mount'])!=(BASE_SHA,'spb','VeryHard','independent_uniform101',
            '/data/yangjinyue/sc2-spb2-level7-20260814/model','/assets/spb'):
        raise RuntimeError('Exact original SpB template required')
    shared.baseline_config()
    ROOT.mkdir();a.STORAGE_LOCK_ROOT=ROOT
    for name in ('train-storage','suite-storage','selection-storage'): (ROOT/name).mkdir()
    sp.run(['git','clone','--quiet','--no-local',str(a.SOURCE),str(ROOT/'runtime')],check=True,timeout=120)
    a.cmd(['git','-C',ROOT/'runtime','checkout','--quiet','--detach',sha])
    for index,part in enumerate(PARTS):
        owner=ROOT/part;owner.mkdir(parents=True)
        for name in ('runs','cpu','tmp','tmp/task-home','tmp/cache','tmp/cuda-cache'): (owner/name).mkdir()
        (owner/'runtime').symlink_to(ROOT/'runtime',target_is_directory=True)
        cfg=copy.deepcopy(base)
        for key in ('prior_failed_root','retained_prefix','fixed_deadline','original_start','deadline'): cfg.pop(key,None)
        cfg.update(runtime_sha=sha,controller_sha=sha,controller_source=str(a.SOURCE),
            orchestration_sha=a.ORCH_SHA,difficulty='CheatMoney',
            seed_protocol=shared.PROTOCOL,seed_group_mode=shared.GROUP,
            training_seeds=[shared.ablation_seeds(shared.PROTOCOL,0,i,1,8) for i in range(96)],
            stages=['pre','train2','post'] if index==0 else ['train96','eval96'],
            games=[8,16,8] if index==0 else [752,8],updates=[0,2,0] if index==0 else [94,0],
            run_prefix=ROOT.name+('-short' if index==0 else '-long'),worker_hook='l7_followup_hook.install',
            wall_seconds=86400,gpu_hours=192,output_limit_bytes=320*a.GIB,saved_steps=[2,32,64,96],
            first_dispatch_by=PRIOR_DEADLINE+4*3600,queue_expires=PRIOR_DEADLINE+4*3600,
            no_retry=True,original_weights=True,no_long_training=False,successors_authorized=index==0,
            authorization=AUTHORIZATION,host_stage_entry_log=True,storage_supervision='host-guardian-v1',
            terminal_handoff='terminal-drain-v1',predecessor=str(PRIOR if index==0 else ROOT/PARTS[0]),
            limitation='Mixed-seed advantage can mix difficulty; reused benchmark numbers on new level; one training stream')
        a.save(owner/'deployment.json',cfg,lock_root=ROOT)
    a.save(ROOT/'deployment.json',dict(runtime_sha=sha,controller_sha=sha,controller_source=str(a.SOURCE),
        orchestration_sha=a.ORCH_SHA,authorization=AUTHORIZATION,parts=PARTS,predecessor=str(PRIOR),
        predecessor_sha=PRIOR_SHA,predecessor_deadline=PRIOR_DEADLINE,
        train_seconds=86400,eval_seconds=21600,suite_seconds=108000,gpu_hours=240,
        new_games=1048,new_updates=96,seed_sha256=plan.SEED_SHA256,eval_seeds=plan.SEEDS,
        saved_steps=[2,32,64,96],selection_seeds=plan.SELECTION_SEEDS,selection_sha256=plan.SELECTION_SHA256,
        selection_after_training=True,retention=dict(retained=[2,32,64,96],best_reference_only=True,
            best_metric='validation32 wins',tie='earlier step',no_training_or_test_selection=True,prune_after_selection=False),
        storage_roots=[str(p) for p in (ROOT,EVAL_ROOT,SOURCE_PARENT)],no_retry=True,
        sampling_version='single-pause-batch-v1',terminal_handoff='terminal-drain-v1',successors_authorized=False),lock_root=ROOT)
    cfg=a.read(ROOT/PARTS[0]/'deployment.json')
    evaluation.prepare(cfg,sha);evaluation.prepare(cfg,sha,True)
    h.sample(accounts(PRIOR_DEADLINE+4*3600),ROOT)


def compare_baseline(config):
    expected=normalized_protocol(shared.baseline_config())
    expected['ray_init']['runtime_env']['env_vars'].update(SC2_DIFFICULTY='CheatMoney',
        SC2_EXPECTED_DIFFICULTY='CheatMoney',SC2_L8_RENDEZVOUS_LOW_PORT='1')
    if normalized_protocol(config)!=expected:
        raise RuntimeError('Unapproved drift beyond difficulty and registered operational controls')


def contract_for():
    owner=ROOT/PARTS[0]
    c=dict(version='accepted-spb-l9-random-full-state-prefix-v1',parent=str(owner),
        checkpoint=str(owner/'runs/train2/checkpoints/global_step_2'),parent_sha=a.read(owner/'deployment.json')['runtime_sha'],
        start_step=2,target_step=96,driver_rng_unavailable_accepted=False,
        files={n:sha256(owner/n) for n in prefix_files()})
    verify_contract(c);return c


def cpu(index):
    reference.BASE_CPU(index)
    path=a.ROOT/'baseline-config-comparison.json';proof=a.read(path)
    proof.update(scientific_changes=['difficulty VeryHard to CheatMoney'],comparison_model='original SpB',
        operational_changes=['low rendezvous port','sparse full checkpoints','bounded terminal drain','run/output/budgets'])
    a.save(path,proof)


def check_cpu():
    reference.BASE_CHECK_CPU()
    sha=a.read(ROOT/'deployment.json')['runtime_sha']
    proof=a.read(ROOT/'host-storage-probes.json')
    if not proof['passed'] or proof['runtime_sha']!=sha: raise RuntimeError('Actual matching host probes required')
    for name in ('cpu-host-lifecycle','cpu-batch-churn','cpu-terminal-drain'):
        proof=a.read(ROOT/name/'result.json')
        if not proof['passed']: raise RuntimeError('CPU probe failed: '+name)
        if name=='cpu-terminal-drain' and (proof['source_sha']!=sha or not proof['cpu_only'] or proof['games'] or proof['updates']):
            raise RuntimeError('Matching no-GPU terminal probe required')


def predecessor_complete():
    read=shared.receipts.small
    state=read(PRIOR/'queue-state.json')
    if state['phase']=='failed': raise RuntimeError('L8 recovery failed; L9 blocked without retry')
    if state['phase']!='completed': return False
    cfg=read(PRIOR/'deployment.json');clock=read(PRIOR/'dispatch.json')
    if (state['exit_code']!=0 or state['completed']!=predecessor.STAGES
            or cfg['runtime_sha']!=PRIOR_SHA or clock['deadline']!=PRIOR_DEADLINE):
        raise RuntimeError('Exact fully completed predecessor required')
    a.clean(PRIOR/'runtime',PRIOR_SHA)
    shared.receipts.validate_terminal(PRIOR,predecessor.STAGES,PRIOR_DEADLINE)
    for stage in predecessor.STAGES:
        shared.receipts.terminal_container(PRIOR,stage,PRIOR_DEADLINE)
        out=PRIOR/'runs'/stage;r=read(out/'result.json');accepted=read(PRIOR/f'acceptance-{stage}.json')
        manifest=read(out/'manifest.json');spec=predecessor.stage_spec(stage);load=read(out/'checkpoint_evaluation.json')
        if (r!=read(out/'.done') or r!=accepted['result'] or r['status']!='completed' or r['process_exit_code']!=0
                or r['training_updates']!=0 or not r['metrics_finite'] or r['metrics_precision']!='binary64-v1'
                or r['episode_outcomes']['natural_games']!=8 or r['episode_outcomes']['truncated']
                or manifest['source_commit']!=PRIOR_SHA or manifest['dirty'] or manifest['world_size']!=8
                or accepted['evidence']['consumed_answers']<=0
                or accepted['evidence']['consumed_answers']!=accepted['evidence']['valid_consumed_answers']
                or not load['val_only'] or load['optimizer_updates']!=0 or load['loaded_global_step']!=spec['expected_step']
                or load['checkpoint']!=(str(spec['checkpoint']) if spec['checkpoint'] else None)
                or load['checkpoint_load_returned']!=bool(spec['checkpoint']) or load['game_seeds']!=spec['seeds']):
            raise RuntimeError('Predecessor accepted terminal/load evidence changed: '+stage)
        for rank in range(8):
            rng=read(out/f'sampling-rank{rank}.json')
            if (rng['rank'],rng['seed'])!=(rank,rank): raise RuntimeError('Predecessor rank RNG mismatch')
            for previous in predecessor.paired_predecessors(stage):
                if not f.previous.paired_rng_matches(rng,read(PRIOR/f'runs/{previous}/sampling-rank{rank}.json'),rank):
                    raise RuntimeError('Predecessor paired RNG mismatch')
    return True


def regressions(host_only=False):
    sys.path[:0]=[str(a.SOURCE/'tests'),str(a.SOURCE/'scripts')]
    if host_only:
        if Path('/.dockerenv').exists(): raise RuntimeError('Real host required')
        names=['test_l7_host_continuation197','test_host_stage197','test_storage_quiescent197',
            'test_storage_batch197','test_terminal_storage197','test_policy_credit_storage197','test_policy_credit_storage_coordination197']
    else:
        import torch
        names=['test_spb_l9random197','test_spb_l8random197','test_qwen_l8random197','test_qwen_l8random_retention',
            'test_spb_l7_random197','test_sc2_policy_resume','test_sc2_checkpoint_resume',
            'test_qwen_l8_probe_env','test_qwen_l8_remainder3_197','test_metric_precision','test_sc2_action_support',
            'test_sc2_policy_credit','test_sc2_no_thinking_torch','test_sc2_reset_startup',
            'test_sc2_generation_tokens','test_policy_credit_acceptance197']
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromNames(names))
    cuda=False if host_only else torch.cuda.is_initialized()
    proof=dict(passed=result.wasSuccessful() and not result.skipped and not cuda,tests=result.testsRun,
        skips=len(result.skipped),cuda_initialized=cuda,host_only=host_only,
        runtime_sha=a.read(ROOT/'deployment.json')['runtime_sha'],checked_at=time.time())
    a.save(ROOT/'host-regressions.json' if host_only else ROOT/PARTS[0]/'regressions.json',proof,lock_root=ROOT)
    if not proof['passed']: raise RuntimeError('All zero-skip CPU gates required')


if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1] in ('regressions','host-regressions'):
        regressions(sys.argv[1]=='host-regressions')
    else:
        configure();shared.main()
