"""Explicit Linux CPU integration/fault injection; no GPU/SC2/model mounts.

python3 -B tests/host_supervision_probe197.py NEW_EMPTY_ROOT
Only newly allocated fixture containers/processes may be paused or terminated.
All containers, logs and receipts retained; no experiment dispatch CLI.
"""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

REPO=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(REPO/'tests'),str(REPO/'experiments/records/20260921-sc2-policy-credit-v1')]
import acceptance197 as a
import storage_quiescent197 as q
from storage_guardian197 import Guardian
import host_stage197 as h
from storage_quiescence_probe197 import IMAGE,run


def wait_path(path,seconds=12):
    until=time.monotonic()+seconds
    while not path.exists():
        if time.monotonic()>=until:raise TimeoutError('CPU barrier: '+str(path))
        time.sleep(.02)


def terminal_receipt(path,seconds=20):
    until=time.monotonic()+seconds
    while time.monotonic()<until:
        try:
            value=a.read(path)
            if value.get('phase') in ('failed','completed'):return value
        except (FileNotFoundError,json.JSONDecodeError):pass
        time.sleep(.02)
    raise TimeoutError('Guardian terminal receipt incomplete')


def create_args(root,tag,code):
    name='sc2-host-cpu-'+hashlib.sha256((str(root)+tag).encode()).hexdigest()[:12]
    return ['docker','create','--name',name,'--label','sc2.acceptance.root='+str(root),
        '--network','none','--read-only','--cpus','0.5','--memory','64m','--pids-limit','16',
        '--cap-drop','ALL','--security-opt','no-new-privileges',
        '-e','NVIDIA_VISIBLE_DEVICES=void','-e','CUDA_VISIBLE_DEVICES=',
        '--mount',f'type=bind,src={root},dst=/fixture','--entrypoint','/bin/sh',IMAGE,'-c',code]


def inventory(cid,root):
    status=q.inspect_owned(cid,root,time.monotonic()+5)
    details=json.loads(run(['docker','inspect','--format',
        '{"gpu_requests":{{json .HostConfig.DeviceRequests}},"mounts":{{json .Mounts}},'
        '"image":{{json .Image}},"network":{{json .HostConfig.NetworkMode}}}',cid]))
    assert not status['Running'] and not status['Paused']
    assert details['gpu_requests'] is None and details['network']=='none' and details['image']==IMAGE
    assert len(details['mounts'])==1 and details['mounts'][0]['Source']==str(root)
    return dict(container_id=cid,state=status,scope=details)


def sequence(root,fail):
    root.mkdir()
    deadline=time.time()+120
    created=[];verified=[]
    def command(stage):
        created.append(stage)
        exitcode=7 if fail and stage=='train2' else 0
        return create_args(root,stage,f'trap "exit 0" TERM INT; sleep 0.35; printf done > /fixture/{stage}.result; exit {exitcode}')
    def verify(stage):
        assert (root/(stage+'.result')).read_text()=='done'
        verified.append(stage)
    accounts=[dict(roots=[root],receipt_root=root,limit=1024**2,deadline=deadline)]
    error=None
    try:
        h.run_stages(['pre','train2','post'],command,verify,accounts,root,root/'control',root,deadline,admit=lambda _:None,interval=.025)
    except RuntimeError as exc:
        if not fail:raise
        error=str(exc)
    state=a.read(root/'control/state.json')
    assert state['deadline']==deadline
    if fail:
        assert error and state['phase']=='failed' and created==['pre','train2'] and verified==['pre']
        assert not (root/'post.result').exists()
    else:
        assert state['phase']=='completed' and verified==['pre','train2','post']
    receipts=[a.read(p) for p in sorted((root/'control').glob('*-guardian.json'))]
    assert all(r['deadline']==deadline for r in receipts)
    containers=[inventory(r['container_id'],root) for r in receipts]
    if not fail:assert all(x['state']['ExitCode']==0 for x in containers)
    proof=dict(passed=True,scenario='stage-failure' if fail else 'three-stages',created=created,verified=verified,
        state=state,guardians=receipts,containers=containers)
    (root/'result.json').write_text(json.dumps(proof,indent=2)+'\n')
    return proof


def fault_child(root,mode):
    cid=run(create_args(root,'fault','trap "exit 0" TERM INT; while :; do sleep 0.02; done'))
    a.save(root/'identity.json',dict(container_id=cid),lock_root=root)
    try:
        with Guardian(cid,root,time.time()+90,root/'guardian.json',root,lease_seconds=1) as guardian:
            guardian.request('start')
            if mode=='lease-expired':
                (root/'ready').touch()
                time.sleep(2)
                guardian.request('pulse')
            else:
                proof={}
                with guardian.quiesce(time.monotonic()+(10 if mode=='supervisor-killed' else .25),proof):
                    (root/'ready').touch()
                    time.sleep(30 if mode=='supervisor-killed' else 1)
    except BaseException as exc:
        (root/'child-failure.json').write_text(json.dumps(dict(error_type=type(exc).__name__,error=str(exc))))
        return 2
    raise AssertionError('Fault was not detected')


def fault(root,mode):
    root.mkdir()
    with (root/'child.log').open('xb') as log:
        child=subprocess.Popen([sys.executable,'-B',__file__,'--child',str(root),mode],stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        try:
            wait_path(root/'ready')
            cid=a.read(root/'identity.json')['container_id']
            if mode=='supervisor-killed':
                status=q.inspect_owned(cid,root,time.monotonic()+5)
                assert status['Running'] and status['Paused']
                child.kill()  # Only this exact newly-created CPU fixture PID.
            child.wait(timeout=15)
            guardian=terminal_receipt(root/'guardian.json')
            assert guardian['phase']=='failed' and guardian['recovery']['stopped_verified']
            if mode=='supervisor-killed':assert guardian['error_type']=='EOFError'
            item=inventory(cid,root)
            proof=dict(passed=True,scenario=mode,supervisor_returncode=child.returncode,guardian=guardian,container=item)
            (root/'result.json').write_text(json.dumps(proof,indent=2)+'\n')
            return proof
        finally:
            if child.poll() is None:
                child.terminate();child.wait(timeout=15)
            if (root/'identity.json').exists():
                # Test teardown safety only; a passing test must already have
                # the independent guardian's verified-stop receipt above.
                cid=a.read(root/'identity.json')['container_id']
                from storage_guardian197 import recover
                recovered=recover(cid,root,True,time.monotonic()+35)
                assert recovered['stopped_verified']


def main():
    if len(sys.argv)>1 and sys.argv[1]=='--child':
        sys.exit(fault_child(Path(sys.argv[2]),sys.argv[3]))
    if not sys.platform.startswith('linux'):raise RuntimeError('Linux CPU required')
    root=Path(sys.argv[1]).resolve();root.mkdir()  # Fresh root only, no retries.
    cases=[sequence(root/'normal',False),sequence(root/'stage-failure',True)]
    for mode in ('supervisor-killed','pause-expired','lease-expired'):
        cases.append(fault(root/mode,mode))
    assert not any(x in sys.modules for x in ('torch','ray','transformers','pysc2'))
    proof=dict(passed=True,scenarios=cases,heavy_imports=False,checked_at=time.time())
    (root/'result.json').write_text(json.dumps(proof,indent=2)+'\n')
    print(json.dumps(proof))


if __name__=='__main__':main()
