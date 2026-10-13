"""Remaining-arm authorization, immutable identities and unchanged policy gates."""
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

RECORD = Path(__file__).resolve().parents[1] / 'experiments/records/20260921-sc2-policy-credit-v1'
sys.path.insert(0, str(RECORD))
import qwen_seed197 as q
import qwen_seed197_r4 as r4


class QwenRemainingTests(unittest.TestCase):
    def setUp(self):
        names = ('SUITE','SPB','SPB_RUNTIME','RUN_PREFIX','CONTAINER_PREFIX','DOCKER_SCRIPT',
                 'PRIOR_ROOTS','ARMS','REUSED_ARM_ROOT','WALL_SECONDS','FIRST_DISPATCH_BY','LIMIT','AUTHORIZATION')
        saved = {key:getattr(q,key) for key in names}
        self.addCleanup(lambda:[setattr(q,key,value) for key,value in saved.items()])
        saved_engine = {key:getattr(q.engine,key) for key in
                        ('ROOT','RUNTIME_SHA','TRAIN_SEEDS','TOKENIZER_SHA','MASK_SHA','STORAGE_LOCK_ROOT')}
        self.addCleanup(lambda:[setattr(q.engine,key,value) for key,value in saved_engine.items()])
        r4.configure()

    def test_only_remaining_three_arms_new_budget_and_no_completed_replay(self):
        self.assertEqual([a[0] for a in q.ARMS], ['l6-random','l7-same','l7-random'])
        self.assertEqual(q.SUITE.name, 'sc2-qwen-seeds197-20260922-r4')
        self.assertEqual((q.WALL_SECONDS,q.LIMIT,q.FIRST_DISPATCH_BY), (21600,512*1024**3,1790051700))
        configs = [q.arm_config(dict(host={},environment={'LONG_DEPENDENCY_PATH':'/deps'},
                                     runtime_sha='fixture',controller_sha='fixture'),i) for i in range(3)]
        self.assertEqual(sum(a['gpu_hours'] for a in configs),48)
        self.assertEqual(sum(sum(a['games']) for a in configs),96)
        self.assertEqual(configs[1]['training_seeds'],[[49]*8,[97]*8])
        self.assertEqual(configs[0]['training_seeds'], configs[2]['training_seeds'])
        for i,cfg in enumerate(configs):
            self.assertEqual(cfg['run_prefix'], 'qwen-seeds197-r4-'+q.ARMS[i][0])
            with patch.object(q.engine,'ROOT',q.SUITE/q.ARMS[i][0]):
                for stage in cfg['stages']:
                    args,env,_ = q.engine.invocation(cfg,stage,dry=True)
                    settings = dict(a.split('=',1) for a in args if '=' in a)
                    self.assertEqual(settings['actor_rollout_ref.rollout.top_p'],'1.0')
                    self.assertEqual(settings['trainer.total_training_steps'],'2')
                    self.assertEqual(env['SC2_DIFFICULTY'],cfg['difficulty'])
                    if stage == 'post':
                        self.assertEqual(settings['trainer.resume_from_path'],str(q.engine.ROOT/'runs/train2/checkpoints/global_step_2'))
                    else:
                        self.assertNotIn('trainer.resume_from_path', settings)

    def test_inclusive_prior_roots_and_strict_six_hour_boundary(self):
        with patch.object(Path,'exists',return_value=True), patch.object(q.engine,'measure_budget') as measure:
            q.budget()
        roots = measure.call_args.args[0]
        self.assertEqual(len(roots),11)
        self.assertIn(q.REUSED_ARM_ROOT.parent,roots)
        with patch.object(q.time,'time',return_value=100), patch.object(q.engine,'measure_budget') as measure:
            with self.assertRaisesRegex(TimeoutError,'6-hour / 48-GPU-hour'): q.budget(145)
            measure.assert_not_called()

    def test_completed_arm_revalidated_read_only_and_not_failed_suite_relabelled(self):
        result={'fixture':'accepted'}
        def read(path):
            self.assertTrue(str(path).startswith(str(q.REUSED_ARM_ROOT)))
            if path.name=='deployment.json':
                return dict(runtime_sha='019a8b3a60aa093d61fccfb4293625e300a2894e',training_seeds=[[49]*8,[97]*8],tokenizer_sha256='tok',mask_sha256='mask')
            if path.name=='state.json':return dict(phase='completed',exit_code=0,completed=['pre','train2','post'])
            return {'result':result} if path.name.startswith('acceptance-') else result
        with patch.object(q,'read',side_effect=read), patch.object(q.engine,'verify') as verify, patch.object(q,'save') as save:
            q.verify_reused_arm()
            self.assertEqual([call.args for call in verify.call_args_list],[('pre',),('train2',),('post',)])
            self.assertTrue(all(call.kwargs=={'write':False} for call in verify.call_args_list))
            save.assert_not_called()


if __name__=='__main__':unittest.main()
