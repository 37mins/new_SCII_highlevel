"""Read-only, bounded collector. Run via SSH stdin on sc2-a100-197.

Reads small outcome/seed ledgers and at most the final 2 MiB of the active
console. It does not load checkpoints, import training code, or write remotely.
"""
import hashlib
import json
import math
import pathlib
import random
import re
from datetime import datetime, timedelta, timezone

ROOT = pathlib.Path('/var/jfsCache/sc2-qwen-l8same96-197-20260926-r2')
PREFIX = pathlib.Path('/var/jfsCache/sc2-qwen-l8same96-197-20260926-r1/qwen-same/short/runs/train2')
RUN = ROOT / 'qwen-same/long/runs/train96'
evidence = []


def small(path, jsonl=False, optional=False):
    if optional and not path.exists():
        return None
    with path.open('rb') as f:
        data = f.read(1024 * 1024 + 1)
    assert len(data) <= 1024 * 1024, ('Not a small ledger', str(path))
    evidence.append({'path': str(path), 'bytes': len(data),
                     'sha256': hashlib.sha256(data).hexdigest()})
    if jsonl:
        # A partial append is not a valid snapshot; fail instead of skipping it.
        assert not data or data.endswith(b'\n'), ('Partial JSONL record', str(path))
        return [json.loads(line) for line in data.splitlines()]
    return json.loads(data)


with (RUN / 'console.log').open('rb') as f:
    f.seek(0, 2)
    end = f.tell()
    start = max(0, end - 2 * 1024 * 1024)
    f.seek(start)
    tail = f.read(end - start).decode('utf-8', errors='replace')
tail_lines = tail.splitlines()[1:-1]  # Exclude possibly clipped edge lines.
keys = ['episode/success_rate', 'actor/grad_norm', 'timing_s/update_actor',
        'timing_s/step', 'episode/valid_action_ratio', 'policy_credit/invalid_advantage_max']
returned = []
for line in tail_lines:
    if 'metrics_precision:binary64-v1' not in line or 'timing_s/update_actor:' not in line:
        continue
    row = {'step': int(re.search(r'\bstep:(\d+)', line)[1])}
    for key in keys:
        row[key] = float(re.search(re.escape(key) + r':([^\s]+)', line)[1])
        assert math.isfinite(row[key])
    assert row['actor/grad_norm'] > 0 and row['timing_s/update_actor'] > 0
    returned.append(row)
assert returned and len({r['step'] for r in returned}) == len(returned)
last = max(r['step'] for r in returned)
assert 3 <= last <= 96
prefix_metrics = small(PREFIX / 'metrics.json')
assert [r['step'] for r in prefix_metrics] == [1, 2]
rng = random.Random(0)
expected = [rng.randint(0, 100) for _ in range(96)]
rows = []
for run, first, stop, source in [(PREFIX, 1, 2, 'r1/train2-retained'), (RUN, 3, last, 'r2/train96')]:
    outcomes = small(run / 'episode_outcomes.jsonl', jsonl=True)
    seeds = small(run / 'training_seeds.jsonl', jsonl=True)
    seed_map = {r['reset_index']: r for r in seeds}
    assert len(seed_map) == len(seeds)
    for step in range(first, stop + 1):
        group = [r for r in outcomes if r['reset_index'] == step - 1]
        assert len(group) == 8 and sorted(r['env_index'] for r in group) == list(range(8))
        assert all(r['terminated'] is True and r['truncated'] is False for r in group)
        seed = seed_map[step - 1]
        assert seed['base_seed'] == 0 and seed['seed_protocol'] == 'same_uniform101'
        assert seed['seeds'] == [expected[step - 1]] * 8
        wins = sum(r['game_result'] == 'Victory' for r in group)
        rows.append({'step': step, 'games': 8, 'wins': wins,
                     'seed': expected[step - 1], 'source': source})
for metric in prefix_metrics + returned:
    assert rows[int(metric['step']) - 1]['wins'] / 8 == metric['episode/success_rate']
queue = small(ROOT / 'queue-state.json')
host = small(ROOT / 'qwen-same/long/host-supervision/state.json')
assert host['stage'] == 'train96'
assert host['container_id'] == '91d0dbd99c166ea114df62af0e3d07ec3aa94cf3f59f5d4a86ea43d6ff4d986b'
assert queue['deadline'] == 1790530922.7417548
data = {
    'schema': 'sc2-l8same-partial-win-curve-v1',
    'checked_at_beijing': datetime.now(timezone(timedelta(hours=8))).isoformat(),
    'node': 'sc2-a100-197', 'target_steps': 96, 'last_returned_step': last,
    'runtime_sha': 'eef0f049bb09b7a51188ae67a6c35436a3bf055f',
    'controller_sha': 'db60d075879750cabf30a38c555d1c3aaaf104c1',
    'queue': queue, 'host': host, 'source_files': evidence,
    'bounded_console': {'path': str(RUN / 'console.log'), 'start_byte': start,
                        'end_byte': end, 'returned_metric_rows': returned},
    'rows': rows,
    'summary': {'games': len(rows) * 8, 'wins': sum(r['wins'] for r in rows),
                'last8_wins': sum(r['wins'] for r in rows[-8:]),
                'last8_games': len(rows[-8:]) * 8},
    'limits': 'Provisional training observations, not held-out evaluation or full final acceptance. '
              'Only complete natural eight-game batches up to latest returned PPO; no padding. '
              'Retains r1 steps1..2; r1 historical host verifier failure remains. '
              'No checkpoints or full console read; no remote writes.'}
print(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False))
