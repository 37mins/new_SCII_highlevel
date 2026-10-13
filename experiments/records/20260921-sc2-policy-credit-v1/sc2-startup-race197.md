# SC2 parallel startup collision candidate — September23

Status: **New r2 native CP8 continuation and paired eval96 completed and
accepted September24 01:22Beijing**. The88-step suffix has614/704 natural wins;
eval8/8 matches its own CP2post8/8, so no demonstrated improvement. Both exact
containers exited0 and the frozen successor gate passed. Full compact terminal,
seed/RNG, metrics and CP-inventory evidence is in the
[completion receipt](qwen-random-complete-spb-random-start-20260924.json).
Old r4 failure and historical CP2 non-bitwise ancestry remain unchanged.
The proposal and20:30 snapshot below are historical, not current status.
User approved diagnosis/repair and a controlled continuation proposal after the
failure handoff, not a new GPU dispatch. Branch `codex/fix-sc2-startup-port-race`
starts at `7bba013c47dd7750aecec3e1d6e275a95e95a62f` before shared startup-code
changes. Keep the existing experiment record; this is not a new scientific arm.

## Current result, checked20:30 Beijing

- SpB L7same:96PPOsteps complete,445/768training wins. Paired pre4/8 → CP2post3/8
  → CP96eval2/8. No demonstrated improvement; eight pairs cannot establish
  stable degradation. Final33/33consumed answers valid.
- Qwen L7random:returned13,11newPPO,88natural games/76wins,324/324consumed valid.
  Global14 reset failed; no final eval. Host queue/part and result=.done remain
  failed/exit1; exact container exited1/OOMfalse. Not answer-legality collapse.
- Only CP8 exists.26required entries (24rank model/optimizer/extra-state files,
  data.pt and sc2_state.pt) are nonempty. Additional tokenizer metadata exists.
  Inventory is not a contents/load proof. Monitor was deleted after handoff.
  No new monitor/queue; SpB-random length/resource authorization is still pending.

[Evidence](sc2-startup-race-diagnosis-20260923.json),
[original failure](l7-qwen-random-failure-20260923.json).

## Evidence versus inference

Frozen runtime `9cb291ea5f50de205c5d88371e08ce229b7d9d04` is unchanged.
A bounded1MiB console tail shows worker2512 closing SC2 API port33471 at
21:26:03.745 and worker2506 closing33471 at21:26:03.781, with disconnected/closed
WebSocket failures. These are verbatim log clock values, not Beijing timestamps;
host state is time authority. Planner bridge ports were distinct55917/50957.
Startup admission was eight-way; actual launcher reset attempts were **one**.
The generic “after retries” message does not show multiple attempts.

Read-only inspection of the exact stopped container's dependency source shows
SC2Process picks its API port before Popen. Portpicker closes its probe socket
before SC2 binds and has process-local bookkeeping by default. This permits a
pick/close/bind race. No third-party source is copied or modified. Dependency
and adapter hashes are in the receipt. SC2 child stderr goes to DEVNULL, so no
retained bind error proves this was the unique historical cause. Treat matching
ports as strong evidence, not certainty. Dependency cleanup also logs KILLED
for an already-exited child; the word does not prove OOM or an external kill.

## Minimal candidate

The Qwen launcher explicitly sets
`+ray_init.runtime_env.env_vars.SC2_RESET_CONCURRENCY='1'`, retaining one reset
attempt and8rollouts. Existing reset lease spans bridge allocation/child launch
through first observation (or failure cleanup), **not the complete game**.
All workers must share SC2_RESET_LOCK_DIR in the stage container; this must be
checked in any new frozen deployment.

The adapter uses a monotonic admission deadline and raises on timeout instead
of returning None and launching unlocked. Metadata errors close descriptors;
alarm setup/clear exceptions cannot leak the lease. Explicit disabled admission
remains unchanged for legacy callers; this candidate does not select it.
No seed resampling, synthetic failed episode or new automatic retry is added.

Model, difficulty, seeds, generation/action/no-thinking support, reward, PPO,
result gates and old artifacts are unchanged. Only the adapter's current source
manifest hash changes. Existing frozen deployments retain old code; completed
SpB and Qwen same96 are not rerun. This coordinates cooperating workers only,
not unrelated port users. Startup scheduling and host pause/resume timing are
not proven GPU-equivalent. Do not call this a general SC2/network fix.

## Actual CPU validation

macOS CPU; no SC2/Ray/CUDA/model initialization:

```bash
python3 -m unittest discover -s tests -p test_sc2_reset_startup.py -v
PYTHONPATH=tests:. python3 -m unittest test_sc2_child_seed test_r6_natural_termination test_r6_terminal_policy_credit test_qwen_l7_long197 test_qwen_seed_acceptance197 -v
bash -n experiments/records/20260921-sc2-policy-credit-v1/run_qwen_seed_arm.sh
shasum -a 256 -c configs/system-v1.sha256
```

9startup tests passed/0skips. Synthetic pick/close/bind reproduces EADDRINUSE;
the real eight-process flock/TCP test keeps8listeners alive on distinct ports
after sequential lease release. Initial sandbox run passed7, denied localhost
bind for2; the permitted rerun passed all9.34existing seed/termination/consumption/
launcher tests passed/0skips.34/34source hashes and shell syntax passed.
These prove CPU mechanism/contract only. Actual Linux/Hydra preflight, native
CP8 deserialization/load and real SC2/GPU acceptance are not performed.

## Controlled continuation proposal — no dispatch

Use only failed Qwen-random's own native CP8 under a new clean SHA and unique
RUN_ID. Preserve old failed r4 and all artifacts; no nonexistent CP13 or same96
weights. Verify native model/Adam/scheduler/dataloader, rank RNG, sc2_state,
driver RNG and independent-seed protocol before admission; no implicit legacy
fallback. Expected next reset index8 must match Random0. New verifier must
account for the retained global3..8 prefix and88-step suffix, not falsely apply
the old94-new-step contract or claim failed r4 passed terminal acceptance.

Proposed global9..96:88PPO/704natural games, then8paired CP96 eval games/0updates.
No separate smoke games: actual first resumed batch is startup/GPU gate. Any
failure stops, no resampling/retry. Existing strict gradient/credit/legality,
natural-ending/load/seed/RNG/checkpoint gates remain.

| Allocation | Game slots |
|---|---:|
| Failed r4 global3..13 completed |88|
| Failed r4 global14 reset dispatched, no completed outcomes |8|
| Proposed CP8→96 train+eval |712|
| Proposed cumulative Qwen long |808|
| Original Qwen long |760|
| Additional approval required |48|

Extra48 =40repeated completed games(global9..13) +8failed dispatched slots.
Suite cap would become1608 instead of1560, retaining interrupted SpB pre cost.
Original accepted Qwen CP2 short run is not repeated. No free retries.

Keep Qwen cutoff **September25 11:58:40 Beijing** (`1790308720.0467553`) and
suite cutoff **September26 19:06:02** (`1790420762.305692`), GPU-hour/storage limits
unchanged. New source/output/preparation must count with every old root.
Admission still needs8free/unowned GPUs,600GiB RAM,1084GiB local space and fsync;
read-only diagnosis does not establish current resource availability. No ETA
while stopped. Explicit approval of48extra slots, exact new provenance/storage
accounting, Linux CPU preflight and native CP8 verification precede any dispatch.
No SpB-random or other experiment is included in this repair authorization.

## September23 explicit approval — one native CP8 recovery

User replied “批准” to the exact48extra-slot proposal. Implementation entry:
`qwen_random_cp8_197.py` (`prepare`, CPU-only `cpu`/`regressions`, then one-shot
host `queue`). Current unique roots are `/var/jfsCache/sc2-qwen-random-cp8-197-20260923-r2`
and `/var/jfsCache/sc2-qwen-random-cp8-197-source-20260923-r2`. No other arm is
authorized. Keep the old failed deployment and result unchanged.

The new native-CP8 contract binds the exact failed-r4 SHA, closed global3..8
prefix, all small evidence hashes,26-file inventory, accepted ancestor CP2 and
precise discarded/failed-slot costs. No large model/optimizer shard is read by
CPU diagnostics. CPU checks deserialize only the saved SC2/driver RNG,
dataloader and eight rank scheduler/RNG files. Actual GPU restoration must
return from native model/Adam/scheduler/dataloader/rank+driver RNG loading;
start8/reset8 and the private Random0 batch8 must match. Legacy fallback is
forbidden here; original CP2's historical non-bitwise limitation remains.

New suffix:88actual PPO(global9..96),704natural games plus8paired CP96 eval.
New periodic CP16..96 supply11sets of26files; retained parentCP8 completes the
12-checkpoint lattice. Final acceptance uses binary64, positive finite gradient,
nonpositive finite invalid advantage, actual optimizer duration, closed games,
consumed valid answers and model-local command evidence. Paired evaluation uses
the original accepted random CP2post rank/RNG/seeds, not same96 or a new panel.

Original deadlines are constants, not computed from restart time. A single
host sampler/guardian measures15exact arm roots and15exact suite roots,
including both new roots and all old failed preparation/source/output roots.
Read-only rootfs/assets/ancestors; only new run and its tmp are writable.
No measurement retries, exclusions, stale-value fallback, checkpoint copy,
seed resampling, extra smoke games or downstream experiment. All8cards must
be free/unowned and600GiB RAM/1084GiB NVMe/fsync pass before each stage.

Local13new receipt/launcher tests passed with zero skips. Full Linux regression,
two actual launcher/Hydra checks and native CP8 preflight remain launch gates.
This receipt is a planned authorization, not proof of CPU/GPU completion.

### CPU-only r1 preparation retained, no GPU attempt

Candidate592cd3a completed its actual native CP8 small-state and two launcher/
Hydra gates: scheduler epoch8 on eight ranks, saved driver RNG accepted by CPU
restore, reset8/episode7, next seeds8,24,72,28,30,18,69,57; CUDA uninitialized.
Its regression launcher incorrectly included host-only Guardian tests inside
the CPU container. The host-only protection rejected this and a fixture thread
blocked; the precisely owned GPU-request-null test container was stopped.
No GPU queue/dispatch took place. Retain r1source/output/container/logs.

r2 separates model/startup CPU-container regressions from actual-host Guardian
regressions, as the previous host-supervised launcher did. This changes test
orchestration only, not model/seed/reward/generation/PPO/startup parameters.
Fresh r2source/output plus both r1preparation roots count toward the same1/2TiB;
the same fixed deadlines and +48slot authorization apply. No failed GPU attempt
or extra training is hidden. The r1regression is not described as passing.

### Actual r2 CPU and first GPU restoration

Frozen runtime/controller `34154283a8298ac4fbaab1c63770a6b81f7d375c`, orchestration
`9a7b0faca5b145a891ad211f189121e4949f0eab`.236Linux model/startup tests and71actual
host tests passed, zero skips; both CPU containers exited0/GPUrequestsnull,
CUDAfalse. Two actual dry launchers/Hydra and34source hashes passed. Native CP8
CPU state proof verifies scheduler8 on all ranks, driver RNG, reset8/episode7.

Single queue21:06:37, actual stage container started21:06:39Beijing. Full ID
`fc2f74a4285c5e80660257f42bd1caa21ad1a0614699d680e74938f013106b06`;
socket `sc2_qwen_random_cp8_197_20260923_r2`, session `qwen_random_cp8_197_r2`.
Eight idle cards/no computePID,600GiB RAM/1084GiB local free/fsync admission
passed. Original deadlines remain constants. At21:07:18, strict15-root arm/suite
measurements were100,362,720,935/931,681,952,800bytes,exit0/no stderr.

At21:08:43actual GPU native CP8 restoration returned with source=checkpoint,
global8/reset8 and seeds8,24,72,28,30,18,69,57. Correct canonical/no-thinking
worker banners,cleanSHA/world8/binary64 manifest and actual SC2 slot0/1/planner
boundary observed. This initial snapshot is **not yet all8games or completed
PPO evidence**. No terminal result or learning conclusion.

[Launch/admission/CPU evidence](qwen-random-cp8-launch-20260923.json),
[first actual GPU restoration and bounded SC2 log evidence](qwen-random-cp8-gpu-20260923.json).

### First completed PPO and user-approved unique monitor

September23 21:26:28Beijing read-only check confirms returned binary64 steps9–14,
six actual PPO updates,48natural games/42wins,162/162consumed valid answers.
First step9 gradient40.51620365679264 and update_actor14.277927180752158seconds;
latest14 gradient14.479531739395952/update14.27652271464467seconds. All six
gradients finite positive and invalid advantage maxima0. Current reset14's seed
registration is only the next batch, not a seventh completed update.
The bounded console read was2,689,004bytes, below4MiB; no large checkpoint or
GPU diagnostic was read. Root queue and host supervision remain running train96;
no result/.done yet. [Evidence](qwen-random-cp8-first-ppo-20260923.json).

After explicit “允许新建唯一巡检”, created only `197-qwen-cp8`, ACTIVE every10minutes.
Inventory before creation had only unrelated sc2-v22-1-gate-handoff and idsc-197;
the obsolete197-l7-r4 was absent. Initial API call lacked destination=thread
and created nothing; the corrected call successfully returned the above id.
Healthy progress stays quiet, previously notified native resume/SC2/PPO events
are not repeated; completion/failure/decision gates only. No remote restart or
budget change. Native restoration/startup success is not strategic-learning
or general SC2-network root-cause proof.
