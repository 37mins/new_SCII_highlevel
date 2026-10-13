"""Explicit Linux CPU probe only; retains two tiny, stopped owned containers.

Usage: python3 -B tests/storage_quiescence_probe197.py NEW_EMPTY_FIXTURE_ROOT
No GPU requests, model/SC2 mounts, networking, source patching or run dispatch.
"""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from unittest.mock import patch

REPO=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(REPO/'experiments/records/20260921-sc2-policy-credit-v1'))
import acceptance197 as a
import storage_quiescent197 as q

IMAGE='sha256:1a497d5721f89bb2e98c0273c4b1495f8fdc6921d589650d090871c11b8d1649'


def run(args,timeout=10):
    return subprocess.run(list(map(str,args)),check=True,text=True,capture_output=True,
                          timeout=timeout).stdout.strip()


def wait_path(path):
    until=time.monotonic()+4
    while not path.exists():
        if time.monotonic()>=until: raise TimeoutError('CPU fixture barrier timed out: '+str(path))
        time.sleep(.01)


def case(root,library,fixed):
    root.mkdir()
    counted=root/'run';counted.mkdir()
    temporary=counted/'compiler.ptx';temporary.write_bytes(b'cpu fixture\n')
    name='sc2-storage-cpu-'+hashlib.sha256(str(root).encode()).hexdigest()[:12]
    # The independent writer does NOT use the metadata lock, just like the
    # runtime compiler. It only deletes our single tiny fixture file.
    code=('set -eu; printf ready > /fixture/ready; '
          'while [ ! -e /fixture/go ]; do sleep 0.01; done; '
          'rm -- /fixture/run/compiler.ptx; printf deleted > /fixture/deleted; '
          'while [ ! -e /fixture/finish ]; do sleep 0.02; done')
    cid=run(['docker','create','--name',name,'--label',f'sc2.acceptance.root={counted}',
             '--network','none','--read-only','--cpus','0.5','--memory','64m',
             '--pids-limit','16','--cap-drop','ALL','--security-opt','no-new-privileges',
             '-e','NVIDIA_VISIBLE_DEVICES=void','-e','CUDA_VISIBLE_DEVICES=',
             '--mount',f'type=bind,src={root},dst=/fixture',
             '--entrypoint','/bin/sh',IMAGE,'-c',code])
    ready,release=root/'du-ready',root/'du-release'
    evidence=dict(container_id=cid,name=name,fixed=fixed,root=str(root))
    try:
        run(['docker','start',cid]);wait_path(root/'ready')
        env=dict(LD_PRELOAD=str(library),SC2_DU_PAUSE_NAME=temporary.name,
                 SC2_DU_PAUSE_READY=str(ready),SC2_DU_PAUSE_RELEASE=str(release))
        with patch.dict(os.environ,env),ThreadPoolExecutor(1) as pool:
            if fixed:
                future=pool.submit(q.measure_owned_budget,cid,counted,[counted],counted,
                    1024**2,time.time()+120,'CPU time limit','CPU fixture cap',lock_root=counted)
            else:
                future=pool.submit(a.measure_budget,[counted],counted,1024**2,
                    time.time()+120,'CPU time limit','CPU fixture cap',lock_root=counted)
            try:
                wait_path(ready)
                (root/'go').touch()
                if fixed:
                    status=q.inspect_owned(cid,counted,time.monotonic()+2)
                    assert status['Paused'] and status['Running']
                    time.sleep(.05)
                    assert temporary.exists() and not (root/'deleted').exists()
                else:
                    wait_path(root/'deleted')
                    assert not temporary.exists()
            finally:
                release.touch()
            if fixed:
                future.result(timeout=12)
                wait_path(root/'deleted')
                receipt=counted/'storage-state.json'
                proof=json.loads(receipt.read_text())
                assert proof['returncode']==0 and proof['stderr']['tail']==''
                assert proof['quiescence']['paused_verified']
                assert proof['quiescence']['cleanup']=='verified-unpaused'
                assert set(proof['root_bytes'])=={str(counted)}
                assert proof['bytes']>=len(b'cpu fixture\n')
            else:
                try: future.result(timeout=12)
                except RuntimeError as exc: assert 'Storage measurement failed' in str(exc)
                else: raise AssertionError('Uncoordinated compiler deletion must fail GNU du')
                receipt=next(counted.glob('storage-failure-*.json'))
                proof=json.loads(receipt.read_text())
                assert proof['returncode']==1 and proof['bytes'] is None
                assert 'compiler.ptx' in proof['stderr']['tail']
                assert 'No such file or directory' in proof['stderr']['tail']
        evidence.update(receipt=str(receipt),receipt_sha256=hashlib.sha256(receipt.read_bytes()).hexdigest(),
                        proof=proof,passed=True)
    finally:
        # Only this newly-created, exact-ID CPU fixture; no remove/delete.
        (root/'finish').touch();release.touch();(root/'go').touch()
        status=q.inspect_owned(cid,counted,time.monotonic()+5)
        if status['Paused']: run(['docker','unpause',cid])
        if status['Running']:
            run(['docker','wait',cid],timeout=8)
        status=q.inspect_owned(cid,counted,time.monotonic()+5)
        assert not status['Running'] and not status['Paused']
        evidence['final_state']=status
        proof=json.loads(run(['docker','inspect','--format',
            '{"gpu_requests":{{json .HostConfig.DeviceRequests}},"mounts":{{json .Mounts}},'
            '"image":{{json .Image}},"network":{{json .HostConfig.NetworkMode}}}',cid]))
        assert proof['gpu_requests'] is None and proof['network']=='none'
        assert proof['image']==IMAGE
        assert len(proof['mounts'])==1 and proof['mounts'][0]['Source']==str(root)
        evidence['container_scope']=proof
        (root/'result.json').write_text(json.dumps(evidence,indent=2,allow_nan=False)+'\n')
    return evidence


def main():
    root=Path(sys.argv[1]).resolve()
    if root.exists(): raise RuntimeError('New CPU fixture root required; never overwrite/retry')
    root.mkdir()
    if not sys.platform.startswith('linux'): raise RuntimeError('Linux CPU required')
    library=root/'pause.so'
    run(['cc','-shared','-fPIC','-O2','-o',library,REPO/'tests/fixtures/storage_du_pause.c','-ldl'])
    results=[case(root/'baseline',library,False),case(root/'fixed',library,True)]
    assert not any(x in sys.modules for x in ['torch','ray','transformers','pysc2'])
    final=dict(passed=True,cases=results,heavy_imports=False,checked_at=time.time())
    (root/'result.json').write_text(json.dumps(final,indent=2,allow_nan=False)+'\n')
    print(json.dumps(final))


if __name__=='__main__': main()
