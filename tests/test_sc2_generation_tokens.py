"""CPU regression for the real FSDP-worker -> HF generation token boundary."""
import contextlib
import os
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch

import torch
from omegaconf import OmegaConf
from tensordict import TensorDict
from transformers import GenerationConfig, Qwen3Config, Qwen3ForCausalLM

from verl import DataProto
from verl.utils.sc2_action_support import ActionSupport, load_support
from verl.workers.rollout.hf_rollout import HFRollout
from test_sc2_action_support import CharTokenizer, query


class IdentitySharding(contextlib.AbstractContextManager):
    def __enter__(self): return self
    def __exit__(self, *args): return False
    def preprocess_data(self, data): return data
    def postprocess_data(self, data): return data


class GenerationTokensTest(unittest.TestCase):
    def setUp(self):
        self.tokenizer = CharTokenizer()
        # Exercise a supported target's real generation/cache path. GPT-2 takes
        # HFRollout's legacy explicit-position branch, unlike Qwen3 and SpB2.
        torch.manual_seed(0)
        self.model = Qwen3ForCausalLM(Qwen3Config(
            vocab_size=130, hidden_size=8, intermediate_size=16,
            num_hidden_layers=1, num_attention_heads=1, num_key_value_heads=1,
            head_dim=8, max_position_embeddings=256, eos_token_id=1,
            pad_token_id=0, attention_dropout=0., use_sliding_window=False)).eval()
        self.cfg = OmegaConf.create(dict(do_sample=True, temperature=.8,
            response_length=64, top_p=1., top_k=0, n=1,
            val_kwargs=dict(top_p=1., top_k=0, temperature=.8)))

    def prompts(self, **metadata):
        rows = [self.tokenizer.encode(query('- marine x 1')),
                self.tokenizer.encode('Game ended.')]
        width = max(map(len, rows))
        ids = torch.tensor([[0] * (width-len(row)) + row for row in rows])
        mask = (ids != 0).long()
        positions = (mask.cumsum(-1) - 1).clamp(min=0)
        return DataProto(batch=TensorDict(dict(input_ids=ids, attention_mask=mask,
            position_ids=positions), batch_size=2), meta_info=metadata)

    def worker_generate(self, rollout, generation_config, data):
        # Execute the production method, including its metadata overwrite. Only
        # GPU placement/offload/sharding/logging are replaced with CPU boundaries.
        import verl.workers.fsdp_workers as workers
        worker = NS(rollout=rollout, generation_config=generation_config,
            tokenizer=self.tokenizer, _is_rollout=True, _is_offload_param=False,
            rollout_sharding_manager=IdentitySharding())
        device = NS(current_device=lambda: 'cpu', empty_cache=lambda: None)
        with patch.object(workers, 'get_torch_device', return_value=device), \
             patch.object(workers, 'log_gpu_memory_usage'), \
             patch('verl.workers.rollout.hf_rollout.get_torch_device', return_value=device), \
             patch('torch.autocast', side_effect=lambda **kw: contextlib.nullcontext()):
            result = workers.ActorRolloutRefWorker.generate_sequences(worker, data)
        self.assertFalse(torch.cuda.is_initialized())
        return result

    def test_worker_to_real_HF_missing_spb_pad_and_qwen_eos_list(self):
        for eos, pad in [(1, None), ([1, 0], 0)]:
            for validate in (False, True):
                with self.subTest(eos=eos, pad=pad, validate=validate):
                    rollout = HFRollout(self.model, self.cfg)
                    rollout.action_support = ActionSupport(self.tokenizer, 64)
                    generation_config = GenerationConfig(eos_token_id=eos, pad_token_id=pad)
                    before = generation_config.to_dict()
                    prompt = self.prompts(validate=validate)
                    seen = {}
                    real_generate = self.model.generate
                    real_prepare = self.model.prepare_inputs_for_generation
                    positions = []
                    def prepared(*args, **kw):
                        model_inputs = real_prepare(*args, **kw)
                        positions.append(model_inputs['position_ids'][:, -1].clone())
                        return model_inputs
                    def traced(**kw):
                        self.assertNotIn('position_ids', kw)
                        seen['eos'], seen['pad'] = kw['eos_token_id'], kw['pad_token_id']
                        kw['output_scores'] = True
                        seen['output'] = real_generate(**kw)
                        return seen['output']
                    with patch.object(self.model, 'generate', side_effect=traced), \
                         patch.object(self.model, 'prepare_inputs_for_generation', side_effect=prepared):
                        result = self.worker_generate(rollout, generation_config, prompt)
                    self.assertGreater(len(positions), 1)
                    for step, actual in enumerate(positions):
                        torch.testing.assert_close(actual, prompt.batch['position_ids'][:, -1] + step)
                    self.assertEqual((seen['eos'], seen['pad']), (1, 0))
                    self.assertEqual(generation_config.to_dict(), before)
                    response = result.batch['responses']
                    self.assertEqual(response.shape, (2, 64))
                    self.assertEqual(response[1].tolist(), [1] + [0] * 63)
                    # EOS is active; every subsequent PAD is masked. The live
                    # plan remains complete and unmodified through worker/HF.
                    length = response[0].tolist().index(1) + 1
                    expected_mask = torch.zeros_like(response)
                    expected_mask[0, :length] = 1
                    expected_mask[1, 0] = 1
                    torch.testing.assert_close(result.batch['attention_mask'][:, -64:], expected_mask)
                    answer = self.tokenizer.decode(response[0])
                    self.assertTrue(answer.startswith('<answer>\n- marine'))
                    self.assertTrue(answer.endswith('</answer>'))
                    torch.testing.assert_close(result.batch['prompts'], prompt.batch['input_ids'])
                    # Same raw model weights: sampled and teacher distributions
                    # agree at every active generated token, including EOS.
                    with torch.no_grad():
                        raw = self.model(result.batch['input_ids'],
                            attention_mask=result.batch['attention_mask'],
                            position_ids=result.batch['position_ids']).logits[:, -65:-1] / .8
                        masked = rollout.action_support.mask_teacher(raw, result.batch['input_ids'], response)
                        teacher = masked.log_softmax(-1).gather(-1, response[..., None]).squeeze(-1)
                        scores = torch.stack(seen['output'].scores, dim=1)
                        n = scores.shape[1]
                        sampled = scores.log_softmax(-1).gather(-1, response[:, :n, None]).squeeze(-1)
                    active = expected_mask[:, :n].bool()
                    torch.testing.assert_close(sampled[active], teacher[:, :n][active], atol=2e-5, rtol=2e-5)

    def test_default_off_preserves_legacy_generation_config_and_pad_fallback(self):
        for eos, pad, expected_pad in [(1, None, 1), ([1, 0], 0, 0)]:
            with self.subTest(eos=eos):
                rollout = HFRollout(self.model, self.cfg)
                seen = {}
                def generated(**kw):
                    seen.update(kw)
                    return NS(sequences=torch.cat([kw['input_ids'], torch.ones(2, 1, dtype=torch.long)], dim=1))
                with patch.object(self.model, 'generate', side_effect=generated):
                    self.worker_generate(rollout, GenerationConfig(eos_token_id=eos, pad_token_id=pad), self.prompts())
                self.assertEqual(seen['eos_token_id'], eos)
                self.assertEqual(seen['pad_token_id'], expected_pad)
                self.assertNotIn('logits_processor', seen)

    def test_incompatible_tokens_and_budget_still_fail_before_model_generation(self):
        for eos, pad, budget in [(3, 0, 64), ([1, 3], 0, 64), ([], 0, 64),
                                 (0, 0, 64), (1, 2, 64), (1, None, 63)]:
            with self.subTest(eos=eos, pad=pad, budget=budget):
                rollout = HFRollout(self.model, self.cfg)
                rollout.action_support = ActionSupport(self.tokenizer, 64)
                with patch.object(self.model, 'generate') as generate, self.assertRaises(ValueError):
                    self.worker_generate(rollout, GenerationConfig(eos_token_id=eos, pad_token_id=pad),
                                         self.prompts(response_length=budget))
                generate.assert_not_called()

    def test_explicit_conflicting_eos_override_still_fails(self):
        rollout = HFRollout(self.model, self.cfg)
        rollout.action_support = ActionSupport(self.tokenizer, 64)
        with patch.dict(os.environ, SPB1_ROLLOUT_EOS_TOKEN_ID='3'), \
             patch.object(self.model, 'generate') as generate, self.assertRaises(ValueError):
            self.worker_generate(rollout, GenerationConfig(eos_token_id=1, pad_token_id=None), self.prompts())
        generate.assert_not_called()

    def test_registered_spb_and_qwen_metadata_resolve_without_weight_loading(self):
        for env in ('SC2_TEST_SPB_METADATA_PATH', 'SC2_TEST_QWEN_METADATA_PATH'):
            path = os.environ[env]  # Required fixture, not a silent skip.
            support = load_support(path, 192)
            config = GenerationConfig.from_pretrained(path, local_files_only=True)
            before = config.to_dict()
            self.assertEqual(support.generation_token_ids(config.eos_token_id, config.pad_token_id),
                             (151645, 151643))
            self.assertEqual(config.to_dict(), before)
            if 'SPB' in env:
                self.assertEqual((config.eos_token_id, config.pad_token_id), (151645, None))
            else:
                self.assertEqual((config.eos_token_id, config.pad_token_id), ([151645, 151643], 151643))
        self.assertFalse(torch.cuda.is_initialized())


if __name__ == '__main__': unittest.main()
