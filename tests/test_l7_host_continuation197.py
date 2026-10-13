"""New-run integration gates, no GPU/SC2 imports or dispatches."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

REC=Path(__file__).resolve().parents[1]/'experiments/records/20260921-sc2-policy-credit-v1'
sys.path.insert(0,str(REC))
import l7_followup197_r4 as r


class HostContinuationTests(unittest.TestCase):
    def test_fixed_original_clocks_and_extra_eight_slots(self):
        self.assertEqual(r.SPB_DEADLINE-r.ORIGINAL_START,48*3600)
        self.assertEqual(r.SUITE_DEADLINE-r.ORIGINAL_START,96*3600)
        self.assertEqual(r.f.PARTS,('spb-same/short','spb-same/long','qwen-random/long'))

    def test_inclusive_accounting_keeps_failed_sources_and_cpu_fixtures(self):
        for index in range(3):
            result=r.accounts(index,r.SPB_DEADLINE)
            self.assertEqual(result[0]['limit'],1024**4)
            self.assertEqual(result[1]['limit'],2*1024**4)
            self.assertEqual(result[1]['deadline'],r.SUITE_DEADLINE)
            self.assertTrue(set(r.RETAINED)<=set(result[0]['roots']))
            self.assertTrue(set(r.RETAINED)<=set(result[1]['roots']))
            self.assertEqual(len(result[1]['roots']),11)
            self.assertEqual(r.f.RANDOM_PARENT in result[0]['roots'],index==2)

    def command(self,index=0):
        root=r.ROOT/r.f.PARTS[index]
        return ['docker','run','--name','new','-v',f'{r.ROOT}:{r.ROOT}',
            '-v',f'{r.ROOT}/.storage.lock:{r.ROOT}/.storage.lock',
            '-v',f'{root}:{root}','-v',f'{root}/tmp:/tmp',
            '-v','/asset:/asset:ro','image','-B','controller','cpu','0']

    def test_bind_contract_has_only_accounted_writers(self):
        with patch.object(r,'BASE_DOCKER',return_value=self.command()):
            args=r.docker('execute',0)
        self.assertIn('--read-only',args)
        self.assertEqual(args[args.index('--log-driver')+1],'none')
        self.assertIn(f'{r.ROOT}:{r.ROOT}:ro',args)
        self.assertIn('HOME=/tmp/task-home',args)
        self.assertIn('/asset:/asset:ro',args)

    def test_unaccounted_bind_refused(self):
        args=self.command();args[2:2]=['-v','/outside:/outside']
        with patch.object(r,'BASE_DOCKER',return_value=args):
            with self.assertRaisesRegex(RuntimeError,'Unaccounted'):r.docker('execute',0)

    def test_old_failure_is_not_restarted(self):
        self.assertNotEqual(r.ROOT,r.old.ROOT)
        self.assertIn(r.old.ROOT,r.RETAINED)
        with tempfile.TemporaryDirectory() as tmp,patch.object(r.f,'SUITE',Path(tmp)):
            with self.assertRaisesRegex(RuntimeError,'Fresh'):r.prepare()

    def test_original_deadline_blocks_admission_before_sampling_or_gpu(self):
        with patch.object(r.time,'time',return_value=r.SPB_DEADLINE),patch.object(r.h,'sample') as sample:
            with self.assertRaises(TimeoutError):r.admit(0,'pre',r.SPB_DEADLINE)
        sample.assert_not_called()

    def test_stage_failure_blocks_later_parts_without_clock_reset(self):
        with tempfile.TemporaryDirectory() as tmp,patch.object(r,'ROOT',Path(tmp)):
            root=Path(tmp)
            for part in r.f.PARTS:(root/part).mkdir(parents=True)
            with patch.object(r,'check_cpu'),patch.object(r.old,'predecessor_complete',return_value=True),\
                 patch.object(r.a,'cmd',return_value=json.dumps(dict(Running=False,Paused=False))),\
                 patch.object(r.f,'select'),patch.object(r.a,'ROOT',root/r.f.PARTS[0]),patch.object(r,'admit'),\
                 patch.object(r.h,'supervise_part',side_effect=RuntimeError('fixture failure')) as run:
                with self.assertRaisesRegex(RuntimeError,'fixture failure'):r.queue()
            self.assertEqual(run.call_count,1)
            self.assertEqual(r.a.read(root/'queue-state.json')['phase'],'failed')
            self.assertEqual(r.a.read(root/'dispatch.json')['deadline'],r.SUITE_DEADLINE)
            self.assertFalse((root/r.f.PARTS[1]/'dispatch.json').exists())
            with patch.object(r,'check_cpu'):
                with self.assertRaisesRegex(RuntimeError,'Already'):r.queue()


if __name__=='__main__':unittest.main()
