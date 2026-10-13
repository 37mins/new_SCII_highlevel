# L7 common 64-seed checkpoint comparison: completed

Read-only verification: September 25, 2026, 09:29–09:32 Beijing. The four-arm
matrix finished at **04:56:53.642**, after 4h59m11s from its single first dispatch
at September 24 23:57:42.505. This is before the unchanged 07:57:42.505 hard
cutoff. All 32 new stages and 256 new natural games completed; zero updates.
The earlier original-Qwen/fresh-Qwen-same 128 games are reused, not rerun.
Together the six arms cover 384 games on the identical 64 frozen scenario seeds.

## Results

Every entry is wins / 64 natural games; no draws or truncation.

| Model | Released instruct weights | Same-seed training CP96 | Random-seed training CP96 |
| --- | ---: | ---: | ---: |
| Qwen | 49/64 (76.5625%) | 53/64 (82.8125%) | 53/64 (82.8125%) |
| SpB | 35/64 (54.6875%) | 16/64 (25.0000%) | 34/64 (53.1250%) |

Within a training step, `same` means eight games share one sampled scenario seed;
`random` means eight independent draws. The evaluation here uses the same 64
new scenario seeds across all six arms, not training-batch wins or the old eight
reused test seeds. CP96 is a frozen checkpoint: no PPO happened in this evaluation.

## Registered paired inference

Differences are trained checkpoint minus its own released original. Improved
means original non-win -> trained win on the same seed; regressed is the reverse.

| Comparison | Improved / regressed | Win difference (percentage points) | Paired bootstrap 95% interval (pp) | Exact two-sided p | Holm-adjusted p |
| --- | ---: | ---: | --- | ---: | ---: |
| Qwen same - original | 4 / 0 | +6.2500 | [+1.5625, +12.5000] | 0.125 | Separate original registration |
| Qwen random - original | 4 / 0 | +6.2500 | [+1.5625, +12.5000] | 0.125 | 0.25 |
| SpB same - original | 2 / 21 | -29.6875 | [-42.1875, -17.1875] | 0.0000660419 | 0.000198126 |
| SpB random - original | 8 / 9 | -1.5625 | [-14.0625, +10.9375] | 1.0 | 1.0 |

Holm correction covers the three added primary comparisons only, as registered;
the original Qwen-same hypothesis retains its separate prior registration.
Exact paired McNemar/binomial inference supplies the rejection decision, not
the percentile-bootstrap interval. With only four discordant pairs all in one
direction, the Qwen percentile bootstrap cannot resample an unobserved opposite
discordance: its positive interval is not an exact-test inversion and must NOT
be used to override p=0.125 or claim confirmed improvement.

Exploratory same-versus-random: Qwen has identical per-seed win/non-win outcomes
across all 64 pairs, not merely equal totals (0 discordances, p=1). This does not
prove policy equivalence: sampled actions and returns need not be identical,
and a zero-width empirical bootstrap interval does not establish population
equivalence. SpB same minus random has 7 improved / 25 regressed pairs,
-28.125pp, bootstrap [-43.75, -12.5]pp, unadjusted exact p=0.00210240. This is
secondary exploratory evidence, not a causal seed-grouping experiment.

## Interpretation

- **Qwen:** both trained checkpoints have a favorable +4-win point estimate,
  but the registered exact tests do not confirm a learning improvement at .05.
  Same and random training curves can look different while these fixed-test win
  outcomes are identical. Neither a training-curve rise nor an old 8/8 proves
  generalization.
- **SpB same:** this checkpoint performs substantially worse than its original
  on the registered benchmark; the paired decrease survives the three-test
  correction. This is a negative learning outcome despite technical acceptance.
- **SpB random:** no demonstrated increase or decrease against original; the
  point estimate is near unchanged, and uncertainty remains meaningful.
- **Not another validity-zero failure:** all consumed answers pass structural
  and semantic acceptance (new four arms 1018/1018; all six 1679/1679).
  SpB same has 261/261 valid consumed answers. The mechanism of its strategic
  degradation has not been diagnosed; legality is not strategic quality.

These are results for one training run per condition and frozen system. They do
not establish a general effect across training random seeds, a unique cause of
degradation, or architectural causation. Model sizes/FLOPs, shared Executor,
historical startup/native-restoration differences and Qwen random lineage limits
remain. Old Qwen same strict-failed precision evidence and failed r4 are not
rewritten. If these 64 seeds guide model selection or repairs, they become a
development benchmark; later confirmation needs untouched seeds.

## Technical completion and provenance

Read small records only: all 48 exact owned stage containers exited0, all guardians
completed under their original deadlines, and queue/state/host terminals agree.
All stage result=.done=acceptance.result; clean frozen source/world8/binary64,
finite metrics, zero updates, eight natural untruncated outcomes per stage,
actual global0 for originals / returned ownCP96 load for trained arms checked.
All six arms use the declared64 seeds; within-model initial rank0..7 CPU/CUDA RNG
receipts match on each batch. Cross-architecture RNG consumption is not claimed
bitwise paired. Frozen controller acceptance includes worker canonical/no-thinking
and model-plan -> queue -> local Depot/Marine checks; this check did not reread
full logs or re-run historical verifiers.

New matrix runtime: `72068c693266dcf74ed8d0d2eb984f834ca8a030`.
Reused Qwen128 runtime: `b19b3a2c2d767f20ea71bd16225eee0183cb2fb7`.
Final matrix storage: 1,809,930,246 bytes / 32GiB, strict two roots, return0,
empty stderr. No failure file. No new experiment, server mutation, checkpoint
read/deletion, restart, retry, or follow-on dispatch was performed this turn.
No periodic notifier was created by the queue; completion above was verified
in this user-requested check, not an earlier claimed notification.

- [Compact outcomes, terminal checks and receipt hashes](l7-matrix256-complete-20260925.json)
- [Matrix preregistration](l7-matrix256-197-20260924.md)
- [Original Qwen128 preregistration](qwen-heldout128-197-20260924.md)
- [Reproducible analysis](analyze-l7-common64.py)

Validation: run bundled Python 3 with `-B analyze-l7-common64.py`; NumPy2.3.5,
10,000 paired bootstrap resamples, default_rng PCG64 seed20260924, linear
percentile quantiles. All receipt assertions and exact-p boundary self-checks
passed. Exact p-values/discordances independently cross-checked in JavaScript
from the same compact outcomes. An optional SciPy cross-check could not run
because SciPy is absent; no dependency was installed. Replaced it with 1088
independent exact rational-PMF cross-checks using the standard library Fraction
recurrence, all passed; primary discordances/p-values, Holm adjustment and
384-game/1679-answer totals also passed explicit assertions.
No model tests were rerun for this read-only
status/analysis task. `git diff --check` is required before commit.
