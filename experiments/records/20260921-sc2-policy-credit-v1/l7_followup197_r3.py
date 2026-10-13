"""Approved replacement queue after CP96-only evaluation; old failed queues untouched."""
import argparse
import json
import subprocess as sp
import sys

import acceptance197 as a
import l7_followup197 as f
import qwen_l7_eval96_197 as e

ROOT = a.Path('/var/jfsCache/sc2-l7-followup197-20260922-r3')
RETAINED = [a.Path('/var/jfsCache/sc2-l7-followup197-20260922-r1'),
    a.Path('/var/jfsCache/sc2-l7-followup197-source-20260922-r1'),
    a.Path('/var/jfsCache/sc2-l7-followup197-20260922-r2'),
    a.Path('/var/jfsCache/sc2-l7-followup197-source-20260922-r2')]
BASE_VERIFY = f.verify


def configure(callbacks=True):
    f.SUITE = ROOT
    f.RETAINED_PREPARATION = RETAINED
    f.PREDECESSOR = e.ROOT
    f.CONTAINER_PREFIX = 'sc2-l7-followup197-20260922-r3-'
    f.RUN_PREFIX = 'l7-followup197-r3-'
    f.DOCKER_SCRIPT = a.HERE/'l7_followup197_r3.py'
    if callbacks:
        f.predecessor_complete, f.verify = predecessor_complete, verify


def predecessor_complete():
    queue = a.read(e.ROOT/'queue-state.json')
    if queue['phase'] == 'failed': raise RuntimeError('New evaluation failed; stop all successors')
    if queue['phase'] != 'completed': return False
    state = a.read(e.ROOT/'state.json')
    if (queue['exit_code'] != 0 or state['phase'] != 'completed' or state['exit_code'] != 0
            or state['completed'] != ['eval96'] or state['deadline'] != e.DEADLINE):
        raise RuntimeError('Final evaluation terminal mismatch')
    status = json.loads(a.cmd(['docker','inspect','--format','{{json .State}}',e.CONTAINER]))
    if status['Running'] or status['ExitCode'] != 0: raise RuntimeError('Eval container not successfully exited')
    cfg = a.read(e.ROOT/'deployment.json')
    a.clean(e.ROOT/'runtime',cfg['runtime_sha'])
    script = a.Path(cfg['controller_source'])/a.HERE.relative_to(a.SOURCE)
    code = f"import sys;sys.path.insert(0,{str(script)!r});import qwen_l7_eval96_197 as e;e.configure();e.verify('eval96',write=False)"
    sp.run([sys.executable,'-B','-c',code],check=True,timeout=120)
    return True


def verify(stage,write=True):
    out = a.ROOT/'runs'/stage
    for name in ('manifest.json','result.json'):
        if a.read(out/name).get('metrics_precision') != 'binary64-v1':
            raise RuntimeError('Full-precision metrics required for every new stage')
    BASE_VERIFY(stage,write)


def prepare():
    f.prepare()
    # Complete the new deployment transaction before CPU validation or freezing.
    for root in [ROOT,*[ROOT/part for part in f.PARTS]]:
        cfg = a.read(root/'deployment.json')
        cfg.update(authorization='Sep22 user approved new CP96-only evaluation with six historical raw gradients '
            'unresolved and old failure retained, then fresh SpB same short+96 and Qwen random ownCP2+96; '
            'same budgets and original admission expiry; no old queue restart or extra training',
            predecessor_contract='CP96 paired zero-update evaluation passed; historical rounded-gradient gap accepted, not retroactive training acceptance')
        a.save(root/'deployment.json',cfg,lock_root=ROOT)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode',choices=['prepare','queue','cpu-command','regressions-command','cpu','parent-cpu','regressions','execute'])
    p.add_argument('index',type=int,nargs='?',choices=range(3))
    args = p.parse_args()
    configure(callbacks=args.mode != 'regressions')
    if args.mode == 'prepare': prepare()
    elif args.mode == 'queue': f.queue()
    elif args.index is None: p.error('Exact part index required')
    elif args.mode.endswith('-command'): print(json.dumps(f.docker(args.mode.removesuffix('-command'),args.index)))
    elif args.mode == 'regressions': f.regressions(args.index)
    elif args.mode == 'cpu': f.cpu(args.index)
    elif args.mode == 'parent-cpu': f.parent_cpu(args.index)
    else: f.select(args.index);a.execute()
