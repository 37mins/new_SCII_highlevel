"""One-shot, host-only CPU admission; never dispatches GPU or retries a job."""
import json
from pathlib import Path
import subprocess as sp
import sys
import time
import spb_l8random197 as m


def main(module=m, train_entry='spb_l8random197.py', eval_entry='spb_l8random_eval197.py', *, terminal_probe=False):
    m=module
    if Path('/.dockerenv').exists(): raise RuntimeError('Real host only')
    m.configure();m.prepare()
    root=m.ROOT;a=m.a;here=a.HERE
    train=[sys.executable,'-B',str(here/train_entry)]
    evaluate=[sys.executable,'-B',str(here/eval_entry)]
    state=dict(status='running',runtime_sha=a.read(root/'deployment.json')['runtime_sha'],
               started_at=time.time(),jobs=[],no_gpu=True)
    receipt=root/'preparation.json'
    def run(label,command):
        item=dict(label=label,started_at=time.time())
        state['jobs'].append(item);a.save(receipt,state,lock_root=root)
        with (root/f'prepare-{label}.log').open('x') as stream:
            result=sp.run(command,stdout=stream,stderr=sp.STDOUT,timeout=600)
        item.update(exit_code=result.returncode,finished_at=time.time())
        if command[0]=='docker':
            name=command[command.index('--name')+1]
            raw=json.loads(a.cmd(['docker','inspect','--format',
                '{"id":"{{.Id}}","state":{{json .State}},"device_requests":{{json .HostConfig.DeviceRequests}}}',name]))
            item.update(container_name=name,container_id=raw['id'],state=raw['state']['Status'],
                        oom=raw['state']['OOMKilled'],device_requests=raw['device_requests'])
            if (raw['device_requests'] or raw['state']['Running'] or raw['state']['OOMKilled']
                    or raw['state']['ExitCode']!=0 or raw['state']['Error']):
                raise RuntimeError('CPU container gate failed: '+label)
        a.save(receipt,state,lock_root=root)
        if result.returncode: raise RuntimeError('CPU job failed: '+label)
    def generated(prefix,*args):
        command=json.loads(a.cmd(prefix+list(args)))
        if command[:2]!=['docker','run'] or '--gpus' in command: raise RuntimeError('No-GPU CPU command required')
        return command
    try:
        run('host-regressions',train+['host-regressions'])
        run('host-lifecycle',[sys.executable,'-B',str(a.SOURCE/'tests/host_supervision_probe197.py'),str(root/'cpu-host-lifecycle')])
        run('batch-churn',[sys.executable,'-B',str(a.SOURCE/'tests/storage_batch_probe197.py'),str(root/'cpu-batch-churn')])
        if terminal_probe:
            image=a.read(root/m.PARTS[0]/'deployment.json')['host']['image']
            run('terminal-drain',[sys.executable,'-B',str(a.SOURCE/'tests/terminal_storage_probe197.py'),
                'host',str(root/'cpu-terminal-drain'),image,state['runtime_sha']])
        a.save(root/'host-storage-probes.json',dict(passed=True,runtime_sha=state['runtime_sha'],
            checked_at=time.time(),no_gpu=True,tests=['cpu-host-lifecycle','cpu-batch-churn']),lock_root=root)
        run('model-regressions',generated(train,'regressions-command','0'))
        run('short-configs',generated(train,'cpu-command','0'))
        run('long-configs',generated(train,'cpu-command','1'))
        run('primary-configs',generated(evaluate,'cpu-command'))
        run('selection-configs',generated(evaluate,'cpu-command','--selection'))
        for index,stage in m.shared.CPU_PROBES:
            run('train-hook-'+stage,generated(train,'cpu-hook-command',str(index),stage))
        for stage in ('b00-original','b00-random96'):
            run('primary-hook-'+stage,generated(evaluate,'cpu-hook-command',stage))
        for step in (2,32,64,96):
            stage='b00-cp'+str(step)
            run('selection-hook-'+stage,generated(evaluate,'cpu-hook-command',stage,'--selection'))
        m.configure();m.shared.check_cpu()
        state.update(status='passed',finished_at=time.time())
    except BaseException as exc:
        state.update(status='failed',error_type=type(exc).__name__,error=str(exc),finished_at=time.time())
        a.save(receipt,state,lock_root=root);raise
    a.save(receipt,state,lock_root=root)
    print(json.dumps(state))


if __name__=='__main__':main()
