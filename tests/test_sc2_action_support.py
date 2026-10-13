"""Real grammar / validator / CPU HF / actor-reference tests; no SC2/GPU."""
import os
import random
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch

import torch
from omegaconf import OmegaConf
from transformers import GPT2Config, GPT2LMHeadModel, LogitsProcessorList

from verl.utils.sc2_action_support import (
    ActionSupport, END_MARKER, MARKER, PlanSupport, candidate_counts, load_support, validate_config,
)
from test_r6_format_reward import strict_validator
from test_original_bo_segment import pipeline


class CharTokenizer:
    eos_token_id = 1
    pad_token_id = 0
    all_special_ids = [0, 1]
    def encode(self, text, **kw): return [ord(ch) + 2 for ch in text]
    def decode(self, tokens, skip_special_tokens=False, **kw):
        return ''.join(chr(int(i) - 2) for i in tokens if int(i) > 1)


def query(body='- marine x 2\n- barracks x 1'):
    return MARKER + '\n' + body + '\n' + END_MARKER


def sample(support, rng):
    state = support.start()
    tokens = []
    while not state.done:
        token = rng.choice(state.allowed())
        tokens.append(token)
        state.advance(token)
        if len(tokens) > support.budget:
            raise AssertionError('generation exceeded budget')
    return tokens


def padded(tokens, n, pad=0): return tokens + [pad] * (n - len(tokens))


class ActionSupportTest(unittest.TestCase):
    def setUp(self): self.tokenizer = CharTokenizer()

    def test_current_candidates_not_global_table_or_example_and_fail_closed(self):
        text = 'Global table: banshee\n' + query() + '\nExample:\n- tank x 9'
        self.assertEqual(candidate_counts(text), {'marine': 2, 'barracks': 1})
        self.assertEqual(candidate_counts('Game ended.'), {})
        self.assertEqual(candidate_counts(query('none')), {})
        for bad in (query('- marine x 513'), query('- marine x 0'), query('- marine\nnot a list'),
                    query() + query(), MARKER + '\n- marine x 2'):
            with self.subTest(bad=bad), self.assertRaises(ValueError): candidate_counts(bad)

    def test_random_plans_pass_real_validator_and_never_exceed_budget_or_quota(self):
        rng = random.Random(7)
        validate = strict_validator()
        prompt = query('- marine x 3\n- techlab barracks x 1\n- Launch OFFENSE with 12 marine x 1')
        with patch.dict(os.environ, SC2_ORIGINAL_BO_SEGMENT='1'):
            for budget in (45, 64, 96, 192):
                support = PlanSupport(self.tokenizer, candidate_counts(prompt), budget)
                for _ in range(30):
                    tokens = sample(support, rng)
                    answer = self.tokenizer.decode(tokens)
                    self.assertTrue(validate(prompt, answer)[0], (answer, validate(prompt, answer)))
                    self.assertEqual(tokens[-1], self.tokenizer.eos_token_id)
                    self.assertTrue(answer.endswith('</answer>'))
                    self.assertLessEqual(len(tokens), budget)

    def test_observed_degenerate_answers_rejected_not_repaired(self):
        support = PlanSupport(self.tokenizer, candidate_counts(query()), 192)
        for text in ('', '</' * 40, ' marine x 1', '<answer>\n- marine x 3\n</answer>',
                     '<answer>\n- banshee\n</answer>'):
            tokens = self.tokenizer.encode(text) + [1]
            with self.subTest(text=text), self.assertRaises(ValueError): support.allowed(tokens)

    def test_empty_slot_eos_only_no_synthetic_action_and_padding(self):
        support = PlanSupport(self.tokenizer, {}, 32)
        self.assertEqual(support.allowed([]), (1,))
        self.assertEqual(support.allowed([1, 0, 0]), (0,))
        with self.assertRaises(ValueError): support.allowed([1, 2])
        with self.assertRaises(ValueError): PlanSupport(self.tokenizer, {'marine': 1}, 5)

    def test_whole_plan_reaches_real_executor_without_fallback(self):
        answer = '<answer>\n- marine x 2\n- marine\n</answer>'
        support = PlanSupport(self.tokenizer, {'marine': 42}, 192)
        support.allowed(self.tokenizer.encode(answer) + [1])
        trace = pipeline(answer, True)
        self.assertTrue(trace['valid'], trace['reason'])
        self.assertNotIn('BO fallback', trace['console'])
        self.assertEqual(len(trace['planner_queue']), 3)
        self.assertEqual(trace['rule_added'], [])

    def test_generation_teacher_support_probability_and_finite_gradient_match(self):
        support = ActionSupport(self.tokenizer, 64)
        prompts = [query(), query('- supplydepot x 1')]
        width = max(len(p) for p in prompts)
        prompt_ids = torch.tensor([[0] * (width-len(p)) + self.tokenizer.encode(p) for p in prompts])
        responses = torch.tensor([padded(sample(support.for_prompt(tuple(row.tolist())), random.Random(i)), 64)
                                  for i, row in enumerate(prompt_ids)])
        ids = torch.cat([prompt_ids, responses], dim=1)
        raw = torch.randn(2, 64, 130, requires_grad=True)
        masked = support.mask_teacher(raw, ids, responses)
        processor = support.generation_processor(prompt_ids, 1, 0, 64)
        for col in range(64):
            gen = processor(ids[:, :width+col], raw[:, col])
            torch.testing.assert_close(gen.softmax(-1), masked[:, col].softmax(-1))
        probs = masked.softmax(-1)
        entropy = masked.logsumexp(-1) - (probs * masked).sum(-1)
        lp = masked.log_softmax(-1).gather(-1, responses[..., None]).squeeze(-1)
        (-lp.mean() - .01 * entropy.mean()).backward()
        self.assertTrue(torch.isfinite(entropy).all())
        self.assertTrue(torch.isfinite(raw.grad).all())
        self.assertTrue((raw.grad[masked == torch.finfo(masked.dtype).min] == 0).all())
        with self.assertRaises(ValueError): support.generation_processor(prompt_ids, 3, 0, 64)

    def test_actual_HF_rollout_overcomes_illegal_preference_and_keeps_raw_tokens(self):
        from verl import DataProto
        from tensordict import TensorDict
        from verl.workers.rollout.hf_rollout import HFRollout
        model = GPT2LMHeadModel(GPT2Config(vocab_size=130, n_positions=256, n_embd=8,
             n_layer=1, n_head=1, eos_token_id=1, pad_token_id=0)).eval()
        generate = model.generate
        class PreferIllegal:
            def __call__(self, ids, scores):
                scores[:, ord('<')+2] += 1000  # would repeat angle brackets without support
                return scores
        def traced(**kw):
            kw['logits_processor'] = LogitsProcessorList([PreferIllegal(), *kw.get('logits_processor', [])])
            return generate(**kw)
        model.generate = traced
        cfg = OmegaConf.create(dict(do_sample=True, temperature=.8, response_length=64, top_p=1., top_k=0, n=1))
        rollout = HFRollout(model, cfg)
        rollout.action_support = ActionSupport(self.tokenizer, 64)
        prompt = torch.tensor([self.tokenizer.encode(query())])
        data = DataProto(batch=TensorDict(dict(input_ids=prompt, attention_mask=torch.ones_like(prompt),
            position_ids=torch.arange(prompt.shape[1])[None, :]), batch_size=1),
            meta_info=dict(eos_token_id=1, pad_token_id=0))
        with patch('torch.autocast', return_value=__import__('contextlib').nullcontext()), \
             patch('verl.workers.rollout.hf_rollout.get_torch_device', return_value=NS(empty_cache=lambda: None)):
            result = rollout._generate_minibatch(data)
        answer = self.tokenizer.decode(result.batch['responses'][0])
        with patch.dict(os.environ, SC2_ORIGINAL_BO_SEGMENT='1'):
            self.assertTrue(strict_validator()(query(), answer)[0], answer)
        torch.testing.assert_close(result.batch['prompts'], prompt)
        self.assertFalse(torch.cuda.is_initialized())

    def test_actual_actor_and_reference_forward_mask_identically(self):
        import verl.workers.actor.dp_actor as module
        prompt = self.tokenizer.encode(query())
        support = ActionSupport(self.tokenizer, 64)
        response = padded(sample(support.for_prompt(tuple(prompt)), random.Random(0)), 64)
        class Model(torch.nn.Module):
            def __init__(self):
                super().__init__()
                self.scores = torch.nn.Parameter(torch.randn(1, len(prompt)+64, 130))
            def forward(self, **kw): return NS(logits=self.scores * 1.)
        cfg = OmegaConf.create(dict(ulysses_sequence_parallel_size=1, use_torch_compile=False, fp32_normalization=True))
        actor, ref = [module.DataParallelPPOActor(cfg, Model()) for _ in range(2)]
        ref.actor_module.load_state_dict(actor.actor_module.state_dict())
        for worker in (actor, ref): worker.action_support, worker.device_name = support, 'cpu'
        ids = torch.tensor([prompt + response])
        data = dict(input_ids=ids, responses=torch.tensor([response]), attention_mask=torch.ones_like(ids),
                    position_ids=torch.arange(ids.shape[1])[None, :])
        cpu_lp = lambda logits, labels: logits.log_softmax(-1).gather(-1, labels[..., None]).squeeze(-1)
        with patch.object(module, 'logprobs_from_logits', cpu_lp):
            ent, lp = actor._forward_micro_batch(data, .8, True)
            _, ref_lp = ref._forward_micro_batch(data, .8, True)
        torch.testing.assert_close(lp, ref_lp)
        torch.testing.assert_close((lp-ref_lp).exp(), torch.ones_like(lp))
        (-lp.mean() - .01 * ent.mean()).backward()
        self.assertTrue(torch.isfinite(actor.actor_module.scores.grad).all())

    def test_actual_sampled_HF_probabilities_match_teacher_forced_model(self):
        # Unlike equal actor/ref alone, this checks the actual autoregressive
        # HF sampling distribution against a full teacher-forced forward.
        model = GPT2LMHeadModel(GPT2Config(vocab_size=130, n_positions=256, n_embd=8,
            n_layer=1, n_head=1, eos_token_id=1, pad_token_id=0,
            resid_pdrop=0., embd_pdrop=0., attn_pdrop=0.)).eval()
        support = ActionSupport(self.tokenizer, 64)
        prompt = torch.tensor([self.tokenizer.encode(query())])
        with torch.no_grad():
            out = model.generate(prompt, attention_mask=torch.ones_like(prompt), max_new_tokens=64,
                do_sample=True, temperature=.8, top_p=1., top_k=0,
                logits_processor=LogitsProcessorList([support.generation_processor(prompt, 1, 0, 64)]),
                return_dict_in_generate=True, output_scores=True)
            sampled = out.sequences[:, prompt.shape[1]:]
            response = torch.tensor([padded(sampled[0].tolist(), 64)])
            ids = torch.cat([prompt, response], dim=1)
            raw = model(ids, attention_mask=torch.ones_like(ids)).logits[:, -65:-1] / .8
            masked = support.mask_teacher(raw, ids, response)
            teacher_lp = masked.log_softmax(-1).gather(-1, response[..., None]).squeeze(-1)
            sample_lp = torch.stack(out.scores, dim=1).log_softmax(-1).gather(-1, sampled[..., None]).squeeze(-1)
        torch.testing.assert_close(sample_lp, teacher_lp[:, :sampled.shape[1]], atol=2e-5, rtol=2e-5)
        self.assertFalse(torch.cuda.is_initialized())

    def test_real_tokenizer_complete_plans_and_no_thinking_mask_compatible(self):
        from verl.utils.sc2_no_thinking import load_constraint
        path = os.environ['SC2_TEST_TOKENIZER_PATH']
        support, no_thinking = load_support(path, 192), load_constraint(path)
        t = support.tokenizer
        prompt = t.apply_chat_template([dict(role='user', content=query())], tokenize=False, add_generation_prompt=True)
        prompt_ids = tuple(t.encode(prompt, add_special_tokens=False))
        for seed in range(16):
            tokens = sample(support.for_prompt(prompt_ids), random.Random(seed))
            no_thinking.prefix_state(tokens)
            text = t.decode(tokens, skip_special_tokens=True, clean_up_tokenization_spaces=False)
            with patch.dict(os.environ, SC2_ORIGINAL_BO_SEGMENT='1'):
                self.assertTrue(strict_validator()(query(), text)[0], text)
        self.assertFalse(torch.cuda.is_initialized())

    def test_config_requires_matched_workers_protocol_budget_and_untruncated_sampling(self):
        cfg = OmegaConf.create(dict(env=dict(env_name='SC2'),
            actor_rollout_ref={k: dict(sc2_action_tokenizer_path='/tokenizer', sc2_action_response_length=192,
                name='hf', response_length=192, n=1, multi_turn=dict(enable=False), top_p=1., top_k=0,
                val_kwargs=dict(top_p=1., top_k=0)) for k in ('actor', 'ref', 'rollout')},
            ray_init=dict(runtime_env=dict(env_vars=dict(SC2_PLANNER_PROTOCOL='legacy', SC2_ORIGINAL_BO_SEGMENT='1')))))
        validate_config(cfg)
        for key, bad in [('actor_rollout_ref.ref.sc2_action_tokenizer_path', None),
                         ('actor_rollout_ref.actor.sc2_action_response_length', 96),
                         ('actor_rollout_ref.rollout.top_p', .9),
                         ('actor_rollout_ref.rollout.val_kwargs.top_p', .9),
                         ('actor_rollout_ref.rollout.n', 2)]:
            before = OmegaConf.select(cfg, key)
            OmegaConf.update(cfg, key, bad)
            with self.assertRaises(ValueError): validate_config(cfg)
            OmegaConf.update(cfg, key, before)
        validate_config(OmegaConf.create(dict(actor_rollout_ref={})))


if __name__ == '__main__': unittest.main()
