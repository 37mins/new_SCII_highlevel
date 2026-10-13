# Host supervision integration — CPU-only acceptance

The user accepted the [quiescent sampler proposal](storage-quiescence-fix.md)
and authorized host-side integration and loss recovery **on CPU only**.
Continue `codex/fix-quiescent-storage` from7305c46 in the same experiment record.
No GPU experiment, fresh experiment preparation/queue, old failed restart,
budget extension or new monitor is authorized. Original failed roots stay intact.

## Minimal integration

`host_stage197.run_stages` owns the sequential stages and the only storage
sampler. `docker_stage` changes the old Docker entry from an inner controller
to `child_stage`, which execs the same `l7_followup197.invocation` command and
environment. No training/action/reward/seed settings change; no sampling occurs
inside the container. Each stage gets a new retained container name and immutable
ID. Every stage requires the caller's fresh resource/fsync admission callback.

`supervise_part` is the future queue integration boundary: it refuses old
deployments without explicit `storage_supervision=host-guardian-v1` and refuses
prior state. It uses the unchanged full-precision/native-prefix/seed/action/PPO
verifier and publishes the compatible part state only after acceptance. It has
no prepare/queue CLI and is **not wired into any existing frozen queue**.
CPU fixtures use synthetic files, not fake experiment acceptance records.

Caller inputs are explicit exact inclusive accounting roots/quotas, receipt
paths, shared lock, **original absolute** account deadlines, stage list and
admission/verifier callbacks. Stage deadline must equal the earliest account
deadline; arm/suite clocks are not reset. All writable container mounts, host
control files, new source/preparation and failed remnants must be included.
The caller must prove the sole active non-controller writer is this container;
neither a label nor a test fixture proves that for a future GPU deployment.

One `storage_guardian197.Guardian` is armed **before Docker start**, in a separate
host session. A close-on-exec socket links it to the supervisor; Docker/du children
do not inherit that connection. The guardian requires a newly created, never
started container with exact full ID and `sc2.acceptance.root`, so it cannot adopt
an existing job. Only it starts, pauses and resumes the container.

- Normal sampling: exclusive metadata lock → guardian pause/verified state →
  the same strict GNUdu → guardian resume/verified state → unlock and receipt.
  The original15second sample allowance includes pause and recovery. No retry,
  missing-file filter, excluded root, partial total or last-good fallback.
- Guardian pause deadline cannot be extended by a heartbeat. Supervisor EOF,
  missed liveness lease (maximum45seconds), pause timeout or original stage
  cutoff triggers bounded restore and **one** owned stop attempt. One final
  inspection records whether it really stopped. No name lookup, kill fallback
  or action on another container. Recovery is attempted before receipt writes.
- Python `finally` is no longer the only protection: a killed supervisor closes
  the socket, while the detached guardian remains alive. If the guardian fails
  but the supervisor lives, the latter verifies/restores/stops the armed exact-ID
  stage. Recovery uses at most40seconds of the original45second cleanup reserve.
- Clean exit racing the pause request is verified once as exited0 and sampled
  statically; the command error, if any, is retained. Nonzero/ambiguous exit fails.
- Exit0 alone never advances a stage: static complete accounting, the original
  result/seed/load/PPO/CP verifier, and accounting/deadline recheck must pass.
  Any failure blocks every successor; no automatic restart/skip.

Guardian terminal receipt is created once before start, then its same inode is
written and fsynced at termination. There is no final rename/unlink or dependency
on the supervisor's storage lock. Empty/partial JSON is not a terminal receipt;
normal acceptance waits for guardian exit0 and reads it, then performs a fresh
static inclusive sample. Failure cleanup precedes publication; any append during
a failed measurement cannot turn that failed stage into an accepted sample.

## Verification commands and scope

Local selected regressions:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=tests python3 -m unittest \
 test_host_stage197 test_storage_quiescent197 test_policy_credit_storage197 \
 test_policy_credit_storage_coordination197 test_policy_credit_acceptance197 \
 test_policy_credit_acceptance197_r3 test_qwen_seed_acceptance197 \
 test_qwen_seed_acceptance197_r3 test_qwen_seed_acceptance197_r4 \
 test_l7_precision_continuation197 -q
```

Initial local result98tests,94passed/4explicit Linux-only skips. The first19tests
cover ownership, start-once, EOF, ambiguous pause, stop after recovery error,
bounded messages, stage exit/verifier gates, unchanged launcher arguments and
refusal of frozen old deployments. First Linux98tests passed zero skips on
clean0b73605, but the real-container probe failed: a clean exit immediately after
unpause was misclassified, and guardian failure publication waited for the
supervisor-held lock. Those CPU failures and all fixture containers are retained
in `/var/jfsCache/sc2-host-supervision-cpu-20260922.7lJiIO`.
The same-inode terminal receipt and clean-exit settlement address these two
observed boundaries. Two regression cases were added: local100tests now96passed
and4Linux-only skips. Final clean Linux confirmation is below. A preceding
bundle fetch named an absent branch ref; the bundle advertised HEAD. Correcting
the ref used the same committed SHA before any CPU/container test, not a GPU retry.

```bash
python3 -B tests/host_supervision_probe197.py NEW_EMPTY_CPU_FIXTURE_ROOT
```

This explicit probe uses the registered pinned image, CPU-only0.5CPU/64MiB
containers, no networking, read-only rootfs and one new fixture bind. No GPU
request, real model/SC2 mount or new experiment dispatch. It tests three serial
synthetic stages, a middle-stage exit7 blocking the last stage, SIGKILL of its
own supervisor while paused, pause expiry and liveness-lease expiry. Exact IDs,
independent recovery receipts and final Docker states are retained. Only owned
new CPU fixture processes may be killed; no old container or other task is touched.

Final Linux confirmation at21:20:07–21:20:15Beijing used clean pushed
`398eb99731be4f15b86caf546d07a3add433b0a8`: **100tests passed, zero skips/errors/
failures**, no torch/Ray/transformers/SC2 imports. All five real-container scenarios
passed; SIGKILL caused an independently recorded EOF → restore → stopped state.
Both expiry cases also independently stopped their stage. The intentional exit7
blocked post; synthetic normal pre/train2/post all exited0 and were verified.
These names are CPU fixture stages, not real SC2 games or PPO updates.

[Compact acceptance with raw artifact hashes](host-supervision-cpu-20260922.json)
records both attempts. New code2/probe2 never overwrote code/probe. All12CPU
containers across the failed and successful attempts were subsequently inspected
by exact ID: exited/unpaused, DeviceRequestsnull. None was removed. Small logs,
receipts and new source remain in the staging root above and must be counted in
future preparation. Git emitted an alternate-object nesting-depth warning;
required files/test fixtures resolved with zero skips, but future frozen source
preparation must explicitly materialize all required historical objects.

The adapter's unchanged invocation and absence of an inner watchdog were unit
tested. This round did not run real model launchers, Hydra configs or SC2 through
a new deployment; those remain part of the future authorized RUN preflight.
CPU lifecycle integration is accepted; no production/GPU acceptance is inferred.

## Remaining limits and continuation boundary

This cannot recover if both host processes, the host kernel or Docker daemon
are unavailable. Such failures require operator recovery and are not claimed
fixed. A successful Docker command is not substituted for final state evidence;
the historical GPU Docker-stop client timeout is not claimed solved.
Pausing GPU/SC2/Ray/NCCL still has no measured timing/equivalence evidence. The
user accepted testing this operational change; CPU acceptance is not GPU proof.

After CPU integration passes, any GPU continuation still needs a new authorized
RUN/deployment, exact all-writer/mount/accounting audit and frozen launch/config
acceptance. Keep SpB cutoff1790247962.305692 and suite cutoff1790420762.305692;
include all previous interrupted attempts and resolve interaction-budget usage
before dispatch. Do not replay accepted Qwen CP96 evaluation or use its weights
for Qwen-random. No queue/monitor is created by this CPU integration work.

Pending continuation proposal (not authorized by CPU acceptance): create a new
RUN for fresh SpB pre8→train2→post8, then its ownCP2→96 and Qwen-random's own
acceptedCP2→96, with the existing full gates. The failed r3 pre dispatched eight
slots with no accepted natural outcomes. Counting those plus the full original
remaining1552-game program gives an explicit upper bound of1560dispatched slots,
an increase of8interaction slots only; the original wall/GPU limits and absolute
deadlines do not reset or increase. This interaction allowance and new RUN need
user approval before freezing the new deployment, running its actual seven-entry
CPU/Hydra preflight and dispatching any GPU stage. Preparation must include both
CPU staging roots and all failed sources/outputs in exact inclusive accounting.
