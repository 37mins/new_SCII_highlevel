"""Pure local reproduction of the pre-registered L8 random paired64 analysis.

Uses the algorithm in frozen ad81511:qwen_l8random_plan.py, without importing
the experiment runtime. No remote access or output-file writes.
"""
import json
import math
from pathlib import Path

import numpy as np


def exact_p(gain, loss):
    n = gain + loss
    return min(1., 2 * sum(math.comb(n, k) for k in range(min(gain, loss) + 1)) / 2**n) if n else 1.


def wilson(wins, n):
    z = 1.959963984540054
    p = wins / n
    denominator = 1 + z*z/n
    center = (p + z*z/(2*n)) / denominator
    half = z * math.sqrt(p*(1-p)/n + z*z/(4*n*n)) / denominator
    return [center-half, center+half]


def analyze(data):
    assert data['queue']['phase'] == 'completed' and data['exact_containers_exited0'] == 40
    arms = data['groups']['primary']['arms']
    seeds = data['groups']['primary']['seeds']
    assert len(seeds) == len(set(seeds)) == 64 and data['groups']['primary']['all_seed_rng_paired']
    scores, summaries = {}, {}
    for name, arm in arms.items():
        assert arm['games'] == 64 and [o['seed'] for o in arm['outcomes']] == seeds
        scores[name] = np.array([o['outcome'] == 'Victory' for o in arm['outcomes']], dtype=np.int8)
        assert int(scores[name].sum()) == arm['wins']
        summaries[name] = dict(wins=arm['wins'], games=64, wilson95=wilson(arm['wins'],64),
            ties=sum(o['outcome']=='Tie' for o in arm['outcomes']), valid_consumed_answers=arm['consumed'])
    comparisons = []
    for control, treatment, role in [('same96','random96','registered_primary'),
                                     ('original','random96','secondary_exploratory'),
                                     ('original','same96','secondary_exploratory')]:
        delta = scores[treatment] - scores[control]
        gains, losses = int((delta==1).sum()), int((delta==-1).sum())
        rng = np.random.default_rng(2026092709)
        bootstrap = delta[rng.integers(0,64,size=(100000,64))].mean(axis=1)
        comparisons.append(dict(treatment=treatment, control=control, role=role, gains=gains, losses=losses,
            difference=float(delta.mean()), paired_bootstrap95=np.quantile(bootstrap,[.025,.975],method='linear').tolist(),
            exact_two_sided_mcnemar=exact_p(gains,losses), multiplicity_adjusted=False))
    return dict(arms=summaries,comparisons=comparisons,
        method=dict(analysis_seed=2026092709,resamples=100000,quantile='linear',numpy_version=np.__version__,
            primary='random96 minus same96; original-model comparisons are exploratory',
            caveat='One run per training condition. Sparse percentile-bootstrap intervals are not exact-test inversions; no equivalence claim.'))


if __name__ == '__main__':
    assert exact_p(11,1) == 0.00634765625 and exact_p(2,0) == .5 and exact_p(0,0) == 1
    path = Path(__file__).with_name('qwen-l8random-r3-paired-complete-20260928-1936.json')
    print(json.dumps(analyze(json.loads(path.read_text())),indent=2,allow_nan=False))
