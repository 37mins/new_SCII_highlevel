# SC2 invalid-answer credit candidate

September30: user explicitly approved **fresh original-SpB L9 random96**;
1048 games/96PPO,30h/240GPUh/352GiB, CP2/32/64/96 retained, no pruning/retry.
Implementation and CPU admission are being prepared; **not yet GPU-dispatched**.
The current L8 recovery264 remains untouched and must fully pass before the
new one-shot queue can advance. Historical L8 same draft is superseded.
[Approved budget, entry points and gates](spb-l8random-recovery264-proposal-20260930.md#l9-approved-launch).

September30 10:38 Beijing: recovery264 has **80/264 natural games accepted,
zero updates**, with CP64 batch01 running. Ten result/done/acceptance receipts
agree, guardians completed/exited0/noOOM,279/279 consumed answers valid;
current exact container running/unpaused, no observed failure. Selection CP2
16/32 and CP32 25/32 are complete; CP64 only5/8 so far, CP96/primary still pending.
Observed mean8.52min/batch suggests completion around14:00–15:30 today,
not guaranteed; absolute cutoff17:11:46 unchanged. Oldr2 strict training remains failed.
User subsequently changed the next priority to **SpB L9 random-seed RL; defer same**,
and explicitly confirmed SpB. The earlier L8 same proposal is superseded, never
prepared or queued. Draft next budget:1048 new games/96PPO,30h/240GPUh/352GiB;
**at that snapshot awaiting budget approval; subsequently approved below**. Current recovery
is not interrupted; a fresh original-SpB start is proposed, not L8 weight transfer.
[Read-only evidence](spb-l8random-recovery264-progress-20260930-1038.json) and
[ETA and revised next priority](spb-l8random-recovery264-proposal-20260930.md#next-l9-random).

September30 10:11 Beijing: user-requested **SpB L8 random r2 96-step training
curve** collected from hash-matched small ledgers:503/768 wins(65.49%), last8
steps35/64(54.69%). All96 returned PPOs refer to the prior forensic audit;
oldr2 remains failed/exit137 and is not retroactively accepted. Training curve
rises then falls; changing scene batches do not establish learning or degradation.
Recovery264 evaluation is excluded. Four collector tests passed; PNG rendered
and visually checked, no remote writes or large checkpoint/console reads.
[Curve, definitions, provenance and reproduction](spb-l8random-r2-curve-20260930.md).

September30 09:55 Beijing read-only update: **SpB recovery evaluation remains
running, with32/264 games accepted and zero new PPO updates**. DiagnosticCP96
is5/8; CP2 selection has12/24 wins across three accepted batches, with its
last8 games running (`sel-b03-cp2`). These are different seed sets, not a
CP2-to-CP96 learning comparison. CP32/64/96 selection and original-vs-fixedCP96
primary64 each remain pending. All four accepted containers exited0, guardian
completed, result=done=acceptance,108/108 consumed answers valid. Current exact
container03370a3a running/unpaused/noOOM; storage receipts return0/empty stderr,
no observed failure. Oldr2 strict training remains failed; no server mutation.
[Compact status and acceptance evidence](spb-l8random-recovery264-progress-20260930-0955.json).

September30 09:23: user-approved **264-game / zero-update failed-r2 artifact
recovery evaluation passed diagnostic8 and is running CP2 validation32**. Single dispatch
09:11:46 Beijing; fixed cutoff17:11:46, including GPU preflight and all33 batches.
Host112 + model/protocol114 actual Linux CPU tests zero skips;33 actual launchers,
7 no-GPU worker imports and all104 required checkpoint file hashes passed.
New code d693286 remotely verified; distinct8 GPU/NCCL probe passed; diagnostic
container0141aeb1 exited0 with completed guardian and result=done=acceptance.
ActualCP96 load/zero updates/original8 seeds and all8 rank CPU/CUDA RNG paired
with ownCP2post;8 natural games5wins,29/29 consumed answers valid. Intent preceded
actualexit by7.84s, no subsequent pause: one real GPU terminal repair gate passed,
not a claim all kernel/freezer failures are eliminated. Host state now lists
sel-b00-cp2, container88853e59; remaining selection128/primary128 not yet accepted.
New32GiB/all-ten-roots352GiB limits unchanged; oldfailed/exit137 and deadlines
retained, no checkpoint deletion/copy/training/CP192/retry.
[CPU and integrity proof](spb-l8random-recovery264-cpu-20260930.json),
[single dispatch and initial GPU proof](spb-l8random-recovery264-launch-20260930.json),
[first real GPU terminal acceptance](spb-l8random-recovery264-diagnostic-20260930.json).
[Approved scope, entrypoints and gates](spb-l8random-recovery264-proposal-20260930.md).

September30 08:30–08:31 Beijing: **SpB r2 recovery forensic checks passed;
no GPU recovery dispatched**. All96 returned binary64 PPO rows,96 audits,
exact seed ledger and768 natural games503wins checked; original short prefix
19 receipt hashes match. CPU-only actual load of40 small state files validates
CP2/32/64/96 driver/rank RNG, scheduler and SC2 counters; model/Adam tensors
remain unread/unverified. R2 still failed/exit137 with no long terminal files.
Eight GPUs idle; retained eight roots301.16GiB. Proposed264 remaining games,
zeroPPO/8h/64GPUh/new32GiB/old+new352GiB requires explicit failed-run artifact
adoption and renewed budget. No old deadline reset, restart or deletion.
[Evidence](spb-l8random-r2-recovery-audit-20260930.json),
[read-only checks, limits and pending recovery proposal](spb-l8random-recovery264-proposal-20260930.md).

September29: terminal/freezer race repair is **opt-in and not deployed to an
experiment**. TaskRunner terminal intent and sampler share the stable lock;
terminal drain requires actual exact-ID exit0 within the unchanged15s batch
allowance. The unchanged recorder runs only after successful guardian/container
termination; failed r2 cannot be relabelled. Local190 tests:186passed/4Linux
skips; full model regressions remain unverified locally. Actual Linux97 CPU
tests zero skips plus all three CPU Docker lifecycle probes passed at23:53.
No GPU dispatch, no new experiment budget, no CP deletion; GPU teardown remains
unverified. [CPU receipts](spb-l8random-terminal-cpu-20260929.json).
[Repair, evidence, tests and CP96 handoff boundary](spb-l8random-terminal-repair-20260929.md).

September29 22:52 Beijing: **SpB L8 random r2 failed at18:53:19; eight GPUs idle**.
Short pre/train2/post accepted; long reached actual returned step96 and wroteCP96,
but no long result/.done/acceptance. Long752 natural games499wins, short16games4wins:
768training games503wins are provisional counts, not strict completed training.
Long94 pre-update audits2658/2658 valid; final returned gradient55.6142,
update_actor8.437s, invalidAdvMax0. Failure again is Docker OCI10s cgroup-freeze
timeout during the single-pause storage sampler; exact container stoppedexit137,
noOOM. Fresh stopped-root du301.12GiB/352GiB, not quota exhaustion. The pause
frequency mitigation did not eliminate the underlying freezer failure.
CP2/32/64/96 each have26required nonempty files by stat; onlyCP2 is published.
No eval96/selection/primary started, no best or pruning. Preserve failed status
and all artifacts; prior ETA invalid. This query did not repair/restart/dispatch.
[Failure handoff and bounded evidence](spb-l8random-r2-failure-20260929-2252.json).

September29 10:48:35 Beijing: **SpB L8 random r2 returned step2; short stage
still awaiting terminal acceptance**. Pre accepted5/8;16 training games4wins,
100/100 pre-update audited consumed answers valid. Actual step2 gradient67.8979,
update_actor74.726s; ownCP2 now on disk59.20GiB, not yet published/accepted.
Exact train2 container running/unpaused/noOOM; successful bounded storage sampler,
no failure. Latest zero GPU snapshot follows update/save, not alone a stall.
Frozen schedule isCP2/32/64/96, full native state; independent validation32 runs
after training. KeepCP2+latestCP64/96+best (ties earlier); only own nonbestCP32
may be removed after validation. This is sparse saving plus terminal retention,
not continuous online rolling; peak four new CPs236.82GiB, usually three177.61GiB
after retention, old failedr1 remains counted. No server changes or deletion.
[Read-only health, actual CP inventory and retention explanation](spb-l8random-r2-health-checkpoint-20260929-1048.json).

September29 10:13:50 Beijing: **SpB L8 random r2 actually running short/pre**.
One queue submitted10:11:02; first GPU probe10:11:03.278, all8 unique GPU/NCCL
checks passed. Exact pre container55f29d76bc76 started10:11:36, originalSpB
clean12f3600/world8/binary64 manifest and SC2 in_game observed. Still pre0updates,
no result/done and no returnedPPO yet. Actual Linux host79/model195 regressions
zero skips; five CPU lifecycle/fault scenarios and four-account churn probe
passed, plus37 launcher configs/nine hooks. Verified pause/measurement/unpause
now works on the live GPU container, six roots64540698052bytes/352GiB, no failure.
Fixed training+selection cutoff Sep30 10:11:03.278; suite Sep30 16:11:03.278.
Oldr1 remains failed/retained; no CP2 adoption, no old deletion, no automaticretry.
[CPU gates](spb-l8random-r2-cpu-20260929.json),
[single dispatch / exact container / GPU and SC2 evidence](spb-l8random-r2-launch-20260929.json).

September29: user explicitly **approved the renewed r2 budget** below. Preparing
a new original-SpB L8 random96 run; no GPU dispatch yet. Docker journal confirms
r1's10s cgroup-freeze timeout. R2 opts into one verified pause for all four quota
accounts within one15s allowance, preserves first pause errors, and still fails
closed. Root cause below the freezer is not proven eliminated. Old+r2 six roots
stay within352GiB;1048 new games include24 repeats,1072 cumulative. Local200
tests:196 passed/four Linux-only skips; actual Linux CPU gates are still required.
[Approved budget, implementation and limitations](spb-l8random-r2-restart-review-20260929.md).

September29 09:52 Beijing: user requested a controlled SpB L8 restart. Eight
GPUs remain idle; r1 remains failed and its CP2 is not an accepted parent. No
server writes or dispatch. The original train cutoff leaves about13h20m,
less than the roughly16.8h training-only extrapolation from returned step2.
A fresh r2 proposal explicitly accounts for24 repeated games and seeks renewed
30h/240GPUh, with old+new six roots still capped at352GiB; numeric renewal and
pause-failure repair/preflight remain outstanding. No old deadline was reset.
[Restart review and exact read-only resource evidence](spb-l8random-r2-restart-review-20260929.md).

September29 09:41 Beijing: **SpB L8 random r1 failed at Sep28 23:49:22;
not running overnight and no long train96 started**. Pre accepted5/8,45/45
consumed answers valid. Short train2 reached returned step2;16 natural games,
7wins,120/120 pre-update audited answers valid, but no result/done/acceptance.
Guardian pause request timed out before storage measurement; pause not verified,
fail-closed recovery stopped exact train2 container(exit137,noOOM). This is a
control-plane failure, not demonstrated disk exhaustion or a model failure.
CP2 file inventory exists(~59.20GiB), but is not a validated/authorized recovery
parent. Post/long/selection/primary all blocked; eight GPUs idle at09:39.
This turn only read status/evidence, no repair/retry/deletion; prior ETA invalid.
[Failure handoff and exact evidence](spb-l8random-r1-failure-20260929-0941.json).

September28 23:14:50 Beijing: **original SpB L8 random96 r1 has actually started**.
Frozen `f7497ab` pushed and exact remote SHA verified before server preparation.
Host71/model195 CPU tests passed, zero skips/noCUDA;14 CPU containers exited0,
37 actual launcher/Hydra configs and9 worker hooks passed. One queue23:12:07,
first GPU23:12:08.209; eight unique devices/NCCL probe exited0. Exact pre
container `d9e4c0ce158a382f2af1e2d74f3efb0d1ee0dfd6015bc29a1ed217bcf3f57d0f`
started23:12:40; clean/world8/binary64 originalSpB manifest, action support and
no-thinking banners, L8 in_game and planner boundary verified. Pre is0 updates,
no result/done/acceptance yet; long still requires own full nativeCP2.
Fixed train+selection cutoff Sep29 23:12:08.209; suite Sep30 05:12:08.209 Beijing.
1048games/96PPO/30h/240GPUh/352GiB unchanged; no old deletion/retry/CP192.
[CPU admission](spb-l8random-r1-cpu-20260928.json),
[single dispatch / GPU / SC2 evidence](spb-l8random-r1-launch-20260928.json).

September28: user **approved SpB L8 random96 budget and exact own-run retention**:
1048games/96PPO,train+selection24h/192GPUh/320GiB,primary6h/48GPUh/32GiB,
suite30h/240GPUh/352GiB; only own nonbestCP32 may be pruned. Thin original-SpB
L8 adapters and native CP2 contract are being validated; deployment/CPU/launch
receipts, not this approval note, establish actual execution. No old deletion,
automatic retry or CP192. [Approved scope and entries](spb-l8random96-proposal-20260928.md).

September28 22:24 Beijing: user requested **L8 SpB random96 from original SpB**.
Read-only check: previous Qwen suite completed/exit0; eight A100s idle/no compute
PID,774.24GiB disk and756.53GiB RAM available; no other service was stopped.
SpB native checkpoint metadata totals59.20GiB each, four estimated236.82GiB.
New proposal1048games/96PPO/30h/240GPUh/352GiB requires numeric budget approval;
original/CP96 paired64 and independent validation32 are separate from training.
No prepare/queue/GPU dispatch or deletion; historical L7 is not an L8 run.
[L8 SpB proposal and approval boundary](spb-l8random96-proposal-20260928.md).

September28 19:36 Beijing: **L8 random r3 entire suite completed at19:20:29,
exit0; primary all192/192 natural games, zero updates,1155/1155 answers valid**.
Original/same96/random96 scored43/64,35/64,45/64 on the same new seeds.
Registered random-minus-same paired gain11/loss1,+15.625pp,exact p=.00634765625;
random-minus-original gain2/loss0,p=.5 does not establish benefit over untrained.
Validation CP2/32/64/96 share identical32 per-seed outcomes, but decision counts
differ; distinct actual checkpoint loads verified, no parameter tensors read.
Historical SpB random is L7:34/64 versus original35/64, no demonstrated gain;
it is not an L8 trained comparator. No server changes or follow-on experiments.
[Completion, paired statistics and diagnostic boundaries](l8random-flat-validation-spb-review-20260928.md).

September28 18:54 Beijing: **primary paired64 remains active, 19/24 stages /
152/192 games accepted**, current b06-same96; exact owner container running,
unpaused/noOOM. No new RL is running. Training curve has no clear sustained rise:
first/middle/last32-step blocks184/256,197/256,194/256; independent validation32
ties22/32 acrossCP2/32/64/96. Execution acceptance is not evidence of learning
benefit. Primary arms still have unequal completed counts, no final comparison.
No server changes or new work dispatched.
[Read-only status and interpretation](qwen-l8random-r3-status-20260928-1854.json).

September28 18:38 Beijing: **L8 random r3 training and independent selection accepted;
primary three-arm paired64 still running (128/192 games)**. All96 returned PPO,
768 natural training games575wins (74.87%),3566/3566 consumed answers legal;
96 finite positive gradient/update rows and exact independent-seed batches checked.
Pre/CP2/CP96 diagnostic8 each6wins. Independent validation32 atCP2/32/64/96
each22wins; predefined tie rule selectsCP2, not evidence of improvement.
Approved queue pruned only its ownCP32 (46.42GiB, irreversible), retainsCP2/64/96;
old runs remain. Current fixed-weight primary b05-original, no PPO, no final
same/random claim. Read-only check and static plot only, no server changes.
[Current status](qwen-l8random-r3-status-20260928-1838.json),
[curve definitions and reproduction](qwen-l8random-r3-curves-20260928.md).

September28 09:48 Beijing: **L8 random r3 actually started, short/pre running**.
Frozen `ad81511` was pushed and exact-SHA remote verified before deployment.
Actual host71/model283 tests passed with zero skips/noCUDA;15 CPU containers
exited0/DeviceRequests=null,45 launcher/Hydra configs and10 Ray worker hooks passed.
L10 five-stage terminal gate passed without interruption. Single queue09:45:14,
first GPU09:45:15.466; eight unique CUDA devices/NCCL probe completed/exit0.
Exact pre container `719101af8b913254e5a816998ab6cb5743e4039490c973e80c71cbf278558305`
started09:46:04; original Qwen clean/world8/binary64 manifest and L8 SC2 planner
observations verified. Pre has no result/done/acceptance yet; zero returned PPO.
Fixed train+selection deadline Sep29 01:45:15.466; suite Sep29 07:45:15.466 Beijing.
Budget remains1112games/96PPO/22h/176GPUh/288GiB, nine roots; no old deletion,
retry or CP192. Latest2+independent-validation-best/CP2 protection is frozen;
no checkpoint has been pruned. Earlier not-deployed notes below are historical.
[Actual CPU gates](qwen-l8random-r3-cpu-20260928.json),
[single dispatch / GPU / SC2 evidence](qwen-l8random-r3-launch-20260928.json).

September28: user explicitly approved controlled **r3** after r2 CPU mount failure.
New exact RUN_ID `sc2-qwen-l8random96-197-20260928-r3`; r1/r2 six roots retained,
all nine r1/r2/r3 roots counted. Budget unchanged1112games/96PPO/22h/176GPUh/288GiB;
train+selection16h/128GPUh/256GiB, primary6h/48GPUh/32GiB. Local baseline-file fix
from`c16dcca` pins the real historical config/hash and mounts only that file readonly.
Old deployments stay frozen; no old deletion/automatic retry/CP192. New r3 CPU and
queue receipts, not this approval note, establish actual admission/dispatch.
[Approved r3 scope](qwen-l8random96-proposal-20260927.md#r3-approved).

September28 00:01:58 Beijing: **L8random r2 CPU admission failed, no queue/GPU/game/PPO**.
Frozen `ce17791` was pushed/remote-verified and prepared once. Actual host71 and
model/controller282 passed, zero skips/noCUDA. Short's three launchers/Hydra and
34 hashes passed, but baseline comparison could not follow historical same-r2's
absolute train2 symlink into unmounted retained same-r1. CPU container exited1;
all successors stopped. L10 exact long/train96 still running and untouched.
Local fix pins/mounts only the real small config file by SHA256;134tests,
130passed/4local Torch skips. Read-only host normalized comparison succeeds with
only authorized seed differences. Fix not deployed/retried; controlled r3 needs
approval, nine old/new roots under unchanged1112games/96PPO/22h/176GPUh/288GiB.
[r2 failure, precise diagnosis and local correction](qwen-l8random-r2-cpu-failure-20260928.json).

Latest Sep27: user approved controlled L8random r2, independent validation32
at CP2/32/64/96, and own-run latest2+best with CP2/final96 protected.
1112games/96PPO, train+selection16h/128GPUh/256GiB, test6h/48GPUh/32GiB,
suite22h/176GPUh/288GiB over all six r1/r2 roots. L10 and old artifacts untouched.
Continuous native training finishes before independent validation; best never uses
training wins or test64, and primary comparison remains fixed CP96. Native save
format unchanged; host fsync/acceptance precedes atomic publication manifests.
Only own CP32 can be pruned, after full selection acceptance and reader checks;
failure stops successors without retry. Runtime deployment/CPU/queue status will
be recorded separately; local implementation is not a GPU launch.
[Approved r2 scope](qwen-l8random96-proposal-20260927.md),
[storage/publication/selection contract](checkpoint-storage-design-20260927.md).
Earlier pending-approval and r1 states below are historical.

September27 23:27: user permits rolling checkpoints plus the current best.
Design scope is new-run latest-two full + validation-best, with CP2 and finalCP96
protected and no duplicate copies; old runs/L10/r1 residues remain untouched.
No implementation/deployment/deletion this turn. Best requires independent
selection validation, not training wins or the final64 test seeds. Proposed
CP2/32/64/96 x32 validation games adds128games/0PPO and requests +4h/32GPUh;
suite would be1112games/96PPO/22h/176GPUh, storage stays288GiB.
Extra evaluation budget and controlled CPU-fix r2 remain pending confirmation.
[Retention, selection, safety and budget](checkpoint-storage-design-20260927.md#rolling-best-policy).

September27 23:16:49 Beijing: L8random r1 was prepared once from remotely backed
`1fbe6e1`, but its CPU regression container exited1 while saving its receipt into
a read-only suite root. Host71 and model/controller265 tests passed with zero
skips; the model receipt was not saved, so CPU admission is NOT accepted.
No GPU probe, queue, new game or PPO; launcher/Hydra and Ray hooks were not run.
Local writable-owner receipt correction is ready:117tests,113passed/4local Torch
skips; it has NOT been deployed or retried. A new controlled r2 requires approval,
retaining all six old/new source/output/eval roots under unchanged budgets.
L10 long/train96 remains running and untouched; r1 failure/artifacts retained.
[CPU failure and local fix receipt](qwen-l8random-cpu-failure-20260927.json).

September27 approval snapshot: user explicitly approved the L8random96 + three-arm new64seed budget,
including four full CP2/32/64/96 and352GiB train admission; local implementation
is in progress, not yet server-prepared/queued. L10 already in long/train96 and
remains untouched. One Qwen full checkpoint measured46.42GiB: model16.44,
optimizer29.97; eight shards, not eight complete copies. A future eval-only/full
split is a proposal, not an unauthorized change to this run or permission to delete.
[Approved scope/implementation](qwen-l8random96-proposal-20260927.md),
[checkpoint breakdown and design](checkpoint-storage-design-20260927.md).

September27 22:32:33 Beijing: user reprioritized the next proposed experiment to
**fresh original-Qwen L8 random96 versus completed L8 same96**, but explicitly
requires a new budget confirmation before dispatch. Read-only inspection confirms
L10 already started and now short/train2 is active after accepted pre8; eight A100s
are occupied. Do not interrupt or change its remaining stages. Existing queue ends
after L10 and has no CP192/additional L9/L10 successor. No L8 random prepared/queued.
Proposed next budget:792training-chain games/96PPO plus192zero-update evaluation
games (original/sameCP96/randomCP96 on64fresh paired seeds),18h/144GPUh/288GiB.
SparseCP2/32/64/96 and352GiB initial/training admission are explicit pending choices,
not silently equal to old same's13checkpoints or1084GiB gate. Current free742.08GiB
must still reserve L10's remaining output. No remote writes/deletion/retry this check.
[Read-only receipt](qwen-l8random-priority-status-20260927.json),
[scope, budget, comparison and acceptance proposal](qwen-l8random96-proposal-20260927.md).

September27 22:20:19 Beijing: **L9 final evaluation accepted; L10 actually started**.
Authorized r3 was queued once at22:11:22, controller`5152bbb`/unchanged runtime`1c6cf60`.
L9 retained784games/96PPO passed the corrected full verifier; only CP96eval8 was
newly run:3/8natural wins,145/145consumed answers valid,0updates,actual CP96load,
all8rank seed/CPU-CUDA RNG paired with ownCP2post. Result=.done=acceptance,
exact container/host/guardian exited0; L9 arm completed22:18:59. Oldr1/r2 failures remain.
L10 auto-dispatched22:19:00; GPU preflight exited0 and exact short/pre container
started22:19:34,still running at the snapshot. This is pre-evaluation,not returned PPO.
Original Qwen→L10 same96/792games follows in the same fail-closed queue.
L10 fixed hard cutoff Sep28 10:19:00; original suite cutoff12:11:48 unchanged.
Actual CPU tests host71+model/controller235/local112,zero skips; ten no-GPU
containers exited0. Nine-root strict storage202044805211bytes<512GiB,return0/empty stderr.
No L9 retraining/deletion/budget extension. Technical acceptance does not establish learning.
[CPU receipt](qwen-l9-l10-r3-cpu-20260927.json),
[launch/completion receipt](qwen-l9-l10-r3-launch-20260927.json),
[handoff](qwen-l9-l10-continuation-20260927.md#r3-actual-launch-and-l9-completion).
Earlier planned/failed entries below are historical snapshots.

September27 late evening: user explicitly authorized **r3 single controlled continuation**,
fixing distinct arm/stage admission receipt names. Real-admission regression first
reproduced r2's collision;112local tests now pass,zero skips. Nine complete r1/r2/r3
roots retain the original512GiB suite cap and fixed deadlines. No repeated L9 training,
no deletion/automatic retry. This is preparation,not a new GPU launch claim.
[r3 scope and tests](qwen-l9-l10-continuation-20260927.md#r3-authorized-admission-repair).

September27 21:44:55 Beijing: **r2 continuation failed before L9 eval launch;
eight GPUs are idle, L10 has not started**. Single enqueue21:40:02, frozen
controller`5261ff5`with unchanged model runtime`1c6cf60`. Corrected full retained
verification passed for L9's784games/96PPO and CP32/64/96 native states;
old r1 failed state is preserved. Eight-UUID/NCCL GPU preflight exited0, but
duplicate arm/stage admission attempted exclusive creation of`fsync-eval96`
twice and failed at21:40:38 before creating any evaluation container.
This is a controller bug, not model/SC2 failure: zero new games/updates.
Actual host71+model/controller231 CPU tests, four no-GPU Ray hooks and ten
no-GPU containers passed, but mocked admission in queue tests missed this
interaction. Local real-admission reproduction confirms the cause.
No retry/deletion/budget extension; a new controlled RUN_ID requires approval.
[CPU receipt](qwen-l9-l10-r2-cpu-20260927.json),
[failure/retention/GPU-release receipt](qwen-l9-l10-r2-failure-20260927.json),
[handoff](qwen-l9-l10-continuation-20260927.md#r2-terminal-failure-september27-214038-beijing).

September27 evening: user explicitly authorized a
[controlled L9 acceptance repair + L9 eval8 then L10 r2 continuation](qwen-l9-l10-continuation-20260927.md).
Retain L9's96PPO/784games, only800games/96PPO remain; no repeated training,
no old writes/deletion, no deadline/budget extension. This is preparation,
not a GPU launch claim; original failed state and the following evidence remain.

September27 20:49–20:55 Beijing: **L9 training process finished96/96, but strict
host acceptance failed; GPUs idle and L10 not started**. Train96 exact container
exited0 at20:28:32, result=.done; complete training outcomes297/768wins.
The frozen verifier indexes CP32 in a result inventory containing only finalCP96;
CP32/64/96 each have26nonempty required files by stat, not payload validation.
No CP96eval, no final L9 acceptance, no retry/fix/dispatch this check.
[Failure evidence](qwen-l9-acceptance-failure-20260927.json),
[L8 completed curves and L9 execution-only curve](l8-l9-curves-20260927.md).
The earlier20:22 running status and completion estimate below are superseded.

September27 20:22 Beijing: **L9 same RL at94/96 returned PPO; L10 not started**.
L8common64 finished12:11:26,192/192natural games/0updates,queue/state/host exited0.
Same64seeds: original46/64,CP96 35/64,CP192 37/64; trained checkpoints are lower,
not established learning improvement. Paired original→CP96:5gains/16losses;
original→CP192:5/14; CP96→CP192:3/1.24result=.done=acceptance and8batch RNGpairs checked.
L9 dispatched12:11:48; pre/train2/post accepted, ownnativeCP2 loaded, long active.
Latest actual returned global94 has positive finite gradient/update time and invalidAdv0;
pending95's passed credit audit is not another returned PPO. CP32/64 directories present;
CP96/eval96 and final acceptance remain. Eight worker processes still occupy GPUs;
instant0%util is not idle. Strict arm storage141.6GiB<256GiB, no recorded storage failure.
Estimated L9 completion20:40–21:10, not guaranteed; fixed L9 cutoff Sep28 00:11:48,
pair cutoff Sep28 12:11:48. No server changes/retries/deletion this check.
[Small progress/result receipt](qwen-l9-l10-status-20260927-2022.json).

September27 10:59 Beijing: **[L9/L10 RL explicitly approved and queued once at10:58:40; waiting for L8, no new GPU dispatch yet](qwen-l9-l10-rl-budget-20260927.md)**.
User selected RL long training, not the offered zero-update transfer evaluation.
Approved two independent original-Qwen same96 arms,1584new games/192PPO,
24h/192GPUh/512GiB combined,CP2/32/64/96 only; each12h/96GPUh/256GiB.
Frozen`1c6cf60`pushed/independently verified; actual211model+71host tests zero skips,
ten launcher/Hydra configs and six real no-GPU Ray hooks passed;11CPUcontainers exited0.
L8common64 has96/192games accepted, b04-cp96active. New host queue is alive and
waiting-predecessor; no L9/L10 GPU/SC2/PPO or old artifact deletion occurred.
[CPU receipt](qwen-l9-l10-cpu-20260927.json), [single-queue receipt](qwen-l9-l10-queue-20260927.json).

September27 09:56 Beijing [L8 conclusion/status check](qwen-l8-conclusions-status-20260927-0957.json):
192actual Qwen same PPO updates completed; no established learning improvement.
Reused8seed diagnostic: original6/8,CP96 5/8,CP192 5/8 (last contrast1gain/1loss).
New common64 evaluation: first original batch accepted6/8,54/54valid,0updates,
exact container/guardian exited0; CP96 batch0 load returned,currently evaluating.
Only8/192new games accepted; no final common64comparison yet. Read-only check,
no new dispatch/retry/deletion. Earlier startup entries below are snapshots.

September27 **actually dispatched09:46:29 Beijing**, first original arm running:
[L8 original/CP96/CP192 common64 paired evaluation](qwen-l8-common64-proposal-20260927.md),
192new games/0updates,6h/48GPUh/32GiB. New exact `sc2-qwen-l8-common192-197-20260927-r1`;
64new seeds frozen,24 serial stages; unchanged L8 protocol, no training/deletion/retry.
Frozen runtime`e01594e`pushed/remote SHA verified;124model+71host tests zero skips,
24actual launchers/Hydra,3real no-GPU Ray hooks and8distinct GPU/NCCL preflight passed.
Fixed hard deadline today15:46:29; estimate11:45–12:45, not a guarantee.
At09:50first original evaluation active atglobal0,0updates, clean/world8/binary64;
bounded sample6consumed answers all valid, no stage result yet.
[Small launch receipt](qwen-l8-common64-launch-20260927.json).

September27 09:22 Beijing: **[L8 CP96→CP192 completed at00:36:17](qwen-l8same-cp192-20260926.md#completed-september27-003617-beijing)**.
All three stages accepted, queue/state/host completed/exit0 and all exact
containers exited0. New97..192:96returned PPO,768natural games494wins(64.32%),
5900/5900valid consumed answers,96audits/96exact seed rows, six26-file CPs.
OwnCP96 pre5/8 → ownCP192 post5/8, one gain/one loss, all8rank seed/CPU-CUDA
RNG paired; no net improvement established on eight reused diagnostic seeds.
Total784new games,5h39m51s wall,280.87GiB/four roots below384GiB. At09:22all
eight GPUs0MiB/0%/no computePID. No new launch/restart/deletion this turn.
[Compact completion evidence](qwen-l8-cp192-complete-20260927.json).
Earlier entries below are historical snapshots, not current running status.

September26 evening: **[approved L8 CP96→CP192 continuation](qwen-l8same-cp192-20260926.md)**
is actually running r2 pre96 as of18:59Beijing. Eight-GPU/NCCL preflight passed;
ownCP96 load returned and SC2 observations seen, no new PPO claimed yet.
Single dispatch18:56:26, fixed hard stop September27 06:56:26. r1 CPU harness
failed before any GPU/game and remains preserved within the four-root384GiB
cap. [Launch receipt](qwen-l8-cp192-r2-launch-20260926.json). Same experiment/branch, new exact RUN_ID;
96additional online PPO steps,768training+16evaluation games. User approved
12h/96GPUh and then the disk-constrained plan: save112..192 every16steps,
384GiB new source/output cap,448GiB training admission; no old deletion/retry.
The existing CP96 group remains completed. This is not a large offline dataset
trained96epochs; public data candidates are documented separately below.

September26 16:54 Beijing: **[Qwen L8 same96 completed at16:52](qwen-l8same-fresh197-20260926.md#completed-september26-1652-beijing)**.
All five stages accepted; queue/long host/state completed/exit0, exact long
containers exited0.96actual PPO/768natural training games/441wins (57.42%);
5938/5938consumed training answers valid, CP2+CP8..96 required inventories
present. OwnCP96 actual load/0updates/8natural games5wins,63/63valid answers,
all8rank RNG paired with ownCP2post. Pre6/8 -> CP2post5/8 -> CP96eval5/8:
technical completion, no net paired win-rate gain or established learning.
Historical r1 failure preserved; no new launch or server write. [Small receipt](qwen-l8same-complete-20260926-1654.json).
Earlier running/ETA entries below are historical snapshots.

September26 12:25 Beijing: [L8 partial training curve and reproducibility](qwen-l8same-fresh197-20260926.md#partial-training-curve-september26-1225-beijing)
now covers34/96returned steps,153/272natural training wins (56.25%);
recent8steps24/64 (37.5%). Still train96 running-unverified,not final evaluation.
Retained1..2 plus nativeCP2 continuation3..34; no duplicate or future points.

September26 10:40 Beijing: [L8 native long has actually started](qwen-l8same-native-long-start-20260926.json).
Post completed5/8natural wins,29/29valid answers,0updates,result=.done=acceptance,
guardian/container exited0. Full native CP2 contract and parent readiness passed.
Train96 container`91d0dbd99c16…` started10:37:54; model/optimizer/dataloader load
returned atglobal2/reset2,next53×8,source=checkpoint. It will execute3..96 and
then eval96 under the unchanged deadline; no new returned PPO claimed yet.
Original pre6/8→post5/8 is only eight paired samples, not a learning conclusion.

September26 10:35 Beijing: [L8 r2 controlled continuation](qwen-l8same-fresh197-20260926.md)
is actually running post8 after full retention acceptance and CP2 CPU checks.
Controller`db60d07` was pushed/independently verified; model runtime stays`eef0f04`.
Actual328container+71host tests/zero skips,3launchers/Ray hooks and8UUID/NCCL
passed. CP2 actual GPU load returned; SC2 in_game/planner observed. Retained
24games/2PPO are not replayed; post→steps3..96→eval96 follows the unchanged
September28 01:42 deadline/384GPUh and aggregate four-root1TiB quota.
No new PPO or stage completion claimed yet; oldr1 remains failed/read-only.
[Small launch receipt](qwen-l8same-continuation-launch-20260926.json).

September26 10:00–10:02 Beijing: **L8 same96 is stopped, not training**.
Queue failed at01:59:45 after train2 exited0: the new L8 verifier incorrectly
indexed the evaluation-only `result['replays']` field in a training result.
Pre passed (6/8 wins,48/48 consumed answers valid). Train2 returned2PPO,
16natural games/8wins,96/96 audit answers valid and saved26required CP2 files;
both gradients/update times are positive. Sixteen L8 replay paths exist.
Train2 strict acceptance is absent; post/long/eval were blocked, so this is
not a completed96-step run. Eight GPUs are now0MiB/0% with no computePID.
No server changes, replayed games or restart this turn. [Read-only failure
receipt](qwen-l8same-status-20260926-1000.json); the original cutoff remains
September28 01:42:02.741755. The prior5–10h ETA no longer applies.

September26 01:45:16 Beijing: [fresh Qwen L8 same96 RL](qwen-l8same-fresh197-20260926.md)
was dispatched once at01:42:02.741755 on197/eight GPUs, frozen runtime`eef0f04`.
Actual319container+71host tests, five launcher configs, three no-GPU Ray hooks,
and eight-distinct-GPU/NCCL preflight passed. Original Qwen pre is now running
with actual SC2/planner activity; no stage completion or PPO return claimed yet.
Approved792games/96PPO,48wallh/384GPUh/1TiB; all stages share the fixed
September28 01:42:02.741755 Beijing deadline. [Launch receipt](qwen-l8same-fresh-launch-20260926.json).
L8 pilot remaining64 evaluation games are not queued; all prior accepted/failed
records remain. Older approval/status statements below are historical.

September26 01:03 Beijing: r6's real no-GPU Ray hook failed on omitted
`SC2PATH`; all eight CPU configs and 96+71 tests passed, but no GPU dispatch
or game occurred. r1 still has 32 accepted games, 64 remain. The original
runtime `769e55e` and failure are preserved. [Small receipt](qwen-l8-pilot-r6-failure-20260926.json).
A local v2 probe now takes the complete actual-launcher environment; it has
not yet passed a real Ray worker or received permission for another attempt.

September26 00:34 Beijing: r5 is [invalid before GPU dispatch](qwen-l8-pilot-r5-failure-20260926.json):
its CPU-hook CLI typo caused a no-GPU container exit1 before Ray ran. It added
0 games/0 updates; r1's 32 accepted games remain. The user approved [one r6
attempt](qwen-l8-pilot-r6-20260926.md) of just the remaining 64 L8 evaluation
games, with a new frozen RUN_ID and a real no-GPU Ray hook gate before any GPU
dispatch. Twelve r1–r6 roots share 32 GiB; first GPU dispatch would start a
new fixed 4h/32GPUh clock. Approval is not a launch or terminal receipt.

September26 after r4 fail-close: the user approved [one r5 L8 remainder
attempt](qwen-l8-pilot-r5-20260926.md) of only the 64 unrun games, with a
no-GPU Ray worker hook check that matches the real launcher's resolved
`PYTHONPATH`. Ten r1–r5 roots share 32 GiB; a new one-shot 4h/32GPUh clock
starts only at r5 GPU dispatch. This approval is not a launch receipt. r1
still has 32 accepted games; r2–r4 each added zero. No L8 RL is approved.

September25 23:48 Beijing: the separately approved [r4 L8 remainder](qwen-l8-pilot-r4-20260925.md)
was dispatched once, but its 0-game GPU preflight failed in the Ray worker
hook: `feedback_eval` was absent from the direct probe's import path. The
short socket path did let Ray start; CUDA/NCCL and all 64 remaining games
were not reached. r4 added0games/0updates; r1's accepted32 stay intact.
No r4 restart or L8 RL is authorized. [Small failure receipt](qwen-l8-pilot-r4-failure-20260925.json).

September25 after the r3 fail-close: the user approved [one r4 64-game L8
remainder attempt](qwen-l8-pilot-r4-20260925.md) with a short Ray socket path
and retained early probe errors. Its new four-hour/32-GPU-hour deadline begins
only at the one permitted GPU dispatch; all eight r1–r4 roots share 32 GiB.
This approval is not a launch receipt. The retained r1 prefix is 32 games;
r2/r3 added zero. No L8 RL training or automatic retry is authorized.

September25 23:14 Beijing: the newly approved r3 L8 remainder was dispatched
once but its eight-GPU preflight failed before any evaluation game. A no-GPU
same-runtime reproduction confirmed the preflight's long Ray `_temp_dir`
exceeds AF_UNIX's 107-byte socket-path limit; the real preflight had no
stderr capture, so r2's CUDA mapping issue is still untested. r3 added0
games/0updates; the original32accepted games remain intact. No retry or
L8 RL was launched. [Exact small receipt](qwen-l8-pilot-r3-failure-20260925.json)
and [analysis](qwen-l8-pilot-r3-20260925.md).

September25 after the expired 21:53:08 original L8 deadline: the user
approved one new, separately budgeted [r3 64-game remainder](qwen-l8-pilot-r3-20260925.md)
with an eight-GPU Ray/NCCL visibility preflight. Its code and safety checks
are being prepared; approval is not a dispatch or GPU receipt. r1's 32
accepted games and both failed queue histories remain unchanged. No L8 RL
training or automatic retry is authorized.

September25 19:14Beijing: the approved once-only [L8 r2 remainder](qwen-l8-pilot-continuation-20260925.md)
was actually dispatched, then failed before its first new game at reference
model NCCL initialization (`Duplicate GPU detected`). r2 added0accepted games,
0updates and launched no successor. The earlier r1's four accepted stages /
32games remain intact, but the 96-game L8 comparison is incomplete. GPUs
were idle after fail-close; no further GPU retry or L8 RL is authorized.
[Compact terminal evidence](qwen-l8-pilot-r2-failure-20260925.json).

September25 after the L8 pilot launch: the original L8 queue failed at its
fifth stage before any game because Torch distributed could not bind a
rendezvous port. Four stages / 32 natural games remain accepted; the failed
queue is preserved. The user approved a once-only, eight-stage / 64-game
[controlled remainder](qwen-l8-pilot-continuation-20260925.md) under the
same original 21:53:08.526 Beijing cutoff and aggregate resource ceilings.
Approval and local code are not a dispatch receipt; the continuation's
actual state must be checked separately. No L8 RL training is queued.

September25 18:01:53Beijing: the approved [Qwen L8 zero-update pilot](qwen-l8-pilot-proposal-20260925.md)
was dispatched once at17:53:08.526; fixed absolute cutoff21:53:08.526
shared by all12 stages. Frozen runtime/GitHub SHA `9f8def1` matched. All12
actual CPU launcher configs,83container+71host tests passed without skips/GPU.
The first original-Qwen L8 batch finished8 natural games/3 wins/0 updates,
48/48 consumed answers valid, with eight `Flat128_CheatVision_Air` replays;
`b00-same-cp96` was running. This is not a completed comparison or training
result. [Compact launch and first-stage evidence](qwen-l8-pilot-launch-20260925.json).

September25, after the 16:32:57 status snapshot below: the user approved
the [Qwen L8 zero-update difficulty pilot](qwen-l8-pilot-proposal-20260925.md)
and separately approved syncing its frozen code/config/small receipts to the
existing GitHub branch. The one-shot 96-game controller, new paired seed plan,
hook, and synthetic safety tests are being validated. Approval and local tests
are **not** a queue/dispatch/GPU receipt. The historical snapshot below remains
accurate for its timestamp; check the newer launch receipt before describing
current server state.

September25 16:32:57Beijing read-only status: SpB CP2/CP8 diagnostic remains
completed16/16,128games,0updates,exit0. Qwen L8 is proposal-only, not
authorized or queued; no new scoped L8 root or running sc2-named container was
observed. No server mutation. [Compact status](l7-queue-status-20260925-163257.json).

The approved L8 pilot compares released/sameCP96/randomCP96 on32 new paired
CheatVision seeds, 96games total, with a 4h/32GPUh/32GiB hard ceiling.

September25 13:27:59Beijing read-only completion check: approved SpB-same CP2/CP8
diagnostic is completed/exit0 with16/16accepted stages,128natural games and0
updates. Small accepted summaries give CP2 40/64 and CP8 37/64, versus reused
released35/64 and sameCP96 16/64. These are descriptive totals; paired tests
and intervals remain to be computed. No server mutation or further experiment.
[Compact completion evidence](spb-early128-completion-20260925.json).

September25 13:20:43Beijing read-only check: the approved SpB-same CP2/CP8
diagnostic has15/16 accepted stages (120/128natural games); final `b07-cp2`
is running with no final `.done`/acceptance yet. Conditional ETA13:30–14:00;
the unchanged hard cutoff is16:07:22. No server mutation or retry.
[Compact status evidence](spb-early128-status-20260925-132043.json).

September25 11:05Beijing: the user-requested current four-panel L7 training
chart, four frozen configurations, completed results and common64 paired
interpretation are published in the existing [SCII log](https://www.yuque.com/yangdage-mu30r/nsahpp/io9ul989o6qkposx).
The new fresh Qwen-same run is distinguished from the historical strict-failed
same run; training curves and held-out evaluation are not conflated.
[Publication receipt and chart hash](l7-four-current-yuque-20260925.md).
No server experiment was launched or changed for this documentation update.

September25 10:10:15Beijing: approved [SpBsame CP2/CP8 diagnostic](spb-same-early-checkpoints-proposal-20260925.md)
is **running**, single dispatch10:07:22.437. It adds128natural games/0updates on
the existing64-seed development benchmark, reusing original/CP96. First CP2
actual load returned/global2/0updates, cleanc9dfd9a/world8/binary64-v1; SC2
in_game/planner observed. No completed batch/result yet. Linux115model/controller
+71host tests zero skips;16actual launchers/Hydra/34source hashes pass; two CPU
containers exited0/noGPU. Fixed deadline16:07:22,48GPUh/32GiB; estimate12:07–13:07
uncertain, not the deadline. No L8/new RL/retry/deletion. [Launch receipt](spb-early128-launch-20260925.json).

September25 09:32Beijing: the L7 common64-seed matrix is **completed**, not still
running. New four arms finished04:56:53 with32/32stages,256natural games,0updates;
all exact containers/guardians completedexit0. With reused Qwen128, all six arms
cover384games. Qwen original/same/random wins49/53/53 of64; SpB35/16/34 of64.
Qwen's +4wins are not confirmed by exact paired tests; SpBsame's -19wins survive
the three-comparison Holm correction. All1679consumed answers valid: technical
acceptance does not imply beneficial learning. No new server job or mutation.
[Results, paired statistics and limitations](l7-common64-results-20260925.md),
[compact completion evidence](l7-matrix256-complete-20260925.json).

September24 23:59:48Beijing: approved L7 four-arm256-game zero-update matrix is
actually running after complete Qwen128 acceptance; one dispatch23:57:42.505.
First original-SpB batch global0/val_only/world8/clean72068c6 and declared new
seeds verified, SC2 game creation observed; no result yet. Actual Linux71host+
93model tests zero skips/noCUDA;32launchers/Hydra and34hashes pass. Fixed8h /
64GPUh cutoff September25 07:57:42.505;32GiB new-root quota, no old mutations.
[Protocol and queue](l7-matrix256-197-20260924.md),
[launch evidence](l7-matrix256-launch-20260924.json).

September24 23:12Beijing: [fresh Qwen and corrected SpB retraining clarification](fresh-and-spb-rerun-clarification-20260924.md).
Fresh means a new RL run from released instruct weights, not random initialization.
Corrected SpB same and random each completed96PPO/768training games with
11313/11313 and1959/1959valid consumed answers. They do not continue degraded
old checkpoints. Technical acceptance is distinct from demonstrated learning.

September24 23:04Beijing: [four-condition L7 completion and next-experiment recommendation](l7-next-experiment-review-20260924.md).
Qwen same/random and SpB same/random have reached CP96 and terminal eval, with
historical failures/lineage limits preserved. The current Qwen128-game evaluation
has64games accepted; no final inference. Recommend filling four missing64-game
evaluation arms (256additional games,0updates) before deciding L8. Proposal only:
no new training/evaluation/level or budget has been authorized or queued.

September24 22:58Beijing analysis: [what the eight-pair results establish](qwen-paired8-interpretation-20260924.md).
Fresh same CP2 6/8 -> CP96 8/8 is2improved/0regressed pairs (illustrative exact
two-sided p=0.5), not confirmed generalization. Original was7/8, so full-run net
gain is1/8. Random8/8 ->8/8 is ceiling-saturated, not evidence of ineffectiveness.
No server operation or change to the ongoing128-game evaluation.

September24 22:26Beijing: approved128-game held-out paired eval is actually running,
single dispatch22:21:44.865 on197/8GPUs. Frozenb19b3a2 remote-matched,71host+
76model/evalCPU tests zero skips/noCUDA,16actual launcher/Hydra stages passed.
First original-Qwen batch: global0/zero updates/declared eight new seeds and
SC2 in_game→ended evidence observed; no result/acceptance yet. CP96 batch pending.
Common6h cutoff September25 04:21:44.865;64,421,592bytes/32GiB,du0/empty stderr.
Old weights/deployments untouched, no retry or duplicate/new heartbeat.
[Actual launch receipt](qwen-heldout128-launch-20260924.json),
[preregistered protocol](qwen-heldout128-197-20260924.md).

September24 21:43–21:53Beijing: fresh Qwen same entire five-stage chain completed
at18:45:38 (queue18:45:51), all exact owned containers/guardians exit0.
96returned PPO/96audits/96seed resets,768natural training games660wins,
3289/3289consumed answers valid; all binary64 gradients finite positive,
minimum0.00046481854042212944. CP2 and8..96:13sets,26required files each.
Pre7/8, ownCP2post6/8, ownCP96eval8/8, actual load returned/zero updates and
all eight rank CPU/CUDA RNG paired. Eight reused seeds do not establish
generalization or architecture advantage. Historical same strict failure remains.
[Completion receipt](qwen-l7same-fresh-complete-20260924.json),
[96-point curve data](qwen-l7same-fresh-curve-20260924-data.json),
[plot script](plot-qwen-fresh-curve.mjs).
The old monitor was already absent (delete returned not_found); no duplicate created.

User approved the next [128-game original-vs-CP96 held-out evaluation](qwen-heldout128-197-20260924.md):
64new paired seeds,0updates,197/8GPUs,6h/48GPUh/32GiB, new queue128GiB disk gate.
Implementation/CPU gates precede a single dispatch; no old deletion or gate edits.
Planning and approval are not evidence of launch. Older progress entries below are historical.

September24 18:35–18:36Beijing user-requested read-only progress check: the NEW
fresh Qwen same-seed run is in long/train96, latest returned global step93/96.
Matched93audits/seeds and744natural training games (644wins);3185/3185consumed
answers valid. Recent returned steps91–93 have finite positive binary64 gradients,
positive actor-update times and invalidAdvMax0; audits94/seed95 are not counted
as returned PPO. CP8..88 eleven sets each have26nonempty required files.
Exact container running/unpaused/noOOM, no failure; strict two-root storage559.09GiB
of1TiB with return0/empty stderr. Short pre/train2/post completed; train96 terminal
and final8-game eval still pending. Recent step times suggest provisional finish
19:00–19:30 today including checkpoint/eval overhead, conditional and not guaranteed;
fixedSeptember26 14:15:03.797 deadline unchanged. Old same strict-failed evidence
is not rewritten; training wins do not establish learning. No server mutation.
[Compact current evidence](qwen-l7same-fresh-progress-20260924-183518.json).

September24 18:21Beijing documentation-only publication: supplemented the existing
Yuque SCII log with [validity-collapse and seed-group analysis](yuque-validity-seed-analysis-20260924.md).
Separates observed repeated-tag degeneration and pre-centering credit mechanisms
from unproven unique causes; explains mixed-UID scenario variance and correlated
same-seed training curves without claiming either curve proves learning. Includes
completed paired evaluations, counterexamples, and proposed controls (not authorized
new experiments). Corrected one concatenated conclusion and stale SpB pending-eval
sentence. Published readback verified31source blocks and retained all5image URLs;
historical section unchanged apart from minus-sign typography.
[Publication receipt](yuque-validity-seed-publication-20260924.json).
No server access, experiment mutation, new sampling, or permission change.

September24 14:56–14:59Beijing read-only minibatch clarification: freshQwen same
actual nativeCP2 load returned (global2/reset2/next53x8), returned longsteps3–6
verified; exact container running, no failure, original budgets/deadline unchanged.
All four recent runs share minibatch8/microbatch1/world8/ppo_epochs1; a reported
PPO/global iteration includes8natural games and multiple optimizer steps, not
one minibatch. Fresh first6steps average221.92s(collection185.24s,actor21.63s),
not faster than oldsame long94steps141.19s. Different samples/protocols are not
a controlled speed benchmark; old strict failed status remains unchanged.
[Counting convention and timing comparison](minibatch-semantics-20260924.md).

September24 14:39:46Beijing read-only ETA query: fresh Qwen same short pre/train2/post
are controller-accepted, result=.done=part acceptance, exact containers exited0.
Two real PPO steps completed with finite positive binary64 gradients; own nativeCP2
parent readiness passed. Long train96 container started14:36:56, clean5228e9a/world8,
start_step2/target96, still running with no long returned step in this snapshot.
First two step times190.92/224.08s suggest about5.42h for the remaining94updates;
with load/checkpoint/eval overhead and uncertainty, provisional finish is September24
20:00–22:00Beijing assuming no failures or resource waits, NOT guaranteed.
Fixed September26 14:15:03.797 hard deadline remains distinct and unchanged.
No server mutation/retry/cleanup/duplicate dispatch; no learning claim.
[Progress and ETA assumptions](qwen-l7same-fresh-progress-eta-20260924-143946.json).

September24 14:28:17–14:31:05Beijing read-only heartbeat: fresh Qwen same pre
completed14:21:52, result=.done=part acceptance, exact container exited0 and guardian
completed under original deadline. Eight natural games/7wins/0updates,49/49valid
consumed answers,49plans/754queue entries/521local Depot-Marine commands;
original eight eval seeds and rank0..7 CPU/CUDA RNG receipts retained.
Fresh train2 automatically started14:21:53, clean5228e9a/world8/binary64-v1.
First returned PPOstep1 verified: gradient4.426372253149748,
update_actor18.666567133739591s,invalidAdv0; first audit39/39valid consumed answers.
Same-seed reset0/1 are49x8/97x8. Later audit2 is57/57valid but not independently
counted as PPO2; train2 terminal/short acceptance/native parent gate not yet verified.
Existing two-root102,318,870bytes/1TiB,return0/empty stderr/no failure;
fixedSeptember26 14:15:03.797deadline unchanged. No server mutation/retry,
no learning claim; notify only new pre completion/first PPO, retain sole monitor.
[Compact stage and returned-update evidence](qwen-l7same-fresh-pre-first-ppo-20260924-142817.json).

September24 14:17:21Beijing: approved fresh Qwen same-seed run is actually running.
Single queue submitted14:15:01; first dispatch14:15:03.797, exact pre container
761f502cd72635dadb63eb301e683b646b7f56dfd3b3ccc285f7ac91b4aaf46b started14:15:04.
Frozen5228e9a is clean and independently matched to remote branch; original model,
world8/binary64-v1 manifest and SC2 in_game/planner first observations verified.
Pre is zero-update and still unaccepted, no returned PPO yet. CPU gates:285model/
controller+71host tests, zero skips/noCUDA; all five launchers/Hydra and34hashes pass.
SpB predecessor original83f3530 five-stage verifier write=False passed before admission.
Unchanged8GPU/600GiB/1084GiB/fsync gates passed. Single48h deadline
1790403303.797456 (September26 14:15:03.797Beijing), not an ETA, shared across all stages.
792games/96PPO/384GPUh/1TiB; exact two roots43,779,536bytes at this snapshot,
return0/empty stderr/no failure. Existing sole monitor now follows this run;
no further deletion or duplicate dispatch. Older planned/waiting entries below are historical.
[Server CPU evidence](qwen-l7same-fresh-cpu-20260924.json),
[actual launch evidence](qwen-l7same-fresh-launch-20260924.json),
[protocol](qwen-l7same-fresh197.md).

September24 13:45:54Beijing: SpB random entire short+long+eval queue completedexit0.
Final eval exact container/guardian exited0, result=.done=acceptance, actual ownCP96
load returned, zero updates,8natural games5wins/21valid consumed answers;
all8rank/seed/CPU-CUDA RNG match ownCP2post. Baseline4/8->5/8 on eight reused pairs
does not establish learning improvement. No extra games or deadline extension.
[Final evidence](spb-random-complete-20260924-134554.json).
New approved Qwen same fresh wrapper is implemented locally; preparation and
actualLinuxCPU/launcher gates still pending, NOT yet queued or dispatched.
[Fresh rerun protocol](qwen-l7same-fresh197.md).

September24 13:35:56Beijing: user-authorized exact pruning completed,320old
Qwen/SpB same-seed CP16..88 model/optim shards removed (1055.95GiB allocated);
532retained files and8metric/result receipts unchanged. CP2/8/96, random arms,
original models, logs and plots preserved; removed intermediate CPs have no backup.
At13:36:13 the EXISTING frozen SpB queue automatically started eval96 after
the unchanged1084GiB disk gate passed.13:37:31 exact container running,
clean83f3530/world8/binary64-v1 manifest; load not yet verified, result absent.
No duplicate dispatch/restart/gate reduction or deadline reset. New Qwen same
remains approved/planned, NOT prepared or queued; its new48h clock not started.
[Pruning scope](plotted-checkpoint-prune-20260924.md),
[deletion receipt](plotted-checkpoint-prune-20260924-receipt.json),
[SpB automatic final-eval admission](spb-eval96-after-prune-20260924-133731.json).

September24 13:09:57Beijing read-only heartbeat: eval96 admission/run absent;
five accepted train96 terminal hashes, hostcompleted[train96] and deadline unchanged.
Strict two-root831,162,453,514bytes/1TiB,exit0/empty stderr/no failure.
No resource re-diagnosis, server changes or new dispatch; unchanged wait quiet.
[Delta evidence](spb-random-heartbeat-20260924-130957.json).

September24 12:09:02Beijing heartbeat/user scheduling query: SpB train96
terminal hashes unchanged, final eval admission/run absent in existing queue.
New Qwen same-seed budget is approved but NOT prepared/queued/dispatched;
prior11:45 disk deficit273.89GiB has no authorized capacity solution.
Small-state check only, no repeated resource diagnosis or server mutation.
[Scheduling status evidence](queue-status-query-20260924-120902.json).

September24 11:59:19Beijing read-only heartbeat: eval96 admission/run absent;
hostcompleted[train96], all five terminal hashes and fixed deadline unchanged.
Strict two-root storage831,162,453,514bytes/1TiB,exit0/empty stderr/no failure.
No GPU diagnostics, server changes or dispatch; unchanged wait quiet.
[Delta evidence](spb-random-heartbeat-20260924-115919.json).

September24 11:49:26Beijing read-only heartbeat: eval96 admission/run absent;
hostcompleted[train96], five accepted terminal hashes and shared deadline unchanged.
Strict two-root storage831,162,453,514bytes/1TiB,exit0/empty stderr/no failure.
No repeated GPU/resource diagnostics or server changes;11:45 capacity evidence
remains prior context. Unchanged wait quiet. [Delta evidence](spb-random-heartbeat-20260924-114926.json).

September24 11:45:37Beijing user-requested read-only GPU check: all8A10080GB
utilization0%,memory0MiB,no compute processes;4containers still running.
FreeNVMe810.11GiB remains below unchanged1084GiB gate by273.89GiB;
RAM passes600GiB. SpB train96 completed, eval96 admission/run absent.
No server mutation, gate change, cleanup/migration or new Qwen dispatch.
[Resource evidence](gpu-usage197-20260924-114537.json).

September24 11:36:00Beijing read-only heartbeat: eval96 admission/run absent;
hostcompleted[train96], five terminal hashes and fixed shared deadline unchanged.
Fresh strict two-root sample831,162,453,514bytes/1TiB,exit0/empty stderr/no failure.
No resource re-diagnosis, server mutation or dispatch; unchanged wait quiet.
[Delta evidence](spb-random-heartbeat-20260924-113600.json).

September24 11:32:26Beijing read-only heartbeat: eval96 admission/run still
absent; hostcompleted[train96], five accepted terminal hashes and shared deadline
unchanged. Strict two-root sample831,162,453,513bytes/1TiB,exit0/empty stderr/no
failure. Prior capacity blocker not remeasured; no server mutation or new dispatch.
Unchanged wait quiet. [Delta evidence](spb-random-heartbeat-20260924-113226.json).

September24 11:12:44Beijing read-only heartbeat: eval96 admission/run remain
absent; hostcompleted[train96] and five accepted terminal hashes unchanged.
Fresh strict two-root storage831,162,453,514bytes/1TiB,exit0/empty stderr/no
failure, original shared deadline. No GPU diagnostics or server mutation;
prior capacity blocker not remeasured. Unchanged wait quiet; sole monitor retained.
[Delta evidence](spb-random-heartbeat-20260924-111244.json).

September24 11:05:49Beijing user-requested project/status review: SpB eval96 still
awaits admission; accepted train terminal hashes unchanged and strict storage
sample831,162,453,514bytes/1TiB,exit0/empty stderr. Actual Yuque reading page
still carriesSeptember23 23:06snapshot (Qwen random51/96, SpB waiting-predecessor);
overnight completion/curves/new budget have not been synced there. Read-only
review only, no experiment or Yuque mutation. [Progress and conclusions](project-progress-review-20260924-110549.md).

September24 10:57:18Beijing read-only heartbeat: unchanged eval96 admission wait;
hostcompleted[train96], five accepted terminal hashes unchanged. Fresh strict
two-root sample831,162,453,512bytes/1TiB,exit0/empty stderr/no failure, original
deadline. No new Qwen dispatch or capacity authorization, no server mutation.
Unchanged wait quiet. [Delta evidence](spb-random-heartbeat-20260924-105718.json).

September24 10:48:27Beijing read-only heartbeat: host remains completed[train96],
eval96 admission/run absent, and all five accepted training terminal hashes
unchanged. Existing strict two-root storage831,162,453,514bytes/1TiB,exit0/empty
stderr/no failure; shared deadline unchanged. Prior10:38 disk-capacity blocker
is not remeasured by this small-state monitor. New Qwen same budget approved
but not prepared/queued/dispatched; no capacity-change authority. No server or
monitor mutation; unchanged wait stays quiet.
[Compact evidence](spb-random-heartbeat-20260924-104827.json).

September24 10:38:01Beijing: user explicitly approved the new Qwen same-seed
full rerun budget:792new games/96PPO/48wallh/384GPUh/1TiB, fresh original weights
and own nativeCP2. Budget is approved, but no prepare/queue/dispatch occurred.
Read-only resource recheck:8GPUs idle/no computePIDs; freeNVMe810.11GiB still
fails unchanged1084GiB gate by273.89GiB. Capacity changes require separate
specific authorization; no cleanup/migration/gate change or SpB queue mutation.
New48h clock has not started; existing SpB deadline and sole monitor unchanged.
[Approved budget](qwen-l7same-rerun-budget-20260924.md);
[Approval and compact resource evidence](qwen-l7same-budget-approved-20260924-103801.json).

September24 10:20:34Beijing user-requested diagnosis: all8GPUs idle/no compute
PIDs and759.73GiB RAM pass; freeNVMe810.11GiB fails unchanged1084GiB admission
by273.89GiB. This blocks SpB eval96, unrelated to historical Qwen gradient gaps.
Existing binary64-v1/.17g fix confirmed in83f3530;14CPU precision tests pass.
User selected a new Qwen same-seed full-rerun budget proposal ONLY: proposed792new
games/96PPO/48wallh/384GPUh/1TiB; no launch or SpB gate change authorized.
Old failures/artifacts, deadlines and sole monitor retained.
[Diagnosis](spb-admission-precision-diagnosis-20260924-102034.json);
[budget proposal](qwen-l7same-rerun-budget-20260924.md).

September24 10:09:50Beijing: delivered user-requested four-arm L7 training
curves, 96 observed points per arm, blue per-step wins and orange trailing8 mean.
Main-trajectory wins: Qwen same609/768 (strict historical gradient gaps retained),
SpB same445/768, Qwen random669/768 (14+41+614, excluding failed-run duplicates),
SpB random513/768. Final SpB random eval96 still awaits admission; no ETA,
server mutation or new experiment. Shared deadline unchanged; sole monitor retained.
[Curves, provenance and limitations](l7-four-arm-curves-20260924.md);
[latest compact status](l7-curves-status-20260924-100950.json).

September24 09:53:50Beijing user-requested read-only status: accepted train96
terminal hashes unchanged; eval96 admission/run still absent. Only the final
8-game zero-update paired evaluation remains in this authorized queue.
No scheduled start/ETA is exposed; specific unmet admission resource is unknown.
Existing two-root storage831,162,453,514bytes/1TiB, return0/empty stderr/no failure.
September26 01:22:39 is the unchanged hard deadline, not an ETA. No server changes;
sole monitor retained. [Compact evidence](spb-random-status-query-20260924-095350.json).

September24 09:49:12Beijing read-only heartbeat: eval96 admission and run still
absent; host remains stage-completed[train96] and queue running-unverified/long.
Five accepted train96 terminal receipt hashes unchanged; no training metrics,
console or checkpoint contents reread. Existing two-root storage831,162,453,514bytes/
1TiB, return0/empty stderr/no failure; fixed shared deadline unchanged.
Awaiting unchanged admission (exact unmet resource not established).
Healthy waiting quiet; retain sole monitor, no dispatch/retry/server mutation.
[Compact evidence](spb-random-heartbeat-20260924-094912.json).

September24 09:35:05–09:37:50Beijing read-only acceptance: SpB random train96
completed at09:26:28, exact owned container exited0 at09:26:50; guardian completed,
result=.done=acceptance result and hostcompleted[train96]. Native ownCP2→96 suffix
has94actual PPO/752natural games/505wins and1834/1834valid consumed answers.
All94final metrics finite, positive gradients/update_actor times, invalidAdv0;
94audits and reset2–95seeds match. CP8–96 twelve sets each26nonempty required
entries by stat only. Including accepted short1–2 gives96PPO/768training games/
513wins and1959/1959valid consumed answers; pre/post/final eval excluded.
Eval96 admission/run still absent; waiting unchanged admission, exact unmet resource
not established. Existing two-root storage831,162,453,513bytes/1TiB,exit0/empty stderr/
no failure, sharedSeptember26 01:22:39deadline unchanged. Notify train96 completion
once; retain sole monitor for paired ownCP96 zero-update evaluation. No learning claim.
[Compact terminal evidence](spb-random-train96-complete-20260924-093505.json).

September24 09:25:25Beijing read-only heartbeat: SpB random long returned95/96,
ninety-three resumed PPO phases/744natural games/498wins and1817/1817 consumed
answers valid. Prior returned3–93 plus current94–95 verify updates; finite positive
gradients/update durations and invalidAdv0. Prior pending94 now returned.
All94long seed batches(reset2–95) match, with prior seed/outcome/audit rows unchanged.
Reset95 has7natural closed rows(7wins/0defeats), but no pre-update audit or returned
PPO96; exclude that pending batch from totals. CP8/16/24/32/40/48/56/64/72/80/88 each
have26required nonempty entries by stat only; CP96 absent. Exact container running/
unpaused; no stage terminal or failure. Existing two-root storage767,579,300,247bytes/
1TiB,exit0/empty stderr; fixed deadline unchanged. Healthy progress quiet;
no server mutation/retry or learning claim.
[Compact evidence](spb-random-heartbeat-20260924-092525.json).

September24 09:15:01Beijing read-only heartbeat: SpB random long returned93/96,
ninety-one resumed PPO phases/728natural games/489wins and1780/1780 consumed
answers valid. Prior returned3–91 plus current92–93 verify updates; finite positive
gradients/update durations and invalidAdv0. All92seed batches match, with prior
seed/outcome/audit rows unchanged. Reset93 has4natural closed rows(4wins/0defeats),
but no pre-update audit or returned PPO94; exclude that pending batch from totals.
CP8/16/24/32/40/48/56/64/72/80/88 each have26required nonempty entries by stat only.
Exact container running/unpaused; no stage terminal or failure. Existing two-root
storage767,524,099,384bytes/1TiB,exit0/empty stderr; fixed deadline unchanged.
Healthy progress quiet; no server mutation/retry or learning claim.
[Compact evidence](spb-random-heartbeat-20260924-091501.json).

September24 09:05:00Beijing read-only heartbeat: SpB random long returned91/96,
eighty-nine resumed PPO phases/712natural games/477wins and1745/1745 consumed
answers valid. Prior returned3–88 plus current89–91 verify updates; finite positive
gradients/update durations and invalidAdv0. Prior pending89 now returned.
All90seed batches match, with prior seed/outcome/audit rows unchanged. Reset91 has
no closed outcome-file rows and is pendingstep92, not a returned PPO.
CP8/16/24/32/40/48/56/64/72/80/88 each have26required nonempty entries by stat only.
Exact container running/unpaused; no stage terminal or failure. Existing two-root
storage767,452,928,045bytes/1TiB,exit0/empty stderr; fixed deadline unchanged.
Healthy progress quiet; no server mutation/retry or learning claim.
[Compact evidence](spb-random-heartbeat-20260924-090500.json).

September24 08:55:23Beijing read-only heartbeat: SpB random long returned88/96,
eighty-six resumed PPO phases/688natural games/459wins and1691/1691 consumed
answers valid. Prior returned3–85 plus current86–88 verify updates; finite positive
gradients/update durations and invalidAdv0. Prior pending86 now returned.
All87seed batches match, with prior seed/outcome/audit rows unchanged. Reset88 has
7natural closed rows(6wins/1defeat), but no pre-update audit or returned PPO89;
exclude that pending batch from totals. CP8/16/24/32/40/48/56/64/72/80/88 each have
26required nonempty entries by stat only. Exact container running/unpaused; no stage
terminal or failure. Existing two-root storage767,393,531,269bytes/1TiB,exit0/empty stderr;
fixed deadline unchanged. Healthy progress quiet; no server mutation/retry or learning claim.
[Compact evidence](spb-random-heartbeat-20260924-085523.json).

September24 08:45:15Beijing read-only heartbeat: SpB random long returned85/96,
eighty-three resumed PPO phases/664natural games/440wins and1640/1640 consumed
answers valid. Prior returned3–82 plus current83–85 verify updates; finite positive
gradients/update durations and invalidAdv0. Prior pending83 now returned.
All84seed batches match, with prior seed/outcome/audit rows unchanged. Reset85 has
7natural closed rows(5wins/2defeats), but no pre-update audit or returned PPO86;
exclude that pending batch from totals. CP8/16/24/32/40/48/56/64/72/80 each have
26required nonempty entries by stat only. Exact container running/unpaused; no stage
terminal or failure. Existing two-root storage703,749,268,274bytes/1TiB,exit0/empty stderr;
fixed deadline unchanged. Healthy progress quiet; no server mutation/retry or learning claim.
[Compact evidence](spb-random-heartbeat-20260924-084515.json).

September24 08:34:57Beijing read-only heartbeat: SpB random long returned82/96,
eighty resumed PPO phases/640natural games/425wins and1588/1588 consumed
answers valid. Prior returned3–80 plus current81–82 verify updates; finite positive
gradients/update durations and invalidAdv0. All81seed batches match, with prior
seed/outcome/audit rows unchanged. Reset82 has7natural closed rows(4wins/3defeats),
but no pre-update audit or returned PPO83; exclude that pending batch from totals.
CP8/16/24/32/40/48/56/64/72/80 each have26required nonempty entries by stat only.
Exact container running/unpaused; no stage terminal or failure. Existing two-root
storage703,670,393,466bytes/1TiB,exit0/empty stderr; fixed deadline unchanged.
Healthy progress quiet; no server mutation/retry or learning claim.
[Compact evidence](spb-random-heartbeat-20260924-083457.json).

September24 08:25:00Beijing read-only heartbeat: SpB random long returned80/96,
seventy-eight resumed PPO phases/624natural games/414wins and1552/1552 consumed
answers valid. Prior returned3–77 plus current78–80 verify updates; finite positive
gradients/update durations and invalidAdv0. All79seed batches match, with prior
seed/outcome/audit rows unchanged. Reset80 has no closed outcome-file rows and
is pendingstep81, not a returned PPO. CP8/16/24/32/40/48/56/64/72/80 each have26required
nonempty entries by stat only. Exact container running/unpaused; no stage terminal
or failure. Existing two-root storage703,590,040,681bytes/1TiB,exit0/empty stderr;
fixed deadline unchanged. Healthy progress quiet; no server mutation/retry or learning claim.
[Compact evidence](spb-random-heartbeat-20260924-082500.json).

September24 08:15:01Beijing read-only heartbeat: SpB random long returned77/96,
seventy-five resumed PPO phases/600natural games/399wins and1497/1497 consumed
answers valid. Prior returned3–75 plus current76–77 verify updates; finite positive
gradients/update durations and invalidAdv0. All76seed batches match, with prior
seed/outcome/audit rows unchanged. Reset77 has no closed outcome-file rows and
is pendingstep78, not a returned PPO. CP8/16/24/32/40/48/56/64/72 each have26required
nonempty entries by stat only. Exact container running/unpaused; no stage terminal
or failure. Existing two-root storage639,951,149,773bytes/1TiB,exit0/empty stderr;
fixed deadline unchanged. Healthy progress quiet; no server mutation/retry or learning claim.
[Compact evidence](spb-random-heartbeat-20260924-081501.json).

September24 08:04:58Beijing read-only heartbeat: SpB random long returned75/96,
seventy-three resumed PPO phases/584natural games/388wins and1463/1463 consumed
answers valid. Prior returned3–72 plus current73–75 verify updates; finite positive
gradients/update durations and invalidAdv0. All74seed batches match, with prior
seed/outcome/audit rows unchanged. Reset75 has no closed outcome-file rows and
is pendingstep76, not a returned PPO. CP8/16/24/32/40/48/56/64/72 each have26required
nonempty entries by stat only. Exact container running/unpaused; no stage terminal
or failure. Existing two-root storage639,876,018,752bytes/1TiB,exit0/empty stderr;
fixed deadline unchanged. Healthy progress quiet; no server mutation/retry or learning claim.
[Compact evidence](spb-random-heartbeat-20260924-080458.json).

September24 07:55:02Beijing read-only heartbeat: SpB random long returned72/96,
seventy resumed PPO phases/560natural games/370wins and1412/1412 consumed answers
valid. Prior returned3–69 plus current70–72 verify updates; finite positive
gradients/update durations and invalidAdv0. All71seed batches match, with prior
seed/outcome/audit rows unchanged. Reset72 has no closed outcome-file rows and
is pendingstep73, not a returned PPO. CP8/16/24/32/40/48/56/64/72 each have26required
nonempty entries by stat only. Exact container running/unpaused; no stage terminal
or failure. Existing two-root storage639,797,597,031bytes/1TiB,exit0/empty stderr;
fixed deadline unchanged. Healthy progress quiet; no server mutation/retry or learning claim.
[Compact evidence](spb-random-heartbeat-20260924-075502.json).

September24 07:45:27Beijing read-only heartbeat: SpB random long returned69/96,
sixty-seven resumed PPO phases/536natural games/352wins and1359/1359 consumed
answers valid. Prior returned3–66 plus current67–69 verify updates; finite positive
gradients/update durations and invalidAdv0. All68seed batches match, with prior
seed/outcome/audit rows unchanged. Reset69/pendingstep70 has seven closed
natural games/four wins, without pre-update audit or returned PPO; excluded from
returned-prefix totals. CP8/16/24/32/40/48/56/64 each have26required nonempty entries
by stat only. Exact container running/unpaused; no stage terminal or failure.
Existing two-root storage576,172,541,857bytes/1TiB,exit0/empty stderr; fixed deadline
unchanged. Healthy progress quiet; no server mutation/retry or learning claim.
[Compact evidence](spb-random-heartbeat-20260924-074527.json).

September24 07:34:55Beijing read-only heartbeat: SpB random long returned66/96,
sixty-four resumed PPO phases/512natural games/331wins and1309/1309 consumed
answers valid. Prior returned3–63 plus current64–66 verify updates; finite positive
gradients/update durations and invalidAdv0. Previously pendingstep64 is now
returned and CP64 has26/26required nonempty files by stat. All65seed batches
match, with prior seed/outcome/audit rows unchanged. Reset66/pendingstep67 has
six closed natural games/six wins, without pre-update audit or returned PPO;
excluded from returned-prefix totals. CP8/16/24/32/40/48/56/64 each have26required
nonempty entries by stat only. Exact container running/unpaused; no stage terminal
or failure. Existing two-root storage576,096,902,931bytes/1TiB,exit0/empty stderr;
fixed deadline unchanged. Healthy progress quiet; no server mutation/retry or learning claim.
[Compact evidence](spb-random-heartbeat-20260924-073455.json).

September24 07:25:23Beijing read-only heartbeat: SpB random long returned63/96,
sixty-one resumed PPO phases/488natural games/314wins and1258/1258 consumed
answers valid in the returned prefix. Prior returned3–61 plus current62–63 verify
updates; finite positive gradients/update durations and invalidAdv0. All62seed
batches match. Reset63/pendingstep64 has8natural games/6wins and17/17valid
consumed answers with pre-update audit accept, but no returned PPO; excluded
from prefix totals (all62audits:1275/1275valid). CP8/16/24/32/40/48/56 each have26
required nonempty entries by stat only. CP64 directory currently has0/26 required
nonempty files in this live non-atomic snapshot: pending, not accepted or treated
as terminal failure. Exact container running/unpaused; no stage terminal or failure.
Existing two-root storage512,456,262,904bytes/1TiB,exit0/empty stderr; fixed
deadline unchanged. Healthy progress quiet; no server mutation/retry or learning claim.
[Compact evidence](spb-random-heartbeat-20260924-072523.json).

September24 07:14:57Beijing read-only heartbeat: SpB random long returned61/96,
fifty-nine resumed PPO phases/472natural games/306wins and1222/1222 consumed
answers valid. Prior returned3–58 plus current59–61 verify updates; finite positive
gradients/update durations and invalidAdv0. All60seed batches match; reset61
has no closed outcome-file rows and is pendingstep62, not a returned PPO.
CP8/16/24/32/40/48/56 each have26required nonempty entries by stat only.
Exact container running/unpaused; no stage terminal or failure. Existing two-root
storage512,372,190,885bytes/1TiB,exit0/empty stderr; fixed deadline unchanged.
Healthy progress quiet; no server mutation/retry or learning claim, sole monitor retained.
[Compact evidence](spb-random-heartbeat-20260924-071457.json).

September24 07:04:57Beijing read-only heartbeat: SpB random long returned58/96,
fifty-six resumed PPO phases/448natural games/286wins and1172/1172 consumed
answers valid. Prior returned3–54 plus current55–58 verify updates, including
previously pendingstep55; finite positive gradients/update durations and invalidAdv0.
All57seed batches match. Reset58 has no closed outcome-file rows and is
pendingstep59, not a returned PPO. CP8/16/24/32/40/48/56 each have26required
nonempty entries by stat only. Exact container running/unpaused; no stage
terminal or failure. Existing two-root storage512,286,268,108bytes/1TiB,
exit0/empty stderr; fixed deadline unchanged. Healthy progress quiet;
no server mutation/retry or learning claim, sole monitor retained.
[Compact evidence](spb-random-heartbeat-20260924-070457.json).

September24 06:55:25Beijing read-only heartbeat: SpB random long returned54/96,
fifty-two resumed PPO phases/416natural games/260wins and1104/1104 consumed
answers valid. Prior returned3–52 plus current53–54 verify updates; finite positive
gradients/update durations and invalidAdv0. All53seed batches match; reset54
has five closed natural games/four wins but is pendingstep55, without returned
PPO or pre-update audit, and excluded from returned-prefix totals.
CP8/16/24/32/40/48 each have26required nonempty entries by stat only.
Exact container running/unpaused; no stage terminal or failure. Existing two-root
storage448,646,060,502bytes/1TiB,exit0/empty stderr; fixed deadline unchanged.
Healthy progress quiet; no server mutation/retry or learning claim, sole monitor retained.
[Compact evidence](spb-random-heartbeat-20260924-065525.json).

September24 06:45:08Beijing read-only heartbeat: SpB random long returned52/96,
fifty resumed PPO phases/400natural games/248wins and1068/1068 consumed answers
valid. Prior returned3–49 plus current50–52 verify updates; finite positive
gradients/update durations and invalidAdv0. All51seed batches match; reset52
has no closed outcome-file rows in this snapshot and is pendingstep53, not a
returned PPO. CP8/16/24/32/40/48 each have26required nonempty entries by stat only.
Exact container running/unpaused; no stage terminal or failure. Existing two-root
storage448,563,006,283bytes/1TiB,exit0/empty stderr; fixed deadline unchanged.
Healthy progress quiet; no server mutation/retry or learning claim, sole monitor retained.
[Compact evidence](spb-random-heartbeat-20260924-064508.json).

September24 06:36:14Beijing read-only heartbeat: SpB random long returned49/96,
forty-seven resumed PPO phases/376natural games/231wins and1016/1016 consumed
answers valid. Prior returned3–45 plus current46–49 verify updates, including
previously pendingstep46; finite positive gradients/update durations and invalidAdv0.
All48seed batches match. Reset49 has no closed outcome-file rows and is pendingstep50,
not a returned PPO. CP8/16/24/32/40/48 each have26required nonempty entries by stat only.
Exact container running/unpaused; no stage terminal or failure. Two-root storage
448,489,971,660bytes/1TiB,exit0/empty stderr; fixed deadline unchanged. Initial local
output truncation was resolved by read-only recollection; no storage measurement or
experiment retry. Healthy progress quiet; no server mutation or learning claim.
[Compact evidence](spb-random-heartbeat-20260924-063614.json).

September24 06:25:02Beijing read-only heartbeat: SpB random long returned45/96,
forty-three resumed PPO phases/344natural games/212wins and949/949 consumed
answers valid in the returned prefix. Prior returned3–42 plus current43–45 verify
updates; finite positive gradients/update durations and invalidAdv0. All44seed
batches match. Reset45/pendingstep46 additionally has8natural games/4wins and
16/16valid consumed answers with pre-update audit accept, but no returned PPO;
excluded from prefix totals (all44audits:965/965valid). CP8/16/24/32/40 each
have26required nonempty entries by stat only. Exact container running/unpaused;
no stage terminal or failure. Two-root storage384,838,246,364bytes/1TiB,
exit0/empty stderr; fixed deadline unchanged. Healthy progress quiet; no server
mutation/retry or learning claim, sole monitor retained.
[Compact evidence](spb-random-heartbeat-20260924-062502.json).

September24 06:15:01Beijing read-only heartbeat: SpB random long returned42/96,
forty resumed PPO phases/320natural games/194wins and897/897 consumed answers
valid. Prior returned3–39 plus current40–42 verify updates; finite positive
gradients/update durations and invalidAdv0. All41seed batches match; reset42
has no closed outcome-file rows in this snapshot and is pendingstep43, not a
returned PPO. CP8/16/24/32/40 each have26required nonempty entries by stat only.
Exact container running/unpaused; no stage terminal or failure. Existing two-root
storage384,758,734,097bytes/1TiB,exit0/empty stderr; fixed deadline unchanged.
Healthy progress quiet; no server mutation/retry or learning claim, sole monitor retained.
[Compact evidence](spb-random-heartbeat-20260924-061501.json).

September24 06:04:59Beijing read-only heartbeat: SpB random long returned39/96,
thirty-seven resumed PPO phases/296natural games/177wins and845/845 consumed
answers valid. Prior returned3–36 plus current37–39 verify updates; finite
positive gradients/update durations and invalidAdv0. All38seed batches match;
reset39 has no closed outcome-file rows in this snapshot and is pendingstep40,
not a returned PPO. CP8/16/24/32 each have26required nonempty entries by stat only.
Exact container running/unpaused; no stage terminal or failure. Existing two-root
storage321,112,219,741bytes/1TiB,exit0/empty stderr; fixed deadline unchanged.
Healthy progress quiet; no server mutation/retry or learning claim, sole monitor retained.
[Compact evidence](spb-random-heartbeat-20260924-060459.json).

September24 05:54:55Beijing read-only heartbeat: SpB random long returned36/96,
thirty-four resumed PPO phases/272natural games/158wins and795/795 consumed
answers valid. Prior returned3–33 plus current34–36 verify updates; finite
positive gradients/update durations and invalidAdv0. All35seed batches match;
reset36 has no closed outcome-file rows in this snapshot and is pendingstep37,
not a returned PPO. CP8/16/24/32 each have26required nonempty entries by stat only.
Exact container running/unpaused; no stage terminal or failure. Existing two-root
storage321,025,498,746bytes/1TiB,exit0/empty stderr; fixed deadline unchanged.
Healthy progress quiet; no server mutation/retry or learning claim, sole monitor retained.
[Compact evidence](spb-random-heartbeat-20260924-055455.json).

September24 05:45:03Beijing read-only heartbeat: SpB random long returned33/96,
thirty-one resumed PPO phases/248natural games/144wins and744/744 consumed
answers valid. Prior returned3–31 plus current32–33 verify updates; finite
positive gradients/update durations and invalidAdv0. All32seed batches match;
reset33 has no closed outcome-file rows in this snapshot and is pendingstep34,
not a returned PPO. CP8/16/24/32 each have26required nonempty entries by stat only.
Exact container running/unpaused; no stage terminal or failure. Existing two-root
storage320,956,757,589bytes/1TiB,exit0/empty stderr; fixed deadline unchanged.
Healthy progress quiet; no server mutation/retry or learning claim, sole monitor retained.
[Compact evidence](spb-random-heartbeat-20260924-054503.json).

September24 05:34:56Beijing read-only heartbeat: SpB random long returned31/96,
twenty-nine resumed PPO phases/232natural games/133wins and711/711 consumed
answers valid. Prior returned3–28 plus current29–31 verify updates; finite
positive gradients/update durations and invalidAdv0. All30seed batches match;
reset31 has no closed games and is pendingstep32, not a completed PPO. CP8/16/24
each have26required nonempty entries by stat only. Exact container running/
unpaused; no stage terminal or failure. Existing two-root storage257,315,484,544
bytes/1TiB,exit0/empty stderr; fixed deadline unchanged. Healthy progress quiet;
no server mutation/retry or learning claim, sole monitor retained.
[Compact evidence](spb-random-heartbeat-20260924-053456.json).

September24 05:24:58Beijing read-only heartbeat: SpB random long returned28/96,
twenty-six resumed PPO phases/208natural games/114wins and662/662 consumed
answers valid. Prior returned3–26 plus current27–28 verify updates; finite
positive gradients/update durations and invalidAdv0. All27seed batches match;
reset28 has no closed games and is pendingstep29, not a completed PPO. CP8/16/24
each have26required nonempty entries by stat only. Exact container running/
unpaused; no stage terminal or failure. Existing two-root storage257,246,153,065
bytes/1TiB,exit0/empty stderr; fixed deadline unchanged. Healthy progress quiet;
no server mutation/retry or learning claim, sole monitor retained.
[Compact evidence](spb-random-heartbeat-20260924-052458.json).

September24 05:14:56Beijing read-only heartbeat: SpB random long returned26/96,
twenty-four resumed PPO phases/192natural games/103wins and624/624 consumed
answers valid. Prior returned3–24 plus current25–26 verify updates; finite
positive gradients/update durations and invalidAdv0. All25seed batches match;
reset26 has no closed games and is pendingstep27, not a completed PPO. CP8/16/24
each have26required nonempty entries by stat only. Exact container running/
unpaused; no stage terminal or failure. Existing two-root storage257,188,706,153
bytes/1TiB,exit0/empty stderr; fixed deadline unchanged. Healthy progress quiet;
no server mutation/retry or learning claim, sole monitor retained.
[Compact evidence](spb-random-heartbeat-20260924-051456.json).

September24 05:05:01Beijing read-only heartbeat: SpB random long returned24/96,
twenty-two resumed PPO phases/176natural games/96wins and575/575 consumed
answers valid. Prior returned3–23 plus current23–24 verify updates; finite
positive gradients/update durations and invalidAdv0. All23seed batches match;
reset24's1closed game/1win is pendingstep25 and excluded. CP8/16/24 each have
26required nonempty entries by stat only. Exact container running/unpaused;
no stage terminal or failure. Existing two-root storage257,142,918,942bytes/
1TiB,exit0/empty stderr; fixed deadline unchanged. Healthy progress quiet;
no server mutation/retry or learning claim, sole monitor retained.
[Compact evidence](spb-random-heartbeat-20260924-050501.json).

September24 04:55:06Beijing read-only heartbeat: SpB random long returned23/96,
twenty-one resumed PPO phases/168natural games/92wins and557/557 consumed
answers valid. Prior returned3–20 plus current21–23 verify updates; finite
positive gradients/update durations and invalidAdv0. All22seed batches match;
reset23 has no closed games and is pendingstep24, not a completed PPO. CP8/16
each have26required nonempty entries by stat only. Exact container running/
unpaused; no stage terminal or failure. Existing two-root storage193,500,243,573
bytes/1TiB,exit0/empty stderr; fixed deadline unchanged. Healthy progress quiet;
no server mutation/retry or learning claim, sole monitor retained.
[Compact evidence](spb-random-heartbeat-20260924-045506.json).

September24 04:44:36Beijing read-only heartbeat: SpB random long returned20/96,
eighteen resumed PPO phases/144natural games/80wins and502/502 consumed answers
valid. Prior returned3–18 plus current19–20 verify updates; finite positive
gradients/update durations and invalidAdv0. All19seed batches match; reset20's
4closed games/3wins are pendingstep21 and excluded. CP8/16 each have26required
nonempty entries by stat only. Exact container running/unpaused; no stage
terminal or failure. Existing two-root storage193,431,912,978bytes/1TiB,
exit0/empty stderr; fixed deadline unchanged. Healthy progress quiet; no server
mutation/retry or learning claim, sole monitor retained.
[Compact evidence](spb-random-heartbeat-20260924-044436.json).

September24 04:34:34Beijing read-only heartbeat: SpB random long returned18/96,
sixteen resumed PPO phases/128natural games/70wins and459/459 consumed answers
valid. Prior returned3–17 plus current17–18 verify updates; finite positive
gradients/update durations and invalidAdv0. All17seed batches match; reset18's
6closed games/3wins are pendingstep19 and excluded. CP8/16 each have26required
nonempty entries by stat only. Exact container running/unpaused; no stage
terminal or failure. Existing two-root storage193,356,692,331bytes/1TiB,
exit0/empty stderr; fixed deadline unchanged. Healthy progress quiet; no server
mutation/retry or learning claim, sole monitor retained.
[Compact evidence](spb-random-heartbeat-20260924-043434.json).

September24 04:24:37Beijing read-only heartbeat: SpB random long returned17/96,
fifteen resumed PPO phases/120natural games/64wins and437/437 consumed answers
valid. Prior returned3–15 plus current16–17 verify updates; finite positive
gradients/update durations and invalidAdv0. All16seed batches match; reset17
has no closed games and is pendingstep18, not a completed PPO. CP8/16 each have
26required nonempty entries by stat only. Exact container running/unpaused;
no stage terminal or failure. Existing two-root storage193,300,206,247bytes/
1TiB,exit0/empty stderr; fixed deadline unchanged. Healthy progress quiet;
no server mutation/retry or learning claim, sole monitor retained.
[Compact evidence](spb-random-heartbeat-20260924-042437.json).

September24 04:14:40Beijing read-only heartbeat: SpB random long returned15/96,
thirteen resumed PPO phases/104natural games/56wins and386/386 consumed answers
valid. Prior returned3–14 plus current14–15 verify updates; finite positive
gradients/update durations and invalidAdv0. All14seed batches match; reset15's
7closed games/4wins are pendingstep16 and excluded. CP8 has26required nonempty
entries by stat only. Exact container running/unpaused; no stage terminal or
failure. Existing two-root storage129,678,826,807bytes/1TiB,exit0/empty stderr;
fixed deadline unchanged. Healthy progress quiet; no server mutation/retry or
learning claim, sole monitor retained.
[Compact evidence](spb-random-heartbeat-20260924-041440.json).

September24 04:04:48Beijing read-only heartbeat: SpB random long returned14/96,
twelve resumed PPO phases/96natural games/52wins and361/361 consumed answers
valid. Prior returned3–12 plus current13–14 verify updates; finite positive
gradients/update durations and invalidAdv0. All13seed batches match; reset14
has no closed games and is pendingstep15, not a completed PPO. CP8 has26required
nonempty entries by stat only. Exact container running/unpaused; no stage
terminal or failure. Existing two-root storage129,624,302,895bytes/1TiB,
exit0/empty stderr; fixed deadline unchanged. Healthy progress quiet; no server
mutation/retry or learning claim, sole monitor retained.
[Compact evidence](spb-random-heartbeat-20260924-040448.json).

September24 03:54:39Beijing read-only heartbeat: SpB random long returned12/96,
ten resumed PPO phases/80natural games/43wins and312/312 consumed answers
valid. Prior returned3–11 plus current11–12 verify updates; finite positive
gradients/update durations and invalidAdv0. All11seed batches match; reset12's
5closed games/3wins are pendingstep13 and excluded. CP8 has26required nonempty
entries by stat only. Exact container running/unpaused; no stage terminal or
failure. Existing two-root storage129,559,988,464bytes/1TiB,exit0/empty stderr;
fixed deadline unchanged. Healthy progress quiet; no server mutation/retry or
learning claim, sole monitor retained.
[Compact evidence](spb-random-heartbeat-20260924-035439.json).

September24 03:44:55Beijing read-only heartbeat: SpB random long returned11/96,
nine resumed PPO phases/72natural games/39wins and290/290 consumed answers
valid. Prior returned3–9 plus current9–11 verify updates; finite positive gradients/
update durations and invalidAdv0. All10seed batches match; reset11 has no closed
games and is pendingstep12, not a completed PPO. CP8 has26required nonempty
entries by stat only. Exact container running/unpaused; no stage terminal or
failure. Existing two-root storage129,493,060,226bytes/1TiB,exit0/empty stderr;
fixed deadline unchanged. Healthy progress quiet; no server mutation/retry or
learning claim, sole monitor retained.
[Compact evidence](spb-random-heartbeat-20260924-034455.json).

September24 03:34:31Beijing read-only heartbeat: SpB random long returned9/96,
seven resumed PPO phases/56natural games/29wins and240/240 consumed answers
valid. Prior returned3–8 plus current8–9 verify updates; finite positive gradients/
update durations and invalidAdv0. All8seed batches match; reset9's7closed games/
3wins are pendingstep10 and excluded. CP8 still has26required nonempty entries
by stat only. Exact container running/unpaused; no stage terminal or failure.
Existing two-root storage129,415,933,251bytes/1TiB,exit0/empty stderr; fixed
deadline unchanged. Healthy progress quiet; no server mutation/retry or learning
claim, sole monitor retained.
[Compact evidence](spb-random-heartbeat-20260924-033431.json).

September24 03:24:45Beijing read-only heartbeat: SpB random long returned8/96,
six resumed PPO phases/48natural games/23wins and218/218 consumed answers
valid. Prior returned3–7 plus current7–8 verify updates; finite positive gradients/
update durations and invalidAdv0. All7seed batches match; reset8's6closed games/
5wins are pendingstep9 and excluded. CP8 has26required nonempty entries by stat,
contents unread. Exact container running/unpaused; no stage terminal or failure.
Existing two-root storage129,370,832,389bytes/1TiB,exit0/empty stderr; fixed
deadline unchanged. Healthy progress quiet; no server mutation/retry or learning
claim, sole monitor retained.
[Compact evidence](spb-random-heartbeat-20260924-032445.json).

September24 03:15:59Beijing read-only heartbeat: SpB random long returned7/96,
five resumed PPO phases/40natural games/18wins and192/192 consumed answers
valid. Prior returned3–6 plus current6–7 verify updates; finite positive gradients/
update durations and invalidAdv0. All6seed batches match; reset7's2closed games/
2wins are pendingstep8 and excluded. Exact container running/unpaused; no stage
terminal, CP8 or failure. Existing two-root storage65,748,149,714bytes/1TiB,
exit0/empty stderr; fixed deadline unchanged. Healthy progress quiet; no server
mutation/retry or learning claim, sole monitor retained.
[Compact evidence](spb-random-heartbeat-20260924-031559.json).

September24 03:04:41Beijing read-only heartbeat: SpB random long returned6/96,
four resumed PPO phases/32natural games/13wins and161/161 consumed answers
valid. Current returned5–6 plus prior3–4 receipts verify updates; finite positive
gradients/update durations, invalidAdv0. All5seed batches match; reset6 is
pendingstep7, not completed PPO. Exact container running/unpaused; no terminal,
CP8 or failure. Existing two-root storage65,642,958,333bytes/1TiB,exit0/empty
stderr, fixed deadline unchanged. Healthy progress quiet; no server mutation,
retry or learning claim; sole monitor retained.
[Compact evidence](spb-random-heartbeat-20260924-030441.json).

September24 02:54:41Beijing read-only heartbeat: SpB random long returned5/96,
three resumed PPO phases/24natural games/10wins and129/129 consumed answers
valid. Priorstep3 plus current bounded-tail4–5 verify updates; gradients and
update durations finite positive, invalidAdv0. All4seed batches match; reset5's
3closed games/2wins are pendingstep6 and excluded. Exact container running/
unpaused; no terminal/CP8/failure. Existing two-root storage65,564,506,624bytes/
1TiB,exit0/empty stderr, fixed deadline unchanged. Healthy progress quiet;
no server mutation/retry/learning claim; sole monitor retained.
[Compact evidence](spb-random-heartbeat-20260924-025441.json).

September24 02:45:46Beijing read-only heartbeat: SpB random long returned4/96,
two resumed PPO phases/16natural games/4wins and102/102 consumed answers valid.
Returned3–4 gradients/update durations are finite positive, invalidAdv0; all
three registered seed batches match. Reset4's two closed games are pendingstep5,
not another PPO. Exact container running/unpaused; no terminal/CP8/failure.
Existing exact two-root storage65,419,765,639bytes/1TiB,exit0/empty stderr;
original deadline unchanged. Healthy progression quiet, sole monitor retained;
no server mutation/retry or learning claim.
[Compact evidence](spb-random-heartbeat-20260924-024546.json).

September24 02:39:12–02:40:40Beijing read-only heartbeat: SpB random long
returned global3 (one resumed PPO; three including accepted short). Actual
gradient33.0792840719223/update_actor193.50770314224064seconds/invalidAdv0;
reset2 closed8 natural games/1win and consumed62/62 valid answers. Reset3
has7 closed natural games/2wins at02:39:12, not another completed PPO.
Both seed batches match privateRandom0. The returnedstep3 line was outside
the initial1MiB tail and verified in a fixed2MiB tail; no full log or checkpoint
contents read. No final metrics/result/acceptance or CP8 yet; exact container
running/unpaused. Existing two-root storage65,256,014,929bytes/1TiB,
exit0/empty stderr, no failure; original deadline unchanged. Healthy progress
stays quiet; first SpB PPO was already notified. No server mutation/retry;
sole monitor retained, no learning-gain claim.
[Compact evidence](spb-random-heartbeat-20260924-023912.json).

September24 02:25:30Beijing read-only heartbeat: SpB random long remains in
the first resumed global3/reset2 batch;7 natural games closed(1win/6defeats),
not a completed8-game batch or returned PPO. No audit/result/acceptance yet.
Exact owned container running/unpaused; native CP2 receipt and reset2 seeds
match. Existing two-root storage64,803,870,541bytes/1TiB,exit0/empty stderr,
no failure; fixed deadline unchanged. Healthy progress stays quiet; no server
mutation, duplicate event or retry; sole monitor retained.
[Compact evidence](spb-random-heartbeat-20260924-022530.json).

September 24 02:15:46 Beijing: **SpB random short fully accepted; native CP2
long training has started**. Post finished 02:11:32 with 8 natural games,
4 wins, 0 updates and 52/52 valid consumed answers; result=.done=acceptance,
exact container exited0 and guardian completed. Paired pre4/8 → CP2post4/8
does not demonstrate gain. Short host/state completed [pre,train2,post]; the
native full-state prefix contract, driver/rank RNG CPU checks and actual-parent
readiness passed. Long container started 02:11:52, actual ownCP2 load returned,
global2/reset2 and next seeds36,17,96,12,79,32,68,90 match. All eight SC2 planner
boundaries and matching worker support banners observed; no returned long PPO
yet. Original shared September26 01:22:39 deadline and budgets unchanged;
existing two-root storage64,643,411,659bytes/1TiB, exit0/empty stderr, no failure.
No monitor-triggered server mutation or retry; sole monitor retained.
[Short completion and native long-start evidence](spb-random-short-complete-long-start-20260924-021546.json).

September24 02:05:53–02:06:50Beijing: **SpB random train2 completed and accepted;
ownCP2 zero-update post is running**. Two returned PPO phases/16natural games,
8wins,125/125consumed answers valid;125plans/1,633queue entries/927local commands.
Both gradients and update durations finite positive, invalid advantage maxima0;
result=.done=acceptance result, clean83f3530/world8/binary64-v1. Exact train2
container exited0 and guardian completed under the original deadline. CP2 has
26/26required nonempty file entries, contents unread. Post started02:00:35,
actual CP2 load returned/0updates, original8evaluation seeds and explicit
rank/seed/CPU-CUDA RNG fields all pair with pre; worker support banners match.
No post result/acceptance, native parent-readiness or long dispatch yet.
Existing two-root storage64,536,083,382bytes/1TiB,exit0/empty stderr,no failure.
No server mutation/retry/budget change; notify train2 completion only, not first
PPO again or a learning-gain claim. Unique monitor retained.
[Train2 terminal and post-start evidence](spb-random-train2-complete-20260924-020553.json).

September24 01:58:25Beijing: **SpB random first actual PPO confirmed**, returned
step1 gradient119.08253415425618, update_actor168.143536365591seconds,
invalid_advantage_max0. Its first independent-seed batch closed8 natural games,
5 wins,46/46 valid consumed answers. Second batch also closed8games/3wins and
its79/79-consumed pre-update audit passed, but no returnedstep2 was observed;
do not count that audit as a second update. Train2 still running/unpaused,
clean83f3530/world8/binary64-v1, hostcompleted[pre]; no train2 result/acceptance,
post, CP2 parent-readiness or long dispatch yet. Bounded3MiB tail included the
earlierstep1 line absent from the preceding1MiB tail. Existing exact two-root
storage850,883,079bytes/1TiB,exit0/empty stderr,no failure; fixed deadline unchanged.
Notify first PPO once, retain unique monitor; no server mutation/retry or gain claim.
[First actual PPO evidence](spb-random-first-ppo-20260924-015825.json).

September24 01:45:50Beijing read-only heartbeat: SpB random remains freshtrain2,
exact owned container running/unpaused, host completed[pre]. Pendingstep1 audit
accepted46/46 consumed answers; **no returned PPO observed** in the bounded1MiB
tail, so the audit is not counted as an update. No train2 result/acceptance,
post or long dispatch/native-parent gate yet. Exact two-root storage629,421,601
bytes/1TiB measuredexit0/empty stderr, no failure; original deadline unchanged.
Healthy progress stays quiet; no server mutation/retry or duplicate event.
[Compact evidence](spb-random-heartbeat-20260924-014550.json).

September 24 01:39:18 Beijing: **SpB random pre completed and accepted;
fresh train2 is running**. Pre ended01:32:50 with8 natural games/4 wins/4 defeats,
zero updates and49/49 valid consumed answers (49 plans/607 queue entries/
362 local Depot/Marine commands). Result=.done=acceptance result,
clean83f3530/world8/binary64-v1, exact owned container exited0 and guardian
completed under the original deadline. Host supervision completed[pre] and
automatically started train2 at01:33:01; its registered first independent-seed
batch is49,97,53,5,33,65,62,51. No returned PPO was observed in the bounded
train2 tail; short acceptance and native CP2 parent-readiness remain pending.
Existing exact two-root storage receipt307,702,761bytes/1TiB, exit0/empty stderr,
no failure. Shared deadlineSeptember26 01:22:39Beijing unchanged; no server
mutation/retry. Pre completion is the new notification; prior Qwen completion
and SpB first GPU/SC2 are not repeated. Unique monitor retained.
[Pre completion evidence](spb-random-pre-complete-20260924-013918.json).

September 24 01:28–01:30 Beijing: **Qwen random native CP8 continuation and
paired CP96 evaluation completed and accepted; SpB random has started**.
Train suffix9..96 contains88 actual PPO updates,704 natural games/614 wins
(87.22%),2,225/2,225 valid consumed answers,88 accepted audits/exact seed batches,
and11 new CP16..96 sets with26 required nonempty files each (contents unread).
Eval96 is8/8 natural wins,0 updates,24/24 valid consumed answers, actual CP96
load returned, and all8 rank/seed/CPU-CUDA RNG hashes pair with its own random
CP2post. That baseline was also8/8: saturated8→8 is **not demonstrated gain**.
Both result=.done=acceptance result, clean3415428/world8/binary64-v1,
host queue/state/guardian completed and exact owned containers exited0.
The frozen SpB controller ran the original Qwen verifier withwrite=False for
both stages before its passed predecessor receipt. This monitor independently
checked compact terminal/metric/load/seed/RNG receipts and CP inventory, not
full logs or checkpoint contents. Old failed r4 and CP2 ancestry restrictions
remain unchanged;614/704 is the new suffix, not the complete1..96 total.

SpB83f3530 automatically dispatched pre at01:22:39; actual worker NCCL,
canonical/no-thinking banners and SC2 planner/terminal boundaries were observed.
It remains zero-update pre, not short acceptance or PPO completion. The fixed
whole-arm deadline isSeptember26 01:22:39Beijing (48h upper bound, not ETA),
792 new games/96PPO/384GPUh/1TiB, shared by short/long/eval. Qwen's final exact
15-root arm/suite totals are650,655,840,531/1,481,975,072,396bytes; SpB's latest
two-root receipt is195,029,243bytes, all measured exit0/empty stderr within limits.
No server mutation or rerun; unique10-minute monitor retained for SpB.
[Completion and first SpB GPU/SC2 evidence](qwen-random-complete-spb-random-start-20260924.json).

September 24 01:13:35 Beijing read-only heartbeat: returned 94/96, 688 natural
games / 603 wins in the native CP8 suffix, 2,172/2,172 consumed answers valid;
87 registered seed batches match. Reset94 is only the next batch. Bounded
console returned 89–94 satisfies finite positive gradient/update-time and
nonpositive invalid-credit checks; CP16..88 each has 26 required nonempty
entries, contents unread. Owned container running/unpaused; no terminal or
failure receipt. Exact 15-root arm/suite totals are 600,758,749,356 /
1,432,077,809,156 bytes, exit 0 / empty stderr within unchanged limits. SpB
remains waiting-predecessor with no dispatch. Healthy progress stays quiet;
no server mutation/retry/learning claim, unique monitor retained.
[Compact evidence](qwen-random-cp8-heartbeat-20260924-011335.json).

September 24 01:05:40 Beijing read-only heartbeat: returned 91/96, 664 natural
games / 583 wins in the native CP8 suffix, 2,088/2,088 consumed answers valid;
84 registered seed batches match. Next-step outcomes/audit are excluded until
PPO return. Bounded console returned 87–91 satisfies finite positive gradient/
update-time and nonpositive invalid-credit checks; CP16..88 each has 26 required
nonempty entries, contents unread. Owned container running/unpaused; no terminal
or failure receipt. Exact 15-root arm/suite totals are 600,694,028,089 /
1,432,013,259,950 bytes, exit 0 / empty stderr within unchanged limits. SpB
remains waiting-predecessor with no dispatch. Healthy progress stays quiet;
no server mutation/retry/learning claim, unique monitor retained.
[Compact evidence](qwen-random-cp8-heartbeat-20260924-010540.json).

September 24 00:53:31 Beijing read-only heartbeat: returned 88/96, 640 natural
games / 565 wins in the native CP8 suffix, 2,000/2,000 consumed answers valid;
81 registered seed batches match. Bounded console returned 81–88 satisfies
finite positive gradient/update-time and nonpositive invalid-credit checks;
CP16..88 each has 26 required nonempty entries, contents unread. Owned container
running/unpaused; no terminal or failure receipt. Exact 15-root arm/suite totals
are 600,618,698,498 / 1,431,937,930,362 bytes, exit 0 / empty stderr within
unchanged limits. SpB remains waiting-predecessor with no dispatch. Healthy
progress stays quiet; no server mutation/retry/learning claim, unique monitor retained.
[Compact evidence](qwen-random-cp8-heartbeat-20260924-005331.json).

September 24 00:43:36 Beijing read-only heartbeat: returned 86/96, 624 natural
games / 552 wins in the native CP8 suffix, 1,949/1,949 consumed answers valid;
79 registered seed batches match. Bounded console returned 77–86 satisfies
finite positive gradient/update-time and nonpositive invalid-credit checks;
CP16..80 each has 26 required nonempty entries, contents unread. Owned container
running/unpaused; no terminal or failure receipt. Exact 15-root arm/suite totals
are 550,703,138,762 / 1,382,022,370,625 bytes, exit 0 / empty stderr within
unchanged limits. SpB remains waiting-predecessor with no dispatch. Healthy
progress stays quiet; no server mutation/retry/learning claim, unique monitor retained.
[Compact evidence](qwen-random-cp8-heartbeat-20260924-004336.json).

September 24 00:33:44 Beijing read-only heartbeat: returned 82/96, 592 natural
games / 526 wins in the native CP8 suffix, 1,848/1,848 consumed answers valid;
75 seed batches match. Bounded console returned 74–82 satisfies finite positive
gradient/update-time and nonpositive invalid-credit checks; CP16..80 each has
26 required nonempty entries, contents unread. Owned container running/unpaused;
no terminal or failure receipt. Exact 15-root arm/suite totals are
550,633,824,121 / 1,381,953,055,985 bytes, exit 0 / empty stderr within unchanged
limits. SpB remains waiting-predecessor with no dispatch. Healthy progress stays
quiet; no server mutation/retry/learning claim, unique monitor retained for both arms.
[Compact evidence](qwen-random-cp8-heartbeat-20260924-003344.json).

September24 00:23:20Beijing read-only heartbeat: returned79/96,568natural
games/504wins in the nativeCP8 suffix,1,772/1,772consumed answers valid;72seed
batches match. Bounded console returned69–79 satisfies finite positive gradient/
update-time and nonpositive invalid-credit checks; CP16..72each26required
nonempty entries, contents unread. Owned container running/unpaused; no terminal
or failure receipt. Exact15-root arm/suite500,700,862,176/1,332,020,094,040bytes,
exit0/empty stderr within unchanged limits. SpB remainswaiting-predecessor/no
dispatch. Healthy progress stays quiet; no server mutation/retry/learning claim,
unique monitor retained for both arms.
[Compact evidence](qwen-random-cp8-heartbeat-20260924-002320.json).

September24 00:16:07Beijing read-only heartbeat: returned76/96,544natural
games/482wins in the nativeCP8 suffix,1,700/1,700consumed answers valid;69seed
batches match. Bounded console returned67–76 satisfies finite positive gradient/
update-time and nonpositive invalid-credit checks; CP16..72each26required
nonempty entries, contents unread. Owned container running/unpaused; no terminal
or failure receipt. Exact15-root arm/suite500,635,959,858/1,331,955,191,721bytes,
exit0/empty stderr within unchanged limits. SpB remainswaiting-predecessor/no
dispatch. Healthy progress stays quiet; no server mutation/retry/learning claim,
unique monitor retained for both arms.
[Compact evidence](qwen-random-cp8-heartbeat-20260924-001607.json).

September24 00:03:26Beijing read-only heartbeat: returned71/96,504natural
games/446wins in the nativeCP8 suffix,1,574/1,574consumed answers valid;64seed
batches match. Bounded console returned62–71 satisfies gradient/update-time/
invalid-credit checks; CP16..64each26required nonempty entries, contents unread.
Owned container running/unpaused; no terminal/failure receipt. Exact15-root
arm/suite450,690,021,654/1,282,004,438,481bytes, exit0/empty stderr within
unchanged limits. SpB remainswaiting-predecessor/no dispatch. Healthy progress
stays quiet; no server mutation/retry/learning claim, unique monitor retained.
[Compact evidence](qwen-random-cp8-heartbeat-20260924-000326.json).

September23 23:53:36Beijing read-only heartbeat: Qwen returned68/96,480natural
games/424wins in the nativeCP8 suffix,1,500/1,500consumed answers valid;61seed
batches match. Bounded console returned59–68 satisfies finite positive gradient/
update-time and nonpositive invalid-credit checks. CP16..64each26required
nonempty entries, contents unread. Owned container running/unpaused, no final
result or failure receipt. Exact15-root arm/suite450,613,557,372/
1,281,932,789,237bytes, exit0/empty stderr within unchanged limits. SpB remains
waiting-predecessor/no dispatch. Healthy progress: no new notification,
server mutation, retry or learning claim; unique monitor retained for both arms.
[Compact read-only evidence](qwen-random-cp8-heartbeat-20260923-235336.json).

September23 23:48:52Beijing user-requested read-only status: **Qwen per-game
random continuation returned66/96**, with464natural games/408wins(87.93%)
in this CP8 recovery segment and1,452/1,452audited consumed answers legal.
59registered seed batches match; bounded console confirms returned57–66 with
finite positive gradients/update durations and invalid advantage max0. CP16
through64each have26required nonempty file entries, contents unread. Exact
owned container remains running/unpaused; no terminal or storage-failure
receipt. Exact15-root arm/suite measured450,567,919,878/1,281,887,152,359bytes,
exit0/empty stderr within unchanged limits. SpB independent-seed successor is
stillwaiting-predecessor with no dispatch. At recent wall-clock pace, remaining
30steps plus evaluation/acceptance are conditionally about1.5–2hours, roughly
September24 01:20–01:50; not a guarantee and original cutoff unchanged.
No server mutation, rerun, new experiment or learning-gain claim.
[Compact evidence and ETA assumptions](qwen-random-progress-20260923-234852.json).

September23 23:41Beijing: user-requested **whole Yuque article reorganization**
published and read back in Safari. Replaced the chronological/duplicated opening
with eight sections: current overview, metric interpretation, verified version/
commit index, experimental rationale, L7 results, common configuration, limits,
and evidence. Preserved all five original images, historical failures and six
Qwen gradient gaps; distinguished runtime, engineering change and result archive.
Corrected early Qwen SC2-SFT vs original generic SpB, and stale SpB-random
budget-pending text to approved/waiting-predecessor. Published23heading texts,
27unique commit links and five original image URLs read back successfully.
[Article source](yuque-project-overview-20260923.md),
[publication/validation receipt](yuque-project-overview-publication-20260923.json).
No experiment rerun, remote mutation, automation change or sharing change.

The interrupted23:06:52Beijing read-only snapshot is retained with this document:
Qwen nativeCP8 continuation returned51/96,43newPPO/344natural games/302wins,
1082/1082consumed answers legal;44registered seed batches match. CP16/24/32/
40/48each26required nonempty entries; owned container running/unpaused and no
terminal/failure receipt. Exact15-root arm/suite measurement350,542,478,126/
1,181,861,709,989bytes, exit0/empty stderr within original limits. New SpB random
stillwaiting-predecessor/no dispatch. This is the article's explicit status
timestamp, not a claim of current terminal acceptance.
[Compact read-only evidence](qwen-random-progress-20260923-230652.json).

September23 22:56Beijing [SpB L7 per-game independent seed short+96](spb-l7-random197.md)
single queue is installed **after current Qwen CP8 train+eval full acceptance**:
original SpB,792new games/96PPO,48wallh/384GPUh/1TiB including short. At22:58
actual `waiting-predecessor`,completed[], no suite/part dispatch, no SpB GPU.
261model/controller+71actual-host CPU tests passed/zero skipped/CUDAfalse;
five actual dry launchers/Hydra and34source hashes passed; three CPU containers
exited0/DeviceRequestsnull. New runtime83f3530. Current Qwen returned47/96,
still train96, original deployment/deadline unchanged. Existing unique monitor
now covers both arms, healthy waiting quiet. [Actual queue/CPU evidence](spb-random-queue-20260923.json).

September23 22:29:40Beijing read-only heartbeat: returned37/96,29newPPO/
232natural games/198wins,737/737consumed answers valid;30seed batches match,
CP16/24/32each26required entries. Exact container running/unpaused, no terminal
or failure receipt.15-root storage250,549,488,531/1,081,868,720,399bytes remains
within unchanged limits, exit0/empty stderr. Healthy progress stays quiet;
no remote mutation or learning claim. [Evidence](qwen-random-cp8-heartbeat-20260923-222940.json).

September23 22:19:59Beijing read-only heartbeat: Qwen CP8 continuation returned
33/96,25newPPO/200natural games/172wins and630/630consumed answers valid.
All26registered seed batches match; CP16/24/32each26required nonempty entries.
Owned container running/unpaused; no terminal/failure receipts. Exact15-root
arm/suite measured250,479,851,439/1,081,799,089,795bytes, exit0/empty stderr,
within unchanged limits. Healthy progress remains quiet; no server mutations
or new learning claim. [Compact evidence](qwen-random-cp8-heartbeat-20260923-221959.json).

September23 22:13–22:14Beijing user-requested ETA: Qwen independent-seed
continuation returned31/96; recent10steps average165.419seconds,65remaining
outer phases imply2.99h training. Allowing remaining saves, variance and paired
eval/loading/acceptance, conditional finish is about3–4h later, September24
01:15–02:15Beijing. Not a guarantee; original September25 11:58:40deadline
unchanged. Initial sampler pause was followed by verified running/unpaused
same container and successful fresh storage receipts; no manual intervention.
The interrupted22:11heartbeat is also retained:30/96,176natural games/150wins,
557/557consumed answers valid, exact23seed batches and CP16/24inventories.
[Timing/health evidence and estimate assumptions](qwen-random-cp8-eta-20260923-221302.json).

September23 22:04Beijing read-only synthesis: current Qwen independent-seed
continuation returned27/96,19new PPO phases with481/481audited consumed
answers valid; final evaluation pending. SpB same96 completed with11,313/11,313
legal training answers, but pairedCP2→CP96 evaluation3/8→2/8; Qwen same7/8→5/8
also does not establish improvement. Largest verified progress is the controlled,
traceable long-running action/RL pipeline, not strategic or architecture superiority.
No experiment changes; SpB random remains budget-pending, not dispatched.
[Experiment purposes and evidence limits](experiment-progress-summary-20260923.md),
[fresh compact status](qwen-random-cp8-status-20260923-220401.json).

September23 21:55:02–21:55:43Beijing read-only heartbeat: **Qwen CP8 recovery
returned step24/96**,16newPPO/128natural games/112wins and406/406consumed
answers valid. Prior committed steps9–14 plus current bounded-tail15–24 prove
returned updates; all17registered batches reset8..24 match private Random0.
NewCP16/24 inventories each have26nonempty required entries (contents unread).
Exact stage container running/unpaused; no terminal result, acceptance or
storage-failure receipt. Existing15-root arm/suite storage samples are
200,428,630,860/1,031,747,862,730bytes, exit0/empty stderr within1/2TiB.
Original clocks/budgets unchanged; no remote writes, retries or new learning
claim. Healthy progress stays quiet; unique197-qwen-cp8 retained.
[Compact evidence and collector caveats](qwen-random-cp8-heartbeat-20260923-215502.json).

September23 21:48Beijing: appended the user-requested **SpB L7same complete96
settings/results/blue-orange curve** to the existing Yuque SCII日志 in Safari.
Published reading view, both tables, full chart and immutable GitHub provenance
links were verified; earlier D/C/Qwen history and sharing permissions retained.
The report distinguishes100%constrained legality from strategic improvement:
445/768training wins, pairedCP2 3/8 → CP96 2/8, only8pairs. No server actions,
reruns or new experiments. [Local report](spb-l7same-yuque-20260923.md),
[publication receipt](spb-l7same-yuque-publication-20260923.json).

September23 21:26:28Beijing: **Qwen CP8 recovery has returned steps9–14**, six
actual PPO updates/48natural games/42wins;162/162consumed answers valid.
All six binary64 gradients are finite positive, invalid advantage max0 and
update_actor durations positive. Initial returned step9 is now GPU/PPO evidence,
not merely a pre-update audit. The queue remains train96/running-unverified.
User explicitly approved the new single10minute heartbeat `197-qwen-cp8`;
created ACTIVE, quiet on healthy progress, no restart or expanded budget.
First native resume/SC2/PPO events have been notified and must not be repeated.
[Compact returned-update evidence](qwen-random-cp8-first-ppo-20260923.json).

September23 21:24:20Beijing: user-requested **complete SpB L7same1–96 curve**
was refreshed read-only from both finalized metrics files, retaining every
metric key.96continuous steps/768natural games/445wins, last8steps29/64,
11,313/11,313consumed answers valid. Paired evaluations stay separate:
pre4/8 → CP2post3/8 → CP96eval2/8, no demonstrated improvement.
Blue observations/orange trailing8step mean retained; no rerun/server mutation.
[Complete local snapshot](spb-l7same-complete-20260923-data.json),
[chart provenance and regeneration](spb-l7same-curve-20260923.md#completed-196-snapshot--september23-212420beijing).

September23 21:08:43Beijing: **Qwen L7random native CP8 continuation r2 is
actually running**. Frozen3415428;236Linux model/startup +71host tests passed,
0skips; two CPU containers exit0/GPUrequestsnull. Single dispatch21:06:39,
actual GPU model/optimizer/dataloader/native RNG load returned,global8/reset8,
next8,24,72,28,30,18,69,57. Correct worker support banners and actual serialized
SC2 startup observed; all-eight-first-batch/PPO completion still pending in
this snapshot. Fixed September25 11:58:40Qwen cutoff and all budgets unchanged.
No extra arms or repeats of completed experiments. [Launch](qwen-random-cp8-launch-20260923.json),
[actual restore](qwen-random-cp8-gpu-20260923.json), [protocol and retained CPU failure](sc2-startup-race197.md).

September23 user explicitly approved **own native Qwen-random CP8→96 plus8eval,
48additional slots**, without deadline/GPU/storage extension. New single-run
controller is being prepared on `codex/fix-sc2-startup-port-race`;88new updates,
704training+8eval games, no other arms. Original Qwen cutoff September25
11:58:40 and suite September26 19:06:02 remain fixed. Local13new contract/launcher
tests passed. CPU-only r1 passed native-state/two Hydra gates, but its combined
regression entry incorrectly ran host-only tests in a container; that preparation
is retained without any GPU dispatch. r2 separates host/container test execution
and includes both old preparation roots in unchanged budgets. Full Linux gates
and actual GPU proof remain pending. [Authorization, provenance and gates](sc2-startup-race197.md#september23-explicit-approval--one-native-cp8-recovery).

September23 20:30Beijing approved diagnosis/repair: **queue remains stopped**.
Two failing SC2 workers logged the same API port33471 within36ms; frozen
dependency inspection supports a pick/close/bind race hypothesis, not a uniquely
proven root cause. New branch `codex/fix-sc2-startup-port-race` from `7bba013`
contains a candidate that serializes startup until first observation (eight live
games retained), fails closed on admission timeout and releases leases on error.
9startup +34related CPU tests,34source hashes and shell syntax passed. No GPU
deployment/restart/new monitor. CP8 has26required nonempty file entries, but
native restoration remains unverified. CP8→96 would repeat40completed games
and replace8failed dispatched slots:48extra slots need approval; original
time/GPU/storage limits cannot reset. [Diagnosis and continuation proposal](sc2-startup-race197.md),
[compact evidence](sc2-startup-race-diagnosis-20260923.json).

Final refresh September23 17:47Beijing: **Qwen L7random long failed at
12:26:16Beijing after returned step13**; host queue/part failed, result=.done
failed/exit1 and exact container exited1/OOMfalse. It completed11newPPO,
88natural games(76wins),324/324consumed answers valid. Failure surfaced during
next SC2 reset: `ServerDisconnectedError` while connecting the SC2 WebSocket,
then `SC2 reset failed after retries`; underlying disconnection cause remains
unknown. This is not evidence of answer-legality collapse. No terminal eval,
no automatic retry, no new run or deadline reset. Only CP8 directory exists,
not a verified resume authorization. [Failure/handoff evidence](l7-qwen-random-failure-20260923.json).
SpB successful96+eval result below stands. The single `197-l7-r4` monitor
was deleted after failure handoff; diagnosis/fix/restart needs user direction.
SpB-random remains planned pending length/budget confirmation.

Earlier September23 12:17:42Beijing stage transition (superseded by failure above): **SpB L7same short+96 and
paired terminal evaluation completed; Qwen L7random long has automatically
started and returned global step9**. SpB continuation94PPO/752natural games
(440wins) passed binary64 gradient/audit/seed/12CP checks; including short,
96training batches have445/768wins(57.94%). Its paired CP2 post3/8 → CP96
eval2/8 (pre4/8) shows no demonstrated improvement; eight pairs are too small
to assert stable degradation. Eval33/33consumed answers valid,0updates;
result=.done, clean9cb291/world8 and both stage containers exited0.
Qwenrandom11:58:40 dispatch loaded its own accepted CP2 with the documented
non-bitwise limitation; independent seed batch36,17,96,12,79,32,68,90 and
actual returned step9 PPO confirmed. Fixed Qwen cutoff September25 11:58:40,
suite September26 19:06:02; neither is an ETA. No remote mutations/retries.
[Compact receipt and source hashes](l7-spb-complete-qwen-random-start-20260923.json),
[completion interpretation](l7-host-continuation197.md#september23-spb-completion-and-qwen-random-start).
Stage/first-event evidence is retained; do not replay completed experiments.
The later failure supersedes this snapshot's running state.

September23 10:23:46Beijing chart refresh: **SpB L7same88/96completed**,
416/704training wins(59.1%), last8steps35/64(54.7%),10,963/10,963actual
consumed answers valid. Existing successor remains Qwen L7random ownCP2→96,
undispatched; SpB random remains budget-pending/planned only. Training fluctuation
is not a controlled learning-gain result. [Full small-data snapshot](spb-l7same-20260923-102346-data.json),
[chart provenance and regeneration](spb-l7same-curve-20260923.md).
Only read-only small receipts/4MiB log tail; no remote mutation/new dispatch.

User status recheck September23 10:15:36Beijing: **87/96completed; step88
in SC2; Qwenrandom long still queued/undispatched**. Last three returned batches
have100%valid actions and finite positive gradients, with1/8,3/8,6/8training wins
across different seeds (not a learning-trend test). Recent mean625.48s/step gives
a conditional1.5–2.5h remaining including CP/eval/acceptance, roughly11:45–12:45;
original hard cutoffs unchanged. [Status/ETA evidence](l7-status-20260923-101536.json).
No server mutation or additional dispatch. SpB random addition still awaits
length/budget confirmation; it is not in the active queue.

Latest September23 10:11–10:12Beijing heartbeat: **SpB L7same completed
step87/96; train96 is still running**. Latest returned binary64-v1 metric has
valid action ratio1, finite positive gradient114.785 and invalid advantage0.
The86 dispatched seed batches reset2..87 match Random0 exactly; checkpoint
file inventories8..80 each contain26 required nonempty files (contents unread).
Existing arm/suite storage704,048,556,091/754,012,707,157bytes are within their
unchanged1/2TiB budgets, exit0/empty stderr. No failure receipts, final stage
results or Qwenrandom long dispatch yet. [Compact read-only evidence](l7-heartbeat-20260923-101101.json).
Healthy progress remains quiet; no remote mutation, retry or new learning claim.

Prior September22 23:33:43Beijing heartbeat: **SpB L7same completed step5/96; step6 has
a113/113valid pre-update gate, not yet a completed PPO claim**. Exact train96
container running/unpaused; existing arm/suite storage samples exit0 within
unchanged budgets, no failure receipts. Qwenrandom long still undispatched.
Empty guardian terminal slot/missing part terminal state are expected while
running. [Compact read-only evidence](l7-heartbeat-20260922-233343.json).
Healthy progress; no duplicate event notification, no remote mutation/retry.

Prior23:07Beijing: **SpB L7same actual completed step3/96; Qwen same96
results and frozen settings rechecked**. Qwen training609/768wins across63
distinct seeds,89/96batches all-win/all-loss; CP2 paired7/8→CP96 5/8 does not
demonstrate improvement. “96updates” means96outer rollout/PPO phases, not
necessarily96AdamW optimizer calls. Full explanation and limits were appended
to the user-specified Yuque SCII日志 in Safari, preserving historical content;
published reading view verified23:19. [Report](l7-results-interpretation-20260922.md),
[compact evidence](l7-settings-analysis-20260922-2307.json),
[publication receipt](l7-yuque-publication-20260922.json).
Only read-only diagnosis/documentation; no new dispatch or experiment changes.

Prior22:50:33Beijing: **SpB L7same short fully completed; long train96 dispatched
22:45 and ownCP2 model/optimizer/SC2state load actually returned**. Short243/243
answers valid, paired4/8→3/8wins (no demonstrated gain). Next is existing queued
Qwen L7random long. [Snapshot/ETA](l7-followup-status-20260922-225033.json).
User-requested [SpB random addition](spb-l7-random197.md) is planned after it,
but added length/budget confirmation is pending; no new queue/dispatch yet.
Original deadlines unchanged. Short completion/first long restore notified.

Prior22:38–22:40Beijing: **SpB L7same completed2actual PPO/16natural games,
103/103consumed answers valid; ownCP2 post stage is running**. Train result=.done,
exit0, actual finite positive gradients and frozen acceptance passed. Pre4/8wins;
post result and both long dispatches still absent. No-thinking remains enabled
alongside canonical action support/top-p1, not a historical-protocol rollback.
[Evidence](l7-protocol-status-20260922-223845.json),
[seed/protocol clarification](l7-host-continuation197.md#seed-and-no-thinking-clarification--september22-22382240beijing).
First SpB actualPPO/train2 completion reported; do not repeat the events.

Prior22:26–22:28Beijing: **SpB L7 pre accepted:4/8wins,46/46consumed answers
valid,0updates; train2 active**. Its available audit is pre-update only, not
proof of completed PPO. Both long successors remain undispatched. No learning
or architecture gain established. [Snapshot and conclusions](l7-conclusions-20260922-222637.json),
[interpretation](l7-host-continuation197.md#user-requested-conclusions--september22-22262228beijing).
Pre completion reported to user; do not repeat the event notification.

Prior22:03:15Beijing: **new r4 queue dispatched once22:00; original SpB5.17B
L7same pre is actually in SC2**, clean9cb291/world8/binary64-v1, correct worker
support hashes and original8evaluation seeds. No PPO yet, pre is zero-update.
Strict inclusive11-root storage50,268,978,045bytes/exit0/empty stderr with actual
owned-container pause/resume verified. SpB short→same96→Qwenrandom ownCP2→96
is now queued behind full stage gates, original fixed cutoffs unchanged.
[Launch and CPU/GPU evidence](l7-host-r4-launch-20260922.json):214model-side and
71host Linux CPU tests passed zero skips;7actual startup/Hydra entries and source
hashes passed,4CPU containers exited0/GPUrequestsnull. No training-core diff
from469c77. Unique197-l7-r4 monitor active10min, firstGPU/SC2 notified; no duplicate.
Legal output/operational sampling success is not a learning or timing-equivalence
claim. Previous CPU-only and failure entries below are preserved history.

September22 user now explicitly authorized the bounded
[new r4 host-supervised continuation](l7-host-continuation197.md): fresh SpB
L7same short+96 → accepted Qwen L7random ownCP2+96. Prior failed pre contributes
eight dispatch slots (1560cumulative upper bound), with original GPU budgets and
absolute cutoffs unchanged. Preparation is authorized; GPU status requires
actual new dispatch evidence. Old failures and accepted CP96 eval remain intact.

September22 subsequent user acceptance authorizes **CPU-only host integration**
of the quiescent sampler and independent loss recovery. The new
[host supervision candidate](host-supervision197.md) executes unchanged stage
launchers with one host sampler and a detached per-stage guardian. Local100tests:
96pass/4Linux-only skips. Final Linux100tests passed zero skips, and all five real
CPU-container scenarios passed at21:20:15Beijing: serial success, failed-stage
successor blocking, supervisor SIGKILL while paused, pause expiry and lease expiry.
[CPU evidence](host-supervision-cpu-20260922.json), tested clean398eb99. All12
fixtures across both attempts are retained/exited/unpaused with no GPU requests.
The first probe's clean-exit and receipt-lock failures are retained, not hidden.
No existing queue/deployment was changed and no GPU continuation was started.

September22 CPU-only follow-up: user approved repair before another continuation
decision. [Owned-container quiescence candidate](storage-quiescence-fix.md) is
isolated on `codex/fix-quiescent-storage`; the existing storage sampler has an
opt-in hook, with no current launcher using it. Local79tests:75pass/4Linux-only
skips; final Linux79tests and actual CPU-container race/fix probe passed with
zero skips at20:46:17Beijing, clean source8d085df. Both fixture containers exited0,
no GPU requests; original du diagnostics survive recovery-client timeout.
[Retained CPU evidence](storage-quiescence-cpu-20260922.json). It is not yet a
GPU-ready controller: host-only integration and lost-supervisor recovery remain
explicit pre-dispatch gates. No experiment restart, budget change or monitor.

Latest September22 19:25:22Beijing: **SpB L7same short failed during pre;
0PPO, both long successors blocked and never dispatched**. Required inclusive
storage measurement returned1 after transient compiler files disappeared during
GNUdu traversal; bytes are unknown, not zero or the last successful value.
Owned container exited1 at19:08:37, OOMfalse. No pre result/.done/acceptance,
train2 directory, new checkpoint or long dispatch exists. This is a storage
accounting/watchdog failure, not evidence of model degradation or disk capacity
exhaustion. [Failure evidence](l7-spb-storage-failure-20260922-192522.json),
[handoff and limits](l7-followup197.md#r3-spb-pre-storage-failure--september22-192522beijing).
All artifacts and fixed budgets/deadlines preserved; no automatic repair/retry.
Unique197-l7 monitor deleted after failure handoff; the subsequent CPU-only
candidate approval/results are above. A new-RUN continuation still needs review. The already
accepted Qwen CP96-only evaluation remains valid within its stated limitations.

Prior19:06:42Beijing: **Qwen CP96-only final eval accepted (5/8wins,0updates,
23/23consumed answers valid); SpB L7same short automatically dispatched19:06:02**.
OwnCP2 paired post was7/8, now5/8; only8pairs, no demonstrated learning gain.
The old six-gradient evidence gap and failed training terminal are unchanged.
SpB short+96 shares deadlineSeptember24 19:06:02, suite deadlineSeptember26
19:06:02; these are ceilings, not ETAs. Qwen random remains subsequent.
[Full completion/queue evidence](l7-eval-complete-spb-start-20260922.json),
[limits and interpretation](metric-precision-fix.md).
By19:08:09, actual SpB5.17B worker/canonical+no-thinking banners and SC2
freshstep0 were verified; pre still running, PPO not yet observed.
[First actual SpB GPU evidence](l7-spb-first-gpu-20260922.json).

September22 subsequent user approval: **new CP96-only8-game evaluation → fresh
SpBsame short+96 → Qwenrandom ownCP2+96**, preserving old failed roots,
the six unresolved historical gradients and all original budgets/deadlines.
[Approved boundary and new run identities](metric-precision-fix.md).
At19:02:35Beijing, new eval actually loadedCP96,0updates, original8seeds
registered and SC2 battle log advancing; successor r3 waiting-predecessor.
Both214-test Linux CPU suites passed0skips,8actual launcher/Hydra configs and
old/new eval protocol match passed before the single19:00dispatch. No training
replay. [Launch/CPU evidence](l7-continuation-launch-20260922.json),
[actual load/seed/SC2 evidence](l7-continuation-gpu-20260922.json).

CPU repair (2026-09-22 17:45Beijing): user approved the metric-precision repair
and a no-retraining continuation proposal. **69 local CPU tests passed, zero
skips**; logger/recorder preserve binary64 scalars, require a versioned receipt
for new runs, and retain the unchanged strict gradient/invalid-credit gates.
No GPU validation, server mutation, queue restart or acceptance waiver this turn.
The six historical raw gradients remain unknown and the failed chain stays
failed. [Repair, usage and pending continuation proposal](metric-precision-fix.md),
[CPU evidence](metric-precision-cpu-20260922.json).

Historical terminal status (2026-09-22 17:15Beijing): **Qwen same96 training
subprocess completed, but frozen terminal acceptance failed**; final eval and
the SpBsame→Qwenrandom follow-up did not dispatch. Training result=.done/exit0,
94new steps/752natural games/601wins; CP8..96 each26required nonempty files by
stat. Six gradients in console-derived metrics are0.000, rejected by the strict
positive-gradient gate. Frozen logger rounds to3decimals, so exact zero versus
small positive remains unresolved; not evidence of model collapse or a passed
long experiment. Root Docker exit1 and successor queue failed take precedence.
[Terminal evidence](qwen-l7-terminal-20260922-171508.json),
[diagnosis and handoff](qwen-l7-long197.md#terminal-acceptance-failure--september22-1715beijing).
Unique197-qwen-l7-seed96 monitor deleted after failure handoff. No retry, gate
relaxation, frozen edit or new dispatch; CPU repair is documented above, while
any later GPU continuation still needs approval. Training79.92% is not a held-out
learning conclusion.

September22 follow-up approval: user approved current Qwen same96 → fresh SpB
Level7 same short+96 → accepted Qwen Level7 random ownCP2→96, each new arm
<=48h/384GPUh/1TiB. [Scope, gates and queue record](l7-followup197.md).
**Previously queued once15:14:50Beijing**,15:16waiting-predecessor/no new GPU dispatch;
now failed on the predecessor gate as recorded above.
190Linux CPU tests zero skips and7actual launcher/Hydra configs passed;
SpB native CP2 gate remains conditional on future real short acceptance.
Existing Qwen was55/96 at15:16; deployment/deadline untouched.
[Queue evidence](l7-followup-queue-20260922.json).

Prior progress (2026-09-22 16:08Beijing): Qwen L7same returned PPO74/96;
cumulative ledgers through73 show464/584wins (79.45%),4299/4299valid consumed
answers. CP8..72 stat inventories passed; paired final evaluation pending.
No strategic gain established. Approved SpBsame→Qwenrandom follow-up still
waits for predecessor acceptance. [Evidence](qwen-l7-progress-20260922-160808.json)
and [interpretation](qwen-l7-long197.md#user-requested-progress--september22-1608beijing).

Prior progress (2026-09-22 14:38:14Beijing): the single Qwen L7same continuation
is running at38/96completed steps,36new PPO/288new natural training games.
Including parentsteps1–2:248/304wins,2004/2004valid consumed answers;
CP8/16/24/32 inventories passed. Final paired evaluation is pending; output
legality does not establish learning. [Summary and limitations](qwen-l7-long197.md#progress-summary-audit--september22-142931beijing),
[latest ETA evidence](qwen-l7-long-eta-20260922-143814.json). Per-game random
long continuation was then approved and queued in the follow-up record above.

Prior status (2026-09-22 13:23Beijing): the approved single
[Qwen L7 same-seed step2→96 continuation](qwen-l7-long197.md) is **running**.
Single dispatch13:18:46; actual ownCP2 restoration returned, nextseed53×8,
first resumed PPOstep3 completed (finite gradient0.164),55/55consumed answers
valid. Fixed48h/384GPUh ceiling **September24 13:18:46Beijing**, not ETA;
1TiB inclusive budget,94new updates then8paired zero-update evaluation games.
[Launch evidence](qwen-l7-long-launch-20260922.json). Missing driver RNG and
ledger-restored SC2 counters were explicitly accepted: not bitwise replay.
Unique monitor197-qwen-l7-seed96 active; firstGPU/load/PPO already notified.
Mechanical validity and the first eight wins do not establish strategic learning.
Default resume remains rejected except for the verified accepted-prefix contract.

Prior status (2026-09-22 11:58 Beijing): **all three Qwen r4 arms completed**;
the retained r3 l6-same completes the four-arm matrix without another replay.
Accepted matrix:128natural games/8actual PPO updates,929of929consumed answers
valid. Paired wins: L6same8→8, L6random8→8, L7same7→7, L7random7→8 (each/8).
This passes short mechanical acceptance, not established strategic learning or
random-seed superiority. [Final verification](qwen-r4-complete-20260922.json),
[results and limitations](qwen-seeds197.md#r4-terminal-acceptance--september22-1158-beijing).
Unique197-qwen-r4 monitor deleted after completion. No96-step/SpB-L7 successor
authorized or started; the previous long-training proposal still needs approval.

Prior status (2026-09-22 11:08 Beijing): **Qwen r4 l6-random completed;
l7-same pre passed and train2 is active**. L6:32natural games/2actual PPO updates,
249of249consumed answers valid, paired wins8/8→8/8 (saturated, no demonstrated
learning gain). L7pre:8natural games/0updates,49of49valid,7wins1defeat;
no completed L7PPO claimed yet. L7random pending. Fixed16:42:12 suite ceiling
unchanged. [Verified event evidence](qwen-r4-l6-complete-l7-pre-20260922.json).
First r4PPO, L6 completion and L7GPU/pre events notified; keep unique197-qwen-r4.

Prior status (2026-09-22 10:51 Beijing): **Qwen r4 l6-random pre passed and
train2 is running**: pre8natural games/0updates,49of49valid consumed answers.
[Pre evidence](qwen-r4-pre-20260922.json). No completed PPO yet claimed;
L7same→L7random successors and fixed16:42:12Beijing total ceiling unchanged.
First GPU/SC2 and pre completion notified; unique197-qwen-r4 follows next events.

Prior status (2026-09-22 10:45 Beijing): **Qwen r4 l6-random is actually running
eight-rank SC2 pre evaluation**, fresh original model/step0/zero updates.
Single GPU dispatch10:42:12Beijing; total6h/48GPUh ceiling16:42:12, not ETA.
[Launch evidence](qwen-r4-launch-20260922.json). L7same→L7random are queued serially;
completed r3l6-same is revalidated and not replayed. New unique monitor197-qwen-r4
follows only this authorized remaining suite; first GPU/SC2 notified, PPO pending.

Prior planned status (2026-09-22 10:40 Beijing): user explicitly approved
[new r4 remaining three Qwen arms](qwen-seeds197.md#explicitly-authorized-r4-remaining-three-arms--september22-planned),
maximum6wallh/48GPUh; CPU/config preparation underway, not yet GPU dispatched.
Reuse completed l6-same; no duplicate replay or old failed-run restart.

Historical status (2026-09-22 01:22 Beijing): **Qwen r3 failed during l6-random
train2 after the suite storage measurement failed at 01:08:00**. GNU du returned
1 when a watchdog temporary state file disappeared during traversal. The child
state publication overlaps that traversal, consistent with an atomic-rename
race; this is not a model-legality failure or evidence of storage exhaustion.
Docker is exited137/OOM=false. First arm l6-same remains completed; l6-random
has only pre accepted, and both Level7 arms were never dispatched. No retry.
No train2 result/metrics/CP2 exists; a before-update audit does not establish
how many PPO updates completed. [Terminal evidence](qwen-r3-terminal-20260922.json),
[handoff and limits](qwen-seeds197.md#r3-terminal-storage-failure--september22-0122-beijing).
Unique monitor197-spb-r4 deleted after terminal handoff. The user subsequently
approved [CPU-only publication/traversal repair](storage-watchdog-fix.md#approved-publicationtraversal-coordination-repair--september22).
At10:21–10:22Beijing the final repair passed49Linux CPU tests with zero skips,
including deterministic actual GNU-du reproduction/fix and failure-state cleanup
guards. A separate CPU-only container verified the actual host/container shared
lock bind (exit0, GPU requestsnull, no model/SC2 mounts).
[CPU evidence](storage-coordination-cpu-20260922.json).
No new GPU run, failed-run restart or replacement monitor was launched or
authorized by this approval. Other uncoordinated filesystem mutations and the
historical Docker stop-client timeout are not claimed fixed.

Prior status (2026-09-22 01:03 Beijing): **Qwen r3 l6-same completed all three
stages**,32natural games/2PPO steps/239of239consumed answers valid. Paired
pre/post wins8/8→8/8: saturated small-sample evaluation, no demonstrated learning
gain. Second arm **l6-random passed pre and is training**; Level7same/random
remain pending. [Current evidence](qwen-r3-l6-same-complete-20260922.json).
Suite deadline08:36:25Beijing unchanged, not an ETA. First-arm PPO/train/post/
completion and second-arm GPU/pre events have been notified; keep monitoring.

Prior status (2026-09-22 00:47 Beijing): **SpB r4 completed all three actual
GPU acceptance stages**:32natural games,2PPO updates,160/160consumed answers
valid, post loaded its ownCP2/paired seeds/rank RNG with0updates. Paired wins
were6/8pre→5/8post: mechanical acceptance passed, learning improvement not shown.
[Completion and successor evidence](r4-complete-qwen-r3-start-20260922.json).
The authorized [Qwen four-arm suite r3](qwen-seeds197.md) automatically dispatched
at00:36:25Beijing; first **l6-same pre passed**,49/49consumed valid and8/8wins,
and train2 is active. At00:47 no completed PPO metrics were available; a pre-update
audit alone is not an update. Qwen suite ceiling is now fixed at08:36:25Beijing,
not an ETA; first-arm ceiling02:36:25. Old failed runs remain untouched.
[SpB full protocol](acceptance197.md), [launch](r4-launch-20260921.json),
[train2](r4-train2-20260922.json). Unique monitor197-spb-r4 continues for Qwen;
long training remains unauthorized. These small samples do not prove learning
or architecture superiority.

Prior status (2026-09-21 23:17 Beijing): separately approved r3 **stopped after
host storage-budget measurement failed**, before any recorded response/PPO or accepted
stage. Docker exited137/OOM=false at23:14; stale child `running-unverified` is not
a live job. No retry; monitor deleted. [Terminal evidence](r3-terminal-20260921.json)
and [historical launch snapshot](r3-launch-20260921.json) are both preserved.
User subsequently approved [CPU-only storage-watchdog repair](storage-watchdog-fix.md).
At23:29–23:30 Beijing it passed32tests on197 Linux CPU (zero skips): retained
du failure diagnostics, strict totals/deadline validation and concurrent atomic
state writes. Historical du root cause remains unknown; this is not GPU/model
acceptance and does not authorize another GPU attempt or restart a failed queue.

Prior status (2026-09-21 21:49 Beijing): SpB r2 GPU precheck **failed before first
answer/PPO**; Qwen successors blocked, no automatic retry. The predecessor
192-game panel completed. See [terminal handoff](terminal197-20260921.md)
and [machine-readable evidence](heartbeat197-terminal-20260921.json).
The repair is **not GPU accepted, not a learning result**.
User subsequently confirmed the scoped [generation-token boundary repair](generation-token-fix.md)
and CPU regression. The metadata fix passed115 tests (zero skips) on the real
worker→tiny-Qwen3 CPU path; SpB/Qwen registered metadata is covered without loading
weights. No GPU restart is authorized by that code-repair confirmation, and the
earlier GPU failure remains the terminal experiment result.
User then separately approved [one fresh r3 GPU short acceptance](acceptance197.md#newly-approved-r3--september21-planned),
32games/2h/16GPUh; dispatched once and failed as above, with no Qwen or long-training successor.
Base: actual Level7 runtime `7236c37b116fd8fbe15db09ccbdcd2e740e4e840`.
Branch: `codex/fix-invalid-policy-credit`. This is a new opt-in objective, not an
in-place alteration of C/D or the stopped Level7 experiment.

## Why

September21 13:41 Beijing diagnostic: 1,405 consumed/evaluable recent L7 answers,
0 valid, 1,391 with repeated `</`; 329 invalid records had positive environment
reward. PPO still had nonzero gradients. The scripted fallback can win without
a valid model plan; pre-centering constant invalid penalties can cancel inside
GiGPO, and representative-episode scoring does not assign per-answer legality.
Cross-seed UID groups additionally mix scenario difficulty with model quality.
These are mechanisms and observed degeneration, not proof of a unique cause or
evidence that every historical RL improvement was false.

## Scope and contract

- `algorithm.sc2_policy_credit.enabled=False` preserves existing behavior.
- When explicitly enabled, keep raw environment reward/metrics and response
  tokens unchanged; bypass the old pre-centering invalid penalty. After GiGPO's
  final centering, every invalid response token gets `min(A,0)-0.1`. Valid answers
  and padding remain unchanged. Thus invalid winners cannot receive positive
  policy-gradient advantage. This is an auxiliary objective, **not an unbiased
  causal estimator**, and does not prove valid answers caused fallback victories.
- Before padding/balancing/any PPO update, measure real consumed active answers.
  Below `min_valid_ratio=0.5`, append `sc2_policy_credit_audit.jsonl` and stop the
  run. No rejection sampling, silent filtering, manufactured samples or retry.
  0.5 is a conservative provisional operational floor, not an optimized threshold.
- Require explicit worker `SC2_ORIGINAL_GAME_SEEDS=0`; after actual reset verify
  each UID contains >=2 games with one identical dispatched seed, before model
  generation. Merely setting a UID/config is insufficient evidence.
- Training defaults to fresh `trainer.resume_mode=disable`; the explicitly
  authorized [accepted-prefix continuation](qwen-l7-long197.md) checks unchanged
  protocol and complete prior evidence. No migration from the collapsed L7
  checkpoint. Evaluation may load checkpoints. Restrict to
  plain SC2 GiGPO + episode reward, without nested sampling/multiturn/tools,
  reward model, KL-in-reward, PF-PPO or dynamic group filtering.

Opt-in overrides on an independently frozen, fully reviewed SC2 launcher:

```text
algorithm.sc2_policy_credit.enabled=True
algorithm.sc2_policy_credit.invalid_advantage_penalty=0.1
algorithm.sc2_policy_credit.min_valid_ratio=0.5
trainer.resume_mode=disable
++ray_init.runtime_env.env_vars.SC2_ORIGINAL_GAME_SEEDS='0'
```

Keep difficulty, T0.8/192token/gamma1/combat0.001 and the existing no-thinking
prompt/support protocol explicit. Same-seed grouping changes the former L7
seed protocol. The no-thinking mask is not an action grammar and is not repaired
by this change; neither top-p consistency nor internal reasoning shutdown is claimed.

## Verification and release gate

First isolated CPU run passed all 12 initial `test_sc2_policy_credit` cases,
including real GiGPO, trainer stop-before-update, default-off, padding, negative
gradient sign and no mutation of rewards/tokens. This is not an SpB GPU update.
The expanded 74-test CPU harness first failed because its source-only upload
lacked Git history/full fixture scripts and the required tokenizer path;
this failed check is retained, not reported as passing. A full-fixture rerun and
two additional boundary tests were then exercised with the full fixture.

At14:17 Beijing the full-fixture run returned0: **76 tests passed, zero skips**,
including14 new policy-credit cases, actual collector seed rejection before
model generation, shipped default-off config, legacy GiGPO, tokenizer/support
constraint, actual CPU actor/reference forward, and action/format regressions.
The actual tokenizer tests assert `torch.cuda.is_initialized() == False`.
Git printed warnings about an optional absent alternate-object directory; all
required `git show` objects resolved and all baseline-comparison tests passed.
No real SpB weights or SC2 games were loaded in these CPU tests.

Tested code commit: `b879ae957778360d0aa64ced1c94d6064282cc73` (privately backed up).
Runtime image: `sha256:1a497d5721f89bb2e98c0273c4b1495f8fdc6921d589650d090871c11b8d1649`.
Command (inside pinned `/runtime/bin/python`, CUDA hidden, no Docker GPU request):

```bash
python -B -m unittest test_sc2_policy_credit test_sc2_task_signal \
  test_sc2_no_thinking_torch test_thinking_action_boundary \
  test_r6_format_reward test_original_bo_segment -v
```

Full evidence: `full-regressions.log` in the CPU staging root below; SHA256
`555edb3d23cfeff8299590b637b6b7b66e99b1ae52c41cbb41324bd6e68b1ac3`.
The log also exists locally at `/private/tmp/sc2-policy-credit-full-regressions-20260921.log`.
Implementation is CPU-verified; GPU/learning recovery remains unverified.

No new training is authorized or launched by this record. User now prioritizes
the separately approved original/D96/C96 matched panel on197, using unchanged
runtime7236 (not this repair). Before future short training, verify fresh-model
validity and execution on GPU; a guard may stop immediately if the base model
already fails the chosen protocol. CPU success cannot establish restored win rate.

## User-requested stop (2026-09-21)

At13:49 the exact owned L7 container was stopped once. Docker's exit-event
confirmation was delayed; by13:50–13:51 it and its dedicated controller/tmux had
exited, and all eight GPU compute lists were empty. Queue records `Level7 exited
137; no retry/next level`. This was a **user-aborted degeneration run**, not a
new OOM/infrastructure diagnosis. L8–10 were never dispatched. CP72 and all earlier
artifacts remain, with no training-resume permission for collapsed weights.
The obsolete `197-c-level7-10` heartbeat was deleted following the app automation
instructions. No old model/checkpoint/run was deleted or rewritten.

Stop evidence: `/var/jfsCache/sc2-c-levels197-20260920-r5/staging/user-stop-20260921-mh4pm680`.
CPU evidence staging: `/var/jfsCache/sc2-policy-credit-cpu-20260921.6kVaYu`.

## Continued repair: canonical output support (2026-09-21)

User requested continued urgent repair after the common Level6/7 failure analysis.
An additional default-off [canonical action-support candidate](../../../docs/decisions/sc2-canonical-action-support.md)
addresses raw generation legality, rather than just stopping collapsed batches.
It shares the same dynamic token support in generation and actor/old-actor/ref,
reserves enough tokens to finish a plan, and enforces current candidate quotas.
This is a restricted-policy protocol change, not proof of learning. For this new
candidate only, top-p becomes1 to avoid nucleus/teacher support mismatch; all old
frozen .9 runs and the current panel remain unchanged. No new GPU run is launched
by this implementation entry. Verification evidence and limitations are in the
linked decision record; future short GPU acceptance needs explicit budget approval.

## Approved bounded GPU acceptance (2026-09-21)

User subsequently approved the [8+16+8 game acceptance](acceptance197.md) after
the existing panel, with two hours / sixteen GPU-hours maximum and no retries or
long-training promotion. The unstarted0172fb9 queue was subsequently withdrawn
with explicit approval for its stale source manifest. Replacement runtimef211c0e9
changes only those five hashes; no training/action/reward code changes. Its new
queue retains the original budget and expiry. See that record for preregistered protocol,
launch status and evidence. Approval/preparation is not GPU success.

## Approved Qwen seed-group ablations (2026-09-21)

User additionally approved [four bounded Qwen short arms](qwen-seeds197.md),
Level6/7 × same/per-game-random seed groups, total≤64GPUh, after the existing
SpB short gate. A new explicit mixed-seed ablation switch preserves the default
strict same-seed guard, invalid-credit objective and all other quality gates.
No running/frozen panel or SpB deployment is changed; see the record for exact
matched-range seed sequences, asset transfer authorization and launch status.
