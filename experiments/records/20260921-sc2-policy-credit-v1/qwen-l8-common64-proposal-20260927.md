# Proposed L8 Qwen original / CP96 / CP192 common64 evaluation

September27, after the completed CP96→192 continuation. Status: **running,
single dispatch09:46:29 Beijing; at09:56original batch0 accepted,CP96batch0 active**. User explicitly replied
“批准” to this budget. Earlier recommendation-only wording is superseded.
Same experiment record/branch, no method change or new training authorization.

## Why this is the next proposed experiment

The completed continuation has96new returned PPO updates, but its reused eight
evaluation seeds give5/8→5/8, one gain/one loss. Training wins494/768 versus
441/768in the prior block are on different seed schedules, not paired evidence
of improvement. Execution is validated; additional useful learning is unresolved.
The older L8 pilot compared original and L7-trained policies on32other seeds,
retained only32accepted games and never completed its three-arm comparison;
it is not a completed common64control for these L8-trained checkpoints.

Propose three frozen arms: released original Qwen3-4B-Instruct-2507; the accepted
L8sameCP96; and its accepted native continuation L8sameCP192. Each sees the same
64new scenario seeds: **192new natural games,0optimizer updates**. Original
measures the full L8 training effect; CP192-minus-CP96 measures the marginal
effect of the added96updates. These are not SpB architecture comparisons.

## Evaluation protocol to freeze before launch

- L8CheatVision/Flat128/Base75689/TerranAir, current canonicalBO, observation/
  action support, no-thinking, Executor, reward and generation settings unchanged.
- Freeze64distinct seeds from an outcome-independent generator before any result;
  exclude training0..100, the original8evaluation seeds, historical L7common64
  and L8pilot32. They are held out from these project runs, not a claim about
  model pretraining. Publish the seed list and hash before GPU dispatch.
- Eight batches of8distinct seeds, each evaluated by all3arms;24serial stages.
  Rotate arm order across batches. The three arms share each rank's initial
  CPU/CUDA sampling RNG and the same per-rank scenario seed. No best-seed selection.
  Training's same-within-step grouping is NOT reused as64copies of one eval seed.
- All arms use a common frozen evaluation implementation and actual assets/load
  evidence. No weights update or new checkpoint writes. Each stage requires
  natural terminal8games,0updates,100%consumed structural/semantic validity,
  actual original/CP96/CP192load, correct difficulty/replays and exact container,
  guardian, result/.done/acceptance exit0. Any failed arm blocks all successors.
- Primary preregistered contrast: CP192-minus-CP96 paired win-rate difference,
  report discordant gains/losses, paired95%interval and exact two-sided McNemar
  test. Original contrasts are secondary/exploratory, not additional unadjusted
  confirmatory claims. Draws count as non-wins and are separately reported.
  The [official statistical reference](https://www.statsmodels.org/v0.14.0/generated/statsmodels.stats.contingency_tables.mcnemar.html)
  documents the exact binomial form. No new library installation is proposed.
- Fixed sample size, no outcome-driven early stop or automatic sample expansion.
 64pairs improve coverage over8but do not guarantee power to detect a small gain;
  a nonsignificant result does not prove equivalence. Report effect uncertainty.

## Approved budget

Only197, eight GPUs in one serial queue. Expected approximately**2–3hours**
after dispatch, extrapolating24stages from the latest actual5.5–6.1minutes per
eight-game evaluation plus inter-stage overhead; longer L8 scenarios or waits
can change this estimate. Proposed hard**6wall hours /48GPUhours /32GiB**new
source+output, including zero-game preflight, loads, gaps and all stages.
First GPU dispatch fixes one deadline shared by all stages,45s cleanup reserve.
No automatic retry, deletion, CP288, L9, SpB training, dataset replacement or
other successor. Eight idle GPUs/no computePID,600GiBavailableRAM,128GiBfree
NVMe and fsync/readback must be rechecked before each stage. Historical training
roots remain read-only and their budgets/gates are not modified.

09:33Beijing read-only snapshot: all8GPUs0MiB/0%,no computePID;
851061149696bytes free NVMe,796788624KiB availableRAM. Recheck every stage.
No claim that approval or a plan means dispatched; launch receipt will record actual start.

## Frozen one-shot implementation

Same record/branch. RUN_ID=`sc2-qwen-l8-common192-197-20260927-r1`.
Output `/var/jfsCache/sc2-qwen-l8-common192-197-20260927-r1`;
source-parent `/var/jfsCache/sc2-qwen-l8-common192-197-source-20260927-r1`,
code under `code`. Only these two new roots count toward32GiB, including source,
bundle, runtime, CPU/preflight remnants and all output; no exclusions/du retry.
Read-only ancestors do not gain any new training budget.
Wrapper [qwen_l8_common64_197.py](qwen_l8_common64_197.py),
worker [qwen_l8_common64_hook.py](qwen_l8_common64_hook.py),
full seed list/rotated24-stage order [qwen_l8_common64_plan.py](qwen_l8_common64_plan.py).
Seed generator `random.Random(20260927).sample(range(65536,2**32-1),64)`;
compact JSON seed-list SHA256 `ac8647f0b3f4e14d25f88a1508d55cd94c6ce6cf82ac8e73a2c386ca2b6e011b`.
Primary paired95%interval will use100000 paired bootstrap resamples, fixed analysis
RNG20260927, alongside exact two-sided McNemar and gains/losses. Secondary
original contrasts explicitly exploratory. No post-result choice of seed/analysis.

No shared core change. Original released Qwen revision
`cdbee75f17c01a7cc42f958dc650907174af0554`; own L8 CP96 and192 paths in the
frozen plan, not the older L7-trained pilot checkpoints. Accepted parent
`f0e1059` small receipt hashes/terminal/container and26-file inventories are
rechecked; CP96 ancestor contract remains bound to its accepted provenance.
No full historical logs or large checkpoint contents reread for this check.
Original assets/container/dependencies/SC2/map/BO identities inherited from the
accepted L8 deployment; actual frozen source SHA, full effective config and
manifest are saved by new runtime. All parent CP/assets/dependencies/rootfs are
read-only; writes only in this run and its counted tmp.

Preflight: local scope tests; actual Linux model and host regressions, zero
skips;24actual launchers/Hydra configs/source manifest;3no-GPU Ray worker hook
imports (one per model arm, all stage config environments validated); then a
single eight-distinct-UUID/NCCL GPU probe without model/games/updates. Probe
shares the first-dispatch six-hour cutoff with24evaluations. CPU is not PPO.
Modes `prepare`, `regressions-command`, `host-regressions`, `cpu-command`,
`cpu-hook-command <b00-original|b00-cp96|b00-cp192>`, `queue`; queue one-shot
locks and refuses a prior dispatch. Any failed gate stops, never auto-retries.
Four-hour bounded first-admission wait starts at preparation; six-hour GPU/wall
budget starts only at first dispatch. No automatic successor or L8 RL.

Local validation before freezing: `PYTHONPATH=/private/tmp/sc2-qwen-native-testdeps-20260924:.:tests`
bundledPython `-B -m unittest test_qwen_l8_common64_197 test_qwen_l8_cp192_197
test_qwen_l8_pilot197 test_qwen_l8_probe_env test_feedback_eval -v`;
51tests,50passed/1explicit pinned-CPU-Torch-only skip on macOS. All15new scope
tests passed. This is NOT the zero-skip Linux gate; that must run in the real
no-GPU pinned environment before dispatch. `shasum -a256 -c configs/system-v1.sha256`
34/34unchanged core hashes and `git diff --check` passed.

## Decision after results (not automatic authorization)

If CP192 clearly improves overCP96, consider further bounded training with a
fresh confirmatory set. If both trained models improve overoriginal but CP192
does not outperformCP96, investigate diminishing returns rather than assume
more steps will help. If neither establishes improvement, inspect task signal,
update magnitude and protocol/data limitations before changing one factor.
L8random or a comparable SpB training run may then be designed with matched
budgets; do not automatically proceed to L9 or claim architecture superiority.

## Actual launch September27

Frozen source/controller `e01594ecd3ea7b43d2296b371fd340f9d575ab3a` pushed to
the existing branch and independently matched by `git ls-remote` before deploy.
Runtime clone uses `--no-local` (no alternating-object dependency). No old
source/deployment/run modified. Single queue after124actual model/controller
tests plus71actual host tests, zero skips/noCUDA;24actual dry launchers/Hydra
configs/34core source hashes;3real no-GPU Ray setup hooks, each passed with
feedback_eval loaded, zero CUDA devices/initialization and zero model/game/update.
All5CPU containers exited0 with DeviceRequests=null. Local macOS skip does
not apply to this Linux gate.

`dispatch.start=1790473589.9456112`; one fixed
`deadline=1790495189.9456112` = September27 **15:46:29.945611 Beijing**.
Eight-GPU preflight passed with8distinct UUIDs and all8NCCL sums28.0, exited0;
no model/game/update in the probe. First original stage container
`9f438f2d0ebdc8459fda03d3bf60a0fd4df28ac16688d958085da6ec16d52c75`,
exact owner newROOT, started09:47:01.740509, GPUall, running at09:48:27.
Its manifest is clean e01594e/world8/binary64; correct tokenizer/mask banners
and first8distinct declared scenario seeds are present. At this snapshot the
model-eval/load-return proof and result were not yet present; do not call it a
completed batch or a successful CP96/192 load. Queue remains running-unverified.
Two-root strict storage51796736bytes/32GiB,return0/empty stderr, no failure.

Estimated finish today **11:45–12:45 Beijing** based on prior evaluations,
subject to actual game durations/admission. Hard cutoff is not the ETA.
Existing host stage sampler+guardian enforce limits/fail-stop, not a claim
that learning succeeded. No extra recurring automation or later experiment
created. Exact socket/session, config hashes and small receipts:
[qwen-l8-common64-launch-20260927.json](qwen-l8-common64-launch-20260927.json).

09:50:16follow-up: first original `checkpoint_evaluation.json` now confirms
global0/checkpoint=null/val_only/0optimizer updates/T0.8/feedback0 and exact
first8new seeds. Bounded32KiB response-tail sample contains6consumed answers,
all6structurally/semantically valid; this is a partial sample, not whole-run
acceptance. Eight GPUs2332–2476MiB allocated (instantaneous utilization0%
while environment work continues, not evidence of a stopped model). No stage
result/failure yet. No CP96/192actual load or learning conclusion claimed.

## Interim interpretation September27 09:56 Beijing

The technical conclusion is192real accepted Qwen L8same PPO updates, not merely
CPU audits or evaluation. First96training steps won441/768(57.42%); next96
won494/768(64.32%), with5938/5938 and5900/5900consumed answers valid.
These are different training seed schedules with correlated same-step games:
the6.90percentage-point training-block difference is not a paired improvement.

Original8reused diagnostic scenarios: original6/8, CP96 5/8, CP192 5/8;
continuation CP192-vs-CP96 has1gain/1loss. No net learning benefit established;
this does not establish equivalence or reliable degradation from so few games.
No completed L8random/SpB matched architecture comparison is available here.

The newcommon64test has onlyone accepted stage: original batch0,8natural games,
6wins2defeats,54/54valid consumed answers,0updates,result=.done=acceptance;
exact guardian and container exited0. CP96batch0 model load returned atglobal96,
declared first8new seeds and0updates, but its batch is still running. Thus8/192
new games accepted, no complete64pair/arm result. Do not extrapolate the6/8
partial original score or compare it with old-seed checkpoint scores.
The fixed cutoff15:46:29 is unchanged; no failures or server writes this turn.
[Small evidence and result hashes](qwen-l8-conclusions-status-20260927-0957.json).
