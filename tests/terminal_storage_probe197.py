"""Tiny CPU-only Docker lifecycle probe; no model/SC2/training entry point."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import time

SOURCE=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(SOURCE),str(SOURCE/'experiments/records/20260921-sc2-policy-credit-v1')]
import acceptance197 as a
import host_stage197 as h
from agent_system.sc2_terminal_handoff import publish


def child(owner, root, sha, case):
    if Path('/dev/nvidia0').exists():
        raise RuntimeError('CPU probe must not receive GPU devices')
    out=owner/'runs/probe';out.mkdir(parents=True)
    a.atomic_save(out/'manifest.json',dict(source_commit=sha,finalization_mode='terminal-drain-v1',dirty=False))
    time.sleep(2)  # Allow at least one ordinary CPU pause before terminal intent.
    publish(out,root,'cpu-'+case+'-probe')
    time.sleep(60 if case=='hang' else .3)
    return 7 if case=='exit7' else 0


def host(root, image, sha):
    if Path('/.dockerenv').exists() or not root.is_absolute() or root.exists():
        raise RuntimeError('Fresh absolute host-only probe root required')
    if not image.startswith('sha256:') or len(image)!=71:
        raise ValueError('Pinned existing Docker image ID required')
    root.mkdir();(root/'.storage.lock').touch()
    results=[];deadline=time.time()+300
    for case in ('exit0','exit7','hang'):
        owner=root/case;owner.mkdir()
        cfg=dict(terminal_handoff='terminal-drain-v1',run_prefix='cpu-'+case,runtime_sha=sha)
        accounts=[dict(roots=[root,SOURCE.parent],receipt_root=owner,limit=256*1024**2,deadline=deadline)]
        # New owned fixture only. Retain containers and all receipts after the probe.
        cmd=['docker','create','--name',root.name+'-'+case,
             '--label','sc2.acceptance.root='+str(owner),'--network','none','--read-only',
             '--cpus','1','--memory','256m','--pids-limit','128','--log-driver','none',
             '--cap-drop','ALL','--security-opt','no-new-privileges',
             '--tmpfs','/tmp:rw,nosuid,nodev,size=16m','-v',f'{SOURCE}:{SOURCE}:ro',
             '-v',f'{root}:{root}','--entrypoint','python3',image,'-B',str(Path(__file__)),
             'child',str(owner),str(root),sha,case]
        options=h.terminal_options(cfg,owner,owner/'control',deadline)
        finalized=[];verified=[]
        options['finalize']=lambda stage,cid:finalized.append(cid)
        failure=None
        try:
            h.run_stages(['probe'],lambda _:cmd,lambda _:verified.append(True),accounts,
                owner,owner/'control',root,deadline,admit=lambda _:None,interval=.1,**options)
        except RuntimeError as exc:
            failure=str(exc)
        status=a.read(owner/'control/state.json');cid=status['container_id']
        raw=subprocess.check_output(['docker','inspect','--format',
            '{"id":"{{.Id}}","state":{{json .State}},"devices":{{json .HostConfig.DeviceRequests}}}',cid],
            text=True,timeout=10)
        container=json.loads(raw)
        guardian=a.read(owner/'control/probe-guardian.json')
        intent=a.read(owner/'runs/probe/terminal-intent.json')
        pauses=[event for event in guardian['events'] if event['op']=='pause']
        if container['devices'] or container['state']['Running'] or container['state']['Paused']:
            raise RuntimeError('CPU fixture not stopped or unexpectedly allocated devices')
        if not pauses or any(event['at']>=intent['at'] for event in pauses):
            raise RuntimeError('Expected initial CPU pause and no pause after terminal publication')
        if case=='exit0':
            if failure or not finalized or not verified or status['phase']!='completed' or container['state']['ExitCode']!=0:
                raise RuntimeError('Normal terminal handoff did not complete')
        elif not failure or finalized or verified or status['phase']!='failed':
            raise RuntimeError('Failed terminal fixture advanced to finalization/verification')
        if case=='hang':
            receipts=list(owner.glob('storage-failure-*.json'))
            if len(receipts)!=1 or 'Terminal drain consumed' not in a.read(receipts[0])['error']:
                raise RuntimeError('Expected original bounded drain timeout')
        results.append(dict(case=case,passed=True,container=container,phase=status['phase'],
            finalized=len(finalized),verified=len(verified),initial_pause_count=len(pauses),
            terminal_intent_at=intent['at'],error=failure))
    value=dict(passed=True,cpu_only=True,games=0,updates=0,source_sha=sha,image=image,
               checked_at=time.time(),results=results)
    a.save(root/'result.json',value,lock_root=root)
    print(json.dumps(value))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',choices=['host','child']);parser.add_argument('args',nargs='+')
    args=parser.parse_args()
    if args.mode=='host':
        host(Path(args.args[0]),args.args[1],args.args[2])
    else:
        sys.exit(child(Path(args.args[0]),Path(args.args[1]),args.args[2],args.args[3]))
