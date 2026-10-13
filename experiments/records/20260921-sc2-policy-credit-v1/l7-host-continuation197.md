# Authorized host-supervised L7 continuation — September22

September23 approved diagnosis/repair update: r4 remains failed and immutable;
no new dispatch. The startup-only candidate and CP8 continuation cost proposal
are [recorded separately](sc2-startup-race197.md). This supersedes no historical
result or gate; additional48game slots still need explicit approval.

User: “快按方案续排实验” explicitly accepts the bounded continuation proposal.
Same experiment record, branch `codex/fix-quiescent-storage`; new r4 RUN only.
Existing failed roots are immutable; accepted Qwen CP96-only eval is verified,
never replayed. No failed GPU run is automatically retried.

## September23 Qwen random failure handoff

Final read-only check17:45–17:47Beijing superseded the earlier12:17running
snapshot: the container had exited1 at12:26:16Beijing, OOMKilled=false.
Host queue and part both failed; result and.done are identical failed receipts.
Qwen returned global13 (11new outer PPO updates),88natural games/76wins,
324/324valid consumed answers; step14 reset had been dispatched, no eval96.
See [compact failure evidence](l7-qwen-random-failure-20260923.json).

Observed trigger is `SC2 reset failed after retries`; the bounded traceback
also shows `ServerDisconnectedError: Server disconnected` in SC2Process
WebSocket connection and reset returning no observation. The underlying
disconnection cause is not established. Do not label this a model-quality,
answer-legality, OOM or proven storage failure. Existing last storage receipt
was successful but historical, not a fresh post-failure measurement. Internal
SC2 log wall-clock labels differ from host/result timestamps; failure time is
grounded in result/Docker UTC timestamps.

Only the CP8 directory is present; no tensor contents were read, no restart
readiness established. Do not claim step13 is checkpointed. Failed run and
all evidence remain unchanged. No automatic fix, retry, resume, new group or
deadline extension was performed. Ask user direction for investigating and
fixing reset/connection failure and any bounded continuation proposal.
The existing monitor was briefly refreshed for the12:17stage transition,
then deleted after the final failure was verified and handed off; no duplicate
monitor was created. SpB completion remains valid; SpB-random budget is pending.

## September23 SpB completion and Qwen random start

Historical snapshot verified September23 12:17:42Beijing via read-only SSH;
later Qwen failure above takes precedence. The
[compact receipt](l7-spb-complete-qwen-random-start-20260923.json) contains
source hashes, acceptance summaries, terminal container states and seed/load
evidence. No remote writes, tests, requeues or runtime modifications this turn.

- SpB long training finished11:45:25, evaluation11:58:36; host stage and part
  completed/exit0, both containers exited0, result=.done. Native ownCP2
  recovery,94returned PPO metrics/audits, finite positive gradients
  (0.2145578656..131.2341400), nonpositive invalid advantage, exact94same-seed
  batches and12CP inventories of26nonempty required files passed. This monitor
  read only checkpoint names/stat, not tensor contents. Long training has
  440/752wins; including short train2, full96batches total445/768(57.94%).
- SpB pre4/8 → ownCP2 post3/8 → ownCP96 eval2/8. The final8natural games
  had0updates and33/33valid consumed answers,33plans,666validated queued
  entries and377local model commands. Actual CP96 load returned and all8
  rank/seed/CPU-CUDA RNG hash pairs matched ownpost. Local command evidence
  is not production completion or a causal victory attribution.
- There is no demonstrated paired improvement; eight paired seeds are too
  few to establish stable degradation. Training wins across changing seeds,
  mechanically constrained legality and nonzero gradients do not establish
  learned strategy, generalization or an architecture advantage.
- Existing Qwenrandom continuation automatically admitted11:58:40; actual
  container started11:58:41. Own accepted randomCP2 load returned, not same96.
  Documented verified-legacy-ledger recovery remains non-bitwise because
  parent driver RNG is unavailable. First reset2 seeds are
  36,17,96,12,79,32,68,90; actual canonical/no-thinking worker banners match
  the frozen hashes. Returned step9 has gradient40.516203656792641,
  update_actor13.972992777824402seconds, invalid advantage0 and validity1;
  seven new outer PPO updates completed, step10 SC2 dispatched. Pre-update
  audit alone was not used as update proof. This mixed-seed UID ablation
  retains scenario-difficulty confounding.
- Qwen dispatch fixes its cutoff to September25 11:58:40Beijing
  (1790308720.0467553), bounded by unchanged suite September26 19:06:02.
  These are budget cutoffs, not ETAs. Existing storage samples all exit0 with
  empty stderr and under their frozen limits; no new du or GPU diagnostics.
- Collector-only initial errors (eval-only field assumed in training result;
  oversized guardian refused at1MiB cap) were corrected in the read-only
  collector. The1,070,614-byte train guardian was not read; host terminal
  state/actual acceptance/Docker exit0 were checked. Neither issue was an
  experiment failure or a GPU retry.

Notify once for SpB long train/eval completion, Qwenrandom first actual events
and later failure. Its failure handoff is the monitor terminal condition.
SpB-random remains planned pending length and
budget confirmation. All prior failed records and Qwen same96 gradient gaps
remain immutable.

The existing `197-l7-r4` heartbeat was first updated in place (same ACTIVE status,
10-minute cadence and target task) to read this transition receipt and suppress
already notified SpB completion/Qwen first events. No duplicate monitor was
created. The OpenAI Docs skill guided the scheduled-task update, following the
[official task-update documentation](https://learn.chatgpt.com/docs/automations#ask-chatgpt-to-create-or-update-scheduled-tasks).
Readback confirmed the Qwen fixed cutoff and receipt reference; following the
final failure check, the tool confirmed deletion of this exact monitor.
Validation for
this documentation-only turn: JSON parse/count/deadline assertions and
`git diff --check` passed; no model or server tests were rerun.

## Frozen plan

- SpB original5.17B L7same: pre8 → train2/16 → post8; its own complete native
  CP2/driverRNG must pass actual gates before94newPPO/752games→eval96/8.
- Then Qwen L7random uses only its accepted r4/l7-random CP2;94newPPO/752games
  → paired eval96/8. Accepted legacy driver-RNG gap remains non-bitwise.
- New1552games/190PPO plus8prior failed-pre dispatch slots =1560cumulative
  dispatch slots. No extra model group, no replay of accepted prefixes/eval.
- Original SpB first start1790075162.305692 and cutoff1790247962.305692
  (September24 19:06:02Beijing) remain. Suite cutoff1790420762.305692
  (September26 19:06:02) remains. Qwen own48h from its first admission is bounded
  by suite cutoff. Per-arm384GPUh/1TiB; suite768GPUh/2TiB. No deadline extension.

New root `/var/jfsCache/sc2-l7-followup197-20260922-r4`, source
`/var/jfsCache/sc2-l7-followup197-source-20260922-r4/code`, wrapper
`l7_followup197_r4.py`. Dedicated socket `sc2_l7_followup197_20260922_r4`,
session `l7_followup197_r4`. Stage containers append stage to
`sc2-l7-followup197-20260922-r4-<part-slashes-as-hyphens>`.
Source/runtime SHA is recorded in new deployment before CPU tests or queue.

## Operational change and accounting

Use the accepted host_stage197 + independent storage_guardian197 path. Only
the host samples; stage container execs the unchanged launcher, no inner
controller/watchdog. A newly created full Docker ID with exact ownership label
is the only pause/resume/stop target. Read-only container rootfs, no Docker log
driver; early entry stdout/stderr is retained in the accounted part. HOME and
compiler caches use the part's /tmp bind. Only part, tmp and stable lock inode
are writable binds; all models/SC2/dependencies/source/parents are read-only.
/dev/shm is128GiB RAM, not a persistent output path. Pauses count toward the
same wall clock and remain unverified for SC2/Ray/NCCL timing until actual GPU.

Suite exact11roots: newoutput, newsource, Qwenrandomparent, r1/r2/r3 output and
source (six), both prior CPU staging roots. Each arm includes its output,
newsource, all eight retained roots; Qwen additionally includes its parent.
No excludes, filtered errors, du retries, partial totals or last-good fallback.
All retained containers/CPU fixtures must be exited/unpaused before queue;
there is no concurrent writer to those roots. Host metadata uses shared lock;
guardian writes only an existing terminal inode. Measurement failure is unknown.

Before every GPU stage: eight idle cards/no compute PID,600GiB RAM,
1084GiB local free and fsync/readback. Resource waits do not reserve cards.
Independent guardian loss recovery remains bounded; host/kernel/daemon loss
and historical GPU stop timeout are not claimed solved. Any stage/gate failure
blocks all successors and requires direction; no automatic replacement RUN.

## Verification and use

One `prepare`, then full existing real-tokenizer/worker CPU regressions and new
host/controller regressions, all zero-skips on197. All seven actual DRY_RUN/
Hydra/source checks pass on the exact new runtime. SpB long native-parent gate
remains deferred until short GPU acceptance; it is never bypassed.
Run `cpu-command INDEX` / `regressions-command 0` for bounded CPU containers;
`host-regressions` is host-only. Queue once with `queue` in dedicated tmux.
No launcher/action/reward/seed/PPO hyperparameter change. Binary64-v1 strict
positive gradients, invalid advantage<=0, natural outcomes, real load/seed/RNG,
action-consumption and26files perCP gates remain. Legality is not learning.

Status: authorized preparation; no GPU dispatch claimed until real receipts.
Superseded by actual22:03:15Beijing [launch evidence](l7-host-r4-launch-20260922.json):
single queue21:59:59.55, pre Docker start22:00:00.64; runtime/controller
9cb291ea5f50de205c5d88371e08ce229b7d9d04 was pushed and remote-verified before
dispatch.214model-side and71host Linux tests passed with zero skips; all7actual
launchers/Hydra/source checks passed. Four CPU containers exited0/no GPU.
SpB worker5.17B/NCCL/canonical+no-thinking banners and SC2 planner boundary
observed;8eval seeds registered,0PPO. Pre completion remains pending. Exact
11-root measurement50,268,978,045bytes/exit0/empty stderr, owned pause and
unpause verified. Future native SpB CP2 gate remains mandatory.
Single197-l7-r4 heartbeat created every10minutes under the OpenAI Docs
[in-chat scheduled-task workflow](https://learn.chatgpt.com/docs/automations#schedule-a-task-inside-a-chat),
with quiet healthy progress, actual event reporting, terminal deletion and
per-round same-branch evidence commits. No old monitor was reactivated.
Local107-test run initially exposed a test fixture's unbound mocked ROOT (one
error, four Linux-only skips), corrected before any remote preparation. This
was a CPU fixture error, not a GPU attempt; final results recorded at launch.

## Purpose clarification — September22 22:13Beijing

User requested an explanation of each experiment, not another launch or live
status check. This round reviewed this frozen-plan record, the experiment README,
[same-seed question/results](qwen-l7-long197.md),
[matched follow-up design](l7-followup197.md) and
[four-arm short matrix](qwen-seeds197.md#matrix-and-question). No server action,
new measurements, model test, queue change or extra experiment was performed.

- Historical original SpB/D96/C96 Level6 panel: evaluate existing checkpoints
  under one frozen zero-update protocol, separating training-curve impressions
  from matched evaluation. It uses the historical protocol, not the new repair.
- SpB Level6 repair short acceptance: check real consumed-plan legality, command
  execution, two actual PPO updates and own-CP2 evaluation before spending on
  long runs. Passing this mechanical gate is not evidence of strategic learning.
- Qwen four short arms (Level6/7 times same/per-game-random): check the same
  repaired pipeline in every intended condition, including both seed protocols.
  Two updates and eight paired evaluation games cannot rank long-run methods.
- Qwen Level7 same96: test whether longer training preserves validity and improves
  paired outcomes beyond its own accepted CP2. CP2 paired wins7/8 versus CP96
  5/8 show no improvement in this sample, not statistically established stable
  degradation. The original six-gradient evidence gap remains unrepaired.
- SpB Level7 same short+96: first establish a native accepted Level7 CP2, then
  compare its learning change with Qwen under matched environment interactions,
  generation/action/reward/executor settings and same-seed grouping. SpB5.17B
  versus Qwen4B, unequal FLOPs and executor attribution preclude a pure
  architecture-superiority claim from this comparison alone.
- Qwen Level7 random96: independently continue the random arm's own CP2, keeping
  model and repaired method fixed while changing within-step seed grouping.
  Test whether broader within-batch scenarios yield different learning/paired
  outcomes from same-seed training. Mixed-seed relative advantages also mix
  scenario difficulty with policy quality; randomization is not an unbiased
  credit fix or guaranteed improvement.

Same means one sampled scenario seed shared by eight games in a step, with a
new draw next step, not one fixed seed for all96steps. Random means eight draws
with replacement from the same0..100range, so collisions are allowed. Total96
steps is a matched interaction budget (768training games), not a convergence
guarantee or algorithmic requirement. Zero-update paired pre/post/final evals
are measurements, not extra training arms. Constrained output validity and high
training wins are distinct from held-out learning evidence. Current r4 host
supervision addresses operational storage-accounting failures, not a new model
method; it does not authorize any additional scientific arm.

Validation: reviewed local source records and documentation-only diff; no new
GPU/model tests needed or claimed. This clarification is committed/pushed on
the existing branch under AGENTS6.4; runtime deployments remain frozen.

## User-requested conclusions — September22 22:26–22:28Beijing

[Read-only snapshot](l7-conclusions-20260922-222637.json): SpB L7 pre accepted,
result=.done/exit0/binary64-v1,8natural games4wins4defeats/no truncation/0updates,
46/46consumed answers valid,46plans/602validated queue entries/367local model
commands. The actual pre container exited0 and host state completed[pre]; train2
container is running with a clean/world8 manifest. Its first pre-update audit
has40/40valid answers, pending_global_step1 and optimizer_updates_for_this_batch0;
metrics/result absent. This snapshot does not establish a completed PPO update.
Short post and both long dispatches remain absent. Existing suite measurement
50,926,218,661bytes/exit0, actual owned pause/unpause verified; no failure receipt.
Pre completion is reported to the user this turn; avoid duplicate event notices.

The evidence supports maintained mechanical legality in the accepted repaired
short arms and this pre stage, not a learned strategic gain. Historical Level6
fixed-protocol panel original31/64,D9628/64,C9627/64 does not demonstrate trained
model improvement; its no-thinking/top-p.9 protocol differs from this repair.
Accepted Qwen short arms have929/929valid consumed answers; L7random7/8→8/8
is one extra win in a tiny panel, not established random-seed superiority.
Qwen same96 paired evaluation7/8atCP2→5/8atCP96 likewise provides no positive
learning evidence. Eight pairs do not establish stable deterioration, and the
six historical rounded-gradient gaps remain unknown/failed strict acceptance.
SpB long and Qwen random long have no new results yet, so neither architecture
superiority nor the benefit of random grouping can be concluded.

Validation: bounded small JSON reads, pre result/.done hash equality, natural
count/zero-update/legality arithmetic and acceptance evidence checked; local
JSON parsing and diff checks. No new model test, GPU diagnostic, CP content
read, remote mutation, retry or queue change. Same-branch evidence commit/push
required; this status query does not modify any frozen runtime.

## Seed and no-thinking clarification — September22 22:38–22:40Beijing

User asked what is running, whether Qwen per-game random seeds were actually
tested, and whether the earlier no-thinking issue was repaired/tested on SpB.
[New read-only evidence](l7-protocol-status-20260922-223845.json): SpB L7same
train2 completed22:32:15Beijing, result=.done/exit0/16natural games5wins11defeats,
103/103consumed answers valid,103plans/1343queue entries/895local commands.
Both actual returned PPO rows are present: gradients185.50870361328126 and
99.85015511512756, update_actor154.801962133497s and93.73110850341618s,
invalid_advantage_max0. Frozen acceptance-train2 passed; host completed[pre,train2]
and post container running. Post manifest requests ownCP2, but post result/load
completion was not verified in this snapshot. Pre remained4/8wins/46valid
answers. Both long dispatches absent. First actual SpB PPO and train2 completion
reported to the user this turn; avoid duplicate event notices.

Actual seed ledger is49x8 then97x8 (same_uniform101), not per-game random.
Actual train argv retains sc2_no_thinking=True and all three actor/rollout/ref
no-thinking plus canonical-action tokenizer paths. The launcher base top_p0.9
is followed by the final explicit top_p1.0 override; val top_p1.0 too, as verified
by the frozen CPU Hydra checks. Policy-credit is enabled with invalid penalty0.1
and validity floor0.5. No running configuration was changed by this query.

Qwen per-game random was actually accepted on both Level6 and Level7 in the
[four-arm short matrix](qwen-seeds197.md): each8pre+16train(twoPPO)+8post;
paired L6random8/8→8/8, L7random7/8→8/8. The96step random continuation has not
dispatched and remains after SpB acceptance/long completion. These two-step
results cannot establish random-group superiority.

The current SpB test is **not** a rollback to historical unconstrained,
thinking-allowed Level6 generation. No-thinking remains enabled; the repair
adds canonical action grammar/quotas and complete ending under192tokens,
new-policy top_p1, matching generation/PPO support, EOS/PAD compatibility and
post-centering invalid credit. It neither deletes/resamples bad answers after
generation nor establishes that internal reasoning is disabled. Old no-thinking
alone did not enforce legal action syntax. A sole-cause claim that no-thinking
caused the historical collapse is unsupported without a controlled on/off
comparison. Such a rollback-only SpB Level7 control has not been completed in
this authorized queue. Earlier successful SpB Level6 repair acceptance and this
L7 training show actual legal consumed output, not established strategic gain.

Validation: actual small receipt hashes, train result/.done equality, two finite
positive returned PPO metrics, acceptance evidence, seed ledger and explicit
generation overrides checked; JSON parsing and diff checks only. No new model
test, large artifact read, server write, runtime edit, restart or added arm.

## SpB random-arm coverage — September22 22:45Beijing

User asked whether SpB per-game independent training seeds have been tested.
Under the current repaired protocol, **no**: accepted SpB Level6 training used
2732x8/43567x8; the current Level7 short used49x8/97x8 and its continuation is
same-seed. Completed independent-seed short arms belong to Qwen. Historical
SpB mixed-seed runs used a different generation/credit protocol and do not fill
this repaired-method control. The approved follow-up explicitly excludes an
extra SpB random arm; a full model-by-seed-mode long comparison therefore lacks
that cell. No extra arm or budget is inferred from this status question.
Checked local acceptance197.md, README and l7-followup197.md frozen-plan scope;
no fresh server query, mutation or model test. Documentation diff checked and
same-branch GitHub sync required by AGENTS6.4.

## Short completion, long admission and requested addition —22:50Beijing

[Read-only22:50:33snapshot](l7-followup-status-20260922-225033.json): SpB short
completed[pre,train2,post]/exit0; post result=.done/8natural games3wins5defeats,
0updates/actual ownCP2load returned and registered8seeds. Post94/94valid consumed
answers/94plans/606queue entries/401local commands. Combined short243/243valid
answers,32natural games/2PPO; paired pre4/8→post3/8, no demonstrated improvement.
New native-parent CPU gate passed, then long dispatched22:45:12 using the
original unchanged SpB deadline. Actual model/optimizer/dataloader/SC2state load
returned atstep2, source=checkpoint, nextreset2/53x8. Long train96 container live;
no completed resumed PPO row yet in the1MiB-bounded tail. Qwenrandom dispatch
still absent. Short completion and first actual long restore reported this turn.

Two completed short steps took580.8693483248353 and630.8087096717209seconds;
mean605.8390289982781seconds/step. Extrapolating94remaining steps gives
56948.86872583814seconds=15.8191hours of training alone. Conditional rough ETA
including checkpoints/eval/loading is16–20hours from this snapshot, approximately
September23 15:00–19:00Beijing. Only two steps underlie it, not a reliable long-run
speed estimate or a promise. SpB hard ceiling remainsSeptember24 19:06:02 and
suiteSeptember26 19:06:02; they are not ETAs.

User additionally requested the missing SpB per-game-random arm. Its
[matched proposal](spb-l7-random197.md) is registered as planned after Qwenrandom;
an async question requests explicit96step/48h384GPUh1TiB versus short-only budget.
No new arm was actually prepared/enqueued/dispatched, no existing runtime changed.
This pending addition is not covered by the old two-arm budget or former exclusion.

Checks: small actual state/result/.done/acceptance/load/parent-readiness hashes,
bounded timing rows and arithmetic, JSON parsing and documentation diff. No
checkpoint-content read, GPU diagnostic, new model test or server mutation.
