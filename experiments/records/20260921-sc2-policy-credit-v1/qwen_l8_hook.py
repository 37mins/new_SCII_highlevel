"""Install existing zero-update evaluator with declared L8 paired seeds."""
import fcntl
import os
from pathlib import Path
import secrets
import socket
from qwen_l8_plan import stage_spec


def allocate_low_port(ledger=Path('/tmp/l8-rendezvous-ports'),
                      range_path=Path('/proc/sys/net/ipv4/ip_local_port_range')):
    """Allocate a distinct non-ephemeral rendezvous port within one eval queue.

    The kernel's ephemeral range starts above this interval on the frozen host.
    The shared ledger prevents two concurrently initialized worker groups from
    selecting the same port; the bind check still fails closed if it is used.
    """
    lower = int(Path(range_path).read_text().split()[0])
    if lower < 30000:
        raise RuntimeError('Reserved L8 rendezvous interval overlaps the ephemeral port range')
    with Path(ledger).open('a+') as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        stream.seek(0)
        used = {int(line) for line in stream.read().splitlines()}
        start = secrets.randbelow(10000)
        for offset in range(10000):
            port = 20000 + (start + offset) % 10000
            if port in used:
                continue
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
                try:
                    probe.bind(('', port))
                except OSError:
                    continue
            stream.seek(0, os.SEEK_END)
            stream.write(f'{port}\n')
            stream.flush()
            os.fsync(stream.fileno())
            return port
    raise RuntimeError('No free L8 rendezvous port in reserved interval')


def install():
    from feedback_eval import install as evaluate
    spec = stage_spec(os.environ['SC2_L8_STAGE'])
    evaluate(expected_step=spec['expected_step'], game_seeds=spec['seeds'],
             expected_temperature=0.8, answer_description='online Qwen L8; no replay or replacement')
