"""Default-off canonical BO decoding support shared by HF and PPO/reference.

This is a NEW restricted policy, not a parser repair or a learned-validity claim.
The model chooses action order, counts and when to finish; no expert plan is added.
"""
from collections import Counter
from functools import lru_cache
import hashlib
import json
import re


VERSION = 'sc2-canonical-bo-support-v1'
MARKER = 'The remaining BO list in this phase:'
END_MARKER = 'Use only exact canonical names that occur in the remaining BO list above.'


def candidate_counts(prompt):
    """Accept only the actual legacy/original-count query, not a global unit table."""
    if MARKER not in prompt:
        # Finished vector slots still participate in generation, but their EOS
        # is not a policy action. Never invent a BO for a missing-context slot.
        return Counter()
    if prompt.count(MARKER) != 1 or END_MARKER not in prompt.split(MARKER, 1)[1]:
        raise ValueError('SC2 action support requires one complete canonical BO section')
    section = prompt.split(MARKER, 1)[1].split(END_MARKER, 1)[0].strip()
    if section == 'none':
        return Counter()
    counts = Counter()
    for line in section.splitlines():
        match = re.fullmatch(r'- ([A-Za-z0-9 ,\-]+?)(?: x ([0-9]+))?', line.strip())
        if not match:
            raise ValueError('SC2 action support received an unsupported BO entry')
        name, count = match.group(1), int(match.group(2) or 1)
        if count < 1:
            raise ValueError('SC2 action support requires positive candidate counts')
        counts[name] += count
    if not counts or len(counts) > 64 or any(n > 512 for n in counts.values()):
        raise ValueError('SC2 action support BO bounds exceeded; no silent clipping')
    return counts


class PlanSupport:
    """Token-sequence grammar with cumulative quotas and an explicit EOS budget.

    Canonical tokenizations are intentionally a subset of valid text spellings.
    Each sequence ends at a complete line, making branches prefix-free.
    """
    def __init__(self, tokenizer, counts, budget):
        self.tokenizer, self.counts, self.budget = tokenizer, counts, budget
        self.eos, self.pad = tokenizer.eos_token_id, tokenizer.pad_token_id
        if self.eos is None or self.pad is None or budget < 1:
            raise ValueError('SC2 action support requires EOS, PAD and positive token budget')
        self.opening = self.encode('<answer>\n')
        self.closing = self.encode('</answer>') + (self.eos,)
        self.actions = []
        for name, count in sorted(counts.items()):
            for n in range(1, count + 1):
                # Keep both permitted one-item spellings; no count rounding.
                spellings = [f'- {name} x {n}\n']
                if n == 1:
                    spellings.append(f'- {name}\n')
                for text in spellings:
                    self.actions.append((self.encode(text), (name, n)))
        if counts and len(self.opening) + min(len(a) for a, _ in self.actions) + len(self.closing) > budget:
            raise ValueError('SC2 action support token budget cannot fit a complete plan')

    def encode(self, text):
        tokens = tuple(self.tokenizer.encode(text, add_special_tokens=False))
        if not tokens or set(tokens).intersection(self.tokenizer.all_special_ids):
            raise ValueError('SC2 action grammar text contains special/empty tokens')
        if self.tokenizer.decode(tokens, skip_special_tokens=False, clean_up_tokenization_spaces=False) != text:
            raise ValueError('SC2 action grammar tokenizer round-trip failed')
        return tokens

    def start(self):
        return PlanState(self)

    def allowed(self, prefix):
        state = self.start()
        for token in prefix:
            state.advance(int(token))
        return state.allowed()


class PlanState:
    def __init__(self, support):
        self.support = support
        self.remaining = support.counts.copy()
        self.used = 0
        self.done = False
        self.paths = [(support.opening, 'open')] if self.remaining else [((support.eos,), 'close')]

    def allowed(self):
        if self.done:
            return (self.support.pad,)
        return tuple(sorted({tokens[0] for tokens, _ in self.paths}))

    def advance(self, token):
        if self.done:
            if token != self.support.pad:
                raise ValueError('SC2 action support found non-padding after EOS')
            return
        paths = [(tokens[1:], event) for tokens, event in self.paths if tokens[0] == token]
        if not paths:
            raise ValueError('SC2 response token is outside the canonical action support')
        self.used += 1
        finished = [event for tokens, event in paths if not tokens]
        if not finished:
            self.paths = paths
            return
        if len(finished) != 1 or len(paths) != 1:
            raise ValueError('SC2 action tokenization is not prefix-free')
        event = finished[0]
        if event == 'close':
            self.done = True
            return
        if event != 'open':
            name, count = event
            self.remaining[name] -= count
        left = self.support.budget - self.used
        self.paths = [(tokens, action) for tokens, action in self.support.actions
                      if action[1] <= self.remaining[action[0]]
                      and len(tokens) + len(self.support.closing) <= left]
        if event != 'open':
            self.paths.append((self.support.closing, 'close'))
        if not self.paths:
            raise ValueError('SC2 action support has no complete continuation')


class ActionSupport:
    def __init__(self, tokenizer, budget):
        self.tokenizer, self.budget = tokenizer, budget

    @lru_cache(maxsize=128)
    def for_prompt(self, tokens):
        text = self.tokenizer.decode(tokens, skip_special_tokens=False, clean_up_tokenization_spaces=False)
        return PlanSupport(self.tokenizer, candidate_counts(text), self.budget)

    def generation_token_ids(self, eos, pad):
        """Resolve model metadata to this restricted policy's single EOS/PAD.

        SpB omits PAD in generation_config; Qwen also lists PAD as a stop token.
        The grammar already emits only tokenizer EOS, then tokenizer PAD. Accept
        those compatible metadata forms, without changing the grammar/teacher
        support or mutating the model config. Conflicting explicit IDs still fail.
        """
        expected_eos, expected_pad = self.tokenizer.eos_token_id, self.tokenizer.pad_token_id
        eos_ids = list(eos) if isinstance(eos, (list, tuple)) else [eos]
        if eos is None:
            eos_ids = [expected_eos]
        if (expected_eos is None or expected_pad is None
                or expected_eos not in eos_ids
                or any(token not in (expected_eos, expected_pad) for token in eos_ids)
                or pad not in (None, expected_pad)):
            raise ValueError(
                f'SC2 action support incompatible generation tokens: EOS={eos!r}, PAD={pad!r}; '
                f'canonical EOS={expected_eos!r}, PAD={expected_pad!r}')
        return expected_eos, expected_pad

    def generation_processor(self, prompts, eos, pad, budget):
        if (eos, pad, budget) != (self.tokenizer.eos_token_id, self.tokenizer.pad_token_id, self.budget):
            raise ValueError(
                'SC2 action support EOS/PAD/budget differs between generation and PPO: '
                f'actual={(eos, pad, budget)!r}, '
                f'expected={(self.tokenizer.eos_token_id, self.tokenizer.pad_token_id, self.budget)!r}')
        return ActionLogitsProcessor([self.for_prompt(tuple(row)) for row in prompts.detach().cpu().tolist()],
                                     prompts.shape[1])

    def mask_teacher(self, logits, input_ids, responses):
        import torch
        length = responses.shape[1]
        if length != self.budget:
            raise ValueError('SC2 teacher response budget differs from action support')
        prompts = input_ids[:, :-length].detach().cpu().tolist()
        labels = responses.detach().cpu().tolist()
        # A separate sparse scatter avoids mutating model logits or losing gradients.
        masked = torch.full_like(logits, torch.finfo(logits.dtype).min)
        for row, (prompt, response) in enumerate(zip(prompts, labels)):
            state = self.for_prompt(tuple(prompt)).start()
            for col, token in enumerate(response):
                allowed = state.allowed()
                masked[row, col, list(allowed)] = logits[row, col, list(allowed)]
                state.advance(token)
            if not state.done:
                raise ValueError('SC2 teacher response did not finish a complete plan and EOS')
        return masked


class ActionLogitsProcessor:
    def __init__(self, supports, prompt_length):
        self.supports, self.prompt_length = supports, prompt_length

    def __call__(self, input_ids, scores):
        import torch
        if len(self.supports) != len(input_ids):
            raise ValueError('SC2 action support requires one generated sequence per prompt')
        masked = torch.full_like(scores, float('-inf'))
        for row, prefix in enumerate(input_ids[:, self.prompt_length:].detach().cpu().tolist()):
            allowed = self.supports[row].allowed(prefix)
            masked[row, list(allowed)] = scores[row, list(allowed)]
        return masked


@lru_cache(maxsize=2)
def load_support(path, budget):
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(path, local_files_only=True, trust_remote_code=False)
    backend = json.loads(tokenizer.backend_tokenizer.to_str())
    if type(tokenizer).__name__ != 'Qwen2TokenizerFast' or backend['decoder']['type'] != 'ByteLevel':
        raise ValueError('SC2 action support only accepts the verified Qwen2 ByteLevel tokenizer')
    proof = dict(mode=VERSION, budget=budget, canonical_tokenizations_only=True,
                 eos_token_id=tokenizer.eos_token_id, pad_token_id=tokenizer.pad_token_id,
                 tokenizer_sha256=hashlib.sha256(tokenizer.backend_tokenizer.to_str().encode()).hexdigest())
    print('SC2_ACTION_SUPPORT ' + json.dumps(proof, sort_keys=True), flush=True)
    return ActionSupport(tokenizer, budget)


def validate_config(config):
    section = config.actor_rollout_ref
    paths = [section.get(key, {}).get('sc2_action_tokenizer_path') for key in ('actor', 'ref', 'rollout')]
    if not any(paths):
        return
    if not all(paths) or len(set(paths)) != 1:
        raise ValueError('SC2 action support must match in actor, reference and rollout')
    budgets = [section[key].get('sc2_action_response_length') for key in ('actor', 'ref', 'rollout')]
    if len(set(budgets)) != 1 or budgets[0] != section.rollout.response_length:
        raise ValueError('SC2 action support requires the same explicit response budget everywhere')
    if (config.env.env_name != 'SC2' or section.rollout.name != 'hf'
            or section.rollout.n != 1 or section.rollout.multi_turn.enable):
        raise ValueError('SC2 action support requires plain SC2 HF generation')
    controls = config.get('ray_init', {}).get('runtime_env', {}).get('env_vars', {})
    for key, expected in [('SC2_PLANNER_PROTOCOL', 'legacy'), ('SC2_ORIGINAL_BO_SEGMENT', '1')]:
        if str(controls.get(key, '')).strip("'\"") != expected:
            raise ValueError('SC2 action support requires explicit legacy/original-count protocol')
    # Use an untruncated distribution for this NEW policy so sampled support and
    # teacher-forced probabilities match. Existing .9 experiments are untouched.
    if (section.rollout.top_p != 1.0 or section.rollout.top_k not in (0, -1)
            or section.rollout.val_kwargs.top_p != 1.0
            or section.rollout.val_kwargs.top_k not in (0, -1)):
        raise ValueError('SC2 action support requires top_p=1 and top_k=0 for train/eval')
