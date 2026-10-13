"""Approved remaining three arms: new bounded attempt, completed l6-same reused."""
from pathlib import Path
import qwen_seed197 as q


def configure():
    q.SUITE = Path('/var/jfsCache/sc2-qwen-seeds197-20260922-r4')
    q.SPB = Path('/var/jfsCache/sc2-policy-credit197-20260921-r4')
    q.SPB_RUNTIME = 'ce8b938341cd5b881b4dea8446ad570ed7509f78'
    q.RUN_PREFIX = 'qwen-seeds197-r4'
    q.CONTAINER_PREFIX = 'sc2-qwen-seeds197-20260922-r4-'
    q.DOCKER_SCRIPT = Path(__file__).resolve()
    q.ARMS = list(q.DEFAULT_ARMS[1:])
    q.REUSED_ARM_ROOT = Path('/var/jfsCache/sc2-qwen-seeds197-20260922-r3/l6-same')
    q.WALL_SECONDS = 6 * 3600
    q.FIRST_DISPATCH_BY = 1790051700  # Sep22 12:35 Beijing, bounded new admission.
    q.LIMIT = 512 * q.engine.GIB  # Retain inclusive old cap; do not add storage budget.
    q.AUTHORIZATION = ('User explicitly approved new remaining l6-random/l7-same/l7-random GPU attempts; '
                       '32 games and <=2h/16GPUh each, total96 games/6PPO/6h48GPUh; '
                       'reuse completed r3 l6-same, no retry/long promotion; old deadlines unchanged')
    q.PRIOR_ROOTS = [Path(path) for path in (
        '/var/jfsCache/sc2-qwen-seeds197-20260921-r1',
        '/var/jfsCache/sc2-qwen-seeds197-source-20260921-r1',
        '/var/jfsCache/sc2-qwen-seeds197-20260921-r2',
        '/var/jfsCache/sc2-qwen-seeds197-source-20260921-r2',
        '/var/jfsCache/sc2-qwen-seeds197-20260922-r3',
        '/var/jfsCache/sc2-qwen-seeds197-source-20260922-r3')]


if __name__ == '__main__':
    configure()
    q.main()
