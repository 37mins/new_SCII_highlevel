# PPO iteration versus minibatch update (September24, read-only)

At14:56:50–14:59:46Beijing, compared actual effective command/override receipts
for freshQwen same, oldQwen same, Qwen random CP8 continuation and SpB random.
All use data.train_batch_size=1, env.rollout.n=8, actor rollout.n=1,
ppo_mini_batch_size=8, ppo_micro_batch_size_per_gpu=1, world_size8.
Frozen PPO epoch default is1 with no override; dynamic batching isfalse and
sequence parallel size1. The listed actor/FSDP/default-config/batch-alignment
implementation is unchanged between oldsame279d549, SpB83f3530 and current5228e9a.
[Selected receipts and timing aggregates](minibatch-semantics-20260924-145650.json).

## Counting convention

One reported global/PPO iteration is eight natural games collected in parallel,
then their consumed model-decision rows flattened into an actor training batch.
Each model decision is one observation/answer training row; a game can supply
multiple rows. The batch is split into minibatches, not reduced to eight games'
single final answers. PPO traverses this collected batch once (ppo_epochs=1).

FSDP normalizes minibatch8 × rollout.n1 / world8 =1row perrank. With microbatch1,
gradient accumulation is1: each synchronized optimizer step uses8rows globally.
The existing copy-padding path duplicates a few decision rows to an8-row multiple;
these are not extra games or independent data. From the verified short audits and
frozen code, step1's39unique answers ->40aligned rows ->5optimizer steps; step2's
57 ->64 ->8optimizer steps. These counts are code-derived, not separately
instrumented counters. Thus **96returned PPO iterations are not96optimizer.step
calls**. Historical PPO/update budget shorthand denotes outer iterations;
this explanation does not rewrite historical receipts or acceptance outcomes.

## Observed wall time, not a controlled speed benchmark

| Run / sample | Whole outer step mean | Collection mean | Actor-update mean |
|---|---:|---:|---:|
| FreshQwen same, first6steps |221.92s|185.24s|21.63s|
| OldQwen same, long94steps |141.19s|105.54s|22.16s|
| Qwen random, resumed88steps |170.02s|148.75s|12.92s|
| SpB random, long94steps |275.71s|253.60s|13.12s|

The fresh run has not demonstrated a speedup over oldQwen same. Collection
includes SC2 reset/game interaction and model generation; actor-update excludes
that collection. Model/seed/decision counts, response lengths, startup timing
and checkpoint/loading/admission waits affect duration. Different populations
(first6 vs complete94/88), model sizes and protocols prevent attributing these
means solely to architecture, kernels or minibatch choice. The current budget
is768training games +24evaluation games, not a claim of convergence.

## Current progress and preserved limitations

Main14:56 snapshot confirms returned global3–6 after the accepted two-step prefix,
all finite positive gradients/update times and invalidAdv0. OwnnativeCP2 load
returned, global2/reset2/next53x8. Exact long container running/unpaused/noOOM,
no failure, existing two-root50,114,527,761bytes/1TiB withdu exit0/empty stderr;
fixed September26 14:15:03.797deadline unchanged. Later audits7/8 and six closed
eight-game batches alone are not extra returned PPO proof. All observed reset2..7
seeds match same_uniform101. Native load is the newly verified milestone.

Fresh run changes include full-precision logging, new native full-stateCP2 and
SC2 startup serialization; it is not just a logger-only or bitwise repeat.
Historical oldsame gradient gaps still mean strict failed. No server mutation,
diagnostic, restart, deletion, duplicate dispatch or monitor change was performed.
