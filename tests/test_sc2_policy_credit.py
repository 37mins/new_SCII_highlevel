"""Actual CPU GiGPO, validity-credit, and trainer collection boundary regressions."""
import ast
from copy import deepcopy
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace as NS
import unittest
from unittest.mock import Mock

import numpy as np
from omegaconf import OmegaConf
import torch

from test_sc2_task_signal import group
from agent_system.reward_manager.episode import EpisodeRewardManager
from gigpo.core_gigpo import compute_step_discounted_returns
from verl.trainer.ppo.ray_trainer import RayPPOTrainer, compute_advantage
from verl.trainer.ppo.sc2_policy_credit import (
    apply_credit, check_same_seed_groups, check_seed_groups, inspect_batch, validate_config,
)


def config(path):
    return OmegaConf.create(dict(
        algorithm=dict(adv_estimator='gigpo', use_kl_in_reward=False,
                       use_pf_ppo=False, filter_groups=dict(enable=False),
                       sc2_policy_credit=dict(enabled=True, invalid_advantage_penalty=.1, min_valid_ratio=.5)),
        reward_model=dict(enable=False, reward_manager='episode'),
        actor_rollout_ref=dict(rollout=dict(n=1, multi_turn=dict(enable=False))),
        env=dict(env_name='SC2', rollout=dict(n=8)),
        ray_init=dict(runtime_env=dict(env_vars=dict(SC2_ORIGINAL_GAME_SEEDS='0'))),
        trainer=dict(default_local_dir=str(path), resume_mode='disable', val_only=False)))


def batch(valids):
    # First four games win, last four lose; both valid and invalid answers occur.
    data = group([20.] * 4 + [-50.] * 4, calls=[2] * 8)
    data.non_tensor_batch['is_action_valid'] = np.asarray(valids, dtype=bool)
    data.non_tensor_batch['policy_action_applied'] = np.ones(16, dtype=bool)
    data.non_tensor_batch['is_tool_query'] = np.zeros(16, dtype=bool)
    reward = EpisodeRewardManager(NS(decode=lambda *a, **kw: ''), 0)(data)
    data.batch['token_level_rewards'] = reward.clone()
    data.batch['token_level_scores'] = reward.clone()
    data.batch['step_rewards'] = compute_step_discounted_returns(data, 1.)
    return compute_advantage(data, 'gigpo', gigpo_mode='mean_norm')


class PolicyCreditTest(unittest.TestCase):
    def test_cross_seed_ablation_requires_explicit_matching_reset_protocol(self):
        cfg = config('/tmp/unused')
        cfg.algorithm.sc2_policy_credit.seed_group_mode = 'mixed_seed_ablation'
        with self.assertRaises(ValueError): validate_config(cfg)
        cfg.ray_init.runtime_env.env_vars.SC2_TRAIN_SEED_PROTOCOL = 'independent_uniform101'
        validate_config(cfg)
        check_seed_groups(list(range(8)), ['g']*8, 'mixed_seed_ablation')
        check_seed_groups([49]*8, ['g']*8, 'mixed_seed_ablation')  # collisions allowed
        for seeds in (None, [101]*8, [-1]*8):
            with self.assertRaises(ValueError): check_seed_groups(seeds, ['g']*8, 'mixed_seed_ablation')
        cfg.algorithm.sc2_policy_credit.seed_group_mode = 'same'
        with self.assertRaises(ValueError): validate_config(cfg)
        cfg.ray_init.runtime_env.env_vars.SC2_TRAIN_SEED_PROTOCOL = 'same_uniform101'
        validate_config(cfg)

    def test_invalid_winner_no_positive_credit_valid_rows_and_raw_data_unchanged(self):
        data = batch([True, False] * 8)
        before = {k: v.clone() for k, v in data.batch.items()}
        self.assertTrue((before['advantages'][1] > 0).all())
        evidence = apply_credit(data, .1)
        self.assertGreater(evidence['policy_credit/invalid_positive_tokens_removed'], 0)
        self.assertTrue((data.batch['advantages'][1::2] <= -.1).all())
        torch.testing.assert_close(data.batch['advantages'][::2], before['advantages'][::2])
        for key in before.keys() - {'advantages', 'returns'}:
            torch.testing.assert_close(data.batch[key], before[key])
        torch.testing.assert_close(data.batch['returns'], data.batch['advantages'])

    def test_all_invalid_constant_penalty_does_not_disappear_after_centering(self):
        data = batch([False] * 16)
        apply_credit(data, .1)
        self.assertTrue((data.batch['advantages'] <= -.1).all())
        # Production additionally stops this batch before advantage/update work.
        self.assertEqual(inspect_batch(data, .5)['decision'], 'stop')

    def test_valid_batch_no_change_and_negative_invalid_is_not_weakened(self):
        data = batch([True] * 16)
        before = data.batch['advantages'].clone()
        apply_credit(data, .1)
        torch.testing.assert_close(data.batch['advantages'], before)
        data.non_tensor_batch['is_action_valid'][15] = False
        apply_credit(data, .1)
        torch.testing.assert_close(data.batch['advantages'][15], before[15] - .1)

    def test_padding_and_zero_advantage(self):
        data = batch([False] * 16)
        data.batch['advantages'].zero_()
        data.batch['response_mask'][:, -1] = 0
        apply_credit(data, .1)
        self.assertTrue((data.batch['advantages'][:, :-1] == -.1).all())
        self.assertTrue((data.batch['advantages'][:, -1] == 0).all())

    def test_permutation_does_not_change_credit(self):
        a, b = batch([True, False] * 8), batch([True, False] * 8)
        apply_credit(a, .1)
        order = torch.arange(15, -1, -1)
        b.reorder(order)
        apply_credit(b, .1)
        torch.testing.assert_close(b.batch['advantages'], a.batch['advantages'][order])

    def test_negative_policy_gradient_reduces_invalid_answer_probability(self):
        data = batch([False] * 16)
        data.batch['advantages'].fill_(35.)  # winning fallback must not reinforce this
        apply_credit(data, .1)
        logits = torch.zeros(2, requires_grad=True)
        optimizer = torch.optim.SGD([logits], lr=.1)
        before = logits.softmax(0)[0].item()
        loss = -data.batch['advantages'][0, 0] * logits.log_softmax(0)[0]
        loss.backward()
        optimizer.step()
        self.assertLess(logits.softmax(0)[0].item(), before)

    def test_config_rejects_resume_cross_seed_and_incompatible_objectives(self):
        cfg = config('/tmp/unused')
        validate_config(cfg)
        for field, value in [('trainer.resume_mode', 'auto'),
                             ('algorithm.use_kl_in_reward', True),
                             ('algorithm.sc2_policy_credit.min_valid_ratio', 0),
                             ('algorithm.sc2_policy_credit.invalid_advantage_penalty', float('nan')),
                             ('ray_init.runtime_env.env_vars.SC2_ORIGINAL_GAME_SEEDS', '1')]:
            bad = deepcopy(cfg)
            OmegaConf.update(bad, field, value)
            with self.subTest(field=field), self.assertRaises(ValueError):
                validate_config(bad)

    def test_actual_seed_evidence_not_just_config_or_uid(self):
        check_same_seed_groups([49] * 8, ['g'] * 8)
        check_same_seed_groups([1, 1, 2, 2], ['a', 'a', 'b', 'b'])
        for seeds, ids in [(None, ['g'] * 8), ([49, 97, 53, 5, 33, 65, 62, 51], ['g'] * 8),
                           ([1], ['g']), ([1, 1], ['g'])]:
            with self.assertRaises(ValueError):
                check_same_seed_groups(seeds, ids)

    def test_missing_false_or_nonboolean_consumption_evidence_fails_closed(self):
        for key, value in [('policy_action_applied', False), ('active_masks', False),
                           ('is_action_valid', float('nan')), ('is_tool_query', True)]:
            data = batch([True] * 16)
            data.non_tensor_batch[key] = np.full(16, value)
            with self.subTest(key=key), self.assertRaises(ValueError):
                inspect_batch(data, .5)
        data = batch([True] * 16)
        del data.non_tensor_batch['is_action_valid']
        with self.assertRaises(ValueError): inspect_batch(data, .5)

    def trainer(self, path, data):
        trainer = RayPPOTrainer.__new__(RayPPOTrainer)
        trainer.config = config(path)
        trainer.global_steps = 1
        trainer.envs = object()
        trainer.actor_rollout_wg = Mock()
        trainer.traj_collector = NS(multi_turn_loop=Mock(return_value=data))
        return trainer

    def test_actual_collection_stops_bad_batch_without_retry_or_optimizer_rpc(self):
        with tempfile.TemporaryDirectory() as path:
            trainer = self.trainer(path, batch([False] * 16))
            with self.assertRaisesRegex(RuntimeError, 'before PPO'):
                trainer._collect_training_batch(object())
            trainer.traj_collector.multi_turn_loop.assert_called_once()
            self.assertEqual(trainer.actor_rollout_wg.mock_calls, [])
            row = json.loads((Path(path) / 'sc2_policy_credit_audit.jsonl').read_text())
            self.assertEqual(row['decision'], 'stop')
            self.assertEqual(row['optimizer_updates_for_this_batch'], 0)

    def test_actual_collection_accepts_threshold_and_default_off_preserves_old_path(self):
        with tempfile.TemporaryDirectory() as path:
            data = batch([True, False] * 8)
            trainer = self.trainer(path, data)
            self.assertIs(trainer._collect_training_batch(object()), data)
            trainer.config.algorithm.sc2_policy_credit.enabled = False
            trainer.traj_collector.multi_turn_loop.return_value = batch([False] * 16)
            self.assertIsNotNone(trainer._collect_training_batch(object()))
            rows = (Path(path) / 'sc2_policy_credit_audit.jsonl').read_text().splitlines()
            self.assertEqual(len(rows), 1)

    def test_real_fit_places_credit_after_centering_before_actor_update(self):
        source = Path(__file__).parents[1] / 'verl/trainer/ppo/ray_trainer.py'
        tree = ast.parse(source.read_text())
        fit = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == 'fit')
        calls = {name: [n.lineno for n in ast.walk(fit) if isinstance(n, ast.Call)
                 and ((isinstance(n.func, ast.Name) and n.func.id == name)
                   or (isinstance(n.func, ast.Attribute) and n.func.attr == name))]
                 for name in ('_collect_training_batch', 'compute_advantage', 'apply_credit', 'update_actor')}
        self.assertLess(calls['_collect_training_batch'][0], calls['compute_advantage'][0])
        self.assertLess(calls['compute_advantage'][0], calls['apply_credit'][0])
        self.assertLess(calls['apply_credit'][0], calls['update_actor'][0])

    def test_actual_collector_rejects_cross_seed_before_model_generation(self):
        from agent_system.multi_turn_rollout.rollout_loop import TrajectoryCollector
        collector = TrajectoryCollector.__new__(TrajectoryCollector)
        collector.config = config('/tmp/unused')
        data = batch([True] * 16)
        envs = NS(is_train=True, envs=NS(last_reset_seeds=list(range(16))),
                  reset=Mock(return_value=({'text':['obs']*16}, [{}]*16)))
        actor = Mock()
        with self.assertRaisesRegex(ValueError, 'actual game seed'):
            collector.vanilla_multi_turn_loop(data, actor, envs)
        self.assertEqual(actor.mock_calls, [])
        envs.reset.assert_called_once()

    def test_shipped_config_is_default_off(self):
        shipped=OmegaConf.load(Path(__file__).parents[1]/'verl/trainer/config/ppo_trainer.yaml')
        self.assertFalse(shipped.algorithm.sc2_policy_credit.enabled)
        self.assertEqual(shipped.algorithm.sc2_policy_credit.min_valid_ratio,.5)


if __name__ == '__main__':
    unittest.main()
