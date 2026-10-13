"""Bounded Ray/NCCL eight-GPU visibility check; no model, SC2 or optimizer."""
from datetime import timedelta
import json
import os
from pathlib import Path
import signal


def run(output, ray_tmp, pythonpath):
    output, ray_tmp = Path(output), Path(ray_tmp)
    output.mkdir()
    ray_tmp.mkdir()
    # Docker intentionally disables daemon logs. Keep early Python/Ray errors
    # inside the accounted run so a failed one-shot probe remains diagnosable.
    fd = os.open(output / 'entry.log', os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    os.dup2(fd, 1)
    os.dup2(fd, 2)
    os.close(fd)
    import ray

    @ray.remote(num_gpus=1, num_cpus=1)
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
                 runtime_env=dict(worker_process_setup_hook='qwen_l8_hook.install',
                                  env_vars=dict(SC2_L8_STAGE='b01-random-cp96',
                                                SC2_L8_RENDEZVOUS_LOW_PORT='1',
                                                PYTHONPATH=pythonpath)))
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
                     natural_games=0, optimizer_updates=0)
        (output / 'gpu-preflight.json').write_text(json.dumps(proof, indent=2) + '\n')
        if not proof['passed']:
            raise RuntimeError('Eight-rank NCCL sum failed')
        print(json.dumps(dict(passed=True, devices=8, nccl_sum=28.0)), flush=True)
    finally:
        ray.shutdown()
        signal.alarm(0)


def check_hook_cpu(output, ray_tmp, pythonpath):
    """Run the real setup hook inside a no-GPU Ray worker before GPU admission."""
    output, ray_tmp = Path(output), Path(ray_tmp)
    output.mkdir()
    ray_tmp.mkdir()
    fd = os.open(output / 'entry.log', os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    os.dup2(fd, 1)
    os.dup2(fd, 2)
    os.close(fd)
    import ray

    @ray.remote(num_cpus=1)
    def worker():
        import sys
        import torch
        return dict(feedback_eval_loaded='feedback_eval' in sys.modules,
                    cuda_visible_devices=os.environ.get('CUDA_VISIBLE_DEVICES'),
                    cuda_initialized=torch.cuda.is_initialized(),
                    cuda_device_count=torch.cuda.device_count())

    signal.alarm(180)
    try:
        ray.init(num_cpus=1, num_gpus=0, include_dashboard=False,
                 object_store_memory=512 * 1024**2, _temp_dir=str(ray_tmp),
                 runtime_env=dict(worker_process_setup_hook='qwen_l8_hook.install',
                                  env_vars=dict(SC2_L8_STAGE='b01-random-cp96',
                                                SC2_L8_RENDEZVOUS_LOW_PORT='1',
                                                PYTHONPATH=pythonpath)))
        row = ray.get(worker.remote(), timeout=90)
        proof = dict(passed=row['feedback_eval_loaded'] and not row['cuda_initialized']
                     and row['cuda_device_count'] == 0,
                     worker=row, model_loaded=False, natural_games=0,
                     optimizer_updates=0, ray_pythonpath=pythonpath)
        (output / 'cpu-hook-preflight.json').write_text(json.dumps(proof, indent=2) + '\n')
        if not proof['passed']:
            raise RuntimeError('No-GPU Ray worker setup hook did not match launcher')
    finally:
        ray.shutdown()
        signal.alarm(0)
