# SpB L7same curve — September23 10:23:46Beijing

Run `/var/jfsCache/sc2-l7-followup197-20260922-r4`, frozen runtime
`9cb291ea5f50de205c5d88371e08ce229b7d9d04`. The [small snapshot](spb-l7same-20260923-102346-data.json)
contains source receipt SHA256s, native resume proof, serial queue/container
state,88paired seed/outcome/actual-consumption rows and latest returned PPO
metrics. The first two steps are its own accepted short run; remaining steps
are native ownCP2 continuation, not a replay or another model's prefix.

`collect-spb-l7-curve197.py` was executed read-only through SSH alias
`sc2-a100-197`, maximum1MiB per receipt and4MiB console tail. No checkpoint
content or complete large log was read. Actual natural outcomes and consumption
audits are charted only through the latest returned PPO step88. Audits alone
are not update completion evidence; final strict all-update acceptance is still
pending. No step89/unfinished game enters the curve.

Result:416/704training wins, last8steps35/64;10,963/10,963consumed answers legal.
Separate short evaluations: pre4/8, ownCP2post3/8; final96eval pending. Different
training seeds between steps confound visual learning-trend interpretation;
legality is constrained and does not establish strategic or architecture gain.

## Rendering and validation

The static renderer `plot-spb-l7-curve.mjs` reuses the prior Qwen/Level7 palette:
raw blue `#3274c7`, trailing8step mean orange `#c67a13`. No smoothing before
eight real points; no interpolation, zero filling, train/eval concatenation or
false break at ownCP2 continuation. Full planned1..96axis shows future region
in grey. Only the two fully audited metrics are drawn; cumulative episode reward
was not reconstructed from unread historical logs or confused with outcome reward.

From repository root, using Node with the registered bundled sharp package:

```bash
node experiments/records/20260921-sc2-policy-credit-v1/plot-spb-l7-curve.mjs \
  experiments/records/20260921-sc2-policy-credit-v1/spb-l7same-20260923-102346-data.json \
  /private/tmp/spb-l7same-20260923-102346-curves.png
```

Actual output directory is this task's registered local visualization directory
`/Users/yangjinyue/.codex/visualizations/2026/09/03/01a06605-4e2f-7052-925a-e3bf70ef2b4b`.
PNG `spb-l7same-20260923-102346-curves.png` SHA256
`f551306536dfeab14e1f75b08b963c6f702d16a01728a97a2114307e50e7d671`;
SVG with the same stem SHA256
`b465ddab7c99e3c7c6f53b0bedbb727336c9b04bb63d3b3b2975c5b5555fb9f6`.
Images are local presentation artifacts; reproducible data and scripts are in Git.

Actual validation: collector asserts all88complete eight-rank natural groups,
private Random0 seeds, positive consumption counts and agreement of recent
returned metric rows; renderer asserts step continuity, proportions, finiteness,
native load and latest-completed bound. Node syntax/render and git diff checks
passed;1440×1010PNG visually inspected for labels, colors, clipping and no gaps.
No model tests were rerun. No queue/runtime/storage/authorization changes.

## Completed1–96 snapshot — September23 21:24:20Beijing

User requested the completed experiment's complete1–96 metrics, a local snapshot
and the same blue measured/orange8step-mean chart. The prior88step snapshot above
is preserved. [New snapshot](spb-l7same-complete-20260923-data.json),343,185bytes,
SHA256 `34c7a709182e1c3e2a3500b03159330f9a1c00f88357f2683227758334a127a8`.
It includes every raw metric field from short `runs/train2/metrics.json`(steps1–2)
and long `runs/train96/metrics.json`(steps3–96), all96derived chart rows,
runtime/manifests/resume/terminal provenance and small-receipt SHA256s. Source is
the same immutable r4/SpB experiment and frozen9cb291SHA, not the current Qwen run.

Collector `--complete` reads only receipts≤1MiB each, no console log, checkpoint
contents, GPU diagnostics or remote writes. Both training results equal .done,
exit0/completed, cleanSHA/world8/binary64-v1,96finite metric rows; every recorded
gradient and optimizer duration is positive, invalid advantage max nonpositive.
Seed/outcome/consumption ledgers cross-check all96groups and8natural games/group.
The short1–2→long3–96 sequence has no holes/duplicates and is ownCP2 native resume.
The parent suite's failed Qwen successor does not negate completed SpB stages.

Results:445/768training wins(57.9427%), last8steps29/64(45.3125%),
11,313/11,313consumed answers legal. Separate0-update evals pre4/8 → CP2post3/8
→ CP96eval2/8. Training fluctuation is descriptive; cross-step seeds differ.
Legality is enforced by generation support and not evidence of strategic gain.
Eight paired evals show no demonstrated improvement, not conclusive stable decline.

```bash
ssh -o BatchMode=yes -o ConnectTimeout=10 sc2-a100-197 'python3 - --complete' \
  < experiments/records/20260921-sc2-policy-credit-v1/collect-spb-l7-curve197.py
node experiments/records/20260921-sc2-policy-credit-v1/plot-spb-l7-curve.mjs \
  experiments/records/20260921-sc2-policy-credit-v1/spb-l7same-complete-20260923-data.json \
  /Users/yangjinyue/.codex/visualizations/2026/09/03/01a06605-4e2f-7052-925a-e3bf70ef2b4b/spb-l7same-complete-20260923.png
```

The SSH result was saved locally using apply_patch. Node was the bundled runtime
from the workspace dependency inventory. Rendering preserves blue `#3274c7`
raw measurements and orange `#c67a13` trailing8step arithmetic mean, beginning at
step8 with no partial-window smoothing. The two100%legality lines overlap.
Final evaluations are text annotations only, not appended to training lines.
No interpolation/zero fill; full96completed axis has no pending-area label.

Actual checks: collector completed with all assertions; Node syntax/render passed;
1440×1010PNG visually inspected for both colors, labels, complete step96, absence
of future-region text and no clipping. PNG SHA256
`28ed7c967eac1175fb00561d9561ab81ae9897100b6ac58584af98b5baa005b3`;
same-stem SVG SHA256
`e1bb784ef924705ac2a7bb9eb9c466284da99ea39069c4a266db610d2c6d4b5f`.
No SpB experiment was dispatched, changed or rerun.
Additional local assertions passed: the first88derived rows exactly match the
old88step snapshot; full-metric steps equal1..96;89complete8step windows, final
mean29/64;445total wins and11,313valid consumed answers. `git diff --check` passed.

The initial upload was blocked by safety review because the complete343KB metrics
snapshot exceeded the earlier small-receipt scope. It stayed local/untracked;
only the already-authorized Qwen receipts were pushed separately as e52a028.
The user subsequently explicitly approved uploading this complete snapshot,
plotting script and explanation to CeraveNew/new_SCII branch
`codex/fix-sc2-startup-port-race`. No weights, credentials or full logs included.
