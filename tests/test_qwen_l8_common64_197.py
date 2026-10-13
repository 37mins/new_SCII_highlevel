"""Approved scope, disjoint paired seeds, zero updates and real hook routing."""
from copy import deepcopy
import json
from pathlib import Path
import random
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'experiments/records/20260921-sc2-policy-credit-v1'))
import qwen_l8_common64_plan as plan
import qwen_l8_common64_hook as hook
import qwen_l8_common64_197 as m


class Common64Tests(unittest.TestCase):
    def cfg(self):
        return dict(environment={'LONG_DEPENDENCY_PATH':'/deps'},model_kind='qwen',model_mount='/assets/qwen',
            difficulty='CheatVision',run_prefix=m.PREFIX,seed_protocol='same_uniform101',seed_group_mode='same',
            worker_hook='qwen_l8_common64_hook.install',host=dict(model='/model',venv='/venv',sc2='/sc2',image='fixture'))

    def resolved(self,stage):
        spec=plan.stage_spec(stage)
        return dict(trainer=dict(val_only=True,val_before_train=True,save_freq=-1,n_gpus_per_node=8,
            sc2_checkpoint_resume=False,resume_mode='resume_path' if spec['checkpoint'] else 'disable',
            resume_from_path=str(spec['checkpoint'])),ray_init=dict(runtime_env=dict(
                worker_process_setup_hook='qwen_l8_common64_hook.install',env_vars=dict(
                    SC2_ACCEPTANCE_STAGE=stage,SC2PATH='/assets/StarCraftII',SC2_DIFFICULTY='CheatVision',
                    SC2_EXPECTED_DIFFICULTY='CheatVision',SC2_L8_RENDEZVOUS_LOW_PORT='1',PYTHONPATH='/deps',
                    SC2_EVAL_SEEDS_LOG_PATH='/seeds',SC2_RUNTIME_LOG_ROOT='/logs',EXTRA='preserve'))))

    def test_seeds_are_frozen_and_disjoint(self):
        plan.validate()
        self.assertEqual(plan.SEEDS,random.Random(20260927).sample(range(65536,2**32-1),64))
        for old in (plan.EVAL_SEEDS,plan.L7_SEEDS,plan.PILOT_SEEDS,range(101)):
            self.assertFalse(set(plan.SEEDS)&set(old))

    def test_all_three_arms_same64_rotated(self):
        self.assertEqual(len(m.STAGES),24)
        for b in range(8):
            expected=plan.ARMS[b%3:]+plan.ARMS[:b%3]
            self.assertEqual(tuple(plan.stage_spec(s)['arm'] for s in m.STAGES[3*b:3*b+3]),expected)
        for arm in plan.ARMS:
            self.assertEqual([seed for s in m.STAGES if plan.stage_spec(s)['arm']==arm
                for seed in plan.stage_spec(s)['seeds']],plan.SEEDS)

    def test_wrong_stage_and_seed_change_rejected(self):
        with self.assertRaises(ValueError):plan.stage_spec('train192')
        with patch.object(plan,'SEEDS',[1]*64):
            with self.assertRaises(ValueError):plan.validate()

    def test_exact_l8_checkpoint_not_l7(self):
        self.assertIn('l8same96',str(plan.CHECKPOINTS['cp96']))
        self.assertIn('l8same192',str(plan.CHECKPOINTS['cp192']))
        self.assertEqual([plan.stage_spec(s)['expected_step'] for s in m.HOOK_STAGES],[0,96,192])

    def test_all24_invocations_zero_updates_no_checkpoint_write(self):
        with patch.object(m.a,'ROOT',m.ROOT):
            for stage in m.STAGES:
                spec=plan.stage_spec(stage);args,env,out=m.invocation(self.cfg(),stage,True)
                settings=dict(x.split('=',1) for x in args if '=' in x)
                for key,value in {'trainer.val_only':'True','trainer.val_before_train':'True',
                        'trainer.save_freq':'-1','trainer.total_epochs':'1','trainer.del_local_ckpt_after_load':'False'}.items():
                    if key in settings:self.assertEqual(settings[key],value)
                self.assertEqual(settings['trainer.resume_mode'],'resume_path' if spec['checkpoint'] else 'disable')
                if spec['checkpoint']:self.assertEqual(settings['trainer.resume_from_path'],str(spec['checkpoint']))
                else:self.assertNotIn('trainer.resume_from_path',settings)
                self.assertEqual(settings['+ray_init.runtime_env.env_vars.SC2_ACCEPTANCE_STAGE'],repr(stage))
                self.assertEqual(settings['+ray_init.runtime_env.env_vars.SC2_L8_RENDEZVOUS_LOW_PORT'],"'1'")
                self.assertEqual(env['SC2_CHECKPOINT_RESUME'],'False');self.assertEqual(out,m.ROOT/'cpu'/stage)
                self.assertLess(len(env['RAY_TMPDIR']),32)

    def test_budget_exact_two_roots_six_hours(self):
        account=m.accounts(123)[0]
        self.assertEqual(account['roots'],[m.ROOT,m.SOURCE_PARENT]);self.assertEqual(account['limit'],32*1024**3)
        self.assertEqual(account['deadline'],123);self.assertEqual(m.WALL_SECONDS,21600)
        self.assertNotIn(plan.PARENT,account['roots'])

    def test_read_only_checkpoints_and_no_unbounded_restart(self):
        with patch.object(m.a,'ROOT',m.ROOT),patch.object(m.a,'read',return_value=self.cfg()):
            for stage in m.STAGES[:3]:
                args=m.docker('stage',stage)
                self.assertEqual(args[:2],['docker','create']);self.assertIn('--read-only',args)
                self.assertIn('--gpus',args);self.assertNotIn('--restart',args);self.assertNotIn('--rm',args)
                for cp in plan.CHECKPOINTS.values():self.assertIn(f'{cp}:{cp}:ro',args)
                self.assertEqual(args[-2:],['stage',stage])

    def test_cpu_no_gpu_request(self):
        with patch.object(m.a,'ROOT',m.ROOT),patch.object(m.a,'read',return_value=self.cfg()):
            args=m.docker('cpu')
        self.assertEqual(args[:2],['docker','run']);self.assertNotIn('--gpus',args)
        self.assertIn('CUDA_VISIBLE_DEVICES=',args)

    def test_full_resolved_runtime_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'resolved.json'
            for stage in m.STAGES:
                p.write_text(json.dumps(self.resolved(stage)))
                env,proof=hook.runtime_environment(p,'/tmp/probe-ray')
                self.assertEqual(env['env_vars']['EXTRA'],'preserve');self.assertEqual(proof['stage'],stage)
                self.assertEqual(proof['required_worker_module'],'feedback_eval')

    def test_training_or_wrong_checkpoint_env_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'resolved.json'
            for key,value in [('val_only',False),('save_freq',16),('sc2_checkpoint_resume',True),('resume_from_path','/wrong')]:
                cfg=self.resolved('b00-cp192');cfg['trainer'][key]=value;p.write_text(json.dumps(cfg))
                with self.assertRaises(ValueError):hook.runtime_environment(p,'/tmp/probe-ray')

    def test_worker_install_exact_steps_and_seeds(self):
        from types import SimpleNamespace
        from unittest.mock import Mock
        evaluate=Mock()
        with patch.dict(sys.modules,feedback_eval=SimpleNamespace(install=evaluate)):
            for stage in m.STAGES:
                with patch.dict(m.os.environ,SC2_ACCEPTANCE_STAGE=stage):hook.install()
                spec=plan.stage_spec(stage)
                evaluate.assert_called_with(expected_step=spec['expected_step'],game_seeds=spec['seeds'],expected_temperature=0.8,
                    answer_description='online Qwen L8; no replay or replacement')

    def test_reprepare_and_cpu_failure_cannot_launch(self):
        with patch.object(Path,'exists',return_value=True):
            with self.assertRaises(RuntimeError):m.prepare()
        with patch.object(m,'check_cpu',side_effect=RuntimeError('CPU failed')),patch.object(m.h,'run_stages') as run:
            with self.assertRaises(RuntimeError):m.queue()
            run.assert_not_called()

    def test_probe_binds_correct_resolved_environment(self):
        resolved=self.resolved('b00-original')
        def read(path):return resolved if str(path).endswith('resolved_config.json') else self.cfg()
        with patch.object(m.a,'ROOT',m.ROOT),patch.object(m.a,'read',side_effect=read):
            args=m.docker('gpu-preflight','b00-original')
        self.assertIn('PYTHONPATH=/deps',args);self.assertEqual(args[-2:],['gpu-preflight','b00-original'])

    def test_failed_gpu_probe_blocks_games_and_no_retry(self):
        with tempfile.TemporaryDirectory() as tmp,patch.object(m,'ROOT',Path(tmp)),\
                patch.object(m.a,'save',side_effect=lambda p,x:p.write_text(json.dumps(x))),\
                patch.object(m,'check_cpu'),patch.object(m,'parents',return_value={'passed':True}),\
                patch.object(m,'admit'),patch.object(m.h,'run_stages',side_effect=RuntimeError('probe failed')) as run:
            (Path(tmp)/'deployment.json').write_text(json.dumps({'first_dispatch_by':10**12}))
            with self.assertRaisesRegex(RuntimeError,'probe failed'):m.queue()
            self.assertEqual(run.call_count,1);self.assertEqual(run.call_args.args[0],['gpu-preflight'])
            d=json.loads((Path(tmp)/'dispatch.json').read_text())
            self.assertEqual(d['deadline']-d['start'],21600);self.assertEqual(d['gpu_hours'],48)
            self.assertEqual((d['new_games'],d['new_updates']),(192,0))
            with self.assertRaisesRegex(RuntimeError,'Already queued'):m.queue()

    def test_bad_parent_blocks_dispatch(self):
        with patch.object(m,'check_cpu'),patch.object(m,'parents',side_effect=RuntimeError('parent changed')),\
                patch.object(m.h,'run_stages') as run:
            with self.assertRaisesRegex(RuntimeError,'parent changed'):m.queue()
            run.assert_not_called()


if __name__=='__main__':unittest.main()
