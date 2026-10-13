# L8 Qwen pilot: fail-closed r1 and once-only remainder r2

September 25, 2026, Beijing. The original 96-game, zero-update L8 screen
dispatched at 17:53:08.526 with an absolute 21:53:08.526 deadline. Its
host supervisor accepted the first four eight-game stages (32 natural games):
`b00-original`, `b00-same-cp96`, `b00-random-cp96`, `b01-same-cp96`. The
fifth stage, `b01-random-cp96`, exited 1 before any natural game, so the
controller marked the original queue **failed** and did not launch a
successor. The failed stage has a failure-valued `.done` recorder artifact,
but no acceptance receipt; `.done` alone is not success. These four accepted stages are retained, not retrospectively
relabeled as a successful twelve-stage experiment. The failed fifth stage
and its partial artifacts are retained as infrastructure-failure evidence.

The bounded terminal traceback for the exact failed container shows
`torch.distributed.DistNetworkError` / `EADDRINUSE` on rendezvous port 34627
during `ActorRolloutRefWorker` initialization. The container was not
OOM-killed, the failed stage has zero natural games and zero updates, and
the small storage receipt was below quota. This proves a distributed socket
bind failure, **not** that the SC2 policy lost, nor which process held the
port. The source's free-port probe closes its socket before Torch binds; a
port-allocation race is a plausible cause, not a proven exclusive cause.

The user explicitly approved **one** controlled continuation of only the
remaining eight stages / 64 games, using a new frozen commit, new unique
source/output roots and `RUN_ID`. The original 17:53:08.526 dispatch start,
21:53:08.526 absolute cutoff, **aggregate** 32 GPUh and **aggregate** 32
GiB for all four old/new roots are unchanged. No extra natural games, PPO
updates, L8 RL training, deletion, automatic retry, budget extension or
successor are authorized. The old 32-game accepted prefix is rechecked via
small result/`.done`/acceptance/guardian hashes and exact exited-0
containers before r2 admission and every r2 acceptance. r2 starts at
`b01-random-cp96`; the first four stages cannot be queued by its controller.
Batch-one new arms must match the already accepted `b01-same-cp96` seed and
rank/CPU/CUDA RNG receipt. Later paired batches compare within r2.

The r2-only mitigation makes Ray worker groups allocate distinct ports from
20000–29999 through a serialized ledger in the new run's accounted `/tmp`,
after checking the live Linux ephemeral range and that a candidate can bind.
It leaves policy/model/SC2 evaluation settings unchanged, but changes
distributed startup timing; it is not proof that all port conflicts are
eliminated. Any recurrence fails closed without another attempt. The
unchanged 128 GiB free NVMe, 600 GiB available RAM, fsync/readback, eight
idle GPU/no compute PID and exact owner/guardian checks still apply to each
new stage. The helper has no entry point to resume or mutate the r1 root.

Implementation: `qwen_l8_remainder197.py` wraps the original frozen
evaluator/host supervisor and `qwen_l8_hook.py` opts into the low-port
allocator only for r2. `tests/test_qwen_l8_remainder197.py` exercises the
eight-stage boundary, original clock/quota, port ledger and fail-closed
queue. This document is a plan plus diagnosis until a separate actual
prepare/CPU/queue/dispatch receipt establishes execution. Successful r2
would complete the original 32-seed, three-arm screen through two distinct
runs; it would not erase r1's failed terminal state or authorize L8 RL.

## Actual r2 outcome, 19:14 Beijing

The new frozen source `8f0fcf9` passed eight real no-GPU launcher/Hydra
checks, 81 container and 71 host regressions without skips, and the old
32-game prefix checks. r2 dispatched once at 19:09:35.169 with the same
original 21:53:08.526 deadline. Its first owned container
`14f04100b88834cb754125993c7848b35fae52d75c97172e916fe973945b93f0`
exited 1 before any new natural game or optimizer update. The host queue and
guardian failed; no r2 stage was accepted and no successor launched. The
aggregate four-root `du` was 187,296,343 bytes / 32 GiB after failure;
the eight host GPUs were idle. [Compact evidence](qwen-l8-pilot-r2-failure-20260925.json).

The low-port ledger allocated 28164, and the original EADDRINUSE error did
not recur. The new direct error is NCCL `Duplicate GPU detected` at reference
model FSDP initialization: all ranks were reported on CUDA device 10000,
despite Ray's debug placement groups assigning eight distinct GPU bundles.
This is infrastructure/device-visibility failure, not a measured policy
outcome. One plausible self-introduced cause is the r2 hook's early import
of `WorkerHelper`: that module imports `verl.utils.device`, which probes
`torch.cuda.is_available()` at module import, whereas the existing evaluation
hook explicitly avoids a CUDA probe inside Ray's worker setup hook. We did
not capture each worker's `CUDA_VISIBLE_DEVICES` at the point of failure, so
this remains an inference, not a proven exclusive cause.

The once-only continuation authorization has been consumed. The 32 accepted
r1 games remain usable as a partial screen, but the planned 96-game paired
L8 result is **not complete**. No further GPU dispatch, L8 RL training,
automatic retry, or budget reset is authorized. A future attempt needs a
new explicit choice and frozen, separately tested startup fix; preserve both
failed run roots and all four accepted original stages.
