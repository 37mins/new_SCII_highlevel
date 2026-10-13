# Qwen L8 fresh same-seed short + 96

## Completed: September26 16:52 Beijing

[96-step counting and timing clarification](qwen-l8same-step-semantics-20260926-1729.json),
checked17:29 Beijing: this was96outer online-RL collect-and-PPO iterations,
not a96-minibatch-only job or an evaluation-only job. Each iteration collected
8natural games; multiple consumed Planner decisions per game formed rows for
PPO minibatches. Actual train2/long effective configs use rollout8, global
decision-row mini-batch8, per-GPU micro-batch1, world8, maxresponse192 and
total target2/96. Frozen defaults and actual resolved training config confirm
ppo_epochs1, lora_rank0 and dynamic batchingfalse. One PPO epoch traverses
each collected decision batch once; it does not mean one update for the whole
run. A global step is not necessarily one underlying AdamW.step call. The
frozen trainer collects before update_actor and only increments global step
after the returned actor update and metrics.96iterations means768training
games, not96passes over a large fixed dataset. "Long" is relative to the
two-iteration acceptance run, not a promise of convergence or days of compute.

All96recorded outer-step timers sum22,397.48seconds (6h13m17s),mean233.31s:
collection/game interaction+generation190.34s, actor-update26.76s perstep;
other work includes log probabilities/reference/checkpointing. Eight games
run concurrently after the startup lease, not768games one after another.
The long3..96 container ran10:37:54–16:46:15 (6h8m21s), including loading and
shutdown, separately from the earlier two-step prefix. The16:46–16:52 segment
was only final8-game evaluation. Timer sums are not the whole wall-clock span:
first dispatch01:42–completion16:52 also includes the historical verifier
failure/wait and approved continuation.48hours is a hard ceiling, not a
required training duration. The old L7 Qwen timing receipt has the same PPO
minibatch/epoch settings; L8 is not demonstrated faster than those Qwen runs.
No change of training budget, seed mode, PPO epochs or runtime was made here.
Read-only config/metric assertions and source-code inspection passed; small
source hashes and timing aggregates are saved, not full logs or checkpoints.

[Read-only terminal receipt](qwen-l8same-complete-20260926-1654.json), checked
at16:54:58 Beijing, supersedes the running/ETA snapshots below. Queue, long
host supervision and long state are completed/exit0. All five stages have
matching result/.done/acceptance results, finite binary64 metrics and exit0.
The exact train96 and eval96 owned containers and their guardians completed
with exit0, no OOM/Error. No server writes or new experiment were performed.

Training completed96actual PPO updates: retained steps1..2 have16natural
games/8wins; native ownCP2 continuation3..96 has752games/433wins. Total
441/768wins (57.42%), zero truncation,5938/5938consumed answers valid. All96
metric rows have positive finite gradients and positive update_actor time,
validratio1 and invalidAdvMax<=0. CP2 and CP8..96 (every8steps) each contain
the26required nonempty files; this query checked names/sizes, not weight bytes.
Training is changing-scenario data, not a held-out estimate or768independent
trials: each step shares its scenario seed across8games.

Train96 result ended16:45:58; eval96 started16:46:34, ended16:52:09, and host
queue finished16:52:10. OwnCP96 actual load returned atglobal96, zero updates;
8natural evaluation games/5wins/3defeats,63/63consumed answers valid. All8rank
model-sampling seeds and CPU/CUDA RNG hashes match ownCP2 post. Scenario seeds
are the original8evaluation seeds; rank sampling seeds0..7 are distinct from
those scenario seeds. Original pre6/8 -> CP2post5/8 -> CP96eval5/8. Relative
to CP2,2previous defeats became wins and2wins became defeats: no net gain.
These8reused pairs do not demonstrate learning improvement, generalized
deterioration or architecture advantage. Technical acceptance is complete;
learning_validated remains false. No unpaired training/eval comparison is
used to infer improvement, and no IID confidence interval is asserted for
the correlated training games.

The full approved group contains792natural games:768training +24evaluation.
Strict four-root final storage650,422,838,238bytes (~605.75GiB)/1TiB,return0,
empty stderr. The original September28 01:42:02.741755 hard deadline and all
budgets were unchanged; completion is early, not a budget reset. Runtime
`eef0f049bb09b7a51188ae67a6c35436a3bf055f`, controller
`db60d075879750cabf30a38c555d1c3aaaf104c1` remain frozen. The historical r1
host-verifier failure remains failed/read-only; accepted pre/train2 were
retained without replay, not retrospectively relabeled as a successful r1.
The loader's legacy text "online SpB" is not model identity: this is Qwen.

Validation: read-only small terminal/acceptance/metric/RNG reads, exact owned
Docker state checks and filename-only checkpoint inventory assertions passed;
source byte lengths/hashes are in the receipt. No full-console read, large
checkpoint read, repeated full verifier, GPU diagnostic, launch or restart.
This status turn does not authorize a next experiment or document publication.

## Read-only progress: September26 15:23 Beijing

[Progress receipt](qwen-l8same-progress-20260926-1523.json): returned77/96
(80.2%),currently dispatched78; advanced38steps since12:49. Exact owned
train96 container is running,no OOM/Error/restart/persistent pause; queue/host
remain running-unverified. Latest2MiB console contains returned76..77 only:
both finite positive gradient/update_actor,validratio1,invalidAdvMax0. This
checks two recent rows,not a full-history gradient acceptance. Their mean
full-step time328.48seconds,versus approximately244seconds/update over the
38-step elapsed interval. Remaining19updates plus checkpoints/acceptance and
8-game eval96 give a provisional September26 17:00–18:00 Beijing finish;
not guaranteed. The original September28 01:42 hard cutoff is unchanged.

All suffix resets2..76 match privateRandom0/same_uniform101; each completed
batch has8distinct envindices/natural termination/no truncation. Including
retained1..2:616training games/348wins (56.49%); recent8steps26/64 (40.63%).
These are changing-scenario training observations,not held-out evaluation.
CP8..72 every8steps each have35nonempty files; filename/size check only,no
large checkpoint read or repeated26-file full acceptance. Strict four-root
storage500,438,367,201bytes (~466.07GiB)/1TiB,return0/empty stderr,sample
12.42seconds old and verified resumed. No new failure receipts observed.
No train96/eval96 result/.done observed. Small-record/2MiB-tail/exact-owner
read-only checks and batch/seed/metric consistency assertions passed; no
server writes,new launch,restart,or budget change. Git diff check passed.

## Read-only health: September26 12:49 Beijing

[Health receipt](qwen-l8same-health-20260926-1249.json): execution is progressing,
returned39/96,dispatch40,up5steps since12:25. Exact owned train96 container is
running/not paused/not restarting,no OOM/Error. Queue/host are running-unverified;
the running guardian's empty terminal slot is normal,not a failure.
Latest5returned steps35..39 have finite positive gradient0.05796..5.04256,
positive update_actor23.29..35.66seconds,validratio1,invalidAdvMax0. Mean full
step time241.05seconds. All suffix resets2..38 match same_uniform101; each
completed batch has8 distinct envindices/natural termination/no truncation.
Including retained prefix,184/312training wins (58.97%); latest8steps47/64
(73.44%). These fluctuating training observations do not establish learning.

Strict four-root storage sample is1.61seconds old:250,306,789,604bytes
(233.12GiB)/1TiB,return0/empty stderr,measured with verified unpause. No new
failure receipt in the newroot,longowner,or host-supervision directories.
CP8/16/24/32 directories each have35nonempty files; only filenames/sizes
checked,no large checkpoint read or full required26-file reacceptance.
Train/eval result/.done/acceptance remain pending. Read-only inspection of
small records,2MiB console tail,and exact Docker state; assertions on owner,
seed/batch integrity and outcome-to-metric agreement passed. No GPU diagnostic,
server write,restart,dispatch,configuration change or budget extension.
This is a time-sensitive execution-health check,not final scientific acceptance.

## Partial training curve: September26 12:25 Beijing

[Plot snapshot](qwen-l8same-curve-20260926-1225-data.json) contains exactly
34 contiguous completed training batches: 272 natural games/153 wins (56.25%).
Recent8steps27..34:24/64wins (37.5%). Queue/host still train96 running-unverified;
this is not final acceptance or CP96 evaluation. Blue points show each8-game
batch; orange dashed line is the trailing8-step arithmetic mean, first shown
atstep8. The purple boundary is afterstep2. Steps1..2 retain the accepted r1
train2 prefix;3..34 are its nativeCP2 continuation,not repeated games. The old
r1 host-verifier failure remains unchanged. No future points or evaluation
games are included. Same-seed batches share scenario difficulty; a0% training
point means0/8wins,not zero answer validity,and this changing-scenario curve
does not establish learning improvement or deterioration.

Collection: [read-only collector](collect-l8same-curve.py), run as
`ssh -o BatchMode=yes -o ConnectTimeout=12 sc2-a100-197 'python3 -' < collect-l8same-curve.py`
from this record directory. It read small outcome/seed ledgers plus the final
2MiB of console; no checkpoint/full-console read or remote write. Each batch
has8 unique envindices,natural termination/no truncation; all34same seeds match
privateRandom0. Prefix1..2 and returned tail28..34 win rates match actual PPO
metrics. Latest returned34 bounds the plotted ledger; future dispatched games
are excluded. The seven returned tail rows have positive finite gradient and
update duration,validratio1,invalidAdvMax0; this is not a full34-step gradient
audit. Small source-file hashes,byte lengths,and console byte range are saved.

Render: `node plot-l8same-curve.mjs qwen-l8same-curve-20260926-1225-data.json OUTPUT.png`
uses the bundled Node/sharp runtime and [plot script](plot-l8same-curve.mjs).
PNG: `/Users/yangjinyue/.codex/visualizations/2026/09/03/01a06605-4e2f-7052-925a-e3bf70ef2b4b/qwen-l8same-curve-20260926-1225.png`,
SHA256`0eee15e5f6feede9c5d1cefcdc692a198600b9c2d618c188a38bea4148d81af2`.
The data/collector/plot script are versioned; PNG/SVG are local presentation
outputs. Actual collector assertions and renderer validation passed; rendered
PNG was visually inspected for correct labels/no clipping. Syntax checks and
`git diff --check` passed. Runtime`eef0f04`/controller`db60d07`,original budget
and fixed deadline unchanged. No experiment launch/restart or server edit.

## Read-only progress: September26 11:43 Beijing

[Small status receipt](qwen-l8same-status-20260926-1143.json): train96 is still
running in the exact owned container,no new failure observed. Returnedglobal22,
reset22/global23 dispatched. Suffix3..22 has20updates/160natural games/99wins,
zero truncation; retained1..2 adds16games/8wins. This is not held-out evaluation.
Bounded last2MiB console tail shows returned18..22,all finite positive gradient
and update_actor duration,valid_action_ratio1,invalidAdvMax0. Recent5steps mean
202.972665seconds. CP8/16 directories each contain35nonempty files; required26
inventory not revalidated in this query. Full train result/acceptance and final
eval remain pending. Strict four-root storage150,237,380,953bytes (~139.92GiB)
/1TiB,return0/empty stderr. Updated provisional finish including final eval:
September26 16:00–18:00 Beijing (~4–6h remaining),not a guarantee or learning
claim. Original hard cutoff September28 01:42 remains unchanged. No remote writes.

## Read-only ETA snapshot: September26 10:57 Beijing

[Small ETA receipt](qwen-l8same-eta-20260926-1057.json): long container still
running with original owner/deadline. Bounded console tail shows returned
global6,binary64,grad283.92100747426349,update_actor20.608157953247428sec,
invalidAdvMax0,step248.29280638601631sec;reset6 dispatchedglobal7.
Running metrics.json is not finalized yet, not evidence of zero updates.
Provisional completion including checkpoints/acceptance/eval96: September26
17:00–19:00 Beijing (roughly6–8hours remaining). Latest-step90remainingsteps
is about6.21hours; variability and final work widen the range. Few measured
steps make this an early estimate, not a guarantee. The hard deadline remains
September28 01:42:02.741755 and is not the ETA. No server writes or dispatch.

## Native long actually running: September26 10:40 Beijing

[Transition receipt](qwen-l8same-native-long-start-20260926.json): post completed
at10:37:35,8natural games/5wins,29/29valid consumed answers,0updates,finite
binary64 metrics,result=.done=acceptance and correct guardian/containerexit0.
The verifier checked ownCP2 actual load and paired8rank CPU/CUDA RNG with pre.
Original pre6/8→post5/8 is descriptive only, not proof of improvement/decline.

The complete accepted-qwen-l8-same-full-state-prefix-v1 contract and actual
native parent-readiness passed before long. Accurate new train96 container
`91d0dbd99c166ea114df62af0e3d07ec3aa94cf3f59f5d4a86ea43d6ff4d986b`
started10:37:54.320353,owner newr2/qwen-same/long,eightGPUs. Clean unchanged
runtime`eef0f04`,world8,binary64-v1; real model/optimizer/dataloader load
returned from ownCP2 withglobal2/reset2,next53×8,source=checkpoint. No legacy
fallback or repeatedprefix. At10:40 this is running-unverified,not a completed
PPO return or final96-step acceptance. Subsequent eval96 remains conditional
on full training acceptance. Four-root storage50,028,662,403bytes/1TiB,
return0/empty stderr; original deadline remains unchanged.

## Actual controlled continuation r2 (September26 10:35 Beijing)

[Launch receipt](qwen-l8same-continuation-launch-20260926.json): frozen controller
`db60d075879750cabf30a38c555d1c3aaaf104c1` was pushed and independently verified
with an exact-SHA dry run showing up-to-date before dispatch. One initial
TLS transport failure was resolved without disabling certificate checking.
Actual Linux328container+71host tests passed/zero skips/noCUDA, all3remaining
launcher/Hydra configs/34hashes and actual post/train96/eval96 Ray hooks passed.
Seven CPU containers exited0 with no GPU requests. Retained pre/train2 full
acceptance and native small-stateCP2 checks passed; next reset2 is53×8.

One resumed GPU dispatch at10:32:11.232839 retains the original clock.
Eight unique CUDA UUIDs/NCCL sum28 preflight exited0, then exact post container
`4873e0440e2659494bf293252ca554efd2eefe7c14f31d4a48224c5244e40d21` started
10:32:58.433491 under the new short owner. At10:35 actual ownCP2 load returned,
world8/clean`eef0f04`/binary64-v1/Qwen manifest, canonical tokenizer/mask,
original8eval seeds and SC2 in_game/planner were observed. Zero updates;
post result/.done not yet present. No new PPO or completed long is claimed.
The loader receipt's legacy text "online SpB" is not model identity; the
Qwen manifest, launcher, assets and revision are authoritative.

Latest strict four-root sample50,000,258,269bytes/1TiB,return0/empty stderr;
no failure observed. Host queue owns subsequent post→long→eval sequencing,
and native parent acceptance still gates long. No desktop monitor was added.
The approved continuation and its constraints are detailed below.

User explicitly permits corrected acceptance, complete CP2 verification, and
continuation within the original budget without repeating the completed24
games. `qwen_l8same_continue197.py` uses a new r2 source/controller/output;
the model runtime remains exactly `eef0f049bb09b7a51188ae67a6c35436a3bf055f`.
No model, optimizer, generation, seed, reward or training semantics change.
Training replay validation now checks the actual16/752 natural L8 replay
files; evaluation still checks its recorded SHA256 inventory. Missing,
empty, duplicate, escaped or wrong-level replay files fail closed. The old
r1 failure and missing acceptance are never overwritten.

New output `/var/jfsCache/sc2-qwen-l8same96-197-20260926-r2`, source parent
`/var/jfsCache/sc2-qwen-l8same96-197-source-20260926-r2`. These whole roots
plus both original r1 roots share the unchanged1TiB quota, including bundles
and CPU artifacts. Every stage inherits start1790358122.7417548 and deadline
1790530922.7417548 (September28 01:42:02.741755 Beijing),384GPUh/48wallh,
45second cleanup reserve. No new clock, deletion, automatic retry or extra arm.

Retain original pre8/train2 16games/2PPO via read-only aliases and verify their
exact terminal owners, guardians, result=.done, full metrics/action evidence,
seed ledgers, replay files and26-file CP2 inventory. Only new owner receives
corrected acceptance receipts. No-GPU CP2 readiness checks native driver,
environment, all8rank Python/NumPy/CPU/CUDA RNG, scheduler and dataloader
small states. Large model/optimizer shards are not read by this CPU check;
their actual GPU loading must return in the real stages.

Execute only post8zero → nativeCP2 steps3..96 (752games/94PPO) → eval96eight
zero. New total768games/94PPO, combined with retained prefix792games/96PPO.
Post acceptance completes the composite short contract; host-supervision
truthfully lists only new post. The accepted-qwen-l8-same-full-state-prefix-v1
contract and actual parent CPU gate remain mandatory before long; no legacy
fallback. Exact new containers have prefix`sc2-qwen-l8same96-197-20260926-r2-`.
Original roots/runtime are mounted read-only; only new selected part/tmp/lock
are writable. Admission still requires8idle GPUs/no computePID,600GiB RAM,
1084GiB free NVMe before training/probe and128GiB before post/eval,fsync.

Before dispatch: actual Linux no-CUDA regressions, all3 remaining launchers/
Hydra configs and34source hashes, and actual post/train96/eval96 Ray CPU
hooks must pass. Then one8UUID/NCCL zero-model/zero-game GPU preflight uses
the real post runtime environment. Any failure blocks all successors.
Local115 regression tests passed with zero skips; this is not remote/GPU
evidence. CLI: prepare, host-regressions, cpu-command0/1, regressions-command0,
prefix-cpu-command0, cpu-hook-command0post/1train96/1eval96, verify-retained,
then one queue. Source must be committed and remotely archived first.

## Latest read-only status: September26 10:00–10:02 Beijing

**Failed at train2 acceptance; post and long training did not start.**
[Small failure receipt](qwen-l8same-status-20260926-1000.json) records the
01:59:45 host fail-close and exact traceback in frozen `eef0f04`:
`qwen_l8same_fresh197.py:188` reads `result['replays']` unconditionally.
`scripts/run_record.py` emits that field for evaluation, not training. The
base verifier returned before this extra L8 check raised. This is a controller
schema bug, not GPU OOM or model-training failure; the synthetic/CPU tests
did not cover this real training-result schema.

Pre completed and was accepted:8natural games/6wins,48/48 consumed answers
valid,0updates,container/guardian exit0. Train2 completed at01:59:25 and its
container exited0 at01:59:42. Two actual returned metrics rows and two accepted
pre-update audits are present,16natural games/8wins,no truncation; consumed
audit answers61/61 and35/35. Gradients4.9503163658082485 and3.733105216745753;
update_actor28.032791825942695s and17.048331038095057s; invalidAdvMax0 for both.
Seeds49×8 then97×8 match same_uniform101. Training result equals.done and
lists26required CP2 files, including sc2_state and eight rank states; sixteen
actual CheatVision replay paths exist. No large checkpoint was read this turn.
CP2 existence is not full continuation acceptance: train2 acceptance and
post are absent, and native load/RNG readiness must still pass before long.

The current10:02 GPU query reports eight cards0MiB/0% and no computePID.
The last controller storage sample is from01:59:45 (49,973,479,244bytes,
strict return0/empty stderr), not a fresh10:02 disk measurement. No remote
file edits, restart, deletion or automatic retry were performed. The original
deadline stays September28 01:42:02.741755; the initial5–10h ETA is invalid
while stopped. Proposed next work requires a corrected frozen verifier plus
regression test and explicitly approved controlled continuation; do not
rewrite failed r1 or repeat its completed games by default.

## Historical launch status

September26 01:45:16 Beijing: dispatched once; pre running, no PPO observed yet.
User explicitly selected original Qwen and the budget below. The prior L8
pilot's accepted32 games and r1–r6 failures remain; remaining64 evaluation
games are not queued.

## Actual launch

[Compact launch receipt](qwen-l8same-fresh-launch-20260926.json) records frozen
runtime `eef0f049bb09b7a51188ae67a6c35436a3bf055f`, independently verified on
GitHub before deployment. Real Linux container319 + host71 tests passed with
zero skips, all five launcher/Hydra configs and34source hashes passed, and
pre/train2/train96 each passed its actual no-GPU Ray worker hook. All six CPU
containers exited0 without GPU device requests. These are not PPO evidence.

One GPU dispatch at **2026-09-26 01:42:02.741755 Beijing** starts the common
48h clock; fixed deadline **2026-09-28 01:42:02.741755 Beijing** (45sec cleanup
reserve). The eight-distinct-CUDA-UUID/NCCL preflight exited0; each rank saw
allreduce sum28, with no model, games or optimizer updates. Formal pre
container `12382dde8901da405f082342eed2cccacbc6dd570fa14e82818c030b5575cd24`
started01:42:34.533154, with exact short owner, all GPUs, clean pinned manifest,
world8/binary64-v1 and the original4.02B Qwen model. Canonical tokenizer and
no-thinking support-mask banners matched. At01:45:16 the bounded console tail
showed actual SC2 build actions and a planner reward boundary (game_loop2312,
last_consumed_policy_action_id1); this is game activity, not a PPO return.

Queue is running-unverified in `qwen-same/short`. No stage completion or PPO
is claimed. The controller will proceed through the five stages only after
each predecessor's full acceptance. Latest strict two-root storage sample
at01:44:05 was50,384,164bytes/1TiB, return0/empty stderr, no failure. Initial
SCP/SSH transport interruptions were checked before successful transfers and
queue submission; no duplicate dispatch occurred. No old data was deleted.
No additional desktop monitoring automation was created; automatic stage
sequencing is owned by this server queue.

## Question and protocol

Can the accepted RL protocol produce complete auditable updates on L8, and
what descriptive change occurs on eight paired evaluation seeds? Start at
released Qwen3-4B-Instruct-2507 revision cdbee75f17c01a7cc42f958dc650907174af0554,
not L7 CP96 or old CP2. Reuse this record/branch. Relative to completed fresh
L7 same, task change is VeryHard→CheatVision (L8); deferred low-port rendezvous
and matching-env preflights are operational changes, not bitwise equivalence.
The frozen SHA, model/image/map/BO identities and complete effective configs
are recorded by preparation and the actual launchers before admission.

Flat128/Base75689/Terran Air/canonicalBO; same_uniform101 private Random(0)
draws one integer0..100 with replacement per step, replicated8times. All96
reset entries checked. Eight games parallel after serial startup lease until
first observation; concurrency1/retries1. T0.8/max192/top-p1/top-k0/gamma1,
combat0.001/LR1e-6 constant/zero warmup. Same canonical action support and
no-thinking; post-centering invalid penalty0.1/consumed-valid gate0.5.
No D+/resampling/early-stop. Mixed-seed arm is not included.

pre8zero → fresh train2(16games/2PPO) → ownCP2 post8zero → own nativeCP2 to96
(752games/94PPO) → ownCP96 eval8zero. Total792games:768training+24evaluation,
96actual returned PPO. Five independent stage containers. Full short
acceptance, explicit accepted-qwen-l8-same-full-state-prefix-v1 contract,
native driver/rank RNG/sc2_state and actual parent readiness precede long.
The new L8 contract only accepts CheatVision; old L7 contracts still require
VeryHard. No legacy fallback. CP2 and8..96:13sets,26required files each.

Evaluation seeds605183188,1075501356,2084414326,2203880230,3000371298,
949752300,3225036469,2823708076 and all8rank CPU/CUDA RNG are paired.
Technical acceptance: result=.done/acceptance, exit0, clean SHA/world8/binary64,
exact natural games/L8 replays, real loads,96returnedPPO+audits, finite positive
gradient/update_actor time,invalidAdv<=0,100%legal consumed answers/no-thinking,
real validated plan→queue→local Depot/Marine commands.
Descriptive metrics: winrate/reward/validity/gradient and paired pre/post/eval.
Report Wilson intervals/exact paired outcomes on completion. Eight reused
pairs, high legality and nonzero gradients do not establish generalization,
strategy learning or architecture advantage.

## Budget and gates

197/eight GPUs only, serial. One48wallh/384GPUh absolute clock from first GPU
dispatch includes preflight/loading/CP/waits/all stages,45sec cleanup reserve.
Admission expires4h after preparation; waiting holds no GPU. Provisional
5–10h estimate from L7, not measured L8 ETA or hard deadline.
Output `/var/jfsCache/sc2-qwen-l8same96-197-20260926-r1` and entire source parent
`/var/jfsCache/sc2-qwen-l8same96-197-source-20260926-r1` jointly limited1TiB,
including bundle/CPU/preparation/logs/checkpoints. Strict GNUdu with no filtering,
retry, exclusions, fallback or unknown-as-zero. Old roots/weights untouched.
Readonly models/dependencies/source; writes only selectedpart/tmp/stablelock.
Host sampler/guardian use unchanged clock and exact owned containers.

Every admission:8idle GPUs/no computePID,600GiB RAM,fsync/readback. Initial,
preflight and training require1084GiB free NVMe; post/eval96 require128GiB as
they write no checkpoint. New queue only; old gates unchanged,1TiB hard quota
still enforced. Any failure blocks successors; no automatic retry/deletion/
new arm/extension. Independent Git object copies avoid old shared-clone chains.

Five actual CPU launcher/Hydra configs, source manifest and zero-skip tests
must pass. Real no-GPU Ray hooks for pre/train2/train96 inherit full actual
runtime_env except short isolated tmp paths. Then one zero-model/zero-game
eight-distinct-CUDA-UUID/NCCL preflight must pass before games. Probe task and
actor retries disabled; CPU or preflight pass is not SC2/PPO evidence.

Entry `qwen_l8same_fresh197.py`: prepare, host-regressions, cpu-command0/1,
regressions-command0, cpu-hook-command0pre/0train2/1train96, then one queue
in dedicated tmux. `-command` entries emit Docker argv without executing it.

Local preparation validation:106 synthetic tests passed/zero skips with
`PYTHONPATH=/private/tmp/sc2-qwen-native-testdeps-20260924:tests:scripts:. python3 -B -m unittest -q test_qwen_l8same_fresh197 test_qwen_l7same_fresh197 test_qwen_l8_probe_env test_sc2_policy_resume test_l7_followup197 test_spb_l7_random197 test_qwen_l8_remainder3_197`.
All34`configs/system-v1.sha256` hashes and`git diff --check` passed. These are
not real Linux Ray/GPU results. At01:17:17Beijing197 had8idle GPUs/0computePID,
759GiB RAM available/1257GiB NVMe free; existing unrelated containers untouched.
