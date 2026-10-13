# Node197 bounded repair acceptance — planned, 2026-09-21

User explicitly approved the proposed sequence: after the active original/D96/C96
panel finishes and all eight GPUs are free, 8 zero-update games, then only if the
gate passes 2 PPO steps / 16 games, then 8 paired zero-update games. At most
2 wall-hours / 16 GPU-hours including model loading, checkpoints and stage gaps.
No retry, no 96-step continuation, no old L7/C/D checkpoint training. Existing
panel runtime and data remain unchanged. This supersedes the earlier statement
that no short GPU run is authorized; it does not claim a run has started.

## Frozen protocol

- Experiment: `20260921-sc2-policy-credit-v1`, existing repair branch.
- Runtime: `0172fb9b334cea91f1e92c0c545f721afe281671`, privately backed up.
- Controller: `acceptance197.py` in the same record; its actual clean SHA is saved
  in deployment/readiness/launch files before dispatch.
- Reused orchestration: `run_seed_group_arm.sh` at private SHA
  `9a7b0faca5b145a891ad211f189121e4949f0eab`, the verified native-eight-rank path.
- New unique root: `/var/jfsCache/sc2-policy-credit197-20260921-r1`;
  runs `policy-credit197-r1-pre`, `policy-credit197-r1-train2`, `policy-credit197-r1-post`.
- Level6 Harder, Flat128, Terran Air, original SpB snapshot, canonical BO,
  T0.8 / 192 tokens / gamma1 / combat0.001, LR1e-6, existing executor unchanged.
  Level6 is chosen as the smaller, already exercised acceptance environment;
  this is not a claim to have fixed Level7 learning.
- New restricted-action policy + no-thinking in generation/actor/oldactor/ref;
  **top-p1** in all stages, same-seed UID training, post-centering invalid credit
  `min(A,0)-0.1`; existing pre-PPO validity floor0.5. These are explicit protocol/
  objective differences from the historical .9 curves, not a single-factor ablation.
- Pre/post 8 seeds: first32bits SHA256 of
  `sc2-policy-credit-acceptance-20260921-v1:0` through `:7`; deterministic list saved
  in deployment before any outcomes. Same rank0–7 sampling reset once per pre/post
  batch; not per-call common randomness after trajectories diverge.
- Train's native RandomState(0) dispatch is `[2732]*8`, then `[43567]*8`.
  Runtime checks the actual dispatched seed equality per UID before generation.
- Train starts fresh with resume disabled; only the post evaluation may load its
  own complete native world-size8 step2 model/optimizer/data checkpoint.
- Reuse the read-only game-boundary observer and opt-in command provenance logger;
  no replayed answers, rewriting, new strategy, reward shaping or extra sampling.
  Depot/Marine local commands are distinguished from engine ACK/production and
  from rule-selected commands. A passed gate does not prove causal victory benefit.

## Preregistered gates, not win-rate selection

1. The predecessor must have accepted all 24 panel batches / 192 games with matching
   result/.done/acceptance files and zero updates. A failed predecessor blocks this
   queue; it is not retried or ignored.
2. Each stage: exit0, matching result/.done, finite metrics, clean runtime SHA,
   world-size8, exactly 8/16/8 naturally finished games, no truncation.
3. At least one real consumed answer and **all consumed answers structurally and
   semantically valid**; actual no-thinking and action-support worker banners with
   registered tokenizer/mask hashes. No generated thinking tags.
4. Command traces must show validated parsed plans, validated queue entries and
   at least one locally queued model-attributed Depot/Marine command; any observed
   postprocess/salvage origin in a parsed plan fails the gate. Existing Commander
   rule entries remain separately identified, not credited to the model.
5. Train: exactly 2 updates, both pre-PPO gate audits, exact two same-seed batches,
   finite nonzero reported gradients, no positive invalid advantage and complete
   step2 checkpoint. Post: actual step2 load returned, original paired seeds/RNG,
   zero updates. Evaluation-only checkpoint restoration may load optimizer state
   via the existing loader but never steps it.
6. Wins are descriptive secondary outcomes only. No minimum wins for promotion.
   Mechanical validity and two optimizer steps do not establish learning recovery,
   historical top-p equivalence, or generalization.

## Resource / failure boundaries

Single-dispatch tmux socket `sc2_policy_credit197_20260921_r1`, session
`policy_credit197_r1`; container `sc2-policy-credit197-20260921-r1` with exact owned
root label. Queue waits without GPU allocation, then rechecks eight zero-memory /
zero-utilization GPUs, no compute PIDs, >=600GiB available RAM, >=140GiB local NVMe
free and fsync/readback. It never stops other jobs and is not a cluster reservation.

Queue expires at 2026-09-22 03:15:40 Beijing (existing panel effective deadline
plus one hour); this does not extend the panel. The acceptance's one two-hour
clock starts at first GPU dispatch and cannot reset. Host watchdog checks both
time and combined new output/source size; 128GiB ceiling. Measurement failure
is a failure, not zero usage. Timeout stops only the exact new owned container;
all failed logs/checkpoints/container evidence remain. No automatic retry or
successor experiment. A failed/expired queue needs user direction.

Outputs are local NVMe; model/venv/SC2 and old orchestration/dependencies mounted
read-only. Same verified image/asset manifests as the panel are saved in deployment
and native run manifests/preflight. This does not fix the storage backend.

## Verification and status

Before enqueue: run the pure-CPU controller tests, then all three real launchers in
DRY_RUN mode inside the pinned CPU-only image; compose their Hydra configurations,
validate action/credit contracts and Ray socket paths; assert CUDA uninitialized.
These are preparation tests, not GPU acceptance. GPU/SC2 results remain pending.

Entry: `python acceptance197.py prepare`, CPU command from `cpu-command`, then
`python acceptance197.py queue` in the declared tmux session, each at most once.

### Actual preparation / queue evidence

- Local `python3 -B -m unittest discover -s tests -p test_policy_credit_acceptance197.py -v`:
  **9 tests passed**, 0.003s, exit0. `git diff --check` passed.
- Controller frozen and privately pushed as
  `b2a011afc5eac0ddada0e9150bfffd563109f42f`; runtime remains0172fb9.
  Incremental 39KiB Git bundle staged at
  `/var/jfsCache/sc2-policy-credit197-staging-20260921-r1/source.bundle`;
  clean controller at `/var/jfsCache/sc2-policy-credit197-source-20260921-r1/code`.
  No active panel/deployment was modified.
- At16:48:36 Beijing, actual `cpu` invocation completed all three DRY_RUN entries,
  Hydra composition, action/credit config checks and Ray socket validation.
  `readiness.json`: passed=true, cuda_initialized=false, matching runtime and
  controller SHAs. Container `sc2-policy-credit197-20260921-r1-cpu` is retained:
  state=exited, exit0, GPU DeviceRequests=null. `cpu/<stage>/resolved_config.json`
  and exact `effective_config.json` preserve all merged settings.
- At**16:49:42 Beijing**, the declared tmux queue was started once. At16:50:11,
  `queue-state.json` was `waiting-predecessor`, tmux pane alive, `dispatch.json`
  absent, no new GPU container running. **Queued is not GPU accepted.**
- Predecessor snapshot16:49:10:72/192 games accepted, original model batch3
  (fourth batch) active, zero PPO updates. This is a timestamped snapshot only.
- Follow-up heartbeat `197` / “197 修复短验收” attached to this task, every15minutes:
  quiet during healthy waiting/progress; records and reports actual GPU/PPO,
  stage completion, failure or user decision; deletes itself after terminal
  acceptance/handoff. Old L7 heartbeat remains deleted and IDSC remains paused.

### Authorized unstarted-r1 replacement — September21

While preparing the separately approved Qwen matrix, a read-only audit at17:39
Beijing found five stale entries in runtime0172fb9's `configs/system-v1.sha256`:
envSC2, rollout_loop, ray_trainer, dp_actor and hf_rollout. The actual files match
the frozen Git commit; this is a stale manifest, not an untracked source edit.
Original CPU DRY_RUN skipped asset verification, so its pass did not cover this
production preflight. The native asset verifier would refuse the run before PPO.

User explicitly approved withdrawing the **not-yet-dispatched** waiting item and
replacing it under a new SHA/root, correcting only the manifest. New runtime
`f211c0e94603468992baa514f00aaee5fd7780d6` differs from0172fb9 in exactly that one
file (five hashes); all training/action/reward code is byte-identical. All27
registered source hashes now pass. Annotated tag
`candidate/policy-credit-manifest-20260921` is privately backed up.

Replacement root `/var/jfsCache/sc2-policy-credit197-20260921-r2`, wrapper
`spb_acceptance197_r2.py`, container `sc2-policy-credit197-20260921-r2`, tmux
socket `sc2_policy_credit197_20260921_r2` / session `policy_credit197_r2`.
Original32games,2h/16GPUh,128GiB and Sep22 03:15:40Beijing queue expiry unchanged.
CPU preparation now explicitly checks source hashes before actual dry entries.
Old r1 artifacts are preserved; replacement preparation is not a GPU retry.
At17:56:37 Beijing, old r1 was verified withdrawn: `dispatch.json` absent;
queue phase `failed` with empty error is the controller's KeyboardInterrupt
record from the authorized withdrawal, not a model/GPU failure. Old source,
readiness, queue logs and partial preparation are retained.

Replacement controller `0e52cfda411be8565739e00b0fe7e4f7a8779234` is privately
backed up and clean at `/var/jfsCache/sc2-qwen-seeds197-source-20260921-r1/code`.
At17:58:43 Beijing its CPU-only container exited0 after source-manifest checking,
all3actual dry entries/Hydra configs and socket validation: readiness passed,
`cuda_initialized=false`, runtime exactlyf211c0e9. At**17:59:46 Beijing** the
new dedicated tmux queue was dispatched once; at18:01:49 it remained
`waiting-predecessor`, expiry1790018140.699252 unchanged, with no GPU dispatch.
The unchanged panel was104/192accepted at17:56:37, D96batch4 active, zero updates.
The four approved Qwen arms depend on this replacement's real GPU acceptance;
they do not depend on the withdrawn old r1. CPU success still is not GPU proof.

### Terminal GPU precheck failure — September21 21:30 Beijing

The panel completed and r2 dispatched once at21:27:57.601 Beijing after the
recorded resource gate. It exited1 in `pre` at21:30:13.370: canonical action
support rejected generation/PPO EOS/PAD/budget disagreement before the first
model answer. Eight SC2 games started, but zero natural games completed and
zero PPO updates occurred. `result.json == .done`, runtime cleanf211c0e9,
world_size8; train2/post never started. This is a code/config integration failure,
not a measured policy-quality failure. Failed artifacts are retained unchanged.

At21:49 the terminal states and bounded traceback were rechecked and saved in
[terminal handoff](terminal197-20260921.md). Qwen successors are blocked. No
repair, retry, budget reset or Level7 dispatch was performed. The unique
heartbeat197 was deleted after terminal handoff preparation, per its stop rule.

### Newly approved r3 — September21, planned

After115 CPU regressions passed for the EOS/PAD boundary repair, the user
explicitly approved **a new32-game, maximum2h/16GPUh short GPU acceptance**.
This is a new authorized attempt, not an automatic retry or a change to old r2.
Only the transport fix is new relative to the repaired policy; see
[CPU repair evidence](generation-token-fix.md). It is not a Level7 rerun.

- Runtime `ce8b938341cd5b881b4dea8446ad570ed7509f78`; the tested code is identical
  to933be4c, with only the completed evidence documentation added.
- Wrapper `spb_acceptance197_r3.py`, same checked acceptance engine and native
  orchestration9a7b0fa; actual controller SHA will be saved before dispatch.
- Unique root `/var/jfsCache/sc2-policy-credit197-20260921-r3`, source
  `/var/jfsCache/sc2-policy-credit197-source-20260921-r3/code`, container
  `sc2-policy-credit197-20260921-r3`, tmux socket
  `sc2_policy_credit197_20260921_r3` / session `policy_credit197_r3`.
- Run IDs `policy-credit197-r3-pre`, `policy-credit197-r3-train2`,
  `policy-credit197-r3-post`; old roots/results/containers are preserved.
- Same Level6 Harder original SpB, eval seeds, native same-seed UID batches,
  top-p1/T0.8/192 tokens/gamma1/combat0.001, no-thinking, canonical support,
  invalid-credit and all result/consumption/execution gates defined above.
- New clock starts at this run's first GPU dispatch, covers loading/all three
  stages/checkpoint/gaps, max7200s. Existing watchdog stops45s before the ceiling
  for cleanup. No per-stage reset, automatic retry,96-step continuation, or
  automatic Qwen successor; Qwen's failed queue stays untouched.
- Existing queue expiry **September22 03:15:40 Beijing** is retained, not extended;
 128GiB output/source ceiling, eight empty cards/no compute PIDs,600GiB RAM,
 140GiB NVMe and fsync/readback gates unchanged. No reservation or stopping others.
- Read-only resource snapshot23:05:50 Beijing: all8memory/utilization zero,
  no compute PIDs,797183396kB RAM available,3341GiB NVMe available. This is not
  a future guarantee; the controller rechecks before dispatch.

Before enqueue, all3actual dry launchers/Hydra configs/source manifest and
controller unit tests must pass under the new SHA with no CUDA initialization.
This record authorizes one fresh short run only; preparation is not GPU success.

#### r3 actual dispatch and first GPU/SC2 evidence

- Controller `a6aa4c33d0956c9d25cb07b88dbee3e3be6ee264` privately pushed;
  its source clone is self-contained (no borrowed alternate objects), clean and
  separate from all old runs. Runtime remains the frozence8b938 above.
- Local command `python3 -B -m unittest discover -s tests -p
  'test_policy_credit_acceptance197*.py' -v`: **10 tests passed**,0.004s,
  exit0; new test checks r3 IDs, unchanged budgets, own post checkpoint and
  successor prohibition. `git diff --check` passed.
- CPU readiness23:10:03.915 Beijing: all3actual launcher/Hydra entries and
 31source hashes passed, CUDA uninitialized, cpu-container exit0/GPU requests
 null. Per-stage exact configs and source-check.log remain in the new root.
- Complete panel predecessor validation returned true again before enqueue:
  all24result/.done/acceptance triples,192natural games,0updates; no panel rerun.
- At23:11:16 the dedicated tmux queue was invoked once. GPU dispatch began at
  **23:11:17.014 Beijing** (`1790003477.0143175`) after eight-card/resource/fsync
  gates. Absolute deadline **September22 01:11:17.014 Beijing**
  (`1790010677.0143175`), never reset. Root state is `running-unverified`, `pre`;
  no stage is yet accepted.
- At23:12:52 GPU workers had loaded the original5.17B SpB model, initialized
  NCCL and emitted `SC2_ACTION_SUPPORT` EOS151645/PAD151643/budget192 with the
  registered tokenizer SHA; no-thinking mask matched63a9546d…. Container is
  running with its exact r3 ownership label. This is actual GPU startup, not PPO.
- At23:13:24 the actual `checkpoint_evaluation.json` confirmed fresh step0,
  no loaded RL checkpoint, val_only and optimizer_updates0; the exact8paired
  seeds were dispatched once. Bounded SC2 logs show Harder/Air/Flat128 games
  launched and live iteration0; model generation was entered. Manifest is
  cleance8b938/world8. No response log yet at this snapshot, no result/.done or
  accepted pre stage, and no PPO update. The legacy `Qwen3-30B` log-directory
  label is not model provenance; the actual loaded model is SpB.
- Storage snapshot23:13:17:49,717,264bytes against137,438,953,472byte cap.
- Unique same-task heartbeat **197-spb-r3**, every10minutes; normal progress
  quiet, only first real GPU/SC2, first PPO, stages/failure/decisions reported.
  First GPU/SC2 startup is recorded here and reported in this turn; do not
  duplicate it. Delete this monitor after completion or terminal failure handoff.
  Old197 and197-c-level7-10 remain deleted; IDSC stays paused. Qwen stays blocked.

Compact launch receipt: [r3-launch-20260921.json](r3-launch-20260921.json).

#### r3 terminal watchdog failure — September21 23:14 Beijing

The23:13 launch snapshot above is historical, not the terminal state. The host
queue marked `failed` at23:13:47.257 when `budget()`'s `du -sb <r3 root> <r3
source parent>` returned1. The controller's existing fail-closed path stopped
only the exact owned r3 container. Docker confirms **exited137, OOMKilled=false**,
finished23:14:00.894 Beijing; allocated container interval about163.83seconds.
This is an operational storage-measurement failure, not an OOM, model-quality
result, renewed EOS/PAD exception, or a128GiB quota-exceeded finding.

Read-only checks at23:16–23:17 confirmed pre has no result/.done or response
audit yet; train2/post directories never existed. No PPO update or stage
acceptance occurred. Root `state.json` remains stale `running-unverified` because
the host watchdog terminated the container; **queue-state + Docker exit override
that stale child state**. No success/result file is manufactured.

The failed command used capture_output=True but its traceback preserved only
arguments and exit status, not stderr. The exact failing entry/reason is therefore
unknown. One bounded post-stop measurement of the same roots succeeded:
52,726,352 +17,595,104 =70,321,456bytes, far below137,438,953,472. Concurrent temporary
file changes are a hypothesis only, not an established cause. Measurement errors
must not be discarded or counted as zero; no chmod, exclusions, retries, runtime
edits, artifact removal or GPU restart were attempted.

Failure evidence is preserved in [r3-terminal-20260921.json](r3-terminal-20260921.json).
The unique197-spb-r3 monitor was deleted after terminal evidence/handoff; there is
no running follow-up to silently retry. Qwen remains blocked, IDSC paused and all
long training/L7 successors unapproved. Next decision: authorize a CPU-only
repair/diagnostic of budget measurement, then separately consider any GPU retry.

#### Subsequently approved CPU-only storage-watchdog repair

The user's subsequent “批准” approves the proposed CPU-only repair/regression,
not another GPU run. [Scope, behavior and CPU evidence](storage-watchdog-fix.md)
are kept separately from the unchanged r3 failure receipt. No r4 preparation,
dispatch, new deadline, successor or monitor is created by this approval.

### Newly authorized r4 — September21 23:53 Beijing, planned

After the CPU-only watchdog repair, the user explicitly requested “进展如何，把实验
跑上！” This authorizes one fresh repetition of the bounded32game/2h/16GPUh
SpB acceptance, not a restart of failedr3 or a Qwen/Level7/long-training queue.
All historical failure records and deployments remain unchanged.

- New root `/var/jfsCache/sc2-policy-credit197-20260921-r4`, source
  `/var/jfsCache/sc2-policy-credit197-source-20260921-r4/code`, wrapper
  `spb_acceptance197_r4.py`. Container `sc2-policy-credit197-20260921-r4`;
  tmux socket `sc2_policy_credit197_20260921_r4`, session `policy_credit197_r4`.
- Runtime remains `ce8b938341cd5b881b4dea8446ad570ed7509f78`, originalSpB,
  Level6Harder. Same8pre→2PPO/16train→8pairedpost, ownCP2only, seeds,
  T.8/192tokens/top-p1/gamma1/combat.001/LR1e-6, support/credit/no-thinking
  and all original consumed-action/result/execution gates. No model-code change.
- New controller incorporates CPU-tested storage diagnostics/strict measurement
  and collision-free atomic writes from3e7141f; actual frozenSHA recorded at
  preparation. The olddu error's exact cause remains unknown; this is not a
  claim that live traversal can no longer fail. Measurement failure still stops.
- Original queue expiry1790018140.699252 (Sep22 03:15:40Beijing) retained.
  This new attempt has one7200second clock from GPU dispatch including load,
  checkpoint and stage gaps,128GiB output/source limit; never reset/retried.
  Same8empty-card/no-computePID,600GiB RAM,140GiB NVMe andfsync gates.
-23:53:02 resource snapshot: eight0MiB/0% cards, no computePID,
  796984572kB availableRAM,3341GiB NVMe free. No reservation; recheck at dispatch.
- Predecessor remains the already completed24batch/192game/0update panel,
  revalidated from its small receipts, never rerun. Qwen successors stay blocked;
  L7/long training not launched, IDSC paused,46out of scope.

Before launch: privately back up clean controller, run itsCPU tests and all3actual
DRY_RUN/Hydra/source-manifest checks. Single queue dispatch only after readiness;
save actual GPU/SC2 evidence without treating initialization as acceptedpre/PPO.

#### r4 actual dispatch — September21 23:57 / September22 00:01 Beijing

- Clean controller `e87b23f33cf5b93fc4c63ffc11ee70645ff743cd` privately pushed
  before deployment; self-contained source clone (no object alternates).
  Native runtime remainsce8b938, orchestration9a7b0fa, no training-code changes.
- Local26tests:24passed+2Linux-only skips; node197 actual26SpB/storage tests
  plus7Qwen compatibility tests: **33passed,0skips**. Three actual dry entries,
  Hydra configs and31source hashes passed; readiness23:57:16.121,
  cpu-container exited0, DeviceRequests=null, CUDA uninitialized.
- Dedicated tmux queue launched once at23:57:38. Actual GPU dispatch
  **23:57:39.137** (`1790006259.1373603`), Docker started23:57:39.184.
  Eight-card/RAM/NVMe/fsync and all24panel-batch predecessor gates passed.
  Absolute ceiling **September22 01:57:39.137 Beijing**
  (`1790013459.1373603`), not an ETA and never reset.
- By00:00:16 actual logs show original5.17B SpB loaded, NCCL initialized,
  eight SC2 workers in Harder/Air/Flat128, game iteration0 and online generation
  entered. Small evaluation proof confirms freshstep0/no RL checkpoint,
  exact8paired seeds and0optimizer updates. Manifest clean ce8b938/world8.
  The legacyQwen3-30B log label is not the actual loaded model.
- By00:01:07 worker action-support EOS151645/PAD151643/budget192 and tokenizer
  a63080b4… match; no-thinking mask63a9546d… matches. Queue remainsdispatched,
  pre running; no response audit/result/.done or accepted stage yet. This is
  actual GPU/SC2 startup, **not first PPO or completed acceptance**.
- Storage sample23:58:39:49,022,557bytes, both exact roots, exit0/no stderr,
  against137,438,953,472bytes. No errors in bounded queue-log tail at00:01:07.
- Unique same-task monitor `197-spb-r4`, every10minutes, created after checking
  no previous197monitor exists. Healthy progress quiet; firstPPO/stages/failure/
  decisions notify. First actual GPU/SC2 is recorded and notified in this turn,
  do not repeat. Delete monitor at completion or terminal failure handoff.
  Qwen/L7/long-training/46 remain unstarted; IDSC remainspaused.

Compact immutable snapshot: [r4-launch-20260921.json](r4-launch-20260921.json).

#### r4 pre accepted / authorized Qwen successor — September22 00:13 Beijing

Pre naturally finished at00:06:52, accepted at00:06:55.630: matching result/.done,
exit0, clean runtimece8b938/world8, finite metrics,8natural games/0truncation/
0updates,6wins2defeats. Actual consumed answers **44/44 valid**,44validated parsed
plans,504validated queue entries,353locally queued model Depot/Marine commands.
`acceptance-pre.json` preserves exact evidence; consoleSHA
`61ca86644f18a42605071aa5063e46b9d7267581a83941e10fbe3427a40861b2`.
This mechanical precheck passed; it is not RL improvement or causal win evidence.
At00:13:37 state was train2/completed[pre], with no PPO audit/metrics yet. Do not
claim a completed PPO update merely because the training stage is active.
Deadline1790013459.1373603 remains unchanged.

The user subsequently authorized requeueing the original Qwen four-arm matrix
after this run actually passes. [NewQwenr3](qwen-seeds197.md) was enqueued once at
00:13:23 and is waiting on this exactr4, not failedr2/r3. This supersedes the old
no-Qwen-successor authorization prospectively, without editing the frozen SpBr4
deployment. No extra SpB/L7/96-step training is authorized. Unique197-spb-r4 monitor
was updated in place to follow both queues; pre completion was reported in this
turn and should not be notified again. First actual PPO remains pending.

#### r4 first PPO / train2 accepted — September22 00:28 Beijing

Read-only small-receipt verification found train2 naturally completed at
00:24:22.098 Beijing and accepted at00:24:44.608. `result.json`, `.done` and the
acceptance's embedded result agree exactly: exit0, clean ce8b938/world8,
start0/last2/completed2,16natural games,0truncation,finite metrics and completeCP2.
The 25 necessary CP2 files (data.pt plus8model/8optimizer/8extra-state shards)
were checked against recorded sizes without reading checkpoint contents.
Actual training seeds are2732×8 then43567×8.

- Two pre-PPO audits accepted44/44 and37/37 actual consumed answers. Their
  `optimizer_updates_for_this_batch=0` fields describe the before-update gate;
  the two completed metric rows and terminal result establish actual PPO.
- Step1/2 gradient norms are1.368/65.487, both finite and positive. Actual
  consumed action legality is81/81;81parsed plans,1236validated queue entries,
  781locally queued model Depot/Marine commands. This is local command evidence,
  not proof of production completion or a causal contribution to wins.
- Both rows report0invalid tokens and0invalid-positive advantage removals,
  with invalid advantage maximum0. Thus this sample does not exercise the
  invalid-answer correction branch; its prior CPU regression is separate.
- Training outcomes15wins/1defeat are descriptive only. Two updates, constrained
  legality and this small training sample do not establish strategic learning
  or architectural superiority.
- At00:28:11 root state was post/completed[pre,train2]. Post's actual loader
  returned own `runs/train2/checkpoints/global_step_2`, loaded_global_step2,
  val_only=true/optimizer_updates0; original8paired seeds match. Post manifest
  remains clean ce8b938/world8. No post result/.done existed at inspection;
  post is **not yet accepted** and Qwenr3 remains waiting-predecessor/completed[].
- Latest storage receipt at00:28:01:64,339,139,444bytes across the exact two
  roots, exit0/no stderr, below128GiB. Original deadline1790013459.1373603
  (01:57:39.137 Beijing) remains unchanged. No restart or new dispatch occurred.

Immutable compact evidence and small-file SHA256s:
[r4-train2-20260922.json](r4-train2-20260922.json).
First actual PPO and train2 completion were notified in this heartbeat; do not
repeat those events. Continue the same197-spb-r4 monitor for post and Qwenr3.

#### r4 completed / Qwen released — September22 00:47 Beijing

Post naturally ended at00:35:46.347 and was accepted at00:35:48.761 Beijing.
Host queue and child state both reportcompleted/exit0 with all3stages. Read-only
cross-checks of all3result/.done/acceptance triples and clean ce8b938/world8
manifests passed. Post's8natural games/0truncation/0updates and finite metrics
passed; own completeCP2 load returned, exact paired seeds and all8rank RNG
receipts were independently verified. No deployment or runtime was changed.

Post had35/35valid consumed answers,35parsed plans,636validated queue entries
and379locally queued model Depot/Marine commands. Across pre/train2/post this
is160/160valid answers,32natural games and exactly2PPO updates. The frozen
controller's acceptance covers actual worker support banners, no-thinking output
and plan/queue/local-command provenance; this heartbeat read the small receipts
and bounded log tail, not large checkpoints or complete trajectory logs.

Paired wins6/8pre→5/8post, difference−12.5percentage points:5win→win,
1win→loss,0loss→win,2loss→loss. Marginal Wilson95% intervals are40.9–92.9%
and30.6–86.3%; they are not a confidence interval for the paired difference.
**This short acceptance demonstrates mechanical validity and execution/update
plumbing, not improved strategy or a statistically established decline.**
No sampled invalid tokens were seen during train2, so its credit-correction
branch remains CPU-tested rather than exercised on invalid sampled responses.

Final storage receipt00:35:46:64,408,946,540bytes across both exact roots,
exit0/no stderr, below128GiB; original01:57:39ceiling unchanged. This current
success does not establish that the historical storage failure is root-fixed.

The already queued Qwenr3 released automatically at00:36:25.330 after its
predecessor/resource gates. No manual dispatch/retry occurred. Its first
Level6same-seed arm passed pre and is training; see[qwen-seeds197.md](qwen-seeds197.md).
Evidence:[r4-complete-qwen-r3-start-20260922.json](r4-complete-qwen-r3-start-20260922.json).
Post/all-SpB completion and Qwen firstGPU/pre completion were notified in this
heartbeat. Keep the same197-spb-r4 monitor for the remaining Qwen work; do not
repeat these events or promote SpB to Level7/96-step training.
