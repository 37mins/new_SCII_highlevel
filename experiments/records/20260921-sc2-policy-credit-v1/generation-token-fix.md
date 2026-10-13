# Generation EOS/PAD boundary repair — 2026-09-21

Authorization: user confirmed continued repair after the terminal failure
handoff. Scope is code repair and CPU regression; **no GPU restart, new queue,
deadline reset, Level7 rerun, Qwen launch or long-training promotion**.
Same experiment branch/record; old failed r2 and all frozen deployments remain
unchanged. This repairs transport of an existing grammar contract, not its
action space, seed grouping, no-thinking mask, reward or credit rule.

## Root cause, established from the actual failed deployment

Read-only197 metadata at22:30:22 Beijing:

| Source | generation_config EOS | generation_config PAD | Tokenizer EOS / PAD |
| --- | --- | --- | --- |
| Failed SpB r2 `runs/pre/model` | 151645 | absent / None | 151645 / 151643 |
| Registered Qwen Instruct-2507 snapshot | [151645,151643] | 151643 | 151645 / 151643 |

`ActorRolloutRefWorker.generate_sequences` replaces prompt metadata with the
model GenerationConfig fields. Previously HF filled missing PAD with EOS,
making SpB PAD151645 conflict with grammar/PPO PAD151643. Qwen's list EOS would
also conflict with the scalar grammar EOS. The earlier tiny HF tests supplied
already-matching EOS/PAD directly and missed this real worker boundary.

Only small model metadata/tokenizer files were inspected or copied; no model
weights or checkpoints were read for this diagnosis or CPU test.

## Minimal fix and retained checks

When action support is enabled, HFRollout resolves compatible model metadata
against ActionSupport's tokenizer before HF generation, padding and response
mask construction. Missing EOS/PAD uses the tokenizer value; `[EOS]` or
`[EOS,PAD]` resolves to canonical EOS. An explicit conflicting PAD, foreign EOS
or missing canonical EOS is rejected. The EOS environment override still passes
through the same check; budget mismatches remain rejected. Errors now include
actual/expected metadata. The support banner includes EOS/PAD IDs.

No config file, model object, response token or reward is rewritten. The grammar
still ends in its tokenizer EOS then PAD, and actor/old-actor/ref use that exact
support. Default-off code retains the old EOS-list and missing-PAD behavior.
The two changed registered source hashes are updated in system-v1.sha256.

## CPU evidence (passed; not GPU acceptance)

Unique staging `/var/jfsCache/sc2-generation-tokens-cpu-20260921.2O3Eqc`.
Pinned image `sha256:1a497d5721f89bb2e98c0273c4b1495f8fdc6921d589650d090871c11b8d1649`,
2CPU/6GiB, network none, CUDA hidden, no Docker GPU request; source and two small
metadata snapshots read-only. No real model weights or SC2 engine are mounted.

Red commit `7083ada55893c408930ede93adc003c40dc2e01b` ran
`python -B -m unittest test_sc2_generation_tokens -v`: five tests, five subcase
errors, exit1. Four errors reproduce the real worker→HF contract exception for
SpB missing PAD and Qwen EOS-list, in both train and validation modes. The fifth
is the intentionally absent new resolver method in the real-metadata test.
Historical default-off behavior and incompatible-override guards passed.
Container `sc2-generation-tokens-cpu-20260921-red` retained, GPU requests=null.
Red log SHA256 `d66e6fea4fd43c608c888080132c4ac40764aa00b617650fdb71ad8287b2b378`.

First full green run at fix commit `bed7a3e5a755f5b2ca0ad0977c54ca2cfa837594`
ran115 tests in8.617s, exit1: all EOS/PAD, legacy and existing110 regression
checks passed, but four subcases of the new probability comparison failed.
This failure is retained in `green.log`, SHA256
`e9d550bef90b4997d74eabda26bd9faa41e0d3c2e447b3c51cd9595ac1d4e2e2`.

A separate CPU position probe at22:41:48 Beijing established a fixture mismatch:
the new tiny GPT-2 integration fixture enters the historical explicit-position
branch and its decode positions remain `[122,10]` every step. Actual tiny Qwen3,
using the supported target's existing generation branch, advances to `[123,11]`,
`[124,12]`, etc., and passes all four unchanged probability comparisons.
Probe `position-probe.log` SHA256
`4980afcdf35466bfbd6747093290332dac267751feadb06f55c48a18f2532e69`;
container GPU requests=null, CUDA initialized=false. Its process exits0 after
reporting both outcomes; this is a diagnosis, not an all-tests-pass receipt.

The regression now uses real tiny Qwen3 and explicitly checks advancing decode
positions. No probability tolerance was widened (`atol=rtol=2e-5`), check removed,
or production position/cache behavior changed. GPT-2's legacy position branch
is not fixed or certified by this patch. SpB's real weights/custom kernels and
distributed precision remain outside CPU-only acceptance.

Final CPU run began22:43:44 Beijing with clean code
`933be4ca33e07e057298f1c92ed2630638455064`. All **115 tests passed, zero skips,
8.560s**, exit0. Container `sc2-generation-tokens-cpu-20260921-green2` is retained
with Docker GPU requests=null; CUDA initialization is explicitly asserted false
in the worker/metadata tests. All31 registered source hashes matched locally and
inside the remote source tree. `git diff --check` passed.

Command, inside the pinned CPU-only runtime:

```bash
python -B -m unittest test_sc2_generation_tokens test_sc2_action_support \
  test_sc2_policy_credit test_sc2_task_signal test_sc2_no_thinking_torch \
  test_thinking_action_boundary test_r6_format_reward test_original_bo_segment \
  test_original_game_seeds test_policy_credit_acceptance197 \
  test_qwen_seed_acceptance197 -v
```

These tests exercise the actual FSDP worker method with only GPU placement,
logging and distributed sharding replaced by CPU boundaries; real tiny Qwen3 HF
generation; variable-length live/terminal rows; EOS masks/padding; train/validation
settings; sampled-versus-teacher probabilities; actual registered SpB/Qwen
metadata; incompatible overrides; and prior action/credit/seed regressions.
Final `green2.log` SHA256
`e4df1f8a1a21648e0f482ca830af0745673178e50fa7b59f970e4b03660df057`.
Compact provenance is in [generation-token-cpu.json](generation-token-cpu.json).

This closes the observed metadata mismatch at CPU integration level only.
No GPU experiment, SC2 game, real-model load, PPO update, old-run mutation or
new monitor occurred in this repair. Distributed GPU acceptance, SpB custom
kernels, actual action consumption/execution and recovered win rate remain
unverified. A fresh bounded GPU acceptance requires new explicit authorization;
the failed r2 cannot be resumed and old budgets/deadlines are not silently reset.
