"""CPU tests for the opt-in host integration; Docker is mocked here."""
from contextlib import nullcontext
import io
import json
from pathlib import Path
import socket
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch,MagicMock

REC=Path(__file__).resolve().parents[1]/'experiments/records/20260921-sc2-policy-credit-v1'
sys.path.insert(0,str(REC))
import acceptance197 as a
import storage_guardian197 as g
import host_stage197 as h
import l7_followup197 as f

CID='a'*64


def state(status='running',paused=False,exit_code=0):
    return dict(Status=status,Running=status=='running',Paused=paused,ExitCode=exit_code,
                Dead=False,Restarting=False)


class GuardianTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)

    def serve(self,requests,initial=None,fail_pause=False,exit_on_resume=False):
        current=state('created') if initial is None else initial.copy()
        actions=[]
        parent,child=socket.socketpair()
        def docker(args,until):
            actions.append(args[0])
            if args[0]=='start':current.update(state())
            elif args[0]=='pause':
                current.update(state(paused=True))
                if fail_pause=='runtime':
                    current.update(state())
                    raise RuntimeError('OCI runtime pause failed: timeout of 10s reached waiting for the cgroup to freeze')
                if fail_pause:raise TimeoutError('ambiguous pause')
            elif args[0]=='unpause':
                current['Paused']=False
                if exit_on_resume:current.update(state('exited'))
            elif args[0]=='stop':current.update(state('exited'))
            return ''
        result=[]
        with patch.object(g.q,'inspect_owned',side_effect=lambda *args:current.copy()),patch.object(g.q,'docker',side_effect=docker):
            worker=threading.Thread(target=lambda:result.append(g.serve(child,CID,self.root,time.time()+90,self.root/'guardian.json',self.root)))
            worker.start()
            with parent.makefile('rb') as stream:
                ready=g.receive(stream)
                if ready.get('ok'):
                    for request in requests:
                        if request['op']=='finish':current.update(state('exited'))
                        g.send(parent,request)
                        reply=g.receive(stream)
                        if not reply.get('ok'):break
            parent.close();worker.join(3)
            self.assertFalse(worker.is_alive())
        return a.read(self.root/'guardian.json'),actions,result

    def test_guardian_start_pause_restore_success(self):
        proof,actions,result=self.serve([dict(op='start'),dict(op='pause',until=time.monotonic()+10),dict(op='resume'),dict(op='finish')])
        self.assertEqual(result,[0]);self.assertEqual(actions,['start','pause','unpause'])
        self.assertEqual(proof['phase'],'completed')

    def test_eof_restores_and_stops_owned_stage(self):
        proof,actions,result=self.serve([dict(op='start'),dict(op='pause',until=time.monotonic()+10)])
        self.assertEqual(result,[1]);self.assertEqual(actions,['start','pause','unpause','stop'])
        self.assertTrue(proof['recovery']['stopped_verified'])

    def test_clean_exit_immediately_after_resume_is_success(self):
        proof,actions,result=self.serve([dict(op='start'),dict(op='pause',until=time.monotonic()+10),dict(op='resume'),dict(op='finish')],exit_on_resume=True)
        self.assertEqual(result,[0]);self.assertEqual(proof['phase'],'completed')
        self.assertEqual(actions,['start','pause','unpause'])

    def test_terminal_receipt_cannot_deadlock_on_supervisor_lock(self):
        with a.storage_guard(self.root,exclusive=True),patch.object(a,'save',side_effect=AssertionError('guardian must not lock/publish by rename')):
            proof,_,result=self.serve([dict(op='start'),dict(op='pause',until=time.monotonic()+10)])
        self.assertEqual(result,[1]);self.assertTrue(proof['recovery']['stopped_verified'])

    def test_eof_before_start_never_starts_job(self):
        proof,actions,_=self.serve([])
        self.assertEqual(actions,[]);self.assertTrue(proof['recovery']['stopped_verified'])

    def test_ambiguous_pause_is_restored_and_failed(self):
        proof,actions,_=self.serve([dict(op='start'),dict(op='pause',until=time.monotonic()+10)],fail_pause=True)
        self.assertEqual(actions,['start','pause','unpause','stop'])
        self.assertEqual(proof['phase'],'failed')

    def test_initially_running_or_paused_is_not_adopted(self):
        for initial in [state(),state(paused=True),state('exited')]:
            with self.subTest(initial=initial):
                proof,actions,_=self.serve([],initial)
                self.assertEqual(actions,[]);self.assertNotIn('recovery',proof)
                (self.root/'guardian.json').unlink()

    def test_invalid_pause_bound_and_duplicate_start_fail_closed(self):
        for request in [dict(op='pause',until=time.monotonic()+100),dict(op='start')]:
            with self.subTest(request=request):
                proof,actions,_=self.serve([dict(op='start'),request])
                self.assertEqual(actions,['start','stop']);self.assertEqual(proof['phase'],'failed')
                (self.root/'guardian.json').unlink()

    def test_identity_requires_full_id_and_host(self):
        with self.assertRaises(ValueError):g.valid_identity('friendly-name',self.root)
        with patch.object(Path,'exists',return_value=True),self.assertRaises(RuntimeError):g.valid_identity(CID,self.root)

    def test_message_rejects_eof_and_oversize(self):
        with self.assertRaises(EOFError):g.receive(io.BytesIO(b''))
        with self.assertRaises(ValueError):g.receive(io.BytesIO(b'x'*8193))

    def test_unacknowledged_pause_preserves_original_error_without_resume(self):
        guard=g.Guardian(CID,self.root,time.time()+90,self.root/'unused.json',self.root)
        guard.process=MagicMock(pid=123)
        proof={}
        with patch.object(guard,'request',side_effect=RuntimeError('cgroup freeze timeout')) as request:
            with self.assertRaisesRegex(RuntimeError,'cgroup freeze timeout'):
                with guard.quiesce(time.monotonic()+10,proof):
                    self.fail('Unverified pause must not enter du')
        self.assertEqual([c.args[0] for c in request.call_args_list],['pause'])
        self.assertEqual(proof['quiescence']['cleanup'],'guardian-recovery-required')
        self.assertFalse(proof['quiescence']['paused_verified'])

    def test_pause_error_is_retained_in_terminal_operation(self):
        proof,_,_=self.serve([dict(op='start'),dict(op='pause',until=time.monotonic()+10)],fail_pause='runtime')
        self.assertEqual(proof['pending_operation']['op'],'pause')
        self.assertEqual(proof['phase'],'failed')
        self.assertIn('cgroup to freeze',proof['pending_operation']['pause_command_error'])
        self.assertFalse(proof['pending_operation']['observed_state']['Paused'])
        self.assertTrue(proof['recovery']['stopped_verified'])

    def test_unpause_failure_still_attempts_owned_stop(self):
        with patch.object(g.q,'inspect_owned',side_effect=[state(paused=True),state(paused=True),state('exited')]),patch.object(g.q,'docker',side_effect=[RuntimeError('unpause'), '']) as command:
            proof=g.recover(CID,self.root,True,time.monotonic()+35)
        self.assertTrue(proof['stopped_verified']);self.assertEqual(len(proof['errors']),1)
        self.assertEqual([x.args[0][0] for x in command.call_args_list],['unpause','stop'])

    def test_recovery_refuses_unowned_pause(self):
        with patch.object(g.q,'inspect_owned',return_value=state(paused=True)),patch.object(g.q,'docker') as command:
            with self.assertRaises(RuntimeError):g.recover(CID,self.root,False,time.monotonic()+35)
            command.assert_not_called()


class HostTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.deadline=time.time()+120
        self.accounts=[dict(roots=[self.root],receipt_root=self.root,limit=1048576,deadline=self.deadline)]

    def run_stages(self,verify,stages=('pre','train2')):
        args=['docker','create','--label','sc2.acceptance.root='+str(self.root),'image','stage']
        return h.run_stages(stages,lambda _:args,verify,self.accounts,self.root,self.root/'control',self.root,self.deadline,admit=lambda _:None,interval=.01)

    def test_stages_require_exit_and_verifier_before_next(self):
        events=[]
        guard=MagicMock();guard.__enter__.return_value=guard
        with patch.object(h,'sample',side_effect=lambda *args:events.append('sample')),patch.object(h.q,'docker',side_effect=lambda *args:events.append('create') or CID),patch.object(h.q,'inspect_owned',return_value=state('exited')),patch.object(h,'Guardian',return_value=guard):
            proof=self.run_stages(lambda s:events.append('verify-'+s))
        self.assertEqual(proof['completed'],['pre','train2'])
        self.assertLess(events.index('verify-pre'),len(events)-1-events[::-1].index('create'))
        self.assertEqual(guard.finish.call_count,2)

    def test_verifier_failure_blocks_next_container(self):
        guard=MagicMock();guard.__enter__.return_value=guard
        with patch.object(h,'sample'),patch.object(h.q,'docker',return_value=CID) as create,patch.object(h.q,'inspect_owned',return_value=state('exited')),patch.object(h,'Guardian',return_value=guard):
            with self.assertRaisesRegex(RuntimeError,'evidence'):self.run_stages(lambda s:(_ for _ in ()).throw(RuntimeError('evidence missing')))
        self.assertEqual(create.call_count,1)
        self.assertEqual(a.read(self.root/'control/state.json')['completed'],[])

    def test_container_failure_blocks_verifier_and_successors(self):
        guard=MagicMock();guard.__enter__.return_value=guard
        with patch.object(h,'sample'),patch.object(h.q,'docker',return_value=CID) as create,patch.object(h.q,'inspect_owned',return_value=state('exited',exit_code=7)),patch.object(h,'Guardian',return_value=guard):
            verify=MagicMock()
            with self.assertRaises(RuntimeError):self.run_stages(verify)
        verify.assert_not_called();self.assertEqual(create.call_count,1)

    def test_preflight_storage_failure_never_creates(self):
        with patch.object(h,'sample',side_effect=RuntimeError('du failed')),patch.object(h.q,'docker') as create:
            with self.assertRaises(RuntimeError):self.run_stages(lambda _:None)
            create.assert_not_called()

    def test_no_overwrite_or_clock_reset(self):
        (self.root/'control').mkdir()
        with patch.object(h.q,'docker') as create:
            with self.assertRaises(FileExistsError):self.run_stages(lambda _:None)
            create.assert_not_called()
        self.accounts[0]['deadline']+=1
        with self.assertRaises(ValueError):self.run_stages(lambda _:None)

    def test_sample_has_one_host_owner_and_exact_quotas(self):
        guard=MagicMock()
        with patch.object(a,'measure_budget') as scan:h.sample(self.accounts,self.root,guard)
        self.assertEqual(scan.call_count,1)
        self.assertEqual(scan.call_args.args[:4],([self.root],self.root,1048576,self.deadline))
        self.assertIs(scan.call_args.kwargs['quiesce'],guard.quiesce)

    def test_adapter_only_replaces_controller_entry_not_runtime_flags(self):
        cfg=dict(stages=['train96'])
        command=['docker','run','--name','fixture','--gpus','all','image','-B','old.py','execute','1']
        with patch.object(f,'select',return_value=cfg),patch.object(f,'docker',return_value=command.copy()):
            value=h.docker_stage(1,'train96')
        self.assertEqual(value[:2],['docker','create']);self.assertIn('--gpus',value)
        self.assertEqual(value[-4:],['stage','1','train96',str(f.SUITE)])
        self.assertNotIn('execute',value)

    def test_child_execs_exact_launcher_without_watchdog(self):
        cfg=dict(storage_supervision='host-guardian-v1',runtime_sha='sha',controller_source='/src',controller_sha='sha')
        args=['bash','launcher','unchanged=value'];env={'SAFE':'fixture'}
        with patch.object(f,'select',return_value=cfg),patch.object(f,'invocation',return_value=(args,env,Path('/out'))),patch.object(a,'clean'),patch.object(h.os,'chdir'),patch.object(h.os,'execvpe') as execute,patch.object(a,'budget') as budget:
            h.child_stage(0,'pre',str(f.SUITE),True)
        execute.assert_called_once_with('bash',args,env);budget.assert_not_called()

    def test_old_frozen_deployment_cannot_enter_new_child(self):
        with patch.object(f,'select',return_value={}),patch.object(h.os,'execvpe') as execute:
            with self.assertRaises(RuntimeError):h.child_stage(0,'pre',str(f.SUITE),True)
        execute.assert_not_called()


if __name__=='__main__':unittest.main()
