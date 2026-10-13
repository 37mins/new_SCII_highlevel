# L8 Qwen pilot: one authorized r4 remainder attempt

September 25, 2026, Beijing. The user approved one new r4 attempt of the
remaining eight stages / 64 natural games after r3 failed at its zero-game GPU
preflight. The first 32 accepted r1 games remain read-only. r2 and r3 each
added zero games and are not reclassified as successes.

The r3 preflight used a Ray `_temp_dir` long enough that a no-GPU reproduction
raised `AF_UNIX path length cannot exceed 107 bytes`. r4 uses the short
container path `/tmp/probe-ray`, mounted to the new accounted output root, and
captures early probe stderr/stdout in `gpu-preflight/entry.log`. This fixes
the observed r3 preflight path error; it does not establish that the earlier
r2 NCCL duplicate-device failure is solved. Eight unique CUDA UUIDs and an
eight-rank NCCL all-reduce must pass before the first game stage.

The only remaining protocol is the original L8 zero-update evaluation:
same three frozen model identities, 32 fresh held-out seeds, `CheatVision`,
eight serial stages of eight games, exact checkpoint load and seed/RNG pairing,
finite binary64 metrics, legal consumed actions and naturally terminated games.
There is no PPO training. The source and output roots are respectively
`/var/jfsCache/sc2-qwen-l8-pilot96-197-source-20260925-r4` and
`/var/jfsCache/sc2-qwen-l8-pilot96-197-20260925-r4`.

This is one one-shot run on node197, with eight GPUs serially, zero optimizer
updates, a fixed 4 wall-hour / 32 GPU-hour deadline from its first GPU
dispatch, and a **32 GiB aggregate cap over all eight r1–r4 source/output
roots**. No deletion, automatic retry, extra game, budget extension,
successor, or L8 RL training is authorized. Formal launch requires clean
GitHub-frozen SHA, exact historical failure receipts, actual launcher/Hydra
checks, zero-skip no-CUDA CPU tests, eight idle GPUs/no compute process,
600 GiB available RAM, 128 GiB free NVMe, exact GNUdu and fsync/readback.

The source SHA, CPU/GPU preflight, dispatch and terminal result are separate
actual receipts. Approval and this plan are not evidence that r4 has started.

## Actual fail-closed r4 outcome

The frozen `707cfb9` source passed eight actual CPU/Hydra launchers, 79 no-GPU
container tests and 71 host tests, all zero skip. r4 dispatched once at
23:45:54.465 Beijing with fixed deadline September 26 03:45:54.465. Its
eight-GPU preflight container exited1 without OOM, and the supervisor and
queue failed without dispatching any formal game stage. r4 therefore added
**zero natural games and zero updates**; the original 32 accepted r1 games
remain the only accepted L8 pilot prefix. [Compact terminal evidence](qwen-l8-pilot-r4-failure-20260925.json).

Unlike r3, Ray started with the short socket path. Its worker setup hook then
raised `ModuleNotFoundError: No module named 'feedback_eval'` before CUDA
identity or NCCL. The direct probe did not source the real launcher's
`EXTRA_PYTHONPATH`, which includes the feedback-evaluation directory. This is
an instrumentation mismatch, not an observed SC2 game or model failure.
The r2 duplicate-GPU issue is still untested. The r4 one-shot authorization
is consumed; no r4 restart or successor is permitted without a new budget.
