"""Read-only curve projection for failed SpB L8 random r2; SSH stdin safe.

Reuses the September30 forensic receipt's hashes to bind small ledgers to all96
previously verified returned PPO rows. Does not rescan console or load checkpoints.
This projection never manufactures missing long result/.done/acceptance files.
"""
from datetime import datetime, timezone, timedelta
import hashlib
import json
from pathlib import Path
import random

ROOT = Path('/var/jfsCache/sc2-spb-l8random96-197-20260929-r2')
SHA = '12f3600ca8e6e8edabc460de70860baeef2b5146'
# Authoritative earlier audit: spb-l8random-r2-recovery-audit-20260930.json.
PROOF = {
    'train2': {
        'manifest.json': 'f48875f1ca48ea489547f717ddebaea7997a691a24834f6221b5c981e6281d3a',
        'training_seeds.jsonl': 'e6fd6d694811367de8b1023e20ba103d0cfbaab581ac1100ae78d4398007676f',
        'episode_outcomes.jsonl': '1048a751d4fac3f6c35286ec25391ab9a0fad4bc1f777492464e590a291b857f',
        'checkpoints/sc2_policy_credit_audit.jsonl': 'a3cd40a1f0a589645154768c477efa9cb3cd328f1cc228a8ea8fc19312016039'},
    'train96': {
        'manifest.json': 'fe7c0d971d2b944152f7797f3e9b5893556a4594b39dca9c823bde1ec6cfdc18',
        'training_seeds.jsonl': '25ec2090b83e1ce562139e88572d61fbda7b7c3907db96941ad3648a3ad9fd3f',
        'episode_outcomes.jsonl': 'fece2d25723234a79619be0748aedb8de49f253266d05e9ab08ae72b034b4fbd',
        'checkpoints/sc2_policy_credit_audit.jsonl': '9687077ae42f1fa181ef61c05a2fc64d0bea8206a686846522feaa1b7f3d1a92'}}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def batch_rows(outcomes, first, last):
    require(len(outcomes) == (last-first+1)*8, 'Incorrect number of outcomes')
    rows = []
    for step in range(first, last+1):
        batch = [o for o in outcomes if o['reset_index'] == step-1]
        require(sorted(o['env_index'] for o in batch) == list(range(8)), 'Missing/duplicate environment')
        require(all(o['terminated'] is True and o['truncated'] is False and
                    o['game_result'] in ('Victory', 'Defeat', 'Tie') for o in batch), 'Not a natural outcome')
        rows.append(dict(step=step, games=8, wins=sum(o['game_result']=='Victory' for o in batch)))
    return rows


def collect():
    evidence = []
    def read(path, expected=None):
        require(path.is_file() and not path.is_symlink(), 'Not a regular receipt')
        with path.open('rb') as f:
            raw = f.read(1024**2+1)
        require(0 < len(raw) <= 1024**2, 'Receipt exceeds 1MiB')
        digest = hashlib.sha256(raw).hexdigest()
        require(expected is None or digest == expected, 'Earlier forensic hash mismatch: '+str(path))
        evidence.append(dict(path=str(path), bytes=len(raw), sha256=digest))
        if path.suffix == '.jsonl':
            require(raw.endswith(b'\n'), 'Partial ledger')
            return [json.loads(line) for line in raw.splitlines()]
        return json.loads(raw)
    queue = read(ROOT/'queue-state.json')
    host = read(ROOT/'spb-random/long/host-supervision/state.json')
    require(queue['phase'] == host['phase'] == 'failed', 'Expected retained failed run')
    rng = random.Random(0)
    expected_seeds = [[rng.randint(0,100) for _ in range(8)] for _ in range(96)]
    rows, segments, answers = [], [], 0
    for part, stage, first, last in [('short','train2',1,2), ('long','train96',3,96)]:
        owner = ROOT/'spb-random'/part
        run = owner/'runs'/stage
        receipts = {n:read(run/n,digest) for n,digest in PROOF[stage].items()}
        m = receipts['manifest.json']
        require(m['source_commit']==SHA and not m['dirty'] and m['world_size']==8 and
                m['metrics_precision']=='binary64-v1', 'Manifest mismatch')
        batches = batch_rows(receipts['episode_outcomes.jsonl'],first,last)
        seeds = receipts['training_seeds.jsonl']
        require(len(seeds)==last-first+1 and all(s['reset_index']==i and s['base_seed']==0 and
                s['seed_protocol']=='independent_uniform101' and s['seeds']==expected_seeds[i]
                for i,s in enumerate(seeds,first-1)), 'Seed protocol mismatch')
        audits = receipts['checkpoints/sc2_policy_credit_audit.jsonl']
        require([a['pending_global_step'] for a in audits]==list(range(first,last+1)), 'Audit interval mismatch')
        require(all(a['decision']=='accept' and a['real_answers']==a['valid_answers']>0 for a in audits), 'Invalid credit audit')
        if stage == 'train2':
            result = read(run/'result.json')
            require(result==read(run/'.done')==read(owner/'acceptance-train2.json')['result'] and
                    result['status']=='completed' and result['process_exit_code']==0, 'Short terminal mismatch')
            require(result['episode_outcomes']['wins']==sum(b['wins'] for b in batches), 'Short wins mismatch')
        else:
            require(not any((run/n).exists() for n in ('result.json','.done','metrics.json')), 'Long terminal changed')
        answers += sum(a['valid_answers'] for a in audits)
        rows.extend(batches)
        segments.append(dict(stage=stage, first=first, last=last, games=8*len(batches),
                             wins=sum(b['wins'] for b in batches), strict_stage_accepted=stage=='train2'))
    require([r['step'] for r in rows]==list(range(1,97)), 'Step gap')
    require(sum(r['wins'] for r in rows)==503 and answers==2758, 'Earlier forensic aggregate mismatch')
    return dict(schema='spb-l8random-r2-training-curve-v1',
        checked_at_beijing=datetime.now(timezone(timedelta(hours=8))).isoformat(),
        node='sc2-a100-197', run_id=ROOT.name, root=str(ROOT), runtime_sha=SHA,
        strict_training_accepted=False, training_queue_phase=queue['phase'],
        prior_returned_ppo_audit='spb-l8random-r2-recovery-audit-20260930.json',
        rows=rows, segments=segments,
        training_summary=dict(returned_ppo_updates=96, games=768, wins=503,
            last8_wins=sum(r['wins'] for r in rows[-8:]), last8_games=64,
            legal_audited_answers=answers, audits=96), source_files=evidence,
        limitations=['All96 actual returned PPO updates were verified by the cited earlier forensic audit.',
            'This collection rechecks exact small-ledger hashes, natural outcomes, seed protocol and audits only.',
            'Old long training remains failed/exit137; no final result/done/metrics, not strict accepted training.',
            'Training batches have changing random scenes; rising training win rate is not fixed-seed learning evidence.',
            'No evaluation outcomes, failed-r1 games, checkpoints or console payloads included.'])


if __name__ == '__main__':
    print(json.dumps(collect(),ensure_ascii=False,allow_nan=False))
