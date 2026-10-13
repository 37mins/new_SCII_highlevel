# Qwen Level6/7 × seed grouping: four bounded short acceptances

Current status September22 11:58Beijing: **r4 completed all three remaining arms**.
With retained r3l6-same, all four short acceptances passed:128natural games,
8actual PPO updates,929of929consumed answers valid. Paired wins/8:
L6same8→8, L6random8→8, L7same7→7, L7random7→8. No established learning gain
or seed-mode superiority. [Terminal evidence](qwen-r4-complete-20260922.json).
Unique197-qwen-r4 monitor deleted; no authorized long-training successor.

Prior status September22 11:08Beijing: **r4 l6-random fully completed;
l7-same passed pre and entered train2**. L6:32games/2actual PPO/249of249valid
consumed answers, paired8/8→8/8wins. L7pre:8games/0updates/49of49valid/7wins;
L7PPO completion not yet claimed, L7random pending. Fixed16:42:12 suite ceiling.
[Verified evidence](qwen-r4-l6-complete-l7-pre-20260922.json).
First r4PPO/L6completion/L7GPU-pre events notified; keep unique197-qwen-r4.

Prior status September22 10:51Beijing: **r4 l6-random pre passed; train2 running**.
Pre8natural games/0updates/8wins,49of49consumed answers valid, result=.done=acceptance.
First actual PPO is not yet established. [Pre evidence](qwen-r4-pre-20260922.json).
Pre completion notified in launch turn; do not duplicate it. Fixed16:42:12 ceiling.

Prior status September22 10:45Beijing: **r4 l6-random actually running pre**,
eight-rank SC2/fresh original Qwen/step0/zero updates. First dispatch10:42:12;
fixed total ceiling16:42:12Beijing, first-arm ceiling12:42:12. Not yet pre accepted
or PPO updated. L7same→L7random remain serial successors; r3l6-same is not rerun.
[Launch evidence](qwen-r4-launch-20260922.json); unique monitor197-qwen-r4 active.

Prior planned status September22 10:40Beijing: **user approved new r4 remaining three
arms**, maximum96games/6PPO/6wallh48GPUh. Preparation underway, no GPU dispatch
yet. Reuse accepted r3 l6-same; failed r3 remains unchanged. See r4 entry below.

Historical status September22 01:03Beijing: **r3 l6-same fully passed; l6-random
passed pre and is running train2**. First arm32natural games/2actual PPO steps,
239/239consumed answers valid, paired wins8/8→8/8. No demonstrated learning
gain from this saturated8game sample. Second pre49/49valid,8wins/0updates;
both Level7 arms remain pending. Suite deadline08:36:25.330Beijing unchanged;
second-arm deadline02:56:13.541. See the complete verification entry below.

Prior status September22 00:47Beijing: **r3 first arm l6-same is running
train2 after actual pre acceptance**. SpBr4 completed all3stages; Qwen dispatched
automatically at00:36:25.330. Pre8natural games/0updates,49/49consumed answers
valid,8wins; no completed PPO metrics yet at00:47. Suite deadline08:36:25.330
and first-arm deadline02:36:25.330Beijing are fixed ceilings, not ETAs.
All12model hashes passed. Failed r2 is preserved, never restarted.
Historical status2026-09-21 18:04:35Beijing: queued / waiting-predecessor,
not GPU dispatched, not GPU accepted; model verification was then pending.
2026-09-21 user requested Qwen at Level6 and Level7 with same-seed and per-game
random groups, then approved four short acceptances, **64 GPU-hours combined**.
User separately approved copying the registered original Instruct-2507 snapshot
from the node44 shared asset to a fresh node197 NVMe directory with full hashes.

## Matrix and question

| Serial order | Difficulty | Training seed protocol | Fresh initialization |
|---|---|---|---|
| l6-same | Harder / Level6 | one random seed shared by eight games in each UID | Qwen original |
| l6-random | Harder / Level6 | independently drawn seed for each of eight games, same UID | Qwen original |
| l7-same | VeryHard / Level7 | one random seed shared by eight games in each UID | Qwen original |
| l7-random | VeryHard / Level7 | independently drawn seed for each of eight games, same UID | Qwen original |

Question: does the repaired policy mechanically generate and execute valid plans
and perform two finite PPO updates in each of these conditions? Secondary paired
pre/post wins, action selections and execution outcomes are descriptive only.
No minimum wins for promotion, no automatic96steps. Eight-game evals/two training
steps cannot establish superiority or stable learning. Report wins/8 and paired
changes with uncertainty, not smoothed training curves as proof.

All four start from **Qwen/Qwen3-4B-Instruct-2507** revision
`cdbee75f17c01a7cc42f958dc650907174af0554`, manifest
`configs/qwen3-4b-instruct-2507.sha256`. No earlier Qwen3-4B/Base, project SFT,
SpB, D96, C96, L7 or preceding-arm checkpoint is allowed as initialization.
Post evaluation alone loads that arm's own complete step2 checkpoint.

To isolate grouping rather than also changing the seed range/RNG, **both arms
draw with replacement from0..100 using private Python Random(0)**. Same-seed
steps are `[49]*8`, `[97]*8`. Random steps are
`[49,97,53,5,33,65,62,51]`, `[100,38,61,45,74,27,64,17]`; collisions are allowed.
This is not a byte-identical historical D/C replay: D/native uses NumPy0..65534.
Same distributions do not imply the same realized scenarios in this short sample.
The mixed-seed UID deliberately retains the scenario-difficulty confound; do not
describe its advantages as unbiased policy-quality comparisons.

## Shared repaired protocol and exact limits

Every arm: 8pre games/0updates → 2PPO steps/16games → 8pairedpost/0updates.
At most32natural games,2h/16GPUh per arm; total128games,8steps,8wallh/64GPUh.
One suite clock starts at first Qwen GPU dispatch and includes loading, stage gaps
and later resource waits; each arm also has its own2h cap. No clock resets/retries.
After the frozen panel and SpB short acceptance **both pass**, wait for all8GPUs
idle/unowned,600GiB RAM, enough NVMe for remaining128GiB/arm plus12GiB headroom,
and fsync. First Qwen dispatch expires Sep22 06:15:40Beijing; latest possible
suite ceiling Sep22 14:15:40Beijing. These are ceilings, not promised finish times.
Any predecessor/arm failure stops successors and asks the user; no skip/retry.
Waiting allocates no GPU and does not reserve the shared node.

Flat128/Base75689, Terran Air, canonicalBO, Planner-from-opening setting,
T.8/192tokens/top-p1/top-k0/gamma1/combat.001/LR1e-6, existing Executor unchanged.
No D+ filtering/early-stop/resampling. Canonical action support plus no-thinking
in actor/oldactor/ref/rollout, post-centering invalid credit and quality floor.5
match the new repair, not the unchanged historical top-p.9 panel.
Pre/post use the same fixed8seeds and once-per-batch rank RNG reset from
[SpB acceptance](acceptance197.md), including across all four Qwen arms.

All acceptance gates from that record apply: matching result/.done/exit0;
clean frozenSHA/world8/finite metrics; exact natural game counts; nonempty100%
valid consumed answers; actual worker banners with Qwen tokenizer/mask hashes;
validated plan→queue→local Depot/Marine command evidence; actual2updates and
pre-PPO audits, finite positive gradients, invalid advantage≤0, full step2;
actual post checkpoint load, original eval seeds and zero updates.
Local commands and mechanically legal plans are not causal production/win proof.

## Minimal implementation and provenance

New `SC2_TRAIN_SEED_PROTOCOL=same_uniform101|independent_uniform101` selects only
the training reset sequence. Default `native` preserves both historical RNG
branches; evaluation is unchanged. The actual dispatched sequence is recorded.
Policy credit defaults to `seed_group_mode=same`, preserving strict actual-reset
checks. `mixed_seed_ablation` requires the explicitly matching independent protocol
and verifies group sizes/range/evidence; it does not disable credit correction,
validity guards, consumption checks or alter UID size. This is an explicit ablation
exception, **not a new repair default**. Training still forbids checkpoint resume.

`qwen_seed197.py` composes the bounded `acceptance197.py` engine in one process per
arm. The original controller defaults remain unchanged; its already-deployed
b2a011a and SpB runtime0172fb9 are never modified. The Qwen native launcher is a
thin adaptation of `run_seed_group_arm.sh@9a7b0fa` (this repository MIT license):
only model config changes to registered Qwen, SpB-only dropout override is absent,
and the approved2step settings replace the generic long-run defaults. Actual
merged configs must be tested for all12launches before enqueue.

Unique suite: `/var/jfsCache/sc2-qwen-seeds197-20260921-r2`.
Controller: `/var/jfsCache/sc2-qwen-seeds197-source-20260921-r2/code`.
Asset: `/var/jfsCache/sc2-qwen-instruct2507-cdbee75-20260921-r1/model`.
Tmux socket `sc2_qwen_seeds197_20260921_r2`, session `qwen_seeds197_r2`.
Each arm has separate deployment, readiness, dispatch, state, runs and owned
container `sc2-qwen-seeds197-20260921-r2-<arm>`. Runtime/controller clean SHA is
frozen in deployment; existing panel's image/venv/game/dependencies read-only.
New NVMe output plus code and copied asset ≤512GiB; no backend-repair claim.
Runtime source hashes/effective configs/model/SC2 manifests remain native run
provenance. No secrets or model weights in Git.

Prepare → CPU-only regressions and12actual dry entries → queue, each once;
preparation/tests alone are not GPU evidence. Exact commands, SHAs and results
are recorded below.

### 2026-09-21 preparation correction (no GPU dispatch)

The r1 host prepare reached the first arm configuration and failed to import
`agent_system` when invoked outside the repository cwd. Its source, partial root
and deployment are retained; no CPU container, queue or GPU run was started for
Qwen r1. The r2 host entry explicitly adds its frozen source root and checks all
arm configs before creating output directories. A subprocess regression runs
outside the repo with no PYTHONPATH. This is preparation repair, not a training
retry; the original64GPUh/128game and admission ceilings are unchanged.
The old SpB r1 was withdrawn by user approval before dispatch. Its replacement
is SpB r2 with manifest-only runtime `f211c0e94603468992baa514f00aaee5fd7780d6`.
Qwen remains gated on the replacement's actual three-stage GPU acceptance.
The first limited-time asset relay and failed private-network transport are
retained. The second relay has a five-hour transport bound and publishes only
after all12 registered hashes pass; copying does not allocate a GPU.

### Actual r2 CPU and queue evidence

- Clean privately-backed-up controller/runtime:
  `5e924e4e50a4c0724907ad6e8cbb6332e50e2ae2`. Each arm's deployment/readiness
  agrees with that SHA. Its source is independent of old Git alternates;
  the suite runtime uses the explicitly mounted new source object store.
- Host controller regression: `python3 -B -m unittest discover -s tests -p
  test_qwen_seed_acceptance197.py -v`:7passed, including a fresh subprocess
  outside repository cwd without PYTHONPATH. `git diff --check` passed.
- Actual container CPU commands were generated by `qwen_seed197.py cpu-command
  0`,1,2,3 and executed sequentially. All12pre/train2/post launchers, composed
  Hydra configs, source hashes, metadata hashes, architecture and seed-mode
  checks passed; all4readiness files have `qwen_arm_verified=true`,
  `cuda_initialized=false`. Evidence: `<arm>/cpu/{pre,train2,post}/`
  effective/resolved configs, source-check.log, and container.log.
- `qwen_seed197.py regressions-command 0` ran the actual pinned Torch CPU
  container against the registered Qwen tokenizer: **110tests passed,0skips**,
  15.402s, exit0; `l6-same/regressions.json` confirms CUDA uninitialized.
  Modules: test_sc2_action_support, test_sc2_policy_credit, test_sc2_task_signal,
  test_sc2_no_thinking_torch, test_thinking_action_boundary, test_r6_format_reward,
  test_original_bo_segment, test_original_game_seeds,
  test_policy_credit_acceptance197 and test_qwen_seed_acceptance197.
  Full log: `l6-same/cpu/regressions.log`. All5CPU containers are retained,
  exited0, Docker GPU DeviceRequests=null.
- Actual Qwen tokenizer hashes (computed, not assumed): mask
  `63a9546dd5fb39a64c6e2a2ad13f31101aacaade9bac07258d0e415480181e0d`, backend
  `a63080b4b30dc861fe1b0e420c53a241304dc81aff3d9bb315e6e33e2a1ab794`.
  They happen to equal the SpB tokenizer hashes; model weights remain distinct.
- At**18:03:25Beijing**, `qwen_seed197.py queue` was started once in the declared
  r2tmux session. At18:04:35, queue phase=waiting-predecessor, completed=[],
  first_dispatch_by=1790028940.699252, `dispatch.json` absent. It waits on
  SpBr2, not withdrawnSpBr1. This is real enqueue, not a GPU launch or reservation.
- Asset transfer uses the configured44/197SSH aliases in controlled local
  session59430 (`/private/tmp/sc2-qwen-relay2-20260921.sh`, exit receipt with
  the same basename and `.exit`). At18:04:35 first shard was128842752bytes and
  no published VERIFIED.sha256 existed: **copying, not complete/verified**.
  Source remains read-only. Receiver performs all12hashes and atomic publication;
  GPU gate additionally requires the registered manifest and native preflight.
- Existing heartbeat197 was updated in place to follow panel→SpBr2→Qwenr2 and
  the transfer receipt, retaining quiet healthy progress and failure/completion
  notifications. No duplicate monitor or additional GPU experiment was created.

### Terminal predecessor block / assets ready — September21 21:49 Beijing

SpB r2 failed in precheck before PPO; Qwen r2 queue now records
`SpB repair acceptance failed; Qwen successors blocked`, completed=[], with no
`dispatch.json`. All four arms remain unstarted; none is a Qwen model failure.

The authorized relay completed with local exit0. Published `VERIFIED.sha256`
contains all12 `OK` entries and FAILED.exit is absent. Receiver manifest and
registered `configs/qwen3-4b-instruct-2507.sha256` both hash to
`c82106ca091f4797af1217cca7578618bb2a5cd7c4136ca0d2d06c0a77ed00a7`.
The existing verification receipt hashes to
`6c2018e8f8a1b7b56ede8e605eacc13875d92cef76b2cb8a63e085dce6596b68`.
This audit read only small receipts/manifests, not weight contents. Asset
completion does not override the failed-predecessor gate. No retry/skip/queue
replacement occurred; all former staging evidence remains retained.
See [terminal handoff](terminal197-20260921.md). Monitor197 is deleted;
resuming GPU work requires a new explicit authorization and controlled run.

### User-authorized r3 replacement — September22, planned

User explicitly requested “你再在后面把实验排上，不要让卡空下来，之前说的qwen的实验也排上”.
This authorizes the same four unused short arms after **SpB r4 actually passes**,
not a failed-queue restart, gate bypass, GPU reservation job or long training.
The fresh wrapper `qwen_seed197_r3.py` selects:

- Suite `/var/jfsCache/sc2-qwen-seeds197-20260922-r3`, source
  `/var/jfsCache/sc2-qwen-seeds197-source-20260922-r3/code`.
- Socket `sc2_qwen_seeds197_20260922_r3`, session `qwen_seeds197_r3`;
  containers `sc2-qwen-seeds197-20260922-r3-<arm>` and independent run prefixes
  `qwen-seeds197-r3-<arm>-<stage>`.
- Exact predecessor `/var/jfsCache/sc2-policy-credit197-20260921-r4`, runtime
  `ce8b938341cd5b881b4dea8446ad570ed7509f78`. Its deployment and running
  controller are untouched. New queue records this subsequent authorization;
  the old SpB deployment's initial no-successor authorization remains historical.
- Same fresh Instruct2507 assets, four-arm order, seeds and repaired policy
  above. New clean runtime/controller includes the already115CPU-tested EOS/PAD
  transport correction, with no additional model/training/action/reward changes.
- Original **128games/8PPO steps/8h64GPUh/512GiB** and first-admission
  deadline1790028940.699252 (Sep22 06:15:40BJ) unchanged. No previous Qwen GPU
  dispatch consumed this budget. No resetting later clocks; 14:15:40 is only
  the latest possible absolute ceiling, not an ETA.
- Whole-suite storage checks now reuse the tested strict NUL-delimited root
  measurement used by SpB: bounded timeout, exact totals, retained stderr/failure
  receipt, no exclusion/retry/zero substitution. Both r1/r2 output and source
  roots, prior copy remnants, verified asset, new suite/source are included.
  New staging sits inside the new source parent and is counted. The historical
  live-du failure cause remains unknown; this does not promise backend recovery.
- Revalidate all24panel batches and all3actual SpBr4 stages before release;
  each Qwen arm needs eight genuinely idle cards and the unchanged resource/fsync
  gate. Polling while awaiting predecessor does not use GPU diagnostics or reserve
  the node. Any failed predecessor/arm stops the queue without retry or skipping.

Before single enqueue: clean SHA privately backed up, controller/whole-suite
tests, real Qwen tokenizer and worker-generation CPU regressions (zero skips,
CUDA uninitialized), all12native dry launchers/Hydra/source-hash checks.
Update existing monitor197-spb-r4 in place to follow both queues; no duplicate.

#### Actual r3 CPU readiness and enqueue — September22 00:12–00:13 Beijing

- Clean privately pushed runtime/controller **019a8b3a60aa093d61fccfb4293625e300a2894e**.
  `git diff ce8b938 HEAD -- agent_system verl gigpo configs` is empty: model,
  action, training, reward and registered source hashes match the tested repair.
  Only controller composition/whole-suite storage and tests/records changed.
  New source is a self-contained clone; no Git object alternates. Old frozen
  SpBr4 and Qwenr1/r2 deployments were not modified.
- Local `python3 -B -m unittest discover -s tests -p 'test_*197*.py' -v`:
  38tests,36passed+2Linux-only skips. Actual197Linux same command:
  **38passed/0skips**,0.098s. All12native pre/train2/post dry launchers,
  Hydra composition and31source hashes passed in four retained CPU containers.
- Pinned CPU image, real registered Qwen tokenizer plus the previously checked
  small SpB metadata fixture: **135tests passed,0skips**,8.655s. Includes actual
  worker→tiny-Qwen3 generation/EOS/PAD/teacher-support regression, credit,
  action support, whole-suite storage, correctr4 predecessor and ownCP2 tests.
  `regressions.json` passed=true, CUDA=false, exact019a8b3 at1790007150.6564336.
  All five CPU containers exited0 with GPU DeviceRequests=null. No GPU inference
  or learning claim follows from these CPU tests.
- Host test log under new source parent `staging/controller-tests.log`, SHA256
  `b7ceb9b9c3ba2be7511979143559241e1e3dfcc444630eb75099ed3cedfe8ead`;
  `l6-same/cpu/regressions.log` SHA256
  `570adc974ddaab9f2b651bec68f786d1db213059c1e8a4d65cd7c848fbd35339`.
- Real strict storage sample at00:13:23: **8,990,505,863bytes** across all nine
  required present roots, limit549,755,813,888bytes, du exit0/no stderr; deadline
  still null because no Qwen GPU has been dispatched. No measurements read
  weight/checkpoint contents; the verified asset was not recopied.
- At**00:13:23Beijing**, the declared tmux queue was invoked once, pane454460
  alive/python3. At00:13:37 `queue-state.json` was waiting-predecessor,
  completed=[], original first-dispatch cutoff unchanged, dispatch.json absent.
  SpBr4 was train2 with pre accepted; no PPO audit/metrics yet at that snapshot.
  Queue admission does not allocate or reserve a GPU. Each subsequent arm starts
  automatically only after all preceding actual acceptance/resource gates pass.
- Existing **197-spb-r4** monitor updated successfully in place as
  “197 SpB与Qwen短验收”, same task/every10minutes. It follows currentr4→fourQwenarms,
  not the failed old queue; normal waiting/progress stays quiet. No new monitor.

Immutable compact enqueue snapshot: [qwen-r3-enqueue-20260922.json](qwen-r3-enqueue-20260922.json).

#### r3 actual first GPU / pre accepted — September22 00:47 Beijing

The existing queue dispatched l6-same once at**00:36:25.330Beijing**
(`1790008585.3296254`), after completed SpBr4 and the unchanged panel/resource
gates. New suite deadline is**1790037385.3296254 (08:36:25.330Beijing)**;
first-arm deadline**1790015785.3296254 (02:36:25.330)**. These include model load,
stage gaps and subsequent waits; no reset/extension. Original first-admission
cutoff1790028940.699252 remains in queue provenance, now already satisfied.

Actual pre naturally ended at00:41:33.337, accepted00:41:41.354. Small
result/.done/acceptance records agree: exit0,8natural games,0truncation/updates,
finite metrics, clean019a8b3/world8. Frozen manifest identifies
`Qwen/Qwen3-4B-Instruct-2507`; dispatch mounts the newly verified Qwen asset
read-only at`/assets/qwen`. Freshstep0/no RL checkpoint, exact8eval seeds and
all8rank RNG receipts verified. Historical `Qwen3-30B` log directory and generic
`answers: online SpB` evaluation label are inherited labels, not model identity;
frozen model manifest and exact asset mount are authoritative. No label was
rewritten in the frozen run.

Actual pre:49/49valid consumed answers,49parsed plans,769validated queue
entries,374locally queued model Depot/Marine commands. Controller acceptance
includes actual worker support/tokenizer/mask and no-thinking checks; bounded
console tail confirms natural SC2 terminations and online validation metrics.
All8games won (marginal Wilson95% interval67.6–100%), with0PPOupdates: this
small baseline sample is neither RL improvement nor architecture superiority.

At00:47:30 state is train2/completed[pre]. A pre-PPO audit exists, but metrics
are not yet present; **do not call the before-update gate a completed update**.
The other three arms are still pending, not separately dispatched. Storage
00:47:26:9,048,077,452bytes across all9required roots, exit0/no stderr,
below512GiB. No new measurement was substituted for an error and no runtime,
frozen deployment, previous queue or old artifact was edited.

Snapshot:[r4-complete-qwen-r3-start-20260922.json](r4-complete-qwen-r3-start-20260922.json).
First actual Qwen GPU/SC2 and first-arm pre completion are notified in this
heartbeat. Same197-spb-r4 monitor continues quietly until next actual PPO,
stage completion, failure or decision; no duplicate monitor or extra budget.

#### l6-same completed / l6-random pre passed — September22 01:03 Beijing

First-arm training ended00:49:43.315 and was accepted00:50:11.939Beijing.
Post ended00:56:02.131, accepted00:56:12.465. All three small result/.done/
acceptance triples are exactly equal, exit0/finite, clean019a8b3/world8,
exact8/16/8natural games and no truncation. Arm statecompleted/exit0 and suite
completed[l6-same] agree. The frozen acceptance also verifies actual worker
support/mask/no-thinking and model-attributed plan→queue→local commands.

- **Two real PPO updates** fromfreshstep0 to2, finite positive gradient norms
  0.595/2.113. Two pre-update audits accept59/59 and58/58actual answers; exact
  dispatched same-uniform101 seeds49×8 then97×8. The audit's update0 field is
  before-update, not a contradiction of the completed metric/result evidence.
- Training117/117valid consumed answers,117parsed plans,1523validated queue
  entries,684local model commands;16wins/16natural games. Both metric rows have
  0invalid tokens,0invalid-positive removals and invalid advantage maximum0.
  This does not exercise the invalid-credit correction on an invalid sample.
- Complete ownCP2 has25required files, all stat sizes matched the result
  manifest. No checkpoint contents were read or rehashed by this monitor;
  stored native model-shard hashes remain provenance, not newly computed hashes.
- Post73/73valid consumed answers,73parsed plans,728validated queue entries,
  453local model commands. ActualownCP2load returned, paired8seeds and rank0–7
  RNG receipts matched,0updates. Pre/post both8/8wins; paired change0,8win→win.
  Marginal Wilson95% interval67.6–100% each, not a paired-difference interval.
  This already-saturated small sample cannot establish improvement, no effect,
  causal strategic learning or architecture superiority. Totalfirst-arm
  consumed validity239/239 across32natural games and2PPOsteps.

Second arm**l6-random** automatically dispatched00:56:13.541
(`1790009773.5412169`), independent fresh originalQwen, not the previousCP2.
Its deadline1790016973.5412169 (02:56:13.541Beijing); the suite's original
1790037385.3296254 (08:36:25.330) does not reset. By01:03:18 it had passed pre
and entered train2; both Level7 arms remained withoutdispatch. Pre ended
01:02:18.123, accepted01:02:30.154,8natural/0updates/8wins,49/49valid answers,
49plans/769validated queue entries/374local commands. Independently checked
result=.done=acceptance, clean019a8b3/world8, freshstep0, pairedseeds/rankRNG.
This repeated baseline is the preregistered pre stage for the independent arm,
not an unbudgeted extra replay. No second-arm PPO completion is inferred from
its running state.

Storage01:03:14:58,947,878,616bytes, exact9roots, exit0/no stderr, below512GiB;
no storage-failure receipts in the suite or any arm at01:01:41. No manual
prepare/queue/dispatch, retry, GPU diagnostic, runtime mutation or deletion.

Evidence:[qwen-r3-l6-same-complete-20260922.json](qwen-r3-l6-same-complete-20260922.json).
This heartbeat notifies firstQwenPPO, l6-same train/post/arm completion, and
l6-random actualGPU/pre completion. Previously notified SpB and l6-same pre
are not new events. Same197-spb-r4 monitor continues for the remaining work.

#### r3 terminal storage failure — September22 01:22 Beijing

Read-only heartbeat observations at 01:20–01:22 establish **host queue failed**,
completed=[l6-same], interrupted arm=l6-random. The failure was recorded at
**01:08:00.551950 Beijing** (`1790010480.5519507`). The full retained receipt is
`storage-failure-ec082ddc64654c43ab7d6feb98560748.json` under the suite root,
SHA256 `c8dc78d4c805d67a0796682bdeb51db5e543b2aa5928b2b057b1000a2c96121d`.
Actual GNU du returned1 with:

```text
du: cannot access '/var/jfsCache/sc2-qwen-seeds197-20260922-r3/l6-random/.storage-state.json.1555a950af464d808fa8ecb15e069242.tmp': No such file or directory
```

This is a specific **monitor-state traversal failure**, not an action-legality
gate failure, OOM finding, or proof that the storage quota was exceeded. The
failed total remains **bytes=null**; neither partial stdout nor the last good
58,977,358,212-byte sample (01:07:45) is accepted as its replacement.
All nine required roots remain covered, with no exclusions, ignored errors,
retries, quota changes or deadline reset.

The failed suite traversal ran 01:08:00.528–.552, overlapping the child sampler
(.522–.537) and state publication. The frozen019a8b3 `save()` creates a unique
`.storage-state.json.<uuid>.tmp`, fsyncs, then atomically replaces the final
file. The exact missing path and timing are consistent with the suite walker
racing that replacement. This is **different from the old shared-temp-name
collision** repaired earlier. No CPU reproduction or fix was run in this
heartbeat, and this evidence does not establish the historical SpB r3 cause.

The queue's automatic own-container `docker stop --time 10` then reported a
15-second client timeout. Docker inspection now confirms **exited137,
OOMKilled=false, Pid0**, finished **01:08:18.057 Beijing**. The remaining child
`running-unverified` state and manifest are stale, not evidence of live training.
No manual stop, GPU diagnostic, restart, frozen deployment edit or deletion
was performed by this monitor.

Scientific/authorization handoff:

- l6-same retains its previously accepted32natural games/2PPO and239/239valid
  consumed answers. Its8/8→8/8 evaluation remains saturated and inconclusive
  for learning; it is not invalidated by the later infrastructure failure.
- l6-random pre remains accepted (8games/0updates,49/49valid). Train2 has no
  result/.done/metrics.json, no train/post acceptance and no CP2. One pre-update
  audit accepts40/40answers with pending_global_step1 and before-update count0.
  **Completed PPO count is not established** by these retained small records;
  do not equate that audit's0 with proof of zero actual updates. Both prescribed
  random seed batches were registered, but registration is not completion.
- l7-same and l7-random have no dispatch receipts and were blocked by failure.
  Do not jump to them or restart any failed arm. Original suite deadline
  08:36:25.330 and arm deadline02:56:13.541 remain historical immutable limits,
  not permission to retry. All old and partial artifacts are preserved.
- Requested next decision: authorize **CPU-only deterministic reproduction and
  repair of measurement/publication concurrency**, preserving strict complete
  accounting, error evidence and deadline gates. This handoff neither performs
  that repair nor authorizes a replacement GPU attempt or extra budget.

Evidence: [qwen-r3-terminal-20260922.json](qwen-r3-terminal-20260922.json), including
small-file hashes, exact failure receipt, bounded log tails, Docker terminal
state, missing acceptance files and checkpoint file-list-only inventory.
Unique **197-spb-r4 monitor deleted successfully** via the app tool after this
terminal handoff; no live authorized successor remains. Only this new failure
and decision are notified, not the previously completed stages.

#### Approved CPU-only repair completed — September22 10:22 Beijing

The user's subsequent approval covered CPU reproduction/repair only, not a GPU
retry. [Storage coordination](storage-watchdog-fix.md#approved-publicationtraversal-coordination-repair--september22)
now has actual49-test Linux CPU acceptance (zero skips) on clean35f1705, plus a
CPU-only host/container lock-bind probe with exit0/DeviceRequestsnull. The
historical temporary-entry disappearance was deterministically reproduced with
real GNU du, then prevented by shared writer/exclusive sampler coordination.
Bounded lock failure still fails closed, and final-state write failure cannot
skip the existing owned stop attempt. Full accounting and unchanged seed/action/
reward/quality contracts remain; no error suppression or excluded directory.

[Evidence](storage-coordination-cpu-20260922.json). This is not GPU/model/learning
acceptance, and the prior Docker stop-client timeout is not claimed repaired.
r3 remains failed; first completed arm remains valid; all old results preserved.
No replacement queue/monitor/experiment was created. At this check the original
08:36:25Beijing r3 ceiling is already past, and was not extended. Any future run
requires a separate user decision and new immutable identity/budget.

### Explicitly authorized r4 remaining three arms — September22, planned

User approved the proposed new **l6-random → l7-same → l7-random** sequence,
maximum2hours/16GPUh each, combined6wallhours/48GPUh. This is an explicit new
attempt for the interrupted l6-random and two unstarted L7 arms, not a restart
of the failed/expired r3 controller. Completed r3 l6-same is revalidated and
retained without another GPU replay. Old partial l6-random costs/results remain
in history; its incomplete training cannot be resumed or treated as completed.

- New suite `/var/jfsCache/sc2-qwen-seeds197-20260922-r4`, source
  `/var/jfsCache/sc2-qwen-seeds197-source-20260922-r4/code`, wrapper
  `qwen_seed197_r4.py`; container prefix `sc2-qwen-seeds197-20260922-r4-`.
  Socket `sc2_qwen_seeds197_20260922_r4`, session `qwen_seeds197_r4`.
- All3arms independently initialize the original verified Instruct2507 snapshot.
  Per arm pre8/0updates → train2/16games → post8/0updates loading only its ownCP2.
  New total96games/6PPOsteps. Difficulty, seed sequences, action/credit/no-thinking,
  T.8/192/top-p1/LR1e-6/gamma1/combat.001 and all acceptance gates unchanged.
  Relative to r3, controller-only storage coordination and terminal cleanup
  protection are new; no model/training/action/reward code changes.
- New first-admission cutoff **Sep22 12:35Beijing (1790051700)** bounds idle
  waiting. First GPU dispatch fixes one21600second suite clock including later
  resource waits, with7200seconds per arm and45second cleanup margin. Thus latest
  possible ceiling18:35Beijing is an upper limit, not ETA. Old deadlines untouched.
- Retain512GiB inclusive ceiling: all r1/r2/r3 source/output roots, old copy
  remnants, verified asset and new source/output counted (11present roots).
  No extra storage quota. Before first dispatch require8emptycards/no computePID,
  600GiB RAM,396GiB freeNVMe (remaining128GiB/arm+12GiB) andfsync; recheck everyarm.
- Revalidate completed192-game panel, completeSpBr4 and r3l6-same. The failedr3
  suite is not relabelled successful. Any newarm failure stops successors; no
  automatic retry, seed switching, longtraining, SpB-L7 or other-node work.
- Existing model asset/VERIFIED receipt reused read-only; no transfer/oldCPload.
  Actual native preflight still validates asset hashes; no CPU result substitutes
  for model load, SC2 completion or PPO evidence.
- Stop-risk preparation at10:36:05Beijing exercised actual `stop_owned()` on one
  unique CPU-only container deliberately ignoringSIGTERM: forced exit137 in
  **10.060seconds**, inside unchanged15second client limit, OOMfalse/GPUrequestsnull.
  Evidence `/var/jfsCache/sc2-storage-coordination-cpu-20260922.bE413S/stop-check.json`.
  This is a current stop-chain check, not proof that previous GPU stop latency
  is root-fixed. Old container was independently confirmed exited/Pid0.
- Resource snapshot10:35Beijing:8×0MiB/0% with no computePID,
  797395344kB availableRAM,3234GiB freeNVMe. Not a reservation; dispatch rechecks.

Before single enqueue: clean privately-pushed SHA, Linux controller regressions,
real Qwen tokenizer/worker CPU regressions and all9actual DRY_RUN/Hydra/source
checks. Save actual dispatch and GPU evidence separately. Create one new quiet
monitor only after successful enqueue; prior197-spb-r4 remains deleted.

#### Actual r4 preparation, enqueue and GPU/SC2 — September22 10:40–10:45 Beijing

- Clean privately pushed controller/runtime **2f95c9fd505bd4529070ff4988c5c9efcb111b53**,
  separate self-contained source clone and frozen deployment. Runtime model,
  action/reward/training files unchanged from acceptedr3; only controller/tests/
  documentation differ. No old source, output or deadline edited.
- Local52tests:48passed/4explicitLinux-only skips. An initial new test fixture
  omitted LONG_DEPENDENCY_PATH and failed locally; fixture corrected before freeze,
  Qwen15tests then passed. Actual197Linux **52tests all passed,0skips**.
- All9actual pre/train2/post DRY_RUN/Hydra configs and31source hashes passed.
  Actual pinned CPU container/real Qwen tokenizer/worker regression **149passed,
  0skips,CUDAfalse**. All4CPU containers exit0/GPUrequestsnull. This is CPU proof,
  separate from the actual GPU evidence below.
- Completed panel/SpBr4/r3l6-same were fully revalidated without writing old roots.
  At10:42:11 strict storage usage59,023,498,631bytes across11roots, exit0/empty
  stderr, below512GiB. The dedicated tmux queue was invoked once at10:42:11.782.
- Actual GPU dispatch **10:42:12.273Beijing (1790044932.2731953)**. Fixed suite
  ceiling **16:42:12.273 (1790066532.2731953)**, first-arm ceiling12:42:12.273
  (1790052132.2731953); neither resets. Eight-card/RAM/NVMe/fsync gates passed.
- At10:44:53 actual pre checkpoint proof isfreshstep0/noRLcheckpoint/val_only/
  optimizer_updates0, original8eval seeds registered, all8rank RNG and eight
  game-boundary files present. Clean2f95c9f/world8 manifest names registered
  Qwen3-4B-Instruct-2507 revisioncdbee75. Container running with exact arm ownership
  label/GPUrequestall, bounded logs show active SC2 simulation and model plans.
  Legacy `Qwen3-30B` logger and `online SpB` descriptive string are inherited labels,
  not actual model identity. Pre/result/acceptance/PPO are not yet claimed complete.
- At10:44:42 current suite storage59,029,621,975bytes/exit0/no stderr; every
  measurement includes full11roots and shared metadata coordination. This is
  healthy current evidence, not a claim that arbitrary live-file races are solved.
- New unique same-task heartbeat **197-qwen-r4** created after checking obsolete
  monitors absent, every10minutes. Normal waiting/progress silent; firstGPU/SC2
  is notified in this launch turn, not repeated. FirstPPO and stage acceptance
  remain pending. Delete after full completion or terminal failure handoff.

Immutable compact snapshot with small-file hashes and bounded logs:
[qwen-r4-launch-20260922.json](qwen-r4-launch-20260922.json).

#### r4 first pre completed — September22 10:51 Beijing

Pre naturally ended10:47:34.037, accepted10:47:43.379. Independent small-file
check confirms result=.done=acceptance.result, exit0/finite/8natural/no truncation/
0updates. Actual consumed49/49valid,49parsed plans/769validated queue entries/
374locally queued model Depot/Marine commands. Eight wins are baseline outcomes,
not an RL improvement. At10:51:02 state istrain2/completed[pre]; no completed PPO
claim follows from stage entry. First-arm12:42:12 and suite16:42:12ceilings unchanged.
[Compact evidence](qwen-r4-pre-20260922.json). This pre completion was notified
in the launch turn; the unique197-qwen-r4 monitor now awaits PPO/stage events.

#### r4 l6-random completed / l7-same pre passed — September22 11:08 Beijing

Read-only checks at11:07–11:08 independently verified all three L6random
result/.done/acceptance triples: exit0, finite metrics, clean2f95c9f/world8,
8/16/8natural games, no truncation. Child completed/exit0 and host completed
[l6-random] agree. Train ended10:57:39.180, accepted10:57:59.131; post ended
11:02:09.551, accepted11:02:14.552Beijing. This is actual GPU completion,
not a CPU or merely file-existence inference.

- Two actual completed PPO steps, fresh0→2, gradient norms1.072/11.505.
  Pre-update audits accept50/50 and71/71answers; audit-before-update zeros
  are not update counters. Both completed metric rows and terminal result
  establish completion. Exact independent_uniform101 seed batches match the
  preregistered49,97,53,5,33,65,62,51 and100,38,61,45,74,27,64,17.
- Train121/121valid consumed answers,121parsed plans/1460validated queue
  entries/728local model commands;15wins1defeat. Invalid tokens/removals and
  invalid-advantage maximum are0in both rows: no invalid GPU sample exercises
  that correction branch. Mixed-seed UID scenario-difficulty confound remains.
- Complete ownCP2:25required files, every stat size matches the result manifest.
  No checkpoint contents read or rehashed. Post load returned ownCP2,step2;
  original8paired seeds and rank0–7CPU/CUDA RNG hashes match pre,0updates.
- Post79/79valid consumed answers,79plans/778validated queue entries/355local
  model Depot/Marine commands. Total249/249valid across32natural games.
  Pre/post8/8→8/8wins,8win→win pairs, difference0. Marginal Wilson95% interval
  67.6–100%each is not a paired-difference interval. This saturated small sample
  demonstrates mechanical acceptance, not improved strategy, no true effect,
  causal model contribution to wins or architectural superiority.

The controller automatically dispatched **l7-same at11:02:16.834Beijing**
(1790046136.8343916), independently from the original Qwen snapshot, not L6CP2.
Its arm ceiling is13:02:16.834 (1790053336.8343916); the suite's original
16:42:12.273 (1790066532.2731953) stays fixed, not an ETA. No manual launch.
Actual Level7VeryHard pre ended11:08:13.436 and accepted11:08:18.031:
result=.done=acceptance, exit0/finite/clean2f95c9f/world8,8natural/no truncation/
0updates, freshstep0/no RLcheckpoint, exact eval seeds/rank0–7RNG.
49/49consumed answers valid,49parsed plans/754validated queue entries/
521local model commands,7wins1defeat. Frozen acceptance covers actual worker
support/tokenizer/mask/no-thinking; bounded log tail confirms natural terminal
and online validation. Legality here is not a long-training recovery claim.

At11:08:29 L7same istrain2/completed[pre]; no completed L7PPO is claimed merely
from stage entry. L7random had no dispatch at11:07:16 and remains next in order.
Storage11:08:18:108,987,649,415bytes across all11roots, exit0/no stderr, below
512GiB; no storage-failure receipts at11:07:16, queue log tail empty. This does
not certify every possible live-file mutation or the historical stop timeout.

[Small-file/hash/stat verification receipt](qwen-r4-l6-complete-l7-pre-20260922.json).
This heartbeat notifies first actual r4PPO, L6 train/post/all-stage completion,
L7same actualGPU/SC2 and pre completion. Do not repeat these or the earlier
L6pre/firstGPU events. Keep the existing unique197-qwen-r4 monitor for remaining
work; no retry, deadline reset, frozen-source edit, GPU diagnostic or deletion.

#### r4 terminal acceptance — September22 11:58 Beijing

The last L7random post naturally ended **11:42:15.973**, accepted11:42:24.205;
its owned container exited0 at11:42:24.332Beijing. Host queue iscompleted,
completed=[l6-random,l7-same,l7-random],exit0; all three child states and Docker
states agree (exited0,OOMfalse,Pid0). The fixed16:42:12.273 suite ceiling and
all arm ceilings were respected, not reset. No manual dispatch or retry.

Read-only checks at11:53 and11:57–11:58 independently revalidated all12stage
result/.done/acceptance triples including retained r3l6-same: exact8/16/8natural
games perarm, no truncation, exit0/finite/clean runtime/world8. Each independent
training starts0→2, has two completed PPO metric rows, two accepting pre-update
audits, prescribed seed batches and complete ownCP2. All25requiredCPfiles perarm
matched recorded stat sizes; no checkpoint content read or rehash. Every post
actually returned from its ownCP2load, with original8eval seeds, matching
rank0–7CPU/CUDA RNG hashes and zero updates. Frozen acceptance supplies the full
actual-worker support/mask/no-thinking and consumed-plan/queue/local-command checks;
the monitor does not claim to have rescanned whole trajectories or big logs.

| Arm / retained run | Pre wins/8 | Train wins/16 | Post wins/8 | Valid consumed answers | PPO gradients |
|---|---:|---:|---:|---:|---|
| L6 same / r3 retained | 8 | 16 | 8 | 239/239 | .595 / 2.113 |
| L6 random / r4 | 8 | 15 | 8 | 249/249 | 1.072 / 11.505 |
| L7 same / r4 | 7 | 8 | 7 | 242/242 | .477 / 3.650 |
| L7 random / r4 | 7 | 14 | 8 | 199/199 | 45.049 / 8.241 |

L7same train accepted11:17:48.744, post accepted11:22:34.229. Train consumed
124/124valid,124plans/2128queue entries/1338local commands; post69/69valid,
69plans/787queue entries/497commands. Paired outcomes are7win→win,1loss→loss.
The training step8/8→0/8 uses different seeds49→97, so it is not a controlled
measurement of learning deterioration. L7random independently dispatched
11:22:37.050; train accepted11:38:23.792,96/96valid,96plans/1614queue/896commands;
post54/54valid,54plans/737queue/456commands. Its paired outcomes are7win→win,
1loss→win,0win→loss: an observed+12.5percentage-point change, only one game.

All four arms together have128accepted natural games/8actual PPO updates and
929/929valid consumed answers. This count includes r3l6-same once, not a rerun;
old interrupted attempts and their costs remain separately preserved. The r4
portion alone is96games/6updates/690of690valid answers. Both L6evals are saturated;
L7same unchanged and L7random improves one pair. Marginal Wilson95% intervals:
8/8=67.6–100%,7/8=52.9–97.8%; these are not paired-difference confidence intervals.
Eight evalgames/two updates perarm cannot establish strategic learning, no true
effect, random-vs-same superiority or architecture advantage. Realized training
scenarios differ and mixed-seedUID difficulty confounding remains. No sampled
invalid tokens occurred, so GPU updates did not exercise invalid-credit correction
on invalid samples. The restored100%legality is mechanically constrained, not
evidence that RL learned the format or that old SpB L7 long-run collapse is fixed.

Final retained successful suite storage receipt11:42:12.123:
208,871,961,301bytes (194.527GiB),all11roots,exit0/empty stderr,below512GiB.
No storage-failure receipts were present in r4suite/threearms at verification.
This is the existing final sample, not a newly forced measurement or proof of
backend root repair; historical failures and Docker stop-timeout limitations stay.

Evidence:[qwen-r4-complete-20260922.json](qwen-r4-complete-20260922.json), small-file
hashes, paired outcomes, stat-only CP check and bounded lastpost tail. The first
oversized verification response was transport-truncated after all assertions
passed; a compact read-only rerun of the verifier produced this complete receipt.
This was a receipt-collection retry, not an experiment or storage-measurement retry.
Documentation-only closure: JSON syntax/consistency and git diff checks; no new
CPU/GPU model tests or changes to frozen source, deployments or old results.

L7same completion and L7random GPU/pre/train2 were already reported in intervening
user-status replies; this heartbeat newly notifies lastpost and fullmatrix
completion. **197-qwen-r4 was successfully deleted** with the app tool under its
terminal rule; no duplicate monitor exists or successor is started. The earlier
human-facing proposal for QwenL7same→total96steps has not received approval.
No96-step or repairedSpB-L7 prepare/queue/dispatch, budget extension, L8–10,
IDSC resume or node46 operation is authorized by this heartbeat.

#### Subsequent human approval: single L7same continuation

The user subsequently approved QwenL7same from its accepted r4CP2 to total96,
and explicitly accepted the discovered missing-driver-RNG ledger restoration
limitation (not bitwise replay). Scope/limits/implementation and new unique run
are recorded in[qwen-l7-long197.md](qwen-l7-long197.md), within this same experiment
and branch. This prospectively supersedes the no-long-successor status above;
it does not rewrite any old frozen deployment or authorize replaying short arms.
