"""Exact bounded evaluation scope, binding, pairing and fail-closed tests."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'experiments/records/20260921-sc2-policy-credit-v1'))
import spb_early128197 as e


class EarlyTests(unittest.TestCase):
    def setUp(self):
        for module in (e,e.m,e.q,e.a):
            guard=patch.dict(vars(module),{})
            guard.start();self.addCleanup(guard.stop)
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.base=Path(self.temp.name)
        e.ROOT=self.base/'new';e.SOURCE_PARENT=self.base/'source'
        e.ROOT.mkdir();e.configure()

    def cfg(self):
        model=dict(runtime_sha='test',controller_sha='test',controller_source='/source/code',
            environment={'LONG_DEPENDENCY_PATH':'/deps'},model_kind='spb',model_mount='/assets/spb',
            seed_protocol='same_uniform101',seed_group_mode='same',difficulty='VeryHard',
            worker_hook='spb_early_hook.install',run_prefix=e.PREFIX,
            host=dict(model='/original-spb',venv='/venv',sc2='/sc2',image='fixed-image'))
        return dict(runtime_sha='test',cpu_config_arm='cp2',arms={arm:model.copy() for arm in e.ARMS},
                    first_dispatch_by=10**12)

    def save(self,path,value):
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(json.dumps(value))

    def test_128_exact_games_shared_64_seeds(self):
        self.assertEqual(len(e.STAGES),16);self.assertEqual(len(set(e.STAGES)),16)
        self.assertEqual(len(e.SEEDS),64);self.assertEqual(len(set(e.SEEDS)),64)
        for arm in e.ARMS:
            specs=[e.stage_spec(s) for s in e.STAGES if e.stage_spec(s)['arm']==arm]
            self.assertEqual([v for s in specs for v in s['seeds']],e.SEEDS)
            self.assertEqual({s['expected_step'] for s in specs},{int(arm[2:])})

    def test_order_counterbalanced(self):
        for b in range(8):
            self.assertEqual([e.stage_spec(s)['arm'] for s in e.STAGES[2*b:2*b+2]],
                             list(e.ARMS if b%2==0 else e.ARMS[::-1]))

    def test_only_declared_stages(self):
        for s in ('b08-cp2','b00-cp96','train96','b00-spb-same'):
            with self.assertRaises(ValueError):e.stage_spec(s)

    def test_process_local_binding(self):
        self.assertEqual(e.m.ROOT,e.ROOT);self.assertEqual(e.q.ROOT,e.ROOT)
        self.assertEqual(e.a.ROOT,e.ROOT);self.assertEqual(e.a.STORAGE_LOCK_ROOT,e.ROOT)
        self.assertIs(e.q.predecessor,e.predecessor);self.assertIs(e.q.verify,e.verify)
        self.assertIs(e.q.docker,e.m.docker);self.assertIs(e.q.admit,e.m.admit)
        self.assertEqual(e.q.STAGES,e.STAGES)
        self.assertEqual(e.a.DOCKER_SCRIPT.name,'spb_early128197.py')

    def test_budget_fixed_and_exact_roots(self):
        self.assertEqual(e.WALL_SECONDS,21600);self.assertEqual(e.q.WALL_SECONDS,21600)
        self.assertEqual(e.LIMIT,32*1024**3)
        self.assertEqual(e.q.accounts(99),[dict(roots=[e.ROOT,e.SOURCE_PARENT],receipt_root=e.ROOT,
                                              limit=e.LIMIT,deadline=99)])

    def test_all_invocations_zero_updates_and_exact_checkpoints(self):
        for stage in e.STAGES:
            spec=e.stage_spec(stage);args,env,out=e.m.invocation(self.cfg(),stage,True)
            opts={v.split('=',1)[0]:v.split('=',1)[1] for v in args if '=' in v}
            self.assertEqual(opts['trainer.val_only'],'True')
            self.assertEqual(opts['trainer.save_freq'],'-1')
            self.assertEqual(opts['trainer.resume_mode'],'resume_path')
            self.assertEqual(opts['trainer.resume_from_path'],str(spec['checkpoint']))
            self.assertEqual(opts['+ray_init.runtime_env.worker_process_setup_hook'],'spb_early_hook.install')
            self.assertEqual(opts['+ray_init.runtime_env.env_vars.SC2_MATRIX_STAGE'],repr(stage))
            self.assertEqual(opts['+ray_init.runtime_env.env_vars.SC2_RESET_CONCURRENCY'],"'1'")
            self.assertEqual(env['SC2_CHECKPOINT_RESUME'],'False')
            self.assertIn('run_seed_group_arm.sh',args[1]);self.assertEqual(out,e.ROOT/'cpu'/stage)

    def test_cpu_spb_config_no_gpu(self):
        with patch.object(e.m,'small',return_value=self.cfg()):args=e.m.docker('cpu')
        self.assertNotIn('--gpus',args);self.assertIn('CUDA_VISIBLE_DEVICES=',args)
        self.assertIn(f'{e.q.SPB_METADATA}:/assets/spb:ro',args)
        self.assertIn('--read-only',args)

    def test_gpu_only_new_roots_writable_old_assets_read_only(self):
        with patch.object(e.m,'small',return_value=self.cfg()):
            for stage in e.STAGES:
                args=e.m.docker('stage',stage)
                self.assertEqual(args[:2],['docker','create']);self.assertIn('--gpus',args)
                self.assertNotIn('--rm',args);self.assertNotIn('--restart',args)
                binds=[args[i+1] for i,v in enumerate(args[:-1]) if v=='-v']
                self.assertEqual([v for v in binds if not v.endswith(':ro')],
                                 [f'{e.ROOT}:{e.ROOT}',f'{e.ROOT}/tmp:/tmp'])
                for cp in e.CHECKPOINTS.values():self.assertIn(f'{cp}:{cp}:ro',binds)

    def test_prepare_refuses_existing_root(self):
        with self.assertRaisesRegex(RuntimeError,'New exact roots'):e.prepare()

    def inventory(self):
        root=self.base/'cp'
        names=['data.pt','sc2_state.pt']+[f'actor/{k}_world_size_8_rank_{r}.pt'
            for k in ('model','optim','extra_state') for r in range(8)]
        for n in names:
            p=root/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b'fake')
        return root,{n:dict(exists=True,bytes=4) for n in names},{n:4 for n in names}

    def test_inventory_exact_26_without_reading_contents(self):
        root,files,sizes=self.inventory()
        with patch.object(Path,'read_bytes',side_effect=AssertionError('No weight reads')):
            e.require_inventory(root,files,sizes)

    def test_missing_inventory_fails(self):
        root,files,sizes=self.inventory();files.pop('data.pt')
        with self.assertRaisesRegex(RuntimeError,'26'):e.require_inventory(root,files,sizes)

    def test_changed_inventory_fails(self):
        root,files,sizes=self.inventory();sizes['data.pt']=5
        with self.assertRaisesRegex(RuntimeError,'inventory changed'):e.require_inventory(root,files,sizes)

    def test_changed_disk_size_fails(self):
        root,files,sizes=self.inventory();(root/'data.pt').write_bytes(b'')
        with self.assertRaisesRegex(RuntimeError,'inventory changed'):e.require_inventory(root,files,sizes)

    def test_symlink_inventory_fails(self):
        root,files,sizes=self.inventory();(root/'data.pt').unlink()
        (root/'data.pt').symlink_to(root/'sc2_state.pt')
        with self.assertRaisesRegex(RuntimeError,'inventory changed'):e.require_inventory(root,files,sizes)

    def test_changed_parent_receipt_blocks(self):
        with patch.object(e.m,'small',return_value={'receipt_sha256':{str(e.PARENT/'state.json'):'expected'}}), \
                patch.object(e.m,'digest',return_value='changed'):
            with self.assertRaisesRegex(RuntimeError,'receipt changed'):e.predecessor()

    def test_parent_proof_cannot_reference_unrelated_root(self):
        with patch.object(e.m,'small',return_value={'receipt_sha256':{'/other/result.json':'x'}}), \
                patch.object(e.m,'digest') as digest:
            with self.assertRaisesRegex(RuntimeError,'receipt changed'):e.predecessor()
            digest.assert_not_called()

    def verify_fixture(self,stage,change=None,bad_rng=None,bad_hash=False):
        spec=e.stage_spec(stage);out=e.ROOT/'runs'/stage
        e.BASELINE=self.base/'baseline';e.BASELINE_PROOF=self.base/'proof.json'
        for n in ('manifest.json','result.json'):self.save(out/n,{'metrics_precision':'binary64-v1'})
        load=dict(val_only=True,optimizer_updates=0,loaded_global_step=spec['expected_step'],games=8,
            checkpoint=str(spec['checkpoint']),checkpoint_load_returned=True,game_seeds=spec['seeds'],
            temperature=.8,do_sample=True,feedback='0')
        if change:load.update(change)
        self.save(out/'checkpoint_evaluation.json',load)
        self.save(out/'evaluation_seeds.jsonl',{'seeds':spec['seeds']})
        (out/'episode_outcomes.jsonl').write_text('\n'.join(json.dumps(dict(env_index=i,terminated=True,truncated=False)) for i in range(8)))
        rng=[dict(rank=i,seed=i,cpu_rng_sha256='cpu'+str(i),cuda_rng_sha256='cuda'+str(i)) for i in range(8)]
        for i,r in enumerate(rng):self.save(out/f'sampling-rank{i}.json',r)
        hashes={}
        for arm in ('spb-original','spb-same'):
            rel=f'acceptance-b{spec["batch"]:02d}-{arm}.json'
            self.save(e.BASELINE/rel,dict(rng=[] if bad_rng==arm else rng,seeds=spec['seeds']))
            hashes[rel]='bad' if bad_hash else e.m.digest(e.BASELINE/rel)
        self.save(e.BASELINE_PROOF,{'receipt_sha256':{'matrix':hashes}})
        with patch.object(e.a,'verify_common',return_value=({'training_updates':0},{})):e.verify(stage)
        accepted=e.m.small(e.ROOT/f'acceptance-{stage}.json')
        self.assertEqual(accepted['paired_with'][-2:],[str(e.BASELINE/f'acceptance-b{spec["batch"]:02d}-{arm}.json')
                                                     for arm in ('spb-original','spb-same')])

    def test_verify_cp2_and_cp8(self):
        for arm in e.ARMS:self.verify_fixture('b00-'+arm)

    def test_verify_rejects_wrong_checkpoint_or_updates(self):
        for change in (dict(loaded_global_step=96),dict(optimizer_updates=1),dict(checkpoint='/wrong'),
                       dict(checkpoint_load_returned=False),dict(temperature=.4),dict(game_seeds=[0]*8)):
            with self.subTest(change=change),self.assertRaisesRegex(RuntimeError,'load/seed'):
                self.verify_fixture('b00-cp2',change)

    def test_both_reused_arms_must_pair_rng(self):
        for arm in ('spb-original','spb-same'):
            with self.subTest(arm=arm),self.assertRaisesRegex(RuntimeError,'RNG mismatch'):
                self.verify_fixture('b00-cp8',bad_rng=arm)

    def test_reused_receipt_change_fails_before_acceptance(self):
        with self.assertRaisesRegex(RuntimeError,'acceptance changed'):self.verify_fixture('b00-cp2',bad_hash=True)
        self.assertFalse((e.ROOT/'acceptance-b00-cp2.json').exists())

    def test_queue_failure_one_shot_fixed_budget(self):
        self.save(e.ROOT/'deployment.json',self.cfg())
        with patch.object(e.q,'check_cpu'),patch.object(e.q,'predecessor',return_value={'passed':True}), \
                patch.object(e.q,'admit'),patch.object(e.h,'run_stages',side_effect=RuntimeError('failed stage')) as run:
            with self.assertRaisesRegex(RuntimeError,'failed stage'):e.q.queue()
            d=e.m.small(e.ROOT/'dispatch.json')
            self.assertEqual(d['deadline']-d['start'],21600)
            self.assertEqual((d['new_games'],d['new_updates'],d['gpu_hours']),(128,0,48))
            self.assertEqual(e.m.small(e.ROOT/'queue-state.json')['phase'],'failed')
            self.assertEqual(run.call_args.args[0],e.STAGES)
            with self.assertRaisesRegex(RuntimeError,'Already queued'):e.q.queue()
            self.assertEqual(run.call_count,1)

    def test_predecessor_failure_blocks_dispatch(self):
        self.save(e.ROOT/'deployment.json',self.cfg())
        with patch.object(e.q,'check_cpu'),patch.object(e.q,'predecessor',side_effect=RuntimeError('parent changed')), \
                patch.object(e.q,'admit') as admit,patch.object(e.h,'run_stages') as run:
            with self.assertRaisesRegex(RuntimeError,'parent changed'):e.q.queue()
            self.assertFalse((e.ROOT/'dispatch.json').exists());admit.assert_not_called();run.assert_not_called()


if __name__=='__main__':unittest.main()
