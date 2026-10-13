# SpB Level7 independent-seed addition — train96 accepted, eval96 awaiting admission

## September24 10:20:34 Beijing — exact admission blocker identified

User explicitly requested a current server-idleness/launch diagnosis, permitting
read-only GPU/ownership/RAM/disk checks beyond the routine small-receipt monitor.
All8GPUs show0memory/0utilization and no computePIDs;759.73GiB availableRAM passes.
AvailableNVMe810.11GiB is below the unchanged1084GiB gate by273.89GiB.
The frozen controller applies that training-size headroom check to eval96 too.
This explains current admission waiting; it is not the old Qwen gradient issue.
No server mutation or gate relaxation. User subsequently chose only a new Qwen
same-seed full-rerun budget proposal, not SpB admission repair; retain original
queue, shared deadline and sole monitor. [Diagnosis](spb-admission-precision-diagnosis-20260924-102034.json).

## September24 09:35:05–09:37:50 Beijing — train96 accepted, eval96 awaiting admission

The native ownCP2→96 long stage ended09:26:28 with94 actual returned PPO phases,
752natural games/505wins/247defeats, no truncation, and1834/1834valid consumed
answers. The frozen verifier's acceptance result matches result and .done.
Clean83f3530/world8/binary64-v1; all94 final metrics are finite, gradients and
update_actor times positive, invalid_advantage_max0,94accepted audits, and all
privateRandom0 reset2–95 batches match. The monitor independently checked the
small266,106byte final metrics file; it did not reread full logs or checkpoint contents.
CP8/16/24/32/40/48/56/64/72/80/88/96 each have26required nonempty files by stat.
Acceptance records1,834plans/77,955validated queue entries/47,164local Depot/Marine
commands; local queuing does not prove production completion or causal wins.

Exact long train96 container40d5a3f43a41fffb0eb51ea9a1c816b118cddef0b151464946d0c663fc024217
exited0 at09:26:50, matching guardiancompleted/originaldeadline/finalstate and
owner. Host supervision isstage-completed withcompleted[train96]; queue is still
running-unverified forlong. Eval96 admission receipt and run are absent. Continued
storage sampling and frozen control flow indicate waiting for unchanged admission;
the exact unmet resource is not established, and no GPU diagnostics were performed.
No retry, repair, redispatch, budget increase, or monitor-side server mutation.

Combining accepted short1–2 and long3–96 gives96PPO/768training games/513wins,
1,959/1,959valid consumed answers. These are training totals, excludingpre/post/
the pending final evaluation. Existing strict two-root storage831,162,453,513bytes/
1TiB, exit0/empty stderr/no failure; shared absolute deadline1790356959.0174987
(September26 01:22:39Beijing) unchanged. Sole monitor remains for ownCP96 paired
8-game, zero-update evaluation with all8rank/seed/CPU-CUDA RNG matched to ownCP2post.
Training legality, win rate and positive gradients do not establish strategic learning
or architecture superiority. Notify this training completion once.
[Compact terminal evidence and hashes](spb-random-train96-complete-20260924-093505.json).

## September24 02:15:46 Beijing — short accepted, native long continuation started

Post ended02:11:32 with8 natural games/4wins/4defeats,0updates,52/52 actual
consumed answers valid,52plans/583queue entries/336local Depot/Marine commands.
Its80 response records are not the consumed-answer denominator. Result=.done=
acceptance result; clean83f3530/world8/binary64-v1, actual ownCP2 load returned,
original8seeds and all8 explicit rank/seed/CPU-CUDA RNG fields match pre.
Exact owned post container exited0, guardian completed with the same ID/owner
and original deadline. Short host/state completed[pre,train2,post]/exit0.
Combining the previously accepted stages gives32natural games/2PPO and
226/226valid consumed answers. Paired pre4/8 → CP2post4/8 shows no demonstrated
gain; do not infer strategic learning or architecture superiority.

The frozen controller created accepted-spb-random-full-state-prefix-v1,
with driver_rng_unavailable_accepted=false. Existing CPU parent-state receipt
has all8rank scheduler epoch2/RNG keys, native driver RNG and next reset2 seeds;
parent-readiness passed with actual_parent_verified=true before dispatch.
The monitor read these small receipts, not checkpoint contents or full logs.

Long train96 container40d5a3f43a41fffb0eb51ea9a1c816b118cddef0b151464946d0c663fc024217
started02:11:52, exact long owner, running/unpaused. Its actual model/optimizer/
dataloader load returned from own shortCP2, source=checkpoint, global2/reset2,
next36,17,96,12,79,32,68,90. Clean83f3530/world8/binary64-v1, matching canonical/
no-thinking worker banners and all8SC2 planner boundaries observed. This is the
first resumed global3 batch, not a returned PPO: no long audit/result yet.
No legacy fallback, extra games, repeat dispatch or monitor-side server write.

Long dispatch preserves the original start1790184159.0174987 and deadline
1790356959.0174987 (September26 01:22:39Beijing), shared with short/eval. Existing
strict two-root storage64,643,411,659bytes/1TiB, exit0/empty stderr/no failure.
Only short/post completion and native long-start are new events; previously
reported firstGPU/SC2/PPO/train2 events are not repeated. Sole monitor retained.
[Compact evidence and hashes](spb-random-short-complete-long-start-20260924-021546.json).

## September24 02:05:53–02:06:50 Beijing — train2 accepted, post loaded ownCP2

Train2 ended02:00:03 with2 actual returned PPO phases/16natural games/8wins,
125/125valid consumed answers,125parsed plans/1,633validated queue entries/
927local model Depot/Marine commands. Result=.done=acceptance result;
clean83f3530/world8/binary64-v1, both metrics finite. Gradients are
119.08253415425618 and76.01430397033691; update_actor durations
168.143536365591 and118.2405032273382seconds; invalid advantage maxima0.
Both independent Random0 seed batches match. Exact train2 container exited0
at02:00:25, guardian completed with matching owner/ID/originaldeadline.

Hostcompleted[pre,train2], nowpost. Its exact owned container
e7d857c5a6f3bf8ea0a9ee6e69d048fe6aa76a5994014a0c9a47221856c125ec
started02:00:35, running/unpaused. Actual ownCP2 load returned, val_only/0updates,
original8seeds and all8rank/seed/CPU-CUDA RNG fields match pre (presence verified;
PID equality not required). Correct canonical/no-thinking worker banners and
SC2 planner/terminal boundaries observed. No post result/.done/acceptance yet.
CP2 inventory26/26 nonempty includes sc2_state.pt, but no checkpoint contents
were read. Full native driver/rank-state parent-readiness and short terminal
acceptance remain mandatory before long; both gate and dispatch are absent.

Existing strict two-root storage64,536,083,382bytes/1TiB,exit0/empty stderr,
no failure. Whole-armSeptember26 01:22:39deadline and budgets unchanged.
Notify train2 completion once; previously notified first PPO is not repeated.
No server mutation, repair, new experiment or learning-gain claim.
[Compact stage evidence](spb-random-train2-complete-20260924-020553.json).

## September24 01:58:25 Beijing — first returned PPO verified

The bounded3MiB console tail contains actual returnedstep1: finite positive
gradient119.08253415425618, update_actor168.143536365591seconds,
invalid_advantage_max0. Reset0 used49,97,53,5,33,65,62,51;8 natural games/5wins
and46/46 valid consumed answers. Reset1 used100,38,61,45,74,27,64,17 and closed
8natural games/3wins with79/79 valid consumed answers. Its pendingstep2 audit
is accepted but no second returned PPO is observed, so onlyone update is counted.
Pre-update audit is not optimizer completion;16 closed games do not mean2PPO.

Exact owned train2 container is running/unpaused, hostcompleted[pre], original
clean83f3530/world8/binary64-v1 manifest. No train2 result/.done/acceptance, post,
CP2 inventory/parent-readiness or long dispatch at this check. Empty running
guardian slot and missing synchronizedpart/state remain expected. Existing
strict two-root storage850,883,079bytes/1TiB,exit0/empty stderr,no failure;
sharedSeptember26 01:22:39deadline unchanged. No server mutation or retry.
This is the first PPO notification, not stage acceptance or learning evidence.
The1MiB first read missed the earlier return line; follow-up boundedread
2,409,601bytes (cap3MiB) confirmed it. No full log is saved or uploaded.
[Compact first PPO evidence](spb-random-first-ppo-20260924-015825.json).

## September24 01:39:18 Beijing — pre accepted, fresh train2 started

Pre ended01:32:50 with8 natural games:4 wins/4 defeats,0 updates,49/49 valid
consumed answers,49 parsed plans/607 validated queue entries/362 local model
Depot/Marine commands. Result=.done=acceptance result; clean83f3530/world8/
binary64-v1 and the original8 evaluation seeds match. Exact pre container and
guardian completed/exited0 without OOM. This is the untrained baseline, not gain.

Host supervision now listscompleted[pre], stage train2, and exact owned
container612a6148306369771e177611693bfd1447460ff026c8a102f1bad788ed106028
running/unpaused from01:33:01. The first registered training batch matches
independent Random0 seeds49,97,53,5,33,65,62,51. Actual SC2 games are progressing;
no returned PPO was observed in the bounded tail, and no train2 result/acceptance
exists yet. The empty running guardian slot and unsynchronized part/state are
expected. Post, native CP2 parent-readiness and long dispatch remain pending.

Existing exact two-root storage307,702,761bytes/1TiB measuredexit0/empty stderr,
no failure receipt. Original1790356959.0174987 deadline and all budgets unchanged.
No remote mutation, repeat dispatch or repair. Notify this pre completion once;
retain the sole monitor for actual first PPO and later accepted stages.
[Read-only evidence](spb-random-pre-complete-20260924-013918.json).

## September24 01:28–01:30 Beijing — predecessor passed, actual GPU/SC2 started

Qwen train96+eval96, exact containers and guardians completed successfully.
The existing frozen SpB controller ran both original3415428 verifiers with
write=False before saving predecessor-acceptance at01:22:38. Its single dispatch
start is1790184159.0174987 (01:22:39Beijing); the shared short/long/eval deadline
is1790356959.0174987 (September26 01:22:39Beijing), not an ETA or a resettable clock.
Original SpB5.17B pre is running withclean83f3530/world8/binary64-v1, original
eight evaluation seeds, real NCCL and matching canonical/no-thinking worker
banners. SC2 planner boundaries and a terminal game boundary were observed.
No pre result/.done yet, no PPO or short-stage acceptance; long native CP2
readiness remains deferred. The running empty guardian slot is expected.
The exact owned pre container isb9e8b1a538d7ee08552ac546d405dd351236f76ff9b745cbce0e163e5a579da2.
Latest existing two-root storage receipt is195,029,243bytes/1TiB, measuredexit0,
empty stderr, no failure receipt. No monitor-triggered dispatch or server write.
First GPU/SC2 event is now reported; do not repeat it. First PPO and subsequent
stage completions still require real evidence. Preserve the sole monitor.
[Compact evidence](qwen-random-complete-spb-random-start-20260924.json).

## September23 — explicit full-arm authorization

User replied “是的，接在当前Qwen完整验收通过之后” to the matched full96-step
48wallh/384GPUh/1TiB proposal. This supersedes the earlier budget-pending status
below. New single arm792games/96PPO; original SpB, not any trained weights.
Current Qwen nativeCP8 continuation **train96 AND eval96** must pass the frozen
actual verifier plus host/container/guardian successful terminal checks first.
Its immutable historical `successors_authorized=false` is not rewritten.

New output `/var/jfsCache/sc2-spb-l7random96-197-20260923-r1`, new source
`/var/jfsCache/sc2-spb-l7random96-197-source-20260923-r1/code`; wrapper
`spb_l7_random197.py`, socket `sc2_spb_l7random96_197_20260923_r1`, session
`spb_l7random96_197_r1`. Fresh short and long parts are under `spb-random/`.
Entire output and source roots (including bundle/candidates/CPU artifacts) count
jointly toward1TiB. Existing Qwen budgets/failed artifacts/deadlines unchanged.
First entry expires September25 12:58:40Beijing, one hour after Qwen's original
cutoff; this is an admission cap, not ETA. New48h clock begins first admission
and is shared by short/long/eval, without reset. No GPU reservation while waiting.

Reuses the existing host guardian and current cooperative SC2 startup lease
(concurrency1 until first observation; eight games still parallel, one reset
attempt). Compared with completed SpB same, this operational startup change
accompanies the scientific seed-grouping change; timing equivalence is unproven.
No generation/action/reward/optimizer changes. The only added resume contract
explicitly admits **native SpB random CP2**, requires driver state and rejects
legacy fallback, wrong models or same-seed prefixes. Frozen settings keep
canonical action support, no-thinking, T0.8/192/top-p1/top-k0/gamma1/combat.001,
LR1e-6, same original reference, map/opponent/BO/Executor. Primary comparison:
CP2→CP96 change on the same8paired evaluation seeds, with small-sample caveats.

Entry: `python3 spb_l7_random197.py prepare`; then actual Linux CPU regressions,
host regressions, short/long `cpu-command 0/1`; queue once only after all pass.
The future native CP2 CPU/load gate remains deferred until short actually passes.
Failures stop the new queue, never retry or skip. The existing unique monitor
must cover both Qwen and this successor, without editing active deployments.
Preparation/CPU/queue receipts will be appended after real verification.

## September23 22:56–22:58 Beijing — queue verified

Frozen runtime/controller `83f3530765babe048035524ddf1651291810818a` was committed,
pushed to `CeraveNew/new_SCII`, and remote SHA verified before deployment.
New source is a dissociated clone (no alternates); original source/runs remain
unchanged. One tmux waiting queue started22:56:00;22:58:36 actual queue is
`waiting-predecessor`,completed[], suite/short/long dispatch all absent.
Current Qwen returned47/96, still train96, no final results yet; it has not
passed the successor gate. SpB has no new GPU/SC2/PPO event.

Actual commands on197 (all CPU entries omit GPU requests):

```text
python3 -B experiments/records/20260921-sc2-policy-credit-v1/spb_l7_random197.py prepare
python3 -B experiments/records/20260921-sc2-policy-credit-v1/spb_l7_random197.py host-regressions
python3 -B experiments/records/20260921-sc2-policy-credit-v1/spb_l7_random197.py cpu-command 0
python3 -B experiments/records/20260921-sc2-policy-credit-v1/spb_l7_random197.py cpu-command 1
python3 -B experiments/records/20260921-sc2-policy-credit-v1/spb_l7_random197.py regressions-command 0
```

Each emitted Docker argv was executed once.71host and261model/controller tests
passed, zero skips; CUDA uninitialized. Both actual launcher/Hydra runs (3short,
2long stages) and34/34source hashes passed. Three CPU containers exited0 with
DeviceRequestsnull/OOMfalse. Native futureCP2 validation remains deferred,
`actual_parent_verified=false` for long is deliberate, not GPU acceptance.
Local AST parsing and `shasum -a256 -c configs/system-v1.sha256` also passed.
Local Python lacks OmegaConf; full functional tests ran in the actual Linux
CPU environment rather than being represented as local passes.

Strict two-root GNUdu returned0/no stderr,36,091,338bytes before enqueue,
including staging bundle/script, cloned source, runtime and allCPU products.
Existing monitor `197-qwen-cp8` updated in place to cover Qwen→SpB; no second
monitor, no GPU reservation, no current-run modification or budget reset.
Evidence: [queue, CPU, resolved configuration hashes and current predecessor](spb-random-queue-20260923.json).

## Earlier planning history (preserved)

September22 user requested adding the missing SpB per-game independent-seed
experiment, plus current status/ETA/queue. The new arm is added to the plan;
**training length and added high-cost budget remain pending the explicit
96-step versus short-only choice**. No new server root, preparation, queue or
dispatch has been created. Existing r4 deployments, order and deadlines remain
immutable. This record is within the existing experiment, not a new method.

## Question and proposed matched design

Complete the model-by-seed-grouping comparison: does original SpB under the same
repaired Level7 protocol behave/learn differently with per-game independent
seeds than with step-shared seeds, and how does its change compare with Qwen's?
Only training seed grouping changes relative to the current SpB arm. Keep
no-thinking, canonical action support, top-p1/T0.8/192tokens, gamma1/combat0.001,
LR1e-6, original reference and Executor unchanged. This is **not** a rollback-only
no-thinking on/off ablation. Mixed-seed UID difficulty confounding remains.

Proposed order: existing SpB L7same short+96 → existing Qwen L7random ownCP2→96
→ new SpB L7random. Require complete predecessor terminal verification and actual
successful owned-container exit; failure blocks this addition without retry or
skipping. No duplicate execution of completed Qwen/SpB prefixes/evaluation.

Start from original SpB5.17B, not current same-seed CP or old collapsed weights.
Private Random(0), independent draws0..100with replacement per game; initial
batches49,97,53,5,33,65,62,51 and100,38,61,45,74,27,64,17, matching Qwen random.
Short8pre→2PPO/16training games→8post ownCP2. Only after real acceptance and
native CP2 with driver RNG/SC2 seed state: ownCP2→96/94PPO752games, CP every8,
then8paired zero-update final games. Total792new natural games/96PPO. Use the
same registered8evaluation seeds/rank RNG pairing; no short/pre replay.

Requested confirmation: either full matched96steps, <=48wallh/384GPUh/1TiB
including short/loading/waits/checkpoints/finaleval, or short-only32games,
<=2wallh/16GPUh/128GiB with no automatic long promotion. Full option adds to,
and does not reset, the existing768GPUh/2TiB program. A confirmed full new arm
will have its own fixed first-dispatch48h clock; existing suite cutoffs unchanged.
Exact new admission expiry, unique roots, SHA, effective config and inclusive
accounting paths must be frozen before any dispatch, after the budget choice.

CPU regression and actual launcher/Hydra/source checks are prerequisites, not
GPU acceptance. Reuse host-only strict storage accounting and independent
guardian, exact owned containers/read-only assets, no measurement fallback,
no automatic repair/retry. Eight completely idle GPUs,600GiB RAM,1084GiB NVMe
and fsync required for dispatch. Native SpB random-prefix restoration and seed
grouping must be explicitly tested; existing same-prefix contract is not an
implicit permission to load random or another model's checkpoint.

Primary scientific comparison is paired evaluation change, not training win
rate or mechanically constrained legality. Eight pairs/two-step short tests
have weak statistical power. Model size/FLOPs and Executor attribution remain
limits; no architecture superiority or random-seed improvement is assumed.

Planning-only validation this round: local source/authorization records reviewed;
no runtime code change or new model tests. Budget clarification sent to user.

## September23 22:34 Beijing — actual queue versus plan

User asked what runs next and whether it is queued. Read-only actual deployment
of Qwen native-CP8 continuation r2 confirms only stages `train96`, `eval96` and
`successors_authorized=false`. Current stage remains train96; its own CP96
eight-game zero-update evaluation is already an automatic gated next stage.
No subsequent model experiment is scheduled by this frozen deployment.

This SpB independent-seed arm remains planned only, with its 96-step versus
short-only resource choice still pending. It must start from original SpB,
not same-seed CP96; the short gate belongs inside the proposed full48h/384GPUh/
1TiB maximum. No current run, deadline, deployment, monitoring or queue changed.
The status request itself is not a new high-cost dispatch authorization.
[Actual queue/authorization evidence](next-experiment-queue-status-20260923-223429.json).
Validation: JSON receipt and Git diff checks only; no new model or GPU tests.
