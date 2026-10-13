"""Read-only small-ledger snapshot; execute via SSH stdin on sc2-a100-197.

No remote writes, model payloads, or console reads. Checks curve consistency and
existing terminal receipts; does not rerun the full frozen acceptance verifier.
"""
import hashlib
import json
import math
from pathlib import Path
import random
import subprocess
from datetime import datetime, timedelta, timezone

ROOT = Path('/var/jfsCache/sc2-qwen-l8random96-197-20260928-r3')
EVAL = Path('/var/jfsCache/sc2-qwen-l8random-paired192-197-20260928-r3')
SHA = 'ad81511b270f782420208ac8a6f305a141e8042b'
evidence = []


def small(path, jsonl=False):
    with path.open('rb') as stream:
        raw = stream.read(1024 * 1024 + 1)
    assert 0 < len(raw) <= 1024 * 1024, ('small evidence required', str(path))
    evidence.append(dict(path=str(path), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest()))
    if jsonl:
        assert raw.endswith(b'\n'), ('partial JSONL append', str(path))
        return [json.loads(line) for line in raw.splitlines()]
    return json.loads(raw)


def terminal(owner, stage):
    run = owner/'runs'/stage
    result, done = small(run/'result.json'), small(run/'.done')
    accepted, manifest = small(owner/f'acceptance-{stage}.json'), small(run/'manifest.json')
    assert result == done == accepted['result']
    assert result['status'] == 'completed' and result['process_exit_code'] == 0
    assert result['metrics_precision'] == 'binary64-v1' and result['metrics_finite']
    assert manifest['source_commit'] == SHA and not manifest['dirty'] and manifest['world_size'] == 8
    outcome = result['episode_outcomes']
    assert not outcome['truncated']
    guardian = small(owner/f'host-supervision/{stage}-guardian.json')
    assert guardian['phase'] == 'completed' and guardian['final_state']['ExitCode'] == 0
    assert guardian['owner_root'] == str(owner)
    info = json.loads(subprocess.check_output(['docker', 'inspect', guardian['container_id']], text=True))[0]
    assert info['Id'] == guardian['container_id']
    assert info['Config']['Labels']['sc2.acceptance.root'] == str(owner)
    assert info['State']['Status'] == 'exited' and info['State']['ExitCode'] == 0
    assert not info['State']['OOMKilled'] and not info['State']['Paused']
    consumed = accepted['evidence']['consumed_answers']
    assert consumed > 0 and consumed == accepted['evidence']['valid_consumed_answers']
    return result, dict(stage=stage, owner=str(owner), container_id=info['Id'],
        container_name=info['Name'], finished_at=info['State']['FinishedAt'],
        result_done_acceptance_equal=True, exit_code=0, guardian_completed=True,
        natural_games=outcome['natural_games'], wins=outcome['wins'],
        consumed_answers=consumed, valid_consumed_answers=consumed,
        zero_updates=result.get('training_updates') == 0)


rng = random.Random(0)
expected = [[rng.randint(0, 100) for _ in range(8)] for _ in range(96)]
rows, segments, diagnostics = [], [], []
for part, stage, first, last in [('short', 'train2', 1, 2), ('long', 'train96', 3, 96)]:
    owner = ROOT/'qwen-random'/part
    run = owner/'runs'/stage
    result, proof = terminal(owner, stage)
    metrics = small(run/'metrics.json')
    outcomes = small(run/'episode_outcomes.jsonl', True)
    seeds = small(run/'training_seeds.jsonl', True)
    audits = small(run/'checkpoints/sc2_policy_credit_audit.jsonl', True)
    assert result['last_global_step'] == last and result['completed_steps'] == last-first+1
    assert [m['step'] for m in metrics] == list(range(first, last+1))
    seed_map = {s['reset_index']: s for s in seeds}
    assert len(seeds) == len(seed_map) == len(metrics) == len(audits)
    assert len(outcomes) == len(metrics)*8
    batch_rows = []
    for m in metrics:
        step = int(m['step'])
        batch = [o for o in outcomes if o['reset_index'] == step-1]
        assert len(batch) == 8 and sorted(o['env_index'] for o in batch) == list(range(8))
        assert all(o['terminated'] is True and o['truncated'] is False for o in batch)
        seed = seed_map[step-1]
        assert seed['base_seed'] == 0 and seed['seed_protocol'] == 'independent_uniform101'
        assert seed['seeds'] == expected[step-1]
        wins = sum(o['game_result'] == 'Victory' for o in batch)
        assert wins/8 == m['episode/success_rate']
        keys = ['actor/grad_norm', 'timing_s/update_actor', 'timing_s/step',
                'episode/valid_action_ratio', 'policy_credit/invalid_advantage_max']
        assert all(math.isfinite(m[k]) for k in keys)
        assert m['actor/grad_norm'] > 0 and m['timing_s/update_actor'] > 0
        assert m['episode/valid_action_ratio'] == 1 and m['policy_credit/invalid_advantage_max'] <= 0
        row = dict(step=step, wins=wins, games=8, seeds=seed['seeds'],
                   **{k: m[k] for k in keys})
        rows.append(row); batch_rows.append(row)
    assert sum(r['wins'] for r in batch_rows) == result['episode_outcomes']['wins']
    proof.update(first=first, last=last, returned_ppo=len(metrics), audits=len(audits),
                 matched_seed_batches=len(seeds))
    segments.append(proof)

for part, stage, step in [('short', 'pre', 0), ('short', 'post', 2), ('long', 'eval96', 96)]:
    result, proof = terminal(ROOT/'qwen-random'/part, stage)
    assert proof['zero_updates'] and proof['natural_games'] == 8
    load = small(ROOT/'qwen-random'/part/'runs'/stage/'checkpoint_evaluation.json')
    assert load['loaded_global_step'] == step and load['optimizer_updates'] == 0
    assert load['checkpoint_load_returned'] == bool(step)
    proof.update(step=step, actual_checkpoint_load_returned=bool(step))
    diagnostics.append(proof)

assert [r['step'] for r in rows] == list(range(1, 97))
selection = small(ROOT/'retention/best.json')
selection_state = small(ROOT/'selection/state.json')
assert selection_state['phase'] == 'completed' and selection_state['exit_code'] == 0
assert len(selection_state['completed']) == 16
assert [x['step'] for x in selection['scored']] == [2, 32, 64, 96]
assert all(x['games'] == 32 for x in selection['scored']) and not selection['test_used']
for x in selection['scored']:
    wins = 0
    for stage, digest in x['receipts'].items():
        path = ROOT/'selection'/f'acceptance-{stage}.json'
        acceptance = small(path)
        assert evidence[-1]['sha256'] == digest
        result = small(ROOT/'selection/runs'/stage/'result.json')
        assert result == acceptance['result'] == small(ROOT/'selection/runs'/stage/'.done')
        assert result['training_updates'] == 0 and result['episode_outcomes']['natural_games'] == 8
        assert not result['episode_outcomes']['truncated']
        wins += result['episode_outcomes']['wins']
    assert wins == x['wins']

primary = small(EVAL/'host-supervision/state.json')
primary_rows = []
for stage in primary['completed']:
    result = small(EVAL/'runs'/stage/'result.json')
    acceptance = small(EVAL/f'acceptance-{stage}.json')
    assert result == small(EVAL/'runs'/stage/'.done') == acceptance['result']
    assert result['status'] == 'completed' and result['process_exit_code'] == 0
    assert result['training_updates'] == 0 and result['episode_outcomes']['natural_games'] == 8
    assert not result['episode_outcomes']['truncated']
    primary_rows.append(dict(stage=stage, batch=int(stage[1:3]), arm=stage[4:],
        wins=result['episode_outcomes']['wins'], games=8))

print(json.dumps(dict(schema='sc2-l8random-r3-curve-v1',
    checked_at_beijing=datetime.now(timezone(timedelta(hours=8))).isoformat(),
    run_id=ROOT.name, node='sc2-a100-197', runtime_sha=SHA, root=str(ROOT),
    rows=rows, segments=segments, diagnostics=diagnostics,
    training_summary=dict(ppo_updates=96, games=768, wins=sum(r['wins'] for r in rows),
        valid_consumed_answers=sum(s['consumed_answers'] for s in segments),
        last8_wins=sum(r['wins'] for r in rows[-8:]), last8_games=64,
        gradient_min=min(r['actor/grad_norm'] for r in rows),
        gradient_max=max(r['actor/grad_norm'] for r in rows),
        actor_update_seconds=sum(r['timing_s/update_actor'] for r in rows)),
    train_state=small(ROOT/'train-state.json'), queue=small(ROOT/'queue-state.json'),
    selection=dict(state=selection_state, best=selection['best']['step'],
        scored=[{k: x[k] for k in ('step','wins','games')} for x in selection['scored']],
        seed_sha256=selection['best']['seed_sha256'], test_used=False),
    retention=small(ROOT/'retention/prune-receipt.json'),
    primary=dict(state=primary, rows=primary_rows, complete=primary['phase']=='completed'),
    source_files=evidence,
    limitations=['Training curves are not fixed-weight held-out evidence.',
        'Validation32 selects best; ties retain earlier step. Test64 is separate.',
        'Primary192 remains incomplete until all24 stages pass; no final treatment claim.',
        'Native checkpoint payloads and full console logs were not read.',
        'CP32 was pruned by the approved queue after validation; old artifacts untouched.']),
    ensure_ascii=False, allow_nan=False))
