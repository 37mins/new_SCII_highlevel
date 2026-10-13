"""Approved missing four L7 arms, 256 zero-update games after accepted Qwen128."""
import argparse
import copy
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess as sp
import sys
import time
import unittest

import acceptance197 as a
import host_stage197 as h
import qwen_heldout128197 as q
from l7_followup197_r4 import writers_clear
from l7_matrix_plan import ARMS, SEEDS, STAGES, PARENTS, CHECKPOINTS, stage_spec
from qwen_heldout_plan import STAGES as QWEN_STAGES, stage_spec as qwen_spec

ROOT = Path('/var/jfsCache/sc2-l7-matrix256-197-20260924-r1')
SOURCE_PARENT = Path('/var/jfsCache/sc2-l7-matrix256-197-source-20260924-r1')
PREDECESSOR = Path('/var/jfsCache/sc2-qwen-heldout128-197-20260924-r1')
PREDECESSOR_SHA = 'b19b3a2c2d767f20ea71bd16225eee0183cb2fb7'
PREDECESSOR_DEADLINE = 1790281304.865174
FIRST_DISPATCH_BY = PREDECESSOR_DEADLINE + 3600
PREFIX = 'sc2-l7-matrix256-197-20260924-r1'
WALL_SECONDS, LIMIT = 8*3600, 32*a.GIB
PARENT_PROOF = a.HERE/'l7-matrix256-parents-20260924.json'


def small(path):
    path = Path(path)
    if path.stat().st_size > 8*1024**2:
        raise RuntimeError('Receipt too large: '+str(path))
    return a.read(path)


def digest(path):
    path = Path(path)
    if path.stat().st_size > 8*1024**2:
        raise RuntimeError('Receipt too large: '+str(path))
    return hashlib.sha256(path.read_bytes()).hexdigest()


def configure():
    a.ROOT = a.STORAGE_LOCK_ROOT = q.ROOT = ROOT
    a.CONTAINER = PREFIX
    a.DOCKER_SCRIPT = a.HERE/'l7_matrix256197.py'
    if (ROOT/'deployment.json').exists():
        a.RUNTIME_SHA = a.read(ROOT/'deployment.json')['runtime_sha']


def terminal_container(owner, stage, deadline, expected_id=None):
    g = small(owner/f'host-supervision/{stage}-guardian.json')
    cid = g['container_id']
    obj = json.loads(a.cmd(['docker','inspect','--format',
        '{"id":"{{.Id}}","owner":"{{index .Config.Labels "sc2.acceptance.root"}}","state":{{json .State}}}',cid]))
    states = (obj['state'],g['final_state'])
    if (obj['id'] != cid or (expected_id and cid != expected_id)
            or obj['owner'] != str(owner) or g['owner_root'] != str(owner)
            or g['phase'] != 'completed' or g['deadline'] != deadline
            or any(s['Running'] or s['Paused'] or s['ExitCode'] != 0
                   or s.get('OOMKilled') or s.get('Error') for s in states)):
        raise RuntimeError('Exact predecessor guardian/container not completed')
    return cid


def validate_terminal(root, stages, deadline, queue=False):
    names = ['state.json','host-supervision/state.json'] + (['queue-state.json'] if queue else [])
    for name in names:
        state = small(root/name)
        if (state['phase'] != 'completed' or state.get('exit_code') != 0
                or state['completed'] != stages or state['deadline'] != deadline):
            raise RuntimeError('Parent terminal mismatch: '+str(root/name))


def parents():
    evidence = small(PARENT_PROOF)['parents']
    for arm,root in PARENTS.items():
        item = evidence[arm]
        if item['root'] != str(root) or item['checkpoint'] != str(CHECKPOINTS[arm]):
            raise RuntimeError('Wrong parent proof root')
        cfg = small(root/'deployment.json')
        if cfg['runtime_sha'] != item['runtime_sha']:
            raise RuntimeError('Wrong parent runtime')
        a.clean(root/'runtime',item['runtime_sha'])
        for rel,expected in {**item['receipt_sha256'],**item['acceptance_sha256']}.items():
            if digest(root/rel) != expected:
                raise RuntimeError('Accepted parent receipt changed: '+rel)
        deadline = item['state']['deadline']
        validate_terminal(root,['train96','eval96'],deadline)
        for stage in ('train96','eval96'):
            terminal_container(root,stage,deadline,item['containers'][stage]['id'])
            result = small(root/f'runs/{stage}/result.json')
            if (result != small(root/f'runs/{stage}/.done')
                    or small(root/f'acceptance-{stage}.json')['result'] != result
                    or result['status'] != 'completed' or result['process_exit_code'] != 0):
                raise RuntimeError('Parent acceptance/result mismatch')
        result = small(root/'runs/train96/result.json')
        if len(item['checkpoint_files']) != 26:
            raise RuntimeError('Full CP96 inventory required')
        for name,size in item['checkpoint_files'].items():
            if (size <= 0 or (CHECKPOINTS[arm]/name).stat().st_size != size
                    or result['checkpoint_files']['checkpoints/global_step_96/'+name]['bytes'] != size):
                raise RuntimeError('Parent CP96 inventory changed')
    return dict(passed=True,proof_sha256=digest(PARENT_PROOF),checked_at=time.time(),
                roots={k:str(v) for k,v in PARENTS.items()},checkpoint_contents_read=False)


def predecessor():
    queue = small(PREDECESSOR/'queue-state.json')
    host = small(PREDECESSOR/'host-supervision/state.json')
    if any(s['phase'] == 'failed' for s in (queue,host)):
        raise RuntimeError('Qwen128 failed; no successor dispatch')
    if queue['phase'] != 'completed':
        return None
    validate_terminal(PREDECESSOR,QWEN_STAGES,PREDECESSOR_DEADLINE,queue=True)
    cfg = small(PREDECESSOR/'deployment.json')
    if cfg['runtime_sha'] != PREDECESSOR_SHA or cfg['eval_seeds'] != SEEDS:
        raise RuntimeError('Qwen128 protocol/seed identity mismatch')
    a.clean(PREDECESSOR/'runtime',PREDECESSOR_SHA)
    hashes = {}
    for stage in QWEN_STAGES:
        terminal_container(PREDECESSOR,stage,PREDECESSOR_DEADLINE)
        out = PREDECESSOR/'runs'/stage
        result,done,manifest = (small(out/p) for p in ('result.json','.done','manifest.json'))
        acceptance = small(PREDECESSOR/f'acceptance-{stage}.json')
        spec = qwen_spec(stage)
        load = small(out/'checkpoint_evaluation.json')
        if (result != done or acceptance['result'] != result
                or result['status'] != 'completed' or result['process_exit_code'] != 0
                or result['training_updates'] != 0 or not result['metrics_finite']
                or manifest['dirty'] or manifest['source_commit'] != PREDECESSOR_SHA
                or manifest['world_size'] != 8 or result['episode_outcomes']['natural_games'] != 8
                or result['episode_outcomes']['truncated'] != 0
                or acceptance['seeds'] != spec['seeds']
                or load['game_seeds'] != spec['seeds'] or not load['val_only']
                or load['optimizer_updates'] != 0 or load['loaded_global_step'] != spec['expected_step']
                or load['checkpoint_load_returned'] != bool(spec['expected_step'])
                or load['checkpoint'] != (str(q.CHECKPOINT) if spec['expected_step'] else None)
                or result['valid_evaluable_action_count'] != result['evaluable_action_count']
                or result['evaluable_action_count'] <= 0):
            raise RuntimeError('Qwen128 stage not accepted: '+stage)
        for name in ('manifest.json','result.json'):
            if small(out/name)['metrics_precision'] != 'binary64-v1':
                raise RuntimeError('Predecessor precision mismatch')
        for rel in [f'runs/{stage}/result.json',f'runs/{stage}/.done',
                    f'acceptance-{stage}.json',f'host-supervision/{stage}-guardian.json']:
            hashes[rel] = digest(PREDECESSOR/rel)
    for b in range(8):
        one,two = [small(PREDECESSOR/f'acceptance-b{b:02d}-{arm}.json') for arm in ('original','cp96')]
        if one['rng'] != two['rng'] or len(one['rng']) != 8:
            raise RuntimeError('Predecessor pair RNG mismatch')
    return dict(passed=True,runtime_sha=PREDECESSOR_SHA,receipt_sha256=hashes,
                checked_at=time.time(),full_logs_reread=False)


def prepare():
    if ROOT.exists() or a.SOURCE != SOURCE_PARENT/'code':
        raise RuntimeError('New exact roots required; no overwrite/retry')
    sha = a.cmd(['git','-C',a.SOURCE,'rev-parse','HEAD'])
    a.clean(a.SOURCE,sha); a.clean(a.ORCH,a.ORCH_SHA)
    proof = parents()
    configs = {}
    for arm in ARMS:
        parent = PARENTS['spb-random' if arm == 'spb-original' else arm]
        cfg = copy.deepcopy(small(parent/'deployment.json'))
        cfg.update(runtime_sha=sha,controller_sha=sha,controller_source=str(a.SOURCE),
            difficulty='VeryHard',run_prefix=PREFIX,worker_hook='l7_matrix_hook.install',
            seed_protocol='same_uniform101',seed_group_mode='same')
        configs[arm] = cfg
    ROOT.mkdir()
    for name in ('runs','cpu','tmp','tmp/task-home','tmp/cache','tmp/cuda-cache'):
        (ROOT/name).mkdir()
    a.cmd(['git','clone','--quiet','--shared',a.SOURCE,ROOT/'runtime'])
    a.cmd(['git','-C',ROOT/'runtime','checkout','--quiet','--detach',sha])
    a.save(ROOT/'deployment.json',dict(runtime_sha=sha,controller_sha=sha,
        controller_source=str(a.SOURCE),orchestration_sha=a.ORCH_SHA,arms=configs,
        stages=STAGES,games=[8]*32,updates=[0]*32,eval_seeds=SEEDS,
        wall_seconds=WALL_SECONDS,gpu_hours=64,output_limit_bytes=LIMIT,
        storage_roots=[str(ROOT),str(SOURCE_PARENT)],new_games=256,new_updates=0,
        first_dispatch_by=FIRST_DISPATCH_BY,predecessor=str(PREDECESSOR),
        predecessor_sha=PREDECESSOR_SHA,no_retry=True,successors_authorized=False,
        authorization='Sep24 user: automatically queue the proposed four missing arms,256games,0updates,197/8GPUs,8h/64GPUh;32GiB new artifacts;no old deletion/retry',
        seed_plan_sha256=digest(a.HERE/'qwen_heldout_plan.py'),
        matrix_plan_sha256=digest(a.HERE/'l7_matrix_plan.py'),
        parent_proof_sha256=digest(PARENT_PROOF)))
    a.save(ROOT/'parent-acceptance.json',proof)


def invocation(deployment, stage, dry=False):
    spec = stage_spec(stage); cfg = deployment['arms'][spec['arm']]
    args,env,old = q.BASE_INVOCATION(cfg,'pre',dry)
    out = ROOT/('cpu' if dry else 'runs')/stage
    args = [value.replace(str(old),str(out)) for value in args]
    settings = {'trainer.total_training_steps':'96','trainer.total_epochs':'1',
        'trainer.save_freq':'-1','trainer.val_only':'True','trainer.val_before_train':'True',
        'trainer.resume_mode':'resume_path' if spec['expected_step'] else 'disable',
        '+ray_init.runtime_env.env_vars.SC2_MATRIX_STAGE':repr(stage)}
    if spec['checkpoint']:
        settings['trainer.resume_from_path'] = str(spec['checkpoint'])
    if spec['model'] == 'spb':
        settings.update({'algorithm.sc2_policy_credit.seed_group_mode':'same',
            '+ray_init.runtime_env.env_vars.SC2_TRAIN_SEED_PROTOCOL':"'same_uniform101'",
            '+ray_init.runtime_env.env_vars.SC2_RESET_CONCURRENCY':"'1'"})
    args = [v for v in args if v.split('=',1)[0] not in settings]
    args += [k+'='+v for k,v in settings.items()]
    env.update(OUTPUT_DIR=str(out),RUN_ID=PREFIX+'-'+stage,RAY_TMPDIR='/tmp/mx-'+stage)
    return args,env,out


def docker(mode, stage=None):
    cfg = small(ROOT/'deployment.json')
    arm = stage_spec(stage)['arm'] if mode == 'stage' else cfg.get('cpu_config_arm', 'qwen-random')
    model = cfg['arms'][arm]; host = model['host']
    args = ['docker','create' if mode == 'stage' else 'run','--name',PREFIX+'-'+(stage or mode),
        '--label','sc2.acceptance.root='+str(ROOT),'--shm-size','128g','--read-only',
        '--log-driver','none','--entrypoint','/runtime/bin/python']
    binds = [(ROOT,ROOT,False),(ROOT/'tmp','/tmp',False),
        (ROOT/'runtime',ROOT/'runtime',True),(SOURCE_PARENT,SOURCE_PARENT,True),
        (a.ORCH,a.ORCH,True),(host['venv'],'/runtime',True),(host['sc2'],'/assets/StarCraftII',True),
        (Path('/var/jfsCache/sc2-c197-20260919-r1/dependencies'),
         '/var/jfsCache/sc2-c197-20260919-r1/dependencies',True)]
    binds += [(cp,cp,True) for cp in CHECKPOINTS.values()]
    if mode == 'stage':
        binds.append((host['model'],model['model_mount'],True))
        args += ['--gpus','all']
    else:
        binds += [(q.CPU_MODEL,'/assets/qwen',True),(q.SPB_METADATA,'/assets/spb',True)]
        args += ['--cpus','2','--memory','6g','-e','CUDA_VISIBLE_DEVICES=',
            '-e','SC2_TEST_QWEN_METADATA_PATH=/assets/qwen','-e','SC2_TEST_SPB_METADATA_PATH=/assets/spb',
            '-e','SC2_TEST_TOKENIZER_PATH=/assets/qwen','-e','OMP_NUM_THREADS=2','-e','TOKENIZERS_PARALLELISM=false']
    for src,dst,ro in binds:
        args += ['-v',f'{src}:{dst}'+(':ro' if ro else '')]
    args += ['-w',str(ROOT/'runtime'),'-e','PYTHONDONTWRITEBYTECODE=1',
        '-e','HOME=/tmp/task-home','-e','XDG_CACHE_HOME=/tmp/cache','-e','CUDA_CACHE_PATH=/tmp/cuda-cache',
        '-e',f'CONTAINER_IMAGE_ID={host["image"]}',
        '-e',f'PYTHONPATH={ROOT}/runtime:{a.HERE}:/var/jfsCache/sc2-c197-20260919-r1/dependencies:/runtime/lib/python3.12/site-packages',
        host['image'],'-B',str(a.DOCKER_SCRIPT),mode]
    return args+([stage] if mode == 'stage' else [])


def cpu():
    import torch
    from hydra import compose, initialize_config_dir
    from omegaconf import OmegaConf
    from verl.trainer.ppo.sc2_policy_credit import validate_config as credit_config
    from verl.utils.sc2_action_support import validate_config as support_config
    cfg = small(ROOT/'deployment.json')
    check = sp.run(['sha256sum','-c','configs/system-v1.sha256'],cwd=ROOT/'runtime',
        capture_output=True,text=True,timeout=30)
    (ROOT/'cpu/source-check.log').write_text(check.stdout+check.stderr)
    if check.returncode: raise RuntimeError('Source manifest mismatch')
    for stage in STAGES:
        spec = stage_spec(stage); args,env,out = invocation(cfg,stage,True)
        p = sp.run(args,env=env,cwd=ROOT/'runtime',capture_output=True,text=True,timeout=90)
        (ROOT/'cpu'/f'{stage}.log').write_text(p.stdout+p.stderr)
        if p.returncode: raise RuntimeError('Actual launcher failed: '+stage)
        command = small(out/'effective_config.json')['command']
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
                or ev.SC2_MATRIX_STAGE != stage or str(ev.SC2_RESET_CONCURRENCY) != '1'
                or str(ev.SC2_RESET_RETRIES) != '1'
                or c.trainer.resume_mode != ('resume_path' if spec['expected_step'] else 'disable')
                or (spec['checkpoint'] and c.trainer.resume_from_path != str(spec['checkpoint']))):
            raise RuntimeError('Resolved zero-update evaluation contract mismatch')
        a.save(out/'resolved_config.json',OmegaConf.to_container(c,resolve=True))
    if torch.cuda.is_initialized(): raise RuntimeError('CPU initialized CUDA')
    a.save(ROOT/'readiness.json',dict(passed=True,runtime_sha=cfg['runtime_sha'],stages=STAGES,
        actual_entries_and_hydra_configs=True,cuda_initialized=False,checked_at=time.time()))


def regressions(host_only=False):
    if host_only:
        return q.regressions(True)
    import torch
    sys.path[:0] = [str(a.SOURCE/'tests'),str(a.SOURCE/'scripts')]
    names = ['test_l7_matrix256197','test_qwen_heldout128197','test_feedback_eval',
        'test_metric_precision','test_sc2_no_thinking_torch','test_sc2_action_support',
        'test_sc2_reset_startup','test_sc2_generation_tokens','test_policy_credit_acceptance197']
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromNames(names))
    cuda = torch.cuda.is_initialized()
    proof = dict(passed=result.wasSuccessful() and not result.skipped and not cuda,
        tests=result.testsRun,skips=len(result.skipped),cuda_initialized=cuda,
        runtime_sha=small(ROOT/'deployment.json')['runtime_sha'],checked_at=time.time())
    a.save(ROOT/'regressions.json',proof)
    if not proof['passed']: raise RuntimeError('Zero-skip CPU tests required')


def verify(stage):
    spec = stage_spec(stage); out = ROOT/'runs'/stage
    result,evidence = a.verify_common(out,stage,8)
    if any(small(out/p)['metrics_precision'] != 'binary64-v1' for p in ('manifest.json','result.json')):
        raise RuntimeError('Full precision required')
    load = small(out/'checkpoint_evaluation.json')
    ledger = [json.loads(x)['seeds'] for x in (out/'evaluation_seeds.jsonl').read_text().splitlines()]
    if (result['training_updates'] != 0 or not load['val_only'] or load['optimizer_updates'] != 0
            or load['loaded_global_step'] != spec['expected_step'] or load['games'] != 8
            or load['checkpoint'] != (str(spec['checkpoint']) if spec['checkpoint'] else None)
            or load['checkpoint_load_returned'] != bool(spec['expected_step'])
            or load['game_seeds'] != spec['seeds'] or ledger != [spec['seeds']]
            or load['temperature'] != 0.8 or not load['do_sample'] or load['feedback'] != '0'):
        raise RuntimeError('Actual load/seed/zero-update evidence mismatch')
    outcomes = [json.loads(x) for x in (out/'episode_outcomes.jsonl').read_text().splitlines()]
    if (len(outcomes) != 8 or sorted(x['env_index'] for x in outcomes) != list(range(8))
            or any(not x['terminated'] or x['truncated'] for x in outcomes)):
        raise RuntimeError('Eight unique natural outcomes required')
    rng = []
    for rank in range(8):
        r = small(out/f'sampling-rank{rank}.json')
        if (r['rank'],r['seed']) != (rank,rank): raise RuntimeError('Wrong sampling rank')
        rng.append({k:r[k] for k in ('rank','seed','cpu_rng_sha256','cuda_rng_sha256')})
    paired = []
    if spec['model'] == 'qwen':
        paired = [PREDECESSOR/f'acceptance-b{spec["batch"]:02d}-{arm}.json' for arm in ('original','cp96')]
    else:
        paired = [ROOT/f'acceptance-b{spec["batch"]:02d}-{arm}.json' for arm in ARMS[:3]
                  if arm != spec['arm'] and (ROOT/f'acceptance-b{spec["batch"]:02d}-{arm}.json').exists()]
    if any(small(p)['rng'] != rng or small(p)['seeds'] != spec['seeds'] for p in paired):
        raise RuntimeError('Within-model paired RNG/seeds mismatch')
    a.save(ROOT/f'acceptance-{stage}.json',dict(result=result,evidence=evidence,rng=rng,
        paired_with=[str(p) for p in paired],seeds=spec['seeds'],checked_at=time.time()))


def accounts(deadline):
    return [dict(roots=[ROOT,SOURCE_PARENT],receipt_root=ROOT,limit=LIMIT,deadline=deadline)]


def admit(stage, deadline):
    while True:
        if time.time() >= deadline-45: raise TimeoutError('Fixed admission/deadline reached')
        h.sample(accounts(deadline),ROOT)
        writers_clear([ROOT,SOURCE_PARENT,*CHECKPOINTS.values()])
        if q.resources_ready(): break
        time.sleep(min(30,deadline-45-time.time()))
    probe = ROOT/('fsync-'+stage)
    with probe.open('xb') as s:
        s.write(b'l7-matrix256\n'); s.flush(); os.fsync(s.fileno())
    if probe.read_bytes() != b'l7-matrix256\n': raise RuntimeError('fsync readback failed')
    a.save(ROOT/f'admission-{stage}.json',dict(passed=True,checked_at=time.time(),deadline=deadline,
        eight_idle_gpus=True,ram_gib_min=600,nvme_gib_min=128,fsync=True))


def queue():
    q.check_cpu()
    with (ROOT/'queue.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (ROOT/'queue-state.json').exists() or (ROOT/'dispatch.json').exists():
            raise RuntimeError('Already queued/dispatched; no retry')
        state = dict(phase='waiting-predecessor',completed=[],new_games=256,new_updates=0)
        try:
            a.save(ROOT/'queue-state.json',state)
            while True:
                h.sample(accounts(FIRST_DISPATCH_BY),ROOT)
                proof = predecessor()
                if proof: break
                if time.time() >= FIRST_DISPATCH_BY-45:
                    raise TimeoutError('First entry deadline; predecessor not accepted')
                time.sleep(30)
            a.save(ROOT/'predecessor-acceptance.json',proof)
            a.save(ROOT/'parent-admission.json',parents())
            admit('first',FIRST_DISPATCH_BY)
            start = time.time(); deadline = start+WALL_SECONDS
            a.save(ROOT/'dispatch.json',dict(start=start,deadline=deadline,gpu_hours=64,new_games=256,new_updates=0))
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
    cfg = small(ROOT/'deployment.json')
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
    args = parser.parse_args(); configure()
    if args.mode.endswith('-command'): print(json.dumps(docker(args.mode.removesuffix('-command'))))
    elif args.mode == 'host-regressions': regressions(True)
    elif args.mode == 'stage': child_stage(args.stage)
    else: globals()[args.mode]()
