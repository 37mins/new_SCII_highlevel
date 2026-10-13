"""Opt-in SC2 validity credit, independent of the centered game-return baseline.

This changes the training objective. It is not a reward/metric relabeling, nor a
claim that valid plans caused the executor's eventual victory.
"""
import math


def validate_config(config):
    cfg = config.algorithm.get('sc2_policy_credit', {})
    if not cfg.get('enabled', False):
        return
    penalty = cfg.get('invalid_advantage_penalty', 0.1)
    minimum = cfg.get('min_valid_ratio', 0.5)
    if not math.isfinite(penalty) or penalty <= 0:
        raise ValueError('SC2 invalid advantage penalty must be finite and positive')
    if not math.isfinite(minimum) or not 0 < minimum <= 1:
        raise ValueError('SC2 minimum valid ratio must be in (0, 1]')
    if (config.env.env_name != 'SC2' or config.algorithm.adv_estimator != 'gigpo'
            or config.algorithm.use_kl_in_reward or config.algorithm.use_pf_ppo
            or config.reward_model.enable or config.reward_model.reward_manager != 'episode'
            or config.algorithm.filter_groups.enable
            or config.actor_rollout_ref.rollout.multi_turn.enable
            or config.trainer.get('sc2_signal_max_batches', 0)
            or config.trainer.get('sc2_empty_policy_max_consecutive', 0)):
        raise ValueError('SC2 validity credit requires plain SC2 GiGPO/episode reward without nested sampling or reward transforms')
    if config.env.rollout.n < 2 or config.actor_rollout_ref.rollout.n != 1:
        raise ValueError('SC2 validity credit requires at least two same-seed environments per group')
    runtime_env = config.get('ray_init', {}).get('runtime_env', {}).get('env_vars', {})
    if str(runtime_env.get('SC2_ORIGINAL_GAME_SEEDS', '')).strip("'\"") != '0':
        raise ValueError('SC2 validity credit requires explicit SC2_ORIGINAL_GAME_SEEDS=0 in worker configuration')
    mode = cfg.get('seed_group_mode', 'same')
    protocol = str(runtime_env.get('SC2_TRAIN_SEED_PROTOCOL', 'native')).strip("'\"")
    allowed = {'same': ('native', 'same_uniform101'),
               'mixed_seed_ablation': ('independent_uniform101',)}
    if mode not in allowed or protocol not in allowed[mode]:
        raise ValueError('SC2 seed-group mode and actual reset protocol must agree explicitly')
    # Default remains fresh-only. The separately approved same-seed extension
    # requires immutable accepted-prefix evidence, never collapsed L7 weights.
    if not config.trainer.val_only and config.trainer.resume_mode != 'disable':
        if not config.trainer.get('sc2_policy_credit_resume_contract'):
            raise ValueError('SC2 validity credit training requires a fresh run; resume is not validated')
        from agent_system.sc2_policy_resume import validate_resume
        validate_resume(config)


def check_same_seed_groups(seeds, group_ids):
    check_seed_groups(seeds, group_ids, 'same')


def check_seed_groups(seeds, group_ids, mode='same'):
    if mode not in ('same', 'mixed_seed_ablation'):
        raise ValueError('Unknown SC2 policy-credit seed-group mode')
    if seeds is None or len(seeds) != len(group_ids) or not len(seeds):
        raise ValueError('Missing actual SC2 reset seed evidence')
    grouped = {}
    for seed, group in zip(seeds, group_ids):
        grouped.setdefault(str(group), []).append(int(seed))
    for group, values in grouped.items():
        if len(values) < 2 or (mode == 'same' and len(set(values)) != 1):
            raise ValueError(f'SC2 policy-credit group {group} must share one actual game seed')
        if mode == 'mixed_seed_ablation' and any(seed < 0 or seed > 100 for seed in values):
            raise ValueError('Mixed-seed ablation requires actual seeds in [0, 100]')


def inspect_batch(data, minimum):
    """Before balancing/padding, measure real consumed answers, never fill missing labels."""
    import numpy as np

    fields = data.non_tensor_batch
    required = ('is_action_valid', 'policy_action_applied', 'active_masks')
    values = {}
    for key in required:
        if key not in fields:
            raise ValueError(f'SC2 policy credit missing {key}')
        rows = np.asarray(fields[key]).reshape(-1)
        if len(rows) != len(data) or not np.isin(rows, [False, True]).all():
            raise ValueError(f'SC2 policy credit invalid {key} labels')
        values[key] = rows.astype(bool)
    if not len(data) or not values['policy_action_applied'].all() or not values['active_masks'].all():
        raise ValueError('SC2 policy credit accepts only nonempty consumed/active policy rows')
    if 'is_tool_query' in fields and np.asarray(fields['is_tool_query']).any():
        raise ValueError('SC2 policy credit does not support tool-query credit')
    valid = int(values['is_action_valid'].sum())
    ratio = valid / len(data)
    return dict(real_answers=len(data), valid_answers=valid, valid_ratio=ratio,
                min_valid_ratio=minimum, decision='accept' if ratio >= minimum else 'stop',
                reason='validity_below_floor' if ratio < minimum else 'validity_floor_passed')


def apply_credit(data, penalty):
    """After *all* advantage centering, disallow positive credit on invalid answers.

    Keep existing negative advantages and subtract a fixed term. Do not modify
    response tokens, response masks, rewards, seeds, or the valid rows.
    """
    import numpy as np
    import torch

    advantages = data.batch['advantages']
    mask = data.batch['response_mask'].bool()
    rows = np.asarray(data.non_tensor_batch['is_action_valid']).reshape(-1)
    if len(rows) != advantages.shape[0] or not np.isin(rows, [False, True]).all():
        raise ValueError('SC2 policy credit invalid action labels')
    if not math.isfinite(penalty) or penalty <= 0:
        raise ValueError('SC2 invalid advantage penalty must be finite and positive')
    if mask.shape != advantages.shape or not torch.isfinite(advantages).all():
        raise ValueError('SC2 policy credit requires finite aligned advantages')
    invalid = torch.as_tensor(~rows.astype(bool), device=advantages.device)[:, None] & mask
    positive = int(((advantages > 0) & invalid).sum().item())
    corrected = torch.where(invalid, advantages.clamp(max=0) - penalty, advantages)
    # GiGPO has no value critic; returns and advantages have the same meaning.
    data.batch['advantages'] = corrected
    data.batch['returns'] = corrected.clone()
    return {'policy_credit/invalid_positive_tokens_removed': positive,
            'policy_credit/invalid_tokens': int(invalid.sum().item()),
            'policy_credit/invalid_advantage_max': float(corrected[invalid].max().item()) if invalid.any() else 0.0}
