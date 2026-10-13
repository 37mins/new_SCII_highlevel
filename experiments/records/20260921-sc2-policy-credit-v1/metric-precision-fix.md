# Metric precision repair and no-retraining proposal

Latest19:06:42Beijing: **new CP96 eval completed and accepted; SpB short
automatically dispatched**. Eval result=.done/exit0, host queue completed,
container exited0/OOMfalse, actual load96/paired8seeds+rank RNG verified,
clean469c77/world8/binary64-v1,8natural games/0updates/5wins3defeats/no truncation.
All23consumed answers are valid,23parsed plans/734validated queue entries/
604locally queued model commands; local commands do not prove production
completion or causal victories. Parent ownCP2 post was7/8, now5/8: two wins
became losses (env3,4), no losses became wins. Descriptive difference−25pp;
CP96 Wilson95% interval30.6–86.3%, paired exact McNemar two-sidedp=.5.
Only8pairs: **no demonstrated learning improvement**, not a robust degradation
estimate or architecture claim. Old six-gradient failure stays unchanged.
[Terminal and successor evidence](l7-eval-complete-spb-start-20260922.json).

SpB part singly dispatched19:06:02Beijing, start1790075162.305692;
short+long deadline1790247962.305692 (September24 19:06:02Beijing), suite
deadline1790420762.305692 (September26 19:06:02Beijing). These are ceilings,
not ETAs, and include all stage gaps. Original admission expiry was satisfied.
At19:06:42, SpB pre running with cleanworld8manifest; actual SC2/PPO proof
still pending at this snapshot. Qwen random waits behind complete SpB acceptance.
Eval completion has been notified; retain the monitor for both successors.

At19:08:09, SpB real5.17B worker/NCCL, actual canonical/no-thinking banners
(required tokenizer/mask hashes), freshstep0/0updates and paired8seeds were
verified. SC2Worker planner boundary/game_loop0 confirms the game started.
No old checkpoint loaded, no PPO yet. First SpB GPU/SC2 event notified; do not
repeat it. [Actual GPU/SC2 evidence](l7-spb-first-gpu-20260922.json).

Subsequent approval, September22: the user explicitly approved the proposed
continuation and historical evidence gap. At19:01Beijing the new evaluation is
**dispatched/running-unverified** and the new successor queue is waiting for it:
`qwen_l7_eval96_197.py`, new root `/var/jfsCache/sc2-qwen-l7eval96-197-20260922-r1`,
source `/var/jfsCache/sc2-qwen-l7eval96-197-source-20260922-r1/code2`; then
`l7_followup197_r3.py`, new root `/var/jfsCache/sc2-l7-followup197-20260922-r3`,
source `/var/jfsCache/sc2-l7-followup197-source-20260922-r3/code2`.
Old roots remain failed and untouched. Both runtime/controller SHAs are the
pushed clean469c77eb9c767f6db87dc4701401805fa22b46e2; orchestration remains
9a7b0faca5b145a891ad211f189121e4949f0eab. The eval was singly dispatched
at1790074800.934445 (19:00:00Beijing), with the original absolute deadline
1790227126.5133374 unchanged. The successor was singly enqueued19:00:01;
completed[] and no suite/part dispatch at19:01. See
[launch/CPU evidence](l7-continuation-launch-20260922.json).

The revised predecessor contract binds the old small receipt hashes from the
terminal snapshot, checks all12CP inventories by size, and permits only the
exact six unresolved rounded gradients. It records the historical failure,
not a passed training gate. New final evaluation must pass every actual
load/seed/RNG/natural-game/legality/zero-update gate with versioned full-precision
receipts and successful host/container exit before the replacement suite proceeds.
New training keeps the strict positive-gradient gate, without this historical
exception. Eight-game final eval uses the same read-only original model and
ownCP96, no new training. Existing resume-helper extensions for the approved
SpB-native/Qwen-random contracts do not activate in eval-only mode; resolved
evaluation config must equal the original frozen planned eval modulo relocation.

Eval fixed deadline remains1790227126.5133374 and its1TiB includes five roots:
new eval output/source plus old same96 output/source and parent r4/l7-same.
Replacement suite retains both failed r1/r2 output/source (four roots), plus
its new output/source and random parent: seven suite roots under2TiB.
Each arm's1TiB includes its new arm subtree/new source and all four old roots,
plus random parent for Qwen. Original48h per arm/96h suite and admission expiry
1790230726.5133374 unchanged. SpB short and long share one arm clock. No retries.
Callbacks change only names, fixed deadline/accounting and approved predecessor
boundary; action/reward/sampling/optimizer gates remain fixed.

Local final preflight:40CPU tests passed,0skips. Actual Linux eval and successor
regression runs each passed214tests,0skips, CUDAfalse. All8real launcher/Hydra
configurations (one eval and seven successor stages), source34hashes and
normalized old/new eval protocol equality passed. Six successful CPU containers
exited0 with DeviceRequestsnull. SpB long actual_parent_verified=false remains
an intentional future nativeCP2 gate; not skipped or declared GPU-ready.

The first Linux regression container failed6fixture errors because two
historical Git objects were invisible through shared-clone alternates inside
the container. Kept its exit1 container/log and copied the failed receipt to
cpu/regressions-missing-history.json. Imported a complete same-SHA Git history
bundle into each code2 object database, without changing tracked source/HEAD,
then used a new CPU container;214tests passed. This was CPU test-dependency
completion before any GPU dispatch, not a failed GPU retry. Bundles and both
candidate directories remain inside the inclusive source budgets.

At19:01, the actual eval container is running, manifest world_size8 and
metrics_precision=binary64-v1; bounded log confirms4.02B Qwen worker/NCCL.
CP96 load-return/SC2 and final acceptance were not yet present at that snapshot.
Five-root storage measurement650340460448bytes/exit0/no stderr is below1TiB;
measurement failures remain fatal/unknown, never substituted with this value.

At19:02:35Beijing, actual checkpoint_evaluation.json confirms load96returned,
val_only=true/optimizer_updates0, original8paired seeds registered. The actual
manifest is clean469c77/world8/binary64-v1. Bounded SC2Worker battle output at
game_loop5672 confirms real SC2 progression, not only prepared files. Final
result/.done not present; acceptance and paired RNG/answer audit still pending.
First new GPU/load/SC2 event has been notified; do not notify it again.
[GPU/load snapshot](l7-continuation-gpu-20260922.json).

Unique thread heartbeat `197-l7` is active every10minutes. It replaces no live
monitor (the failed chain's monitor had already been deleted); IDSC remains
paused. Per OpenAI Docs automation guidance and the user's notification intent,
healthy waiting/progress is quiet; only new real phase events, completion,
failure or required decisions notify. It must cover the entire new eval plus
both successors, preserving budgets and archival requirements, not stop merely
when eval completes. No extra task, training arm or resource reservation created.

First candidate4e7a2a7 host preparation failed **before root creation, CPU
container or GPU dispatch**: old result.json inventories only its finalCP96,
not intermediateCP8..88. The new reader incorrectly expected saved byte counts
for all12CPs. Corrected to the original26-nonempty-file stat gate for everyCP,
plus exact saved byte sizes for all26CP96files. Added a real tiny-file regression
covering final-only records, empty intermediate files and mismatchedCP96sizes.
Candidate `code` clones stay untouched; corrected committed source will use
fresh `code2` directories under the same fully counted source roots. No failed
GPU run or queue was retried; the final deployments were subsequently created
from469c77 and remain immutable.

Historical status, superseded by the approval/launch above: September22 2026
17:45Beijing **local CPU verified; GPU continuation
pending explicit approval**. The user's approval covers CPU repair, regressions
and a continuation proposal, not a new GPU dispatch, retraining or acceptance
waiver. Same experiment record and `codex/fix-invalid-policy-credit` branch;
this is an observability repair, not a new training method. Starting source:
`e441e0ba0d3dc68e87bd18154b526e5c299b49f2`.

## Failure and bounded repair

The frozen logger rendered every scalar with `.3f`; the run recorder reparsed
that console text into `metrics.json`. Both a true zero and a gradient of0.0004
therefore become0.000. Historical steps7,9,10,56,65,92 have only rounded evidence;
their original values cannot be recovered. The completed training subprocess
and CP96 are retained, but the original strict terminal acceptance **failed**.
This defect can erase small gradients; it does not prove those six historical
values were positive. See [terminal evidence](qwen-l7-terminal-20260922-171508.json).

The new logger uses17significant digits and an explicit `metrics_precision:binary64-v1`
marker. This round-trips the binary64 scalar given to the logger; it neither
recovers upstream tensor/reduction precision nor reconstructs old decimals.
The recorder declares the precision version in each new manifest/result and
records the logger/recorder source hashes. Both files are now covered by the
34-entry source freeze manifest.

New declared runs reject missing/wrong precision markers and duplicate PPO
step rows instead of silently falling back to rounded text. NaN/Inf remain
visible as failed finite-metric evidence. A missing marker raises before result
or `.done` publication; the supervising controller must treat that exception as
failure, never completion. No frozen run was processed or rewritten this turn.
Legacy parsing remains available for description, labelled
`legacy-console-unverified`, never upgraded to full-precision evidence.

No changes to model, prompt, sampling, action support, reward, advantage,
optimizer, learning rate, checkpoint or seed protocols. The real existing
terminal verifier is unchanged: gradient must be finite and strictly positive;
invalid-action advantage must be nonpositive. Full precision also prevents a
tiny positive invalid advantage from being rounded down into apparent compliance.

## Read-only diagnostic

From this repository root:

```bash
python3 scripts/diagnose_ppo_metrics.py /path/to/run
```

Reads only `metrics.json`, `result.json` and `manifest.json`, each limited to1MiB,
and prints a JSON report with their hashes, missing fields, nonpositive/nonfinite
gradient steps and positive/nonfinite invalid-credit steps. Missing/malformed
files, over-size receipts and a new-precision result/manifest mismatch fail
explicitly. `precision_declared` describes the receipts, not independently
verified runtime provenance. `acceptance_granted` is always false. No writes,
checkpoint reads, launch, retry, acceptance amendment or GPU initialization.
Do not run the recorder's mutating `finish` command on historical frozen runs.

## CPU verification

Executed locally with Python3.9.6; **69tests passed, zero skips**,2.281seconds:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=tests python3 -m unittest \
  test_metric_precision test_system_release test_signal_sampling_record \
  test_policy_credit_acceptance197 test_qwen_l7_long197 -v
shasum -a 256 -c configs/system-v1.sha256
```

The14new tests exercise actual logger→recorder→unchanged terminal verifier,
206binary64 values including subnormal/max finite values, actual LocalLogger
and Ray-prefixed lines, new manifest hashes, true zero/NaN/Inf rejection,
tiny positive invalid-credit rejection, version/duplicate failures, read-only
legacy diagnostics, and evaluation's zero-update rule. Existing tests cover
launchers, resource/failure gates, CP bookkeeping and source freeze; all34hashes
match. Fixtures are tiny temporary CPU data, not real model checkpoints.
No SSH, server writes, CUDA, live tokenizer/model load or GPU validation occurred.
These tests do not establish actual GPU repair acceptance or strategic learning.
[Machine-readable evidence](metric-precision-cpu-20260922.json).

## Proposed continuation — not dispatched or authorized by this CPU approval

1. **Retain CP96; no training replay.** Preserve the failed Qwen root, all12CP
   inventories,94update receipts,752natural games and the six unresolved raw
   gradients. Do not rewrite the old result, deployment, terminal state or
   claim every historical update passed strict positivity.
2. With separate approval, prepare a **new unique eval-only run** from that
   CP96: exactly8paired natural games,0updates, no new pre-eval or training.
   Keep Level7, model/action/reward/executor, original reference, sampling and
   seed/rank CPU-CUDA RNG matching unchanged; only metric provenance is repaired.
   The original absolute deadline remains September24 13:18:46Beijing
   (`1790227126.5133374`), with no reset of the48h/384GPUh ceiling. Count new
   evaluation/source/preparation artifacts together with all original three
   accounting roots under the same1TiB cap. Actual CP96 load, result=.done,
   exit0, cleanSHA/world8, finite metrics, natural games, zero updates, consumed
   action legality and local-command provenance must all be verified.
3. Such an eval can report **CP96 held-out behavior**, not rehabilitate the
   failed historical gradient gate or prove RL caused a gain. The paired seeds
   are605183188,1075501356,2084414326,2203880230,3000371298,949752300,3225036469,
   2823708076, as in the accepted parent post-eval;8pairs remain small-sample.
4. Only after explicit acceptance of the historical evidence gap **and a revised
   predecessor contract**, propose a fresh replacement successor queue:
   SpB L7same short+96 → Qwen L7random ownCP2→96, keeping the approved method,
   792+760newgames/96+94PPO, each<=48h/384GPUh/1TiB, total<=96h/768GPUh/2TiB.
   Preserve and account for old failed r1/r2 preparations; replacement roots
   must be added to inclusive accounting, not replace/exclude old roots.
   Keep the original admission expiry September24 14:18:46Beijing. No new
   predecessor rule is implemented in this CPU repair. Evaluation success alone
   must not silently waive the old gate or restart the failed queue.
5. Before any authorized dispatch: committed/pushed clean source, actual Linux
   CPU launcher/Hydra/source checks, eight fully free owned GPUs,600GiB RAM,
   1084GiB local space and fsync; do not reserve idle cards or stop others.
   A live monitor can be created for an authorized active continuation, but
   none was created in this turn. No prepare/queue/dispatch/retry occurred.

If the historical gradient evidence gap is unacceptable, retain this as a
failed-acceptance run and do not pretend CPU tests can fill it. Any new training
would require a separately scoped approval; it is not part of this proposal.
