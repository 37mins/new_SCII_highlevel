"""Fail-closed accepted-prefix migration and protocol normalization."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from omegaconf import OmegaConf
from agent_system.sc2_policy_resume import normalized_protocol, prefix_files, sha256, verify_contract, validate_resume


class PolicyResumeTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.parent=Path(self.tmp.name)
        self.cfg=dict(data=dict(train_files='/old/data/train.parquet',val_files='/old/data/test.parquet'),
            env=dict(prompt_response_log_path='/old/log',seed=0),
            trainer=dict(resume_mode='disable',total_epochs=2,total_training_steps=2,
                         save_freq=2,del_local_ckpt_after_load=False,default_local_dir='/old/cp'),
            algorithm=dict(sc2_policy_credit=dict(enabled=True,min_valid_ratio=.5)),
            ray_init=dict(_temp_dir='/old/tmp',runtime_env=dict(worker_process_setup_hook='acceptance_hook.install',
                env_vars=dict(SC2_BO_ADDRESS='/old/bo.json',SC2_TRAIN_SEED_PROTOCOL='same_uniform101',SC2_DIFFICULTY='VeryHard'))))

    def contract(self):
        def save(name,obj):
            path=self.parent/name
            path.parent.mkdir(parents=True,exist_ok=True)
            path.write_text(json.dumps(obj))
        for name in prefix_files():save(name,{})
        save('state.json',dict(phase='completed'))
        save('deployment.json',dict(runtime_sha='accepted-sha',difficulty='VeryHard',seed_protocol='same_uniform101',seed_group_mode='same',model_kind='qwen'))
        save('cpu/train2/resolved_config.json',self.cfg)
        for stage,games in [('pre',8),('train2',16),('post',8)]:
            result=dict(status='completed',process_exit_code=0,metrics_finite=True,
                episode_outcomes=dict(natural_games=games,truncated=0),training_updates=0,
                start_step=0,last_global_step=2,completed_steps=2,checkpoint_complete=True,checkpoint_files={})
            if stage=='train2':
                for name in ['data.pt']+[f'actor/{k}_world_size_8_rank_{r}.pt' for k in ('model','optim','extra_state') for r in range(8)]:
                    rel='checkpoints/global_step_2/'+name
                    path=self.parent/'runs/train2'/rel
                    path.parent.mkdir(parents=True,exist_ok=True)
                    path.write_bytes(b'x')
                    result['checkpoint_files'][rel]={'bytes':1}
            for name in ('result.json','.done'):save(f'runs/{stage}/{name}',result)
            save(f'runs/{stage}/manifest.json',dict(dirty=False,world_size=8,source_commit='accepted-sha'))
            save(f'acceptance-{stage}.json',dict(result=result,evidence=dict(consumed_answers=2,valid_consumed_answers=2)))
        return dict(version='accepted-same-seed-prefix-v1',parent=str(self.parent),parent_sha='accepted-sha',
            checkpoint=str(self.parent/'runs/train2/checkpoints/global_step_2'),start_step=2,target_step=96,
            driver_rng_unavailable_accepted=True,files={p:sha256(self.parent/p) for p in prefix_files()})

    def test_complete_prefix_and_no_silent_modified_evidence(self):
        c=self.contract()
        self.assertEqual(verify_contract(c),self.cfg)
        (self.parent/'runs/train2/.done').write_text('{}')
        with self.assertRaisesRegex(ValueError,'evidence changed'):verify_contract(c)

    def test_missing_optimizer_not_weights_only_resume(self):
        c=self.contract()
        (self.parent/'runs/train2/checkpoints/global_step_2/actor/optim_world_size_8_rank_3.pt').unlink()
        with self.assertRaises(FileNotFoundError):verify_contract(c)

    def test_no_unaccepted_driver_rng_gap_or_other_target(self):
        c=self.contract()
        for key,value in [('driver_rng_unavailable_accepted',False),('target_step',192),('start_step',72)]:
            bad=deepcopy(c);bad[key]=value
            with self.assertRaises(ValueError):verify_contract(bad)

    def test_training_semantics_not_normalized_away(self):
        old=normalized_protocol(self.cfg)
        c=deepcopy(self.cfg);c['trainer']['total_training_steps']=96;c['data']['train_files']='/new/data/train.parquet'
        self.assertEqual(old,normalized_protocol(c))
        for section,key,value in [('algorithm','sc2_policy_credit',{'enabled':False}),('env','seed',1)]:
            c=deepcopy(self.cfg);c[section][key]=value
            self.assertNotEqual(old,normalized_protocol(c))

    def test_explicit_resume_rejects_changed_protocol_checkpoint_and_auto(self):
        c=self.contract();path=self.parent/'contract.json';path.write_text(json.dumps(c))
        cfg=OmegaConf.create(deepcopy(self.cfg))
        cfg.trainer.update(dict(resume_mode='resume_path',resume_from_path=c['checkpoint'],
            sc2_checkpoint_resume=True,sc2_import_legacy_final=True,total_training_steps=96,
            sc2_policy_credit_resume_contract=str(path)))
        validate_resume(cfg)
        for key,value in [('resume_from_path','/other/global_step_2'),('resume_mode','auto'),('del_local_ckpt_after_load',True)]:
            bad=deepcopy(cfg);bad.trainer[key]=value
            with self.assertRaises(ValueError):validate_resume(bad)
        cfg.algorithm.sc2_policy_credit.min_valid_ratio=.1
        with self.assertRaisesRegex(ValueError,'changed the training protocol'):validate_resume(cfg)
