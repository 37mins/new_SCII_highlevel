"""Approved original SpB L8 random96, own native CP2, validation32 and paired64.

Reuse the accepted L8 queue/verifiers; the profile is installed only in this
process. Historical deployments are immutable. No automatic retry or CP192.
"""
import copy
import json
from pathlib import Path
import subprocess as sp
import sys
import time
import unittest

import qwen_l8random197 as shared
import spb_l8random_plan as plan
import spb_l8random_eval197 as evaluation
import storage_batch197
from agent_system.sc2_policy_resume import normalized_protocol,prefix_files,sha256,verify_contract

a,f,h=shared.a,shared.f,shared.h
BASE_CPU=shared.cpu
BASE_CHECK_CPU=shared.check_cpu
ROOT,EVAL_ROOT,SOURCE_PARENT,PARTS=plan.ROOT,plan.EVAL_ROOT,plan.SOURCE_PARENT,plan.PARTS
BASE=Path('/var/jfsCache/sc2-spb-l7random96-197-20260923-r1/spb-random/short')
BASE_SHA='83f3530765babe048035524ddf1651291810818a'
BASE_CONFIG=BASE/'cpu/train2/resolved_config.json'
BASE_CONFIG_SHA256='fe0e3c00571eabc7e625ea192b55f6e360d5a6cb3d53c602085a81bada1fed5b'
PRIOR=Path('/var/jfsCache/sc2-qwen-l8random96-197-20260928-r3')
PRIOR_EVAL=Path('/var/jfsCache/sc2-qwen-l8random-paired192-197-20260928-r3')
PRIOR_SHA='ad81511b270f782420208ac8a6f305a141e8042b'
AUTHORIZATION=('Sep29 approved r2 original SpB L8 random96:1048 new natural games/96PPO; '
    'train+selection24h/192GPUh/320GiB, selection6h/48GPUh/8GiB included; '
    'primary128 games6h/48GPUh/32GiB; renewed suite30h/240GPUh; old+new six roots352GiB; '
    'r1 retains24 consumed games and about4.9655GPUh separately, total1072 games; '
    'CP2/32/64/96 full, protectCP2+latest2+validation-best, only own nonbestCP32 prune; '
    'no old deletion/automatic retry/CP192')


def configure():
    h.sample=storage_batch197.sample
    for name in ('ROOT','EVAL_ROOT','SOURCE_PARENT','PARTS','SELECTION_ROOT'):
        setattr(shared,name,getattr(plan,name))
    shared.BASE,shared.BASE_SHA=BASE,BASE_SHA
    shared.BASE_CONFIG,shared.BASE_CONFIG_SHA256=BASE_CONFIG,BASE_CONFIG_SHA256
    shared.MODEL_KIND='spb'
    shared.TRAIN_SECONDS,shared.EVAL_SECONDS,shared.SUITE_SECONDS=86400,21600,108000
    shared.TRAIN_GPU_HOURS,shared.SUITE_GPU_HOURS,shared.TRAIN_FREE_GIB=192,240,416
    shared.NEW_GAMES=1048
    shared.PRIOR_ROOT,shared.PRIOR_MASTER,shared.PRIOR_SHA,shared.PRIOR_CONTROLLER=PRIOR,PRIOR,PRIOR_SHA,PRIOR_SHA
    shared.PRIOR_DEADLINE=1790639115.4663188
    shared.prepare,shared.configure,shared.accounts=prepare,configure,accounts
    shared.contract_for,shared.predecessor_complete,shared.compare_same=contract_for,predecessor_complete,compare_baseline
    shared.cpu=cpu
    shared.check_cpu=check_cpu
    shared.fresh.ROOT,shared.fresh.PARTS,shared.fresh.PREFIX=ROOT,PARTS,ROOT.name+'-'
    f.SUITE,f.PARTS,f.CONTAINER_PREFIX=ROOT,PARTS,ROOT.name+'-'
    f.DOCKER_SCRIPT=a.HERE/'spb_l8random197.py'
    f.parent_for=shared.parent_for
    f.invocation,f.verify=shared.invocation,shared.verify
    evaluation.configure_profile()


def accounts(deadline):
    return [dict(roots=[plan.OLD_ROOT,plan.OLD_SOURCE_PARENT,ROOT,SOURCE_PARENT],receipt_root=ROOT/'train-storage',limit=320*a.GIB,deadline=deadline),
        dict(roots=list(plan.EVAL_STORAGE_ROOTS),receipt_root=EVAL_ROOT/'eval-storage',limit=32*a.GIB,deadline=deadline),
        dict(roots=[plan.SELECTION_ROOT],receipt_root=ROOT/'selection-storage',limit=8*a.GIB,deadline=deadline),
        dict(roots=[plan.OLD_ROOT,plan.OLD_EVAL_ROOT,plan.OLD_SOURCE_PARENT,ROOT,EVAL_ROOT,SOURCE_PARENT],receipt_root=ROOT/'suite-storage',limit=352*a.GIB,deadline=deadline)]


def prepare():
    if ROOT.exists() or EVAL_ROOT.exists() or a.SOURCE!=SOURCE_PARENT/'code':
        raise RuntimeError('Fresh exact SpB roots required; no overwrite/retry')
    plan.validate();sha=a.cmd(['git','-C',a.SOURCE,'rev-parse','HEAD'])
    a.clean(a.SOURCE,sha);a.clean(a.ORCH,a.ORCH_SHA)
    failed=a.read(plan.OLD_ROOT/'queue-state.json')
    old=a.read(plan.OLD_ROOT/'deployment.json')
    if failed['phase']!='failed' or old['runtime_sha']!='f7497ab5a1876a5e899f3e620758850c996212d6':
        raise RuntimeError('Exact retained failed r1 required; never restart/adopt its CP2')
    shared.fresh.queue_impl.host.writers_clear([plan.OLD_ROOT,plan.OLD_EVAL_ROOT,plan.OLD_SOURCE_PARENT])
    base=a.read(BASE/'deployment.json')
    if (base['runtime_sha'],base['model_kind'],base['difficulty'],base['seed_protocol'],
            base['host']['model'],base['model_mount'])!=(BASE_SHA,'spb','VeryHard','independent_uniform101',
            '/data/yangjinyue/sc2-spb2-level7-20260814/model','/assets/spb'):
        raise RuntimeError('Exact original SpB baseline required')
    shared.baseline_config()
    ROOT.mkdir()
    for name in ('train-storage','suite-storage','selection-storage'): (ROOT/name).mkdir()
    a.STORAGE_LOCK_ROOT=ROOT
    sp.run(['git','clone','--quiet','--no-local',str(a.SOURCE),str(ROOT/'runtime')],check=True,timeout=120)
    a.cmd(['git','-C',ROOT/'runtime','checkout','--quiet','--detach',sha])
    for index,part in enumerate(PARTS):
        owner=ROOT/part;owner.mkdir(parents=True)
        for name in ('runs','cpu','tmp','tmp/task-home','tmp/cache','tmp/cuda-cache'): (owner/name).mkdir()
        (owner/'runtime').symlink_to(ROOT/'runtime',target_is_directory=True)
        cfg=copy.deepcopy(base)
        for key in ('prior_failed_root','retained_prefix','fixed_deadline','original_start','deadline'): cfg.pop(key,None)
        cfg.update(runtime_sha=sha,controller_sha=sha,controller_source=str(a.SOURCE),
            orchestration_sha=a.ORCH_SHA,difficulty='CheatVision',
            seed_protocol=shared.PROTOCOL,seed_group_mode=shared.GROUP,
            training_seeds=[shared.ablation_seeds(shared.PROTOCOL,0,i,1,8) for i in range(96)],
            stages=['pre','train2','post'] if index==0 else ['train96','eval96'],
            games=[8,16,8] if index==0 else [752,8],updates=[0,2,0] if index==0 else [94,0],
            run_prefix=ROOT.name+('-short' if index==0 else '-long'),worker_hook='l7_followup_hook.install',
            wall_seconds=86400,gpu_hours=192,output_limit_bytes=320*a.GIB,saved_steps=[2,32,64,96],
            first_dispatch_by=time.time()+4*3600,queue_expires=time.time()+4*3600,
            no_retry=True,original_weights=True,no_long_training=False,successors_authorized=index==0,
            authorization=AUTHORIZATION,host_stage_entry_log=True,storage_supervision='host-guardian-v1',
            predecessor=str(PRIOR if index==0 else ROOT/PARTS[0]),
            limitation='Mixed-seed advantage may mix difficulty; fixed benchmark already used by Qwen; no learning claim')
        a.save(owner/'deployment.json',cfg,lock_root=ROOT)
    a.save(ROOT/'deployment.json',dict(runtime_sha=sha,controller_sha=sha,controller_source=str(a.SOURCE),
        orchestration_sha=a.ORCH_SHA,authorization=AUTHORIZATION,parts=PARTS,predecessor=str(PRIOR),
        train_seconds=86400,eval_seconds=21600,suite_seconds=108000,gpu_hours=240,
        new_games=1048,new_updates=96,seed_sha256=plan.SEED_SHA256,eval_seeds=plan.SEEDS,
        saved_steps=[2,32,64,96],selection_seeds=plan.SELECTION_SEEDS,selection_sha256=plan.SELECTION_SHA256,
        selection_after_training=True,retention=dict(latest=2,protected=[2,96],best_metric='validation32 wins',
            tie='earlier step',no_training_or_test_selection=True,prune_after_selection=True),
        storage_roots=[str(p) for p in accounts(time.time()+4*3600)[-1]['roots']],no_retry=True,
        sampling_version='single-pause-batch-v1',prior_failed_root=str(plan.OLD_ROOT),
        repeated_games=24,cumulative_games=1072,
        successors_authorized=False),lock_root=ROOT)
    base=a.read(ROOT/PARTS[0]/'deployment.json')
    evaluation.prepare(base,sha);evaluation.prepare(base,sha,True)
    h.sample(accounts(time.time()+4*3600),ROOT)


def compare_baseline(config):
    expected=normalized_protocol(shared.baseline_config())
    ev=expected['ray_init']['runtime_env']['env_vars']
    ev.update(SC2_DIFFICULTY='CheatVision',SC2_EXPECTED_DIFFICULTY='CheatVision',SC2_L8_RENDEZVOUS_LOW_PORT='1')
    actual=normalized_protocol(config)
    if actual!=expected: raise RuntimeError('SpB L7-to-L8 drift beyond difficulty and registered operational controls')


def contract_for():
    owner=ROOT/PARTS[0]
    c=dict(version='accepted-spb-l8-random-full-state-prefix-v1',parent=str(owner),
        checkpoint=str(owner/'runs/train2/checkpoints/global_step_2'),parent_sha=a.read(owner/'deployment.json')['runtime_sha'],
        start_step=2,target_step=96,driver_rng_unavailable_accepted=False,
        files={n:sha256(owner/n) for n in prefix_files()})
    verify_contract(c);return c


def cpu(index):
    BASE_CPU(index)
    path=a.ROOT/'baseline-config-comparison.json'
    proof=a.read(path)
    proof.update(scientific_changes=['difficulty VeryHard to CheatVision'],
        comparison_model='original SpB, unchanged independent seed training',
        operational_changes=['L8 rendezvous port','sparse checkpoint cadence','run/output/clock/resource controls'])
    a.save(path,proof)


def check_cpu():
    BASE_CHECK_CPU()
    proof=a.read(ROOT/'host-storage-probes.json')
    if not proof['passed'] or proof['runtime_sha']!=a.read(ROOT/'deployment.json')['runtime_sha']:
        raise RuntimeError('Matching actual host storage probes required')
    for name in ('cpu-host-lifecycle','cpu-batch-churn'):
        if not a.read(ROOT/name/'result.json')['passed']:
            raise RuntimeError('Actual CPU storage probe failed: '+name)


def predecessor_complete():
    state=shared.receipts.small(PRIOR/'queue-state.json')
    if state['phase']=='failed': raise RuntimeError('Previous Qwen failed; no bypass')
    if state['phase']!='completed': return False
    if (state['exit_code']!=0 or state['completed']!=['qwen-random/short','qwen-random/long','selection32','paired64']
            or a.read(PRIOR/'deployment.json')['runtime_sha']!=PRIOR_SHA):
        raise RuntimeError('Exact completed Qwen suite required')
    for owner,stages in [(PRIOR/'qwen-random/short',['pre','train2','post']),
                         (PRIOR/'qwen-random/long',['train96','eval96']),
                         (PRIOR_EVAL,shared.receipts.small(PRIOR_EVAL/'deployment.json')['stages'])]:
        deadline=a.read(owner/'dispatch.json')['deadline']
        shared.receipts.validate_terminal(owner,stages,deadline)
        for stage in stages:
            shared.receipts.terminal_container(owner,stage,deadline)
            out=owner/'runs'/stage;r=shared.receipts.small(out/'result.json')
            accepted=shared.receipts.small(owner/f'acceptance-{stage}.json')
            manifest=shared.receipts.small(out/'manifest.json')
            if (r!=shared.receipts.small(out/'.done') or r!=accepted['result'] or r['status']!='completed'
                    or r['process_exit_code']!=0 or not r['metrics_finite'] or r['metrics_precision']!='binary64-v1'
                    or r['episode_outcomes']['truncated'] or manifest['source_commit']!=PRIOR_SHA
                    or manifest['dirty'] or manifest['world_size']!=8):
                raise RuntimeError('Prior accepted terminal evidence changed')
    return True


def regressions(host_only=False):
    # Run defaults before installing this process-local SpB profile. Tests restore their globals.
    sys.path[:0]=[str(a.SOURCE/'tests'),str(a.SOURCE/'scripts')]
    if host_only:
        if Path('/.dockerenv').exists(): raise RuntimeError('Real host required')
        names=['test_l7_host_continuation197','test_host_stage197','test_storage_quiescent197','test_storage_batch197',
               'test_policy_credit_storage197','test_policy_credit_storage_coordination197']
    else:
        import torch
        names=['test_spb_l8random197','test_qwen_l8random197','test_qwen_l8random_retention',
            'test_spb_l7_random197','test_sc2_policy_resume','test_sc2_checkpoint_resume',
            'test_qwen_l8_probe_env','test_qwen_l8_remainder3_197','test_metric_precision',
            'test_sc2_action_support','test_sc2_policy_credit','test_sc2_no_thinking_torch',
            'test_sc2_reset_startup','test_sc2_generation_tokens','test_policy_credit_acceptance197']
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
        configure()
        shared.main()
