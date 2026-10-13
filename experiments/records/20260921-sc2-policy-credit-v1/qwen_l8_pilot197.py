"""One-shot, paired 96-game Qwen L8 screen on node 197; zero updates."""
import argparse
import copy
import fcntl
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
import l7_matrix256197 as matrix
import qwen_heldout128197 as q
from l7_followup197_r4 import writers_clear
from qwen_l8_plan import ARMS, CHECKPOINTS, PARENTS, SEEDS, STAGES, stage_spec

ROOT = Path('/var/jfsCache/sc2-qwen-l8-pilot96-197-20260925-r1')
SOURCE_PARENT = Path('/var/jfsCache/sc2-qwen-l8-pilot96-197-source-20260925-r1')
PREFIX = 'sc2-qwen-l8-pilot96-197-20260925-r1'
PARENT_PROOF = a.HERE/'l7-matrix256-parents-20260924.json'
WALL_SECONDS, LIMIT = 4*3600, 32*a.GIB
BASE_INVOCATION = q.BASE_INVOCATION
PRIOR_ACCEPTANCE_ROOT = None


def configure():
    a.ROOT = a.STORAGE_LOCK_ROOT = ROOT
    a.CONTAINER = PREFIX
    a.DOCKER_SCRIPT = a.HERE/'qwen_l8_pilot197.py'
    if (ROOT/'deployment.json').exists():
        a.RUNTIME_SHA = matrix.small(ROOT/'deployment.json')['runtime_sha']


def parents():
    """Only the two Qwen CP96s, with accepted terminal and size-only CP inventory."""
    same = q.predecessor()
    item = matrix.small(PARENT_PROOF)['parents']['qwen-random']
    root = PARENTS['random-cp96']
    if item['root'] != str(root) or item['checkpoint'] != str(CHECKPOINTS['random-cp96']):
        raise RuntimeError('Random parent identity mismatch')
    cfg = matrix.small(root/'deployment.json')
    if cfg['runtime_sha'] != item['runtime_sha']:
        raise RuntimeError('Random parent runtime mismatch')
    a.clean(root/'runtime', item['runtime_sha'])
    for rel, expected in {**item['receipt_sha256'], **item['acceptance_sha256']}.items():
        if matrix.digest(root/rel) != expected:
            raise RuntimeError('Random accepted receipt changed: '+rel)
    deadline = item['state']['deadline']
    matrix.validate_terminal(root, ['train96','eval96'], deadline)
    for stage in ('train96','eval96'):
        matrix.terminal_container(root,stage,deadline,item['containers'][stage]['id'])
        result = matrix.small(root/f'runs/{stage}/result.json')
        if (result != matrix.small(root/f'runs/{stage}/.done')
                or result != matrix.small(root/f'acceptance-{stage}.json')['result']
                or result['status'] != 'completed' or result['process_exit_code'] != 0):
            raise RuntimeError('Random parent result/acceptance mismatch')
    train = matrix.small(root/'runs/train96/result.json')
    if len(item['checkpoint_files']) != 26:
        raise RuntimeError('Full random CP96 inventory required')
    for name, size in item['checkpoint_files'].items():
        if (size <= 0 or (CHECKPOINTS['random-cp96']/name).stat().st_size != size
                or train['checkpoint_files']['checkpoints/global_step_96/'+name]['bytes'] != size):
            raise RuntimeError('Random CP96 inventory changed')
    return dict(passed=True,same=same,random_proof_sha256=matrix.digest(PARENT_PROOF),
                checked_at=time.time(),checkpoint_contents_read=False)


def prepare():
    if ROOT.exists() or a.SOURCE != SOURCE_PARENT/'code':
        raise RuntimeError('New exact roots required; no overwrite or retry')
    sha = a.cmd(['git','-C',a.SOURCE,'rev-parse','HEAD'])
    a.clean(a.SOURCE,sha); a.clean(a.ORCH,a.ORCH_SHA)
    proof = parents()
    source = matrix.small(PARENTS['same-cp96']/'qwen-same/short/deployment.json')
    configs = {}
    for arm in ARMS:
        cfg = copy.deepcopy(source)
        cfg.update(runtime_sha=sha,controller_sha=sha,controller_source=str(a.SOURCE),
            difficulty='CheatVision',run_prefix=PREFIX,worker_hook='qwen_l8_hook.install',
            seed_protocol='same_uniform101',seed_group_mode='same')
        configs[arm] = cfg
    ROOT.mkdir()
    for name in ('runs','cpu','tmp','tmp/task-home','tmp/cache','tmp/cuda-cache'):
        (ROOT/name).mkdir()
    a.cmd(['git','clone','--quiet','--shared',a.SOURCE,ROOT/'runtime'])
    a.cmd(['git','-C',ROOT/'runtime','checkout','--quiet','--detach',sha])
    a.save(ROOT/'deployment.json',dict(runtime_sha=sha,controller_sha=sha,
        controller_source=str(a.SOURCE),orchestration_sha=a.ORCH_SHA,arms=configs,
        stages=STAGES,games=[8]*12,updates=[0]*12,eval_seeds=SEEDS,
        wall_seconds=WALL_SECONDS,gpu_hours=32,output_limit_bytes=LIMIT,
        storage_roots=[str(ROOT),str(SOURCE_PARENT)],new_games=96,new_updates=0,
        first_dispatch_by=time.time()+2*3600,no_retry=True,no_training=True,
        successors_authorized=False,level='L8',difficulty='CheatVision',
        only_environment_change='SC2 bot VeryHard to CheatVision',
        authorization='Sep25 user: Qwen L8 original/sameCP96/randomCP96,32 new paired seeds,96 natural games,0 updates,197/8 GPUs serial,4h/32 GPUh/32GiB; no retry/successor/deletion',
        seed_plan_sha256=matrix.digest(a.HERE/'qwen_l8_plan.py'),
        parent_proof_sha256=matrix.digest(PARENT_PROOF)))
    a.save(ROOT/'parent-acceptance.json',proof)


def invocation(deployment, stage, dry=False):
    spec = stage_spec(stage)
    cfg = deployment['arms'][spec['arm']]
    args,env,old = BASE_INVOCATION(cfg,'pre',dry)
    out = ROOT/('cpu' if dry else 'runs')/stage
    args = [value.replace(str(old),str(out)) for value in args]
    settings = {'trainer.total_training_steps':'96','trainer.total_epochs':'1',
        'trainer.save_freq':'-1','trainer.val_only':'True','trainer.val_before_train':'True',
        'trainer.resume_mode':'resume_path' if spec['expected_step'] else 'disable',
        '+ray_init.runtime_env.env_vars.SC2_L8_STAGE':repr(stage)}
    if spec['checkpoint']:
        settings['trainer.resume_from_path'] = str(spec['checkpoint'])
    args = [v for v in args if v.split('=',1)[0] not in settings]
    args += [k+'='+v for k,v in settings.items()]
    env.update(OUTPUT_DIR=str(out),RUN_ID=PREFIX+'-'+stage,RAY_TMPDIR='/tmp/l8-'+stage)
    if env['SC2_DIFFICULTY'] != 'CheatVision':
        raise RuntimeError('L8 difficulty not applied')
    return args,env,out


def docker(mode, stage=None):
    cfg = matrix.small(ROOT/'deployment.json')
    arm = stage_spec(stage)['arm'] if mode == 'stage' else 'original'
    model = cfg['arms'][arm]; host = model['host']
    args = ['docker','create' if mode == 'stage' else 'run','--name',PREFIX+'-'+(stage or mode),
        '--label','sc2.acceptance.root='+str(ROOT),'--shm-size','128g',
        '--read-only','--log-driver','none','--entrypoint','/runtime/bin/python']
    binds = [(ROOT,ROOT,False),(ROOT/'tmp','/tmp',False),
        (ROOT/'runtime',ROOT/'runtime',True),(SOURCE_PARENT,SOURCE_PARENT,True),
        (a.ORCH,a.ORCH,True),(host['venv'],'/runtime',True),
        (host['sc2'],'/assets/StarCraftII',True),
        (Path('/var/jfsCache/sc2-c197-20260919-r1/dependencies'),
         '/var/jfsCache/sc2-c197-20260919-r1/dependencies',True)]
    binds += [(cp,cp,True) for cp in CHECKPOINTS.values()]
    if mode == 'stage':
        binds.append((host['model'],model['model_mount'],True))
        args += ['--gpus','all']
    else:
        binds += [(q.CPU_MODEL,'/assets/qwen',True),(q.SPB_METADATA,'/assets/spb',True)]
        args += ['--cpus','2','--memory','6g','-e','CUDA_VISIBLE_DEVICES=',
            '-e','SC2_TEST_QWEN_METADATA_PATH=/assets/qwen',
            '-e','SC2_TEST_SPB_METADATA_PATH=/assets/spb',
            '-e','SC2_TEST_TOKENIZER_PATH=/assets/qwen',
            '-e','OMP_NUM_THREADS=2','-e','TOKENIZERS_PARALLELISM=false']
    for source,target,ro in binds:
        args += ['-v',f'{source}:{target}'+(':ro' if ro else '')]
    args += ['-w',str(ROOT/'runtime'),'-e','PYTHONDONTWRITEBYTECODE=1',
        '-e','HOME=/tmp/task-home','-e','XDG_CACHE_HOME=/tmp/cache',
        '-e','CUDA_CACHE_PATH=/tmp/cuda-cache',
        '-e',f'CONTAINER_IMAGE_ID={host["image"]}',
        '-e',f'PYTHONPATH={ROOT}/runtime:{a.HERE}:/var/jfsCache/sc2-c197-20260919-r1/dependencies:/runtime/lib/python3.12/site-packages',
        host['image'],'-B',str(a.DOCKER_SCRIPT),mode]
    writable = [tuple(args[i+1].split(':')[:2]) for i,v in enumerate(args[:-1])
                if v == '-v' and args[i+1].split(':')[-1] != 'ro']
    if set(writable) != {(str(ROOT),str(ROOT)),(str(ROOT/'tmp'),'/tmp')} or len(writable) != 2:
        raise RuntimeError('Unexpected writable bind')
    if mode == 'stage':
        args.append(stage)
    return args


def cpu():
    import torch
    from hydra import compose, initialize_config_dir
    from omegaconf import OmegaConf
    from verl.trainer.ppo.sc2_policy_credit import validate_config as credit_config
    from verl.utils.sc2_action_support import validate_config as support_config
    cfg = matrix.small(ROOT/'deployment.json')
    check = sp.run(['sha256sum','-c','configs/system-v1.sha256'],cwd=ROOT/'runtime',
        capture_output=True,text=True,timeout=30)
    (ROOT/'cpu/source-check.log').write_text(check.stdout+check.stderr)
    if check.returncode: raise RuntimeError('Source manifest mismatch')
    for stage in STAGES:
        spec = stage_spec(stage)
        args,env,out = invocation(cfg,stage,True)
        p = sp.run(args,env=env,cwd=ROOT/'runtime',capture_output=True,text=True,timeout=90)
        (ROOT/'cpu'/f'{stage}.log').write_text(p.stdout+p.stderr)
        if p.returncode: raise RuntimeError('Actual launcher failed: '+stage)
        command = matrix.small(out/'effective_config.json')['command']
        with initialize_config_dir(config_dir=str(ROOT/'runtime/verl/trainer/config'),version_base=None):
            c = compose(config_name='ppo_trainer',overrides=command[command.index('verl.trainer.main_ppo')+1:])
        credit_config(c); support_config(c)
        ev = c.ray_init.runtime_env.env_vars
        if (not c.trainer.val_only or not c.trainer.val_before_train or c.trainer.save_freq != -1
                or c.trainer.n_gpus_per_node != 8 or c.env.val_rollout_n != 8
                or c.trainer.sc2_checkpoint_resume or c.trainer.del_local_ckpt_after_load
                or c.actor_rollout_ref.rollout.response_length != 192
                or c.actor_rollout_ref.rollout.val_kwargs.temperature != 0.8
                or c.actor_rollout_ref.rollout.val_kwargs.top_p != 1.0
                or not c.actor_rollout_ref.rollout.val_kwargs.do_sample or not c.data.sc2_no_thinking
                or ev.SC2_L8_STAGE != stage or str(ev.SC2_DIFFICULTY) != 'CheatVision'
                or str(ev.SC2_EXPECTED_DIFFICULTY) != 'CheatVision'
                or str(ev.SC2_RESET_CONCURRENCY) != '1' or str(ev.SC2_RESET_RETRIES) != '1'
                or c.trainer.resume_mode != ('resume_path' if spec['expected_step'] else 'disable')
                or (spec['checkpoint'] and c.trainer.resume_from_path != str(spec['checkpoint']))):
            raise RuntimeError('Resolved L8 zero-update protocol mismatch')
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
        names = ['test_qwen_l8_pilot197','test_qwen_heldout128197','test_feedback_eval',
            'test_metric_precision','test_sc2_no_thinking_torch','test_sc2_action_support',
            'test_sc2_reset_startup','test_sc2_generation_tokens','test_policy_credit_acceptance197']
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromNames(names))
    cuda = False if host_only else torch.cuda.is_initialized()
    proof = dict(passed=result.wasSuccessful() and not result.skipped and not cuda,
        tests=result.testsRun,skips=len(result.skipped),cuda_initialized=cuda,
        host_only=host_only,runtime_sha=matrix.small(ROOT/'deployment.json')['runtime_sha'],
        checked_at=time.time())
    a.save(ROOT/('host-regressions.json' if host_only else 'regressions.json'),proof)
    if not proof['passed']: raise RuntimeError('Zero-skip CPU tests required')


def check_cpu():
    cfg = matrix.small(ROOT/'deployment.json')
    for path in (a.SOURCE,ROOT/'runtime'):
        a.clean(path,cfg['runtime_sha'])
    a.clean(a.ORCH,a.ORCH_SHA)
    for name in ('readiness.json','regressions.json','host-regressions.json'):
        p = matrix.small(ROOT/name)
        if not p['passed'] or p.get('skips',0) or p['cuda_initialized'] or p['runtime_sha'] != cfg['runtime_sha']:
            raise RuntimeError('Matching real CPU proof required')


def verify(stage):
    spec = stage_spec(stage); out = ROOT/'runs'/stage
    result,evidence = a.verify_common(out,stage,8)
    if any(matrix.small(out/p).get('metrics_precision') != 'binary64-v1'
           for p in ('manifest.json','result.json')):
        raise RuntimeError('Full-precision metrics required')
    load = matrix.small(out/'checkpoint_evaluation.json')
    ledger = [json.loads(x)['seeds'] for x in (out/'evaluation_seeds.jsonl').read_text().splitlines()]
    if (result['training_updates'] != 0 or not load['val_only'] or load['optimizer_updates'] != 0
            or load['loaded_global_step'] != spec['expected_step'] or load['games'] != 8
            or load['checkpoint'] != (str(spec['checkpoint']) if spec['checkpoint'] else None)
            or load['checkpoint_load_returned'] != bool(spec['expected_step'])
            or load['game_seeds'] != spec['seeds'] or ledger != [spec['seeds']]
            or load['temperature'] != 0.8 or not load['do_sample'] or load['feedback'] != '0'):
        raise RuntimeError('Actual Qwen load/seeds/zero-update evidence mismatch')
    outcomes = [json.loads(x) for x in (out/'episode_outcomes.jsonl').read_text().splitlines()]
    if (len(outcomes) != 8 or sorted(x['env_index'] for x in outcomes) != list(range(8))
            or any(not x['terminated'] or x['truncated'] for x in outcomes)):
        raise RuntimeError('Eight unique natural L8 outcomes required')
    if (len(result['replays']) != 8 or
            any('/Flat128_CheatVision_Air/' not in path for path in result['replays'])):
        raise RuntimeError('Actual eight SC2 L8 replay paths required')
    rng = []
    for rank in range(8):
        r = matrix.small(out/f'sampling-rank{rank}.json')
        if (r['rank'],r['seed']) != (rank,rank): raise RuntimeError('Sampling rank mismatch')
        rng.append({k:r[k] for k in ('rank','seed','cpu_rng_sha256','cuda_rng_sha256')})
    prior = []
    for arm in ARMS:
        if arm == spec['arm']: continue
        path = ROOT/f'acceptance-b{spec["batch"]:02d}-{arm}.json'
        if not path.exists() and PRIOR_ACCEPTANCE_ROOT is not None:
            path = PRIOR_ACCEPTANCE_ROOT/f'acceptance-b{spec["batch"]:02d}-{arm}.json'
        if path.exists():
            item = matrix.small(path)
            if item['rng'] != rng or item['seeds'] != spec['seeds']:
                raise RuntimeError('Within-Qwen paired rank/CPU/CUDA RNG mismatch')
            prior.append(str(path))
    a.save(ROOT/f'acceptance-{stage}.json',dict(result=result,evidence=evidence,
        rng=rng,seeds=spec['seeds'],paired_with=prior,difficulty='CheatVision',
        checked_at=time.time()))


def accounts(deadline):
    return [dict(roots=[ROOT,SOURCE_PARENT],receipt_root=ROOT,limit=LIMIT,deadline=deadline)]


def resources_ready():
    rows = a.cmd(['nvidia-smi','--query-gpu=index,memory.used,utilization.gpu',
        '--format=csv,noheader,nounits'])
    if len(rows.splitlines()) != 8: raise RuntimeError('Eight GPUs required')
    if any(float(v.strip()) > 0 for row in rows.splitlines() for v in row.split(',')[1:]):
        return False
    if a.cmd(['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader']):
        return False
    mem = dict(row.split(':',1) for row in Path('/proc/meminfo').read_text().splitlines())
    return (int(mem['MemAvailable'].split()[0])*1024 >= 600*a.GIB
            and shutil.disk_usage(ROOT).free >= 128*a.GIB)


def admit(stage,deadline):
    while True:
        if time.time() >= deadline-45: raise TimeoutError('Fixed admission/deadline reached')
        h.sample(accounts(deadline),ROOT)
        writers_clear([ROOT,SOURCE_PARENT,*CHECKPOINTS.values()])
        if resources_ready(): break
        time.sleep(min(30,deadline-45-time.time()))
    probe = ROOT/('fsync-'+stage)
    with probe.open('xb') as f:
        f.write(b'qwen-l8-pilot\n'); f.flush(); os.fsync(f.fileno())
    if probe.read_bytes() != b'qwen-l8-pilot\n': raise RuntimeError('fsync/readback failed')
    a.save(ROOT/f'admission-{stage}.json',dict(passed=True,checked_at=time.time(),
        deadline=deadline,eight_idle_gpus=True,ram_gib_min=600,nvme_gib_min=128,fsync=True))


def queue():
    check_cpu()
    with (ROOT/'queue.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (ROOT/'queue-state.json').exists() or (ROOT/'dispatch.json').exists():
            raise RuntimeError('Already queued/dispatched; no retry')
        state = dict(phase='checking-parents',completed=[],new_games=96,new_updates=0)
        try:
            a.save(ROOT/'queue-state.json',state)
            a.save(ROOT/'parent-admission.json',parents())
            admit('first',matrix.small(ROOT/'deployment.json')['first_dispatch_by'])
            start = time.time(); deadline = start+WALL_SECONDS
            a.save(ROOT/'dispatch.json',dict(start=start,deadline=deadline,
                gpu_hours=32,new_games=96,new_updates=0))
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
    cfg = matrix.small(ROOT/'deployment.json')
    a.clean(a.SOURCE,cfg['runtime_sha']); a.clean(ROOT/'runtime',cfg['runtime_sha'])
    args,env,_ = invocation(cfg,stage)
    fd = os.open(ROOT/(stage+'-entry.log'),os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    os.dup2(fd,1); os.dup2(fd,2); os.close(fd)
    os.chdir(ROOT/'runtime'); os.execvpe(args[0],args,env)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',choices=['prepare','cpu','regressions','host-regressions',
        'cpu-command','regressions-command','queue','stage'])
    parser.add_argument('stage',nargs='?')
    cli = parser.parse_args(); configure()
    if cli.mode.endswith('-command'): print(json.dumps(docker(cli.mode.removesuffix('-command'))))
    elif cli.mode == 'host-regressions': regressions(True)
    elif cli.mode == 'stage': child_stage(cli.stage)
    else: globals()[cli.mode]()
