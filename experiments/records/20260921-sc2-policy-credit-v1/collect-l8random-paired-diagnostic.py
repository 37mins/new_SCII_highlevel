"""Read only bounded accepted evaluation receipts; never open weights or logs."""
import ast
from datetime import datetime, timedelta, timezone
import hashlib
import itertools
import json
from pathlib import Path
import subprocess

TRAIN = Path('/var/jfsCache/sc2-qwen-l8random96-197-20260928-r3')
EVAL = Path('/var/jfsCache/sc2-qwen-l8random-paired192-197-20260928-r3')
SOURCE = Path('/var/jfsCache/sc2-qwen-l8random96-197-source-20260928-r3/code')
SHA = 'ad81511b270f782420208ac8a6f305a141e8042b'
files = []


def raw(path):
    with path.open('rb') as stream:
        data = stream.read(131073)
    assert 0 < len(data) <= 131072, str(path)
    files.append(dict(path=str(path), bytes=len(data), sha256=hashlib.sha256(data).hexdigest()))
    return data


def read(path):
    return json.loads(raw(path))


plan = ast.parse(raw(SOURCE/'experiments/records/20260921-sc2-policy-credit-v1/qwen_l8random_plan.py'))
constants = {}
for node in plan.body:
    if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
        name = node.targets[0].id
        if name in ('SEEDS', 'SELECTION_SEEDS', 'SEED_SHA256', 'SELECTION_SHA256'):
            constants[name] = ast.literal_eval(node.value)
for key, digest in [('SEEDS','SEED_SHA256'), ('SELECTION_SEEDS','SELECTION_SHA256')]:
    assert hashlib.sha256(json.dumps(constants[key],separators=(',',':')).encode()).hexdigest() == constants[digest]

queue = read(TRAIN/'queue-state.json')
assert queue['phase'] == 'completed' and queue['exit_code'] == 0
groups = {}
containers = []
for group, owner, arms, batches, seeds in [
    ('selection',TRAIN/'selection',('cp2','cp32','cp64','cp96'),4,constants['SELECTION_SEEDS']),
    ('primary',EVAL,('original','same96','random96'),8,constants['SEEDS']),
]:
    state = read(owner/'state.json')
    host = read(owner/'host-supervision/state.json')
    assert state == host and state['phase'] == 'completed' and state['exit_code'] == 0
    assert len(state['completed']) == len(arms)*batches
    result_arms = {}
    reference_rng = {}
    for arm in arms:
        expected_step = int(arm[2:]) if group == 'selection' else 0 if arm == 'original' else 96
        expected_cp = None if arm == 'original' else str(
            Path('/var/jfsCache/sc2-qwen-l8same96-197-20260926-r2/qwen-same/long/runs/train96/checkpoints/global_step_96')
            if arm == 'same96' else TRAIN/'qwen-random'/('short/runs/train2' if expected_step == 2 else 'long/runs/train96')/'checkpoints'/f'global_step_{expected_step}')
        rows, stages = [], []
        for batch in range(batches):
            stage = f'b{batch:02d}-{arm}'
            run = owner/'runs'/stage
            result = read(run/'result.json')
            acceptance = read(owner/f'acceptance-{stage}.json')
            assert result == read(run/'.done') == acceptance['result']
            assert result['status'] == 'completed' and result['process_exit_code'] == result['training_updates'] == 0
            assert result['metrics_finite'] and result['metrics_precision'] == 'binary64-v1'
            m = read(run/'manifest.json')
            assert m['source_commit'] == SHA and not m['dirty'] and m['world_size'] == 8
            load = read(run/'checkpoint_evaluation.json')
            assert load['checkpoint'] == expected_cp and load['loaded_global_step'] == expected_step
            assert load['checkpoint_load_returned'] == bool(expected_step) and load['optimizer_updates'] == 0 and load['val_only']
            assert load['game_seeds'] == acceptance['seeds'] == seeds[batch*8:batch*8+8]
            rng = acceptance['rng']
            assert [r['rank'] for r in rng] == list(range(8))
            if batch not in reference_rng:
                reference_rng[batch] = rng
            assert rng == reference_rng[batch]
            assert all(x['cpu_rng_sha256'] and x['cuda_rng_sha256'] for x in rng)
            outcomes = sorted(result['episode_outcomes']['outcomes'],key=lambda x:x['env_index'])
            assert [o['env_index'] for o in outcomes] == list(range(8))
            assert all(o['terminated'] and not o['truncated'] for o in outcomes)
            assert result['episode_outcomes']['natural_games'] == 8 and not result['episode_outcomes']['truncated']
            evidence = acceptance['evidence']
            assert evidence['consumed_answers'] == evidence['valid_consumed_answers'] > 0
            guardian = read(owner/f'host-supervision/{stage}-guardian.json')
            assert guardian['phase'] == 'completed' and guardian['owner_root'] == str(owner)
            assert guardian['final_state']['ExitCode'] == 0 and guardian['deadline'] == host['deadline']
            containers.append((guardian['container_id'],str(owner)))
            rows.extend(dict(seed=seeds[batch*8+i],outcome=o['game_result'],decisions=o['policy_decision_count']) for i,o in enumerate(outcomes))
            stages.append(dict(stage=stage,checkpoint=expected_cp,loaded_step=expected_step,load_returned=bool(expected_step),
                consumed=evidence['consumed_answers'],test_score=result['metrics']['val/text/test_score'],container_id=guardian['container_id']))
        result_arms[arm] = dict(wins=sum(r['outcome']=='Victory' for r in rows),games=len(rows),
            consumed=sum(s['consumed'] for s in stages),outcomes=rows,stages=stages)
    groups[group] = dict(state=state,seeds=seeds,all_seed_rng_paired=True,arms=result_arms)

actual = json.loads(subprocess.check_output(['docker','inspect',*[c for c,_ in containers]],text=True))
for info,(cid,owner) in zip(actual,containers):
    assert info['Id'] == cid and info['Config']['Labels']['sc2.acceptance.root'] == owner
    assert info['State']['Status'] == 'exited' and info['State']['ExitCode'] == 0
    assert not info['State']['OOMKilled'] and not info['State']['Paused']
comparisons = []
for first,second in itertools.combinations(groups['selection']['arms'],2):
    a,b = (groups['selection']['arms'][k]['outcomes'] for k in (first,second))
    comparisons.append(dict(first=first,second=second,
        win_discordances=sum((x['outcome']=='Victory')!=(y['outcome']=='Victory') for x,y in zip(a,b)),
        outcome_discordances=sum(x['outcome']!=y['outcome'] for x,y in zip(a,b)),
        decision_count_differences=sum(x['decisions']!=y['decisions'] for x,y in zip(a,b))))
print(json.dumps(dict(checked_at=datetime.now(timezone(timedelta(hours=8))).isoformat(),runtime_sha=SHA,
    queue=queue,groups=groups,selection_pairwise=comparisons,exact_containers_exited0=len(containers),source_files=files,
    scope='Read-only bounded receipts; no weights, console, repair, pruning or new evaluation.',
    caveat='Distinct loaded checkpoint paths/steps and completed PPO do not independently quantify actual parameter deltas or prove meaningful learning.'),ensure_ascii=False,allow_nan=False))
