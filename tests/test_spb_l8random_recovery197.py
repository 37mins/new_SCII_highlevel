"""Approved failed-artifact adoption is evaluation-only, bounded and fail-closed."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch
import zipfile

REPO=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(REPO),str(REPO/'experiments/records/20260921-sc2-policy-credit-v1')]
import spb_l8random_recovery197 as m
import spb_l8random_recovery_plan as p
import spb_l8random_recovery_hook as hook


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        for module in (m.common,m.a,m.h):
            guard=patch.dict(vars(module),{});guard.start();self.addCleanup(guard.stop)
        with patch.object(m.a,'cmd',return_value='fixture'):m.configure()

    def cfg(self):
        return dict(runtime_sha='fixture',environment={'LONG_DEPENDENCY_PATH':'/deps'},
            model_kind='spb',model_mount='/assets/spb',difficulty='CheatVision',run_prefix=p.ROOT.name,
            seed_protocol='independent_uniform101',seed_group_mode='mixed_seed_ablation',
            worker_hook=p.WORKER_HOOK,terminal_handoff='terminal-drain-v1',
            host=dict(model='/original',venv='/venv',sc2='/sc2',image='fixture'))

    def resolved(self,stage):
        spec=p.stage_spec(stage)
        return dict(trainer=dict(val_only=True,val_before_train=True,save_freq=-1,n_gpus_per_node=8,
            sc2_checkpoint_resume=False,resume_mode='resume_path' if spec['checkpoint'] else 'disable',
            resume_from_path=str(spec['checkpoint']),sc2_terminal_handoff_lock_root=str(p.ROOT)),
            ray_init=dict(runtime_env=dict(worker_process_setup_hook=p.WORKER_HOOK,env_vars=dict(
                SC2_ACCEPTANCE_STAGE=stage,SC2PATH='/assets/StarCraftII',SC2_DIFFICULTY='CheatVision',
                SC2_EXPECTED_DIFFICULTY='CheatVision',SC2_L8_RENDEZVOUS_LOW_PORT='1',
                PYTHONPATH='/deps',SC2_EVAL_SEEDS_LOG_PATH='/seeds',SC2_RUNTIME_LOG_ROOT='/logs'))))

    def test_264_games_diag_first_same_registered_seed_sets(self):
        p.validate();self.assertEqual(len(p.STAGES)*8,264)
        self.assertEqual(p.STAGES[0],'diagnostic-cp96')
        for group,arms,seeds in [('selection',p.old.SELECTION_ARMS,p.old.SELECTION_SEEDS),
                                ('primary',p.old.ARMS,p.old.SEEDS)]:
            for arm in arms:
                actual=[seed for s in p.STAGES if p.stage_spec(s)['group']==group and p.stage_spec(s)['arm']==arm
                        for seed in p.stage_spec(s)['seeds']]
                self.assertEqual(actual,seeds)

    def test_cross_category_never_pairs_or_replaces_primary_with_best(self):
        self.assertEqual(p.paired_predecessors('test-b00-original'),[])
        self.assertEqual(p.paired_predecessors('test-b00-random96'),['test-b00-original'])
        self.assertEqual(p.paired_predecessors('sel-b00-cp32'),['sel-b00-cp2'])
        for s in p.STAGES:
            if s.startswith('test-') and not s.endswith('original'):
                self.assertEqual(p.stage_spec(s)['checkpoint'],p.CHECKPOINTS['cp96'])

    def test_wrong_stage_rejected(self):
        for s in ('train96','train192','b00-original','sel-b04-cp2'):
            with self.assertRaises(ValueError):p.stage_spec(s)

    def test_exact_ten_roots_limits_single_clock(self):
        accounts=m.accounts(123)
        self.assertEqual([x['limit']//m.a.GIB for x in accounts],[32,352])
        self.assertEqual(len(set(accounts[-1]['roots'])),10)
        self.assertTrue(all(x['deadline']==123 for x in accounts))
        self.assertEqual(p.WALL_SECONDS,28800)

    def test_all33_invocations_zero_update_terminal_opt_in(self):
        for stage in p.STAGES:
            args,env,out=m.invocation(self.cfg(),stage,True)
            settings=dict(x.split('=',1) for x in args if '=' in x)
            self.assertEqual(settings['trainer.val_only'],'True')
            self.assertEqual(settings['trainer.val_before_train'],'True')
            self.assertEqual(settings['trainer.save_freq'],'-1')
            self.assertEqual(settings['+trainer.sc2_terminal_handoff_lock_root'],str(p.ROOT))
            self.assertEqual(env['SC2_FINALIZATION_MODE'],'terminal-drain-v1')
            self.assertEqual(env['SC2_CHECKPOINT_RESUME'],'False')
            self.assertEqual(out,p.ROOT/'cpu'/stage);self.assertLess(len(env['RAY_TMPDIR']),20)
            spec=p.stage_spec(stage)
            if spec['checkpoint']:self.assertEqual(settings['trainer.resume_from_path'],str(spec['checkpoint']))
            else:self.assertNotIn('trainer.resume_from_path',settings)

    def test_new_only_writable_cpu_metadata_gpu_exact_spb(self):
        with patch.object(m.a,'read',return_value=self.cfg()):
            cpu=m.docker('cpu');gpu=m.docker('stage',p.STAGES[0])
        self.assertNotIn('--gpus',cpu);self.assertIn('CUDA_VISIBLE_DEVICES=',cpu)
        self.assertIn(str(m.common.previous.SPB_METADATA)+':/assets/spb:ro',cpu)
        self.assertIn('/original:/assets/spb:ro',gpu)
        self.assertIn(str(p.OLD_ROOT)+':'+str(p.OLD_ROOT)+':ro',gpu)
        self.assertEqual(gpu[:2],['docker','create']);self.assertNotIn('--restart',gpu)
        self.assertNotIn('--rm',gpu);self.assertEqual(gpu[-2:],['stage',p.STAGES[0]])

    def test_hook_preserves_runtime_and_rejects_missing_terminal_or_training(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'config.json'
            for stage in p.HOOK_STAGES:
                cfg=self.resolved(stage);path.write_text(json.dumps(cfg))
                _,proof=hook.runtime_environment(path,'/tmp/probe-ray')
                self.assertEqual(proof['stage'],stage)
                for key,val in [('val_only',False),('save_freq',32),('sc2_terminal_handoff_lock_root','/old')]:
                    bad=copy.deepcopy(cfg);bad['trainer'][key]=val;path.write_text(json.dumps(bad))
                    with self.assertRaises(ValueError):hook.runtime_environment(path,'/tmp/probe-ray')

    def test_installs_real_feedback_evaluator_all33(self):
        from types import SimpleNamespace
        evaluate=Mock()
        with patch.dict(sys.modules,feedback_eval=SimpleNamespace(install=evaluate)):
            for stage in p.STAGES:
                with patch.dict(m.os.environ,SC2_ACCEPTANCE_STAGE=stage):hook.install()
                spec=p.stage_spec(stage);kw=evaluate.call_args.kwargs
                self.assertEqual(kw['expected_step'],spec['expected_step']);self.assertEqual(kw['game_seeds'],spec['seeds'])

    def test_stream_hash_and_crc_bind_all_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            cp=Path(tmp);(cp/'actor').mkdir()
            for name in m.checkpoint_names():
                with zipfile.ZipFile(cp/name,'w') as z:z.writestr('data',b'fixture')
            sizes={name:(cp/name).stat().st_size for name in m.checkpoint_names()}
            with patch.object(Path,'read_bytes',side_effect=AssertionError('No whole-tensor buffering')):
                proof=m.inspect_checkpoint(cp,sizes,{})
            self.assertEqual(len(proof['files']),26)
            self.assertEqual(sum(x['model_zip_crc_checked'] for x in proof['files'].values()),8)
            with self.assertRaises(RuntimeError):m.inspect_checkpoint(cp,sizes,{'sc2_state.pt':'wrong'})
            (cp/'actor/model_world_size_8_rank_0.pt').write_bytes(b'bad')
            sizes['actor/model_world_size_8_rank_0.pt']=3
            with self.assertRaises(zipfile.BadZipFile):m.inspect_checkpoint(cp,sizes,{})

    def test_audit_shape_and_path_bindings_match_real_fixture(self):
        audit=m.a.read(m.AUDIT)
        for arm,cp in p.CHECKPOINTS.items():
            item=audit['host']['result']['checkpoints'][arm[2:]]
            self.assertEqual(item['path'],str(cp));self.assertEqual(set(item['required_files']),set(m.checkpoint_names()))
            self.assertIn('sc2_state.pt',audit['small_state']['result']['checkpoints'][arm[2:]]['small_file_sha256'])

    def test_symlink_or_empty_checkpoint_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'empty';path.touch()
            with self.assertRaises(ValueError):m.file_identity(path)
            path.write_bytes(b'valid');link=Path(tmp)/'link';link.symlink_to(path)
            with self.assertRaises(ValueError):m.file_identity(link)

    def test_cpu_or_contract_failure_never_dispatches(self):
        with patch.object(m.common,'check_cpu',side_effect=RuntimeError('cpu')),patch.object(m.h,'run_stages') as run:
            with self.assertRaisesRegex(RuntimeError,'cpu'):m.queue()
            run.assert_not_called()
        with patch.object(m.common,'check_cpu'),patch.object(m,'check_contract',side_effect=RuntimeError('adoption')),patch.object(m.h,'run_stages') as run:
            with self.assertRaisesRegex(RuntimeError,'adoption'):m.queue()
            run.assert_not_called()

    def test_failed_probe_cannot_start_diagnostic_or_retry(self):
        with tempfile.TemporaryDirectory() as tmp,patch.object(m,'ROOT',Path(tmp)),\
                patch.object(m.common,'check_cpu'),patch.object(m,'check_contract'),patch.object(m.common,'admit'),\
                patch.object(m.a,'save',side_effect=lambda path,data:path.write_text(json.dumps(data))),\
                patch.object(m.h,'run_stages',side_effect=RuntimeError('probe')) as run:
            root=Path(tmp);(root/'recovery-contract.json').write_text('{}')
            (root/'preparation.json').write_text(json.dumps(dict(status='passed',
                recovery_contract_sha256=m.sha256(root/'recovery-contract.json'))))
            (root/'deployment.json').write_text('{"first_dispatch_by":1e12}')
            with self.assertRaisesRegex(RuntimeError,'probe'):m.queue()
            self.assertEqual(run.call_count,1);self.assertEqual(run.call_args.args[0],['gpu-preflight'])
            clock=json.loads((root/'dispatch.json').read_text())
            self.assertEqual(clock['deadline']-clock['start'],28800)
            self.assertEqual(clock['gpu_hours'],64)
            self.assertEqual(json.loads((root/'queue-state.json').read_text())['phase'],'failed')
            with self.assertRaises(FileExistsError):m.queue()

    def test_diagnostic_rng_mismatch_never_accepts(self):
        with patch.object(m,'rng_at',side_effect=[[{'seed':0}],[{'seed':1}]]),patch.object(m.common,'verify') as verify:
            with self.assertRaisesRegex(RuntimeError,'Diagnostic'):m.verify('diagnostic-cp96')
            verify.assert_not_called()

    def test_selection_pair_mismatch_never_accepts(self):
        with patch.object(m,'rng_at',return_value=[{'seed':0}]),\
                patch.object(m.a,'read',return_value={'rng':[{'seed':1}],'seeds':[]}),patch.object(m.common,'verify') as verify:
            with self.assertRaisesRegex(RuntimeError,'paired RNG'):m.verify('sel-b00-cp32')
            verify.assert_not_called()


if __name__=='__main__':unittest.main()
