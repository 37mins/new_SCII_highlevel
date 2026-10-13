"""Bounded Ray/NCCL eight-GPU visibility check; no model, SC2 or optimizer."""
from datetime import timedelta
import copy
import hashlib
import json
import os
from pathlib import Path
import signal

def runtime_environment(resolved_config, ray_tmp):
    """Use the actual launcher's complete Ray environment, with isolated tmp paths."""
    source = Path(resolved_config)
    if source.stat().st_size > 1024**2:
        raise ValueError('Expected small CPU/Hydra resolved configuration')
    raw = source.read_bytes()
    cfg = json.loads(raw)
    env = copy.deepcopy(cfg['ray_init']['runtime_env'])
    variables = env['env_vars']
    required = ('PYTHONPATH', 'SC2PATH', 'SC2_L8_STAGE', 'SC2_DIFFICULTY',
                'SC2_EXPECTED_DIFFICULTY', 'SC2_L8_RENDEZVOUS_LOW_PORT',
                'SC2_EVAL_SEEDS_LOG_PATH', 'SC2_RUNTIME_LOG_ROOT')
    if (env.get('worker_process_setup_hook') != 'qwen_l8_hook.install'
            or any(not variables.get(k) for k in required)
            or variables['SC2PATH'] != '/assets/StarCraftII'
            or variables['SC2_L8_STAGE'] != 'b01-random-cp96'
            or variables['SC2_DIFFICULTY'] != 'CheatVision'
            or variables['SC2_EXPECTED_DIFFICULTY'] != 'CheatVision'
            or str(variables['SC2_L8_RENDEZVOUS_LOW_PORT']) != '1'
            or not cfg['trainer']['val_only']
            or cfg['trainer']['n_gpus_per_node'] != 8):
        raise ValueError('Complete matching frozen L8 evaluation environment required')
    variables.update(TMPDIR=str(ray_tmp), RAY_TMPDIR=str(ray_tmp))
    return env, dict(resolved_config_sha256=hashlib.sha256(raw).hexdigest(),
        env_sha256=hashlib.sha256(json.dumps(env, sort_keys=True).encode()).hexdigest(),
        env_var_names=sorted(variables), overridden_env_vars=['RAY_TMPDIR', 'TMPDIR'],
        worker_process_setup_hook=env['worker_process_setup_hook'])


def run(output, ray_tmp, resolved_config, *, environment_loader=runtime_environment):
    output, ray_tmp = Path(output), Path(ray_tmp)
    runtime_env, environment_proof = environment_loader(resolved_config, ray_tmp)
    output.mkdir()
    ray_tmp.mkdir()
    # Docker intentionally disables daemon logs. Keep early Python/Ray errors
    # inside the accounted run so a failed one-shot probe remains diagnosable.
    fd = os.open(output / 'entry.log', os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    os.dup2(fd, 1)
    os.dup2(fd, 2)
    os.close(fd)
    import ray

    @ray.remote(num_gpus=1, num_cpus=1, max_restarts=0, max_task_retries=0)
    class Probe:
        def identity(self, rank):
            import torch
            from verl.single_controller.base.worker import WorkerHelper

            if torch.cuda.device_count() != 1:
                raise RuntimeError('Expected exactly one visible GPU per Ray actor')
            properties = torch.cuda.get_device_properties(0)
            return dict(rank=rank, visible_devices=os.environ.get('CUDA_VISIBLE_DEVICES'),
                        ray_gpu_ids=ray.get_gpu_ids(), cuda_uuid=str(properties.uuid),
                        master_port=WorkerHelper()._get_free_port())

        def nccl(self, rank, port):
            import torch
            import torch.distributed as dist

            dist.init_process_group('nccl', init_method=f'tcp://127.0.0.1:{port}',
                                    rank=rank, world_size=8, timeout=timedelta(seconds=45))
            try:
                value = torch.tensor(float(rank), device='cuda')
                dist.all_reduce(value)
                return value.item()
            finally:
                dist.destroy_process_group()

    signal.alarm(240)
    try:
        ray.init(num_cpus=8, num_gpus=8, include_dashboard=False,
                 object_store_memory=1024**3, _temp_dir=str(ray_tmp),
                 runtime_env=runtime_env)
        actors = [Probe.remote() for _ in range(8)]
        rows = ray.get([actor.identity.remote(rank) for rank, actor in enumerate(actors)],
                       timeout=90)
        if (sorted(row['rank'] for row in rows) != list(range(8))
                or len({row['cuda_uuid'] for row in rows}) != 8
                or len({str(row['visible_devices']) for row in rows}) != 8
                or any(not row['ray_gpu_ids'] for row in rows)):
            raise RuntimeError('Eight distinct Ray/CUDA device identities required')
        port = rows[0]['master_port']
        sums = ray.get([actor.nccl.remote(rank, port) for rank, actor in enumerate(actors)],
                       timeout=90)
        proof = dict(passed=all(value == 28.0 for value in sums),
                     ranks=rows, nccl_sums=sums, model_loaded=False,
                     natural_games=0, optimizer_updates=0,
                     runtime_environment=environment_proof)
        (output / 'gpu-preflight.json').write_text(json.dumps(proof, indent=2) + '\n')
        if not proof['passed']:
            raise RuntimeError('Eight-rank NCCL sum failed')
        print(json.dumps(dict(passed=True, devices=8, nccl_sum=28.0)), flush=True)
    finally:
        ray.shutdown()
        signal.alarm(0)


def check_hook_cpu(output, ray_tmp, resolved_config, *, environment_loader=runtime_environment):
    """Run the real setup hook inside a no-GPU Ray worker before GPU admission."""
    output, ray_tmp = Path(output), Path(ray_tmp)
    runtime_env, environment_proof = environment_loader(resolved_config, ray_tmp)
    pythonpath = runtime_env["env_vars"]["PYTHONPATH"]
    required_module = environment_proof.get('required_worker_module', 'feedback_eval')
    output.mkdir()
    ray_tmp.mkdir()
    fd = os.open(output / 'entry.log', os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    os.dup2(fd, 1)
    os.dup2(fd, 2)
    os.close(fd)
    import ray

    @ray.remote(num_cpus=1, max_retries=0)
    def worker():
        import sys
        import torch
        return dict(feedback_eval_loaded='feedback_eval' in sys.modules,
                    required_module=required_module, required_module_loaded=required_module in sys.modules,
                    sc2path=os.environ.get('SC2PATH'),
                    cuda_visible_devices=os.environ.get('CUDA_VISIBLE_DEVICES'),
                    cuda_initialized=torch.cuda.is_initialized(),
                    cuda_device_count=torch.cuda.device_count())

    signal.alarm(180)
    try:
        ray.init(num_cpus=1, num_gpus=0, include_dashboard=False,
                 object_store_memory=512 * 1024**2, _temp_dir=str(ray_tmp),
                 runtime_env=runtime_env)
        row = ray.get(worker.remote(), timeout=90)
        proof = dict(passed=row['required_module_loaded'] and not row['cuda_initialized']
                     and row['cuda_device_count'] == 0
                     and row['sc2path'] == runtime_env['env_vars']['SC2PATH'],
                     worker=row, model_loaded=False, natural_games=0,
                     optimizer_updates=0, ray_pythonpath=pythonpath,
                     runtime_environment=environment_proof)
        (output / 'cpu-hook-preflight.json').write_text(json.dumps(proof, indent=2) + '\n')
        if not proof['passed']:
            raise RuntimeError('No-GPU Ray worker setup hook did not match launcher')
    finally:
        ray.shutdown()
        signal.alarm(0)
