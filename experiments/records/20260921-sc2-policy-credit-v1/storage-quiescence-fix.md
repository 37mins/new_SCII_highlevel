# Owned-container quiescence candidate — CPU only, September22

Subsequent user acceptance led to [host supervision CPU integration](host-supervision197.md):
100Linux tests and five real CPU-container lifecycle/fault scenarios passed.
The primitive results and original review boundary below are retained as history;
no GPU deployment or restart follows automatically from either CPU acceptance.

User approval follows the19:25 [SpB pre failure](l7-spb-storage-failure-20260922-192522.json):
CPU repair first, then review a continuation proposal. No new GPU run, failed
queue restart, budget extension or monitor is authorized in this round.

This changes process supervision, so development is isolated on
`codex/fix-quiescent-storage`, based on
`c0e8a2eba0684a8b1aded48396646a5def6c7fe2`. The original experiment branch,
all deployments and failed outputs remain unchanged. This is not a new model
method or a new experiment record; training/action/reward/seed code is untouched.

## Why the previous lock was insufficient

The failed frozen469c77 controller held the shared accounting lock correctly,
but compiler subprocesses do not participate in it. The retained failure
receipts identify disappearing `.ptx`, `.s`, `.o` and related paths during GNUdu.
Another writer lock or unique JSON filename cannot stop those removals.
Ignoring ENOENT, excluding tmp directories, trusting partial totals, moving
temporary data outside accounting, or using a previous total would violate
the existing budget contract; none is implemented.

## Implemented CPU candidate

`storage_quiescent197.measure_owned_budget(...)` is a **host-only, explicit
opt-in** wrapper around the existing strict sampler. No current launcher or
queue calls it. Inputs: full immutable64hex Docker ID, exact ownership-label
root, inclusive roots, receipt directory, original limit/deadline and lock root.
It rejects reusable names, an unaccounted writable root, or a sampler executing
inside a container. The caller must prove all remaining roots are immutable and
every uncoordinated active writer is inside the selected container; that fact
cannot be inferred merely from one Docker label.

Sequence:

1. Acquire the same exclusive metadata lock **before** pausing. This allows any
   controller currently holding a shared lock to finish, avoiding a frozen lock
   owner. Uncoordinated compiler children may still run until the next step.
2. Inspect exact ID and `sc2.acceptance.root` label; require running, unpaused,
   non-restarting state. Refuse ownership mismatches and pre-existing pauses.
3. Pause only this owned container, inspect again and require Paused=true before
   running one unchanged `du -sb --null -- <all exact roots>`.
4. In `finally`, inspect the same ID/label and unpause if needed; verify recovery.
   This also runs after an ambiguous pause timeout, du error or Python interrupt.
   Never resume an initially paused job. Recovery failure prevents acceptance
   and is retained in the failure receipt with the original du result.
5. Release the lock, then publish the existing atomic receipt. Exact roots,
   no stderr/nonzero exit, finite counts, quota and original wall-deadline gates
   remain. Unknown measurement is bytes=null, never zero. One measurement only.

Lock, pause, du and successful recovery must fit the original15second sampling
allowance. Recovery after a failure gets at most10seconds from the existing
45second terminal-cleanup reserve, never more measurement or experiment time.
The experiment wall clock is not paused. New receipts include paused/returned
state and timestamps, Docker ID, recovery outcome and measurement time.
The optional `quiesce` argument defaults to None, preserving existing launchers.

## CPU verification

Local command (no Docker calls; Docker is mocked):

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=tests python3 -m unittest \
  test_storage_quiescent197 test_policy_credit_storage197 \
  test_policy_credit_storage_coordination197 test_policy_credit_acceptance197 \
  test_policy_credit_acceptance197_r3 test_qwen_seed_acceptance197 \
  test_qwen_seed_acceptance197_r3 test_qwen_seed_acceptance197_r4 \
  test_l7_precision_continuation197 -q
git diff --check
```

Final local result:79tests,75passed,4explicit Linux-only skips. The17new cases cover
ordering, ownership, exact ID/root coverage, pre-existing pause rejection,
ambiguous pause timeout, unconfirmed pause, interrupted/failed du, failed
recovery, exit during sampling, unchanged roots/error policy and elapsed time.
The final extra test preserves du stdout/stderr separately from a later unpause
client timeout, rather than losing the original diagnostic to cleanup output.
An initial run exposed a legacy test's mocked-clock exhaustion; measurement-time
recording is now opt-in, preserving its old number of clock reads. A broader
local import of `test_l7_followup197` could not run because this macOS Python lacks
omegaconf; it is not recorded as a pass or hidden by the79-test result.

Explicit Linux CPU probe, after committed clean source is placed in NEW staging:

```bash
python3 -B tests/storage_quiescence_probe197.py NEW_EMPTY_FIXTURE_ROOT
```

It uses the previously registered pinned image and two new tiny CPU containers,
0.5CPU/64MiB each, networknone, read-only rootfs, no capabilities/GPU request,
one fixture-only bind, no model/SC2 mounts. The test-only existing LD_PRELOAD
fixture pauses real GNUdu after discovering `compiler.ptx`. An independent
container removes that file without the controller lock: baseline must produce
actual exit1/ENOENT/bytes=null. With the candidate, the same delete request cannot
execute until after measurement and unpause: real du must exit0 with all roots
and no stderr, then the writer must finish. Both containers and small diagnostic
artifacts are retained; only their owned fixture file is removed by the writer.
This validates the identified failure mechanism, not original compiler internals
or model/GPU behavior. No GPU claim is made.

First actual Linux run at20:42:47–20:42:48Beijing used clean privately pushed
`f47f90349f1223324bec8e42d67bf06029f254a1`, hostPython3.10.12/GNUdu8.32:
78tests passed, zero skips/errors/failures and no torch/Ray/model imports.
The real independent-writer baseline returned1/ENOENT/bytes=null; the fixed
case returned0/no stderr with59fixture bytes, followed by verified unpause
and deletion. Both dedicated CPU containers exited0/OOMfalse, DeviceRequests
null, networknone, sole fixture-only bind. Retained staging:
`/var/jfsCache/sc2-storage-quiescence-cpu-20260922.4LzwSM`.
This is a small CPU fixture, not an experiment storage-size or GPU acceptance.
Final confirmation at20:46:16–20:46:17Beijing used clean pushed
`8d085dfd82c1f8efdf92442f4c2d2d8921581761`: **79tests passed, zero skips,
errors or failures**, no heavy imports. The actual container probe again passed:
baseline du exit1/ENOENT/bytes=null; paused case exit0/empty stderr with71fixture
bytes, verified unpause and delayed writer completion. Both final CPU fixtures
exited0/OOMfalse/unpaused with DeviceRequestsnull. The59/71byte fixture totals
are not comparable experiment storage measurements.
[Compact evidence and raw receipt/log hashes](storage-quiescence-cpu-20260922.json)
retain both runs, exact commands/source SHAs and container scope. Final small
artifacts are `unit-result-final.json`, `unit-tests-final.log`, `probe-final.log`
and `probe-final/result.json` in the retained staging above. Four CPU fixture
containers across both rounds remain retained, all exited0. No GPU experiment
launcher was executed and no production integration is claimed.

## Required review before any GPU continuation

**Do not inject this wrapper into both old watchdogs.** Pausing the container that
runs a sampler would freeze the sampler itself. A replacement controller needs
one host-side sampling owner; child controllers must not independently scan the
live tree. Preferred integration: host supervises each stage, while the container
only runs that stage's unchanged launcher. Startup, stage exit and failure paths
need CPU integration tests before dispatch. Independent bounded recovery on host
supervisor loss is also required: Python finally cannot guarantee unpause after
SIGKILL, host crash or daemon failure. This primitive alone is not GPU-ready.

Periodic whole-container pauses could affect wall-clock-sensitive SC2/Ray/NCCL
timeouts and throughput. No gameplay or learning equivalence has been established.
Before GPU use, review that operational change explicitly, account every pause
within the same deadline, and verify the new supervision path in CPU containers.
If this is unacceptable, stop and choose an explicitly budgeted filesystem
snapshot/quota design; do not silently loosen the old du gate.

After separately approved integration/acceptance, propose a new unique RUN,
not restarting r3. Preserve accepted Qwen CP96 eval, all failed roots and original
SpB cutoff1790247962.305692 / suite cutoff1790420762.305692. No clock reset.
SpB has no accepted pre/PPO/CP2, so its pre cannot be claimed completed. Any new
8-game pre repeats interrupted attempts; count those attempts explicitly and
resolve the total interaction allowance before launching, rather than calling
them free. Qwen random must still use its own accepted CP2 after SpB passes.
Retain all output/source/CPU preparation in inclusive accounting. No new run,
container for training, prepare/queue/dispatch or monitor was created here.
