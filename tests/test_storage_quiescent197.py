"""CPU unit tests: only mocked Docker, never an experiment or GPU dispatch."""
from contextlib import contextmanager
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

RECORD = Path(__file__).resolve().parents[1]/'experiments/records/20260921-sc2-policy-credit-v1'
sys.path.insert(0, str(RECORD))
import acceptance197 as a
import storage_quiescent197 as q

CID = 'a'*64


def state(paused=False, running=True):
    return dict(Running=running, Paused=paused, Restarting=False, Dead=False)


class QuiescentTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.proof = {}

    def context(self):
        return q.paused_owned(CID, self.root, time.monotonic()+15, self.proof)

    def test_pause_verify_body_restore_order(self):
        events = []
        states = iter([state(), state(True), state(True), state()])
        def inspect(*args):
            events.append('inspect');return next(states)
        with patch.object(q, 'inspect_owned', side_effect=inspect), \
             patch.object(q, 'docker', side_effect=lambda args, _: events.append(args[0])):
            with self.context(): events.append('du')
        self.assertEqual(events, ['inspect','pause','inspect','du','inspect','unpause','inspect'])
        self.assertEqual(self.proof['quiescence']['cleanup'], 'verified-unpaused')

    def test_preexisting_pause_or_stopped_job_is_never_taken_over(self):
        for initial in [state(True), state(running=False), dict(state(), Restarting=True)]:
            with self.subTest(initial=initial), patch.object(q,'inspect_owned',return_value=initial), \
                 patch.object(q,'docker') as docker:
                with self.assertRaises(RuntimeError):
                    with self.context(): self.fail('must not scan')
                docker.assert_not_called()

    def test_wrong_owner_or_id_is_rejected(self):
        for value in [dict(id=CID,labels={'sc2.acceptance.root':'/wrong'},state=state()),
                      dict(id='b'*64,labels={'sc2.acceptance.root':str(self.root)},state=state())]:
            with self.subTest(value=value), patch.object(q,'docker',return_value=json.dumps(value)):
                with self.assertRaisesRegex(RuntimeError,'ownership'):
                    q.inspect_owned(CID,self.root,time.monotonic()+1)

    def test_inspect_does_not_request_environment_or_commands(self):
        value = dict(id=CID,labels={'sc2.acceptance.root':str(self.root)},state=state())
        with patch.object(q,'docker',return_value=json.dumps(value)) as command:
            q.inspect_owned(CID,self.root,time.monotonic()+1)
        template = command.call_args.args[0][2]
        self.assertNotIn('.Config.Env',template)
        self.assertNotIn('.Config.Cmd',template)

    def test_pause_timeout_is_ambiguous_and_always_restored(self):
        with patch.object(q,'inspect_owned',side_effect=[state(),state(True),state()]), \
             patch.object(q,'docker',side_effect=[subprocess.TimeoutExpired('pause',1),'']) as docker:
            with self.assertRaises(subprocess.TimeoutExpired):
                with self.context(): self.fail('must not scan')
        self.assertEqual([c.args[0][0] for c in docker.call_args_list],['pause','unpause'])
        self.assertEqual(self.proof['quiescence']['cleanup'],'verified-unpaused')

    def test_unconfirmed_pause_forbids_du(self):
        with patch.object(q,'inspect_owned',side_effect=[state(),state(),state()]), \
             patch.object(q,'docker'):
            with self.assertRaisesRegex(RuntimeError,'quiescence'):
                with self.context(): self.fail('must not scan')

    def test_du_exception_and_keyboard_interrupt_both_restore(self):
        for error in [ValueError('du error'), KeyboardInterrupt()]:
            with self.subTest(error=error), \
                 patch.object(q,'inspect_owned',side_effect=[state(),state(True),state(True),state()]), \
                 patch.object(q,'docker') as docker:
                with self.assertRaises(type(error)):
                    with self.context(): raise error
                self.assertEqual(docker.call_args.args[0],['unpause',CID])

    def test_failed_unpause_fails_closed_and_records_recovery_error(self):
        with patch.object(q,'inspect_owned',side_effect=[state(),state(True),state(True)]), \
             patch.object(q,'docker',side_effect=['',RuntimeError('unpause failed')]):
            with self.assertRaisesRegex(RuntimeError,'unpause failed'):
                with self.context(): pass
        self.assertEqual(self.proof['quiescence']['cleanup'],'failed')

    def test_exit_during_scan_rejects_acceptance(self):
        with patch.object(q,'inspect_owned',side_effect=[state(),state(True),state(running=False)]), \
             patch.object(q,'docker'):
            with self.assertRaisesRegex(RuntimeError,'exited'):
                with self.context(): pass

    def test_wrapper_requires_immutable_id_and_inclusive_root(self):
        for container, roots in [('name',[self.root]), (CID,[self.root/'unrelated'])]:
            with self.subTest(container=container,roots=roots), patch.object(a,'measure_budget') as scan:
                with self.assertRaises(ValueError):
                    q.measure_owned_budget(container,self.root,roots,self.root,1024,time.time()+90,
                                           'time','size',lock_root=self.root)
                scan.assert_not_called()

    def test_wrapper_refuses_execution_inside_container(self):
        with patch.object(Path,'exists',return_value=True), patch.object(a,'measure_budget') as scan:
            with self.assertRaisesRegex(RuntimeError,'Host-only'):
                q.measure_owned_budget(CID,self.root,[self.root],self.root,1024,time.time()+90,
                                       'time','size',lock_root=self.root)
            scan.assert_not_called()

    def test_docker_nonzero_stderr_and_exhausted_allowance(self):
        for result in [subprocess.CompletedProcess('docker',1,'','error'),
                       subprocess.CompletedProcess('docker',0,'','warning')]:
            with patch.object(q.subprocess,'run',return_value=result):
                with self.assertRaises(RuntimeError): q.docker(['pause',CID],time.monotonic()+1)
        with patch.object(q.subprocess,'run') as call:
            with self.assertRaises(TimeoutError): q.docker(['pause',CID],time.monotonic()-1)
            call.assert_not_called()

    def test_existing_sampler_locks_before_pause_and_keeps_exact_roots(self):
        events=[]
        @contextmanager
        def guard(*args,**kwargs):
            events.append('lock' if kwargs.get('exclusive') else 'publish');yield
        @contextmanager
        def quiet(until,proof):
            events.append('pause');yield;events.append('resume')
        def run(args,**kwargs):
            events.append('du')
            self.assertEqual(args,['du','-sb','--null','--',str(self.root)])
            return subprocess.CompletedProcess(args,0,f'42\t{self.root}\0','')
        with patch.object(a,'storage_guard',guard), patch.object(a.sp,'run',side_effect=run):
            a.measure_budget([self.root],self.root,1000,time.time()+90,'time','size',quiesce=quiet)
        self.assertEqual(events,['lock','pause','du','resume','publish'])

    def test_du_failure_still_restores_and_keeps_unknown_bytes(self):
        @contextmanager
        def quiet(until,proof):
            try: yield
            finally: self.proof['restored']=True
        bad=subprocess.CompletedProcess('du',1,f'1\t{self.root}\0','missing compiler.ptx')
        with patch.object(a.sp,'run',return_value=bad) as call:
            with self.assertRaisesRegex(RuntimeError,'Storage measurement failed'):
                a.measure_budget([self.root],self.root,1000,time.time()+90,'time','size',
                                 lock_root=self.root,quiesce=quiet)
        self.assertTrue(self.proof['restored']);self.assertEqual(call.call_count,1)
        receipt=json.loads(next(self.root.glob('storage-failure-*')).read_text())
        self.assertIsNone(receipt['bytes'])
        self.assertIn('compiler.ptx',receipt['stderr']['tail'])

    def test_cleanup_failure_retains_du_evidence_but_no_success(self):
        @contextmanager
        def quiet(until,proof):
            yield
            raise RuntimeError('recovery unverified')
        good=subprocess.CompletedProcess('du',0,f'42\t{self.root}\0','')
        with patch.object(a.sp,'run',return_value=good):
            with self.assertRaisesRegex(RuntimeError,'Storage measurement failed'):
                a.measure_budget([self.root],self.root,1000,time.time()+90,'time','size',
                                 lock_root=self.root,quiesce=quiet)
        receipt=json.loads(next(self.root.glob('storage-failure-*')).read_text())
        self.assertEqual(receipt['returncode'],0);self.assertIsNone(receipt['bytes'])
        self.assertFalse((self.root/'storage-state.json').exists())

    def test_pause_and_cleanup_time_cannot_extend_sample_allowance(self):
        clock=[0]
        @contextmanager
        def quiet(until,proof):
            clock[0]+=2
            yield
            clock[0]+=14
        good=subprocess.CompletedProcess('du',0,f'42\t{self.root}\0','')
        with patch.object(a.time,'monotonic',side_effect=lambda:clock[0]), \
             patch.object(a.sp,'run',return_value=good) as command:
            with self.assertRaisesRegex(RuntimeError,'Storage measurement failed'):
                a.measure_budget([self.root],self.root,1000,time.time()+90,'time','size',
                                 lock_root=self.root,quiesce=quiet)
        self.assertEqual(command.call_args.kwargs['timeout'],13)
        self.assertFalse((self.root/'storage-state.json').exists())

    def test_cleanup_timeout_does_not_overwrite_completed_du_diagnostics(self):
        @contextmanager
        def quiet(until,proof):
            yield
            raise subprocess.TimeoutExpired('unpause',10,output='pause-client',stderr='daemon timeout')
        bad=subprocess.CompletedProcess('du',1,'original partial total','original du error')
        with patch.object(a.sp,'run',return_value=bad):
            with self.assertRaisesRegex(RuntimeError,'Storage measurement failed'):
                a.measure_budget([self.root],self.root,1000,time.time()+90,'time','size',
                                 lock_root=self.root,quiesce=quiet)
        receipt=json.loads(next(self.root.glob('storage-failure-*')).read_text())
        self.assertEqual(receipt['stdout']['tail'],'original partial total')
        self.assertEqual(receipt['stderr']['tail'],'original du error')
        self.assertEqual(receipt['exception_output']['stderr']['tail'],'daemon timeout')
        self.assertIsNone(receipt['bytes'])


if __name__=='__main__': unittest.main()
