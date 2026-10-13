"""Bounded synthetic tests; no actual server, GPU or checkpoint contents."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'experiments/records/20260921-sc2-policy-credit-v1'))
import l7_matrix256197 as m


class MatrixTests(unittest.TestCase):
    def setUp(self):
        guard = patch.dict(vars(m.a),{})
        guard.start(); self.addCleanup(guard.stop)

    def cfg(self):
        arms = {}
        for arm in m.ARMS:
            kind = 'qwen' if arm.startswith('qwen') else 'spb'
            arms[arm] = dict(runtime_sha='test',controller_sha='test',controller_source='/source/code',
                environment={'LONG_DEPENDENCY_PATH':'/deps'},model_kind=kind,model_mount='/assets/'+kind,
                seed_protocol='same_uniform101',seed_group_mode='same',difficulty='VeryHard',
                worker_hook='l7_matrix_hook.install',run_prefix=m.PREFIX,
                host=dict(model='/original-'+kind,venv='/venv',sc2='/sc2',image='fixed-image'))
        return dict(runtime_sha='test',arms=arms,first_dispatch_by=10**12)

    def test_exact_256_no_duplicate_existing_arms(self):
        self.assertEqual(len(m.STAGES),32)
        self.assertEqual(len(set(m.STAGES)),32)
        self.assertNotIn('qwen-same',m.ARMS)
        self.assertNotIn('qwen-original',m.ARMS)
        for arm in m.ARMS:
            specs=[m.stage_spec(s) for s in m.STAGES if m.stage_spec(s)['arm']==arm]
            self.assertEqual([s for spec in specs for s in spec['seeds']],m.SEEDS)
            self.assertEqual(len(specs),8)

    def test_balanced_order(self):
        for arm in m.ARMS:
            for position in range(4):
                self.assertEqual(sum(m.stage_spec(m.STAGES[b*4+position])['arm']==arm for b in range(8)),2)
        with self.assertRaises(ValueError):m.stage_spec('b08-spb-original')
        with self.assertRaises(ValueError):m.stage_spec('train96')

    def test_all_32_invocations(self):
        m.a.ROOT=m.ROOT
        for stage in m.STAGES:
            spec=m.stage_spec(stage);args,env,out=m.invocation(self.cfg(),stage,True)
            opts={x.split('=',1)[0]:x.split('=',1)[1] for x in args if '=' in x}
            self.assertEqual(opts['trainer.val_only'],'True')
            self.assertEqual(opts['trainer.save_freq'],'-1')
            self.assertEqual(opts['+ray_init.runtime_env.worker_process_setup_hook'],'l7_matrix_hook.install')
            self.assertEqual(opts['+ray_init.runtime_env.env_vars.SC2_MATRIX_STAGE'],repr(stage))
            self.assertEqual(env['SC2_CHECKPOINT_RESUME'],'False')
            self.assertEqual(out,m.ROOT/'cpu'/stage)
            self.assertLess(len(env['RAY_TMPDIR']),45)
            self.assertIn('run_qwen_seed_arm.sh' if spec['model']=='qwen' else 'run_seed_group_arm.sh',args[1])
            if spec['checkpoint']:
                self.assertEqual(opts['trainer.resume_from_path'],str(spec['checkpoint']))
            else:
                self.assertEqual(opts['trainer.resume_mode'],'disable')
                self.assertNotIn('trainer.resume_from_path',opts)
            if spec['model']=='spb':
                self.assertEqual(opts['+ray_init.runtime_env.env_vars.SC2_RESET_CONCURRENCY'],"'1'")

    def test_read_only_assets_and_exact_writable_binds(self):
        with patch.object(m,'small',return_value=self.cfg()):
            for stage in m.STAGES:
                args=m.docker('stage',stage)
                self.assertEqual(args[:2],['docker','create'])
                self.assertIn('--read-only',args)
                self.assertIn('--gpus',args)
                self.assertNotIn('--rm',args);self.assertNotIn('--restart',args)
                binds=[args[i+1] for i,x in enumerate(args[:-1]) if x=='-v']
                self.assertEqual([b for b in binds if not b.endswith(':ro')],
                    [f'{m.ROOT}:{m.ROOT}',f'{m.ROOT}/tmp:/tmp'])
                for cp in m.CHECKPOINTS.values():self.assertIn(f'{cp}:{cp}:ro',binds)
                spec=m.stage_spec(stage)
                self.assertIn('/original-'+spec['model']+':/assets/'+spec['model']+':ro',binds)

    def test_cpu_both_metadata_no_gpu(self):
        with patch.object(m,'small',return_value=self.cfg()):args=m.docker('cpu')
        self.assertNotIn('--gpus',args)
        self.assertIn('CUDA_VISIBLE_DEVICES=',args)
        self.assertIn(f'{m.q.CPU_MODEL}:/assets/qwen:ro',args)
        self.assertIn(f'{m.q.SPB_METADATA}:/assets/spb:ro',args)

    def test_budget_and_accounts(self):
        self.assertEqual(m.WALL_SECONDS,28800)
        self.assertEqual(m.LIMIT,32*1024**3)
        self.assertEqual(m.FIRST_DISPATCH_BY,m.PREDECESSOR_DEADLINE+3600)
        self.assertEqual(m.accounts(99),[dict(roots=[m.ROOT,m.SOURCE_PARENT],receipt_root=m.ROOT,
            limit=32*1024**3,deadline=99)])

    def test_prepare_refuses_existing_root(self):
        with tempfile.TemporaryDirectory() as t,patch.object(m,'ROOT',Path(t)):
            with self.assertRaisesRegex(RuntimeError,'New exact roots'):m.prepare()

    def test_predecessor_running_does_not_dispatch(self):
        with patch.object(m,'small',side_effect=[{'phase':'running-unverified'},{'phase':'running-unverified'}]):
            self.assertIsNone(m.predecessor())

    def test_predecessor_failed_is_not_waiting(self):
        with patch.object(m,'small',side_effect=[{'phase':'failed'},{'phase':'completed'}]):
            with self.assertRaisesRegex(RuntimeError,'failed'):m.predecessor()

    def test_queue_failure_is_one_shot(self):
        with tempfile.TemporaryDirectory() as t,patch.object(m,'ROOT',Path(t)), \
                patch.object(m.q,'check_cpu'),patch.object(m.h,'sample'), \
                patch.object(m,'predecessor',return_value={'passed':True}), \
                patch.object(m,'parents',return_value={'passed':True}),patch.object(m,'admit'), \
                patch.object(m.h,'run_stages',side_effect=RuntimeError('stage failed')) as run:
            m.a.STORAGE_LOCK_ROOT=Path(t)
            with self.assertRaisesRegex(RuntimeError,'stage failed'):m.queue()
            dispatch=m.a.read(Path(t)/'dispatch.json')
            self.assertEqual(dispatch['deadline']-dispatch['start'],28800)
            self.assertEqual(dispatch['new_games'],256);self.assertEqual(dispatch['new_updates'],0)
            self.assertEqual(m.a.read(Path(t)/'queue-state.json')['phase'],'failed')
            with self.assertRaisesRegex(RuntimeError,'Already queued'):m.queue()
            self.assertEqual(run.call_count,1)

    def test_predecessor_failure_blocks_dispatch(self):
        with tempfile.TemporaryDirectory() as t,patch.object(m,'ROOT',Path(t)), \
                patch.object(m.q,'check_cpu'),patch.object(m.h,'sample'), \
                patch.object(m,'predecessor',side_effect=RuntimeError('predecessor failed')), \
                patch.object(m,'admit') as admit,patch.object(m.h,'run_stages') as run:
            m.a.STORAGE_LOCK_ROOT=Path(t)
            with self.assertRaisesRegex(RuntimeError,'predecessor failed'):m.queue()
            self.assertFalse((Path(t)/'dispatch.json').exists())
            admit.assert_not_called();run.assert_not_called()

    def verify_fixture(self,stage,changes=None,rng_bad=False):
        spec=m.stage_spec(stage)
        with tempfile.TemporaryDirectory() as t,patch.object(m,'ROOT',Path(t)),patch.object(m,'PREDECESSOR',Path(t)/'old'):
            m.a.STORAGE_LOCK_ROOT=Path(t)
            out=Path(t)/'runs'/stage;out.mkdir(parents=True)
            for name in ('manifest.json','result.json'):(out/name).write_text(json.dumps({'metrics_precision':'binary64-v1'}))
            load=dict(val_only=True,optimizer_updates=0,loaded_global_step=spec['expected_step'],games=8,
                checkpoint=str(spec['checkpoint']) if spec['checkpoint'] else None,
                checkpoint_load_returned=bool(spec['expected_step']),game_seeds=spec['seeds'],
                temperature=0.8,do_sample=True,feedback='0')
            if changes:load.update(changes)
            (out/'checkpoint_evaluation.json').write_text(json.dumps(load))
            (out/'evaluation_seeds.jsonl').write_text(json.dumps({'seeds':spec['seeds']})+'\n')
            outcomes=[dict(env_index=i,terminated=True,truncated=False) for i in range(8)]
            (out/'episode_outcomes.jsonl').write_text('\n'.join(map(json.dumps,outcomes)))
            rng=[dict(rank=i,seed=i,cpu_rng_sha256='cpu'+str(i),cuda_rng_sha256='gpu'+str(i)) for i in range(8)]
            for i,r in enumerate(rng):(out/f'sampling-rank{i}.json').write_text(json.dumps(r))
            if spec['model']=='qwen':
                (Path(t)/'old').mkdir()
                for arm in ('original','cp96'):
                    (Path(t)/f'old/acceptance-b{spec["batch"]:02d}-{arm}.json').write_text(
                        json.dumps({'rng':[] if rng_bad else rng,'seeds':spec['seeds']}))
            elif rng_bad:
                other='spb-original' if spec['arm']!='spb-original' else 'spb-same'
                (Path(t)/f'acceptance-b{spec["batch"]:02d}-{other}.json').write_text(json.dumps({'rng':[],'seeds':spec['seeds']}))
            with patch.object(m.a,'verify_common',return_value=({'training_updates':0},{})):m.verify(stage)
            self.assertTrue((Path(t)/f'acceptance-{stage}.json').exists())

    def test_valid_each_arm(self):
        for arm in m.ARMS:self.verify_fixture('b00-'+arm)

    def test_wrong_cp_or_load_or_seeds_updates_fail(self):
        for changes in [dict(checkpoint='/old/global_step_96'),dict(checkpoint_load_returned=False),
                dict(optimizer_updates=1),dict(game_seeds=[0]*8),dict(feedback='1'),dict(temperature=0.4)]:
            with self.subTest(changes=changes),self.assertRaisesRegex(RuntimeError,'load/seed'):
                self.verify_fixture('b00-spb-same',changes)

    def test_original_cannot_load_trained_weights(self):
        with self.assertRaisesRegex(RuntimeError,'load/seed'):
            self.verify_fixture('b00-spb-original',dict(loaded_global_step=96))

    def test_qwen_rng_matches_reused_arms(self):
        with self.assertRaisesRegex(RuntimeError,'paired RNG'):
            self.verify_fixture('b00-qwen-random',rng_bad=True)

    def test_spb_rng_matches_other_spb(self):
        with self.assertRaisesRegex(RuntimeError,'paired RNG'):
            self.verify_fixture('b00-spb-random',rng_bad=True)

    def test_small_file_limit(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'large.json';p.touch()
            with p.open('wb') as f:f.truncate(8*1024**2+1)
            with self.assertRaisesRegex(RuntimeError,'too large'):m.small(p)
            with self.assertRaisesRegex(RuntimeError,'too large'):m.digest(p)


if __name__=='__main__':unittest.main()
