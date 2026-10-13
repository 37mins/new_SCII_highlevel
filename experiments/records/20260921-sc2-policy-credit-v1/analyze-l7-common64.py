"""Reproduce preregistered paired win inference from compact accepted receipts.

Usage: python analyze-l7-common64.py [receipt.json]
Prints JSON only; does not modify runs or write output. Requires NumPy.
"""
import json
import math
from pathlib import Path
import sys

import numpy as np


def exact_p(improved, regressed):
    n = improved + regressed
    return min(1.0, 2 * sum(math.comb(n, k) for k in range(min(improved, regressed) + 1)) / 2**n) if n else 1.0


def analyze(data):
    assert len(data['seeds']) == len(set(data['seeds'])) == 64
    assert all(data['checks'][k] for k in (
        'all_48_stages_passed', 'all_48_exact_containers_exited0',
        'within_model_all_8_ranks_rng_paired_each_batch',
        'declared64_seeds_all_six_arms', 'all384_natural_games_zero_updates',
        'all_consumed_answers_valid'))
    wins = {}
    for name, arm in data['arms'].items():
        assert arm['games'] == len(arm['outcomes']) == 64
        assert arm['stage_count'] == 8 and arm['updates'] == 0
        assert arm['valid_consumed'] == arm['consumed'] > 0
        assert set(arm['outcomes']) <= {'Victory', 'Defeat', 'Tie'}
        wins[name] = np.array([int(x == 'Victory') for x in arm['outcomes']])
        assert int(wins[name].sum()) == arm['wins']
    # The identical paired index resamples are reused across comparisons.
    indices = np.random.default_rng(20260924).integers(0, 64, size=(10000, 64))
    comparisons = []
    def compare(trained, baseline, family):
        difference = wins[trained] - wins[baseline]
        improved = int((difference == 1).sum())
        regressed = int((difference == -1).sum())
        ci = np.quantile(difference[indices].mean(axis=1), [.025, .975], method='linear')
        comparisons.append(dict(trained=trained, baseline=baseline, family=family,
            trained_wins=int(wins[trained].sum()), baseline_wins=int(wins[baseline].sum()),
            n_pairs=64, improved=improved, regressed=regressed,
            both_win=int(((wins[trained] == 1) & (wins[baseline] == 1)).sum()),
            both_nonwin=int(((wins[trained] == 0) & (wins[baseline] == 0)).sum()),
            difference=float(difference.mean()), bootstrap95=ci.tolist(),
            exact_two_sided_p=exact_p(improved, regressed)))
    compare('qwen-same', 'qwen-original', 'original_qwen128_primary')
    compare('spb-same', 'spb-original', 'added_three_primary')
    compare('spb-random', 'spb-original', 'added_three_primary')
    compare('qwen-random', 'qwen-original', 'added_three_primary')
    compare('qwen-same', 'qwen-random', 'exploratory_unadjusted')
    compare('spb-same', 'spb-random', 'exploratory_unadjusted')
    family = sorted((c for c in comparisons if c['family'] == 'added_three_primary'), key=lambda c: c['exact_two_sided_p'])
    previous = 0.0
    for index, comparison in enumerate(family):
        previous = min(1.0, max(previous, (len(family) - index) * comparison['exact_two_sided_p']))
        comparison['holm_adjusted_p'] = previous
        comparison['reject_at_family_alpha_005'] = previous < .05
    return dict(method=dict(test='exact two-sided paired McNemar/binomial',
        bootstrap='paired percentile; NumPy default_rng PCG64; linear quantiles',
        resamples=10000, rng_seed=20260924, numpy_version=np.__version__,
        primary_multiplicity='Holm for three added comparisons only; Qwen-same retains separate preregistration',
        caveat='Sparse one-direction discordance makes percentile bootstrap anti-conservative near boundary. It is not an exact-test inversion; use preregistered exact test for rejection, not whether bootstrap interval excludes zero.'),
        comparisons=comparisons)


if __name__ == '__main__':
    assert exact_p(4, 0) == .125 and exact_p(0, 0) == 1 and exact_p(8, 9) == 1
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).with_name('l7-matrix256-complete-20260925.json')
    print(json.dumps(analyze(json.loads(path.read_text())), indent=2))
