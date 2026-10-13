"""Read-only node197 snapshot: small receipts + at most 8 MiB of console tail."""
import collections
import datetime as dt
import hashlib
import json
from pathlib import Path
import random
import re
import subprocess as sp
import sys

ROOT = Path('/var/jfsCache/sc2-qwen-l7same96-197-20260922-r1')
PARENT = Path('/var/jfsCache/sc2-qwen-seeds197-20260922-r4/l7-same')
SHA = '279d5496464de29e14c64924ccb829147351efbd'


def remote():
    hashes = {}
    def small(path, optional=False):
        if optional and not path.exists():
            return None
        with path.open('rb') as f:
            data = f.read(1024 * 1024 + 1)
        if len(data) > 1024 * 1024:
            raise ValueError('Not a small receipt: ' + str(path))
        hashes[str(path)] = hashlib.sha256(data).hexdigest()
        return data.decode()
    def js(path, optional=False):
        text = small(path, optional)
        return None if text is None else json.loads(text)
    def jl(path):
        return [json.loads(line) for line in small(path).splitlines() if line.strip()]
    manifest = js(ROOT/'runs/train96/manifest.json')
    assert manifest['source_commit'] == SHA and not manifest['dirty']
    assert manifest['world_size'] == 8 and manifest['start_step'] == 2
    resume = js(ROOT/'runs/train96/checkpoints/resume_state.json')
    assert resume['model_optimizer_dataloader_load_returned'] and resume['global_step'] == 2
    assert resume['from_checkpoint'] == str(PARENT/'runs/train2/checkpoints/global_step_2')
    pmanifest = js(PARENT/'runs/train2/manifest.json')
    assert pmanifest['source_commit'] == '2f95c9fd505bd4529070ff4988c5c9efcb111b53'
    assert js(PARENT/'runs/train2/result.json') == js(PARENT/'runs/train2/.done')
    with (ROOT/'runs/train96/console.log').open('rb') as f:
        size = f.seek(0, 2)
        start = max(0, size - 8 * 1024 * 1024)
        f.seek(start)
        raw = f.read(8 * 1024 * 1024)
    clean = re.sub(r'\x1b\[[0-9;]*[A-Za-z]', '', raw.decode(errors='replace'))
    completed = {}
    for line in clean.splitlines():
        match = re.search(r'\bstep:(\d+) - ', line)
        if not match or 'actor/grad_norm:' not in line:
            continue
        metrics = {k: float(v) for k, v in re.findall(r'([A-Za-z_][\w/.-]*):(-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)', line)}
        completed[int(match[1])] = metrics
    assert completed, 'No completed PPO in bounded tail'
    last = max(completed)
    assert sorted(completed) == list(range(3, last + 1)), 'Missing early steps; refuse invented/bridged points'
    parent_metrics = js(PARENT/'runs/train2/metrics.json')
    assert len(parent_metrics) == 2
    all_metrics = {i + 1: m for i, m in enumerate(parent_metrics)} | completed
    seed_rows, outcomes, audits = {}, collections.defaultdict(list), {}
    for run in (PARENT/'runs/train2', ROOT/'runs/train96'):
        for row in jl(run/'training_seeds.jsonl'):
            step = row['reset_index'] + 1
            assert step not in seed_rows
            seed_rows[step] = row
        for row in jl(run/'episode_outcomes.jsonl'):
            outcomes[row['reset_index'] + 1].append(row)
        for row in jl(run/'checkpoints/sc2_policy_credit_audit.jsonl'):
            assert row['pending_global_step'] not in audits
            audits[row['pending_global_step']] = row
    rng = random.Random(0)
    rows = []
    for step in range(1, last + 1):
        seed = rng.randint(0, 100)
        seeds, games, gate, m = seed_rows[step], outcomes[step], audits[step], all_metrics[step]
        assert seeds['seed_protocol'] == 'same_uniform101' and seeds['seeds'] == [seed] * 8
        assert len(games) == 8 and sorted(x['env_index'] for x in games) == list(range(8))
        assert all(x['terminated'] and not x['truncated'] for x in games)
        assert gate['decision'] == 'accept' and gate['real_answers'] > 0
        wins = sum(x['game_result'] == 'Victory' for x in games)
        assert abs(m['episode/success_rate'] - wins / 8) < 0.001
        rows.append(dict(step=step, games=8, wins=wins, win_rate=wins / 8,
            reward=m['episode/reward/mean'], real_answers=gate['real_answers'],
            valid_answers=gate['valid_answers'], valid_action_ratio=gate['valid_answers']/gate['real_answers'],
            seconds=m['timing_s/step'], seed=seed, grad_norm=m['actor/grad_norm'],
            advantage_min=m['critic/advantages/min'], advantage_max=m['critic/advantages/max'],
            entropy=m['actor/entropy_loss'], source='accepted parent' if step <= 2 else 'continuation',
            metrics_precision='raw JSON' if step <= 2 else 'console 3-decimal precision'))
    evaluations = {}
    for stage in ('pre', 'post'):
        run = PARENT/'runs'/stage
        result = js(run/'result.json')
        assert result == js(run/'.done')
        games = jl(run/'episode_outcomes.jsonl')
        assert len(games) == 8 and all(x['terminated'] and not x['truncated'] for x in games)
        evaluations[stage] = dict(wins=sum(x['game_result'] == 'Victory' for x in games), games=8,
            result=result, global_step=0 if stage == 'pre' else 2)
    checkpoints = []
    names = ['data.pt', 'sc2_state.pt'] + [f'actor/{kind}_world_size_8_rank_{rank}.pt'
        for kind in ('model', 'optim', 'extra_state') for rank in range(8)]
    for step in range(8, last + 1, 8):
        checkpoint = ROOT/f'runs/train96/checkpoints/global_step_{step}'
        sizes = {name: (checkpoint/name).stat().st_size for name in names}
        assert all(value > 0 for value in sizes.values())
        checkpoints.append(dict(step=step, required_files=len(sizes), sizes=sizes))
    state = json.loads(sp.check_output(['docker', 'inspect', '--format', '{{json .State}}',
        'sc2-qwen-l7same96-197-20260922-r1'], text=True, timeout=15))
    output = dict(checked_at=dt.datetime.now(dt.timezone(dt.timedelta(hours=8))).isoformat(),
        root=str(ROOT), parent=str(PARENT), runtime_sha=SHA, resume=resume,
        state=js(ROOT/'state.json'), queue=js(ROOT/'queue-state.json'),
        storage=js(ROOT/'storage-state.json'), storage_failure=js(ROOT/'storage-failure.json', True),
        container_state=state, dispatch=js(ROOT/'dispatch.json'), rows=rows,
        checkpoints=checkpoints, evaluations=evaluations,
        train_result=js(ROOT/'runs/train96/result.json', True),
        final_eval_result=js(ROOT/'runs/eval96/result.json', True),
        console_tail=dict(bytes_read=len(raw), file_bytes=size, start=start,
            sha256=hashlib.sha256(raw).hexdigest()), receipt_sha256=hashes)
    output['summary'] = dict(last_step=last, games=8 * len(rows), wins=sum(r['wins'] for r in rows),
        last8_wins=sum(r['wins'] for r in rows[-8:]),
        real_answers=sum(r['real_answers'] for r in rows), valid_answers=sum(r['valid_answers'] for r in rows),
        resumed_games=8*(last-2), resumed_updates=last-2)
    print(json.dumps(output, ensure_ascii=False))


if __name__ == '__main__':
    if '--remote' in sys.argv:
        remote()
    else:
        result = sp.run(['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=8',
            '-o', 'ConnectionAttempts=1', 'sc2-a100-197', 'timeout 40s python3 - --remote'],
            input=Path(__file__).read_text(), text=True, capture_output=True, check=True, timeout=55)
        d = json.loads(result.stdout)
        tag = d['checked_at'][:19].replace('-', '').replace(':', '').replace('T', '-')
        path = Path(__file__).parent / f'qwen-l7same96-{tag}-data.json'
        with path.open('x') as f:
            json.dump(d, f, ensure_ascii=False, indent=2)
        print(json.dumps(dict(path=str(path), checked_at=d['checked_at'], summary=d['summary'],
            container=d['container_state']['Status'], checkpoint_steps=[x['step'] for x in d['checkpoints']],
            rows=[{k:r[k] for k in ('step','wins','reward','valid_action_ratio','seed','grad_norm')}
                  for r in d['rows']]), ensure_ascii=False))
