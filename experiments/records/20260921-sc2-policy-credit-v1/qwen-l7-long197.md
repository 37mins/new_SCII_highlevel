# Qwen Level7 same-seed continuation, September22

Separately authorized final-eval continuation completed19:05:21Beijing:
8natural games/5wins3defeats/0updates,23/23consumed answers valid, paired
load/seed/RNG and exit0 fully accepted. ParentCP2 had7/8wins; no demonstrated
learning improvement in this small paired sample. This does not erase the old
six-gradient acceptance failure. [Final evidence](l7-eval-complete-spb-start-20260922.json).

This original run remains **terminal acceptance failed**, September22 17:15Beijing;
training reached96, but six console-rounded gradients cannot establish strict
positivity. Final eval did not run. See the [terminal evidence](qwen-l7-terminal-20260922-171508.json)
and [separately approved CP96-only continuation](metric-precision-fix.md).
Subsequent user approval accepted the historical evidence gap, without changing
this failure: new unique eval dispatched19:00 and actually loadedCP96/registered
8paired seeds with0updates by19:02:35. No training replay or frozen edits.
[New actual load evidence](l7-continuation-gpu-20260922.json).

Earlier snapshot, September22 16:08:08Beijing: returned PPOstep74/96.
Cumulative ledgers are independently checked through73; CP8..72 each26required
nonempty files by stat at16:04:54. Final evaluation not started.
Single GPU dispatch13:18:46; actual ownCP2 restoration returned.
The user approved the single48h/384GPUh/1TiB continuation, then explicitly
**accepted** the missing-driver-RNG ledger migration. Reuse this record and branch
`codex/fix-invalid-policy-credit`; no new method/parallel experiment is created.

## Question and scope

Does the accepted constrained-output Qwen policy remain mechanically valid and
improve on paired Level7 evaluation after96total PPO steps? One arm only, not an
architecture comparison or proof that RL caused executor victories. Keep current
model/prompt/action/reward/executor fixed. The deliberate change is2→96steps.
Training wins across different step seeds are not a controlled learning curve.
The eight paired evaluation seeds are small-sample evidence, not statistical
proof of a general strategic gain. Report paired win/loss changes and marginal
Wilson intervals separately; do not claim model/architecture superiority.

- Parent: `/var/jfsCache/sc2-qwen-seeds197-20260922-r4/l7-same`;
  clean runtime `2f95c9fd505bd4529070ff4988c5c9efcb111b53`, accepted32natural games,
  two actual PPO updates,242/242valid consumed answers, paired7/8→7/8wins.
  Full three-stage evidence is in[qwen-r4-complete-20260922.json](qwen-r4-complete-20260922.json).
- Restore only its `runs/train2/checkpoints/global_step_2`: model, AdamW optimizer,
  constant scheduler, per-rank RNG and dataloader. No weights-only reset, no old
  collapsed SpB checkpoint, no replay of steps1–2 or other Qwen arms.
- The parent has25required files but **no `sc2_state.pt`**. The user accepted
  recovering closed-game/reset counters from complete seed/outcome/answer ledgers.
  Python/NumPy/Torch **driver** RNG was not saved and cannot be reconstructed:
  explicitly **not bitwise replay**. Worker RNG is distinct and loaded by the
  existing FSDP loader. Missing state is not fabricated or written into oldCP2.
- Deterministic private PythonRandom(0),0..100 with replacement, same seed for
  all8games per step. Parent49×8,97×8; newstep3=53×8, followed by5×8,33×8,… .
  Verify all94new seed batches against reset indices2..95. Future checkpoints
  save SC2 state including explicit seed-protocol identity and driver RNG.
- Keep original Qwen3-4B-Instruct-2507 reference/metadata, revision
  `cdbee75f17c01a7cc42f958dc650907174af0554`, verified12-file asset, Qwen3ForCausalLM.
  Actor continues its ownCP2; reference remains the original model, not CP2.
- Level7VeryHard,Flat128/SC2Base75689/Air/Terran, canonical BO, model plans from
  opening. T.8/192tokens/top-p1/top-k0/gamma1/combat.001/LR1e-6 and constant
  zero-warmup scheduler. Same canonical action/no-thinking support across
  actor/oldactor/ref/rollout. Post-centering invalid credit and .5real consumed
  legality PPO floor remain unchanged; no resampling/D+filter/early-stop promotion.

## New run and exact limits

- Unique root `/var/jfsCache/sc2-qwen-l7same96-197-20260922-r1`;
  source `/var/jfsCache/sc2-qwen-l7same96-197-source-20260922-r1/code`.
  Run prefixes `qwen-l7same96-197-r1-train96` and `…-eval96`.
- Controller `qwen_l7_long197.py`; socket `sc2_qwen_l7same96_197_20260922_r1`,
  session `qwen_l7same96_197_r1`; container `sc2-qwen-l7same96-197-20260922-r1`.
  Pinned existing image1a497d57… and orchestration9a7b0faca5b145a891ad211f189121e4949f0eab.
- `train96`:94new PPO updates /752natural games; checkpoint every8global steps
  (8,16,…,96), each26required files including SC2 state. Existingsteps1–2retained.
  Then only `eval96`:8paired natural games/0updates/actual ownCP96 load returned.
  Total new760games; no freshpre/step2post replay, no automatic successor.
- First actual GPU dispatch fixes172800seconds including loading, intermediate
  waits, checkpointing and final evaluation; maximum384GPUhours.45second cleanup
  margin. Queue admission expires **September22 18:00Beijing**, not an ETA.
  No retries, deadline resets or migration to another node. Any failure is kept
  and handed off. Historical Docker stop-client timeout is not claimed fixed.
- Strict1TiB combined ceiling covers the entire new output root, new source
  root (including transfer/preparation artifacts) and retained parent arm.
  Existing verified original model is mounted read-only, not recopied.
  Failed measurements are unknown, never0/old successful values. Shared storage
  lock retained; no ignored paths/errors, retries, deletion or old artifact edits.
- Admission requires all8cards entirely free/no computePIDs,600GiB RAM,
  1084GiB NVMe free and fsync/readback; no idle GPU reservation or stopping others.
  New outputs on NVMe; SC2/runtime dependencies remain read-only existing storage.

## Gate and implementation

Default policy-credit resume still rejects. The explicit
`trainer.sc2_policy_credit_resume_contract` permits only a completed accepted
same-seed prefix with matching small-file SHA256 receipts, all25CPfiles and
unchanged training protocol. Path relocation, length/checkpoint cadence and
explicit restore controls are the only normalized config differences.
CPU checks compare actual resolved Hydra config with parent and hash data/BO.
No changes to loss, action grammar, sampling or executor logic.

The controller reuses the existing owned-container deadline/storage/stop engine;
the two actual launchers and real tokenizer/worker plus resume regressions must
pass on pinned Linux CPU with zero skips/no CUDA before enqueue. CPU success
cannot replace actual step2 load/nextseed/finite-PPO evidence. Result/.done/exit0,
clean SHA/world8,752+8natural games/no truncation, all real answers valid/no
thinking, plan→queue→local model commands,94audits/PPO metrics/finite positive
gradients/nonpositive invalid advantages, checkpoints and final seed/rank RNG
pairing are terminal gates. Mechanical legality is not strategic learning.

After single enqueue, one quiet monitor follows first actualGPU/load, firstPPO,
phase completion, failures/decisions; normal progress stays silent. Delete it
when this run completes or terminal failure is handed off with no further authority.
No SpB-L7,96-step extra arms,L8–10,IDSC resumption,node46 or old-run restart.

## CPU preparation, September22 13:14Beijing

Candidate `f4c4539c2795805225f4766e5b96066cd8567e8a` passed170Linux CPU tests,
zero skips, CUDA uninitialized; both actual train96/eval96 DRY_RUN entries and
Hydra/source32hash checks passed in isolated `cpu-candidate1` under the new
source root. No model/optimizer production shards or SC2/GPU were loaded.
Actual tiny-Torch Adam/scheduler/dataloader loading, native/Random0 seed recovery,
default resume rejection, protocol mismatch and actual GNUdu coordination are
covered. Candidate containers/results are retained; this was CPU preparation,
not a GPU attempt or a run retry. Local56tests had52passed/4Linux-only skips.

Final preflight additionally inspected eight small saved scheduler/RNG receipts
and the actual parent ledger. Paired evaluation compares rank/seed/CPU-CUDA RNG
hashes, not process PID. Final `279d5496464de29e14c64924ccb829147351efbd` passed
171Linux CPU tests with zero skips, both actual DRY_RUN/Hydra entries and32source
hashes. Both CPU containers exited0/DeviceRequests=null/CUDA=false. Entries were
`qwen_l7_long197.py regressions` and `qwen_l7_long197.py cpu` in the pinned image;
readiness/regressions receipts and container state were independently read back.

## Actual launch and first PPO, September22 13:23Beijing

[Machine-readable evidence](qwen-l7-long-launch-20260922.json) preserves the
small receipt hashes, CPU/container evidence, actual resume and first PPO.
Source/controller/runtime are clean `279d5496464de29e14c64924ccb829147351efbd`;
the documentation commit afterward does not modify the frozen runtime.

- Single enqueue/dispatch: September22 **13:18:46Beijing**,
  `start=1790054326.5133374`, fixed `deadline=1790227126.5133374`:
  **September24 13:18:46Beijing**, a maximum rather than ETA. Admission verified
  eight empty GPUs/no computePIDs,600GiB RAM,1084GiB NVMe and fsync.
- Actual GPU `resume_state.json` confirms ownCP2/model-optimizer-dataloader load
  returned, globalstep2/resetindex2 and nextseeds53×8; manifestclean/world8.
  Worker action/no-thinking banners carry the registered tokenizer/support hashes.
- The first eight games naturally ended, without truncation;55/55real consumed
  answers passed legality. The actual step3 PPO console subsequently returned
  finite gradient0.164, update_actor23.622s, invalid_advantage_max0 (rounded).
  This is stronger evidence than the earlier before-update audit alone.
- That batch's eight wins and near-zero rounded environment advantages do **not**
  establish strategic improvement; nonzero gradients can include the KL term.
  Final paired evaluation and the full acceptance gates remain pending.
- 13:22 storage measurement returned0/no stderr,50,049,006,377bytes across exactly
  the three budget roots. This is a time-sensitive snapshot, not a permanent
  storage guarantee or claim of a backend fix.
- Unique same-task monitor `197-qwen-l7-seed96` is active every10minutes;
  firstGPU/load/SC2/PPO already notified, healthy progression quiet. Delete after
  complete final acceptance or failure handoff without further authorization.

## Progress summary audit — September22 14:29:31Beijing

User requested a current progress summary. This round only read node197 small
receipts, checkpoint file sizes and an8MiB-bounded console tail via the approved
SSH alias, then archived this local record; no runtime/deployment edits, GPU
diagnostics, checkpoint-content reads, new launch or retry. Initial sandbox SSH
access failed before observation; the approved read-only connection then passed.

[Snapshot and receipt hashes](qwen-l7-long-progress-20260922-142931.json) record
the actual running container, root train96 state and unchanged fixed deadline.
The archived [collector](collect_qwen_l7_progress.py) checks contiguous completed
PPO console rows, natural outcomes, private Random0 same-seed batches, accepting
audits, parent result/.done and stat-only CP inventories. Run locally with
`python3 experiments/records/20260921-sc2-policy-credit-v1/collect_qwen_l7_progress.py`;
it SSH-reads node197 and writes a uniquely timestamped small JSON beside itself.
Each receipt is limited to1MiB and the console to8MiB; missing early PPO rows
cause an explicit failure rather than interpolation or invented progress.

- Completed globalstep33/96:31new actual PPO updates and248new natural games;
  including retained parentsteps1–2,264training games and216wins (81.82%).
  Latest8steps:56/64wins (87.5%). No pre/post evaluation games enter these totals.
- All1796/1796actually consumed training answers passed legality. This is output
  validity under constrained decoding, not command-completion rate or proof that
  RL learned valid syntax. Full terminal trajectory/worker acceptance is pending.
- CP8/16/24/32 each have26nonempty required files by stat; no large state was read.
- Strict existing storage receipt:250,113,841,405bytes (232.94GiB), exact three
  roots,return0/no stderr; no storage-failure receipt. No forced new measurement.
- Runtime remains clean279d5496464de29e14c64924ccb829147351efbd/world8, original
  dispatch/deadline unchanged. Train/result and eval/result remain absent, so
  neither stage is declared completed. Ceiling September24 13:18:46 is not ETA.

Learning is still unproven. All eight games in many same-seed batches share the
outcome; seven of the latest eight batches show advantage min/max rounded to
zero at console precision (step26 instead reports−.834/+.578). Rounded zeros
are not exact-gradient measurements; returned PPO/nonzero gradients can include
KL contributions. Cross-step seed changes and the small8-seed final panel limit
causal learning claims. No protocol or acceptance threshold is changed here.

Completed context, not re-run this round: the [SpB panel](terminal197-20260921.md)
gave original31/64,D9628/64,C9627/64 under the frozen no-thinking/top-p.9
evaluation protocol, with no demonstrated trained-model win advantage. The
[SpB repair](acceptance197.md) passed32games/2updates/160valid answers and paired
6/8→5/8; the [four Qwen short arms](qwen-seeds197.md) passed128games/8updates/
929valid answers, paired L6same8→8,L6random8→8,L7same7→7,L7random7→8.
These demonstrate mechanical acceptance, not strategic/architecture superiority.

Local verification: collector assertions passed during the read-only snapshot;
archived JSON/count/CP/seed consistency, collector AST syntax and git diff checks
passed. No new model/SC2 tests were run. This round is committed on the existing
experiment branch and pushed to its GitHub origin; the final response reports
the verified commit. No successor is scheduled; existing monitor follows this
single train96→paired-eval96 run only.

## ETA and per-game-random proposal — September22 14:38:14Beijing

User asked how long remains and whether each game within a step can draw a
random seed. [Read-only evidence and ETA inputs](qwen-l7-long-eta-20260922-143814.json)
show completed38/96,58steps remaining, container running and no terminal result
or storage failure. Recentsteps31–38 average108.1805seconds/step:58steps project
to6274.469seconds (104.57minutes). Wall time since initial dispatch divided by
36new completed steps is132.456seconds/step, including initial overhead.
Report approximately2–3hours left (September22 16:40–17:40Beijing) including
future saves/loading/paired evaluation, conditional on similar throughput.
This estimate is not a guarantee; the unchanged hard deadline remains
September24 13:18:46Beijing.

All304completed training games have248wins (81.58%),2004/2004valid consumed
answers. Only34distinct game seeds were sampled across38batches;31batches
are8/8wins and7are0/8. These are correlated same-scenario repetitions, not304
independent scenarios. Original Qwen already won7/8in the parent fixed-seed
pre-evaluation. High training win rate and mechanically constrained100%answer
legality do not establish strategic learning; train/eval seed distributions differ.

Per-game independent0..100sampling with replacement already passed the separate
L7random short acceptance (7/8pre→8/8post, only one improved pair). It can broaden
within-step scenario coverage, but mixed-seed UID advantages still conflate
scenario difficulty and policy quality. It is an ablation, not an automatic fix
for unbiased advantage or a guarantee of better training.

Propose keeping this frozen same-seed run intact, then separately extending the
accepted r4L7random arm's ownCP2→96 with752new training games and8paired eval
games, maximum48wallh/384GPUh/1TiB, after explicit budget/order approval and new
restore/preflight checks. Never inherit this same-seed arm's weights. A missing
parent driver RNG requires explicit non-bitwise-restore acceptance; do not infer
that the current same-seed restore gate already supports random-prefix migration.
No successor is prepared/queued/dispatched, no current process is stopped, and
no frozen config/deployment or experiment budget is changed in this round.

Verification: bounded2MiB recent console and small-ledger assertions; all38seed
batches/natural outcome counts/accepting audits checked, recent8returned PPO
rows contiguous, CP8/16/24/32 each26required nonempty files by stat. Archived
JSON arithmetic/timing checks and git diff checks passed; no model tests run.

## User-requested progress — September22 16:08Beijing

[Evidence](qwen-l7-progress-20260922-160808.json): actual recent console PPO74/96
returned; cumulative seed/outcome/answer ledgers independently verified through73
(584training games,464wins=79.45%,4299/4299valid consumed answers; latest8batches
48/64wins=75%). Retained parentsteps1–2 included; evaluation games excluded.
These73batches cover57distinct seeds, with58all-win and15all-loss batches;
within-step repetitions are correlated, not584independent scenarios. Constrained
validity is maintained, but strategic improvement is not established.

Eight actual returned PPO rows67..74 average154.848375seconds;22remainingsteps
project to3406.66425seconds (56.78minutes) before final loading/evaluation overhead.
Estimate roughly1–1.5hours from16:08Beijing if throughput holds, not a guarantee.
The hard48h deadline remainsSeptember24 13:18:46; no budget or config changes.

16:04:54 state/container remain live train96, no train/eval terminal results;
CP8..72 every8steps have26required nonempty files by stat. Existing storage
receipt500,200,594,930bytes/return0/no stderr across exact3roots; no failure.
Follow-up remains waiting-predecessor/completed[], all dispatches absent.
After complete current train/eval acceptance: SpB L7same short+96 then Qwen
L7random ownCP2→96, under the separately approved follow-up record; no new launch.

The full-history collector correctly rejected missing early PPO rows in its
8MiB tail. A2MiB recent8-row attempt also lackedstep66 and was discarded.
No log bound was expanded and no missing PPO point invented. Final evidence
uses actual available recent rows separately from complete small-ledger totals
through73, keeping laterstep74out of those cumulative totals. This is a read-only
reporting limitation, not a training failure; source/deployment unchanged.
JSON/seed/natural-outcome/answer/CP/ETA consistency and diff checks passed.
No GPU diagnostics, model tests, runtime edits, restart or extra experiment.

## Terminal acceptance failure — September22 17:15Beijing

[Terminal evidence](qwen-l7-terminal-20260922-171508.json): training subprocess
ended17:02:06Beijing with result=.done/statuscompleted/exit0, global96 and94new
steps. The94console-derived metric rows each have a positive returned
update_actor duration, alongside94accepting pre-update audits and the exact
94same-seed batches/reset2..95. There are752natural training games,601wins and
151defeats/no truncation (79.9202%); these correlated training outcomes do not
establish held-out improvement. CP8..96 every8steps each have26required nonempty
files by stat, including sc2_state.pt; no checkpoint contents were read.

The outer verifier subsequently raised`Actual PPO/audit/gradient acceptance
failed` at qwen_l7_long197.py:275. Docker exited1/OOMfalse at17:02:34, root queue
and state arefailed. All audit decisions/counts, seed rows and recorded invalid
advantages pass the inspected predicates; the rejecting metric rows are
steps7,9,10,56,65,92 with recorded actor/grad_norm0.0. Final eval did not start,
and no full train acceptance artifact was issued. This is a terminal acceptance
failure despite successful training subprocess exit, not a completed experiment.

Frozen-source diagnosis at279d5496464de29e14c64924ccb829147351efbd:

- Actual effective_config uses trainer.logger=['console'].
- verl/utils/logger/aggregate_logger.py:27 formats every number with`.3f`.
- scripts/run_record.py:87 metric_rows reparses that rounded console; its
  finish routine writes those parsed floats into metrics.json at208.
- qwen_l7_long197.py:271–275 requires every recorded gradient to be finite and
  strictly positive. Its input is therefore not full-precision gradient data.
- Local CPU-only reproduction executed the frozen concat_dict_to_str function:
  both0.0 and0.0004 serialize as0.000 and fail the reparsed positive test;
  0.0006 serializes as0.001 and passes. This proves precision loss can cause a
  false rejection, not that these six historical raw gradients were positive.

**Correction to the16:54 follow-up note:** calling the pending gate
“full-precision” was incorrect. No raw gradient values have been recovered;
the six zeros cannot establish exact zero or strictly positive raw gradients.
Do not rewrite old metrics, mark these steps accepted, or weaken the gate.
Recorded validity is1 across all94metric rows; passing the earlier frozen
verify_common checks is additional controller evidence, not a fresh independent
scan of all large response/command logs in this monitoring round.

Existing strict storage receipt measured650,287,561,313bytes across the exact
three authorized roots, return0/no stderr; no storage-failure artifact. Original
deadline unchanged. Successor queue failed with`Predecessor failed; stop all
successors`, completed[], no suite/part dispatch and no successor containers.
All checkpoints and failed preparation/run evidence remain preserved.

Handoff: request authority for CPU-only full-precision PPO evidence/diagnostic
repair and then a separately reviewed no-retraining eval/continuation proposal.
No automatic repair, retry, checkpoint replay, budget reset, frozen edit or GPU
diagnostic was performed. The unique197-qwen-l7-seed96 heartbeat was deleted
through the app after terminal handoff; no remaining authorized active work.
The OpenAI Docs skill was used only to check scheduled-task management before
that deletion, not to authorize experiment changes.

Validation: small JSON receipt assertions,94metric/audit/seed predicates,
12checkpoint filename/size inventories, frozen-logger precision reproduction,
JSON parsing and git diff checks. No model/GPU tests. Per-round atomic record
commit/push and remote-SHA equality check remain required for this handoff.
