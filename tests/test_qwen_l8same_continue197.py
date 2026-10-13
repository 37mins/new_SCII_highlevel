"""Bounded continuation retains the failed host history and original budget."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] /
    'experiments/records/20260921-sc2-policy-credit-v1'))
import qwen_l8same_continue197 as c


class ContinuationTests(unittest.TestCase):
    def setUp(self):
        for module in (c.m, c.m.fresh, c.m.orchestration, c.f, c.a, c.f.previous):
            guard = patch.dict(vars(module), {})
            guard.start(); self.addCleanup(guard.stop)
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / 'r2'; self.root.mkdir()
        guard = patch.object(c, 'ROOT', self.root)
        guard.start(); self.addCleanup(guard.stop)
        c.configure()
        for index, part in enumerate(c.PARTS):
            owner = self.root / part; owner.mkdir(parents=True)
            c.a.save(owner / 'deployment.json', self.cfg(index), lock_root=self.root)
        c.a.save(self.root / 'deployment.json', {'controller_sha': 'new'}, lock_root=self.root)

    def cfg(self, index):
        return dict(runtime_sha=c.RUNTIME_SHA, controller_sha='new', controller_source='/source/code',
            environment={}, training_seeds=[[49]*8, [97]*8], model_kind='qwen', model_mount='/assets/qwen',
            seed_protocol='same_uniform101', seed_group_mode='same', difficulty='CheatVision',
            run_prefix='test', worker_hook='l7_followup_hook.install',
            stages=['post'] if index == 0 else ['train96', 'eval96'],
            host=dict(model='/original-qwen', venv='/venv', sc2='/sc2', image='fixed-image'))

    def test_original_four_root_budget_and_no_overwrite(self):
        acc = c.accounts(c.DEADLINE)[0]
        self.assertEqual(acc['roots'], [c.OLD, c.OLD_SOURCE, self.root, c.SOURCE_PARENT])
        self.assertEqual(acc['limit'], 1024**4)
        self.assertEqual(c.DEADLINE-c.START, 48*3600)
        with self.assertRaises(ValueError): c.accounts(c.DEADLINE+1)
        with self.assertRaisesRegex(RuntimeError, 'Fresh exact'): c.prepare()

    def test_fresh_prepare_retains_readonly_aliases_and_only_remaining_stages(self):
        new = self.root / 'new'
        def read(path):
            return self.cfg(0 if 'short' in str(path) else 1)
        with patch.object(c, 'ROOT', new), patch.object(c, 'old_terminal', return_value={}), \
                patch.object(c.a, 'SOURCE', c.SOURCE_PARENT / 'code'), patch.object(c.a, 'clean'), \
                patch.object(c.a, 'cmd', return_value='new'), patch.object(c.a, 'read', side_effect=read), \
                patch.object(c.time, 'time', return_value=c.START+100):
            c.prepare()
        cfg = json.loads((new / c.PARTS[0] / 'deployment.json').read_text())
        self.assertEqual(cfg['stages'], ['post'])
        self.assertEqual(cfg['runtime_sha'], c.RUNTIME_SHA)
        self.assertEqual(cfg['fixed_deadline'], c.DEADLINE)
        for stage in ('pre', 'train2'):
            link = new / c.PARTS[0] / 'runs' / stage
            self.assertTrue(link.is_symlink())
            self.assertEqual(link.readlink(), c.OLD / c.PARTS[0] / 'runs' / stage)
        dep = json.loads((new / 'deployment.json').read_text())
        self.assertEqual((dep['retained_games'], dep['new_games'], dep['new_updates']), (24,768,94))

    def test_expired_prepare_has_no_writes(self):
        new = self.root / 'expired'
        with patch.object(c, 'ROOT', new), patch.object(c.a, 'SOURCE', c.SOURCE_PARENT / 'code'), \
                patch.object(c.time, 'time', return_value=c.DEADLINE):
            with self.assertRaises(TimeoutError): c.prepare()
        self.assertFalse(new.exists())

    def test_docker_old_roots_readonly_cpu_no_cuda_exact_stage_cli(self):
        for mode, index, stage in [('prefix-cpu',0,None),('cpu',0,None),('stage',0,'post'),
                                   ('stage',1,'train96'),('parent-cpu',1,None)]:
            args = c.docker(mode,index,stage)
            for root in (c.OLD,c.OLD_SOURCE): self.assertIn(f'{root}:{root}:ro',args)
            self.assertIn(str(c.a.HERE / 'qwen_l8same_continue197.py'),args)
            self.assertEqual('--gpus' in args,mode=='stage')
            if mode=='prefix-cpu': self.assertEqual(args[-2:],['prefix-cpu','0'])
        with self.assertRaisesRegex(ValueError,'Undeclared'): c.docker('stage',0,'train2')
        with self.assertRaisesRegex(ValueError,'Undeclared'): c.docker('stage',0,'pre')

    def test_probe_failure_blocks_post_and_requeue(self):
        with patch.object(c,'check_cpu'),patch.object(c,'verify_retained'),patch.object(c.m,'admit'), \
                patch.object(c.h,'run_stages',side_effect=RuntimeError('probe failed')) as run:
            with self.assertRaisesRegex(RuntimeError,'probe failed'): c.queue()
            self.assertEqual(run.call_count,1)
            clock=c.a.read(self.root/'dispatch.json')
            self.assertEqual((clock['start'],clock['deadline']),(c.START,c.DEADLINE))
            self.assertEqual(clock['new_games'],768)
            self.assertEqual(c.a.read(self.root/'queue-state.json')['phase'],'failed')
            with self.assertRaisesRegex(RuntimeError,'Already queued'): c.queue()

    def test_post_failure_blocks_contract_and_long(self):
        with patch.object(c,'check_cpu'),patch.object(c,'verify_retained'),patch.object(c.m,'admit'), \
                patch.object(c.h,'run_stages',side_effect=[{},RuntimeError('post failed')]) as run, \
                patch.object(c.m,'contract_for') as contract:
            with self.assertRaisesRegex(RuntimeError,'post failed'): c.queue()
            self.assertEqual(run.call_args.args[0],['post'])
            contract.assert_not_called()
            self.assertFalse((self.root/c.PARTS[1]/'dispatch.json').exists())

    def test_composite_prefix_and_native_parent_gate_before_long(self):
        c.a.save(self.root/'retained-acceptance.json',{'passed':True},lock_root=self.root)
        def parent(*args,**kwargs):
            c.a.save(self.root/c.PARTS[1]/'parent-readiness.json',
                {'actual_parent_verified':True},lock_root=self.root)
        def stages(names,*args,**kwargs):
            if names==['train96','eval96']:
                s=c.a.read(self.root/c.PARTS[0]/'state.json')
                self.assertEqual(s['completed'],['pre','train2','post'])
                self.assertEqual(s['newly_executed'],['post'])
                self.assertEqual(s['retained_from'],str(c.OLD/c.PARTS[0]))
            return dict(phase='completed',exit_code=0,completed=names,deadline=c.DEADLINE)
        with patch.object(c,'check_cpu'),patch.object(c,'verify_retained'),patch.object(c.m,'admit'), \
                patch.object(c.h,'run_stages',side_effect=stages) as run, \
                patch.object(c.m,'contract_for',return_value={'native':True}),patch.object(c.sp,'run',side_effect=parent):
            c.queue()
            self.assertEqual([x.args[0] for x in run.call_args_list],
                [['gpu-preflight'],['post'],['train96','eval96']])
        self.assertEqual(c.a.read(self.root/'queue-state.json')['phase'],'completed')


if __name__=='__main__': unittest.main()
