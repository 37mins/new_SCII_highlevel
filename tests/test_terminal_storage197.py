"""CPU-only terminal/freezer ordering and fail-closed finalization regressions."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import Mock, MagicMock, patch

REPO=Path(__file__).resolve().parents[1]
REC=REPO/'experiments/records/20260921-sc2-policy-credit-v1'
sys.path[:0]=[str(REPO),str(REC)]
from agent_system import sc2_terminal_handoff as child
import host_stage197 as host
import storage_batch197 as batch
import terminal_storage197 as terminal

CID='a'*64


def state(running=False, code=0, paused=False):
    return dict(Status='running' if running else 'exited',Running=running,
                Paused=paused,ExitCode=code,Dead=False,Restarting=False)


class TerminalTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup)
        self.root=Path(temp.name);self.out=self.root/'runs/train96'
        self.out.mkdir(parents=True);(self.root/'.storage.lock').touch()
        self.manifest=dict(finalization_mode=child.VERSION,source_commit='b'*40,dirty=False)
        self.write(self.out/'manifest.json',self.manifest)
        self.intent=dict(path=self.out/'terminal-intent.json',run_id='fixture-train96',source_commit='b'*40)
        self.guard=Mock(cid=CID,owner=self.root)
        self.events=[]
        @contextmanager
        def freeze(until,proof):
            self.events.append('pause')
            yield
            self.events.append('resume')
        self.guard.quiesce=Mock(side_effect=freeze)
        self.accounts=[dict(roots=[self.root],receipt_root=self.root,limit=10**6,deadline=time.time()+120)]

    def write(self,path,value):
        path.write_text(json.dumps(value))

    def publish(self):
        return child.publish(self.out,self.root,self.intent['run_id'])

    def du(self,args,**kwargs):
        self.events.append('du')
        return subprocess.CompletedProcess(args,0,f'1\t{self.root}\0','')

    def sample(self):
        return batch.sample(self.accounts,self.root,self.guard,terminal_intent=self.intent)

    def test_default_no_marker_retains_one_verified_pause(self):
        with patch.object(batch.sp,'run',side_effect=self.du):self.sample()
        self.assertEqual(self.events,['pause','du','resume'])

    def test_marker_never_freezes_teardown_and_requires_exit_before_du(self):
        self.publish()
        def inspect(*_):
            self.events.append('inspect')
            return state(running=self.events.count('inspect')==1)
        with patch.object(terminal.q,'inspect_owned',side_effect=inspect),patch.object(batch.sp,'run',side_effect=self.du):
            self.sample()
        self.assertEqual(self.events,['inspect','inspect','du'])
        self.guard.quiesce.assert_not_called()
        proof=json.loads((self.root/'storage-state.json').read_text())
        self.assertEqual(proof['quiescence']['mode'],'exited-zero')
        self.assertFalse(proof['quiescence']['paused_verified'])

    def test_nonzero_paused_dead_or_restarting_terminal_never_measured(self):
        self.publish()
        cases=[state(code=137),state(True,paused=True),dict(state(True),Dead=True),dict(state(True),Restarting=True)]
        for current in cases:
            with self.subTest(current=current),patch.object(terminal.q,'inspect_owned',return_value=current),patch.object(batch.sp,'run') as du:
                with self.assertRaises(RuntimeError):self.sample()
                du.assert_not_called();self.guard.quiesce.assert_not_called()
        self.assertFalse((self.root/'storage-state.json').exists())

    def test_drain_timeout_does_not_fallback_retry_pause_or_publish_success(self):
        self.publish();self.accounts[0]['deadline']=time.time()+45.12
        with patch.object(terminal.q,'inspect_owned',return_value=state(True)),patch.object(batch.sp,'run') as du:
            with self.assertRaises(RuntimeError):self.sample()
            du.assert_not_called();self.guard.quiesce.assert_not_called()
        self.assertFalse((self.root/'storage-state.json').exists())
        failure=json.loads(next(self.root.glob('storage-failure-*.json')).read_text())
        self.assertIn('original measurement allowance',failure['error'])

    def test_drain_and_du_share_remaining_allowance(self):
        self.publish();clock=[10.0]
        def inspect(*_):clock[0]+=3;return state()
        with patch.object(batch.time,'monotonic',side_effect=lambda:clock[0]),patch.object(terminal.q,'inspect_owned',side_effect=inspect),patch.object(batch.sp,'run',side_effect=self.du) as du:
            self.sample()
        self.assertEqual(du.call_args.kwargs['timeout'],12)

    def test_bad_intent_never_falls_back_to_pause(self):
        good=self.publish()
        cases=[dict(good,source_commit='wrong'),dict(good,run_id='other'),dict(good,experiment_accepted=True),dict(good,version='v0')]
        for value in cases:
            self.write(self.intent['path'],value)
            with patch.object(batch.sp,'run') as du:
                with self.assertRaises(RuntimeError):self.sample()
                du.assert_not_called();self.guard.quiesce.assert_not_called()

    def test_partial_and_symlink_intent_fail_closed(self):
        self.intent['path'].write_text('{')
        with self.assertRaises(ValueError):terminal.validate_intent(self.intent)
        self.intent['path'].unlink();self.intent['path'].symlink_to(self.out/'manifest.json')
        with self.assertRaises(ValueError):terminal.validate_intent(self.intent)

    def test_publication_is_opt_in_one_shot_not_success(self):
        value=self.publish()
        self.assertFalse(value['experiment_accepted'])
        self.assertFalse((self.out/'result.json').exists())
        with self.assertRaises(FileExistsError):self.publish()
        self.manifest['finalization_mode']='inline';self.write(self.out/'manifest.json',self.manifest)
        with self.assertRaises(RuntimeError):self.publish()

    def test_existing_stable_lock_required(self):
        (self.root/'.storage.lock').unlink()
        with self.assertRaises(FileNotFoundError):self.publish()
        self.assertFalse(self.intent['path'].exists())

    def test_exclusive_scanner_blocks_terminal_transition(self):
        with (self.root/'.storage.lock').open('r+') as lock,ThreadPoolExecutor(1) as pool:
            fcntl.flock(lock,fcntl.LOCK_EX)
            future=pool.submit(self.publish)
            time.sleep(.05)
            self.assertFalse(future.done());self.assertFalse(self.intent['path'].exists())
            fcntl.flock(lock,fcntl.LOCK_UN)
            future.result(timeout=2)
        terminal.validate_intent(self.intent)

    def test_shared_publication_blocks_sampler_before_freeze(self):
        with (self.root/'.storage.lock').open('r+') as lock,ThreadPoolExecutor(1) as pool:
            fcntl.flock(lock,fcntl.LOCK_SH)
            with patch.object(terminal.q,'inspect_owned',return_value=state()),patch.object(batch.sp,'run',side_effect=self.du):
                future=pool.submit(self.sample)
                time.sleep(.05);self.guard.quiesce.assert_not_called()
                self.publish()
                fcntl.flock(lock,fcntl.LOCK_UN)
                future.result(timeout=2)
        self.assertEqual(self.events,['du']);self.guard.quiesce.assert_not_called()

    def prepare_finalizer(self):
        self.publish();control=self.root/'host-supervision';control.mkdir()
        deadline=self.accounts[0]['deadline']
        proof=dict(phase='completed',container_id=CID,owner_root=str(self.root),deadline=deadline,final_state=state())
        self.write(control/'train96-guardian.json',proof)
        cfg=dict(terminal_handoff=child.VERSION,runtime_sha='b'*40,run_prefix='fixture')
        return cfg,control,deadline,proof

    def test_failed_guardian_or_container_cannot_be_relabelled_by_recorder(self):
        cfg,control,deadline,proof=self.prepare_finalizer()
        for phase,actual in [('failed',state()),('completed',state(code=137)),('completed',state(True))]:
            proof['phase']=phase;self.write(control/'train96-guardian.json',proof)
            with patch.object(host.q,'inspect_owned',return_value=actual),patch.object(host.subprocess,'run') as run:
                with self.assertRaises(RuntimeError):host.finalize_record(cfg,'train96',CID,self.root,control,deadline)
                run.assert_not_called()

    def test_finalizer_uses_frozen_recorder_only_after_actual_exit(self):
        cfg,control,deadline,_=self.prepare_finalizer()
        with patch.object(host.q,'inspect_owned',return_value=state()) as inspect,patch.object(host.subprocess,'run') as run:
            host.finalize_record(cfg,'train96',CID,self.root,control,deadline)
            inspect.assert_called_once()
            self.assertEqual(run.call_args.args[0][2],str(self.root/'runtime/scripts/run_record.py'))
            self.assertEqual(run.call_args.args[0][-2:],['--exit-code','0'])
            self.assertLessEqual(run.call_args.kwargs['timeout'],deadline-45-time.time()+.1)
        (self.out/'.done').touch()
        with patch.object(host.q,'inspect_owned',return_value=state()),patch.object(host.subprocess,'run') as run:
            with self.assertRaisesRegex(RuntimeError,'existing result'):host.finalize_record(cfg,'train96',CID,self.root,control,deadline)
            run.assert_not_called()

    def test_launcher_deferred_trap_preserves_pipeline_failure(self):
        source=(REPO/'scripts/train_sc2.sh').read_text()
        function=source[source.index('finish_run() {'):source.index('case "${SC2_FINALIZATION_MODE')]
        for mode in ['inline',child.VERSION]:
            for code in [0,17]:
                proc=subprocess.run(['bash','-c',function+'\ntrap finish_run EXIT\nexit '+str(code)],
                    env=dict(os.environ,SC2_FINALIZATION_MODE=mode,PYTHON_BIN='echo',repo_dir=str(REPO),OUTPUT_DIR=str(self.out)),capture_output=True,text=True)
                self.assertEqual(proc.returncode,code)
                self.assertEqual('run_record.py' in proc.stdout,mode=='inline')

    def test_taskrunner_hook_after_successful_fit_before_function_exit(self):
        source=(REPO/'verl/trainer/main_ppo.py').read_text()
        self.assertLess(source.index('trainer.fit()'),source.index('publish_from_config(config)'))
        class Config:
            trainer={}
        self.assertIsNone(child.publish_from_config(Config()))

    def test_explicit_launch_and_host_options_must_match(self):
        cfg=dict(terminal_handoff=child.VERSION,run_prefix='fixture',runtime_sha='b'*40)
        args=['bash','launcher'];env={}
        host.terminal_launch(cfg,args,env,self.root)
        host.terminal_launch(cfg,args,env,self.root)
        self.assertEqual(len(args),3)
        self.assertEqual(env['SC2_FINALIZATION_MODE'],child.VERSION)
        options=host.terminal_options(cfg,self.root,self.root/'control',self.accounts[0]['deadline'])
        self.assertEqual(options['terminal_intent_for']('train96'),self.intent)
        host.terminal_launch({},[],env,self.root)
        self.assertNotIn('SC2_FINALIZATION_MODE',env)
        self.assertEqual(host.terminal_options({},self.root,self.root,0),{})
        with self.assertRaises(ValueError):host.terminal_options(dict(terminal_handoff='typo'),self.root,self.root,0)

    def test_host_finalizes_only_after_guardian_and_blocks_next_on_error(self):
        cfg,control,deadline,_=self.prepare_finalizer()
        # run_stages allocates its own separate fresh control root.
        def finalize(stage,cid):
            self.events.append('finalize')
            self.assertIn('guardian-finish',self.events)
            raise RuntimeError('fixture recorder failed')
        guard=MagicMock();guard.__enter__.return_value=guard
        guard.finish.side_effect=lambda:self.events.append('guardian-finish')
        args=['docker','create','--label','sc2.acceptance.root='+str(self.root),'image']
        with patch.object(host,'sample'),patch.object(host.q,'docker',return_value=CID) as create,patch.object(host.q,'inspect_owned',return_value=state()),patch.object(host,'Guardian',return_value=guard):
            verify=Mock()
            with self.assertRaisesRegex(RuntimeError,'fixture recorder failed'):
                host.run_stages(['pre','train2'],lambda _:args,verify,self.accounts,self.root,
                    self.root/'fresh-control',self.root,deadline,admit=lambda _:None,
                    terminal_intent_for=lambda _:self.intent,finalize=finalize)
            verify.assert_not_called();self.assertEqual(create.call_count,1)
        self.assertEqual(json.loads((self.root/'fresh-control/state.json').read_text())['completed'],[])

    def test_real_publisher_process_drains_before_static_measurement(self):
        code=('import sys,time; from pathlib import Path; '
              'from agent_system.sc2_terminal_handoff import publish; '
              'publish(Path(sys.argv[1]),Path(sys.argv[2]),sys.argv[3]); '
              'print("intent",flush=True); time.sleep(.15)')
        proc=subprocess.Popen([sys.executable,'-B','-c',code,str(self.out),str(self.root),self.intent['run_id']],
            cwd=REPO,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        try:
            import select
            self.assertTrue(select.select([proc.stdout],[],[],3)[0])
            self.assertEqual(proc.stdout.readline().strip(),'intent')
            self.assertIsNone(proc.poll())
            def inspect(*_):
                code=proc.poll()
                return state(running=code is None,code=code or 0)
            def du(args,**kw):
                self.assertEqual(proc.poll(),0)
                return self.du(args,**kw)
            with patch.object(terminal.q,'inspect_owned',side_effect=inspect),patch.object(batch.sp,'run',side_effect=du):
                self.sample()
            self.guard.quiesce.assert_not_called()
        finally:
            proc.communicate(timeout=3)


if __name__=='__main__':unittest.main()
