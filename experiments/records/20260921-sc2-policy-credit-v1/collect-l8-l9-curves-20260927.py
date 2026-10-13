"""Read-only small-ledger collector, executed over SSH stdin on sc2-a100-197.

No checkpoint payloads, console logs, GPU operations, imports of training code,
or remote writes. Outputs only per-step wins/seed and compact provenance.
This is a curve consistency check, NOT a replacement for stage acceptance.
"""
import hashlib
import json
import math
import pathlib
import random
from datetime import datetime, timedelta, timezone

BASE = pathlib.Path('/var/jfsCache')
evidence = []


def small(path, jsonl=False):
    with path.open('rb') as stream:
        data = stream.read(1024 * 1024 + 1)
    assert len(data) <= 1024 * 1024, ('Size limit', str(path))
    evidence.append({'path': str(path), 'bytes': len(data),
                     'sha256': hashlib.sha256(data).hexdigest()})
    if jsonl:
        assert not data or data.endswith(b'\n'), ('Partial JSONL', str(path))
        return [json.loads(line) for line in data.splitlines()]
    return json.loads(data)


rng = random.Random(0)
expected = [rng.randint(0, 100) for _ in range(192)]


def segment(relative, first, last, runtime_sha):
    run = BASE / relative
    metrics = small(run / 'metrics.json')
    result = small(run / 'result.json')
    done = small(run / '.done')
    manifest = small(run / 'manifest.json')
    outcomes = small(run / 'episode_outcomes.jsonl', True)
    seeds = small(run / 'training_seeds.jsonl', True)
    assert result == done
    assert result['status'] == 'completed' and result['process_exit_code'] == 0
    assert result['last_global_step'] == last
    assert result['completed_steps'] == last - first + 1
    assert result['metrics_precision'] == 'binary64-v1'
    assert runtime_sha in json.dumps(manifest), ('Runtime mismatch', relative)
    assert [m['step'] for m in metrics] == list(range(first, last + 1))
    seed_map = {s['reset_index']: s for s in seeds}
    assert len(seed_map) == len(seeds) == len(metrics)
    assert len(outcomes) == len(metrics) * 8
    rows = []
    for m in metrics:
        step = int(m['step'])
        batch = [o for o in outcomes if o['reset_index'] == step - 1]
        assert len(batch) == 8 and sorted(o['env_index'] for o in batch) == list(range(8))
        assert all(o['terminated'] is True and o['truncated'] is False for o in batch)
        seed = seed_map[step - 1]
        assert seed['base_seed'] == 0 and seed['seed_protocol'] == 'same_uniform101'
        assert seed['seeds'] == [expected[step - 1]] * 8
        wins = sum(o['game_result'] == 'Victory' for o in batch)
        assert wins / 8 == m['episode/success_rate']
        for key in ('actor/grad_norm', 'timing_s/update_actor'):
            assert math.isfinite(m[key]) and m[key] > 0
        assert m['episode/valid_action_ratio'] == 1
        assert math.isfinite(m['policy_credit/invalid_advantage_max'])
        assert m['policy_credit/invalid_advantage_max'] <= 0
        rows.append({'step': step, 'wins': wins, 'games': 8, 'seed': expected[step - 1]})
    assert sum(r['wins'] for r in rows) == result['episode_outcomes']['wins']
    return {'run': str(run), 'runtime_sha': runtime_sha,
            'first': first, 'last': last, 'rows': rows,
            'summary': {'wins': sum(r['wins'] for r in rows), 'games': len(rows) * 8},
            'checks': {'result_done_equal': True, 'process_exit_code': 0,
                       'metrics_precision': 'binary64-v1', 'natural_batches': len(rows),
                       'exact_same_seed_rows': len(rows), 'returned_ppo_metrics': len(metrics),
                       'finite_positive_gradient_and_update_time_rows': len(metrics),
                       'valid_action_ratio_one_rows': len(metrics),
                       'invalid_advantage_nonpositive_rows': len(metrics)}}


l8 = [segment('sc2-qwen-l8same96-197-20260926-r1/qwen-same/short/runs/train2', 1, 2,
              'eef0f049bb09b7a51188ae67a6c35436a3bf055f'),
      segment('sc2-qwen-l8same96-197-20260926-r2/qwen-same/long/runs/train96', 3, 96,
              'eef0f049bb09b7a51188ae67a6c35436a3bf055f'),
      segment('sc2-qwen-l8same192-197-20260926-r2/runs/train192', 97, 192,
              'f0e1059aabd28cc5be259908e0955c2509d74a87')]
l9 = [segment('sc2-qwen-l9same96-197-20260927-r1/qwen-same/short/runs/train2', 1, 2,
              '1c6cf60b111570ef13f9817d0b1b16fb774546f5'),
      segment('sc2-qwen-l9same96-197-20260927-r1/qwen-same/long/runs/train96', 3, 96,
              '1c6cf60b111570ef13f9817d0b1b16fb774546f5')]
print(json.dumps({'schema': 'sc2-l8-l9-curves-v1',
                  'checked_at_beijing': datetime.now(timezone(timedelta(hours=8))).isoformat(),
                  'node': 'sc2-a100-197', 'l8': l8, 'l9': l9, 'source_files': evidence,
                  'acceptance': {'l8': 'completed; see existing completion receipts',
                                 'l9': 'failed host acceptance after train96 exit0; no eval96; L10 blocked'},
                  'limitations': ['Curve consistency checks do not replace strict acceptance.',
                                  'Same seed within each eight-game batch; cross-step difficulty changes.',
                                  'Training wins and positive gradients do not demonstrate learning.',
                                  'L8 retained r1 prefix is not a reversal of historical r1 failure.']},
                 ensure_ascii=False, allow_nan=False))
