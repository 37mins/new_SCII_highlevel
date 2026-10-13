"""Complete the exact r6 pre-deployment Git scaffold; never dispatch a container."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess as sp
import sys
import time

SOURCE = Path('/var/jfsCache/sc2-qwen-l8-pilot96-197-source-20260926-r6/code')
SHA = '769e55ef1b615ed08fe3259aee7026c730874429'
sys.path.insert(0, str(SOURCE / 'experiments/records/20260921-sc2-policy-credit-v1'))
import qwen_l8_remainder6_197 as r6


def main():
    r6.configure()
    a, pilot, matrix, root = r6.a, r6.pilot, r6.matrix, r6.ROOT
    a.clean(SOURCE, SHA)
    if (set(p.name for p in root.iterdir()) != {'cpu', 'runs', 'tmp', 'runtime'}
            or list((root / 'cpu').iterdir()) or list((root / 'runs').iterdir())
            or set(p.name for p in (root / 'runtime').iterdir()) != {'.git'}):
        raise RuntimeError('Only the observed unfinished r6 preparation is permitted')
    if a.cmd(['docker', 'ps', '-a', '--filter', 'name=' + r6.PREFIX,
              '--format', '{{.ID}}']):
        raise RuntimeError('r6 already has a container; preparation completion denied')
    runtime = root / 'runtime'
    if a.cmd(['git', '-C', runtime, 'rev-parse', 'HEAD']) != SHA:
        raise RuntimeError('Partial runtime HEAD changed')
    alternate = runtime / '.git/objects/info/alternates'
    alternate_bytes = alternate.read_bytes()
    if alternate_bytes.decode().strip() != str(SOURCE / '.git/objects'):
        raise RuntimeError('Unexpected partial Git object source')
    history, parents = r6.previous_failures(), pilot.parents()
    a.measure_budget(r6.accounts(0)[0]['roots'], root, r6.LIMIT,
                     time.time() + 600, 'Preparation ceiling', '32GiB aggregate ceiling')
    # Materialize the same already-verified commit. Read the frozen source;
    # write only the incomplete new runtime, preserving its alternate pointer.
    packed = sp.run(['git', '-C', str(SOURCE), 'pack-objects', '--stdout', '--revs'],
                    input=(SHA + '\n').encode(), capture_output=True, timeout=60, check=True)
    if len(packed.stdout) > 256 * 1024**2:
        raise RuntimeError('Unexpectedly large source-only Git pack')
    indexed = sp.run(['git', '-C', str(runtime), 'index-pack', '--stdin'],
                     input=packed.stdout, capture_output=True, timeout=60, check=True)
    alternate.rename(alternate.with_name('alternates.preparation-history'))
    a.cmd(['git', '-C', runtime, 'checkout', '--quiet', '--detach', SHA])
    a.clean(runtime, SHA)
    a.clean(SOURCE, SHA)
    source = matrix.small(pilot.PARENTS['same-cp96'] / 'qwen-same/short/deployment.json')
    arms = {}
    for arm in r6.ARMS:
        cfg = copy.deepcopy(source)
        cfg.update(runtime_sha=SHA, controller_sha=SHA, controller_source=str(SOURCE),
                   difficulty='CheatVision', run_prefix=r6.PREFIX,
                   worker_hook='qwen_l8_hook.install', seed_protocol='same_uniform101',
                   seed_group_mode='same')
        arms[arm] = cfg
    a.save(root / 'deployment.json', dict(runtime_sha=SHA, controller_sha=SHA,
        controller_source=str(SOURCE), orchestration_sha=a.ORCH_SHA,
        arms=arms, stages=r6.STAGES, games=[8] * len(r6.STAGES), updates=[0] * len(r6.STAGES),
        eval_seeds=r6.SEEDS, wall_seconds=r6.WALL_SECONDS, gpu_hours=32,
        output_limit_bytes=r6.LIMIT, storage_roots=[str(x) for x in r6.accounts(0)[0]['roots']],
        previous_accepted_games=32, r2_new_games=0, r3_new_games=0, r4_new_games=0, r5_new_games=0,
        new_games=64, new_updates=0, first_dispatch_by=time.time() + 2 * 3600,
        no_retry=True, no_training=True, successors_authorized=False,
        gpu_preflight_required=True, cpu_ray_hook_preflight_required=True,
        gpu_preflight_natural_games=0, gpu_preflight_ray_tmp='/tmp/probe-ray',
        level='L8', difficulty='CheatVision',
        port_mitigation='deferred low-port allocation inside Ray actor constructor',
        authorization='Sep26 user: one new r6 attempt of remaining64 L8 games; '
                      '197 eight GPUs serial,zero updates,new4h/32GPUh,twelve roots/32GiB; '
                      'no deletion,automatic retry or L8 RL'))
    a.save(root / 'historical-boundary.json', history)
    a.save(root / 'parent-acceptance.json', parents)
    a.save(root / 'preparation-completion.json', dict(runtime_sha=SHA,
        cause='git shared-alternate nesting depth exceeded before deployment existed',
        source_unchanged=True, runtime_clean=True, containers_before=[],
        games=0, updates=0, dispatch=False,
        git_pack_bytes=len(packed.stdout), git_pack_sha256=hashlib.sha256(packed.stdout).hexdigest(),
        index_pack_output=indexed.stdout.decode().strip(),
        original_alternates_sha256=hashlib.sha256(alternate_bytes).hexdigest(),
        helper_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        checked_at=time.time()))
    print(json.dumps(dict(prepared=True, runtime_sha=SHA, gpu_dispatched=False)))


if __name__ == '__main__':
    main()
