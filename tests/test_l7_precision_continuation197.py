"""CPU-only boundaries for explicitly approved CP96 eval and replacement queue."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

REC = Path(__file__).resolve().parents[1]/'experiments/records/20260921-sc2-policy-credit-v1'
sys.path.insert(0,str(REC))
import qwen_l7_eval96_197 as e
import l7_followup197_r3 as r


class ContinuationTests(unittest.TestCase):
    def config(self):
        return dict(environment={'LONG_DEPENDENCY_PATH':'/deps'},model_kind='qwen',
            model_mount='/assets/qwen',difficulty='VeryHard',run_prefix='eval',
            seed_protocol='same_uniform101',seed_group_mode='same',worker_hook='qwen_l7_long_hook.install')

    def test_only_existing_cp96_evaluation_never_training(self):
        with patch.object(e.a,'ROOT',e.ROOT):
            args,env,out=e.invocation(self.config(),'eval96',True)
        values=dict(x.split('=',1) for x in args if '=' in x)
        self.assertEqual(values['trainer.resume_from_path'],str(e.CHECKPOINT))
        self.assertEqual(values['trainer.val_only'],'True')
        self.assertEqual(values['trainer.save_freq'],'-1')
        self.assertEqual(values['trainer.total_epochs'],'1')
        self.assertEqual(values['trainer.total_training_steps'],'96')
        self.assertEqual(env['SC2_CHECKPOINT_RESUME'],'False')
        self.assertEqual(out,e.ROOT/'cpu/eval96')
        self.assertEqual(values['+ray_init.runtime_env.env_vars.SC2_ACCEPTANCE_STAGE'],"'eval96'")
        for stage in ('pre','train2','train96','post'):
            with self.assertRaises(ValueError): e.invocation(self.config(),stage)

    def test_original_deadline_and_all_five_roots_required(self):
        self.assertEqual(e.DEADLINE,1790227126.5133374)
        with patch.object(e.a,'measure_budget') as measure:
            e.budget(e.DEADLINE)
        self.assertEqual(measure.call_args.args[0],e.storage_roots())
        self.assertEqual(measure.call_args.args[2],1024**4)
        self.assertEqual(len(e.storage_roots()),5)
        with self.assertRaisesRegex(RuntimeError,'reset'):e.budget(e.DEADLINE+1)

    def test_recorder_has_final_cp_only_intermediates_still_require_all_files(self):
        with tempfile.TemporaryDirectory() as tmp,patch.object(e,'HISTORY',Path(tmp)):
            result={'checkpoint_files':{}}
            names=['data.pt','sc2_state.pt']+[f'actor/{k}_world_size_8_rank_{r}.pt'
                for k in ('model','optim','extra_state') for r in range(8)]
            for step in range(8,97,8):
                for name in names:
                    relative=f'checkpoints/global_step_{step}/{name}'
                    path=e.HISTORY/'runs/train96'/relative
                    path.parent.mkdir(parents=True,exist_ok=True)
                    path.write_bytes(b'fixture')
                    if step==96:result['checkpoint_files'][relative]={'bytes':7}
            e.checkpoint_inventory(result)
            file=e.HISTORY/'runs/train96/checkpoints/global_step_8/data.pt'
            file.write_bytes(b'')
            with self.assertRaisesRegex(RuntimeError,'inventory'):e.checkpoint_inventory(result)
            file.write_bytes(b'fixture')
            result['checkpoint_files']['checkpoints/global_step_96/data.pt']['bytes']=8
            with self.assertRaisesRegex(RuntimeError,'inventory'):e.checkpoint_inventory(result)

    def test_prepare_cannot_reuse_historical_or_new_root(self):
        with tempfile.TemporaryDirectory() as tmp,patch.object(e,'ROOT',Path(tmp)):
            with self.assertRaisesRegex(RuntimeError,'Fresh'):e.prepare()

    def test_any_historical_receipt_drift_rejected_before_dispatch(self):
        frozen={'receipts':{str(e.HISTORY/'state.json'):{'sha256':'unchanged'}}}
        with patch.object(e.a,'read',return_value=frozen),patch.object(Path,'stat') as stat,patch.object(e,'sha256',return_value='different'):
            stat.return_value.st_size=100
            with self.assertRaisesRegex(RuntimeError,'Historical receipt changed'):e.history_evidence()

    def test_replacement_retains_both_failed_preparations(self):
        self.assertEqual(len(r.RETAINED),4)
        self.assertIn(Path('/var/jfsCache/sc2-l7-followup197-20260922-r2'),r.RETAINED)
        self.assertNotEqual(r.ROOT,Path('/var/jfsCache/sc2-l7-followup197-20260922-r2'))
        self.assertEqual(r.f.FIRST_DISPATCH_BY,1790230726.5133374)
        self.assertEqual(r.f.ARM_SECONDS,48*3600)

    def test_new_predecessor_host_failure_overrules_stale_child(self):
        with patch.object(r.a,'read',return_value={'phase':'failed'}):
            with self.assertRaisesRegex(RuntimeError,'evaluation failed'):r.predecessor_complete()
        with patch.object(r.a,'read',return_value={'phase':'dispatched'}):
            self.assertFalse(r.predecessor_complete())

    def test_completion_without_exact_eval_stage_or_deadline_rejected(self):
        queue={'phase':'completed','exit_code':0}
        state={'phase':'completed','exit_code':0,'completed':['train96','eval96'],'deadline':e.DEADLINE}
        with patch.object(r.a,'read',side_effect=[queue,state]):
            with self.assertRaisesRegex(RuntimeError,'terminal mismatch'):r.predecessor_complete()

    def test_completed_child_without_successful_container_rejected(self):
        queue={'phase':'completed','exit_code':0}
        state={'phase':'completed','exit_code':0,'completed':['eval96'],'deadline':e.DEADLINE}
        with patch.object(r.a,'read',side_effect=[queue,state]),patch.object(r.a,'cmd',return_value=json.dumps({'Running':True,'ExitCode':0})):
            with self.assertRaisesRegex(RuntimeError,'successfully exited'):r.predecessor_complete()

    def test_new_stage_rejects_legacy_precision_without_entering_old_verifier(self):
        with patch.object(r.a,'read',return_value={'metrics_precision':'legacy-console-unverified'}),patch.object(r,'BASE_VERIFY') as verifier:
            with self.assertRaisesRegex(RuntimeError,'Full-precision'):r.verify('train96')
            verifier.assert_not_called()


if __name__=='__main__':unittest.main()
