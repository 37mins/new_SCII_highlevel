"""Real small-file publication/pruning faults; no server/GPU/large weights."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'experiments/records/20260921-sc2-policy-credit-v1'))
import qwen_l8random_retention as r
READERS_CLEAR=r.readers_clear


class RetentionTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        root=Path(self.tmp.name).resolve()/'new-r2';root.mkdir()
        for module in (r,r.a,r.receipts):
            p=patch.dict(vars(module),{});p.start();self.addCleanup(p.stop)
        r.ROOT=root;r.SELECTION_ROOT=root/'selection';r.SELECTION_ROOT.mkdir()
        r.SELECTION_CHECKPOINTS={'cp'+str(s):root/r.PARTS[0 if s==2 else 1]/
            ('runs/train2' if s==2 else 'runs/train96')/f'checkpoints/global_step_{s}' for s in r.SAVED_STEPS}
        self.write(root/'deployment.json',dict(runtime_sha='test'))
        for step,cp in [(s,r.SELECTION_CHECKPOINTS['cp'+str(s)]) for s in r.SAVED_STEPS]:
            for name in r.checkpoint_names():
                p=cp/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b'small fixture '+str(step).encode())
        for index in (0,1):
            owner=root/r.PARTS[index];stage='train2' if index==0 else 'train96';steps=[2] if index==0 else [32,64,96]
            result=dict(status='completed',process_exit_code=0)
            self.write(owner/f'acceptance-{stage}.json',dict(result=result))
            self.write(owner/f'runs/{stage}/result.json',result);self.write(owner/f'runs/{stage}/.done',result)
            self.write(owner/'dispatch.json',dict(deadline=time.time()+3600))
            inv={}
            for s in steps:
                inv.update({f'checkpoints/global_step_{s}/'+n:v for n,v in r.inventory(r.SELECTION_CHECKPOINTS['cp'+str(s)]).items()})
            self.write(owner/'checkpoint-readiness.json',dict(passed=True,cuda_initialized=False,
                runtime_sha='test',steps=steps,inventory=inv))
        for name in ('terminal_container','validate_terminal'):
            p=patch.object(r.receipts,name);p.start();self.addCleanup(p.stop)
        p=patch.object(r,'readers_clear');self.readers=p.start();self.addCleanup(p.stop)
        self.write(r.SELECTION_ROOT/'dispatch.json',dict(deadline=time.time()+3600))

    def write(self,path,value):
        path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value))

    def publish_all(self):
        r.publish(0);r.publish(1);r.require_published()

    def selection(self,scores):
        for arm,wins in zip(r.SELECTION_ARMS,scores):
            remaining=wins
            for batch in range(4):
                stage=f'b{batch:02d}-{arm}';n=min(remaining,8);remaining-=n
                result=dict(status='completed',process_exit_code=0,training_updates=0,
                    episode_outcomes=dict(natural_games=8,truncated=0,wins=n))
                self.write(r.SELECTION_ROOT/f'runs/{stage}/result.json',result)
                self.write(r.SELECTION_ROOT/f'runs/{stage}/.done',result)
                self.write(r.SELECTION_ROOT/f'acceptance-{stage}.json',dict(result=result,
                    seeds=r.SELECTION_SEEDS[batch*8:batch*8+8]))
            r.update_best(arm)

    def test_real_publication_latest_and_no_repeat(self):
        self.publish_all();self.assertEqual(r.a.read(r.ROOT/'retention/latest.json')['step'],96)
        with self.assertRaisesRegex(RuntimeError,'already published'):r.publish(1)

    def test_failed_state_gate_or_missing_shard_never_publishes(self):
        owner=r.ROOT/r.PARTS[0];p=owner/'checkpoint-readiness.json'
        cfg=r.a.read(p);cfg['passed']=False;self.write(p,cfg)
        with self.assertRaisesRegex(RuntimeError,'gate required'):r.publish(0)
        self.assertFalse((r.ROOT/'retention/cp2.json').exists())
        cfg['passed']=True;self.write(p,cfg)
        (r.SELECTION_CHECKPOINTS['cp2']/r.checkpoint_names()[0]).unlink()
        with self.assertRaises(ValueError):r.publish(0)

    def test_symlink_file_ancestor_and_outside_paths_rejected(self):
        cp=r.SELECTION_CHECKPOINTS['cp32'];p=cp/r.checkpoint_names()[0]
        p.unlink();p.symlink_to(__file__)
        with self.assertRaises(ValueError):r.inventory(cp)
        with self.assertRaises(ValueError):r.inventory(r.ROOT.parent)

    def test_publish_fsync_failure_no_complete_marker(self):
        with patch.object(r.os,'fsync',side_effect=OSError('fsync fault')):
            with self.assertRaises(OSError):r.publish(0)
        self.assertFalse((r.ROOT/'retention/cp2.json').exists())

    def test_ties_keep_earliest_and_best_never_uses_test(self):
        self.publish_all();self.selection([20,20,20,20])
        p=r.a.read(r.ROOT/'retention/best.json')
        self.assertEqual(p['best']['step'],2);self.assertFalse(p['test_used'])
        self.assertEqual(r.retained_steps(32),[2,32,64,96])
        self.assertEqual(r.retained_steps(96),[2,64,96])

    def test_best32_keeps_all_no_copy_no_delete(self):
        self.publish_all();self.selection([10,25,20,24]);r.prune()
        self.assertEqual(r.a.read(r.ROOT/'retention/prune-receipt.json')['removed'],[])
        self.assertTrue(all(p.exists() for p in r.SELECTION_CHECKPOINTS.values()))

    def test_prune_only_own32_preserves_metrics_old_and_protected(self):
        self.publish_all();self.selection([10,15,20,25])
        old=r.ROOT.parent/'old-cp32';old.mkdir();(old/'keep').write_text('old')
        metric=r.SELECTION_CHECKPOINTS['cp32'].parent/'metrics.json';metric.write_text('keep')
        r.prune()
        self.assertFalse(r.SELECTION_CHECKPOINTS['cp32'].exists())
        self.assertTrue(old.exists());self.assertTrue(metric.exists())
        r.require_published([2,64,96])
        self.assertTrue((r.ROOT/'retention/cp32.json').exists())
        with self.assertRaisesRegex(RuntimeError,'no retry'):r.prune()

    def test_incomplete_validation_never_prunes_or_changes_best(self):
        self.publish_all();self.selection([10,15,20,25])
        p=r.SELECTION_ROOT/'acceptance-b03-cp96.json';p.unlink()
        with self.assertRaises(FileNotFoundError):r.prune()
        self.assertTrue(r.SELECTION_CHECKPOINTS['cp32'].exists())

    def test_active_reader_and_changed_inventory_block_deletion(self):
        self.publish_all();self.selection([10,15,20,25]);self.readers.side_effect=RuntimeError('active reader')
        with self.assertRaisesRegex(RuntimeError,'active reader'):r.prune()
        self.assertTrue(r.SELECTION_CHECKPOINTS['cp32'].exists())
        self.readers.side_effect=None
        (r.SELECTION_CHECKPOINTS['cp32']/r.checkpoint_names()[0]).write_bytes(b'changed')
        with self.assertRaisesRegex(RuntimeError,'changed'):r.prune()

    def test_readonly_reader_mount_is_also_protected(self):
        for source in (r.ROOT,r.ROOT.parent,r.SELECTION_CHECKPOINTS['cp32']):
            with patch.object(r.a,'cmd',side_effect=['exact-container',json.dumps([{'Source':str(source),'RW':False}])]):
                with self.assertRaisesRegex(RuntimeError,'reader/writer'):READERS_CLEAR()
        with patch.object(r.a,'cmd',side_effect=['unrelated',json.dumps([{'Source':str(r.ROOT.parent/'old-r1'),'RW':True}])]):
            READERS_CLEAR()

    def test_unlink_failure_has_intent_and_never_retries(self):
        self.publish_all();self.selection([10,15,20,25])
        with patch.object(Path,'unlink',side_effect=OSError('unlink fault')):
            with self.assertRaises(OSError):r.prune()
        self.assertTrue((r.ROOT/'retention/prune-intent.json').exists())
        self.assertFalse((r.ROOT/'retention/prune-receipt.json').exists())
        with self.assertRaisesRegex(RuntimeError,'no retry'):r.prune()

    def test_best_tamper_rejected(self):
        self.publish_all();self.selection([10,15,20,25])
        p=r.ROOT/'retention/best.json';v=r.a.read(p);v['best']['step']=32;self.write(p,v)
        with self.assertRaisesRegex(RuntimeError,'mismatch'):r.prune()


if __name__=='__main__':unittest.main()
