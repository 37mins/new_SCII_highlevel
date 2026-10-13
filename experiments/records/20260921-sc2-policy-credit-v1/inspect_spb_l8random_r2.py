#!/usr/bin/env python3
"""Read-only forensic evidence for one failed run; never creates acceptance.

host: bounded streaming extraction of returned PPO rows, small ledgers and stat.
small: CPU-only loading of <1MiB driver/dataloader/rank RNG files, no model/Adam.
Both modes print a receipt to stdout and never modify the failed run.
"""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import random
import re
import time

ROOT = Path('/var/jfsCache/sc2-spb-l8random96-197-20260929-r2')
SOURCE = Path('/var/jfsCache/sc2-spb-l8random96-197-source-20260929-r2/code')
SHA = '12f3600ca8e6e8edabc460de70860baeef2b5146'
METRIC = re.compile(r'([\w/]+):(-?(?:\d+(?:\.\d*)?|nan|inf)(?:e[+-]?\d+)?)', re.I)
KEYS = ('actor/grad_norm', 'timing_s/update_actor',
        'policy_credit/invalid_advantage_max', 'episode/valid_action_ratio',
        'episode/success_rate', 'training/global_step')


def require(ok, message):
    if not ok:
        raise ValueError(message)


def small_bytes(path):
    require(path.is_file() and not path.is_symlink(), f'Not a regular file: {path}')
    require(0 < path.stat().st_size < 1024**2, f'Not a small receipt: {path}')
    return path.read_bytes()


def read(path):
    return json.loads(small_bytes(path))


def ledger(path):
    return [json.loads(line) for line in small_bytes(path).splitlines()]


def returned_rows(path, lo, hi):
    require(path.is_file() and not path.is_symlink(), 'Console must be a regular file')
    before = path.stat()
    require(0 < before.st_size < 100 * 1024**2, 'Console exceeds 100MiB bound')
    rows, digest, selected_bytes = {}, hashlib.sha256(), 0
    until = time.monotonic() + 60
    with path.open('rb') as stream:
        while True:
            raw = stream.readline(256 * 1024 + 1)
            if not raw:
                break
            require(len(raw) <= 256 * 1024, 'Console line exceeds 256KiB bound')
            require(time.monotonic() < until, 'Metric extraction exceeded 60 seconds')
            if b'actor/grad_norm:' not in raw or b'episode/success_rate:' not in raw:
                continue
            line = raw.decode('utf-8', errors='strict')
            match = re.search(r'\bstep:(\d+)\s+-', line)
            require(match is not None, 'PPO row without global step')
            require(' - metrics_precision:binary64-v1 - ' in line, 'Precision marker absent')
            step = int(match[1])
            require(step not in rows, 'Duplicate returned PPO step')
            values = {k: float(v) for k, v in METRIC.findall(line)}
            require(all(math.isfinite(v) for v in values.values()), 'Nonfinite returned metric')
            require(all(k in values for k in KEYS), 'Required returned metric missing')
            require(values['training/global_step'] == step, 'Metric step mismatch')
            require(values['actor/grad_norm'] > 0 and values['timing_s/update_actor'] > 0,
                    'No positive finite gradient/update duration')
            require(values['policy_credit/invalid_advantage_max'] <= 0, 'Positive invalid credit')
            require(values['episode/valid_action_ratio'] == 1, 'Invalid consumed answer ratio')
            rows[step] = {'step': step, **{k: values[k] for k in KEYS}}
            digest.update(raw)
            selected_bytes += len(raw)
    after = path.stat()
    require((before.st_size, before.st_mtime_ns) == (after.st_size, after.st_mtime_ns),
            'Console changed during extraction')
    require(sorted(rows) == list(range(lo, hi + 1)), 'Incomplete returned PPO interval')
    return {'rows': [rows[i] for i in sorted(rows)], 'source_bytes': before.st_size,
            'source_mtime_ns': before.st_mtime_ns, 'selected_bytes': selected_bytes,
            'selected_rows_sha256': digest.hexdigest(),
            'access': 'bounded server-side streaming scan; only PPO projections returned; no full-log download'}


def checkpoint(step):
    part, stage = ('short', 'train2') if step == 2 else ('long', 'train96')
    return ROOT / f'spb-random/{part}/runs/{stage}/checkpoints/global_step_{step}'


def names():
    return ['data.pt', 'sc2_state.pt'] + [f'actor/{kind}_world_size_8_rank_{r}.pt'
            for kind in ('model', 'optim', 'extra_state') for r in range(8)]


def host():
    require(read(ROOT/'queue-state.json')['phase'] == 'failed', 'Expected retained failed queue')
    long = ROOT/'spb-random/long'
    require(read(long/'host-supervision/state.json')['phase'] == 'failed', 'Expected failed host')
    result = {'queue_phase': 'failed', 'strict_training_accepted': False, 'stages': {}, 'checkpoints': {}}
    parent = ROOT/'spb-random/short'
    contract = read(long/'resume-contract.json')
    require(contract['version'] == 'accepted-spb-l8-random-full-state-prefix-v1'
            and contract['parent'] == str(parent) and contract['checkpoint'] == str(checkpoint(2))
            and contract['parent_sha'] == SHA and contract['start_step'] == 2
            and contract['target_step'] == 96 and contract['driver_rng_unavailable_accepted'] is False,
            'Unexpected accepted CP2 contract')
    require(read(parent/'state.json')['phase'] == 'completed', 'Short prefix not completed')
    for name, digest in contract['files'].items():
        require(Path(name).is_relative_to('.') and '..' not in Path(name).parts, 'Invalid receipt path')
        require(hashlib.sha256(small_bytes(parent/name)).hexdigest() == digest, 'Prefix receipt changed: '+name)
    for stage, games in [('pre',8), ('train2',16), ('post',8)]:
        out = parent/'runs'/stage
        terminal, manifest = read(out/'result.json'), read(out/'manifest.json')
        acceptance = read(parent/f'acceptance-{stage}.json')
        require(terminal == read(out/'.done') == acceptance['result']
                and terminal['status'] == 'completed' and terminal['process_exit_code'] == 0
                and terminal['metrics_finite'] and terminal['metrics_precision'] == 'binary64-v1'
                and terminal['episode_outcomes']['natural_games'] == games
                and terminal['episode_outcomes']['truncated'] == 0
                and manifest['source_commit'] == SHA and not manifest['dirty'] and manifest['world_size'] == 8,
                'Short prefix terminal disagreement')
    result['accepted_short_prefix'] = {'terminal_agreement': True, 'contract_files_matched': len(contract['files']),
            'contract_sha256': hashlib.sha256(small_bytes(long/'resume-contract.json')).hexdigest()}
    for part, stage, lo, hi in [('short', 'train2', 1, 2), ('long', 'train96', 3, 96)]:
        out = ROOT/f'spb-random/{part}/runs/{stage}'
        manifest = read(out/'manifest.json')
        require(manifest['source_commit'] == SHA and not manifest['dirty']
                and manifest['world_size'] == 8 and manifest['metrics_precision'] == 'binary64-v1',
                'Frozen manifest mismatch')
        metrics = returned_rows(out/'console.log', lo, hi)
        audit = ledger(out/'checkpoints/sc2_policy_credit_audit.jsonl')
        require([r['pending_global_step'] for r in audit] == list(range(lo, hi+1)), 'Audit interval mismatch')
        require(all(r['decision'] == 'accept' and r['real_answers'] > 0
                    and r['real_answers'] == r['valid_answers'] for r in audit), 'Audit validity mismatch')
        seeds = ledger(out/'training_seeds.jsonl')
        rng = random.Random(0)
        expected = [[rng.randint(0, 100) for _ in range(8)] for _ in range(96)]
        require(len(seeds) == hi-lo+1 and all(r['reset_index'] == i and r['base_seed'] == 0
                and r['seed_protocol'] == 'independent_uniform101' and r['seeds'] == expected[i]
                for i, r in enumerate(seeds, lo-1)), 'Independent seed ledger mismatch')
        outcomes = ledger(out/'episode_outcomes.jsonl')
        require(len(outcomes) == (hi-lo+1)*8 and
                {(r['reset_index'], r['env_index']) for r in outcomes} ==
                {(i, e) for i in range(lo-1, hi) for e in range(8)} and
                all(r['terminated'] and not r['truncated'] for r in outcomes), 'Natural outcome closure mismatch')
        wins = sum(r['game_result'] == 'Victory' for r in outcomes)
        for row in metrics['rows']:
            batch = [r for r in outcomes if r['reset_index'] == row['step']-1]
            require(row['episode/success_rate'] == sum(r['game_result'] == 'Victory' for r in batch)/8,
                    'Returned success rate disagrees with natural outcomes')
        terminal = {n: (out/n).exists() for n in ('result.json', '.done', 'metrics.json')}
        require(all(terminal.values()) if stage == 'train2' else not any(terminal.values()),
                'Unexpected terminal artifact change')
        result['stages'][stage] = {'returned': metrics, 'audits': len(audit),
                'legal_answers': sum(r['valid_answers'] for r in audit), 'seed_batches': len(seeds),
                'natural_games': len(outcomes), 'wins': wins, 'terminal_files': terminal,
                'small_evidence_sha256': {str(p.relative_to(out)): hashlib.sha256(small_bytes(p)).hexdigest()
                    for p in [out/'manifest.json', out/'training_seeds.jsonl', out/'episode_outcomes.jsonl',
                              out/'checkpoints/sc2_policy_credit_audit.jsonl']}}
    resume = read(long/'runs/train96/checkpoints/resume_state.json')
    require(resume['source'] == 'checkpoint' and resume['from_checkpoint'] == str(checkpoint(2))
            and resume['global_step'] == resume['next_reset_index'] == 2
            and resume['next_seeds'] == [36,17,96,12,79,32,68,90]
            and resume['model_optimizer_dataloader_load_returned'], 'Native CP2 load receipt mismatch')
    result['native_cp2_load_receipt'] = resume
    for step in (2,32,64,96):
        cp = checkpoint(step)
        inventory = {}
        for name in names():
            p = cp/name
            require(p.is_file() and not p.is_symlink() and p.stat().st_size > 0, 'Incomplete CP: '+str(p))
            inventory[name] = p.stat().st_size
        result['checkpoints'][step] = {'path': str(cp), 'bytes': sum(inventory.values()),
                'required_files': inventory, 'model_optimizer_content_checked': False}
    return result


def small_state():
    import sys
    import numpy as np
    import torch
    from types import SimpleNamespace
    sys.path.insert(0, str(SOURCE))
    from agent_system.sc2_resume import restore_environment
    require(not torch.cuda.is_initialized() and not torch.cuda.is_available(), 'CPU-only check required')
    os.environ['SC2_TRAIN_SEED_PROTOCOL'] = 'independent_uniform101'
    results = {}
    for step in (2,32,64,96):
        cp, digests = checkpoint(step), {}
        def load(name):
            import io
            content = small_bytes(cp/name)
            digests[name] = hashlib.sha256(content).hexdigest()
            return torch.load(io.BytesIO(content), map_location='cpu', weights_only=False)
        state = load('sc2_state.pt')
        require(state['global_step'] == step and not state['empty_policy_batches'], 'CP not at closed global step')
        py, nr, tr = state['driver_rng']
        random.Random().setstate(py)
        np.random.RandomState().set_state(nr)
        torch.Generator().set_state(tr)
        for label in ('train_env', 'val_env'):
            saved = state[label]
            raw = SimpleNamespace(**{k:saved[k] for k in ('seed','env_num','group_n','is_train')},
                    reset_index=0,training_rng=np.random.RandomState(0),validation_rng=np.random.RandomState(0))
            restore_environment(SimpleNamespace(envs=raw,memory=None), saved)
            if label == 'train_env':
                require(raw.reset_index == step and raw.seed == 0 and raw.group_n == 8 and raw.env_num == 1,
                        'SC2 counter/protocol mismatch')
        for rank in range(8):
            extra = load(f'actor/extra_state_world_size_8_rank_{rank}.pt')
            require(extra['lr_scheduler']['last_epoch'] == step, 'Scheduler step mismatch')
            rng = extra['rng']
            for name in ('cpu','cuda'):
                require(isinstance(rng[name],torch.Tensor) and rng[name].numel() > 0, 'Rank RNG absent')
            torch.Generator().set_state(rng['cpu'])
            random.Random().setstate(rng['random'])
            np.random.RandomState().set_state(rng['numpy'])
        require(bool(load('data.pt')), 'Dataloader state absent')
        results[step] = {'global_step': step, 'train_reset_index': step, 'driver_rng_valid': True,
                'rank_rng_states': 8, 'scheduler_epochs': step, 'small_file_sha256': digests}
    require(not torch.cuda.is_initialized(), 'CUDA was initialized')
    return {'passed': True, 'cuda_initialized': False, 'checkpoints': results,
            'model_optimizer_tensors_loaded': False, 'strict_training_accepted': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['host','small'])
    args = parser.parse_args()
    result = host() if args.mode == 'host' else small_state()
    print(json.dumps({'checked_at': time.time(), 'source_sha': SHA,
        'mode': args.mode, 'diagnostic_only': True, 'run_writes': False, 'result': result},
        indent=2, allow_nan=False))
