"""User-requested Qwen matrix requeue after SpB r4; no failed-run restart."""
from pathlib import Path
import qwen_seed197 as q


def configure():
    q.SUITE = Path('/var/jfsCache/sc2-qwen-seeds197-20260922-r3')
    q.SPB = Path('/var/jfsCache/sc2-policy-credit197-20260921-r4')
    q.SPB_RUNTIME = 'ce8b938341cd5b881b4dea8446ad570ed7509f78'
    q.RUN_PREFIX = 'qwen-seeds197-r3'
    q.CONTAINER_PREFIX = 'sc2-qwen-seeds197-20260922-r3-'
    q.DOCKER_SCRIPT = Path(__file__).resolve()
    q.PRIOR_ROOTS = [Path('/var/jfsCache/sc2-qwen-seeds197-20260921-r1'),
                     Path('/var/jfsCache/sc2-qwen-seeds197-source-20260921-r1'),
                     Path('/var/jfsCache/sc2-qwen-seeds197-20260921-r2'),
                     Path('/var/jfsCache/sc2-qwen-seeds197-source-20260921-r2')]
    # Reuse unused 64GPUh/128games and original admission cutoff. The suite
    # starts its one clock at its first-ever Qwen GPU dispatch, never at enqueue.


if __name__ == '__main__':
    configure()
    q.main()
