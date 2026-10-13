"""Explicit accepted-prefix continuation; no weights-only or collapsed-run migration."""
import copy
import hashlib
import json
import math
from pathlib import Path


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def normalized_protocol(config):
    """Only relocation, step budget and explicit restore controls may differ.

    The parent stores its actual CPU-resolved launcher config. Data/BO content
    hashes are checked separately by the deployment preflight.
    """
    from omegaconf import OmegaConf
    value = OmegaConf.to_container(config, resolve=True) if OmegaConf.is_config(config) else copy.deepcopy(config)
    for name in ('train_files', 'val_files'):
        value['data'][name] = Path(value['data'][name]).name
    value['env'].pop('prompt_response_log_path', None)
    trainer = value['trainer']
    # Only relocate the exact output-derived SpB view, never arbitrary assets.
    view = str(Path(trainer['default_local_dir']).parent / 'model')
    for section, key in (('actor_rollout_ref', 'path'), ('critic', 'tokenizer_path'),
                         ('reward_model', 'input_tokenizer')):
        model = value.get(section, {}).get('model', {})
        if model.get(key) == view:
            model[key] = '<same-registered-source/per-run-model-view>'
    for name in ('total_epochs', 'total_training_steps', 'save_freq', 'resume_mode', 'resume_from_path',
                 'experiment_name', 'default_local_dir', 'sc2_checkpoint_resume',
                 'sc2_import_legacy_final', 'sc2_policy_credit_resume_contract',
                 'sc2_terminal_handoff_lock_root'):
        trainer.pop(name, None)
    ray = value['ray_init']
    ray.pop('_temp_dir', None)
    ray['runtime_env'].pop('worker_process_setup_hook', None)
    env = ray['runtime_env']['env_vars']
    for name in ('PYTHONPATH', 'TMPDIR', 'RAY_TMPDIR', 'SC2_TRAIN_SEEDS_LOG_PATH',
                 'SC2_RUNTIME_LOG_ROOT', 'SC2_EPISODE_OUTCOME_LOG', 'SC2_ACCEPTANCE_STAGE',
                 'SC2_EVAL_SEEDS_LOG_PATH', 'SC2_COMMAND_TRACE_DIR'):
        env.pop(name, None)
    env['SC2_BO_ADDRESS'] = Path(env['SC2_BO_ADDRESS']).name
    return value


def prefix_files():
    files = ['state.json', 'deployment.json', 'cpu/train2/resolved_config.json']
    for stage in ('pre', 'train2', 'post'):
        files += [f'acceptance-{stage}.json']
        files += [f'runs/{stage}/{name}' for name in ('result.json', '.done', 'manifest.json')]
    files += ['runs/train2/training_seeds.jsonl', 'runs/train2/episode_outcomes.jsonl',
              'runs/train2/metrics.json', 'runs/train2/checkpoints/sc2_policy_credit_audit.jsonl']
    return files


def verify_contract(contract):
    if contract.get('version') == 'accepted-qwen-l8-cp96-to192-v1':
        return verify_completed_l8_cp96(contract)
    if contract.get('version') == 'recovered-qwen-random-native-cp8-v1':
        return verify_recovered_cp8(contract)
    parent = Path(contract['parent'])
    versions = {
        'accepted-same-seed-prefix-v1': ('qwen', 'same_uniform101', 'same', True),
        'accepted-qwen-same-full-state-prefix-v1': ('qwen', 'same_uniform101', 'same', False),
        'accepted-qwen-l8-same-full-state-prefix-v1': ('qwen', 'same_uniform101', 'same', False),
        'accepted-qwen-l8-random-full-state-prefix-v1': ('qwen', 'independent_uniform101', 'mixed_seed_ablation', False),
        'accepted-qwen-l9-same-full-state-prefix-v1': ('qwen', 'same_uniform101', 'same', False),
        'accepted-qwen-l10-same-full-state-prefix-v1': ('qwen', 'same_uniform101', 'same', False),
        'accepted-qwen-random-prefix-v1': ('qwen', 'independent_uniform101', 'mixed_seed_ablation', True),
        'accepted-spb-same-full-state-prefix-v1': ('spb', 'same_uniform101', 'same', False),
        'accepted-spb-random-full-state-prefix-v1': ('spb', 'independent_uniform101', 'mixed_seed_ablation', False),
        'accepted-spb-l8-random-full-state-prefix-v1': ('spb', 'independent_uniform101', 'mixed_seed_ablation', False),
        'accepted-spb-l9-random-full-state-prefix-v1': ('spb', 'independent_uniform101', 'mixed_seed_ablation', False),
    }
    if contract['version'] not in versions:
        raise ValueError('Unsupported accepted-prefix resume contract')
    model, protocol, group, legacy = versions[contract['version']]
    if (contract['start_step'] != 2
            or contract['target_step'] != 96 or contract['driver_rng_unavailable_accepted'] != legacy
            or set(contract['files']) != set(prefix_files())
            or contract['checkpoint'] != str(parent / 'runs/train2/checkpoints/global_step_2')):
        raise ValueError('Unsupported accepted-prefix resume contract')
    for name, digest in contract['files'].items():
        if sha256(parent / name) != digest:
            raise ValueError('Accepted-prefix evidence changed: ' + name)
    read = lambda name: json.loads((parent / name).read_text())
    if read('state.json').get('phase') != 'completed':
        raise ValueError('Accepted prefix is not completed')
    cfg = read('deployment.json')
    difficulty = {
        'accepted-qwen-l8-same-full-state-prefix-v1': 'CheatVision',
        'accepted-qwen-l8-random-full-state-prefix-v1': 'CheatVision',
        'accepted-spb-l8-random-full-state-prefix-v1': 'CheatVision',
        'accepted-spb-l9-random-full-state-prefix-v1': 'CheatMoney',
        'accepted-qwen-l9-same-full-state-prefix-v1': 'CheatMoney',
        'accepted-qwen-l10-same-full-state-prefix-v1': 'CheatInsane',
    }.get(contract['version'], 'VeryHard')
    if (cfg['runtime_sha'] != contract['parent_sha'] or cfg['difficulty'] != difficulty
            or cfg['seed_protocol'] != protocol or cfg['seed_group_mode'] != group
            or cfg['model_kind'] != model):
        raise ValueError('Wrong accepted-prefix model/protocol')
    for stage, games in (('pre', 8), ('train2', 16), ('post', 8)):
        r = read(f'runs/{stage}/result.json')
        m = read(f'runs/{stage}/manifest.json')
        a = read(f'acceptance-{stage}.json')
        if (r != read(f'runs/{stage}/.done') or r != a['result']
                or r['status'] != 'completed' or r['process_exit_code'] != 0
                or not r['metrics_finite'] or r['episode_outcomes']['natural_games'] != games
                or r['episode_outcomes']['truncated'] or m['source_commit'] != contract['parent_sha']
                or m['dirty'] or m['world_size'] != 8
                or a['evidence']['consumed_answers'] <= 0
                or a['evidence']['consumed_answers'] != a['evidence']['valid_consumed_answers']):
            raise ValueError('Incomplete actual prefix acceptance: ' + stage)
        if stage != 'train2' and r['training_updates'] != 0:
            raise ValueError('Prefix evaluation performed training')
        if stage == 'train2':
            if (r['start_step'], r['last_global_step'], r['completed_steps']) != (0, 2, 2) or not r['checkpoint_complete']:
                raise ValueError('Prefix is not its complete fresh step2')
            required = ['data.pt'] + [f'actor/{kind}_world_size_8_rank_{rank}.pt'
                for kind in ('model', 'optim', 'extra_state') for rank in range(8)]
            if not legacy:
                required += ['sc2_state.pt']
            for name in required:
                rel = 'checkpoints/global_step_2/' + name
                size = (parent/'runs/train2'/rel).stat().st_size
                if size <= 0 or size != r['checkpoint_files'][rel]['bytes']:
                    raise ValueError('Incomplete prefix checkpoint: ' + name)
    return read('cpu/train2/resolved_config.json')


def recovered_prefix_files():
    """Small immutable receipts only; never hash model/optimizer shards here."""
    files = ['state.json', 'deployment.json', 'resume-contract.json',
             'cpu/train96/resolved_config.json']
    files += ['runs/train96/' + name for name in (
        'result.json', '.done', 'manifest.json', 'metrics.json',
        'training_seeds.jsonl', 'episode_outcomes.jsonl', 'prompt_response.jsonl',
        'checkpoints/resume_state.json', 'checkpoints/sc2_policy_credit_audit.jsonl',
        'checkpoints/global_step_8/data.pt', 'checkpoints/global_step_8/sc2_state.pt')]
    files += [f'runs/train96/checkpoints/global_step_8/actor/extra_state_world_size_8_rank_{r}.pt'
              for r in range(8)]
    return files


def checkpoint_names():
    return ['data.pt', 'sc2_state.pt'] + [f'actor/{kind}_world_size_8_rank_{r}.pt'
        for kind in ('model', 'optim', 'extra_state') for r in range(8)]


def verify_recovered_cp8(contract):
    """Only the explicitly approved failed-r4 native CP8, not generic retries.

    Validate the closed global3..8 prefix without rewriting failed terminal
    status or treating discarded global9..13 updates as checkpointed state.
    Native tensor/RNG content checks are a separate mandatory CPU/load gate.
    """
    from agent_system.sc2_seed_protocol import ablation_seeds
    parent = Path(contract['parent'])
    cp = parent / 'runs/train96/checkpoints/global_step_8'
    if (contract['start_step'] != 8 or contract['target_step'] != 96
            or contract['driver_rng_unavailable_accepted'] is not False
            or contract['parent_sha'] != '9cb291ea5f50de205c5d88371e08ce229b7d9d04'
            or contract['checkpoint'] != str(cp)
            or set(contract['files']) != set(recovered_prefix_files())
            or set(contract['checkpoint_bytes']) != set(checkpoint_names())):
        raise ValueError('Unsupported native CP8 recovery contract')
    for name, digest in contract['files'].items():
        if (parent/name).stat().st_size > 8*1024**2 or sha256(parent/name) != digest:
            raise ValueError('Native CP8 evidence changed: ' + name)
    for name, size in contract['checkpoint_bytes'].items():
        if size <= 0 or (cp/name).stat().st_size != size:
            raise ValueError('Native CP8 file inventory changed: ' + name)
    read = lambda name: json.loads((parent/name).read_text())
    ancestor = read('resume-contract.json')
    if ancestor['version'] != 'accepted-qwen-random-prefix-v1':
        raise ValueError('CP8 must descend from accepted independent-seed CP2')
    verify_contract(ancestor)
    cfg, result, manifest = (read(name) for name in
        ('deployment.json', 'runs/train96/result.json', 'runs/train96/manifest.json'))
    if (read('state.json')['phase'] != 'failed' or result != read('runs/train96/.done')
            or result['status'] != 'failed' or result['process_exit_code'] != 1
            or (result['start_step'], result['last_global_step'], result['completed_steps']) != (2, 13, 11)
            or result.get('empty_policy_batches') or result['metrics_precision'] != 'binary64-v1'
            or manifest['metrics_precision'] != 'binary64-v1' or manifest['dirty']
            or manifest['world_size'] != 8 or manifest['source_commit'] != contract['parent_sha']
            or cfg['runtime_sha'] != contract['parent_sha'] or cfg['model_kind'] != 'qwen'
            or cfg['difficulty'] != 'VeryHard' or cfg['seed_protocol'] != 'independent_uniform101'
            or cfg['seed_group_mode'] != 'mixed_seed_ablation'):
        raise ValueError('Unexpected failed r4 provenance; no broader recovery waiver')
    rows = lambda name: [json.loads(x) for x in (parent/'runs/train96'/name).read_text().splitlines()]
    seeds = rows('training_seeds.jsonl')
    if len(seeds) != 12 or any(row['reset_index'] != i or row['base_seed'] != 0
            or row['seed_protocol'] != 'independent_uniform101'
            or row['seeds'] != ablation_seeds('independent_uniform101', 0, i, 1, 8)
            for i, row in enumerate(seeds, 2)):
        raise ValueError('Failed-r4 dispatched seed ledger mismatch')
    outcomes = rows('episode_outcomes.jsonl')
    identities = [(x['reset_index'], x['env_index']) for x in outcomes]
    if (len(identities) != 88 or set(identities) != {(r,e) for r in range(2,13) for e in range(8)}
            or any(not x['terminated'] or x['truncated'] for x in outcomes)):
        raise ValueError('Failed-r4 closed-game ledger mismatch')
    metrics, audits = read('runs/train96/metrics.json'), rows('checkpoints/sc2_policy_credit_audit.jsonl')
    if ([x['step'] for x in metrics] != list(range(3,14))
            or [x['pending_global_step'] for x in audits] != list(range(3,14))):
        raise ValueError('Failed-r4 completed PPO identities mismatch')
    for metric, audit in zip(metrics[:6], audits[:6]):
        if (not math.isfinite(metric['actor/grad_norm']) or metric['actor/grad_norm'] <= 0
                or not math.isfinite(metric['policy_credit/invalid_advantage_max'])
                or metric['policy_credit/invalid_advantage_max'] > 0
                or not math.isfinite(metric['timing_s/update_actor']) or metric['timing_s/update_actor'] <= 0
                or audit['decision'] != 'accept' or audit['real_answers'] <= 0
                or audit['real_answers'] != audit['valid_answers']):
            raise ValueError('Native CP8 prefix PPO/credit evidence invalid')
    answers = rows('prompt_response.jsonl')
    consumed = [x for x in answers if x.get('policy_action_applied')]
    if not consumed or any(not all(x[k] for k in ('semantic_action_evaluable','semantic_action_valid','is_action_valid'))
            for x in consumed) or any('<think' in x['llm_response'].lower() or '</think' in x['llm_response'].lower() for x in answers):
        raise ValueError('Failed-r4 consumed-answer contract changed')
    resume = read('runs/train96/checkpoints/resume_state.json')
    if (resume['from_checkpoint'] != ancestor['checkpoint'] or resume['global_step'] != 2
            or resume['next_reset_index'] != 2 or not resume['model_optimizer_dataloader_load_returned']
            or resume['source'] != 'verified legacy ledger; driver RNG unavailable, not bitwise replay'):
        raise ValueError('Native CP8 ancestor actual restoration missing')
    config = read('cpu/train96/resolved_config.json')
    env = config['ray_init']['runtime_env']['env_vars']
    if env.get('SC2_RESET_CONCURRENCY') not in (None, 8, '8') or str(env['SC2_RESET_RETRIES']) != '1':
        raise ValueError('Unexpected parent startup protocol')
    # Explicitly approved operational change only, not a global normalization.
    env['SC2_RESET_CONCURRENCY'] = '1'
    return config


def validate_resume(config):
    t = config.trainer
    if (t.resume_mode != 'resume_path' or not t.get('sc2_checkpoint_resume')
            or t.del_local_ckpt_after_load):
        raise ValueError('Explicit complete-state accepted-prefix continuation required')
    contract = json.loads(Path(t.sc2_policy_credit_resume_contract).read_text())
    if t.total_training_steps != contract['target_step']:
        raise ValueError('Training target differs from accepted-prefix contract')
    if bool(t.get('sc2_import_legacy_final', False)) != contract['driver_rng_unavailable_accepted']:
        raise ValueError('Legacy import permission differs from accepted-prefix contract')
    if t.resume_from_path != contract['checkpoint']:
        raise ValueError('Resume checkpoint is not the accepted prefix')
    parent_config = verify_contract(contract)
    if normalized_protocol(config) != normalized_protocol(parent_config):
        raise ValueError('Accepted-prefix continuation changed the training protocol')


def completed_l8_files():
    """Closed CP96 receipts and small native state; no model/optimizer hashing."""
    names = ['state.json', 'deployment.json', 'resume-contract.json',
             'host-supervision/state.json', 'cpu/train96/resolved_config.json']
    for stage in ('train96', 'eval96'):
        names += [f'acceptance-{stage}.json']
        names += [f'runs/{stage}/{n}' for n in ('result.json', '.done', 'manifest.json')]
    names += ['runs/train96/' + n for n in ('metrics.json', 'training_seeds.jsonl',
        'episode_outcomes.jsonl', 'checkpoints/resume_state.json',
        'checkpoints/sc2_policy_credit_audit.jsonl')]
    names += ['runs/train96/checkpoints/global_step_96/' + n for n in
              ['data.pt', 'sc2_state.pt'] +
              [f'actor/extra_state_world_size_8_rank_{r}.pt' for r in range(8)]]
    return names


def verify_completed_l8_cp96(contract):
    """Opt-in Sep26 budget extension, not a waiver for failed or legacy runs."""
    from agent_system.sc2_seed_protocol import ablation_seeds
    parent = Path(contract['parent'])
    cp = parent / 'runs/train96/checkpoints/global_step_96'
    if (contract['start_step'] != 96 or contract['target_step'] != 192
            or contract['driver_rng_unavailable_accepted'] is not False
            or contract['parent_sha'] != 'eef0f049bb09b7a51188ae67a6c35436a3bf055f'
            or contract['checkpoint'] != str(cp)
            or set(contract['files']) != set(completed_l8_files())
            or set(contract['checkpoint_bytes']) != set(checkpoint_names())):
        raise ValueError('Unsupported completed L8 CP96 extension contract')
    for name, digest in contract['files'].items():
        if not 0 < (parent / name).stat().st_size <= 8 * 1024**2 or sha256(parent / name) != digest:
            raise ValueError('Completed L8 evidence changed: ' + name)
    read = lambda name: json.loads((parent / name).read_text())
    ancestor = read('resume-contract.json')
    if ancestor['version'] != 'accepted-qwen-l8-same-full-state-prefix-v1':
        raise ValueError('Complete native L8 CP2 ancestry required')
    verify_contract(ancestor)
    for name in ('state.json', 'host-supervision/state.json'):
        state = read(name)
        if (state['phase'] != 'completed' or state['exit_code'] != 0
                or state['completed'] != ['train96', 'eval96']):
            raise ValueError('L8 parent is not fully completed')
    cfg = read('deployment.json')
    if (cfg['runtime_sha'] != contract['parent_sha'] or cfg['model_kind'] != 'qwen'
            or cfg['difficulty'] != 'CheatVision' or cfg['seed_protocol'] != 'same_uniform101'
            or cfg['seed_group_mode'] != 'same'):
        raise ValueError('Wrong L8 CP96 model/protocol')
    for stage, games in (('train96', 752), ('eval96', 8)):
        r, m, accepted = (read(n) for n in (f'runs/{stage}/result.json',
            f'runs/{stage}/manifest.json', f'acceptance-{stage}.json'))
        if (r != read(f'runs/{stage}/.done') or r != accepted['result']
                or r['status'] != 'completed' or r['process_exit_code'] != 0
                or not r['metrics_finite'] or r['episode_outcomes']['natural_games'] != games
                or r['episode_outcomes']['truncated'] or m['dirty'] or m['world_size'] != 8
                or m['source_commit'] != contract['parent_sha']
                or r['metrics_precision'] != 'binary64-v1' or m['metrics_precision'] != 'binary64-v1'
                or accepted['evidence']['consumed_answers'] <= 0
                or accepted['evidence']['consumed_answers'] != accepted['evidence']['valid_consumed_answers']):
            raise ValueError('Incomplete L8 CP96 acceptance: ' + stage)
        if stage == 'eval96' and r['training_updates'] != 0:
            raise ValueError('Parent evaluation updated weights')
        if stage == 'train96':
            if (r['start_step'], r['last_global_step'], r['completed_steps']) != (2, 96, 94) or not r['checkpoint_complete']:
                raise ValueError('Expected completed L8 steps3..96')
            for name, size in contract['checkpoint_bytes'].items():
                if (size <= 0 or (cp / name).stat().st_size != size
                        or r['checkpoint_files']['checkpoints/global_step_96/' + name]['bytes'] != size):
                    raise ValueError('Incomplete L8 CP96 inventory: ' + name)
    rows = lambda n: [json.loads(x) for x in (parent / 'runs/train96' / n).read_text().splitlines()]
    metrics = read('runs/train96/metrics.json')
    audits = rows('checkpoints/sc2_policy_credit_audit.jsonl')
    if ([x['step'] for x in metrics] != list(range(3, 97))
            or [x['pending_global_step'] for x in audits] != list(range(3, 97))
            or any(x['decision'] != 'accept' or x['real_answers'] <= 0
                   or x['real_answers'] != x['valid_answers'] for x in audits)
            or any(not math.isfinite(x[k]) or x[k] <= 0 for x in metrics
                   for k in ('actor/grad_norm', 'timing_s/update_actor'))
            or any(not math.isfinite(x['policy_credit/invalid_advantage_max'])
                   or x['policy_credit/invalid_advantage_max'] > 0 for x in metrics)):
        raise ValueError('Parent actual finite PPO evidence required')
    seeds = rows('training_seeds.jsonl')
    if len(seeds) != 94 or any(x['reset_index'] != i or x['base_seed'] != 0
            or x['seed_protocol'] != 'same_uniform101'
            or x['seeds'] != ablation_seeds('same_uniform101', 0, i, 1, 8)
            for i, x in enumerate(seeds, 2)):
        raise ValueError('Parent L8 seed ledger mismatch')
    outcomes = rows('episode_outcomes.jsonl')
    if (len(outcomes) != 752 or {(x['reset_index'], x['env_index']) for x in outcomes}
            != {(r, e) for r in range(2, 96) for e in range(8)}
            or any(not x['terminated'] or x['truncated'] for x in outcomes)):
        raise ValueError('Parent L8 natural-game ledger mismatch')
    resume = read('runs/train96/checkpoints/resume_state.json')
    if (resume['from_checkpoint'] != ancestor['checkpoint'] or resume['global_step'] != 2
            or resume['next_reset_index'] != 2 or resume['source'] != 'checkpoint'
            or not resume['model_optimizer_dataloader_load_returned']):
        raise ValueError('Parent L8 native restoration missing')
    return read('cpu/train96/resolved_config.json')
