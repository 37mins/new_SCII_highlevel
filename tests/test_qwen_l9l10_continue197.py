"""Controlled continuation boundaries, no GPU/server side effects."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'experiments/records/20260921-sc2-policy-credit-v1'))
import qwen_l9l10_continue197 as c
from test_qwen_l9l10_same197 import HigherLevelQueueTests


class ContinuationTests(unittest.TestCase):
    def setUp(self):
        for module in (c,c.m,c.m.fresh,c.m.fresh.queue_impl,c.f,c.a,c.f.previous):
            guard=patch.dict(vars(module),{});guard.start();self.addCleanup(guard.stop)

    def cfg(self,index,level):
        cfg=HigherLevelQueueTests().cfg(index,level)
        if level==9:cfg['stages']=[] if index==0 else ['eval96']
        return cfg

    def fixture(self,tmp):
        c.ROOTS={9:Path(tmp)/'new9',10:Path(tmp)/'new10'}
        c.OLD_ROOTS={9:Path(tmp)/'old9',10:Path(tmp)/'old10'}
        c.OLD_SOURCE=Path(tmp)/'oldsource';c.SOURCE_PARENT=Path(tmp)/'newsource'
        c.FAILED_ROOTS={9:Path(tmp)/'failed9',10:Path(tmp)/'failed10'}
        c.FAILED_SOURCE=Path(tmp)/'failedsource'
        for level,root in c.ROOTS.items():
            root.mkdir();c.a.save(root/'deployment.json',dict(controller_sha='test',runtime_sha=c.RUNTIME_SHA),lock_root=root)
            for index,part in enumerate(c.PARTS):
                owner=root/part;owner.mkdir(parents=True)
                c.a.save(owner/'deployment.json',self.cfg(index,level),lock_root=root)
                c.a.save(owner/'parent-readiness.json',{'actual_parent_verified':True},lock_root=root)
        c.a.save(c.ROOTS[9]/'retained-acceptance.json',{'passed':True},lock_root=c.ROOTS[9])

    def test_nine_roots_original_limits_no_clock_extension(self):
        a=c.accounts(c.L9_DEADLINE)
        self.assertEqual(len(a[-1]['roots']),9)
        self.assertEqual(len(set(a[-1]['roots'])),9)
        self.assertEqual(a[-1]['limit'],512*c.a.GIB)
        for item in a[:2]:self.assertEqual(len(item['roots']),6);self.assertEqual(item['limit'],256*c.a.GIB)
        with self.assertRaises(ValueError):c.accounts(c.SUITE_DEADLINE+1)

    def test_only_l9_eval_new_l10_fresh_and_readonly_old_binds(self):
        for level in (9,10):
            c.configure(level)
            def read(path):
                if str(path).endswith('resolved_config.json'):return HigherLevelQueueTests().resolved(level,'eval96' if level==9 else 'train2')
                return self.cfg(1 if level==9 else 0,level)
            with patch.object(c.a,'read',side_effect=read):
                index,stage=(1,'eval96') if level==9 else (0,'pre')
                gpu=c.docker('stage',index,stage);cpu=c.docker('retained-cpu',index)
                self.assertEqual(gpu[-4:],['stage',str(level),str(index),stage])
                self.assertEqual(cpu[-3:],['retained-cpu',str(level),str(index)])
                self.assertNotIn('--gpus',cpu)
                for old in [*c.OLD_ROOTS.values(),*c.FAILED_ROOTS.values(),c.OLD_SOURCE,c.FAILED_SOURCE]:
                    self.assertIn(f'{old}:{old}:ro',gpu)
                self.assertIn(f'{c.ROOTS[9]}/.storage.lock:{c.ROOTS[9]}/.storage.lock',gpu)
                if level==9:
                    with self.assertRaises(ValueError):c.docker('stage',1,'train96')

    def run_fixture(self,tmp,side_effect=None,real_admission=False):
        self.fixture(tmp)
        patches=[patch.object(c,'check_cpu'),patch.object(c,'verify_retained'),
            patch.object(c.m,'contract_for',return_value={}),patch.object(c.sp,'run'),
            patch.object(c,'docker',return_value=['noop']),patch.object(c.time,'time',return_value=c.START+1000)]
        if not real_admission:patches.append(patch.object(c.m,'admit'))
        for p in patches:p.start();self.addCleanup(p.stop)
        return patch.object(c.h,'run_stages',side_effect=side_effect,return_value={})

    def test_real_admission_full_queue_order_uses_unique_receipts(self):
        def stages(names,*args,**kwargs):
            for name in names:kwargs['admit'](name)
            return {'phase':'completed','exit_code':0}
        with tempfile.TemporaryDirectory() as tmp:
            with self.run_fixture(tmp,stages,real_admission=True),patch.object(c.h,'sample'), \
                    patch.object(c.m.fresh.queue_impl.host,'writers_clear'), \
                    patch.object(c.m,'resources_ready',return_value=True) as resources:
                c.queue()
            self.assertEqual([x.args[0] for x in resources.call_args_list],
                ['eval96','gpu-preflight','eval96','arm','gpu-preflight','pre','train2','post','train96','eval96'])
            expected={9:{'long':['arm','gpu-preflight','eval96']},
                      10:{'short':['arm','gpu-preflight','pre','train2','post'],'long':['train96','eval96']}}
            for level,parts in expected.items():
                for part,names in parts.items():
                    owner=c.ROOTS[level]/('qwen-same/'+part)
                    self.assertEqual(sorted(p.name for p in owner.glob('fsync-*')),sorted('fsync-'+n for n in names))
                    for name in names:self.assertEqual((owner/('fsync-'+name)).read_bytes(),b'l9l10\n')
            # Receipt naming must NOT change the eval resource threshold.
            p=c.a.read(c.ROOTS[9]/c.PARTS[1]/'admission-arm.json')
            self.assertEqual(p['nvme_gib_min'],128)
            self.assertEqual(p['stage'],'eval96')
            self.assertEqual(p['receipt_name'],'arm')

    def test_repeated_actual_stage_admission_still_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.fixture(tmp);c.configure(9)
            with patch.object(c.h,'sample'),patch.object(c.m.fresh.queue_impl.host,'writers_clear'), \
                    patch.object(c.m,'resources_ready',return_value=True),patch.object(c.time,'time',return_value=c.START+1000):
                c.m.admit(1,'eval96',c.L9_DEADLINE)
                with self.assertRaises(FileExistsError):c.m.admit(1,'eval96',c.L9_DEADLINE)

    def r2_terminal_fixture(self,tmp):
        self.fixture(tmp)
        root=c.FAILED_ROOTS[9];owner=root/c.PARTS[1]
        owner.mkdir(parents=True);c.FAILED_ROOTS[10].mkdir()
        cid='4ef0996c8aee36a782df0003218ae573dec3e137b3c64007e2b5989d4c8e23f1'
        terminal={'Running':False,'Paused':False,'ExitCode':0,'OOMKilled':False,'Error':''}
        failed={'phase':'failed','error_type':'FileExistsError',
                'error':f"[Errno 17] File exists: '{owner}/fsync-eval96'",'completed':[]}
        data={root/'queue-state.json':dict(failed),owner/'host-supervision/state.json':dict(failed),
              root/'dispatch.json':{'start':c.START,'deadline':c.L9_DEADLINE},
              root/'suite-dispatch.json':{'deadline':c.SUITE_DEADLINE},
              owner/'gpu-preflight-supervision/state.json':{'phase':'completed','exit_code':0,
                  'completed':['gpu-preflight'],'deadline':c.L9_DEADLINE,'container_id':cid},
              owner/'gpu-preflight-supervision/gpu-preflight-guardian.json':{'phase':'completed',
                  'container_id':cid,'owner_root':str(owner),'deadline':c.L9_DEADLINE,'final_state':terminal}}
        for p in (patch.object(c.a,'read',side_effect=lambda p:data[Path(p)]),patch.object(c.a,'clean'),
                  patch.object(c.a,'cmd',return_value=json.dumps({'id':cid,'owner':str(owner),'state':terminal})),
                  patch.object(c.m,'sha256',return_value='f9cf19d822ef78bfea8a30dfdc503cc7e1cc51566a3aaab5cda53a21209ff7a4')):
            p.start();self.addCleanup(p.stop)
        return data

    def test_exact_r2_failure_gate_and_wrong_failure_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            data=self.r2_terminal_fixture(tmp)
            self.assertTrue(c.failed_r2_terminal()['passed'])
            data[c.FAILED_ROOTS[9]/'queue-state.json']['error_type']='RuntimeError'
            with self.assertRaisesRegex(RuntimeError,'Exact pre-game'):c.failed_r2_terminal()

    def test_r2_dispatch_or_live_probe_blocks_handoff(self):
        with tempfile.TemporaryDirectory() as tmp:
            data=self.r2_terminal_fixture(tmp)
            guardian=c.FAILED_ROOTS[9]/c.PARTS[1]/'gpu-preflight-supervision/gpu-preflight-guardian.json'
            data[guardian]['final_state']['Running']=True
            with self.assertRaisesRegex(RuntimeError,'Exact exited'):c.failed_r2_terminal()
            data[guardian]['final_state']['Running']=False
            (c.FAILED_ROOTS[10]/'dispatch.json').touch()
            with self.assertRaisesRegex(RuntimeError,'no new evaluation'):c.failed_r2_terminal()

    def test_success_order_retains96_never_retrains_l9(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.run_fixture(tmp) as run:c.queue()
            self.assertEqual([x.args[0] for x in run.call_args_list],
                [['gpu-preflight'],['eval96'],['gpu-preflight'],['pre','train2','post'],['train96','eval96']])
            l9=c.a.read(c.ROOTS[9]/'dispatch.json');l10=c.a.read(c.ROOTS[10]/'dispatch.json')
            self.assertEqual(l9['start'],c.START);self.assertEqual(l9['deadline'],c.L9_DEADLINE)
            self.assertEqual(l10['deadline'],min(c.START+1000+12*3600,c.SUITE_DEADLINE))
            suite=c.a.read(c.ROOTS[9]/'suite-dispatch.json')
            self.assertEqual(suite['start'],c.START);self.assertEqual(suite['deadline'],c.SUITE_DEADLINE)
            with self.assertRaisesRegex(RuntimeError,'Already queued'):c.queue()

    def test_l9_failure_blocks_l10(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.run_fixture(tmp,[{},RuntimeError('eval failed')]) as run:
                with self.assertRaisesRegex(RuntimeError,'eval failed'):c.queue()
            self.assertEqual(run.call_count,2)
            self.assertFalse((c.ROOTS[10]/'dispatch.json').exists())

    def test_retention_failure_blocks_all_gpu(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.run_fixture(tmp) as run,patch.object(c,'verify_retained',side_effect=RuntimeError('invalid retained')):
                with self.assertRaisesRegex(RuntimeError,'invalid retained'):c.queue()
                run.assert_not_called()

    def test_original_expired_l9_blocks_all_gpu(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.run_fixture(tmp) as run,patch.object(c.time,'time',return_value=c.L9_DEADLINE):
                with self.assertRaises(TimeoutError):c.queue()
                run.assert_not_called()


if __name__=='__main__':unittest.main()
