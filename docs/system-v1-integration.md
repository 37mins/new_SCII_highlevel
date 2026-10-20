# Canonical System-v1 integration

This page records the original August 31 packaging, not the current default.
The September 6 repair integration and current validation status are in
[Integrated Fixes v1](integrated-fixes-v1.md). Do not apply the historical
"unchanged reward/trainer" statement below to the repaired main branch.

This change packages existing behavior; it does not repair the Planner protocol,
change the learning objective or improve micro. The implementation starts from
remote main `d42096e2fe7f375b25d16b30fd151df10bbab308`, preserving its Instruct
entry point, SC2 log isolation and unrelated v1524 experiment records.

The default method is the Qwen r6 / SpB r7 contract. All model entry scripts
delegate to `scripts/train_sc2.sh`; `configs/system-v1.env` holds shared
defaults and each model config identifies exactly one original snapshot.
`configs/system-v1.sha256` freezes the existing Planner, SC2 manager,
Executor, reward, GiGPO and PPO implementation. These twelve files are not
modified by the integration.

The published r6 source is already a cleaned reconstruction of its historical
runtime, not a byte-for-byte original. The new SpB preparation function applies
the same r7 eight-line patch: in training, SSE uses the differentiable chunk
path even for short sequences; inference still uses the previous recurrent
selection. Native tokenizers and architecture-specific kernels remain different.

The optional Rush BO is copied byte-for-byte from
`codex/experiment-level6-system-ab-v1`, SHA-256
`e21c5a8518bc7c16a408ba7e245d0fd26c1a8aa6ab9d2410cb4c41c599d92f14`.
It concentrates the fixed opening into one base, three Barracks and 24 Marine
commands. No new prompt, attack-wave scheduler, completion gate, new micro,
SFT data, reward normalization or batch-padding semantics are included.

## Recording and failure behavior

The run directory is created atomically and must not already exist. Real
training requires a clean commit and verified assets. Before the trainer
starts, `manifest.json` captures provenance and `effective_config.json`
captures the full argument vector and Hydra overrides.

Ray's default temporary directory is `/dev/shm/sc2_<12-hex-hash>`, derived from
the run ID to keep Unix socket paths within Linux's
107-byte limit even with long run IDs. Explicit `RAY_TMPDIR` overrides are
preserved and must also be short and unique. The full run ID remains unchanged
in artifact directories and experiment metadata. The actual temporary path is
recorded in `effective_config.json`.

Existing seed and raw
prompt/response logging is unchanged; SC2 controller, Ray environment-worker,
game-agent, and rollout audit/debug output is separated under
`sc2-logs/worker-output/`. Trainer progress and metrics remain in `console.log`.
The Qwen long-loop launcher skips all-natural-terminal batches with no consumed
policy actions, without advancing PPO; it stops after 3 consecutive or 8 total
empty batches and records them in `empty_policy_batches.jsonl`. Set both
`SC2_EMPTY_POLICY_MAX_CONSECUTIVE=0` and `SC2_EMPTY_POLICY_MAX_TOTAL=0` to disable
this guard; otherwise both limits must be positive.
Long-loop `resource_memory` is an object with exactly five named targets in both
the model-summary output and persisted memory:

```json
{
	"resource_memory": {
		"recommended_mineral_collection_rate": "600 minerals/min",
		"recommended_vespene_collection_rate": "120 vespene/min",
		"recommended_mineral_utilization": "75%",
		"recommended_vespene_utilization": "50%",
		"recommended_total_supply_growth_rate": "12 supply/min"
	},
	"army_memory": []
}
```

Each resource target defaults to `null` until evidence is available. Missing or
extra resource keys and list-format model outputs are rejected. Existing saved
five-item resource lists are converted to the named object on load; the next
successful update saves the object format. Retrieval uses the key names, not
JSON field order. The example values above illustrate the format, not defaults.

Summary replay telemetry contains only absolute `game_time_seconds`, `minerals`,
and `vespene`, plus signed count deltas for `own_units`, `own_structures`,
`visible_enemy_units`, and `visible_enemy_structures`. Each map's first snapshot
is relative to zero; later snapshots are relative to its last available snapshot.
New types produce positive deltas, disappeared types negative deltas, and unchanged
types are omitted. Empty maps mean no change; missing maps are unobserved, not
zero counts. Positive changes use ordinary JSON numbers (`5`, not `+5`). Replay
JSON uses compact separators and retains terminal `won` outside telemetry.
Raw telemetry remains stored internally for metric computation and enemy-evidence
validation. Deltas are recomputed for each summary attempt without mutating it.
Visible-enemy decreases may indicate lost vision, not kills; count deltas do not
measure gross production or combat losses.

The summary prompt treats higher resource metrics as preferable during normal
game progression and established targets as non-decreasing minimum goals. Wins
may support higher targets; losing below any target preserves all existing targets
and directs reflection to unit matchups. Only when all targets are met does the
loss branch assess whether targets are too low. Missing measurements preserve
existing targets and do not establish attainment. These are prompt instructions,
not numerical update constraints enforced by the parser. Supply growth is still
measured as net supply change; gross production excluding losses is not yet tracked.

Long-loop resource targets must retain a numeric value; a low target is written
as `600 minerals/min (too low)`, never as `too low` alone. If telemetry contains
positive-count enemy units, a memory update must include at least one structured
army matchup; an empty army list is valid only when no enemy units were observed.
The summary prompt asks each matchup to target one enemy unit type, or two only
when their interaction requires a joint response, and prioritizes causal unit
mechanisms over roster coverage. Rationales should explain the mechanism and
essential limitations in 1-2 concise sentences. These are generation instructions,
not additional parser constraints; existing broad entries are narrowed on update.
Each memory-summary attempt appends its full prompt, raw model response, rollout
ID, status, and any error to `memory_summary_io.jsonl` beside
`long_loop_memory.json`. Summary generation defaults to a per-call limit of
1,024 new tokens (`SC2_MEMORY_SUMMARY_MAX_NEW_TOKENS`); policy-action generation
retains its configured response length. Qwen long-loop policy rollouts retain
the 4,096-token default input limit (`MAX_PROMPT_LENGTH`); memory-summary prompts
use a separate 8,192-token limit (`SC2_MEMORY_SUMMARY_MAX_PROMPT_LENGTH`). Both
can be overridden independently before launch. Other launchers retain the
system default.

On normal shell exit, `run_record.py` extracts the metric rows and writes
`metrics.json`, `result.json` and `.done`. Completed means the process
exited zero, steps 1 through the target are present, metrics are finite, and
all eight model/optimizer/extra-state shards plus data state exist and are
nonempty. Model shards receive SHA-256 digests; all checkpoint files record
sizes. Non-finite values are preserved as strings in the JSON evidence.
A killed host or SIGKILL can leave no final record; a start manifest is not
evidence that training is still alive or completed.

This is filesystem/numeric completion validation, not a claim of policy
quality. Large finite gradients, invalid plans, generation at the token limit,
or falling reward are not silently relabeled as infrastructure failures.

## Remaining scientific limits

Canonical keeps the six-action/96-token contract, the strict name parser,
the scheduled BO expansion, submission-based execution, the first-20/next-10
automatic-attack thresholds and old micro. The historical Qwen run had large
finite pre-clip gradients; the SpB run frequently reached its output budget.
Neither is a fully repaired model-policy baseline.

Rush seed2 was a good individual run, while seed1 had late-stage protocol
collapse despite high win rate. A seed is not a fix. The Level 6 7/8 Rush
observation is only a one-update System smoke, not sustained high-level
performance or an architecture result.

The integration is a candidate until Qwen and SpB each pass an authorized
GPU/SC2 smoke using this exact commit. Do not replace historical metrics with
numbers from a dry run or claim that this packaging has already reproduced
96 updates.

## Verification on 2026-08-31

The CPU suite ran with Python 3.12.13 and Gymnasium 1.2.3:
`python -m unittest discover -s tests -v` passed 14 tests. This includes real
Planner query/extraction tests, both model entry points in dry-run mode,
shared argument equality, exact Rush BO and source hashes, isolated SpB model
preparation, refusal to overwrite runs, and incomplete/non-finite result audits.
`bash -n scripts/*.sh`, Python AST parsing, JSON parsing, local documentation
link checks and `git diff --check` also passed.

No GPU/SC2 job or Docker image build was started for this integration.
The original working tree's uncommitted documentation was not modified.
