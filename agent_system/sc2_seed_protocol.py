"""Explicit seed-group ablation; legacy RNG streams remain the default."""
import random


def ablation_seeds(protocol, base_seed, reset_index, env_num, group_n):
    if protocol not in ('same_uniform101', 'independent_uniform101'):
        raise ValueError('Unknown SC2 training seed protocol: ' + protocol)
    if reset_index < 0 or env_num < 1 or group_n < 2:
        raise ValueError('Invalid seed-group dimensions')
    per_reset = env_num if protocol == 'same_uniform101' else env_num * group_n
    rng = random.Random(base_seed)
    draws = [rng.randint(0, 100) for _ in range((reset_index + 1) * per_reset)][-per_reset:]
    return [seed for seed in draws for _ in range(group_n)] if protocol == 'same_uniform101' else draws
