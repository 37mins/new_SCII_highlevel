# Fresh Qwen same-seed short + 96 (September24)

## Completed September24 18:45Beijing; verified21:43–21:53

Five stages accepted, queue/host/guardians completedexit0.96real PPO,
768training games660wins (85.9375%),3289/3289consumed answers legal,
96audits and exact96same-seed resets.13complete CP sets retained.
All gradients strictly positive in binary64 (min0.00046481854042212944),
so the new run has no historical rounded-gradient gap.
Pre7/8,CP2post6/8,CP96eval8/8 on eight reused pairs; load96 returned,
zero updates,rank/CPU/CUDA RNG paired. This is not generalization evidence.
End-to-end first dispatch to eval result ~4h30m34s; original48h deadline unchanged.
Storage605.5847GiB/1TiB; strictdu exit0/empty stderr. Old same strict failure
and old random failures remain immutable. No additional cleanup.

The [completion receipt](qwen-l7same-fresh-complete-20260924.json) records hashes,
CP metadata and exact container states. The [curve data](qwen-l7same-fresh-curve-20260924-data.json)
contains only selected per-step aggregates, not full raw logs.
Reproduce with node plot-qwen-fresh-curve.mjs DATA.json OUTPUT.png
(SC2_SHARP_MODULE may select the installed sharp module).
Three panels show all96observations and arithmetic trailing8 means; gradient uses
log display, not smoothing of logarithms. Evaluations are separate from training.
Last8training steps48/64wins=75%; the curve is not monotonically improving.
PNG/SVG visually checked at1440x1210. Data SHA256:
fb44b2a6c3554ed1634278dc81aae111a018bbb06c29b95c999b5802bdca5c98.

## Current progress and conditional ETA: September24 14:39Beijing

The frozen controller accepted all three short stages. Pre/train2/post exact
containers exited0 and each result matches .done and its part acceptance receipt.
Train2 completed two returned PPO updates (16natural games,8wins); gradients
4.426372253149748/19.828430019319057 and update_actor18.67/26.32s are finite positive.
Post actually loaded ownCP2 and completed8natural games/6wins/0updates.
Pre7/8 -> post6/8 on eight reused seeds does not establish learning improvement.
Own native parent readiness now passed/actual_parent_verified=true at14:36:54;
this supersedes the launch-time deferred-parent state below, without altering it.

Long train96 exact container80abe03174c3b0b584e16b1d0aef48fb87f9f45390435b3cc57484a5dba1df9d
started14:36:56, correct long owner, running/unpaused/noOOM. Manifest clean5228e9a,
world8/binary64-v1,start2/target96. No long terminal or returned PPO was observed yet;
parent CPU readiness alone is not proof of the GPU native load returning.
Two-root49,994,358,380bytes/1TiB, strictdu exit0/empty stderr; no failure receipt.

Mean of the first two full step times190.92/224.08s is207.50s; extrapolating94steps
gives5.42hours before extra loading/checkpoint/evaluation overhead. Provisional
completion window: **September24 20:00–22:00Beijing**, assuming no failure or resource
wait. Only two early steps support this rough estimate; seed-dependent game durations
and I/O can shift it. **September26 14:15:03.797 remains the hard budget deadline,
not expected finish time.** No server writes, diagnostics, restart or repeat dispatch.
[Read-only snapshot and assumptions](qwen-l7same-fresh-progress-eta-20260924-143946.json).

## Actual admission and launch: September24 14:17Beijing

Runtime/controller5228e9acc7698c69bdcce9af30aa5a7570829a19, independently remote-matched
by read-only Git dry-run ref comparison after successful push (ls-remote TLS failed).
Source clean, prepared14:06; actual Linux CPU gates passed14:09:285model/controller
tests (including24fresh-Qwen tests)+71host tests, zero skipped/CUDAuninitialized;
three CPU containers exited0/DeviceRequestsnull. Five launcher/Hydra configurations
and34source hashes passed. Local final regression86tests/0skips is separate evidence.
Long actual_parent_verified=false deliberately waits for own future nativeCP2.
The reused readiness helper's deferred_gate string says SpB; Qwen model/path and
accepted-qwen-same-full-state-prefix-v1 contract are authoritative. Receipt stays untouched.
[CPU and preparation receipt](qwen-l7same-fresh-cpu-20260924.json).

Single tmux queue submitted14:15:01, socket sc2_qwen_l7same96_197_20260924_r1,
session qwen_l7same96_197_r1. Frozen SpB predecessor five-stage verifier write=False
and exact terminal/container/guardian checks passed. Original admission gates passed.
dispatch.start1790230503.797456; deadline1790403303.797456
(September26 14:15:03.797Beijing), common48h clock, not estimated finish time.
Pre container761f502cd72635dadb63eb301e683b646b7f56dfd3b3ccc285f7ac91b4aaf46b
started14:15:04, exact owner qwen-same/short, running/unpaused/noOOM, GPUrequestall.
Manifestclean5228e9a/world8/binary64-v1/originalQwen and SC2 in_game/planner
first observations observed14:17:21. Still zero-update pre, no result/.done/acceptance,
no PPO yet; guardian empty terminal slot is normal. Two-root sample43,779,536bytes/
1TiB,return0/empty stderr/no failure. [Launch receipt](qwen-l7same-fresh-launch-20260924.json).
Existing unique ten-minute monitor retained; no further cleanup/restart/duplicate dispatch.

## Frozen protocol and pre-launch planning history

Budget already approved: see[qwen-l7same-rerun-budget-20260924.md](qwen-l7same-rerun-budget-20260924.md).
This is a new repetition, not repair of historical rounded gradients.
Historical Qwen same strict failed and all failure records remain unchanged.
Separate user-authorized pruning affected only old same-arm intermediate weights;
no further automatic pruning is permitted.

Output:/var/jfsCache/sc2-qwen-l7same96-197-20260924-r1;
source:/var/jfsCache/sc2-qwen-l7same96-197-source-20260924-r1/code.
Both entire roots count toward1TiB, including preparation/CPU/bundle remnants.
RUN prefix:sc2-qwen-l7same96-197-20260924-r1; parts qwen-same/short and qwen-same/long.
Only197/8GPUs; fresh original Qwen3-4B-Instruct-2507 revision
cdbee75f17c01a7cc42f958dc650907174af0554, never old trained weights.

pre8/0update -> fresh train2(16games/2PPO) -> post8/0update ->
own nativeCP2->96(752games/94PPO) -> ownCP96 eval8/0update.
792new natural games/96PPO,48wallh/384GPUh from one first dispatch, common absolute
deadline for all five containers, no reset at long. First admission expires
September26 02:22:39Beijing (predecessor cutoff+1h), not an ETA.
Admission remains8idle/unowned GPUs/no computePID,600GiB RAM,1084GiB freeNVMe,
fsync/readback; host sampler/guardian,45second cleanup,no retries or fallback.
No GPU is reserved during CPU preparation or admission waiting.

The new wrapper reuses the tested SpB one-shot host queue, per-stage container
isolation and strict two-root accounting; it does not edit any frozen deployment.
Only the explicit accepted-qwen-same-full-state-prefix-v1 contract is added:
Qwen/same_uniform101/same/native driver state required, legacy import forbidden.
No training/reward/action/generation algorithm changes. Existing startup1 and
single reset attempt remain, eight games in parallel; not bitwise replay of old same.
Private Random0 draws one0..100 per step with replacement, replicated across8.
Full reset0..95 seed sequence, actual returned PPO with binary64-v1 positive finite
gradient and update_actor time, invalidAdv<=0 and96audits required.
CP2 andCP8..96:13complete26-file checkpoints. Endpoints' eight seeds and all rank
CPU/CUDA RNG pair with own fresh evaluation prefix, zero eval updates.
Mechanical legality/gradient/finite metrics do not prove strategic learning.

Predecessor gate: original SpB random queue completedshort+long; both part
state/host state and all five exactowned containers/guardians completedexit0
with original deadline; call frozen83f3530 five-stage verifiers write=False.
Then own short must pass before nativeCP2 contract+actual parent CPU readiness,
and only then long. Any failure blocks all successors; no manual skipping/restart.

Entry:python3 -B qwen_l7same_fresh197.py prepare, host-regressions,
cpu-command0/1 and regressions-command0. Commands emit exact Docker argv; CPU
entries request no GPU and must exit0 with CUDA uninitialized and zero skipped
tests. Five actual launchers/Hydra and34source hashes must pass before queue.
The parent-readiness check is intentionally deferred until fresh CP2 exists.
queue is one-shot under exclusive lock and refuses existing queue-state/dispatch.
This planning record is NOT proof of server preparation, CPU success or GPU dispatch;
actual sourceSHA/receipts will be appended after those operations.

Local preflight: syntax and34/34manifest hashes checked. Initial five-module
synthetic regression run passed85tests/zero skips (not Linux/GPU proof); final
regression marker check added afterward and retested below in deployment receipts.
Command:PYTHONPATH=/private/tmp/sc2-qwen-native-testdeps-20260924:tests:scripts:.
bundled-python -B -m unittest -v test_qwen_l7same_fresh197 test_spb_l7_random197
test_l7_followup197 test_sc2_policy_resume test_metric_precision.
Only local isolated test dependencies OmegaConf2.3.0/antlr4-runtime4.9.3/PyYAML6.0.3
were installed; no server/shared runtime dependencies changed.
