"""Explicitly approved fresh short acceptance of the CPU-verified EOS/PAD fix."""
import argparse
import json
from pathlib import Path
import acceptance197 as engine

engine.ROOT = Path('/var/jfsCache/sc2-policy-credit197-20260921-r3')
engine.CONTAINER = 'sc2-policy-credit197-20260921-r3'
engine.RUNTIME_SHA = 'ce8b938341cd5b881b4dea8446ad570ed7509f78'
engine.DOCKER_SCRIPT = Path(__file__).resolve()
# Retain the prior queue expiry. This separately approved run has one new
# 7200-second clock from first GPU dispatch, never reset between stages.


def prepare():
    engine.prepare()
    cfg = engine.read(engine.ROOT / 'deployment.json')
    cfg.update(run_prefix='policy-credit197-r3',
               authorization='User explicitly approved a new 32-game / two-hour / sixteen-GPU-hour '
                             'GPU acceptance after the EOS/PAD CPU repair; no automatic retries, '
                             'Qwen successor or long training.',
               prior_failed_root='/var/jfsCache/sc2-policy-credit197-20260921-r2',
               successors_authorized=False)
    engine.save(engine.ROOT / 'deployment.json', cfg)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['prepare', 'cpu', 'cpu-command', 'queue', 'execute'])
    mode = parser.parse_args().mode
    if mode == 'cpu-command':
        print(json.dumps(engine.docker('cpu')))
    elif mode == 'prepare':
        prepare()
    else:
        getattr(engine, mode)()
