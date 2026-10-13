"""Synthetic L8 approval, pairing and one-shot guards; no GPU/server writes."""
import json
from pathlib import Path
import random
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'experiments/records/20260921-sc2-policy-credit-v1'))
import qwen_l8_pilot197 as m
from qwen_l8_plan import ARMS, CHECKPOINTS, SEEDS, STAGES, stage_spec
from qwen_heldout_plan import SEEDS as L7_SEEDS


class L8PilotTests(unittest.TestCase):
    def setUp(self):
        guard = patch.dict(vars(m.a),{})
        guard.start(); self.addCleanup(guard.stop)

    def cfg(self):
        arm = dict(environment={'LONG_DEPENDENCY_PATH':'/deps'},model_kind='qwen',
            model_mount='/assets/qwen',seed_protocol='same_uniform101',seed_group_mode='same',
            difficulty='CheatVision',worker_hook='qwen_l8_hook.install',run_prefix=m.PREFIX,
            host=dict(model='/original-qwen',venv='/venv',sc2='/sc2',image='fixed-image'))
        return dict(runtime_sha='test',arms={x:arm for x in ARMS},first_dispatch_by=10**12)

    def test_new_32_seeds_and_balanced_stage_order(self):
        self.assertEqual(SEEDS,random.Random(20260925).sample(range(65536,2**32-1),32))
        self.assertEqual(len(set(SEEDS)),32)
        self.assertFalse(set(SEEDS)&set(L7_SEEDS))
        self.assertEqual(len(STAGES),12)
        for b in range(4):
            stages=STAGES[3*b:3*b+3]
            self.assertEqual([stage_spec(s)['arm'] for s in stages],list(ARMS[b%3:]+ARMS[:b%3]))
            self.assertEqual([stage_spec(s)['seeds'] for s in stages],[SEEDS[8*b:8*(b+1)]]*3)
        with self.assertRaises(ValueError):stage_spec('b04-original')

    def test_invocations_use_l8_no_update_and_own_cp(self):
        m.a.ROOT=m.ROOT
        for stage in STAGES:
            args,env,out=m.invocation(self.cfg(),stage,True)
            eff={x.split('=',1)[0]:x.split('=',1)[1] for x in args if '=' in x}
            spec=stage_spec(stage)
            self.assertEqual(out,m.ROOT/'cpu'/stage)
            self.assertEqual(env['SC2_DIFFICULTY'],'CheatVision')
            self.assertEqual(eff['trainer.val_only'],'True')
            self.assertEqual(eff['trainer.save_freq'],'-1')
            self.assertEqual(eff['+ray_init.runtime_env.worker_process_setup_hook'],'qwen_l8_hook.install')
            self.assertEqual(eff['trainer.resume_mode'],'resume_path' if spec['checkpoint'] else 'disable')
            if spec['checkpoint']:
                self.assertEqual(eff['trainer.resume_from_path'],str(spec['checkpoint']))
            else:self.assertNotIn('trainer.resume_from_path',eff)

    def test_read_only_ancestor_and_cpu_no_gpu(self):
        m.a.DOCKER_SCRIPT=m.a.HERE/'qwen_l8_pilot197.py'
        with patch.object(m.matrix,'small',return_value=self.cfg()):
            gpu=m.docker('stage',STAGES[0]); cpu=m.docker('cpu')
        self.assertEqual(gpu[:2],['docker','create'])
        self.assertIn('--read-only',gpu)
        for cp in CHECKPOINTS.values(): self.assertIn(f'{cp}:{cp}:ro',gpu)
        self.assertNotIn('--gpus',cpu)
        self.assertIn('CUDA_VISIBLE_DEVICES=',cpu)
        self.assertNotIn('--restart',gpu)

    def test_exact_budget_and_roots(self):
        self.assertEqual(m.WALL_SECONDS,4*3600)
        self.assertEqual(m.LIMIT,32*1024**3)
        self.assertEqual(m.accounts(123),[dict(roots=[m.ROOT,m.SOURCE_PARENT],
            receipt_root=m.ROOT,limit=32*1024**3,deadline=123)])

    def test_prepare_refuses_existing_root(self):
        with tempfile.TemporaryDirectory() as tmp,patch.object(m,'ROOT',Path(tmp)):
            with self.assertRaisesRegex(RuntimeError,'New exact roots'):m.prepare()

    def test_failed_queue_never_retries(self):
        with tempfile.TemporaryDirectory() as tmp,patch.object(m,'ROOT',Path(tmp)), \
                patch.object(m,'check_cpu'),patch.object(m,'parents',return_value={'passed':True}), \
                patch.object(m,'admit'),patch.object(m.h,'run_stages',side_effect=RuntimeError('failed')) as run:
            m.a.STORAGE_LOCK_ROOT=Path(tmp)
            m.a.save(Path(tmp)/'deployment.json',self.cfg())
            with self.assertRaisesRegex(RuntimeError,'failed'):m.queue()
            dispatch=m.a.read(Path(tmp)/'dispatch.json')
            self.assertEqual(dispatch['deadline']-dispatch['start'],4*3600)
            self.assertEqual(dispatch['new_games'],96)
            self.assertEqual(run.call_count,1)
            self.assertEqual(m.a.read(Path(tmp)/'queue-state.json')['phase'],'failed')
            with self.assertRaisesRegex(RuntimeError,'Already queued'):m.queue()

    def test_bad_parent_never_dispatches(self):
        with tempfile.TemporaryDirectory() as tmp,patch.object(m,'ROOT',Path(tmp)), \
                patch.object(m,'check_cpu'),patch.object(m,'parents',side_effect=RuntimeError('parent')), \
                patch.object(m,'admit') as admit,patch.object(m.h,'run_stages') as run:
            m.a.STORAGE_LOCK_ROOT=Path(tmp)
            with self.assertRaisesRegex(RuntimeError,'parent'):m.queue()
            self.assertFalse((Path(tmp)/'dispatch.json').exists())
            admit.assert_not_called();run.assert_not_called()


if __name__=='__main__':unittest.main()
