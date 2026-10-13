# Canonical action support candidate v1 — 2026-09-21

Status: prior CPU candidate failed the real GPU precheck on September21 before
first generation/PPO; token-metadata integration fix passed115 CPU regressions
at22:43 Beijing. A separately approved fresh r3 reached GPU/SC2 startup but the
host storage-budget measurement failed and stopped it at23:14. No recorded response, stage
or PPO update accepted; exact measurement failure cause remains unknown.
Default off; not a GPU or learning acceptance. See the
[token-boundary repair record](../../experiments/records/20260921-sc2-policy-credit-v1/generation-token-fix.md).
This extends the separate policy-credit repair branch,
not any historical deployment or the active original/D96/C96 panel.

## Observed problem and bounded change

The real original-model `b00-original` panel answers, inspected at16:18 Beijing,
include empty text, translated action names, missing bullet prefixes, and repeated
lists beyond the candidate quotas. This is therefore not only a collapsed RL
checkpoint problem. The old no-thinking mask excludes thinking tags, not invalid
action syntax. Prompt clarification was already enabled and is not a new fix.

The candidate restricts generation to `<answer>` containing at least one complete
canonical action line, then `</answer>` and EOS. Choices come only from the current
remaining BO section, not the global name table or example. The model still chooses
action identity, ordering, count and when to finish. Repeated lines and `x N` are
allowed within cumulative quotas. No new strategic rule, best-action lookup,
resampling, response rewriting, reward change or parser leniency is introduced.
No maximum of15 expanded actions is added. The token budget must always leave room
for a complete line, closing tag and EOS; it is not increased.

This is explicitly a **restricted policy / new protocol**. It uses canonical
tokenizations rather than every token spelling of equivalent text. Near the token
limit, only complete continuations fit. Structural validity achieved this way is
mechanical, not evidence that RL learned legality or better strategy. Wins can
still reflect executor rules. Historical curves must not be relabeled as this
candidate's results.

## Interface and fail-closed boundaries

Entry: `verl/utils/sc2_action_support.py`; wired into HF rollout and the common
actor / old-actor / reference forward path. The collector verifies configuration
agreement before use. Old defaults are untouched.

Explicit overrides (in addition to the existing no-thinking and policy-credit
repair settings, with identical fresh model / executor / reward / difficulty):

```text
+actor_rollout_ref.actor.sc2_action_tokenizer_path=/assets/spb
+actor_rollout_ref.ref.sc2_action_tokenizer_path=/assets/spb
+actor_rollout_ref.rollout.sc2_action_tokenizer_path=/assets/spb
+actor_rollout_ref.actor.sc2_action_response_length=192
+actor_rollout_ref.ref.sc2_action_response_length=192
+actor_rollout_ref.rollout.sc2_action_response_length=192
actor_rollout_ref.rollout.top_p=1.0
actor_rollout_ref.rollout.top_k=0
actor_rollout_ref.rollout.val_kwargs.top_p=1.0
actor_rollout_ref.rollout.val_kwargs.top_k=0
++ray_init.runtime_env.env_vars.SC2_PLANNER_PROTOCOL='legacy'
++ray_init.runtime_env.env_vars.SC2_ORIGINAL_BO_SEGMENT='1'
```

For this **new** policy, top-p becomes1 rather than historical0.9, so no nucleus
truncation creates a sampling/teacher-forcing distribution mismatch. Temperature
remains0.8 in both paths. This does not retroactively fix historical top-p behavior,
nor prove every other probability/cache issue absent. Matching teacher masks and
same-weight probabilities require actual verification.

Only offline Qwen2 ByteLevel tokenizers, HF one-sequence generation, and padded,
unfused, non-sequence-parallel actor/reference are accepted. EOS/PAD/token-budget
overrides must match. In this opt-in mode only, absent model-generation EOS/PAD
fields resolve to the grammar tokenizer IDs. A model EOS list containing the
tokenizer EOS and optionally its PAD resolves to the grammar's single EOS:
the existing grammar never emits PAD as a live action/stop choice. This covers
SpB's absent PAD and Qwen's `[EOS,PAD]` metadata without changing teacher support.
Any explicit conflicting PAD, foreign EOS or EOS list missing the canonical EOS
still fails before generation. HF stopping, output padding and response masks
use the same resolved IDs; model metadata and historical default-off behavior
are not mutated. Workers report canonical EOS/PAD in `SC2_ACTION_SUPPORT`.
Malformed/ambiguous candidate sections, more than64 names,
counts above512, insufficient complete-plan budget and off-support training tokens
raise errors rather than silently clipping or salvaging text. The existing
no-thinking prefix/mask can coexist; generated tokens stay intact in audit/PPO.

Missing/empty candidate sections emit EOS only, not synthetic actions. This exists
for terminal vector slots; it is **not** a legal plan for a live empty-candidate
state. Existing consumption evidence and the pre-PPO validity gate must reject
any attempted training on such invalid live output. No terminal result is changed.

Workers emit `SC2_ACTION_SUPPORT` with mode, token budget and tokenizer SHA256.
The run must also preserve source SHA, effective config, raw prompt/response,
consumption / semantic validity, executor and actual game outcomes.

## Verification plan and release boundary

Tests cover actual strict validator and Planner/Commander queue; cumulative
quotas; observed malformed outputs; completed EOS under192tokens; empty terminal
slots; real tokenizer round trips; no-thinking compatibility; real tiny CPU HF
rollout; per-position generation/teacher distributions; actor/reference equal
log-probs; finite entropy/gradients; and default-off legacy regressions.

GPU release requires a separately authorized bounded fresh-model acceptance,
actual legal consumed actions and execution, then a short same-seed PPO check.
Do not resume collapsed weights, insert this into the active panel, or promote
CPU success into a96-step run. Even passing the short gate would not establish
generalization or a statistically reliable win-rate improvement.

## Evidence log

- Local AST parsing and400 pure-Python grammar paths completed within their
  budgets. These do not load Torch, tokenizer, real model or SC2.
- First isolated CPU container exited126 before Python: image entrypoint treated
  the Python executable as a shell script. No tests ran. Container and staging
  are retained; this is test-harness failure, not GPU/SC2 or model failure.
- CPU staging: `/var/jfsCache/sc2-action-support-cpu-20260921.W0hNLj`.
- Second CPU container ran86 tests: the10 new cases passed, but a historical
  baseline comparison had5 subcase errors because its alternate Git objects
  were not mounted. This failed suite is retained. With the existing baseline
  objects mounted read-only, container r3 returned0 with86 tests, zero skips.
- Final r4 adds a distinct real autoregressive-HF-versus-teacher-forcing
  probability comparison, not merely actor-versus-identical-reference. All
  **87 tests passed, zero skips, 19.301s**, exit0; GPU device requests are null,
  CUDA is explicitly hidden and the relevant tests assert no CUDA initialization.
  The five actual tested source/test file hashes match the local files exactly.
  Optional missing alternate-object warnings remain; all required historical
  `git show` baseline comparisons resolved and passed in r3/r4.
- Full command, image and file/log hashes are in
  [the CPU evidence record](../../experiments/records/20260921-sc2-policy-credit-v1/action-support-cpu.json).
  These tests use small random CPU models and the real tokenizer, **not SpB
  weights, distributed GPU execution or SC2 game success**.
