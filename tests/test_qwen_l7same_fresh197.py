"""Synthetic fresh same-seed Qwen contract/queue tests; no server or GPU actions."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'experiments/records/20260921-sc2-policy-credit-v1'))
import qwen_l7same_fresh197 as m
from test_l7_followup197 import AddedResumeContracts
from agent_system.sc2_policy_resume import sha256, verify_contract


class QwenNativeContractTests(AddedResumeContracts):
    def native_qwen(self):
        c = self.updated(True)
        path = self.parent/'deployment.json'
        cfg = json.loads(path.read_text())
        cfg['model_kind'] = 'qwen'
        path.write_text(json.dumps(cfg))
        c['version'] = 'accepted-qwen-same-full-state-prefix-v1'
        c['files'] = {p: sha256(self.parent/p) for p in c['files']}
        return c

    def test_native_qwen_requires_full_state_and_not_legacy(self):
        c = self.native_qwen()
        verify_contract(c)
        for key, value in [('version','accepted-same-seed-prefix-v1'),
                           ('version','accepted-spb-same-full-state-prefix-v1'),
                           ('driver_rng_unavailable_accepted',True)]:
            bad = copy.deepcopy(c)
            bad[key] = value
            with self.assertRaises(ValueError): verify_contract(bad)
        (self.parent/'runs/train2/checkpoints/global_step_2/sc2_state.pt').unlink()
        with self.assertRaises(FileNotFoundError): verify_contract(c)


class FreshQueueTests(unittest.TestCase):
    def setUp(self):
        for module in (m.queue_impl, m.f, m.a, m.f.previous):
            guard = patch.dict(vars(module), {})
            guard.start()
            self.addCleanup(guard.stop)

    def cfg(self, index):
        return dict(runtime_sha='test', controller_sha='test', controller_source='/source/code',
            environment={'LONG_DEPENDENCY_PATH':'/deps'}, training_seeds=[[49]*8,[97]*8],
            model_kind='qwen', model_mount='/assets/qwen', seed_protocol='same_uniform101',
            seed_group_mode='same', difficulty='VeryHard', run_prefix='test',
            stages=['pre','train2','post'] if index == 0 else ['train96','eval96'],
            host=dict(model='/original-qwen',venv='/venv',sc2='/sc2',image='fixed-image'))

    def test_fresh_and_only_own_native_cp2(self):
        m.configure()
        for index, stage in [(0,'pre'),(0,'train2'),(0,'post'),(1,'train96'),(1,'eval96')]:
            with patch.object(m.a,'read',return_value=self.cfg(index)):
                cfg = m.f.select(index)
                args, env, _ = m.invocation(cfg, stage, True)
            self.assertIn('run_qwen_seed_arm.sh', args[1])
            self.assertIn("algorithm.sc2_policy_credit.seed_group_mode=same", args)
            self.assertIn("+ray_init.runtime_env.env_vars.SC2_TRAIN_SEED_PROTOCOL='same_uniform101'", args)
            if stage in ('pre','train2'):
                self.assertFalse(any(x.startswith('trainer.resume_from_path=') for x in args))
            elif stage == 'train96':
                self.assertIn('trainer.resume_from_path='+str(m.ROOT/m.PARTS[0]/'runs/train2/checkpoints/global_step_2'), args)
                self.assertIn('+trainer.sc2_import_legacy_final=False', args)
            self.assertFalse(any('SC2_RESET_CONCURRENCY' in x for x in args))  # already in Qwen shell
        with self.assertRaises(ValueError): m.parent_for(2)

    def test_exact_bindings_and_no_cpu_gpu(self):
        m.configure()
        with patch.object(m.a,'read',return_value=self.cfg(0)):
            cpu = m.docker('cpu',0)
            gpu = m.docker('stage',0,'pre')
        self.assertNotIn('--gpus',cpu)
        self.assertIn('CUDA_VISIBLE_DEVICES=',cpu)
        self.assertIn(f'{m.f.previous.CPU_MODEL}:/assets/qwen:ro',cpu)
        self.assertEqual(gpu[:2],['docker','create'])
        self.assertIn('--read-only',gpu)
        self.assertIn('/original-qwen:/assets/qwen:ro',gpu)
        self.assertEqual(gpu[-3:],['stage','0','pre'])

    def test_budget_and_no_overwrite(self):
        m.configure()
        account = m.queue_impl.accounts(456)[0]
        self.assertEqual(account['roots'],[m.ROOT,m.a.SOURCE.parent])
        self.assertEqual(account['limit'],1024**4)
        self.assertEqual(account['deadline'],456)
        self.assertEqual(m.WALL_SECONDS,48*3600)
        with tempfile.TemporaryDirectory() as tmp, patch.object(m,'ROOT',Path(tmp)):
            with self.assertRaisesRegex(RuntimeError,'Fresh root'): m.prepare()

    def test_original_cpu_receipt_is_not_new_qwen_regression_proof(self):
        with patch.object(m,'BASE_CHECK_CPU'), patch.object(m.a,'read',return_value={'passed':True}):
            with self.assertRaisesRegex(RuntimeError,'Fresh Qwen regression'): m.check_cpu()

    def test_predecessor_failure_no_clock_or_gpu(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(m,'ROOT',Path(tmp)):
            m.configure()
            with patch.object(m.queue_impl,'check_cpu'), patch.object(m.a,'read',return_value={'phase':'failed'}), \
                    patch.object(m.queue_impl,'admit') as admit, patch.object(m.h,'run_stages') as run:
                with self.assertRaisesRegex(RuntimeError,'predecessor failed'): m.queue_impl.queue()
            self.assertFalse((Path(tmp)/'dispatch.json').exists())
            admit.assert_not_called()
            run.assert_not_called()

    def test_short_failure_blocks_long_and_keeps_absolute_clock(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(m,'ROOT',Path(tmp)):
            m.configure()
            for index, part in enumerate(m.PARTS):
                owner = Path(tmp)/part
                owner.mkdir(parents=True)
                m.a.save(owner/'deployment.json',self.cfg(index),lock_root=Path(tmp))
            with patch.object(m.queue_impl,'check_cpu'), patch.object(m.queue_impl,'predecessor_complete',return_value=True), \
                    patch.object(m.queue_impl,'admit'), patch.object(m.h,'run_stages',side_effect=RuntimeError('short failed')) as run:
                with self.assertRaisesRegex(RuntimeError,'short failed'): m.queue_impl.queue()
                with self.assertRaisesRegex(RuntimeError,'Already queued'): m.queue_impl.queue()
            dispatch = m.a.read(Path(tmp)/'dispatch.json')
            self.assertEqual(dispatch['deadline']-dispatch['start'],48*3600)
            self.assertFalse((Path(tmp)/m.PARTS[1]/'dispatch.json').exists())
            self.assertEqual(run.call_count,1)

    def fixture(self, bad_guardian=False):
        queue = dict(phase='completed',exit_code=0,completed=['spb-random/short','spb-random/long'],deadline=m.PREDECESSOR_DEADLINE)
        cfg = dict(runtime_sha=m.PREDECESSOR_SHA,controller_source=str(m.PREDECESSOR/'source/code'))
        objects = {str(m.PREDECESSOR/'queue-state.json'):queue,str(m.PREDECESSOR/'deployment.json'):cfg}
        statuses = []
        for part, stages in [('short',['pre','train2','post']),('long',['train96','eval96'])]:
            owner = m.PREDECESSOR/'spb-random'/part
            terminal = dict(phase='completed',exit_code=0,completed=stages,deadline=m.PREDECESSOR_DEADLINE)
            for name in ('state.json','host-supervision/state.json'): objects[str(owner/name)] = terminal
            for stage in stages:
                state = dict(Running=False,Paused=False,ExitCode=0,OOMKilled=False,Error='')
                statuses.append(json.dumps(dict(id='a'*64,owner=str(owner),state=state)))
                objects[str(owner/f'host-supervision/{stage}-guardian.json')] = dict(
                    container_id='a'*64,owner_root=str(owner),phase='failed' if bad_guardian else 'completed',
                    deadline=m.PREDECESSOR_DEADLINE,final_state=state)
        return objects, statuses

    def test_five_stage_predecessor_and_original_verifier(self):
        for bad in (False,True):
            objects, statuses = self.fixture(bad)
            with patch.object(m.a,'read',side_effect=lambda p:objects[str(p)]), patch.object(m.a,'clean'), \
                    patch.object(m.a,'cmd',side_effect=statuses), patch.object(m.sp,'run') as run:
                if bad:
                    with self.assertRaises(RuntimeError): m.predecessor_complete()
                    run.assert_not_called()
                else:
                    self.assertTrue(m.predecessor_complete())
                    self.assertIn('write=False',run.call_args.args[0][-1])
                    self.assertIn("('train96','eval96')",run.call_args.args[0][-1])
                    self.assertIn("('pre','train2','post')",run.call_args.args[0][-1])


if __name__ == '__main__': unittest.main()
