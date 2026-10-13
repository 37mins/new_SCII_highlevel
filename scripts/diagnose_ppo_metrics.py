#!/usr/bin/env python3
"""Read small metric/result receipts; never rewrite, accept, launch or retry a run."""
import argparse
import hashlib
import json
import math
from pathlib import Path

from run_record import METRIC_PRECISION


def diagnose(metrics, precision):
    bad_gradient, bad_credit, missing = [], [], []
    for index, row in enumerate(metrics):
        step = row.get('step', index + 1)
        for key in ('actor/grad_norm', 'policy_credit/invalid_advantage_max'):
            if key not in row:
                missing.append({'step': step, 'key': key})
        gradient = row.get('actor/grad_norm')
        credit = row.get('policy_credit/invalid_advantage_max')
        numeric = lambda v: isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)
        if not numeric(gradient) or gradient <= 0:
            bad_gradient.append(step)
        if not numeric(credit) or credit > 0:
            bad_credit.append(step)
    return dict(metric_rows=len(metrics), metrics_precision=precision,
                precision_declared=precision == METRIC_PRECISION,
                nonpositive_or_nonfinite_gradient_steps=bad_gradient,
                positive_or_nonfinite_invalid_credit_steps=bad_credit,
                missing_fields=missing, acceptance_granted=False,
                interpretation=('Raw positivity unresolved for rounded legacy zeros; do not backfill or accept.'
                                if precision != METRIC_PRECISION else
                                'Precision receipt present; this diagnostic alone is not full run acceptance.'))


def inspect_run(run):
    receipts = {}
    def read(name):
        path = run / name
        if path.stat().st_size > 1024 * 1024:
            raise ValueError(f'Receipt exceeds 1MiB: {name}')
        data = path.read_bytes()
        receipts[name] = hashlib.sha256(data).hexdigest()
        return json.loads(data)
    metrics = read('metrics.json')
    result = read('result.json')
    manifest = read('manifest.json')
    declared = manifest.get('metrics_precision')
    precision = result.get('metrics_precision', 'legacy-console-unverified')
    if precision == METRIC_PRECISION and declared != precision:
        raise ValueError('Precision result/manifest mismatch')
    report = diagnose(metrics, precision)
    report.update(run=str(run), receipts_sha256=receipts)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run', type=Path)
    print(json.dumps(inspect_run(parser.parse_args().run), indent=2, allow_nan=False))
