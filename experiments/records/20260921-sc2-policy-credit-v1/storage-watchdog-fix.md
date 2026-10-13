# Storage watchdog diagnostic repair — CPU only, September21

The user approved **CPU repair/regression first, a separate decision before GPU
retry** after [r3's terminal failure](r3-terminal-20260921.json). No new GPU run,
queue, budget or monitor is authorized here. r3 and all frozen deployments stay
unchanged. The historical `du` exit1 lacks stderr: its precise cause cannot be
recovered, and transient-file disappearance remains only a hypothesis.

## Changes and unchanged safety boundaries

`acceptance197.py` now records each failed measurement in its own
`storage-failure-<uuid>.json`: exact command/roots, original deadline/limit,
timestamps, return code or exception, and stdout/stderr tails (8192 characters
each, original lengths and truncation flags). If the receipt cannot be written,
the same bounded diagnostic goes to the existing controller stderr log and the
failure still propagates. A last successful `storage-state.json` is **historical**,
never a fallback for failed current measurement. Separate failure files cannot
be erased by the other watchdog's later successful state publication.

Use GNU `du -sb --null -- <run-root> <source-parent>` once, with timeout limited
to 15seconds or the remaining pre-cleanup time, whichever is smaller. Validate
exit0, no diagnostic stderr, exactly one NUL-terminated nonnegative integer count
for **each exact root**, no omissions/duplicates/extra paths. Nonzero exit,
timeout, malformed or partial output is unknown usage, not zero. No directory
exclusions, error filtering, retry or fallback. This preserves `du`'s existing
apparent-byte/symlink/hardlink accounting; it does not create an atomic filesystem
snapshot. A concurrently mutating tree can still cause an intentional stop.

The original two-hour/16GPUh wall clock, 45second cleanup margin, 128GiB inclusive
ceiling, root coverage and ownership-checked stop behavior are unchanged. Check
the deadline again **after** measurement before permitting progress. Both host
and child watchdogs retain fail-closed behavior and cannot dispatch a successor
after a failure. No runtime/training/action/reward/seed/launcher change.

The shared `save()` previously used one `<name>.tmp` for all writers. A barrier
regression forces two writers to fsync before either rename and reproduces a
lost rename (`FileNotFoundError`) deterministically. Unique exclusive UUID
temporary files fix that separate race, including host/container PID-namespace
collisions. This is **not proof that this race caused r3's `du` failure**.
No frozen Qwen controller is edited; its shared future `save()` benefits from the
atomic-write fix, but its separate suite-level storage sampler is outside this
SpB repair and is not certified by these measurement tests.

## Verification

Local preliminary tests reproduced the old shared-temp race, then passed on the
candidate. Local macOS excludes the two actual GNU-du integration cases; those
must pass on node197 Linux CPU before this candidate is handed off as verified.

Commands (no model/SC2/CUDA imports or GPU allocation):

```bash
python3 -B -m unittest discover -s tests -p 'test_policy_credit*197*.py' -v
python3 -B -m unittest discover -s tests -p test_qwen_seed_acceptance197.py -v
git diff --check
```

Tests cover valid exact totals, quota equality, pre/post measurement deadline,
timeout/launch errors/nonzero exit/diagnostic stderr, truncated evidence, malformed
or missing counts, receipt write failure, concurrent atomic publication, and the
host/child stop paths (all process/GPU actions mocked). Actual Linux integration
measures only small temporary fixture roots, including a deliberately absent root
that makes real GNU-du emit exit1 and the exact missing-path diagnostic.

### Actual CPU result — September21 23:29–23:30 Beijing

- Tested clean, privately pushed commit
  `3e7141fb43e87e6c5ca0ad72c39885cdc202fe27` on the existing
  `codex/fix-invalid-policy-credit` branch.
- Unique staging `/var/jfsCache/sc2-storage-watchdog-cpu-20260921.d897mo`;
  self-contained clone, no old deployment edits. The host Python3.10.12 and
  GNU coreutils8.32 ran under a30second outer timeout with only small NVMe
  fixture files. No Docker/GPU launch, model/CP read, SC2 or torch import.
- Historical `save()` from controllera6aa4c3 fails the controlled two-writer
  barrier with `FileNotFoundError` (1test,1expected error). This independent
  defect is reproduced, not merely inferred from the r3 exit.
- Candidate **32 tests passed, zero failures/errors/skips**,0.083seconds:
  9common controller +1r3 protocol +15storage +7Qwen compatibility tests.
  This includes both real GNU-du integration cases that were skipped locally.
- A separate retained small fixture preserves actual GNU-du success followed
  by a deliberate missing-root exit1. The failed receipt records the exact
  missing path, stderr, partial stdout and **bytes=null**, not zero. It neither
  retries nor reclassifies the previous successful sample as current success.
- Local macOS run:23passed+2Linux-only skips in the25-test SpB/storage suite,
  plus7Qwen compatibility passes. `git diff --check` passed.

Remote command after checkout (the small harness and evidence are retained):

```bash
TMPDIR=/var/jfsCache/sc2-storage-watchdog-cpu-20260921.d897mo timeout 30s \
  python3 -B /var/jfsCache/sc2-storage-watchdog-cpu-20260921.d897mo/sc2-storage-watchdog-cpu-20260921.py
```

Evidence SHA256:

| Staging file | SHA256 |
|---|---|
| `regressions.log` | `fec2f2a895b66ebeee70d9e464751268d1e8bbe61ea594224c407eb9ece25b73` |
| `baseline-race.log` | `bfb255193db55856126db303d9364bbbf7a7ce9fbfda17ae699866383c72f32e` |
| `result.json` | `196e3f84751165c5bff2da2cb3d205a48b04ec3045e57b1a0425092c87cdd00b` |
| CPU harness | `31352df98ab424e4659f51ea338e0f4b5e69bc247379a0307381614241e3441e` |
| `retained-fixture/run/storage-failure-197646bb791842ae87168197e61e30d3.json` | `3647141fbc433e7848d153dbf569ea0b0677a5a86aa05e5fe25ddf9e37b41ef2` |

CPU success certifies these boundaries, **not historical root cause, reliable
live SC2 traversal, restored model validity, PPO or learning improvement**. The
old r3 remains exited137/OOM=false with0PPO; it is not resumed. No replacement
GPU queue/monitor is created. Any future GPU attempt still needs separate
authorization and a new frozen controller/run; there is no claim that this
diagnostic repair prevents every future `du` traversal failure.

## New Qwen r3 observation — September22 01:22 Beijing

The later Qwen r3 suite failed at01:08:00 while GNU du traversed a disappearing
child `.storage-state.json.<uuid>.tmp`. Frozen019a8b3 uses unique temp names and
atomic replacement: the new exact-path/timing evidence is consistent with a
walker-versus-publication race, distinct from the shared-name writer collision
covered above. Strict failure capture worked (exit1, full diagnostic,
bytes=null); safe concurrent live traversal is **not yet repaired or certified**.
The queue stopped, container exited137/OOM=false, and both Level7 successors
were never dispatched. A stop-client timeout was also retained, not hidden.

See [terminal handoff](qwen-seeds197.md#r3-terminal-storage-failure--september22-0122-beijing)
and [small evidence](qwen-r3-terminal-20260922.json). No new test, repair, retry,
measurement-error suppression, path exclusion or GPU launch was performed.
CPU-only follow-up requires the user's direction; old r3 failures remain intact.

## Approved publication/traversal coordination repair — September22

The user's subsequent approval is **CPU reproduction, repair and regression
only**. No experiment prepare/queue/dispatch, GPU allocation, failed-run resume,
new budget, frozen deployment mutation or replacement monitor is included.
Work stays on the existing experiment branch/record. Training, generation,
actions, rewards, seeds and acceptance thresholds remain unchanged.

### Minimal coordination contract

- `acceptance197.storage_guard()` uses one persistent `.storage.lock` inode.
  Standalone SpB places it under its new run root; Qwen uses its **suite** root
  for both suite and arm samplers and all controller `save()` calls. Read-only
  predecessor verification must never create a lock in an old SpB directory.
- `save()` holds a shared `flock` from before unique temporary-file creation
  through fsync and atomic replacement. Writers can still coexist because their
  temporary names differ. `measure_budget()` holds an exclusive lock throughout
  the single actual GNU du traversal, so those temporary names cannot vanish
  while that traversal is in progress. The stable lock file is counted, never
  removed or replaced. JSON readers still see atomically published files.
- Qwen's future child command adds one exact read-write bind mount of the suite
  lock inode, alongside the existing read-only runtime. It does not expose other
  arms' data as writable. The `--mount type=bind` form refuses a missing source
  file instead of silently creating a directory. New preparation creates the
  lock through its first metadata save; old frozen deployments stay unchanged.
- Lock acquisition uses bounded nonblocking polling. Measurement lock wait and
  du share the original15second/remaining-pre-cleanup allowance, with the original
  wall deadline checked after measurement. Ordinary metadata saves wait at most
  15seconds for this lock. Lock timeout is failure, never a measurement retry or
  permission to extend the experiment. Failure receipt publication does not
  wait again for a contended lock; bounded original evidence goes to stderr if
  its receipt cannot be written. No old successful total substitutes for failure.
- Exact root coverage (all9Qwen roots), finite totals, quota/deadline checks,
  error retention and no-successor-after-failure remain. No ENOENT filtering,
  excluded transient directories or repeated du. This coordinates **controller
  metadata only**, not an atomic snapshot of all SC2/Ray/checkpoint activity.
  Uncoordinated disappearing runtime files still fail closed. The separately
  observed Docker stop-client timeout is retained, not silently called fixed.

### CPU verification plan and local result

`test_policy_credit_storage_coordination197.py` covers distinct processes using
one lock, both scan→write and write→scan ordering, bounded lock timeout without
du/last-good fallback, lock time charged to the du allowance, failure release,
and Qwen suite selection even during predecessor checks. Existing tests retain
concurrent writers, exact/error/partial-total/deadline gates, no restart, same
launch protocols and all twelve stage configurations.

The Linux-only deterministic regression extracts **the exact historical save()
from frozen019a8b3**. A small test-only `LD_PRELOAD` fixture pauses real GNU du
after it discovers that writer's temporary directory entry; the writer then
renames it before du can stat it. It must produce actual exit1 and the missing
temporary-file diagnostic with bytes=null. The fixed companion test pauses the
writer at the same fsync boundary and requires that du cannot start until the
publication has finished, then accepts the complete error-free measurement.
The fixture is compiled only inside a small CPU test directory; it is never a
runtime preload, a measurement-error filter, or a model/GPU dependency.

Local macOS commands:

```bash
python3 -B -m unittest discover -s tests -p 'test_policy_credit*197*.py' -v
python3 -B -m unittest discover -s tests -p 'test_qwen_seed_acceptance197*.py' -v
git diff --check
```

Local result:34tests (30passed,4Linux-only skips), plus12Qwen tests passed;
diff check passed. Linux CPU reproduction/integration is still required before
claiming this repair verified. No GPU or SC2 game is launched by these tests.

### First Linux result and terminal-path completion

At10:18:04–10:18:05Beijing, clean privately pushed217a1f4 passed all46tests on
197 host Python3.10.12, **zero skips/errors/failures**. The real GNU du fixture
reproduced historical019a8b3 exit1/missing temporary entry with bytes=null;
the coordinated fixture returned0/empty stderr/complete totals. No torch, Ray,
transformers, SC2 or model modules were imported. Evidence retained under
`/var/jfsCache/sc2-storage-coordination-cpu-20260922.bE413S` as
`regressions-01.log` and `result-01.json`; logSHA256
`e3c375f6c6785cc3c99e853199078505d4a354f6d7b4c848022e9092755904cf`.

Follow-up review adds three CPU regressions for a directly related lock-failure
boundary: if final failed-state publication itself times out, the SpB host,
child and Qwen host must still reach their existing owned stop/process-group
interrupt in `finally`. Stop targets, ownership checks and signals do not change;
all stop calls are mocked in these regressions. This does not repair or dismiss
the historical Docker stop-client timeout. Expanded local result:37tests
(33passed,4Linux-only skips) plus12Qwen tests passed; final Linux confirmation
of the expanded patch is pending.

### Final actual CPU acceptance — September22 10:21–10:22 Beijing

- Final code SHA **35f1705b76b4e561d8b32bd94f2ad8dca0c2a418**, clean and
  privately pushed on `codex/fix-invalid-policy-credit`; separate `code-final`
  clone in the same new CPU staging, first clone/results preserved.
- **49tests passed, zero skips/failures/errors**, host Python3.10.12,
  10:21:37.656–10:21:38.377Beijing. Includes the real historical GNU-du race,
  fixed ordering, interprocess coordination, lock timeout/deadline accounting,
  all3terminal-publication cleanup guards, strict totals/error retention, and
  SpB/Qwen launch/seed/no-restart contracts. Stop/GPU operations in unit tests
  are mocked. No torch/Ray/transformers/SC2 module imported.
- Retained real historical reproduction: exit1, exact vanished UUID temp name,
  bytes=null. Fixed fixture: exit0, no stderr, exact2root total121bytes. These
  numbers describe tiny test fixtures, **not production storage measurements**.
- An additional one-shot **CPU-only container bind probe** at10:22:19 used the
  pinned existing image,1CPU/256MiB,networknone/read-only rootfs,no GPU request,
  no model/SC2 assets. It used final `storage_guard()` through the exact lock-file
  bind mechanism: blocked while the host held its lock, observed the same inode,
  then acquired after host release. Exited0/OOMfalse/DeviceRequestsnull; container
  and generated proof retained, not deleted. This proves the lock crosses the
  tested host/container mount boundary; it is not an SC2 or training acceptance.
- Expanded local check:49tests,45passed and4explicit Linux-only skips;
  `git diff --check` passed. No training/action/reward/seed code changed.

Actual host entry point (stdin harness loads the six modules listed below,
captures verbosity2 logs and asserts clean SHA/no heavy imports):

```bash
cd /var/jfsCache/sc2-storage-coordination-cpu-20260922.bE413S/code-final
TMPDIR=/var/jfsCache/sc2-storage-coordination-cpu-20260922.bE413S \
  timeout 45s python3 -B -
```

Loaded test modules: `test_policy_credit_acceptance197`,
`test_policy_credit_acceptance197_r3`, `test_policy_credit_storage197`,
`test_policy_credit_storage_coordination197`, `test_qwen_seed_acceptance197`,
`test_qwen_seed_acceptance197_r3`.

Retained final log `regressions-02.log` SHA256
`9a1fb96b2e2effcf85b7d569df0b3537ffefe49336c50bde7030739cdc88df59`;
result `result-02.json` SHA256
`4101d356326beafc7b87b1b64df0d889ce388d5482e3e16c6de3f67b94a344f5`;
bind proof `bind-check.json` SHA256
`085893a46f91403091c86043acbef009252e4036d5feed3ba67bc65741f153a6`.
Full compact receipt: [storage-coordination-cpu-20260922.json](storage-coordination-cpu-20260922.json).

The approved CPU repair is complete. No failed experimental root was modified
or restarted, no new GPU queue/monitor was created, and no old budget/deadline
was extended. A future separately authorized attempt needs a new run/config
and this source; the previously expired r3 is not a restart target. The result
does not certify an atomic snapshot of arbitrary runtime mutations or solve
the distinct historical Docker stop-client timeout.
