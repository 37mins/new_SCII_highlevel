# L7 completion matrix and proposed next experiment

Reviewed September24 23:04Beijing. Status/recommendation only: no new queue,
level, training run, deletion, restart or budget expansion is authorized or launched.

## Four trained conditions have reached CP96 and their terminal evaluation

| Condition | Accepted run lineage | CP2 post -> CP96 eval (eight reused pairs) |
| --- | --- | --- |
| Qwen same | Fresh96-update run, runtime5228e9a; old same precision-gap run remains strict-failed | 6/8 -> 8/8 |
| Qwen random | Valid short1–2 and long3–8 prefix, then nativeCP8 resumed9–96 suffix under3415428; not a new uninterrupted fresh96 run | 8/8 -> 8/8 |
| SpB same | Own shortCP2 ->96, runtime9cb291e; accepted training and eval before failed Qwen successor | 3/8 -> 2/8 |
| SpB random | Fresh short plus own nativeCP2 ->96, runtime83f3530; finaleval completed September24 13:45 | 4/8 -> 5/8 |

Sources: [Qwen same](qwen-l7same-fresh-complete-20260924.json),
[Qwen random](qwen-random-complete-spb-random-start-20260924.json),
[SpB same terminal](l7-spb-complete-qwen-random-start-20260923.json) and
[full96 metric validation](spb-l7same-curve-20260923.md),
[SpB random training](spb-random-train96-complete-20260924-093505.json) and
[terminal eval](spb-random-complete-20260924-134554.json).
These are execution/acceptance results, not four demonstrations of learning.
Neither SpB3->2 proves stable degradation nor4->5 proves improvement.
The old Qwen same failure, failed random-r4 branch and Qwen ancestor CP2
non-bitwise limitation are retained. Same/random runs also differ in historical
startup/restoration details; this is not a perfectly isolated seed-only ablation.

## Current permitted work

Original Qwen versus fresh-sameCP96 on64new paired seeds,128natural games,
zero updates. At23:04:18, eight stages accepted (64games/32completed pairs),
running b04-original; no failure, exact container running/unpaused/notOOM,
strict250,311,410bytes/32GiB,du0/empty stderr. All completed stages have
result=.done=acceptance.result,exit0,zero updates and fully legal consumption.
No final inference or stopping decision from these partial results.
[Small read-only snapshot](qwen-heldout128-status-20260924-230418.json).

## Recommended priority, not a launch authorization

1. Finish and analyze the already-approved128games under its frozen plan.
2. Before another long training run, complete a common L7 evaluation matrix:
   originalQwen, Qwen-sameCP96, Qwen-randomCP96, originalSpB, SpB-sameCP96,
   SpB-randomCP96 on the same frozen64scenario seeds. The current run supplies
   two arms128games; the four missing arms require256additional games, zero
   updates. Prioritize originalSpB and its twoCP96s to address the project goal;
   include Qwen-randomCP96 to complete both models' same/random comparison.
   Freeze protocol/comparisons/statistics before collecting added-arm outcomes,
   preserve existing gates/deadlines and create no writes in old runs.
   A separate approved wall/GPU/storage budget and per-stage resource admission
   would be required. This recommendation is not permission to dispatch.

For the proposed added arms, use identical scene/protocol/executor/generation
budgets and within-model paired sampling conventions, explicit actual-load
receipts, natural outcomes and zero-update evidence. Existing Qwen scores can
be reused only if provenance and evaluation protocol match; do not silently
change runtime semantics to claim pairing. SpB/Qwen parameter and compute
differences remain, so the table compares checkpoints, not pure architecture.
Report effect sizes, uncertainty and paired discordant counts; predeclare handling
of multiple comparisons. This now-common benchmark ceases to be a fresh holdout
for later model selection/tuning; a later confirmatory test needs untouched seeds.

3. Decide the next level from that evidence, not the old8/8 ceiling:
   - If L7 remains informative and SpB shows no clear benefit or trails Qwen,
     first audit saved advantage/return distributions, policy-gradient versus
     KL/entropy terms and clipping, then propose one controlled change. Do not
     assume these are diagnosed root causes or automatically extend training.
   - If broader L7 evaluation is near-ceiling and cannot discriminate checkpoints,
     propose a small paired L8 zero-update difficulty pilot first, not immediate
     full L8 training. Avoid an equally uninformative all-loss floor. Advancing
     difficulty can be justified as a measurement choice without claiming L7 RL
     improvement was proved. L8 is currently not authorized.
   - If a training effect is promising and the claim concerns the method rather
     than one checkpoint, budget independent training-run seeds with prospectively
     matched conditions; additional evaluation seeds do not replace train-run
     replication. [Methodological background](https://jmlr.org/papers/v25/23-0183.html).

Current recommendation: complete L7 evaluation evidence first; no additional
L7 long training or L8 long training is queued by this review. Retained CP96s
permit evaluation despite the previously authorized intermediate same-weight
pruning; do not repeat deletion or claim pruned intermediate CPs are restorable.

Validation this turn: read archived completion receipts and full SpB curve
documentation, recomputed current64-game accepted-stage consistency from small
server receipts, checked diff formatting. No model tests or large checkpoint reads.

## Additional evaluation duration estimate — September 24, 23:23 Beijing

Estimate only, based on archived timings; no fresh server poll or launch. The
four missing arms are Qwen-random CP96, original SpB, SpB-same CP96 and
SpB-random CP96. Each has 64 games on the same frozen scenario seeds:
256 additional natural games, zero training updates. Existing original-Qwen
and fresh-Qwen-same results are reused only with matching protocol/provenance.

The Qwen receipt at 23:04 records eight accepted stages / 64 games taking
42.00 minutes from initial dispatch to the eighth result, including loading
and intervening gaps: approximately 5.25 minutes per eight-game stage. The
completed SpB-random terminal evaluation container ran from 13:36:13.313 to
13:45:08.735, approximately 8.92 minutes for eight games. That is only one
SpB timing sample on the old evaluation seeds, not a measured throughput for
all three SpB arms or the new seeds.

A simple projection is 42.00 minutes for one Qwen arm plus three times
8 * 8.92 minutes for SpB, approximately 4.27 hours. Plan roughly **4–6 hours
after the additional queue actually starts**, with the models serial on the
same eight GPUs and eight games parallel per stage. This excludes preparation,
waiting for the existing queue/resources, and any failure requiring a decision.
An **8-hour / 64-GPU-hour hard cap is a proposal only**, not an approved budget
or a guarantee of completion; a complete resource/stop plan must precede any
authorization and single dispatch. The existing 128-game queue's approved
6-hour deadline is unchanged. No additional experiment was scheduled here.

Timing sources: [Qwen accepted-stage snapshot](qwen-heldout128-status-20260924-230418.json),
[SpB terminal container timestamps](spb-random-complete-20260924-134554.json).
Arithmetic was recomputed locally with Node; no model test was needed.

## Why fill the missing arms? — September 24 user clarification

This is a measurement step, not more training. Use the same frozen 64 new
scenarios as a common test for six checkpoints, reusing the two currently
authorized Qwen arms where protocol/provenance match. The four added arms
would answer questions absent from the current original-Qwen versus
Qwen-same comparison:

1. Compare each CP96 with its own original model to estimate that particular
   RL run's net change on unseen scenarios. CP2 is already trained and is not
   an untrained control. An original SpB arm is therefore necessary.
2. Compare same and random CP96 within each model on identical evaluation
   scenarios. Training batches change scenarios, and same-seed batches contain
   correlated games, so their curve heights/shapes are not a common test score.
   A common evaluation can rank these checkpoints, but historical startup and
   restoration differences and one training run per condition prevent a causal
   attribution solely to the seed grouping rule.
3. Quantify the observed SpB-versus-Qwen gap under common task/protocol settings
   and inform whether to investigate training or propose a harder-level pilot.
   Parameter/compute differences remain; this is not proof of an architectural
   effect. Broader L7 ceiling would justify an L8 measurement pilot, whereas
   weak SpB performance is not itself a reason to advance to L8 long training.

The previous eight reused pairs (including saturated 8/8 results) do not
resolve these questions. Sixty-four paired scenarios improve the measurement
but cannot guarantee detection of small effects or replace independent
training-run replication. Once used to choose/tune models, these scenarios
are a development benchmark; later confirmatory evaluation needs fresh seeds.

If the only question is whether fresh Qwen same improved over original Qwen,
finish the already approved 128 games: the extra 256 games are not needed for
that narrower question. They are proposed for the broader four-condition L7
comparison and SpB project objective. No extra evaluation was authorized or
launched by asking its purpose. Local documentation review only, no server
access, runtime changes or new tests; diff formatting checked.
