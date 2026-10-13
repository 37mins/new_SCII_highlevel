"""Approved192 natural evaluation games, 0 updates, 197/8GPU/6h/48GPUh/32GiB."""
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
import l7_matrix256197 as receipts
import qwen_l7_long197 as previous
import qwen_l8_cp192_197 as parent
import qwen_l8_cuda_probe_v2 as probe
from l7_followup197_r4 import writers_clear
from agent_system.sc2_policy_resume import checkpoint_names, verify_contract
from qwen_l8_common64_plan import ARMS, CHECKPOINTS, PARENT, SEEDS, SEED_SHA256, STAGES, stage_spec, validate
from qwen_l8_common64_hook import runtime_environment

ROOT = Path('/var/jfsCache/sc2-qwen-l8-common192-197-20260927-r1')
SOURCE_PARENT = Path('/var/jfsCache/sc2-qwen-l8-common192-197-source-20260927-r1')
PREFIX = ROOT.name
WALL_SECONDS, LIMIT = 6*3600, 32*a.GIB
PARENT_SHA = 'f0e1059aabd28cc5be259908e0955c2509d74a87'
PARENT_PROOF = a.HERE/'qwen-l8-cp192-complete-20260927.json'
# Three actual no-GPU worker imports cover each load mode; all24 configs checked.
HOOK_STAGES = STAGES[:3]
MODEL_KIND = 'qwen'
DIFFICULTY = 'CheatVision'


def configure():
    a.ROOT = a.STORAGE_LOCK_ROOT = ROOT
    a.CONTAINER = PREFIX; a.DOCKER_SCRIPT = a.HERE/'qwen_l8_common64_197.py'
    a.RUNTIME_SHA = (a.read(ROOT/'deployment.json')['runtime_sha'] if (ROOT/'deployment.json').exists()
                     else a.cmd(['git','-C',a.SOURCE,'rev-parse','HEAD']))


def parents():
    """Accepted hash-bound small receipts plus CP filename/stat only; no large reads."""
    proof = receipts.small(PARENT_PROOF)
    if proof['run_root'] != str(PARENT) or proof['source_sha'] != PARENT_SHA or not proof['checks_passed']:
        raise RuntimeError('Exact accepted CP192 proof required')
    cfg = receipts.small(PARENT/'deployment.json')
    if cfg['runtime_sha'] != PARENT_SHA or cfg['controller_sha'] != PARENT_SHA:
        raise RuntimeError('Wrong parent runtime')
    a.clean(PARENT/'runtime',PARENT_SHA); a.clean(Path(cfg['controller_source']),PARENT_SHA)
    receipts.validate_terminal(PARENT,['pre96','train192','eval192'],proof['dispatch']['deadline'],queue=True)
    for stage,item in proof['stages'].items():
        if (receipts.digest(PARENT/f'runs/{stage}/result.json') != item['result_sha256']
                or receipts.digest(PARENT/f'acceptance-{stage}.json') != item['acceptance_sha256']):
            raise RuntimeError('Accepted parent receipt changed')
        result = receipts.small(PARENT/f'runs/{stage}/result.json')
        if result != receipts.small(PARENT/f'runs/{stage}/.done') or result != receipts.small(PARENT/f'acceptance-{stage}.json')['result']:
            raise RuntimeError('Parent result/done/acceptance mismatch')
        receipts.terminal_container(PARENT,stage,proof['dispatch']['deadline'],item['container']['id'])
    parent.parent_terminal()
    contract = receipts.small(PARENT/'resume-contract.json'); verify_contract(contract)
    if contract['checkpoint'] != str(CHECKPOINTS['cp96']): raise RuntimeError('Wrong CP96 ancestor')
    train = receipts.small(PARENT/'runs/train192/result.json')
    inventory = {}
    for arm,cp in CHECKPOINTS.items():
        inventory[arm] = {name:(cp/name).stat().st_size for name in checkpoint_names()}
        for name,size in inventory[arm].items():
            expected = (contract['checkpoint_bytes'][name] if arm=='cp96' else
                        train['checkpoint_files']['checkpoints/global_step_192/'+name]['bytes'])
            if size <= 0 or size != expected: raise RuntimeError('Full parent checkpoint inventory changed')
    return dict(passed=True,proof_sha256=receipts.digest(PARENT_PROOF),checkpoint_bytes=inventory,
        accepted_receipts_unchanged=True,checkpoint_contents_read=False,checked_at=time.time())


def prepare():
    if ROOT.exists() or a.SOURCE != SOURCE_PARENT/'code': raise RuntimeError('Fresh exact roots required; no retry')
    validate(); sha = a.cmd(['git','-C',a.SOURCE,'rev-parse','HEAD'])
    a.clean(a.SOURCE,sha); a.clean(a.ORCH,a.ORCH_SHA); proof = parents()
    ROOT.mkdir()
    for name in ('runs','cpu','tmp','tmp/task-home','tmp/cache','tmp/cuda-cache'): (ROOT/name).mkdir()
    sp.run(['git','clone','--quiet','--no-local',str(a.SOURCE),str(ROOT/'runtime')],check=True,timeout=120)
    a.cmd(['git','-C',ROOT/'runtime','checkout','--quiet','--detach',sha])
    cfg = copy.deepcopy(receipts.small(PARENT/'deployment.json'))
    for key in ('parent_terminal','predecessor','training_seeds','start_step','target_step','saved_steps',
                'train_admission_free_gib','original_start','fixed_deadline','deadline','retained_prefix','prior_failed_root'):
        cfg.pop(key,None)
    cfg.update(runtime_sha=sha,controller_sha=sha,controller_source=str(a.SOURCE),orchestration_sha=a.ORCH_SHA,
        stages=STAGES,games=[8]*24,updates=[0]*24,run_prefix=PREFIX,worker_hook='qwen_l8_common64_hook.install',
        eval_seeds=SEEDS,seed_sha256=SEED_SHA256,checkpoints={k:str(v) for k,v in CHECKPOINTS.items()},
        wall_seconds=WALL_SECONDS,gpu_hours=48,output_limit_bytes=LIMIT,storage_roots=[str(ROOT),str(SOURCE_PARENT)],
        first_dispatch_by=time.time()+4*3600,new_games=192,new_updates=0,no_retry=True,no_training=True,
        successors_authorized=False,evaluation_admission_free_gib=128,
        authorization='Sep27 user approves proposed original/own L8CP96/own L8CP192 common64,192natural games,0updates,197 eightGPU serial,6wallh/48GPUh/32GiB new roots; no deletion/retry/successor',
        limitation='Fixed64 pairs; primary CP192-minus-CP96, no architecture claim; secondary original contrasts exploratory')
    cfg['queue_expires'] = cfg['first_dispatch_by']
    a.save(ROOT/'deployment.json',cfg); a.save(ROOT/'parent-acceptance.json',proof)


def invocation(cfg,stage,dry=False):
    spec = stage_spec(stage)
    if cfg['difficulty'] != DIFFICULTY or cfg['model_kind'] != MODEL_KIND: raise ValueError('Wrong evaluation difficulty/model')
    args,env,base = a.invocation(cfg,'pre',dry)
    out = ROOT/('cpu' if dry else 'runs')/stage
    args = [x.replace(str(base),str(out)) for x in args]
    settings = {'+ray_init.runtime_env.env_vars.SC2_ACCEPTANCE_STAGE':repr(stage),
        'trainer.total_training_steps':'192','trainer.total_epochs':'1','trainer.save_freq':'-1',
        'trainer.val_only':'True','trainer.val_before_train':'True',
        'trainer.resume_mode':'resume_path' if spec['checkpoint'] else 'disable'}
    if spec['checkpoint']: settings['trainer.resume_from_path'] = str(spec['checkpoint'])
    args = [x for x in args if x.split('=',1)[0] not in settings]
    args += [k+'='+v for k,v in settings.items()]
    args += ["+ray_init.runtime_env.env_vars.SC2_L8_RENDEZVOUS_LOW_PORT='1'"]
    if MODEL_KIND=='spb':
        args += ["+ray_init.runtime_env.env_vars.SC2_RESET_CONCURRENCY='1'",
                 f"algorithm.sc2_policy_credit.seed_group_mode={cfg['seed_group_mode']}",
                 f"+ray_init.runtime_env.env_vars.SC2_TRAIN_SEED_PROTOCOL='{cfg['seed_protocol']}'"]
    env.update(OUTPUT_DIR=str(out),RUN_ID=PREFIX+'-'+stage,SC2_CHECKPOINT_RESUME='False',RAY_TMPDIR='/tmp/c64-'+stage)
    return args,env,out


def docker(mode,stage=None):
    gpu = mode in ('stage','gpu-preflight')
    if mode in ('stage','gpu-preflight','cpu-hook'): stage_spec(stage)
    args = a.docker('execute' if gpu else 'cpu')
    args[2:2] = ['--read-only','--log-driver','none','-e','HOME=/tmp/task-home',
        '-e','XDG_CACHE_HOME=/tmp/cache','-e','CUDA_CACHE_PATH=/tmp/cuda-cache','-e','TMPDIR=/tmp']
    for cp in CHECKPOINTS.values(): args[2:2] = ['-v',f'{cp}:{cp}:ro']
    if not gpu:
        cfg = a.read(ROOT/'deployment.json')
        args[args.index(f'{cfg["host"]["model"]}:/assets/qwen:ro')] = f'{previous.CPU_MODEL}:/assets/qwen:ro'
        args[2:2] = ['-v',f'{previous.SPB_METADATA}:/metadata/spb:ro','-e','SC2_TEST_SPB_METADATA_PATH=/metadata/spb',
            '-e','SC2_TEST_QWEN_METADATA_PATH=/assets/qwen','-e','SC2_TEST_TOKENIZER_PATH=/assets/qwen',
            '-e','OMP_NUM_THREADS=2','-e','TOKENIZERS_PARALLELISM=false']
        if mode=='cpu-hook': args[args.index('--memory')+1]='16g'
    writable = [tuple(args[i+1].split(':')[:2]) for i,x in enumerate(args[:-1]) if x=='-v' and args[i+1].split(':')[-1]!='ro']
    if writable != [(str(ROOT),str(ROOT)),(str(ROOT/'tmp'),'/tmp')]: raise RuntimeError('Unexpected writable mounts')
    if mode in ('cpu-hook','gpu-preflight'):
        ev = a.read(ROOT/f'cpu/{stage}/resolved_config.json')['ray_init']['runtime_env']['env_vars']
        for i,x in enumerate(args):
            if x.startswith('PYTHONPATH='): args[i]='PYTHONPATH='+ev['PYTHONPATH']
    args[args.index('--name')+1]=PREFIX+'-'+(stage if mode=='stage' else mode+('-'+stage if stage else ''))
    args[-1:]=[mode]+([stage] if stage else [])
    if gpu: args[1]='create'
    return args


def cpu():
    import torch
    from hydra import compose, initialize_config_dir
    from omegaconf import OmegaConf
    from verl.trainer.ppo.sc2_policy_credit import validate_config as credit_config
    from verl.utils.sc2_action_support import validate_config as support_config
    from ray._private.utils import validate_socket_filepath
    sys.path.insert(0,str(a.ORCH/a.REC)); from seed_ray_paths import socket_path
    cfg = a.read(ROOT/'deployment.json')
    check=sp.run(['sha256sum','-c','configs/system-v1.sha256'],cwd=ROOT/'runtime',capture_output=True,text=True,timeout=30)
    (ROOT/'cpu/source-check.log').write_text(check.stdout+check.stderr)
    if check.returncode: raise RuntimeError('Source manifest mismatch')
    for stage in STAGES:
        args,env,out=invocation(cfg,stage,True)
        p=sp.run(args,env=env,cwd=ROOT/'runtime',capture_output=True,text=True,timeout=90)
        (ROOT/'cpu'/f'{stage}.log').write_text(p.stdout+p.stderr)
        if p.returncode: raise RuntimeError('Actual launcher failed: '+stage)
        command=a.read(out/'effective_config.json')['command']
        with initialize_config_dir(config_dir=str(ROOT/'runtime/verl/trainer/config'),version_base=None):
            c=compose(config_name='ppo_trainer',overrides=command[command.index('verl.trainer.main_ppo')+1:])
        credit_config(c); support_config(c)
        r=c.actor_rollout_ref.rollout; ev=c.ray_init.runtime_env.env_vars
        if (c.env.val_rollout_n!=8 or c.trainer.del_local_ckpt_after_load or r.response_length!=192
                or r.val_kwargs.temperature!=0.8 or r.val_kwargs.top_p!=1.0 or r.val_kwargs.top_k!=0
                or not r.val_kwargs.do_sample or not c.data.sc2_no_thinking
                or str(ev.SC2_RESET_CONCURRENCY)!='1' or str(ev.SC2_RESET_RETRIES)!='1'):
            raise RuntimeError('Changed evaluation protocol')
        a.save(out/'resolved_config.json',OmegaConf.to_container(c,resolve=True))
        runtime_environment(out/'resolved_config.json','/tmp/probe-ray')
        validate_socket_filepath(socket_path(env['RAY_TMPDIR']))
    if torch.cuda.is_initialized(): raise RuntimeError('CPU initialized CUDA')
    a.save(ROOT/'readiness.json',dict(passed=True,runtime_sha=cfg['runtime_sha'],stages=STAGES,
        actual_entries_and_hydra_configs=True,cuda_initialized=False,checked_at=time.time()))


def regressions(host_only=False):
    sys.path[:0]=[str(a.SOURCE/'tests'),str(a.SOURCE/'scripts')]
    if host_only:
        if Path('/.dockerenv').exists(): raise RuntimeError('Actual host tests required')
        names=['test_l7_host_continuation197','test_host_stage197','test_storage_quiescent197',
            'test_policy_credit_storage197','test_policy_credit_storage_coordination197']
    else:
        import torch
        names=['test_qwen_l8_common64_197','test_qwen_l8_cp192_197','test_qwen_l8_probe_env',
            'test_qwen_l8_remainder3_197','test_qwen_l8_pilot197','test_qwen_heldout128197','test_feedback_eval',
            'test_metric_precision','test_sc2_no_thinking_torch','test_sc2_action_support',
            'test_sc2_reset_startup','test_sc2_generation_tokens','test_policy_credit_acceptance197']
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromNames(names))
    cuda=False if host_only else torch.cuda.is_initialized()
    proof=dict(passed=result.wasSuccessful() and not result.skipped and not cuda,tests=result.testsRun,
        skips=len(result.skipped),cuda_initialized=cuda,host_only=host_only,
        runtime_sha=a.read(ROOT/'deployment.json')['runtime_sha'],checked_at=time.time())
    a.save(ROOT/('host-regressions.json' if host_only else 'regressions.json'),proof,lock_root=ROOT)
    if not proof['passed']: raise RuntimeError('Zero-skip CPU tests required')


def check_cpu():
    cfg=a.read(ROOT/'deployment.json')
    a.clean(a.SOURCE,cfg['runtime_sha']);a.clean(ROOT/'runtime',cfg['runtime_sha']);a.clean(a.ORCH,a.ORCH_SHA)
    for name in ('readiness.json','regressions.json','host-regressions.json'):
        p=a.read(ROOT/name)
        if not p['passed'] or p.get('skips',0) or p['cuda_initialized'] or p['runtime_sha']!=cfg['runtime_sha']:
            raise RuntimeError('Matching zero-skip CPU gates required')
    for stage in HOOK_STAGES:
        p=a.read(ROOT/f'cpu/hook-{stage}/cpu-hook-preflight.json')
        if (not p['passed'] or p['worker']['cuda_initialized'] or p['worker']['cuda_device_count']
                or p['model_loaded'] or p['natural_games'] or p['optimizer_updates']
                or p['runtime_environment']['resolved_config_sha256']!=receipts.digest(ROOT/f'cpu/{stage}/resolved_config.json')):
            raise RuntimeError('Real no-GPU Ray worker hook required')


def verify_probe(stage):
    p=a.read(ROOT/'gpu-preflight/gpu-preflight.json')
    if (stage!='gpu-preflight' or not p['passed'] or len(p['ranks'])!=8
            or len({r['cuda_uuid'] for r in p['ranks']})!=8 or p['nccl_sums']!=[28.0]*8
            or p['model_loaded'] or p['natural_games'] or p['optimizer_updates']
            or p['runtime_environment']['resolved_config_sha256']!=receipts.digest(ROOT/f'cpu/{STAGES[0]}/resolved_config.json')):
        raise RuntimeError('Distinct eight-GPU/NCCL proof required')


def verify(stage):
    spec=stage_spec(stage);out=ROOT/'runs'/stage
    result,evidence=a.verify_common(out,stage,8)
    if any(a.read(out/p).get('metrics_precision')!='binary64-v1' for p in ('manifest.json','result.json')):
        raise RuntimeError('Full-precision metrics required')
    load=a.read(out/'checkpoint_evaluation.json')
    ledger=[json.loads(x)['seeds'] for x in (out/'evaluation_seeds.jsonl').read_text().splitlines()]
    if (result['training_updates']!=0 or not load['val_only'] or load['optimizer_updates']!=0
            or load['loaded_global_step']!=spec['expected_step'] or load['games']!=8
            or load['checkpoint']!=(str(spec['checkpoint']) if spec['checkpoint'] else None)
            or load['checkpoint_load_returned']!=bool(spec['expected_step'])
            or load['game_seeds']!=spec['seeds'] or ledger!=[spec['seeds']]
            or load['temperature']!=0.8 or not load['do_sample'] or load['feedback']!='0'):
        raise RuntimeError('Actual model load/seeds/zero-update mismatch')
    outcomes=[json.loads(x) for x in (out/'episode_outcomes.jsonl').read_text().splitlines()]
    if (len(outcomes)!=8 or sorted(x['env_index'] for x in outcomes)!=list(range(8))
            or any(not x['terminated'] or x['truncated'] for x in outcomes)):
        raise RuntimeError('Eight unique natural outcomes required')
    if len(result['replays'])!=8 or any(f'/Flat128_{DIFFICULTY}_Air/' not in p for p in result['replays']):
        raise RuntimeError('Eight L8 replays required')
    rng=[]
    for rank in range(8):
        r=a.read(out/f'sampling-rank{rank}.json')
        if (r['rank'],r['seed'])!=(rank,rank):raise RuntimeError('Rank seed mismatch')
        rng.append({k:r[k] for k in ('rank','seed','cpu_rng_sha256','cuda_rng_sha256')})
    paired=[]
    for arm in ARMS:
        if arm==spec['arm']:continue
        path=ROOT/f'acceptance-b{spec["batch"]:02d}-{arm}.json'
        if path.exists():
            other=a.read(path)
            if other['rng']!=rng or other['seeds']!=spec['seeds']:raise RuntimeError('Paired CPU/CUDA RNG mismatch')
            paired.append(str(path))
    a.save(ROOT/f'acceptance-{stage}.json',dict(result=result,evidence=evidence,rng=rng,seeds=spec['seeds'],
        paired_with=paired,difficulty=DIFFICULTY,checked_at=time.time()))


def accounts(deadline):
    return [dict(roots=[ROOT,SOURCE_PARENT],receipt_root=ROOT,limit=LIMIT,deadline=deadline)]


def resources_ready():
    rows=a.cmd(['nvidia-smi','--query-gpu=index,memory.used,utilization.gpu','--format=csv,noheader,nounits']).splitlines()
    if len(rows)!=8 or sorted(int(r.split(',')[0]) for r in rows)!=list(range(8)):raise RuntimeError('Eight GPUs required')
    if any(float(v.strip())>0 for r in rows for v in r.split(',')[1:]):return False
    if a.cmd(['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader']):return False
    mem=dict(row.split(':',1) for row in Path('/proc/meminfo').read_text().splitlines())
    return int(mem['MemAvailable'].split()[0])*1024>=600*a.GIB and shutil.disk_usage(ROOT).free>=128*a.GIB


def admit(stage,deadline):
    if stage not in (*STAGES,'first','gpu-preflight'):raise ValueError('Undeclared stage')
    while True:
        if time.time()>=deadline-45:raise TimeoutError('Fixed admission/deadline reached')
        h.sample(accounts(deadline),ROOT);writers_clear([ROOT,SOURCE_PARENT,*CHECKPOINTS.values()])
        if resources_ready():break
        a.save(ROOT/'admission-wait.json',dict(stage=stage,deadline=deadline,checked_at=time.time()))
        time.sleep(min(30,deadline-45-time.time()))
    path=ROOT/('fsync-'+stage)
    with path.open('xb') as f:f.write(b'common64\n');f.flush();os.fsync(f.fileno())
    if path.read_bytes()!=b'common64\n':raise RuntimeError('Fsync/readback failed')
    a.save(ROOT/f'admission-{stage}.json',dict(passed=True,deadline=deadline,checked_at=time.time(),
        eight_idle_gpus=True,ram_gib_min=600,nvme_gib_min=128,fsync=True))


def queue():
    check_cpu();proof=parents()
    with (ROOT/'queue.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (ROOT/'queue-state.json').exists() or (ROOT/'dispatch.json').exists():raise RuntimeError('Already queued/dispatched; no retry')
        state=dict(phase='waiting-admission',completed=[],new_games=192,new_updates=0)
        try:
            a.save(ROOT/'parent-admission.json',proof);a.save(ROOT/'queue-state.json',state)
            admit('first',a.read(ROOT/'deployment.json')['first_dispatch_by'])
            start=time.time();deadline=start+WALL_SECONDS
            a.save(ROOT/'dispatch.json',dict(start=start,deadline=deadline,gpu_hours=48,new_games=192,new_updates=0,includes_gpu_preflight=True))
            state.update(phase='gpu-preflight',deadline=deadline);a.save(ROOT/'queue-state.json',state)
            h.run_stages(['gpu-preflight'],lambda _:docker('gpu-preflight',STAGES[0]),verify_probe,
                accounts(deadline),ROOT,ROOT/'gpu-preflight-supervision',ROOT,deadline,admit=lambda _:admit('gpu-preflight',deadline))
            state.update(phase='running-unverified');a.save(ROOT/'queue-state.json',state)
            terminal=h.run_stages(STAGES,lambda s:docker('stage',s),verify,accounts(deadline),ROOT,
                ROOT/'host-supervision',ROOT,deadline,admit=lambda s:admit(s,deadline))
            a.save(ROOT/'state.json',terminal);a.save(ROOT/'queue-state.json',terminal)
        except BaseException as exc:
            state.update(phase='failed',error_type=type(exc).__name__,error=str(exc),finished_at=time.time())
            a.save(ROOT/'state.json',state);a.save(ROOT/'queue-state.json',state);raise


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode',choices=['prepare','cpu','cpu-command','regressions','host-regressions',
        'regressions-command','cpu-hook','cpu-hook-command','gpu-preflight','queue','stage'])
    p.add_argument('stage',nargs='?',choices=STAGES);arg=p.parse_args()
    # Test old controllers without changing their globals/fixtures.
    if arg.mode in ('regressions','host-regressions'):regressions(arg.mode=='host-regressions');return
    configure()
    if arg.mode.endswith('-command'):print(json.dumps(docker(arg.mode.removesuffix('-command'),arg.stage)))
    elif arg.mode in ('prepare','cpu','queue'):globals()[arg.mode]()
    elif arg.mode in ('cpu-hook','gpu-preflight'):
        stage_spec(arg.stage);config=ROOT/f'cpu/{arg.stage}/resolved_config.json'
        if arg.mode=='cpu-hook':probe.check_hook_cpu(ROOT/f'cpu/hook-{arg.stage}',Path('/tmp/hook-'+arg.stage),config,environment_loader=runtime_environment)
        elif arg.stage==STAGES[0]:probe.run(ROOT/'gpu-preflight',Path('/tmp/probe-ray'),config,environment_loader=runtime_environment)
        else:raise ValueError('One bounded GPU probe only')
    else:
        cfg=a.read(ROOT/'deployment.json');a.clean(a.SOURCE,cfg['runtime_sha']);a.clean(ROOT/'runtime',cfg['runtime_sha'])
        args,env,_=invocation(cfg,arg.stage)
        fd=os.open(ROOT/(arg.stage+'-entry.log'),os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
        os.dup2(fd,1);os.dup2(fd,2);os.close(fd);os.chdir(ROOT/'runtime');os.execvpe(args[0],args,env)


if __name__=='__main__':main()
