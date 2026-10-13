# Approved diagnostic: locate SpB-same degradation along training

September25 10:10:15Beijing. Status: **running / first CP2 batch, no completed batch yet**.
User explicitly answered: “批准这组128局退步定位评测”. Only the offered scope
below is authorized. No additional training, L8 promotion, retry, pruning or
resource extension is implied. Same original record/branch are retained.

Actual single queue submission10:07:21; dispatch10:07:22.437 and first container
10:07:22.851. Runtime `c9dfd9a4603c98e5e73c4e5874c8be9950aecdf1` was pushed and
independently matched via `git ls-remote` before prepare. Exact first container
`cc1b57af3067e4f0f6ca5a904299b7c5f6a610721a9955e37088468f572e6800`, name
`sc2-spb-early128-197-20260925-r1-b00-cp2`, owner=new output root below.
By10:10:15 actual retained CP2 load returned, global2/0updates/val_only; correct
eight declared seeds; SC2 in_game/planner boundary observed. Not a completed
batch or final RNG-pair acceptance yet. Expected12:07–13:07Beijing is uncertain;
absolute hard deadline **September25 16:07:22.437Beijing** never resets.

Actual Linux model/controller tests115 and host tests71 all passed with0skips,
no CUDA initialized. Sixteen real launcher+Hydra configs and34source hashes pass;
two exact CPU containers exited0 withDeviceRequestsnull. Local115 tests had four
Linux-only skips; those passed in Linux. Test/launch scope and bounded evidence
are in [launch receipt](spb-early128-launch-20260925.json) and
[local test receipt](spb-early128-local-tests-20260925.json). No old artifacts
deleted or rewritten, no duplicate queue/dispatch, no automatic training successor.

## Why this comes next

The completed common64 benchmark found released SpB35/64, sameCP9616/64,
randomCP9634/64. SameCP96 loses19net wins, with21regressed and2improved pairs;
the registered paired decrease survives Holm correction. All261consumed answers
in that arm are valid. The issue is measured task-performance regression, not
another legality-zero event. Qwen's49->53 gains are not confirmed by its exact
tests; the current results do not motivate claiming L7 is solved or that same
grouping universally improves learning.

Recommend evaluating the **existing SpB same CP2 and CP8**, each on the exact
64 scenario seeds already frozen in qwen_heldout_plan.py:128additional natural
games, zero updates. Reuse accepted original-SpB and sameCP96 outcomes unchanged.
This creates four observed points: released -> CP2 -> CP8 -> CP96, without
retraining or pretending unavailable CP16..88 can be evaluated.

The prior prune receipt says CP2/8/96 were preserved; CP8's saved retained
inventory has36files withpositive sizes. CP2 is outside the pruned long-run
intermediates and appears as the actual long-run parent in the completed SpB
snapshot. The September25 09:48:36Beijing read-only check now confirms each CP
has all26required nonempty files. CP2 sizes match its accepted train2 result;
CP8 sizes bind to retained prune inventory, not train96's finalCP96-only listing.
The controller repeats stat-only checks and binds small receipt hashes before
launch; no checkpoint contents are read in these checks. Exact paths:

- /var/jfsCache/sc2-l7-followup197-20260922-r4/spb-same/short/runs/train2/checkpoints/global_step_2
- /var/jfsCache/sc2-l7-followup197-20260922-r4/spb-same/long/runs/train96/checkpoints/global_step_8

## Approved scope and budget

- Node197 only,8GPUs;16serial stages of8natural games, fixed alternating CP2/CP8
  order across eight batches, paired seed/env_index and initial rankCPU/CUDA RNG.
- Unchanged L7/Flat128/VeryHard/TerranAir/canonicalBO, T.8/max192/top-p1/top-k0,
  no-thinking support, reward and Executor. SC2 reset concurrency1 until first
  observation;8games still parallel. Only checkpoint global2 versus8 changes.
- Zero PPO updates or checkpoint saves; actual returned checkpoint load and
  expected global2/8 must pass. Do not reinterpret historical native-resume
  limitations as bitwise training equivalence.
- Hard cap6wallh/48GPUh from first dispatch; new source+output32GiB, exact roots
  frozen below; at least128GiBfreeNVMe/600GiBavailableRAM/all8GPUsidle,
  no computePID, fsync/readback and exact owner/container guards at admission.
- Estimate2–3hours, uncertain: proportional scaling from the completed256-game
  matrix (4h59m11s) gives2h29m36s for128, but these arms are allSpB and game/load
  times vary. Preparation/resource waiting is not an asserted start time.
- Preserve all existing artifacts and frozen runtimes. No automatic retry,
  parameter change, extra games, learning-rate trial or continuation after this.
  Any failed gate blocks successors and requires handoff.

## Frozen launch contract and usage

- RUN_ID / prefix: `sc2-spb-early128-197-20260925-r1`.
- Whole output: `/var/jfsCache/sc2-spb-early128-197-20260925-r1`.
- Whole source parent: `/var/jfsCache/sc2-spb-early128-197-source-20260925-r1`,
  code at `code/`; both roots count against32GiB including bundle/preparation/CPU
  artifacts. No exclusions, retries or stale storage fallback; unknown is not0.
- Wrapper `spb_early128197.py`, plan `spb_early_plan.py`, hook `spb_early_hook.py`
  calling the existing `feedback_eval.install` observer with expected2/8.
- tmux socket `sc2_spb_early128_197_20260925_r1`, session `spb_early128_197_r1`.
- Stages `b00-cp2`,`b00-cp8`,`b01-cp8`,`b01-cp2`, etc through `b07-cp2`;
  sixteen independent containers with alternating first checkpoint by batch.
- First admission waits at most2h from prepare, not an ETA. Fixed6h from first
  dispatch includes loading/gaps/all16stages and45s cleanup reserve. No clock reset.

Use clean committed/pushed new source: `python -B spb_early128197.py prepare`
exactly once. `cpu-command` and `regressions-command` return actual no-GPU Docker
argv; execute those and actual-host `host-regressions`, then `queue` once under
the named tmux. Queue refuses an existing queue/dispatch and requires matching
zero-skip CPU/readiness/source proofs. These commands are not retry procedures.
Launch receipt will identify runtime SHA. Deployment copies the accepted SpBsame
parent's effective per-arm config with the new observer/output and explicit same
evaluation protocol. Existing34-file core hash manifest, SC2/map/model/tokenizer/
image/venv, generation/action/reward/Executor assets remain inherited and read-only.

The wrapper composes existing host guardian, admission, precision and natural
game acceptance; process-local bindings do not edit old runtimes. Backward-
compatible helper option `cpu_config_arm` selects SpB for CPU; old matrix default
remains `qwen-random`. Parent proof binds five old stage acceptance/result/.done/
guardian receipts and exact containers; matrix proof binds32accepted stages.
Old complete logs and large CP contents are not reread. Each new acceptance
requires actual load2/8 return, world8, binary64-v1,0updates,8natural nontruncated
games,100% consumed-answer legality, worker tokenizer/mask/local-command evidence,
exact seeds/env indices, and initial CPU/CUDA RNG matching both reused originalSpB
and sameCP96 plus the other new arm when present. Old CP2/native-resume limitations
remain historical; this evaluation does not claim bitwise training equivalence.

At09:48:36 eight A100s had0MiB/0% and no computePID; availableRAM796806200KiB,
NVMe1350780776448bytes; exact new roots absent. Four unrelated standing containers
remain untouched. Admission checks these time-sensitive resources again.

## What this can and cannot tell us

If CP2 is already materially below original, degradation is present by the
first two updates. If CP2/CP8 retain performance but CP96 is lower, the evidence
points to a later interval, not an exact change point or proof of overfitting.
Mixed or uncertain results stay uncertain. CP16..88 were pruned, so the interval
between8and96 cannot be filled from nonexistent weights.

Report all128outcomes, paired differences, discordant counts and intervals,
including null or adverse outcomes. CP2-vs-original and CP8-vs-original can use
exact paired tests with Holm across the two new contrasts; CP2/8/96 adjacent
contrasts are exploratory. This proposal was selected after the CP96 result:
the64seeds are now a **development/diagnostic benchmark**, not an untouched
confirmatory holdout. No best-checkpoint or stopping selection based on interim
wins; complete the fixed scope unless technical/safety gates fail. Later repaired
training requires separate authorization and untouched-seed confirmation.

In parallel with an approved run, use bounded existing metrics/audits to inspect
the relevant training interval: task-advantage variability, clipping/KL/entropy,
return/decision-count relations and consumed-action evidence. Correlation cannot
assign the unique cause to learning rate, seed grouping, reward or Executor.
Changing to multi-seed groups or a lower learning rate is a later controlled
training proposal, not automatically approved by this evaluation.

General methodological support, not evidence for our particular mechanism:
[Henderson et al., Deep Reinforcement Learning That Matters](https://arxiv.org/abs/1709.06560)
documents sensitivity to seeds, hyperparameters and implementation, motivating
controlled comparisons and cautious interpretation of individual curves.

Sources: [six-arm results](l7-common64-results-20260925.md),
[compact completion](l7-matrix256-complete-20260925.json),
[prune scope/receipt](plotted-checkpoint-prune-20260924.md),
[SpB parent snapshot](spb-l7same-complete-20260923-data.json),
[seed/credit mechanism analysis](yuque-validity-seed-analysis-20260924.md).
See [small parent/resource proof](spb-early128-parents-20260925.json). The earlier
09:43proposal used only local evidence. Approved execution adds read-only parent
checks and new launch code. Actual tests and dispatch are recorded separately;
synthetic tests and CPU activity never substitute for GPU/game evidence.
