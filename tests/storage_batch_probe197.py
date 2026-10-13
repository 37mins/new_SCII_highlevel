"""Explicit new-root Linux CPU churn probe: four accounts, one pause each tick."""
import json
from pathlib import Path
import sys
import time

sys.path[:0]=[str(Path(__file__).resolve().parent),str(Path(__file__).resolve().parents[1]/'experiments/records/20260921-sc2-policy-credit-v1')]
from host_supervision_probe197 import create_args,inventory
import acceptance197 as a
import host_stage197 as h
import storage_batch197 as b


def main():
    if not sys.platform.startswith('linux'):raise RuntimeError('Linux host required')
    root=Path(sys.argv[1]).resolve();root.mkdir()
    deadline=time.time()+120;accounts=[]
    for n in range(4):
        receipt=root/str(n);receipt.mkdir()
        accounts.append(dict(roots=[root],receipt_root=receipt,limit=1024**3,deadline=deadline))
    h.sample=b.sample
    script=('set -e; i=0; while [ "$i" -lt 16 ]; do '
        'dd if=/dev/zero of=/fixture/live.tmp bs=1M count=8 status=none; '
        'mv /fixture/live.tmp /fixture/live.bin; i=$((i+1)); sleep 0.1; done; '
        'printf done > /fixture/done')
    state=h.run_stages(['churn'],lambda _:create_args(root,'batch',script),
        lambda _:None,accounts,root,root/'control',root,deadline,admit=lambda _:None,interval=.15)
    guardian=a.read(root/'control/churn-guardian.json')
    actions=[x['op'] for x in guardian['events']]
    pauses=actions.count('pause')
    assert pauses>=2 and actions.count('resume')==pauses
    assert all(actions[i+1]=='resume' for i,op in enumerate(actions) if op=='pause')
    assert state['phase']=='completed' and (root/'done').read_text()=='done'
    for item in accounts:
        receipt=a.read(item['receipt_root']/'storage-state.json')
        assert receipt['batch_accounts']==4 and receipt['sampling_version']=='single-pause-batch-v1'
        assert receipt['returncode']==0 and receipt['stderr']['characters']==0
    proof=dict(passed=True,checked_at=time.time(),runtime_sha=a.cmd(['git','-C',a.SOURCE,'rev-parse','HEAD']),
        stage_state=state,pause_count=pauses,account_count=4,container=inventory(guardian['container_id'],root),
        no_gpu=True,no_games=True,no_model=True,limit_bytes=1024**3)
    a.atomic_save(root/'result.json',proof)
    print(json.dumps(proof))


if __name__=='__main__':main()
