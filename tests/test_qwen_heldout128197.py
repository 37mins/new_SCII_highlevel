"""Synthetic approval, pairing and fail-closed tests; no real GPU/server writes."""
import copy
import json
from pathlib import Path
import random
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'experiments/records/20260921-sc2-policy-credit-v1'))
import qwen_heldout128197 as m
from qwen_heldout_plan import SEEDS, STAGES, stage_spec
from acceptance_hook import EVAL_SEEDS


class HeldoutTests(unittest.TestCase):
    def setUp(self):
        guard = patch.dict(vars(m.a),{})
        guard.start(); self.addCleanup(guard.stop)

    def cfg(self):
        return dict(runtime_sha='test',controller_sha='test',controller_source='/source/code',
            environment={'LONG_DEPENDENCY_PATH':'/deps'}, model_kind='qwen',model_mount='/assets/qwen',
            seed_protocol='same_uniform101',seed_group_mode='same',difficulty='VeryHard',
            worker_hook='qwen_heldout_hook.install',run_prefix=m.PREFIX,stages=STAGES,
            host=dict(model='/original-qwen',venv='/venv',sc2='/sc2',image='fixed-image'),
            first_dispatch_by=10**12)

    def test_frozen_seeds(self):
        self.assertEqual(SEEDS,random.Random(20260924).sample(range(65536,2**32-1),64))
        self.assertEqual(len(set(SEEDS)),64)
        self.assertFalse(set(SEEDS)&set(EVAL_SEEDS))
        self.assertTrue(all(s>100 for s in SEEDS))

    def test_exact_pair_and_balanced_order(self):
        self.assertEqual(len(STAGES),16)
        for b in range(8):
            first,second=STAGES[2*b:2*b+2]
            self.assertEqual(stage_spec(first)['seeds'],stage_spec(second)['seeds'])
            self.assertEqual(stage_spec(first)['arm'],'original' if b%2==0 else 'cp96')
        with self.assertRaises(ValueError): stage_spec('b08-original')
        with self.assertRaises(ValueError): stage_spec('train96')

    def test_all_invocations_are_evaluation_and_exact_checkpoint(self):
        m.a.ROOT=m.ROOT
        for stage in STAGES:
            args,env,out=m.invocation(self.cfg(),stage,True)
            effective={x.split('=',1)[0]:x.split('=',1)[1] for x in args if '=' in x}
            self.assertEqual(effective['trainer.val_only'],'True')
            self.assertEqual(effective['trainer.save_freq'],'-1')
            self.assertEqual(effective['+ray_init.runtime_env.worker_process_setup_hook'],'qwen_heldout_hook.install')
            self.assertEqual(out,m.ROOT/'cpu'/stage)
            self.assertEqual(env['SC2_CHECKPOINT_RESUME'],'False')
            self.assertLess(len(env['RAY_TMPDIR']),40)
            if stage.endswith('cp96'):
                self.assertEqual(effective['trainer.resume_from_path'],str(m.CHECKPOINT))
            else:
                self.assertNotIn('trainer.resume_from_path',effective)
                self.assertEqual(effective['trainer.resume_mode'],'disable')

    def test_read_only_ancestor_and_cpu_no_gpu(self):
        m.a.ROOT=m.ROOT; m.a.DOCKER_SCRIPT=m.a.HERE/'qwen_heldout128197.py'
        with patch.object(m.a,'read',return_value=self.cfg()):
            gpu=m.docker('stage',STAGES[0]); cpu=m.docker('cpu')
        self.assertEqual(gpu[:2],['docker','create'])
        self.assertIn('--read-only',gpu)
        self.assertIn(f'{m.CHECKPOINT}:{m.CHECKPOINT}:ro',gpu)
        self.assertNotIn('--gpus',cpu)
        self.assertIn('CUDA_VISIBLE_DEVICES=',cpu)
        self.assertIn(f'{m.CPU_MODEL}:/assets/qwen:ro',cpu)
        self.assertNotIn('--restart',gpu)

    def test_only_new_roots_and_budget(self):
        self.assertEqual(m.WALL_SECONDS,6*3600)
        self.assertEqual(m.LIMIT,32*1024**3)
        self.assertEqual(m.accounts(123),[dict(roots=[m.ROOT,m.SOURCE_PARENT],
            receipt_root=m.ROOT,limit=32*1024**3,deadline=123)])

    def test_prepare_refuses_existing_root(self):
        with tempfile.TemporaryDirectory() as t,patch.object(m,'ROOT',Path(t)):
            with self.assertRaisesRegex(RuntimeError,'New exact roots'): m.prepare()

    def test_queue_failure_blocks_successors_and_second_dispatch(self):
        with tempfile.TemporaryDirectory() as t,patch.object(m,'ROOT',Path(t)), \
                patch.object(m,'check_cpu'),patch.object(m,'predecessor',return_value={'passed':True}), \
                patch.object(m,'admit'),patch.object(m.h,'run_stages',side_effect=RuntimeError('failed')) as run:
            m.a.STORAGE_LOCK_ROOT=Path(t)
            m.a.save(Path(t)/'deployment.json',self.cfg())
            with self.assertRaisesRegex(RuntimeError,'failed'): m.queue()
            dispatch=m.a.read(Path(t)/'dispatch.json')
            self.assertEqual(dispatch['deadline']-dispatch['start'],21600)
            self.assertEqual(run.call_count,1)
            self.assertEqual(m.a.read(Path(t)/'queue-state.json')['phase'],'failed')
            with self.assertRaisesRegex(RuntimeError,'Already queued'): m.queue()
            self.assertEqual(run.call_count,1)

    def test_predecessor_failure_never_dispatches(self):
        with tempfile.TemporaryDirectory() as t,patch.object(m,'ROOT',Path(t)), \
                patch.object(m,'check_cpu'),patch.object(m,'predecessor',side_effect=RuntimeError('parent')), \
                patch.object(m,'admit') as admit,patch.object(m.h,'run_stages') as run:
            m.a.STORAGE_LOCK_ROOT=Path(t)
            with self.assertRaisesRegex(RuntimeError,'parent'): m.queue()
            self.assertFalse((Path(t)/'dispatch.json').exists())
            admit.assert_not_called(); run.assert_not_called()

    def fixture(self,stage):
        spec=stage_spec(stage)
        return dict(loaded_global_step=spec['expected_step'],games=8,game_seeds=spec['seeds'],
            checkpoint=str(m.CHECKPOINT) if spec['expected_step'] else None,
            checkpoint_load_returned=bool(spec['expected_step']),val_only=True,optimizer_updates=0)

    def run_verify(self,stage,mutate=None,paired_rng=None):
        spec=stage_spec(stage)
        with tempfile.TemporaryDirectory() as t,patch.object(m,'ROOT',Path(t)):
            m.a.STORAGE_LOCK_ROOT=Path(t)
            out=Path(t)/'runs'/stage;out.mkdir(parents=True)
            for name in ('result.json','manifest.json'):
                (out/name).write_text(json.dumps({'metrics_precision':'binary64-v1'}))
            proof=self.fixture(stage)
            if mutate: proof.update(mutate)
            (out/'checkpoint_evaluation.json').write_text(json.dumps(proof))
            (out/'evaluation_seeds.jsonl').write_text(json.dumps({'seeds':spec['seeds']})+'\n')
            outcomes=[dict(env_index=i,terminated=True,truncated=False,game_result='Victory') for i in range(8)]
            (out/'episode_outcomes.jsonl').write_text('\n'.join(map(json.dumps,outcomes)))
            for rank in range(8):
                (out/f'sampling-rank{rank}.json').write_text(json.dumps(dict(rank=rank,seed=rank,
                    cpu_rng_sha256='cpu'+str(rank),cuda_rng_sha256='gpu'+str(rank))))
            if paired_rng is not None:
                other=f'b{spec["batch"]:02d}-'+('original' if spec['expected_step'] else 'cp96')
                (Path(t)/f'acceptance-{other}.json').write_text(json.dumps({'rng':paired_rng}))
            with patch.object(m.a,'verify_common',return_value=({'training_updates':0},{})):
                m.verify(stage)
            self.assertTrue((Path(t)/f'acceptance-{stage}.json').exists())

    def test_valid_original_and_cp96_proofs(self):
        self.run_verify('b00-original'); self.run_verify('b00-cp96')

    def test_wrong_load_or_updates_or_seeds_rejected(self):
        for bad in [dict(checkpoint='/old/global_step_96'),dict(optimizer_updates=1),
                    dict(checkpoint_load_returned=False),dict(game_seeds=EVAL_SEEDS)]:
            with self.subTest(bad=bad), self.assertRaisesRegex(RuntimeError,'load/seeds'):
                self.run_verify('b00-cp96',bad)

    def test_mismatched_pair_rng_rejected(self):
        with self.assertRaisesRegex(RuntimeError,'RNG mismatch'):
            self.run_verify('b00-cp96',paired_rng=[])

    def test_stale_cpu_sha_refused(self):
        cfg=self.cfg()
        with patch.object(m.a,'clean'),patch.object(m.a,'read',
                side_effect=[cfg,dict(passed=True,cuda_initialized=False,runtime_sha='old')]):
            with self.assertRaisesRegex(RuntimeError,'CPU proof'):m.check_cpu()


if __name__=='__main__':
    unittest.main()
