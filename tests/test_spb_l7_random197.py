"""Fresh random SpB gates; synthetic receipts only, no server/GPU actions."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'experiments/records/20260921-sc2-policy-credit-v1'))
import spb_l7_random197 as m
from test_l7_followup197 import AddedResumeContracts
from agent_system.sc2_policy_resume import sha256,verify_contract


class RandomNativeContractTests(AddedResumeContracts):
    def random_contract(self):
        c=self.updated(True)
        p=self.parent/'deployment.json';cfg=json.loads(p.read_text())
        cfg.update(seed_protocol='independent_uniform101',seed_group_mode='mixed_seed_ablation')
        p.write_text(json.dumps(cfg))
        c.update(version='accepted-spb-random-full-state-prefix-v1')
        c['files']={p:sha256(self.parent/p) for p in c['files']}
        return c

    def test_random_requires_explicit_native_contract(self):
        c=self.random_contract();verify_contract(c)
        for name,value in [('version','accepted-spb-same-full-state-prefix-v1'),
                           ('version','accepted-qwen-random-prefix-v1'),
                           ('driver_rng_unavailable_accepted',True)]:
            bad=copy.deepcopy(c);bad[name]=value
            with self.assertRaises(ValueError):verify_contract(bad)
        (self.parent/'runs/train2/checkpoints/global_step_2/sc2_state.pt').unlink()
        with self.assertRaises(FileNotFoundError):verify_contract(c)


class SpbRandomQueueTests(unittest.TestCase):
    def setUp(self):
        for module in (m.f,m.a,m.f.previous):
            guard=patch.dict(vars(module),{});guard.start();self.addCleanup(guard.stop)

    def cfg(self,index):
        return dict(runtime_sha='test',controller_sha='test',controller_source='/source/code',
            environment={'LONG_DEPENDENCY_PATH':'/deps'},training_seeds=[[49,97,53,5,33,65,62,51],[100,38,61,45,74,27,64,17]],
            model_kind='spb',model_mount='/assets/spb',seed_protocol='independent_uniform101',
            seed_group_mode='mixed_seed_ablation',difficulty='VeryHard',run_prefix='test',
            stages=['pre','train2','post'] if index==0 else ['train96','eval96'],
            host=dict(model='/original-spb',venv='/venv',sc2='/sc2',image='fixed-image'))

    def test_fresh_short_then_only_own_native_cp2(self):
        m.configure()
        for index,stage in [(0,'train2'),(1,'train96'),(1,'eval96')]:
            with patch.object(m.a,'read',return_value=self.cfg(index)):
                cfg=m.f.select(index);args,env,_=m.invocation(cfg,stage,True)
            self.assertIn("+ray_init.runtime_env.env_vars.SC2_TRAIN_SEED_PROTOCOL='independent_uniform101'",args)
            self.assertIn('algorithm.sc2_policy_credit.seed_group_mode=mixed_seed_ablation',args)
            self.assertIn("+ray_init.runtime_env.env_vars.SC2_RESET_CONCURRENCY='1'",args)
            if index==0:self.assertFalse(any(x.startswith('trainer.resume_from_path=') for x in args))
            elif stage=='train96':
                self.assertIn('trainer.resume_from_path='+str(m.ROOT/m.PARTS[0]/'runs/train2/checkpoints/global_step_2'),args)
                self.assertIn('+trainer.sc2_import_legacy_final=False',args)
        with self.assertRaises(ValueError):m.parent_for(2)

    def test_cpu_has_no_gpu_and_gpu_has_exact_writers(self):
        m.configure()
        with patch.object(m.a,'read',return_value=self.cfg(0)):
            cpu=m.docker('cpu',0);gpu=m.docker('stage',0,'pre')
        self.assertNotIn('--gpus',cpu);self.assertIn('CUDA_VISIBLE_DEVICES=',cpu)
        self.assertEqual(gpu[:2],['docker','create']);self.assertNotIn('--rm',gpu)
        self.assertIn('--read-only',gpu);self.assertIn('/original-spb:/assets/spb:ro',gpu)
        self.assertIn(f'{m.ROOT}:{m.ROOT}:ro',gpu)
        self.assertEqual(gpu[-3:],['stage','0','pre'])

    def test_budget_includes_entire_output_and_source(self):
        proof=m.accounts(123)[0]
        self.assertEqual(proof['limit'],1024**4)
        self.assertEqual(proof['roots'],[m.ROOT,m.a.SOURCE.parent])
        self.assertEqual(proof['deadline'],123)
        self.assertEqual(m.WALL_SECONDS,48*3600)
        self.assertEqual(m.FIRST_DISPATCH_BY,m.PREDECESSOR_DEADLINE+3600)

    def test_predecessor_failure_overrules_stale_running_child(self):
        with patch.object(m.a,'read',side_effect=[{'phase':'failed'},{'phase':'running-unverified'}]),patch.object(m.sp,'run') as run:
            with self.assertRaisesRegex(RuntimeError,'predecessor failed'):m.predecessor_complete()
        run.assert_not_called()
        with patch.object(m.a,'read',return_value={'phase':'running-unverified'}):
            self.assertFalse(m.predecessor_complete())

    def predecessor_fixture(self,guardian_phase='completed',container_exit=0):
        complete=dict(phase='completed',exit_code=0,completed=['train96','eval96'],deadline=m.PREDECESSOR_DEADLINE)
        cfg=dict(runtime_sha=m.PREDECESSOR_SHA,controller_source=str(m.PREDECESSOR/'source/code'))
        docker=dict(id='a'*64,owner=str(m.PREDECESSOR),state=dict(Running=False,Paused=False,ExitCode=container_exit,OOMKilled=False,Error=''))
        guardian=dict(phase=guardian_phase,container_id='a'*64,owner_root=str(m.PREDECESSOR),
            deadline=m.PREDECESSOR_DEADLINE,final_state=docker['state'])
        return [complete,complete,complete,cfg,guardian,guardian],docker

    def test_full_predecessor_invokes_its_frozen_readonly_verifier(self):
        values,docker=self.predecessor_fixture()
        with patch.object(m.a,'read',side_effect=values),patch.object(m.a,'clean'),\
                patch.object(m.a,'cmd',return_value=json.dumps(docker)),patch.object(m.sp,'run') as run:
            self.assertTrue(m.predecessor_complete())
        code=run.call_args.args[0][-1]
        self.assertIn("m.verify('train96',write=False)",code)
        self.assertIn("m.verify('eval96',write=False)",code)

    def test_bad_terminal_container_or_guardian_blocks(self):
        for phase,exit_code in [('failed',0),('completed',1)]:
            values,docker=self.predecessor_fixture(phase,exit_code)
            with patch.object(m.a,'read',side_effect=values),patch.object(m.a,'clean'),\
                    patch.object(m.a,'cmd',return_value=json.dumps(docker)),patch.object(m.sp,'run') as run:
                with self.assertRaises(RuntimeError):m.predecessor_complete()
            run.assert_not_called()

    def test_predecessor_failure_never_allocates_or_creates_clock(self):
        with tempfile.TemporaryDirectory() as tmp,patch.object(m,'ROOT',Path(tmp)),\
                patch.object(m,'check_cpu'),patch.object(m,'predecessor_complete',side_effect=RuntimeError('failed predecessor')),\
                patch.object(m,'admit') as admit,patch.object(m.h,'run_stages') as run:
            with self.assertRaisesRegex(RuntimeError,'failed predecessor'):m.queue()
            self.assertFalse((Path(tmp)/'dispatch.json').exists())
            self.assertEqual(m.a.read(Path(tmp)/'queue-state.json')['phase'],'failed')
            with self.assertRaisesRegex(RuntimeError,'Already queued'):m.queue()
        admit.assert_not_called();run.assert_not_called()

    def test_short_failure_blocks_long_and_clock_not_reset(self):
        with tempfile.TemporaryDirectory() as tmp,patch.object(m,'ROOT',Path(tmp)),patch.object(m,'check_cpu'),\
                patch.object(m,'predecessor_complete',return_value=True),patch.object(m,'admit'),\
                patch.object(m.h,'run_stages',side_effect=RuntimeError('short failed')) as run:
            m.configure()
            for i,part in enumerate(m.PARTS):
                p=Path(tmp)/part;p.mkdir(parents=True);m.a.save(p/'deployment.json',self.cfg(i),lock_root=Path(tmp))
            with self.assertRaisesRegex(RuntimeError,'short failed'):m.queue()
            d=m.a.read(Path(tmp)/'dispatch.json')
            self.assertEqual(d['deadline']-d['start'],48*3600)
            self.assertFalse((Path(tmp)/m.PARTS[1]/'dispatch.json').exists())
        self.assertEqual(run.call_count,1)


if __name__=='__main__':unittest.main()
