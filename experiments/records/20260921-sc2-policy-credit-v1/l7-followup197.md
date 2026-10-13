# Approved Level7 follow-up queue — September22

New r3 status19:06:42Beijing: predecessor CP96-only eval fully accepted,
SpBsame short/pre singly dispatched19:06:02. Arm short+long deadline
1790247962.305692, suite1790420762.305692, never reset. Qwen random pending.
[New terminal/dispatch evidence](l7-eval-complete-spb-start-20260922.json).
The old r2 failure below remains immutable; it was not restarted.
19:08:09 actual original SpB5.17B worker/required support banners/freshstep0
and SC2 start verified; pre running, no PPO yet. First GPU/SC2 notified.
[SpB actual snapshot](l7-spb-first-gpu-20260922.json).

Original r2 status: **failed at predecessor gate**, September22 17:15Beijing;
no suite/part GPU dispatch. Failed deployment remains frozen and must not restart.
The user subsequently approved a [new r3 replacement](metric-precision-fix.md)
with a new CP96-only final-eval predecessor contract, explicitly accepting the
old six-gradient evidence gap but not marking old training accepted. r3 was
singly queued19:00:01Beijing;19:02:35waiting-predecessor,completed[], no part
dispatched. Old r1/r2 roots remain failed/retained and are included in budgets.
[New launch/CPU evidence](l7-continuation-launch-20260922.json).

Earlier snapshot: **queued once September22 15:14:50Beijing, waiting-predecessor**.
At15:16:32, suite and all three part dispatches were absent; completed list empty.
Current Qwen was still training, actual console PPOstep55/96. No new GPU launch.
[Queue and CPU evidence](l7-followup-queue-20260922.json).
User explicitly accepted the proposed sequence, budgets and Qwen legacy RNG
limitation. Current Qwen deployment and deadline are unchanged.

## Sequence and matched protocol

1. Wait for current Qwen same96 root `/var/jfsCache/sc2-qwen-l7same96-197-20260922-r1`
   to complete train96/eval96, successful host queue/container exit, and its
   original actual terminal verifier. Failure blocks both new arms.
2. Original SpB5.17B Level7 VeryHard: pre8 → fresh train2/16games → post8 ownCP2;
   after actual acceptance, ownCP2→96/94updates752games → paired eval96/8games.
   **792 new games/96 updates**. No old Level6 or collapsed L7 weights.
3. Qwen3-4B-Instruct-2507 Level7 random: accepted r4/l7-random ownCP2→96,
   then paired eval96. **760 new games/94 updates**; never replay its32-game
   prefix. Missing driver RNG accepted: ledger-restored SC2 counters plus native
   worker RNG/model/Adam/scheduler/dataloader, not bitwise continuation.

SpB lacks an accepted Level7 prefix, hence its short gate. Its newCP2 must have
native `sc2_state.pt`/driver RNG; no legacy fallback. Each model's total training
effort is96×8=768games including Qwen's retained16traininggames. Step96 is a
matched budget, not an algorithmic requirement. No extra SpB random arm.

Same repaired method: Flat128/Base75689/Terran Air/canonicalBO, T.8/192tokens/
top-p1/top-k0/gamma1/combat.001/LR1e-6 constant/zero warmup, canonical action
support, no-thinking shared support, post-centering invalid credit, .5 real
consumed-validity PPO floor. No D+, resampling or early-stop. Original references.
Pinned image, SpB original5.17B asset and dependency/environment provenance
inherited from accepted SpBr4; Qwen from accepted r4/l7-random, verified12files,
revision cdbee75f17c01a7cc42f958dc650907174af0554. Assets read-only, no transfers.
Tokenizer/mask hashes unchanged; exact host/config inheritance in deployment.

Seeds: private PythonRandom0,0..100with replacement. Same49×8,97×8,53×8…;
random49,97,53,5,33,65,62,51 then100,38,61,45,74,27,64,17; continuation starts
reset_index2. Existing mixed-seed UID exception is explicit ablation only;
scenario difficulty still confounds group advantage. Eight eval seeds/rank RNGs
match each own post-prefix. Primary comparison is paired zero-update wins,
reporting paired outcomes/exact sign uncertainty, not training win rate.
Eight pairs are weak evidence. Constrained legality, nonzero gradients or wins
do not establish strategy learning or architecture superiority. SpB5.17B versus
Qwen4B and unequal FLOPs remain explicit limits despite equal interactions.

## One-shot budget and provenance

Each new model arm <=48wallh/384GPUh/1TiB. SpB clock includes short, loading,
native-prefix CPU gate, gaps, checkpoints and eval; long stage never resets it.
Qwen48h starts at its GPU dispatch. Suite96h starts at first SpB GPU dispatch
and includes subsequent waiting, with45s cleanup reserve. No reset/retry.
First admission expiry: existing Qwen deadline+1h, **Sep24 14:18:46Beijing**
(1790230726.5133374), not ETA. Total1552newgames190updates; no extra experiments.

Suite `/var/jfsCache/sc2-l7-followup197-20260922-r2`; source
`/var/jfsCache/sc2-l7-followup197-source-20260922-r2/code`.
Parts `spb-same/short`, `spb-same/long`, `qwen-random/long`.
Launcher `l7_followup197.py`; runtime/controller SHA frozen in deployment;
orchestration9a7b0faca5b145a891ad211f189121e4949f0eab.
SpB1TiB counts whole spb-same+source root; Qwen1TiB counts whole qwen-random+
source+retained r4/l7-random. Suite2TiB counts whole suite+source+retained random
parent, including all candidate/preparation residuals. Strict coordinated GNUdu,
measurement errors unknown not0, no exclusions/retries/cached substitutions.
Each dispatch requires8idle/unowned GPUs/no compute PIDs,600GiB RAM,
1084GiB local free, fsync/readback. Waiting does not reserve cards or stop others.
Any failure stops successors, preserves evidence and requests direction.
Historical Docker-stop client timeout is not claimed fixed.

## Verification

Additive accepted-prefix contracts permit only Qwen independent legacy prefix
(accepted missing driver RNG) and SpB same native-state prefix. Historical Qwen
same contract unchanged. All effective training protocol fields must match the
parent except narrowly defined relocation/length/restore controls. No policy,
action,reward or optimizer algorithm changes. Same method branch/record reused
under AGENTS6.2; this is not a new major method.

Before enqueue: full Linux real-tokenizer/worker CPU suite zero skips; all7
actual DRY_RUN/Hydra/source-manifest gates; CUDA uninitialized. SpB long's
initial CPU gate is **conditional** on future CP2. After actual short acceptance,
separate CPU native-prefix validation must pass before its long GPU dispatch.
It cannot fabricate future receipts or overwrite initial CPU evidence.

Every actual stage: result=.done/exit0/cleanSHA/world8/finite/natural games;
100%valid consumed answers/no-thinking output/worker support hashes;
validated plan→queue→local Depot/Marine commands. Long training94actual PPO
metrics/audits, positive finite gradients/invalid advantage<=0, CP8..96 each26
files, exact reset_indices2..95 and actual own-prefix load. Final ownCP96load,
8paired seeds/rank RNG,0updates. Pre-update audits alone are not completed PPO.

Entry: `prepare` once; `cpu-command 0/1/2`, `regressions-command 0` emit CPU-only
Docker commands; `queue` once under dedicated tmux after verified receipts.
Existing monitor updated in place, not duplicated. Each round commits/pushes
small evidence to GitHub; large weights/checkpoints/logs never enter Git.

## CPU preparation boundary

Candidate ba11e835 passed189Linux CPU tests,0skips/CUDAfalse. Its r1 preparation
then passed SpB short DRY/Hydra but correctly rejected short/long normalization:
the unchanged SpB launcher creates each stage's `OUTPUT_DIR/model` view, so the
three resolved model/tokenizer paths legitimately relocate. No queue/dispatch
or GPU work occurred. r1 source/output are retained untouched and included in
every new1TiB/2TiB measurement, not discarded or reclassified as a GPU retry.
The r2 candidate normalizes only exactly output-derived model views; arbitrary
asset-path changes still fail. Original weights and model-preparation logic are
unchanged, and actual launchers verify the registered source asset manifest.

Final runtime/controller `e95b9cb425e1d25c4c2c006bb674fb66e8f6dc95`: all190Linux
CPU regressions passed, zero skips/CUDAfalse; all7 actual DRY_RUN/Hydra configs
and32source hashes passed. Four CPU containers exited0 with DeviceRequestsnull.
Qwen random's actual small CP/ledger restored nextreset2, next seeds
36,17,96,12,79,32,68,90. SpB future native CP2 gate remains mandatory/deferred.
Socket `sc2_l7_followup197_20260922_r2`, session `l7_followup197_r2`; queue must
not be dispatched again. Code push and remote SHA equality verified before queue.

Monitor `197-qwen-l7-seed96` was updated in place to the full serial queue,
still ACTIVE every10minutes, no duplicate. It remains quiet on healthy progress,
reports actual first GPU/PPO events for new arms, stage completion or failures,
and is removed only after the whole authorized chain completes or a terminal
failure is handed off without further authority. Following the OpenAI Docs
[in-chat scheduled-task guidance](https://learn.chatgpt.com/docs/automations),
its saved prompt specifies durable scope, decision gates and stopping conditions.
AGENTS6.4 per-round small-evidence commit/push/remote-SHA checks are included.

## Quiet monitor — September22 15:37:53Beijing

[Read-only snapshot](l7-followup-heartbeat-20260922-153753.json): original Qwen
returned PPO through62/96; step63 has only a before-update gate, not completion.
Owned container and both dedicated tmux sessions are live; train/eval terminal
results absent. CP8/16/24/32/40/48/56 each have26required nonempty files by stat.
The existing exact-three-root storage receipt measures400,304,825,661bytes,
exit0/no stderr; no failure receipt. Original deadline unchanged.
Follow-up remains waiting-predecessor/completed[], no suite or part dispatch.
No new stage/event/failure/decision: keep the existing monitor, do not notify.
Only small JSON/stat receipts and a2MiB console tail were read; no large CP,
GPU diagnostics, launch/retry, frozen edit or budget change. JSON/metric/CP/
deadline assertions and local diff checks passed; no model tests were run.
Archive this heartbeat on the same branch and verify the pushed remote SHA.

## Quiet monitor — September22 15:52:30Beijing

[Snapshot](l7-followup-heartbeat-20260922-155230.json): actual returned PPO68/96;
step69 remains pre-update only. CP8..64 every8steps each26required nonempty
files by stat. Exact-three-root storage450,263,282,896bytes/exit0/no stderr;
no storage failure, terminal results or changed deadline. Current container and
both dedicated tmux sessions live. Follow-up still waiting-predecessor, zero
new dispatches. Healthy progress stays silent; same monitor retained. Small
receipt/2MiB log-tail, finite-PPO/CP/clock/queue checks passed; no model tests,
GPU diagnostics or remote mutations. Per-round GitHub evidence sync required.

## Quiet monitor — September22 16:26:19Beijing

[Snapshot](l7-followup-heartbeat-20260922-162619.json): actual returned PPO81/96;
train96 continues without terminal train/eval results. CP8..80 every8steps each
have26required nonempty files by stat, including sc2_state.pt. Exact-three-root
storage550,206,319,914bytes/exit0/no stderr; no storage failure and deadline
unchanged. Owned container and both dedicated tmux sessions remain live.
Follow-up is waiting-predecessor, no suite/part dispatch or new GPU container.
Recent console PPO80/81 has finite positive gradients and valid-answer ratio1;
these rounded training metrics do not establish strategic learning. No new
stage completion/failure/decision, so keep monitoring silently. Small receipt/
2MiB tail, runtime/clock/finite-PPO/CP/queue checks passed; no model tests or
remote mutations. Save on the original branch and verify GitHub remote SHA.

## Quiet monitor — September22 16:41:22Beijing

[Snapshot](l7-followup-heartbeat-20260922-164122.json): returned PPO88/96;
CP8..88 each26required nonempty files by stat. Current container and both tmux
sessions live; train/eval result/.done absent, original deadline unchanged.
Exact-three-root storage600,210,408,523bytes/exit0/no stderr, no failure receipt.
SpB→Qwenrandom remains waiting-predecessor with no new dispatch/container.
Step88 has finite positive gradient and consumed-validity1; its single-batch
zero win rate is not a final evaluation or learning conclusion. Healthy progress
stays quiet. Small JSON/2MiB tail, runtime/clock/PPO/CP/queue checks passed;
no model tests or remote changes. Commit/push this round on the same branch.

## Quiet monitor — September22 16:54:49Beijing

[Snapshot](l7-followup-heartbeat-20260922-165449.json): returned PPO93/96;
CP8..88 each26required nonempty files by stat, train/eval terminals absent.
Container/tmux live; unchanged deadline and exact-three-root storage
600,372,220,104bytes/exit0/no stderr, no failure receipt. Follow-up still waits,
with zero dispatches. Recent steps91..93 consumed-validity1; step92 gradient
prints0.000 at console precision, which proves neither exact zero nor positive
raw gradient. The full-precision terminal gate remains mandatory, unchanged and
pending. No new completion/failure/decision: retain quiet monitoring. Runtime/
clock/finite-metric/CP/queue checks passed; no model tests or remote mutations.

## Predecessor failed — September22 17:15Beijing

[Terminal snapshot](qwen-l7-terminal-20260922-171508.json) supersedes the healthy
16:54 status: predecessor training returned global96,94new steps/752natural
games andCP96, but its frozen terminal gradient gate failed. Six gradients in
console-derived metrics are0.000; the3decimal logging/parser chain cannot
establish their raw positivity. The earlier wording “full-precision terminal
gate” was incorrect; see [diagnosis](qwen-l7-long197.md#terminal-acceptance-failure--september22-1715beijing).
No gate was relaxed and no model-collapse conclusion is justified.

Actual r2queue isfailed/completed[] with`Predecessor failed; stop all successors`.
Suite and all3part dispatches remain absent; no SpBshort/long or Qwenrandom
container exists. Thus none of the1552authorized follow-up games was started.
The predecessor final paired8-game evaluation also did not dispatch. Dedicated
tmux sessions ended; current Docker exited1/OOMfalse. No other tasks were
inspected/stopped. Original budgets, frozen deployments and old artifacts remain.

Failure handed off for user direction; no automatic replacement queue or retry.
Deleted the unique197-qwen-l7-seed96 monitor using the app tool, as required
after terminal failure with no subsequent authorization. A future CPU repair
and separately reviewed continuation needs new approval. Concise evidence is
committed/pushed on the same experiment branch with remote-SHA verification.

## R3 SpB pre storage failure — September22 19:25:22Beijing

[Read-only failure snapshot](l7-spb-storage-failure-20260922-192522.json)
supersedes the19:08:09 healthy first-GPU snapshot. The replacement r3 queue
is failed/completed[], part spb-same/short/pre. Owned Docker exited1 at
19:08:37Beijing, OOMKilled=false. There is no pre result/.done/acceptance,
no train2/post run, and no SpB long or Qwen random dispatch/container.
Thus0PPO occurred; no natural games were accepted, while actual unfinished
game outcomes are unknown. Do not label this as a model or learning failure.

Two immutable failure receipts identify the immediate trigger. At19:08:32.946
the host suite GNUdu returned1 because3 paths under
`spb-same/short/tmp/fup-pre` disappeared (`.ptx`, `.log`, `.ptx.o`). At
19:08:33.991 the child inclusive-suite measurement also returned1, reporting
22missing temporary/compiler paths (`.s`, `.o`, `.res`, `.cdtor.c`, etc.).
Both receipts explicitly contain bytes=null and reject partial totals.
The observed ENOENT failures are consistent with temporary-file removal during
directory traversal; the producer/lifetime mechanism has not been independently
reproduced. The shared measurement lock does not establish a stable snapshot
against unrelated compiler file creation/removal. No new measurement retry,
error filtering, path exclusion or runtime patch was performed.

The retained suite storage-state50113781242bytes at19:08:18 predates failure;
the child arm-only156482295bytes success at19:08:33 does not replace the
required failed suite accounting. Neither can prove current usage, and no
disk-full or GPU-OOM conclusion is supported. The historical GPU stop-timeout
root cause is still not claimed repaired; this owned container did exit.

Already accepted Qwen CP96-only evaluation remains unchanged and is not rerun.
SpB first dispatch1790075162.305692, arm deadline1790247962.305692 and suite
deadline1790420762.305692 remain fixed in frozen records. All failed output,
source, temporary artifacts and prior checkpoints are retained. No new source,
deployment, queue or GPU job was created, and no other node/task was inspected.

Failure handed off for direction. Request CPU-only diagnosis/regression repair
first, then separately review any new RUN and remaining-budget continuation;
current approval does not permit automatic repair or retry. Following the
explicit terminal-stop instruction and the OpenAI Docs skill's
[scheduled-task workflow](https://learn.chatgpt.com/docs/automations), the app
tool deleted the unique197-l7 heartbeat (`deleteStatus=deleted`). This removed
only future monitoring, not experiment artifacts. No replacement monitor.

Validation this round: read-only small JSON/hash, queue/Docker terminal,
zero-training/missing-successor and fixed-clock consistency checks; bounded
16KiB/35line log tails; local JSON and diff checks. No model tests, checkpoint
payload reads, GPU diagnostics or server writes. Archive on
codex/fix-invalid-policy-credit with an atomic commit/push and remote-SHA check.
