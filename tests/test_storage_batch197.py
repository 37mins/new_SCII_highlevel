"""Single freeze for inclusive account batch; no GPU, no Docker calls."""
from contextlib import contextmanager
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'experiments/records/20260921-sc2-policy-credit-v1'))
import storage_batch197 as b


class BatchTests(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory();self.addCleanup(t.cleanup);self.root=Path(t.name)
        self.accounts=[]
        for n in range(4):
            p=self.root/str(n);p.mkdir()
            self.accounts.append(dict(roots=[self.root,p],receipt_root=p,limit=1000,deadline=time.time()+90))
        self.events=[]
        case=self
        class Guard:
            @contextmanager
            def quiesce(self,until,proof):
                case.events.append('pause');proof['quiescence']={'paused_verified':True}
                try: yield
                finally:case.events.append('resume')
        self.guard=Guard()

    def du(self,args,**kwargs):
        self.events.append('du')
        self.assertGreater(kwargs['timeout'],0);self.assertLessEqual(kwargs['timeout'],15)
        return subprocess.CompletedProcess(args,0,''.join('1\t'+p+'\0' for p in args[4:]),'')

    def test_four_exact_accounts_one_pause_all_publish_after_resume(self):
        original=b.a.save
        def save(*args,**kwargs):
            self.assertEqual(self.events[-1],'resume');return original(*args,**kwargs)
        with patch.object(b.sp,'run',side_effect=self.du) as run,patch.object(b.a,'save',side_effect=save):
            b.sample(self.accounts,self.root,self.guard)
        self.assertEqual(self.events,['pause','du','du','du','du','resume'])
        self.assertEqual(run.call_count,4)
        for x in self.accounts:
            p=b.a.read(x['receipt_root']/'storage-state.json')
            self.assertEqual(p['bytes'],2);self.assertEqual(p['batch_accounts'],4)
            self.assertEqual(p['roots'],list(map(str,x['roots'])))

    def test_any_stderr_nonzero_partial_or_quota_rejects_entire_batch(self):
        cases=[(0,'warning',None),(1,'ENOENT',None),(0,'','partial'),(0,'',None)]
        for code,stderr,stdout in cases:
            with self.subTest(code=code,stderr=stderr,stdout=stdout):
                self.accounts[-1]['limit']=2 if (code,stderr,stdout)==(0,'',None) else 1000
                def run(args,**kw):
                    r=self.du(args,**kw)
                    if len(self.events)>=5:
                        r.returncode=code;r.stderr=stderr
                        if stdout is not None:r.stdout=stdout
                    return r
                self.events=[]
                with patch.object(b.sp,'run',side_effect=run):
                    with self.assertRaises(RuntimeError): b.sample(self.accounts,self.root,self.guard)
                self.assertEqual(self.events[-1],'resume')
                self.assertTrue(all(not (x['receipt_root']/'storage-state.json').exists() for x in self.accounts))

    def test_no_traversal_after_pause_failure(self):
        @contextmanager
        def fail(*_):
            raise RuntimeError('OCI freeze failed')
            yield
        with patch.object(self.guard,'quiesce',side_effect=fail),patch.object(b.sp,'run') as run:
            with self.assertRaises(RuntimeError): b.sample(self.accounts,self.root,self.guard)
            run.assert_not_called()
        proof=b.a.read(next(self.accounts[-1]['receipt_root'].glob('storage-failure-*.json')))
        self.assertIsNone(proof['bytes']);self.assertEqual(proof['samples'],[])

    def test_resume_failure_prevents_all_success_receipts(self):
        @contextmanager
        def fail(*_):
            yield
            raise RuntimeError('unpause failed')
        with patch.object(self.guard,'quiesce',side_effect=fail),patch.object(b.sp,'run',side_effect=self.du):
            with self.assertRaises(RuntimeError):b.sample(self.accounts,self.root,self.guard)
        self.assertTrue(all(not (x['receipt_root']/'storage-state.json').exists() for x in self.accounts))

    def test_single_allowance_and_static_sample(self):
        with patch.object(b.sp,'run',side_effect=self.du) as run:
            b.sample(self.accounts,self.root)
        timeouts=[x.kwargs['timeout'] for x in run.call_args_list]
        self.assertEqual(timeouts,sorted(timeouts,reverse=True))
        self.assertEqual(self.events,['du']*4)

    def test_expired_deadline_fails_before_du(self):
        self.accounts[-1]['deadline']=time.time()+44
        with patch.object(b.sp,'run') as run:
            with self.assertRaises(TimeoutError):b.sample(self.accounts,self.root,self.guard)
            run.assert_not_called()


if __name__=='__main__':unittest.main()
