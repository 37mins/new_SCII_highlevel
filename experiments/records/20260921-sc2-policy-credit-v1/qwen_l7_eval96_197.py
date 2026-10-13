"""Approved CP96-only continuation, retaining the failed historical gradient gate."""
import argparse
import copy
import fcntl
import json
import math
import os
from pathlib import Path
import subprocess as sp
import sys
import time

import acceptance197 as a
import qwen_l7_long197 as old
from agent_system.sc2_policy_resume import sha256, normalized_protocol
from agent_system.sc2_seed_protocol import ablation_seeds

HERE, SOURCE = a.HERE, a.SOURCE
ROOT = Path('/var/jfsCache/sc2-qwen-l7eval96-197-20260922-r1')
HISTORY = old.ROOT
HISTORY_SOURCE = Path('/var/jfsCache/sc2-qwen-l7same96-197-source-20260922-r1')
PREFIX = old.PARENT
CHECKPOINT = HISTORY/'runs/train96/checkpoints/global_step_96'
CONTAINER = 'sc2-qwen-l7eval96-197-20260922-r1'
DEADLINE = 1790227126.5133374
UNKNOWN = [7, 9, 10, 56, 65, 92]
BASE_INVOCATION, BASE_DOCKER = a.invocation, a.docker


def storage_roots():
    return [ROOT, SOURCE.parent, HISTORY, HISTORY_SOURCE, PREFIX]


def history_evidence():
    """Hash-bound known exception, not a general waiver and never old-run acceptance."""
    frozen = a.read(HERE/'qwen-l7-terminal-20260922-171508.json')
    hashes = {}
    for raw, expected in frozen['receipts'].items():
        path = Path(raw)
        if not path.is_relative_to(HISTORY) or path.name == 'storage-state.json':
            continue
        if path.stat().st_size > 1024*1024 or sha256(path) != expected['sha256']:
            raise RuntimeError('Historical receipt changed: '+raw)
        hashes[raw] = expected['sha256']
    result = a.read(HISTORY/'runs/train96/result.json')
    if (result != a.read(HISTORY/'runs/train96/.done') or result['status'] != 'completed'
            or result['process_exit_code'] != 0 or not result['metrics_finite']
            or (result['start_step'],result['last_global_step'],result['completed_steps']) != (2,96,94)
            or result['episode_outcomes']['natural_games'] != 752 or result['episode_outcomes']['truncated']):
        raise RuntimeError('Historical completed training subprocess mismatch')
    rows = a.read(HISTORY/'runs/train96/metrics.json')
    if ([int(x['step']) for x in rows] != list(range(3,97))
            or [int(x['step']) for x in rows if x['actor/grad_norm'] == 0] != UNKNOWN
            or any(not math.isfinite(x['actor/grad_norm']) or x['actor/grad_norm'] < 0
                   or not math.isfinite(x['policy_credit/invalid_advantage_max'])
                   or x['policy_credit/invalid_advantage_max'] > 0
                   or not math.isfinite(x['timing_s/update_actor']) or x['timing_s/update_actor'] <= 0 for x in rows)):
        raise RuntimeError('Exception is limited to the six unchanged rounded gradients')
    seeds = [json.loads(x) for x in (HISTORY/'runs/train96/training_seeds.jsonl').read_text().splitlines()]
    if len(seeds) != 94 or any(x['reset_index'] != i or x['seed_protocol'] != 'same_uniform101'
            or x['seeds'] != ablation_seeds('same_uniform101',0,i,1,8) for i,x in enumerate(seeds,2)):
        raise RuntimeError('Historical seed sequence mismatch')
    checkpoint_inventory(result)
    if (HISTORY/'runs/eval96').exists():
        raise RuntimeError('Prior final evaluation exists; refuse duplicate games')
    if a.read(HISTORY/'dispatch.json')['deadline'] != DEADLINE:
        raise RuntimeError('Original deadline changed')
    return dict(version='approved-rounded-gradient-gap-v1', approved=True,
        historical_terminal_acceptance='failed, unchanged', historical_gradient_unknown=UNKNOWN,
        historical_receipts_sha256=hashes, checkpoint=str(CHECKPOINT), retraining=False,
        interpretation='CP96 behavior only; not retroactive full training acceptance')


def checkpoint_inventory(result):
    # Recorder fingerprints its final CP only. Intermediate CPs retain the
    # original strict 26-nonempty-file stat gate, not invented saved byte counts.
    names = ['data.pt','sc2_state.pt']+[f'actor/{k}_world_size_8_rank_{r}.pt'
        for k in ('model','optim','extra_state') for r in range(8)]
    for step in range(8,97,8):
        for name in names:
            relative = f'checkpoints/global_step_{step}/{name}'
            size = (HISTORY/'runs/train96'/relative).stat().st_size
            if size <= 0 or (step == 96 and size != result['checkpoint_files'][relative]['bytes']):
                raise RuntimeError('Historical checkpoint inventory changed')


def configure():
    cfg = a.read(ROOT/'deployment.json')
    a.ROOT = ROOT
    a.STORAGE_LOCK_ROOT = ROOT
    a.RUNTIME_SHA = cfg['runtime_sha']
    a.CONTAINER = CONTAINER
    a.DOCKER_SCRIPT = HERE/'qwen_l7_eval96_197.py'
    a.invocation, a.verify, a.budget = invocation, verify, budget


def prepare():
    if ROOT.exists(): raise RuntimeError('Fresh evaluation root required; no retry')
    proof = history_evidence()
    sha = a.cmd(['git','-C',SOURCE,'rev-parse','HEAD'])
    a.clean(SOURCE,sha); a.clean(a.ORCH,a.ORCH_SHA)
    cfg = copy.deepcopy(a.read(HISTORY/'deployment.json'))
    cfg.update(runtime_sha=sha,controller_sha=sha,controller_source=str(SOURCE),
        predecessor=str(HISTORY),stages=['eval96'],games=[8],updates=[0],
        run_prefix='qwen-l7eval96-197-r1',wall_seconds=48*3600,gpu_hours=384,
        absolute_deadline=DEADLINE,queue_expires=DEADLINE-45,
        storage_roots=list(map(str,storage_roots())),output_limit_bytes=1024*a.GIB,
        no_retry=True,no_long_training=True,successors_authorized=True,
        authorization='User approved retaining CP96, exactly8 paired zero-update final games with original deadline/budget; '
        'accepts six historical gradients unresolved and old failure retained; then new SpB same and Qwen random queue under existing budgets')
    ROOT.mkdir()
    for name in ('runs','cpu','tmp'): (ROOT/name).mkdir()
    a.cmd(['git','clone','--quiet','--shared',SOURCE,ROOT/'runtime'])
    a.cmd(['git','-C',ROOT/'runtime','checkout','--quiet','--detach',sha])
    a.save(ROOT/'historical-evidence-gap.json',proof,lock_root=ROOT)
    a.save(ROOT/'deployment.json',cfg,lock_root=ROOT)


def invocation(cfg,stage,dry=False):
    if stage != 'eval96': raise ValueError('Only eight-game zero-update eval96 authorized')
    args,env,out = BASE_INVOCATION(cfg,'post',dry)
    target = ROOT/('cpu' if dry else 'runs')/'eval96'
    args = [x.replace(str(out),str(target)) for x in args]
    settings = {'+ray_init.runtime_env.env_vars.SC2_ACCEPTANCE_STAGE':"'eval96'",
        'trainer.total_training_steps':'96','trainer.total_epochs':'1','trainer.save_freq':'-1',
        'trainer.resume_mode':'resume_path','trainer.resume_from_path':str(CHECKPOINT)}
    args = [x for x in args if x.split('=',1)[0] not in settings]
    args += [k+'='+v for k,v in settings.items()]
    env.update(OUTPUT_DIR=str(target),RUN_ID=cfg['run_prefix']+'-eval96',
        SC2_CHECKPOINT_RESUME='False',RAY_TMPDIR='/tmp/qe96')
    return args,env,target


def budget(deadline):
    if deadline != DEADLINE: raise RuntimeError('Cannot reset original deadline')
    a.measure_budget(storage_roots(),ROOT,1024*a.GIB,DEADLINE,
        'Original48h/384GPUh deadline; no extension','Original1TiB includes every retained and new root',lock_root=ROOT)


def docker(mode):
    args = BASE_DOCKER('execute' if mode=='execute' else 'cpu')
    for path in (HISTORY,HISTORY_SOURCE,PREFIX,PREFIX.parent/'runtime'):
        args[2:2] = ['-v',f'{path}:{path}:ro']
    if mode != 'execute':
        model = a.read(ROOT/'deployment.json')['host']['model']
        args[args.index(f'{model}:/assets/qwen:ro')] = f'{old.CPU_MODEL}:/assets/qwen:ro'
        args[args.index('--name')+1] += '-'+mode
        args[2:2] = ['-v',f'{old.SPB_METADATA}:/metadata/spb:ro',
            '-e','SC2_TEST_SPB_METADATA_PATH=/metadata/spb','-e','SC2_TEST_QWEN_METADATA_PATH=/assets/qwen',
            '-e','SC2_TEST_TOKENIZER_PATH=/assets/qwen','-e','OMP_NUM_THREADS=2','-e','TOKENIZERS_PARALLELISM=false']
    args[-1] = mode
    return args


def cpu():
    # Reuse actual launcher/Hydra/config/source checks; only small prefix states.
    old.ROOT,old.invocation = ROOT,invocation
    old.cpu()
    expected = a.read(HISTORY/'cpu/eval96/resolved_config.json')
    actual = a.read(ROOT/'cpu/eval96/resolved_config.json')
    if normalized_protocol(expected) != normalized_protocol(actual):
        raise RuntimeError('Final evaluation protocol differs beyond allowed relocation')
    history_evidence()
    a.save(ROOT/'cpu/protocol-match.json',dict(passed=True,old_sha=sha256(HISTORY/'cpu/eval96/resolved_config.json'),
        new_sha=sha256(ROOT/'cpu/eval96/resolved_config.json'),checkpoint=str(CHECKPOINT),zero_new_training=True))


def verify(stage,write=True):
    if stage != 'eval96': raise ValueError('Only eval96')
    out = ROOT/'runs/eval96'
    result,evidence = a.verify_common(out,stage,8)
    manifest = a.read(out/'manifest.json')
    if result.get('metrics_precision') != 'binary64-v1' or manifest.get('metrics_precision') != 'binary64-v1':
        raise RuntimeError('New full-precision receipt required')
    proof = a.read(out/'checkpoint_evaluation.json')
    seeds = [json.loads(x)['seeds'] for x in (out/'evaluation_seeds.jsonl').read_text().splitlines()]
    if (result['training_updates'] != 0 or proof['optimizer_updates'] != 0 or not proof['val_only']
            or proof['loaded_global_step'] != 96 or not proof['checkpoint_load_returned']
            or proof['checkpoint'] != str(CHECKPOINT) or proof['game_seeds'] != a.EVAL_SEEDS or seeds != [a.EVAL_SEEDS]):
        raise RuntimeError('Actual CP96 paired evaluation mismatch')
    for rank in range(8):
        if not old.paired_rng_matches(a.read(out/f'sampling-rank{rank}.json'),
                a.read(PREFIX/f'runs/post/sampling-rank{rank}.json'),rank):
            raise RuntimeError('Paired rank RNG mismatch')
    evidence.update(historical=history_evidence(),training_updates=0)
    if write: a.save(ROOT/'acceptance-eval96.json',dict(result=result,evidence=evidence,checked_at=time.time()))


def queue():
    cfg = a.read(ROOT/'deployment.json')
    a.clean(SOURCE,cfg['controller_sha']); a.clean(ROOT/'runtime',cfg['runtime_sha']); a.clean(a.ORCH,a.ORCH_SHA)
    for name in ('readiness','regressions'):
        p = a.read(ROOT/f'{name}.json')
        if not p['passed'] or p['cuda_initialized'] or p.get('skips',0) or p['runtime_sha'] != cfg['runtime_sha']:
            raise RuntimeError('Actual zero-skip CPU gates required')
    if not a.read(ROOT/'cpu/protocol-match.json')['passed']:
        raise RuntimeError('Actual old/new final evaluation protocol equality required')
    with (ROOT/'queue.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (ROOT/'queue-state.json').exists() or (ROOT/'dispatch.json').exists():
            raise RuntimeError('Already queued; no retry')
        process = None
        try:
            history_evidence()
            state = json.loads(a.cmd(['docker','inspect','--format','{{json .State}}','sc2-qwen-l7same96-197-20260922-r1']))
            if state['Running'] or state['ExitCode'] != 1: raise RuntimeError('Historical terminal container changed')
            a.save(ROOT/'queue-state.json',dict(phase='waiting-resources',deadline=DEADLINE))
            old.ROOT = ROOT
            while True:
                budget(DEADLINE)
                if old.resources_ready(): break
                time.sleep(60)
            with (ROOT/'fsync-probe').open('xb') as stream:
                stream.write(b'qwen-cp96-eval\n');stream.flush();os.fsync(stream.fileno())
            if (ROOT/'fsync-probe').read_bytes() != b'qwen-cp96-eval\n': raise RuntimeError('Fsync mismatch')
            args = docker('execute')
            a.save(ROOT/'dispatch.json',dict(start=time.time(),deadline=DEADLINE,command=args,
                original_start=1790054326.5133374,original_deadline_preserved=True))
            a.save(ROOT/'queue-state.json',dict(phase='dispatched',deadline=DEADLINE))
            with (ROOT/'container.log').open('x') as log:
                process = sp.Popen(args,stdout=log,stderr=sp.STDOUT)
                while process.poll() is None:
                    budget(DEADLINE);time.sleep(15)
            if process.returncode or a.read(ROOT/'state.json')['phase'] != 'completed':
                raise RuntimeError('Final evaluation failed; no retry or successor')
            verify('eval96',write=False)
            a.save(ROOT/'queue-state.json',dict(phase='completed',exit_code=0,deadline=DEADLINE,
                historical_terminal_acceptance='failed, unchanged'))
        except BaseException as exc:
            try: a.save(ROOT/'queue-state.json',dict(phase='failed',error=str(exc),deadline=DEADLINE))
            finally:
                if process is not None: a.stop_owned()
            raise


def regressions():
    import l7_followup197 as f
    # Reuse the full verified Linux suite with new precision/continuation tests.
    f.regressions(0,receipt_root=ROOT)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode',choices=['prepare','cpu','regressions','cpu-command','regressions-command','queue','execute'])
    mode = p.parse_args().mode
    if mode not in ('prepare','regressions'): configure()
    if mode.endswith('-command'): print(json.dumps(docker(mode.removesuffix('-command'))))
    elif mode == 'execute': a.execute()
    else: globals()[mode]()
