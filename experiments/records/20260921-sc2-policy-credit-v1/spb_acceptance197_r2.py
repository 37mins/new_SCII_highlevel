"""User-authorized replacement of unstarted r1; only runtime manifest differs."""
import argparse
import json
from pathlib import Path
import acceptance197 as engine

engine.ROOT = Path('/var/jfsCache/sc2-policy-credit197-20260921-r2')
engine.CONTAINER = 'sc2-policy-credit197-20260921-r2'
engine.RUNTIME_SHA = 'f211c0e94603468992baa514f00aaee5fd7780d6'
engine.DOCKER_SCRIPT = Path(__file__).resolve()
# Original seeds, 7200 seconds, 128GiB and QUEUE_EXPIRES are retained.

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['prepare', 'cpu', 'cpu-command', 'queue', 'execute'])
    mode = parser.parse_args().mode
    if mode == 'cpu-command':
        print(json.dumps(engine.docker('cpu')))
    else:
        getattr(engine, mode)()
