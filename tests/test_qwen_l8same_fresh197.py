"""L8 fresh authorization, native prefix, exact environment and fail-close tests."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] /
    'experiments/records/20260921-sc2-policy-credit-v1'))
import qwen_l8same_fresh197 as m
from test_qwen_l7same_fresh197 import QwenNativeContractTests
from agent_system.sc2_policy_resume import sha256, verify_contract


class L8ContractTests(QwenNativeContractTests):
    def test_l8_contract_is_not_l7_or_legacy(self):
        c = self.native_qwen()
        c['version'] = 'accepted-qwen-l8-same-full-state-prefix-v1'
        with self.assertRaisesRegex(ValueError, 'model/protocol'): verify_contract(c)
        path = self.parent / 'deployment.json'
        cfg = json.loads(path.read_text()); cfg['difficulty'] = 'CheatVision'
        path.write_text(json.dumps(cfg))
        c['files'] = {name: sha256(self.parent / name) for name in c['files']}
        verify_contract(c)
        for key, value in [('version', 'accepted-qwen-same-full-state-prefix-v1'),
                           ('driver_rng_unavailable_accepted', True)]:
            bad = copy.deepcopy(c); bad[key] = value
            with self.assertRaises(ValueError): verify_contract(bad)
        (self.parent / 'runs/train2/checkpoints/global_step_2/sc2_state.pt').unlink()
        with self.assertRaises(FileNotFoundError): verify_contract(c)


class L8FreshTests(unittest.TestCase):
    def setUp(self):
        for module in (m.fresh, m.orchestration, m.f, m.a, m.f.previous):
            guard = patch.dict(vars(module), {})
            guard.start(); self.addCleanup(guard.stop)

    def cfg(self, index):
        return dict(runtime_sha='test', controller_sha='test', controller_source='/source/code',
            environment={'LONG_DEPENDENCY_PATH': '/deps'}, training_seeds=[[49]*8, [97]*8],
            model_kind='qwen', model_mount='/assets/qwen', seed_protocol='same_uniform101',
            seed_group_mode='same', difficulty='CheatVision', run_prefix='test',
            worker_hook='l7_followup_hook.install',
            stages=['pre', 'train2', 'post'] if index == 0 else ['train96', 'eval96'],
            host=dict(model='/original-qwen', venv='/venv', sc2='/sc2', image='fixed-image'))

    def test_real_training_schema_has_no_replays(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); out = root / 'runs/train2'; out.mkdir(parents=True)
            (out / 'result.json').write_text(json.dumps({'status': 'completed',
                'completed_steps': 2, 'checkpoint_files': {}}))
            for i in range(16):
                p = out / f'sc2-logs/game-{i}/default_player/Flat128_CheatVision_Air/model/time/replay.SC2Replay'
                p.parent.mkdir(parents=True); p.write_bytes(b'replay')
            with patch.object(m.a, 'ROOT', root), patch.object(m.fresh, 'verify') as base:
                m.verify('train2', write=False)
                base.assert_called_once_with('train2', write=False)
                m.verify('train2')
                self.assertEqual(base.call_args.kwargs, {'write': True})
                p.unlink()
                with self.assertRaisesRegex(RuntimeError, 'natural replay'): m.verify('train2')
            p.parent.mkdir(exist_ok=True); p.write_bytes(b'')
            with self.assertRaises(RuntimeError): m.replay_evidence(out, 'train2')

    def test_replay_wrong_level_and_evaluation_digest_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp); files = []
            for i in range(8):
                p = out / f'sc2-logs/game-{i}/default_player/Flat128_CheatVision_Air/model/time/replay.SC2Replay'
                p.parent.mkdir(parents=True); p.write_bytes(b'replay'); files.append(p)
            result = {'replays': {str(p.relative_to(out)): sha256(p) for p in files}}
            (out / 'result.json').write_text(json.dumps(result))
            self.assertEqual(len(m.replay_evidence(out, 'post')), 8)
            files[0].write_bytes(b'changed')
            with self.assertRaisesRegex(RuntimeError, 'digest'): m.replay_evidence(out, 'post')
            files[0].write_bytes(b'replay')
            wrong = out / 'sc2-logs/game-0/default_player/Flat128_VeryHard_Air/model/time/replay.SC2Replay'
            wrong.parent.mkdir(parents=True); files[0].rename(wrong)
            with self.assertRaisesRegex(RuntimeError, 'natural replay'): m.replay_evidence(out, 'post')

    def resolved(self, stage='train2'):
        return {'trainer': {'val_only': stage in ('pre', 'post', 'eval96'), 'n_gpus_per_node': 8},
            'ray_init': {'runtime_env': {'worker_process_setup_hook': 'l7_followup_hook.install',
                'env_vars': {'PYTHONPATH': '/frozen/code:/deps', 'SC2PATH': '/assets/StarCraftII',
                    'SC2_ACCEPTANCE_STAGE': stage, 'SC2_DIFFICULTY': 'CheatVision',
                    'SC2_EXPECTED_DIFFICULTY': 'CheatVision', 'SC2_L8_RENDEZVOUS_LOW_PORT': '1',
                    'SC2_TRAIN_SEED_PROTOCOL': 'same_uniform101', 'SC2_EVAL_SEEDS_LOG_PATH': '/cpu/seeds',
                    'SC2_RUNTIME_LOG_ROOT': '/cpu/logs', 'EXTRA_REQUIRED_ENV': 'preserved'}}}}

    def test_fresh_then_only_own_native_cp2(self):
        m.configure()
        for index, stage in [(0, 'pre'), (0, 'train2'), (0, 'post'), (1, 'train96'), (1, 'eval96')]:
            with patch.object(m.a, 'read', return_value=self.cfg(index)):
                cfg = m.f.select(index)
                args, env, _ = m.invocation(cfg, stage, True)
            self.assertEqual(env['SC2_DIFFICULTY'], 'CheatVision')
            self.assertIn("+ray_init.runtime_env.env_vars.SC2_L8_RENDEZVOUS_LOW_PORT='1'", args)
            self.assertIn('algorithm.sc2_policy_credit.seed_group_mode=same', args)
            if stage in ('pre', 'train2'):
                self.assertFalse(any(x.startswith('trainer.resume_from_path=') for x in args))
            if stage == 'train96':
                self.assertIn('+trainer.sc2_import_legacy_final=False', args)
                self.assertIn('trainer.resume_from_path=' + str(m.ROOT / m.PARTS[0] /
                    'runs/train2/checkpoints/global_step_2'), args)
            self.assertTrue(env['RAY_TMPDIR'].startswith('/tmp/l8-'))

    def test_full_environment_and_missing_sc2path(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'config.json'
            for stage in ('pre', 'train2', 'train96', 'post', 'eval96'):
                cfg = self.resolved(stage); path.write_text(json.dumps(cfg))
                env, proof = m.probe.runtime_environment(path, '/tmp/probe-ray')
                expected = copy.deepcopy(cfg['ray_init']['runtime_env'])
                expected['env_vars'].update(TMPDIR='/tmp/probe-ray', RAY_TMPDIR='/tmp/probe-ray')
                self.assertEqual(env, expected)
                self.assertEqual(proof['resolved_config_sha256'], sha256(path))
                self.assertEqual(proof['required_worker_module'], 'refinery_order_eval')
            del cfg['ray_init']['runtime_env']['env_vars']['SC2PATH']
            path.write_text(json.dumps(cfg))
            with self.assertRaises(ValueError): m.probe.runtime_environment(path, '/tmp/probe-ray')

    def test_probe_docker_gpu_boundary_and_cli(self):
        m.configure()
        def read(path):
            return self.resolved() if str(path).endswith('resolved_config.json') else self.cfg(0)
        with patch.object(m.a, 'read', side_effect=read):
            cpu = m.docker('cpu-hook', 0, 'train2')
            gpu = m.docker('gpu-preflight', 0, 'train2')
        self.assertNotIn('--gpus', cpu)
        self.assertIn('CUDA_VISIBLE_DEVICES=', cpu)
        self.assertEqual(cpu[-3:], ['cpu-hook', '0', 'train2'])
        self.assertEqual(gpu[:2], ['docker', 'create'])
        self.assertEqual(gpu[-3:], ['gpu-preflight', '0', 'train2'])
        self.assertIn('--gpus', gpu)
        self.assertNotIn('--rm', gpu)
        self.assertIn('PYTHONPATH=/frozen/code:/deps', gpu)

    def test_budget_and_no_overwrite(self):
        self.assertEqual(m.WALL_SECONDS, 48 * 3600)
        self.assertEqual(m.accounts(123)[0], dict(roots=[m.ROOT, m.SOURCE_PARENT],
            receipt_root=m.ROOT, limit=1024**4, deadline=123))
        with tempfile.TemporaryDirectory() as tmp, patch.object(m, 'ROOT', Path(tmp)):
            with self.assertRaisesRegex(RuntimeError, 'Fresh exact'): m.prepare()

    def test_probe_failure_blocks_games_and_requeue(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(m, 'ROOT', Path(tmp)):
            m.configure()
            m.a.save(Path(tmp) / 'deployment.json', {'first_dispatch_by': 10**12}, lock_root=Path(tmp))
            with patch.object(m, 'check_cpu'), patch.object(m, 'admit'), \
                    patch.object(m.h, 'run_stages', side_effect=RuntimeError('gpu failed')) as run:
                with self.assertRaisesRegex(RuntimeError, 'gpu failed'): m.queue()
                self.assertEqual(run.call_count, 1)
                self.assertEqual(run.call_args.args[0], ['gpu-preflight'])
                clock = m.a.read(Path(tmp) / 'dispatch.json')
                self.assertEqual(clock['deadline'] - clock['start'], 48 * 3600)
                self.assertEqual(clock['new_games'], 792)
                with self.assertRaisesRegex(RuntimeError, 'Already queued'): m.queue()

    def test_short_failure_blocks_long(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(m, 'ROOT', Path(tmp)):
            m.configure()
            m.a.save(Path(tmp) / 'deployment.json', {'first_dispatch_by': 10**12}, lock_root=Path(tmp))
            for index, part in enumerate(m.PARTS):
                owner = Path(tmp) / part; owner.mkdir(parents=True)
                m.a.save(owner / 'deployment.json', self.cfg(index), lock_root=Path(tmp))
            with patch.object(m, 'check_cpu'), patch.object(m, 'admit'), \
                    patch.object(m.h, 'run_stages', side_effect=[{}, RuntimeError('short failed')]) as run, \
                    patch.object(m, 'contract_for') as contract:
                with self.assertRaisesRegex(RuntimeError, 'short failed'): m.queue()
                self.assertEqual(run.call_count, 2)
                contract.assert_not_called()
                self.assertFalse((Path(tmp) / m.PARTS[1] / 'dispatch.json').exists())


if __name__ == '__main__': unittest.main()
