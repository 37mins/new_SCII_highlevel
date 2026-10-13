"""Authorized queue boundaries and the added explicit native/random resume cases."""
import copy
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

REC=Path(__file__).resolve().parents[1]/'experiments/records/20260921-sc2-policy-credit-v1'
sys.path.insert(0,str(REC))
import l7_followup197 as m
from test_sc2_policy_resume import PolicyResumeTests
from agent_system.sc2_policy_resume import verify_contract,sha256,validate_resume
from omegaconf import OmegaConf


class FollowupTests(unittest.TestCase):
    def cfg(self, index):
        return dict(environment={'PYTHON_BIN':'python','LONG_DEPENDENCY_PATH':'/deps'},
            stages=['pre','train2','post'] if index==0 else ['train96','eval96'],
            model_kind='spb' if index<2 else 'qwen',model_mount='/assets/spb' if index<2 else '/assets/qwen',
            seed_group_mode='same' if index<2 else 'mixed_seed_ablation',
            seed_protocol='same_uniform101' if index<2 else 'independent_uniform101',
            difficulty='VeryHard',worker_hook='l7_followup_hook.install',run_prefix='test')

    def test_spb_short_is_fresh_and_captures_native_state(self):
        with patch.object(m,'INDEX',0):
            args,env,_=m.invocation(self.cfg(0),'train2',True)
        self.assertEqual(env['SC2_CHECKPOINT_RESUME'],'True')
        self.assertIn("+ray_init.runtime_env.env_vars.SC2_TRAIN_SEED_PROTOCOL='same_uniform101'",args)
        self.assertNotIn('trainer.resume_mode=resume_path',args)
        self.assertIn('trainer.total_training_steps=2',args)

    def test_each_long_uses_only_own_prefix_and_explicit_import_mode(self):
        for index in (1,2):
            with patch.object(m,'INDEX',index):
                args,env,_=m.invocation(self.cfg(index),'train96',True)
            self.assertIn('trainer.resume_from_path='+str(m.parent_for(index)/'runs/train2/checkpoints/global_step_2'),args)
            self.assertIn('trainer.total_training_steps=96',args)
            self.assertIn('+trainer.sc2_import_legacy_final='+str(index==2),args)
            self.assertEqual(env['SC2_CHECKPOINT_RESUME'],'True')
            self.assertIn('trainer.save_freq=8',args)

    def test_fixed_order_budget_and_no_prepare_overwrite(self):
        self.assertEqual(m.PARTS,('spb-same/short','spb-same/long','qwen-random/long'))
        self.assertEqual(m.ARM_SECONDS,48*3600)
        with tempfile.TemporaryDirectory() as tmp,patch.object(m,'SUITE',Path(tmp)):
            with self.assertRaisesRegex(RuntimeError,'Fresh suite'):m.prepare()

    def test_predecessor_failed_host_overrules_stale_child(self):
        with patch.object(m.a,'read',side_effect=[{'phase':'failed'},{'phase':'running-unverified'}]):
            with self.assertRaisesRegex(RuntimeError,'Predecessor failed'):m.predecessor_complete()
        with patch.object(m.a,'read',side_effect=[{'phase':'dispatched'},{'phase':'completed'}]):
            self.assertFalse(m.predecessor_complete())

    def test_no_claim_update_from_audit_only(self):
        with self.assertRaisesRegex(RuntimeError,'PPO'):
            m.verify_updates([{'pending_global_step':1,'decision':'accept'}],[],1,1)
        with self.assertRaisesRegex(RuntimeError,'PPO'):
            m.verify_updates([{'pending_global_step':1,'decision':'accept'}],[{'actor/grad_norm':float('nan'),'policy_credit/invalid_advantage_max':0}],1,1)


class AddedResumeContracts(PolicyResumeTests):
    def test_only_output_derived_spb_model_views_normalize(self):
        from agent_system.sc2_policy_resume import normalized_protocol
        a=copy.deepcopy(self.cfg);a['actor_rollout_ref']={'model':{'path':'/old/model'}}
        b=copy.deepcopy(a);b['trainer']['default_local_dir']='/new/cp';b['actor_rollout_ref']['model']['path']='/new/model'
        self.assertEqual(normalized_protocol(a),normalized_protocol(b))
        b['actor_rollout_ref']['model']['path']='/other/weights'
        self.assertNotEqual(normalized_protocol(a),normalized_protocol(b))

    def updated(self,native):
        c=self.contract()
        cfg=json.loads((self.parent/'deployment.json').read_text())
        cfg.update(model_kind='spb' if native else 'qwen',seed_protocol='same_uniform101' if native else 'independent_uniform101',
            seed_group_mode='same' if native else 'mixed_seed_ablation')
        (self.parent/'deployment.json').write_text(json.dumps(cfg))
        c.update(version='accepted-spb-same-full-state-prefix-v1' if native else 'accepted-qwen-random-prefix-v1',
                 driver_rng_unavailable_accepted=not native)
        if native:
            rel='checkpoints/global_step_2/sc2_state.pt'
            (self.parent/'runs/train2'/rel).write_bytes(b'x')
            r=json.loads((self.parent/'runs/train2/result.json').read_text())
            r['checkpoint_files'][rel]={'bytes':1}
            for f in ('result.json','.done'):(self.parent/'runs/train2'/f).write_text(json.dumps(r))
            evidence=json.loads((self.parent/'acceptance-train2.json').read_text());evidence['result']=r
            (self.parent/'acceptance-train2.json').write_text(json.dumps(evidence))
        c['files']={p:sha256(self.parent/p) for p in c['files']}
        return c

    def test_random_explicit_contract_not_same_contract(self):
        c=self.updated(False);verify_contract(c)
        c['version']='accepted-same-seed-prefix-v1'
        with self.assertRaisesRegex(ValueError,'model/protocol'):verify_contract(c)

    def test_spb_requires_real_native_state_no_legacy_permission(self):
        c=self.updated(True);verify_contract(c)
        path=self.parent/'contract.json';path.write_text(json.dumps(c))
        cfg=OmegaConf.create(copy.deepcopy(self.cfg))
        cfg.trainer.update(dict(resume_mode='resume_path',resume_from_path=c['checkpoint'],
            sc2_checkpoint_resume=True,sc2_import_legacy_final=False,total_training_steps=96,
            sc2_policy_credit_resume_contract=str(path)))
        validate_resume(cfg)
        cfg.trainer.sc2_import_legacy_final=True
        with self.assertRaisesRegex(ValueError,'Legacy import'):validate_resume(cfg)
        (self.parent/'runs/train2/checkpoints/global_step_2/sc2_state.pt').unlink()
        with self.assertRaises(FileNotFoundError):verify_contract(c)
