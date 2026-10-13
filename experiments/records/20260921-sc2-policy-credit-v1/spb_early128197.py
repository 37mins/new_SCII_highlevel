"""One-shot approved SpB CP2/CP8 evaluation; compose accepted queue helpers."""
import argparse
import copy
import json
from pathlib import Path
import sys
import time
import unittest

import l7_matrix256197 as m
from spb_early_plan import ARMS, CHECKPOINTS, PARENT, SEEDS, STAGES, stage_spec

a, q, h = m.a, m.q, m.h
ROOT = Path('/var/jfsCache/sc2-spb-early128-197-20260925-r1')
SOURCE_PARENT = Path('/var/jfsCache/sc2-spb-early128-197-source-20260925-r1')
PREFIX = 'sc2-spb-early128-197-20260925-r1'
BASELINE = Path('/var/jfsCache/sc2-l7-matrix256-197-20260924-r1')
BASELINE_SHA = '72068c693266dcf74ed8d0d2eb984f834ca8a030'
PARENT_SHA = '9cb291ea5f50de205c5d88371e08ce229b7d9d04'
PARENT_PROOF = a.HERE/'spb-early128-parents-20260925.json'
BASELINE_PROOF = a.HERE/'l7-matrix256-complete-20260925.json'
WALL_SECONDS, LIMIT = 6*3600, 32*a.GIB


def configure():
    # Process-local binding of the existing thin launch/verification helpers.
    # Frozen old deployments are not imported as mutable working trees or edited.
    a.ROOT = a.STORAGE_LOCK_ROOT = q.ROOT = m.ROOT = ROOT
    a.CONTAINER = q.PREFIX = m.PREFIX = PREFIX
    a.DOCKER_SCRIPT = a.HERE/'spb_early128197.py'
    q.SOURCE_PARENT = m.SOURCE_PARENT = SOURCE_PARENT
    q.STAGES = m.STAGES = STAGES
    m.ARMS = ARMS; m.CHECKPOINTS = CHECKPOINTS; m.stage_spec = stage_spec
    q.WALL_SECONDS = m.WALL_SECONDS = WALL_SECONDS
    q.LIMIT = m.LIMIT = LIMIT
    q.predecessor = predecessor; q.docker = m.docker; q.verify = verify
    q.admit = m.admit; q.accounts = m.accounts
    if (ROOT/'deployment.json').exists():
        a.RUNTIME_SHA = m.small(ROOT/'deployment.json')['runtime_sha']


def require_inventory(checkpoint, files, expected):
    required = ['data.pt','sc2_state.pt'] + [f'actor/{k}_world_size_8_rank_{r}.pt'
        for k in ('model','optim','extra_state') for r in range(8)]
    if set(files) != set(required):
        raise RuntimeError('Exactly 26 required checkpoint files expected')
    for name in required:
        value = files[name]
        path = checkpoint/name
        if (not value['exists'] or not isinstance(value['bytes'],int) or value['bytes'] <= 0
                or expected.get(name) != value['bytes'] or path.is_symlink()
                or not path.is_file() or path.stat().st_size != value['bytes']):
            raise RuntimeError('Parent checkpoint inventory changed: '+name)


def predecessor():
    proof = m.small(PARENT_PROOF)
    for path,sha in proof['receipt_sha256'].items():
        if not Path(path).is_relative_to(PARENT) or m.digest(path) != sha:
            raise RuntimeError('Parent receipt changed: '+path)
    retained = m.small(a.HERE/'plotted-checkpoint-prune-20260924-plan.json')['retained_inventory']
    for part,stages,arm in [('short',['pre','train2','post'],'cp2'),('long',['train96','eval96'],'cp8')]:
        root = PARENT/part; item = proof['parts'][part]
        if item['root'] != str(root) or item['checkpoint'] != str(CHECKPOINTS[arm]) or item['runtime_sha'] != PARENT_SHA:
            raise RuntimeError('Wrong parent identity')
        a.clean(root/'runtime',PARENT_SHA)
        deadline = item['state']['deadline']
        m.validate_terminal(root,stages,deadline)
        for stage in stages:
            m.terminal_container(root,stage,deadline,item['guardians'][stage]['container_id'])
            result = m.small(root/f'runs/{stage}/result.json')
            if (result != m.small(root/f'runs/{stage}/.done')
                    or result != m.small(root/f'acceptance-{stage}.json')['result']
                    or result['process_exit_code'] != 0 or result['status'] != 'completed'):
                raise RuntimeError('Parent result terminal mismatch')
        if arm == 'cp2':
            result = m.small(root/'runs/train2/result.json')
            expected = {k.removeprefix('checkpoints/global_step_2/'):v['bytes']
                        for k,v in result['checkpoint_files'].items() if k.startswith('checkpoints/global_step_2/')}
        else:
            prefix = str(CHECKPOINTS[arm])+'/'
            expected = {v['path'][len(prefix):]:v['bytes'] for v in retained if v['path'].startswith(prefix)}
        require_inventory(CHECKPOINTS[arm],item['files'],expected)
    base = m.small(BASELINE_PROOF)
    for rel,sha in base['receipt_sha256']['matrix'].items():
        if m.digest(BASELINE/rel) != sha:
            raise RuntimeError('Completed baseline receipt changed: '+rel)
    cfg = m.small(BASELINE/'deployment.json')
    if cfg['runtime_sha'] != BASELINE_SHA or cfg['eval_seeds'] != SEEDS:
        raise RuntimeError('Baseline source/seeds mismatch')
    a.clean(BASELINE/'runtime',BASELINE_SHA)
    deadline = base['roots']['matrix']['dispatch']['deadline']
    m.validate_terminal(BASELINE,cfg['stages'],deadline,queue=True)
    for item in base['stages']:
        if item['root_key'] == 'matrix':
            m.terminal_container(BASELINE,item['stage'],deadline,item['container_id'])
    return dict(passed=True,checked_at=time.time(),parent_sha=PARENT_SHA,
        baseline_sha=BASELINE_SHA,parent_proof_sha256=m.digest(PARENT_PROOF),
        baseline_proof_sha256=m.digest(BASELINE_PROOF),checkpoint_contents_read=False,
        checkpoints={k:str(v) for k,v in CHECKPOINTS.items()},required_files_each=26,
        limitation='evaluation only; no historical legacy/native training equivalence claim')


def prepare():
    if ROOT.exists() or a.SOURCE != SOURCE_PARENT/'code':
        raise RuntimeError('New exact roots required; no overwrite/retry')
    sha = a.cmd(['git','-C',a.SOURCE,'rev-parse','HEAD'])
    a.clean(a.SOURCE,sha); a.clean(a.ORCH,a.ORCH_SHA)
    proof = predecessor()
    base = copy.deepcopy(m.small(PARENT/'long/deployment.json'))
    base.update(runtime_sha=sha,controller_sha=sha,controller_source=str(a.SOURCE),
        worker_hook='spb_early_hook.install',run_prefix=PREFIX,seed_group_mode='same',
        seed_protocol='same_uniform101',difficulty='VeryHard')
    cfg = dict(runtime_sha=sha,controller_sha=sha,controller_source=str(a.SOURCE),
        orchestration_sha=a.ORCH_SHA,arms={arm:copy.deepcopy(base) for arm in ARMS},
        cpu_config_arm='cp2',stages=STAGES,games=[8]*16,updates=[0]*16,eval_seeds=SEEDS,
        wall_seconds=WALL_SECONDS,gpu_hours=48,output_limit_bytes=LIMIT,
        new_games=128,new_updates=0,storage_roots=[str(ROOT),str(SOURCE_PARENT)],
        no_retry=True,no_long_training=True,successors_authorized=False,
        first_dispatch_by=time.time()+2*3600,
        authorization='Sep25 user approved CP2/CP8 128-game regression localization,0updates,197/8GPUs,6h/48GPUh/32GiB,no delete/retry/automatic training',
        seed_plan_sha256=m.digest(a.HERE/'qwen_heldout_plan.py'),
        checkpoint_plan_sha256=m.digest(a.HERE/'spb_early_plan.py'),
        parent_proof_sha256=m.digest(PARENT_PROOF),baseline_proof_sha256=m.digest(BASELINE_PROOF))
    ROOT.mkdir()
    for name in ('runs','cpu','tmp','tmp/task-home','tmp/cache','tmp/cuda-cache'):
        (ROOT/name).mkdir()
    a.cmd(['git','clone','--quiet','--shared',a.SOURCE,ROOT/'runtime'])
    a.cmd(['git','-C',ROOT/'runtime','checkout','--quiet','--detach',sha])
    a.save(ROOT/'deployment.json',cfg); a.save(ROOT/'predecessor-acceptance.json',proof)


def verify(stage):
    spec = stage_spec(stage); out = ROOT/'runs'/stage
    hashes = m.small(BASELINE_PROOF)['receipt_sha256']['matrix']
    rng = [{k:r[k] for k in ('rank','seed','cpu_rng_sha256','cuda_rng_sha256')}
        for r in (m.small(out/f'sampling-rank{i}.json') for i in range(8))]
    for arm in ('spb-original','spb-same'):
        rel = f'acceptance-b{spec["batch"]:02d}-{arm}.json'
        if m.digest(BASELINE/rel) != hashes[rel]:
            raise RuntimeError('Paired baseline acceptance changed')
        old = m.small(BASELINE/rel)
        if old['rng'] != rng or old['seeds'] != spec['seeds']:
            raise RuntimeError('Paired original/CP96 seed or RNG mismatch')
    # Existing verifier checks actual load2/8,0updates,natural games,precision,
    # legality,worker banners,local commands and pair with the other new arm.
    m.verify(stage)
    accepted = m.small(ROOT/f'acceptance-{stage}.json')
    accepted['paired_with'] += [str(BASELINE/f'acceptance-b{spec["batch"]:02d}-{arm}.json')
                               for arm in ('spb-original','spb-same')]
    a.save(ROOT/f'acceptance-{stage}.json',accepted)


def regressions(host_only=False):
    # Run before configure(), keeping original module globals for their tests.
    sys.path[:0] = [str(a.SOURCE/'tests'),str(a.SOURCE/'scripts')]
    if host_only:
        if Path('/.dockerenv').exists(): raise RuntimeError('Actual host tests required')
        names = ['test_l7_host_continuation197','test_host_stage197','test_storage_quiescent197',
                 'test_policy_credit_storage197','test_policy_credit_storage_coordination197']
    else:
        import torch
        names = ['test_spb_early128197','test_l7_matrix256197','test_qwen_heldout128197',
            'test_feedback_eval','test_metric_precision','test_sc2_no_thinking_torch',
            'test_sc2_action_support','test_sc2_reset_startup','test_sc2_generation_tokens',
            'test_policy_credit_acceptance197']
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromNames(names))
    cuda = False if host_only else torch.cuda.is_initialized()
    configure()
    proof = dict(passed=result.wasSuccessful() and not result.skipped and not cuda,
        tests=result.testsRun,skips=len(result.skipped),cuda_initialized=cuda,host_only=host_only,
        runtime_sha=m.small(ROOT/'deployment.json')['runtime_sha'],checked_at=time.time())
    a.save(ROOT/('host-regressions.json' if host_only else 'regressions.json'),proof)
    if not proof['passed']: raise RuntimeError('Zero-skip CPU tests required')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode',choices=['prepare','cpu','regressions','host-regressions',
        'cpu-command','regressions-command','queue','stage'])
    p.add_argument('stage',nargs='?');v=p.parse_args()
    if v.mode in ('regressions','host-regressions'):
        regressions(v.mode=='host-regressions')
    else:
        configure()
        if v.mode.endswith('-command'):print(json.dumps(m.docker(v.mode.removesuffix('-command'))))
        elif v.mode=='cpu':m.cpu()
        elif v.mode=='stage':m.child_stage(v.stage)
        elif v.mode=='queue':q.queue()
        else:prepare()
