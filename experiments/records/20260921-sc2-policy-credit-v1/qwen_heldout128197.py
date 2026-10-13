"""Approved 128-game original/own CP96 paired evaluation, one-shot host queue."""
import argparse
import copy
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess as sp
import sys
import time
import unittest

import acceptance197 as a
import host_stage197 as h
from l7_followup197_r4 import writers_clear
from qwen_l7_long197 import CPU_MODEL, SPB_METADATA
from qwen_heldout_plan import SEEDS, STAGES, stage_spec

ROOT = Path('/var/jfsCache/sc2-qwen-heldout128-197-20260924-r1')
SOURCE_PARENT = Path('/var/jfsCache/sc2-qwen-heldout128-197-source-20260924-r1')
PARENT = Path('/var/jfsCache/sc2-qwen-l7same96-197-20260924-r1')
PARENT_SHA = '5228e9acc7698c69bdcce9af30aa5a7570829a19'
CHECKPOINT = PARENT/'qwen-same/long/runs/train96/checkpoints/global_step_96'
PREFIX = 'sc2-qwen-heldout128-197-20260924-r1'
WALL_SECONDS, LIMIT = 6*3600, 32*a.GIB
BASE_INVOCATION, BASE_DOCKER = a.invocation, a.docker


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def configure():
    a.ROOT = a.STORAGE_LOCK_ROOT = ROOT
    a.CONTAINER = PREFIX
    a.DOCKER_SCRIPT = a.HERE/'qwen_heldout128197.py'
    if (ROOT/'deployment.json').exists():
        a.RUNTIME_SHA = a.read(ROOT/'deployment.json')['runtime_sha']


def predecessor():
    # Reuse hash-bound completed acceptance; never reread checkpoints or full logs.
    proof = a.read(a.HERE/'qwen-l7same-fresh-complete-20260924.json')
    if a.read(PARENT/'queue-state.json')['phase'] != 'completed':
        raise RuntimeError('Fresh Qwen predecessor not completed')
    a.clean(PARENT/'runtime', PARENT_SHA)
    for relative, expected in proof['receipt_sha256'].items():
        path = PARENT/relative
        if path.stat().st_size > 1024*1024 or digest(path) != expected:
            raise RuntimeError('Accepted predecessor receipt changed: '+relative)
    for part, stages in [('short',['pre','train2','post']),('long',['train96','eval96'])]:
        owner = PARENT/'qwen-same'/part
        for name in ('state.json','host-supervision/state.json'):
            state = a.read(owner/name)
            if state['phase'] != 'completed' or state.get('exit_code') != 0 or state['completed'] != stages:
                raise RuntimeError('Predecessor host terminal mismatch')
        for stage in stages:
            receipt = a.read(owner/f'host-supervision/{stage}-guardian.json')
            info = json.loads(a.cmd(['docker','inspect','--format',
                '{"id":"{{.Id}}","owner":"{{index .Config.Labels "sc2.acceptance.root"}}","state":{{json .State}}}',
                'sc2-qwen-l7same96-197-20260924-r1-'+part+'-'+stage]))
            status = info['state']
            if (status['Running'] or status['Paused'] or status['ExitCode'] != 0 or status['OOMKilled']
                    or status['Error'] or info['owner'] != str(owner)
                    or receipt['container_id'] != info['id'] or receipt['owner_root'] != str(owner)
                    or receipt['phase'] != 'completed' or receipt['deadline'] != 1790403303.797456
                    or receipt['final_state']['ExitCode'] != 0 or receipt['final_state']['Running']):
                raise RuntimeError('Predecessor exact container/guardian mismatch')
    result = a.read(PARENT/'qwen-same/long/runs/train96/result.json')
    required = ['data.pt','sc2_state.pt']+[f'actor/{k}_world_size_8_rank_{r}.pt'
        for k in ('model','optim','extra_state') for r in range(8)]
    for name in required:
        size = (CHECKPOINT/name).stat().st_size
        if size <= 0 or size != result['checkpoint_files']['checkpoints/global_step_96/'+name]['bytes']:
            raise RuntimeError('CP96 file inventory changed')
    return dict(passed=True, parent=str(PARENT), runtime_sha=PARENT_SHA,
                checkpoint=str(CHECKPOINT), files=26, checked_at=time.time(),
                acceptance='hash-bound five-stage completion; no historical waiver')


def prepare():
    if ROOT.exists() or a.SOURCE != SOURCE_PARENT/'code':
        raise RuntimeError('New exact roots required; no overwrite/retry')
    sha = a.cmd(['git','-C',a.SOURCE,'rev-parse','HEAD'])
    a.clean(a.SOURCE,sha); a.clean(a.ORCH,a.ORCH_SHA)
    proof = predecessor()
    cfg = copy.deepcopy(a.read(PARENT/'qwen-same/short/deployment.json'))
    cfg.update(runtime_sha=sha,controller_sha=sha,controller_source=str(a.SOURCE),
        predecessor=str(PARENT),stages=STAGES,games=[8]*16,updates=[0]*16,
        training_seeds=[],eval_seeds=SEEDS,run_prefix=PREFIX,worker_hook='qwen_heldout_hook.install',
        wall_seconds=WALL_SECONDS,gpu_hours=48,output_limit_bytes=LIMIT,new_games=128,new_updates=0,
        storage_roots=[str(ROOT),str(SOURCE_PARENT)],no_retry=True,no_long_training=True,
        successors_authorized=False,first_dispatch_by=time.time()+2*3600,
        resource_check='eight empty GPUs/no compute PIDs, 600GiB RAM, 128GiB free NVMe, fsync',
        authorization='Sep24 user explicitly approved 128 paired held-out games,0updates,197/8GPUs,6h/48GPUh/32GiB; new queue128GiB free disk only; no delete/retry',
        limitation='Qwen training-effect evaluation only, not an architecture comparison',
        parent_completion_sha256=digest(a.HERE/'qwen-l7same-fresh-complete-20260924.json'),
        seed_plan_sha256=digest(a.HERE/'qwen_heldout_plan.py'))
    ROOT.mkdir()
    for name in ('runs','cpu','tmp','tmp/task-home','tmp/cache','tmp/cuda-cache'):
        (ROOT/name).mkdir()
    a.cmd(['git','clone','--quiet','--shared',a.SOURCE,ROOT/'runtime'])
    a.cmd(['git','-C',ROOT/'runtime','checkout','--quiet','--detach',sha])
    a.save(ROOT/'deployment.json',cfg)
    a.save(ROOT/'predecessor-acceptance.json',proof)


def invocation(cfg, stage, dry=False):
    spec = stage_spec(stage)
    args,env,old = BASE_INVOCATION(cfg,'pre',dry)
    out = ROOT/('cpu' if dry else 'runs')/stage
    args = [value.replace(str(old),str(out)) for value in args]
    settings = {'trainer.total_training_steps':'96','trainer.total_epochs':'1',
        'trainer.save_freq':'-1','trainer.val_only':'True','trainer.val_before_train':'True',
        'trainer.resume_mode':'resume_path' if spec['expected_step'] else 'disable',
        '+ray_init.runtime_env.env_vars.SC2_HELDOUT_STAGE':"'"+stage+"'"}
    if spec['expected_step']:
        settings['trainer.resume_from_path'] = str(CHECKPOINT)
    args = [value for value in args if value.split('=',1)[0] not in settings]
    args += [key+'='+value for key,value in settings.items()]
    env.update(OUTPUT_DIR=str(out),RUN_ID=PREFIX+'-'+stage,RAY_TMPDIR='/tmp/qh-'+stage)
    return args,env,out


def docker(mode, stage=None):
    cfg = a.read(ROOT/'deployment.json')
    args = BASE_DOCKER('execute' if mode == 'stage' else 'cpu')
    args[2:2] = ['--read-only','--log-driver','none','-e','HOME=/tmp/task-home',
        '-e','XDG_CACHE_HOME=/tmp/cache','-e','CUDA_CACHE_PATH=/tmp/cuda-cache',
        '-v',f'{CHECKPOINT}:{CHECKPOINT}:ro']
    if mode != 'stage':
        args[args.index(f'{cfg["host"]["model"]}:/assets/qwen:ro')] = f'{CPU_MODEL}:/assets/qwen:ro'
        args[2:2] = ['-v',f'{SPB_METADATA}:/metadata/spb:ro','-e','SC2_TEST_SPB_METADATA_PATH=/metadata/spb',
            '-e','SC2_TEST_QWEN_METADATA_PATH=/assets/qwen','-e','SC2_TEST_TOKENIZER_PATH=/assets/qwen',
            '-e','OMP_NUM_THREADS=2','-e','TOKENIZERS_PARALLELISM=false']
    writable = [tuple(args[i+1].split(':')[:2]) for i,v in enumerate(args[:-1])
                if v == '-v' and args[i+1].split(':')[-1] != 'ro']
    if set(writable) != {(str(ROOT),str(ROOT)),(str(ROOT/'tmp'),'/tmp')} or len(writable) != 2:
        raise RuntimeError('Unexpected writable bind')
    args[args.index('--name')+1] = PREFIX+'-'+(stage or mode)
    args[-1] = mode
    if mode == 'stage':
        stage_spec(stage)
        args[1] = 'create'
        args.append(stage)
    return args


def cpu():
    import torch
    from hydra import compose, initialize_config_dir
    from omegaconf import OmegaConf
    from verl.trainer.ppo.sc2_policy_credit import validate_config as credit_config
    from verl.utils.sc2_action_support import validate_config as support_config
    cfg = a.read(ROOT/'deployment.json')
    source = sp.run(['sha256sum','-c','configs/system-v1.sha256'],cwd=ROOT/'runtime',
        capture_output=True,text=True,timeout=30)
    (ROOT/'cpu/source-check.log').write_text(source.stdout+source.stderr)
    if source.returncode: raise RuntimeError('Source manifest mismatch')
    for stage in STAGES:
        args,env,out = invocation(cfg,stage,True)
        p = sp.run(args,env=env,cwd=ROOT/'runtime',capture_output=True,text=True,timeout=90)
        (ROOT/'cpu'/f'{stage}.log').write_text(p.stdout+p.stderr)
        if p.returncode: raise RuntimeError('Actual dry launcher failed: '+stage)
        command = a.read(out/'effective_config.json')['command']
        with initialize_config_dir(config_dir=str(ROOT/'runtime/verl/trainer/config'),version_base=None):
            c = compose(config_name='ppo_trainer',overrides=command[command.index('verl.trainer.main_ppo')+1:])
        credit_config(c); support_config(c)
        spec = stage_spec(stage)
        ev = c.ray_init.runtime_env.env_vars
        if (not c.trainer.val_only or not c.trainer.val_before_train or c.trainer.save_freq != -1
                or c.trainer.n_gpus_per_node != 8 or c.env.val_rollout_n != 8
                or c.trainer.sc2_checkpoint_resume or c.trainer.del_local_ckpt_after_load
                or c.actor_rollout_ref.rollout.response_length != 192
                or c.actor_rollout_ref.rollout.val_kwargs.temperature != 0.8
                or not c.actor_rollout_ref.rollout.val_kwargs.do_sample
                or not c.data.sc2_no_thinking or ev.SC2_HELDOUT_STAGE != stage
                or str(ev.SC2_RESET_CONCURRENCY) != '1' or str(ev.SC2_RESET_RETRIES) != '1'
                or c.trainer.resume_mode != ('resume_path' if spec['expected_step'] else 'disable')
                or (spec['expected_step'] and c.trainer.resume_from_path != str(CHECKPOINT))):
            raise RuntimeError('Resolved evaluation contract mismatch')
        a.save(out/'resolved_config.json',OmegaConf.to_container(c,resolve=True))
    if torch.cuda.is_initialized(): raise RuntimeError('CPU initialized CUDA')
    a.save(ROOT/'readiness.json',dict(passed=True,runtime_sha=cfg['runtime_sha'],stages=STAGES,
        actual_entries_and_hydra_configs=True,cuda_initialized=False,checked_at=time.time()))


def regressions(host_only=False):
    sys.path[:0] = [str(a.SOURCE/'tests'),str(a.SOURCE/'scripts')]
    if host_only:
        if Path('/.dockerenv').exists(): raise RuntimeError('Actual host tests required')
        names = ['test_l7_host_continuation197','test_host_stage197','test_storage_quiescent197',
            'test_policy_credit_storage197','test_policy_credit_storage_coordination197']
    else:
        import torch
        names = ['test_qwen_heldout128197','test_feedback_eval','test_metric_precision',
            'test_sc2_no_thinking_torch','test_sc2_action_support','test_sc2_reset_startup',
            'test_sc2_generation_tokens','test_policy_credit_acceptance197']
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromNames(names))
    cuda = False if host_only else torch.cuda.is_initialized()
    proof = dict(passed=result.wasSuccessful() and not result.skipped and not cuda,tests=result.testsRun,
        skips=len(result.skipped),cuda_initialized=cuda,host_only=host_only,
        runtime_sha=a.read(ROOT/'deployment.json')['runtime_sha'],checked_at=time.time())
    a.save(ROOT/('host-regressions.json' if host_only else 'regressions.json'),proof)
    if not proof['passed']: raise RuntimeError('Zero-skip CPU tests required')


def check_cpu():
    cfg = a.read(ROOT/'deployment.json')
    a.clean(a.SOURCE,cfg['runtime_sha']); a.clean(ROOT/'runtime',cfg['runtime_sha']); a.clean(a.ORCH,a.ORCH_SHA)
    for name in ('readiness.json','regressions.json','host-regressions.json'):
        p = a.read(ROOT/name)
        if not p['passed'] or p.get('skips',0) or p['cuda_initialized'] or p['runtime_sha'] != cfg['runtime_sha']:
            raise RuntimeError('Matching real CPU proof required')


def verify(stage):
    spec = stage_spec(stage); out = ROOT/'runs'/stage
    result,evidence = a.verify_common(out,stage,8)
    if any(a.read(out/p).get('metrics_precision') != 'binary64-v1' for p in ('manifest.json','result.json')):
        raise RuntimeError('Full precision required')
    proof = a.read(out/'checkpoint_evaluation.json')
    ledger = [json.loads(row)['seeds'] for row in (out/'evaluation_seeds.jsonl').read_text().splitlines()]
    if (result['training_updates'] != 0 or not proof['val_only'] or proof['optimizer_updates'] != 0
            or proof['loaded_global_step'] != spec['expected_step'] or proof['games'] != 8
            or proof['checkpoint'] != (str(CHECKPOINT) if spec['expected_step'] else None)
            or proof['checkpoint_load_returned'] != bool(spec['expected_step'])
            or proof['game_seeds'] != spec['seeds'] or ledger != [spec['seeds']]):
        raise RuntimeError('Actual load/seeds/zero-update evidence mismatch')
    outcomes = [json.loads(row) for row in (out/'episode_outcomes.jsonl').read_text().splitlines()]
    if (len(outcomes) != 8 or sorted(x['env_index'] for x in outcomes) != list(range(8))
            or any(not x['terminated'] or x['truncated'] for x in outcomes)):
        raise RuntimeError('Exactly eight distinct natural game outcomes required')
    rng = []
    for rank in range(8):
        r = a.read(out/f'sampling-rank{rank}.json')
        if (r['rank'],r['seed']) != (rank,rank): raise RuntimeError('Sampling rank mismatch')
        rng.append({k:r[k] for k in ('rank','seed','cpu_rng_sha256','cuda_rng_sha256')})
    other = f'b{spec["batch"]:02d}-'+('original' if spec['expected_step'] else 'cp96')
    paired = (ROOT/f'acceptance-{other}.json').exists()
    if paired and a.read(ROOT/f'acceptance-{other}.json')['rng'] != rng:
        raise RuntimeError('Paired initial CPU/CUDA RNG mismatch')
    a.save(ROOT/f'acceptance-{stage}.json',dict(result=result,evidence=evidence,rng=rng,
        paired_rng_checked=paired,seeds=spec['seeds'],checked_at=time.time()))


def accounts(deadline):
    return [dict(roots=[ROOT,SOURCE_PARENT],receipt_root=ROOT,limit=LIMIT,deadline=deadline)]


def resources_ready():
    rows = a.cmd(['nvidia-smi','--query-gpu=index,memory.used,utilization.gpu','--format=csv,noheader,nounits'])
    if len(rows.splitlines()) != 8: raise RuntimeError('Eight GPUs required')
    if any(float(v.strip()) > 0 for row in rows.splitlines() for v in row.split(',')[1:]): return False
    if a.cmd(['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader']): return False
    mem = dict(row.split(':',1) for row in Path('/proc/meminfo').read_text().splitlines())
    return int(mem['MemAvailable'].split()[0])*1024 >= 600*a.GIB and shutil.disk_usage(ROOT).free >= 128*a.GIB


def admit(stage, deadline):
    while True:
        if time.time() >= deadline-45: raise TimeoutError('Fixed admission/deadline reached')
        h.sample(accounts(deadline),ROOT); writers_clear([ROOT,SOURCE_PARENT,CHECKPOINT])
        if resources_ready(): break
        time.sleep(min(30,deadline-45-time.time()))
    probe = ROOT/('fsync-'+stage)
    with probe.open('xb') as s:
        s.write(b'qwen-heldout128\n'); s.flush(); os.fsync(s.fileno())
    if probe.read_bytes() != b'qwen-heldout128\n': raise RuntimeError('fsync readback failed')
    a.save(ROOT/f'admission-{stage}.json',dict(passed=True,checked_at=time.time(),
        deadline=deadline,eight_idle_gpus=True,ram_gib_min=600,nvme_gib_min=128,fsync=True))


def queue():
    check_cpu()
    with (ROOT/'queue.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (ROOT/'queue-state.json').exists() or (ROOT/'dispatch.json').exists():
            raise RuntimeError('Already queued/dispatched; no retry')
        state = dict(phase='checking-predecessor',completed=[],new_games=128,new_updates=0)
        try:
            a.save(ROOT/'queue-state.json',state)
            a.save(ROOT/'predecessor-admission.json',predecessor())
            admit('first',a.read(ROOT/'deployment.json')['first_dispatch_by'])
            start = time.time(); deadline = start+WALL_SECONDS
            a.save(ROOT/'dispatch.json',dict(start=start,deadline=deadline,gpu_hours=48,new_games=128,new_updates=0))
            state.update(phase='running-unverified',deadline=deadline)
            a.save(ROOT/'queue-state.json',state)
            terminal = h.run_stages(STAGES,lambda s:docker('stage',s),verify,accounts(deadline),
                ROOT,ROOT/'host-supervision',ROOT,deadline,admit=lambda s:admit(s,deadline))
            a.save(ROOT/'state.json',terminal)
            state.update(phase='completed',exit_code=0,completed=STAGES,finished_at=time.time())
            a.save(ROOT/'queue-state.json',state)
        except BaseException as exc:
            state.update(phase='failed',error_type=type(exc).__name__,error=str(exc),finished_at=time.time())
            a.save(ROOT/'queue-state.json',state)
            raise


def child_stage(stage):
    cfg = a.read(ROOT/'deployment.json')
    a.clean(a.SOURCE,cfg['runtime_sha']); a.clean(ROOT/'runtime',cfg['runtime_sha'])
    args,env,_ = invocation(cfg,stage)
    fd = os.open(ROOT/(stage+'-entry.log'),os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    os.dup2(fd,1); os.dup2(fd,2); os.close(fd)
    os.chdir(ROOT/'runtime'); os.execvpe(args[0],args,env)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode',choices=['prepare','cpu','regressions','host-regressions',
        'cpu-command','regressions-command','queue','stage'])
    p.add_argument('stage',nargs='?')
    v = p.parse_args()
    configure()
    if v.mode.endswith('-command'): print(json.dumps(docker(v.mode.removesuffix('-command'))))
    elif v.mode == 'host-regressions': regressions(True)
    elif v.mode == 'stage': child_stage(v.stage)
    else: globals()[v.mode]()
