"""Read-only chart snapshot. Run via ssh sc2-a100-197 python3 - < this file.

Only small receipts (1 MiB maximum each) and a 4 MiB console tail are read.
With --complete, require finalized metrics1..96 and do not read console logs.
No checkpoint tensor, complete large log, server output or GPU diagnostic.
"""
import collections
import datetime
import hashlib
import json
import math
from pathlib import Path
import random
import re
import subprocess
import sys

ROOT = Path('/var/jfsCache/sc2-l7-followup197-20260922-r4')
SHORT = ROOT / 'spb-same/short'
LONG = ROOT / 'spb-same/long'
SHA = '9cb291ea5f50de205c5d88371e08ce229b7d9d04'
hashes = {}
complete = '--complete' in sys.argv[1:]


def small(path, optional=False):
    if optional and not path.exists():
        return None
    with path.open('rb') as f:
        b = f.read(1048577)
    if len(b) > 1048576:
        raise ValueError('Not a small receipt: ' + str(path))
    hashes[str(path)] = hashlib.sha256(b).hexdigest()
    return b.decode()


def js(path, optional=False):
    text = small(path, optional)
    return json.loads(text) if text is not None else None


def jl(path):
    return [json.loads(line) for line in small(path).splitlines() if line.strip()]


manifest = js(LONG / 'runs/train96/manifest.json')
assert manifest['source_commit'] == SHA and not manifest['dirty']
assert manifest['world_size'] == 8 and manifest['start_step'] == 2
resume = js(LONG / 'runs/train96/checkpoints/resume_state.json')
assert resume['model_optimizer_dataloader_load_returned'] and resume['global_step'] == 2
assert resume['from_checkpoint'] == str(SHORT / 'runs/train2/checkpoints/global_step_2')
assert js(SHORT / 'runs/train2/result.json') == js(SHORT / 'runs/train2/.done')
parent_metrics = js(SHORT / 'runs/train2/metrics.json')
assert len(parent_metrics) == 2

returned = {}
terminal, full_metrics, manifests, console_tail = {}, [], {}, None
if complete:
    for name, run, expected in [('short', SHORT / 'runs/train2', range(1, 3)),
                                ('long', LONG / 'runs/train96', range(3, 97))]:
        result = js(run / 'result.json')
        assert result == js(run / '.done')
        assert result['status'] == 'completed' and result['process_exit_code'] == 0
        assert result['metrics_finite'] and result['metrics_precision'] == 'binary64-v1'
        assert result['completed_steps'] == len(expected)
        m = js(run / 'manifest.json')
        assert m['source_commit'] == SHA and not m['dirty'] and m['world_size'] == 8
        assert m['metrics_precision'] == 'binary64-v1'
        manifests[name] = m
        metrics = js(run / 'metrics.json')
        assert [r['step'] for r in metrics] == list(expected)
        assert all(isinstance(v, (int, float)) and math.isfinite(v)
                   for r in metrics for v in r.values())
        for r in metrics:
            assert r['actor/grad_norm'] > 0 and r['timing_s/update_actor'] > 0
            assert r['policy_credit/invalid_advantage_max'] <= 0
            returned[int(r['step'])] = r
        full_metrics.extend(metrics)
        terminal[name] = {k: result[k] for k in ('status', 'ended_at', 'process_exit_code',
            'completed_steps', 'start_step', 'last_global_step', 'metrics_finite', 'metrics_precision')}
        terminal[name]['result_equals_done'] = True
else:
    console = LONG / 'runs/train96/console.log'
    with console.open('rb') as f:
        size = f.seek(0, 2)
        start = max(0, size - 4194304)
        f.seek(start)
        b = f.read(4194304)
    clean = re.sub(r'\x1b\[[0-9;]*[A-Za-z]', '', b.decode(errors='replace'))
    for line in clean.splitlines():
        m = re.search(r'\bstep:(\d+) - metrics_precision:binary64-v1', line)
        if m and 'actor/grad_norm:' in line:
            metrics = {k: float(v) for k, v in re.findall(r'([A-Za-z_][\w/.-]*):(-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)', line)}
            returned[int(m[1])] = metrics
    console_tail = {'bytes_read': len(b), 'start': start, 'file_bytes': size,
                    'sha256': hashlib.sha256(b).hexdigest()}
assert returned, 'No completed PPO metric rows'
last = max(returned)

seeds, outcomes, audits = {}, collections.defaultdict(list), {}
for run in (SHORT / 'runs/train2', LONG / 'runs/train96'):
    for row in jl(run / 'training_seeds.jsonl'):
        step = row['reset_index'] + 1
        assert step not in seeds
        seeds[step] = row
    for row in jl(run / 'episode_outcomes.jsonl'):
        outcomes[row['reset_index'] + 1].append(row)
    for row in jl(run / 'checkpoints/sc2_policy_credit_audit.jsonl'):
        step = row['pending_global_step']
        assert step not in audits
        audits[step] = row

rng, rows = random.Random(0), []
for step in range(1, last + 1):
    seed = rng.randint(0, 100)
    s, games, a = seeds[step], outcomes[step], audits[step]
    assert s['seed_protocol'] == 'same_uniform101' and s['seeds'] == [seed] * 8
    assert len(games) == 8 and sorted(g['env_index'] for g in games) == list(range(8))
    assert all(g['terminated'] and not g['truncated'] for g in games)
    assert a['decision'] == 'accept' and a['real_answers'] > 0
    assert a['valid_answers'] == a['real_answers']
    wins = sum(g['game_result'] == 'Victory' for g in games)
    if step in returned:
        assert returned[step]['episode/success_rate'] == wins / 8
        assert returned[step]['episode/valid_action_ratio'] == a['valid_answers'] / a['real_answers']
    rows.append({'step': step, 'seed': seed, 'games': 8, 'wins': wins,
                 'win_rate': wins / 8, 'real_answers': a['real_answers'],
                 'valid_answers': a['valid_answers'],
                 'valid_action_ratio': a['valid_answers'] / a['real_answers'],
                 'source': 'accepted short' if step <= 2 else 'native continuation'})

evaluations = {}
for stage in (('pre', 'post', 'eval96') if complete else ('pre', 'post')):
    run = (LONG if stage == 'eval96' else SHORT) / 'runs' / stage
    result = js(run / 'result.json')
    assert result == js(run / '.done')
    assert result['status'] == 'completed' and result['process_exit_code'] == 0
    assert result['training_updates'] == 0
    games = jl(run / 'episode_outcomes.jsonl')
    assert len(games) == 8 and all(g['terminated'] and not g['truncated'] for g in games)
    evaluations[stage] = {'wins': sum(g['game_result'] == 'Victory' for g in games), 'games': 8}

container = json.loads(subprocess.check_output(['docker', 'inspect', '--format', '{{json .State}}',
    'sc2-l7-followup197-20260922-r4-spb-same-long-train96'], text=True, timeout=15))
out = {'schema': 'spb-l7-curve-v2' if complete else 'spb-l7-curve-v1',
       'complete': complete, 'full_metrics': full_metrics, 'terminal': terminal,
       'training_manifests': manifests,
       'checked_at': datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(),
       'root': str(ROOT), 'runtime_sha': SHA, 'rows': rows,
       'queue': js(ROOT / 'queue-state.json'),
       'host_state': js(LONG / 'host-supervision/state.json'), 'container_state': container,
       'resume': resume, 'evaluations': evaluations,
       'train_result': terminal.get('long') if complete else js(LONG / 'runs/train96/result.json', True),
       'eval_result': evaluations.get('eval96') if complete else js(LONG / 'runs/eval96/result.json', True),
       'qwen_random_dispatch': js(ROOT / 'qwen-random/long/dispatch.json', True),
       'storage_failure': js(ROOT / 'storage-failure.json', True),
       'arm_storage_failure': js(LONG / 'storage-failure.json', True),
       'recent_returned_ppo': [{'step': step, **{k: m[k] for k in
           ('actor/grad_norm', 'episode/success_rate', 'episode/valid_action_ratio',
            'policy_credit/invalid_advantage_max', 'timing_s/step')}} for step, m in sorted(returned.items())],
       'console_tail': console_tail,
       'summary': {'last_step': last, 'games': 8 * last, 'wins': sum(r['wins'] for r in rows),
                   'last8_wins': sum(r['wins'] for r in rows[-8:]),
                   'real_answers': sum(r['real_answers'] for r in rows),
                   'valid_answers': sum(r['valid_answers'] for r in rows)},
       'receipt_sha256': hashes,
       'limits': ['Full trajectory uses natural-outcome and consumed-answer ledgers only through the latest returned PPO step.',
                  'Pre-update audits alone do not prove PPO completion. Latest returned step bounds this serial trajectory; final strict all-update acceptance remains pending.',
                  'No reward curve: historical per-step reward metrics were not read from complete large logs.',
                  'Training seed changes between steps. Curves are descriptive, not a controlled learning or architecture advantage test.',
                  'Short pre/post evaluations are separate from training curves; no interpolation or missing-step zero fill.']}
if complete:
    assert last == 96 and len(full_metrics) == 96
    out['limits'] = [
        'Full finalized metrics1..96 retained; short1..2 and own-native-CP2 continuation3..96. No console or large checkpoint read.',
        'Both training stages completed/exit0/result=.done; all metrics finite and positive update gradients/durations verified.',
        'Training seed changes between steps. Curves are descriptive, not a controlled learning or architecture advantage test.',
        'Consumption legality is constrained mechanically, not evidence of strategy learning.',
        'Pre/CP2/CP96 evaluations are separate eight-game samples; do not concatenate with training or infer stable generalization from them.'
    ]
print(json.dumps(out, ensure_ascii=False, allow_nan=False))
