# Proposed Qwen L8 zero-update difficulty pilot

September 25, 2026. Originally a recommendation. The user subsequently
**approved this exact 96-game, zero-update, 4h/32 GPUh/32 GiB pilot** and
separately approved pushing its frozen code/config/small receipts to the
existing `codex/fix-sc2-startup-port-race` branch. Approval is not evidence
that it was prepared, queued, dispatched or completed; those require separate
receipts below.

The common L7 64-seed test gave released Qwen 49/64 and both L7 CP96 policies
53/64. Each trained-minus-original comparison has four improved and zero
regressed pairs, but exact two-sided p=0.125; L7 generalization gain is not
confirmed. The SpB-same CP2/CP8 diagnostic has completed 40/64 and 37/64,
versus released 35/64 and CP96 16/64. Paired interval analysis for the two
new early checkpoints is still pending. Neither result authorizes L8 long RL.

**Approved GPU experiment:** one frozen new set of 32 L8
scenario seeds; evaluate the released Qwen3-4B-Instruct-2507, accepted fresh
L7-same CP96, and accepted L7-random CP96 on exactly those seeds. This is
3 x 32 = 96 new natural games, 12 serial eight-game stages, zero optimizer
updates, no checkpoint writes. The three arms share map Flat128, Terran/Air,
observation/action/canonical no-thinking support, prompt, generation budget,
Executor, reward and evaluation protocol. The only planned environment change
from current L7 evaluation is SC2 bot VeryHard -> CheatVision (historical L8
mapping); freeze a new effective config and verify the actual SC2 difficulty
at launch. Reuse original model and retained CP96 weights read-only, with
actual load, seed, RNG, game-terminal and consumed-action receipts. The
historical August L8 runs were canceled before training and are not controls.

Authorized resource ceiling: node197 only, eight GPUs in one serial queue,
**4 wall hours / 32 GPU hours / 32 GiB new source+output**, including setup,
gaps and evaluation, with a fixed deadline from first dispatch and no reset.
Based on the completed L7 Qwen128 evaluation (about 1h27m), 96 games might
take roughly 1–2 hours after dispatch; L8 game durations may differ, so this
is not an ETA or guarantee. Before any dispatch, recheck exact ownership,
eight idle GPUs/no compute PID, RAM/NVMe capacity, fsync/readback and the
frozen source/config. No retry, successor training, deletion, or budget
extension without separate authorization.

Primary output: paired natural win outcomes/returns and confidence intervals.
This is a difficulty/dynamic-range screen, not a powered proof of policy gain:
if all three arms cluster at floor or ceiling, do not automatically launch
96-step L8 RL. If the task is informative, preregister a larger confirmatory
evaluation or a matched L8 training comparison with fresh training-run seeds
and an explicit new budget. Qwen-only L8 evaluation cannot establish an
architecture advantage over SpB. Because the L7 64 seeds were used for model
selection, the L8 pilot must use newly frozen seeds; future confirmation must
use another untouched set.

References: [accepted L7 paired comparison](l7-common64-results-20260925.md)
and [completed SpB early-checkpoint summary](spb-early128-completion-20260925.json).
The CheatVision mapping was checked against the historical August L8 effective
config in the main project repository; that old canceled run is not reused.

## Frozen implementation and entry criteria

The declaration is in `qwen_l8_plan.py`; `qwen_l8_hook.py` only supplies
its new paired seeds to the existing evaluator; `qwen_l8_pilot197.py` provides
the one-shot host queue and strict stage verification. All 12 stages are
declared in advance and rotate the three arm positions. The 32 seeds are
`random.Random(20260925).sample(range(65536, 2**32-1), 32)`, without overlap
with the L7 64 held-out or eight original evaluation seeds. Every stage runs
eight natural games, with val-only and no optimizer/checkpoint writes.
Read-only predecessor checks bind both accepted Qwen CP96s to their receipts
and 26-file size inventories; they never load large weights in the controller.

The exact new roots are `/var/jfsCache/sc2-qwen-l8-pilot96-197-20260925-r1`
and `/var/jfsCache/sc2-qwen-l8-pilot96-197-source-20260925-r1`. Both are
jointly counted under 32 GiB. First dispatch must be within two hours of
preparation. The hard four-hour deadline begins at actual first dispatch and
is shared by all 12 stages, with a 45-second safety reserve. Each stage waits
for eight truly idle GPUs, at least 600 GiB available RAM and 128 GiB free
NVMe, then fsync/readback; waiting never reserves or stops others' tasks.
No retry, automatic repair, extra games, successor or L8 training is allowed.

Acceptance requires result=`.done`, exact container/owner/guardian exit 0,
clean source and binary64 metrics, actual model load (CP96 only), zero updates,
the declared eight seeds, natural terminal outcomes, 100% valid consumed
answers, and matching rank/CPU/CUDA initial RNG across each three-arm batch.
The CPU-resolved real launcher/Hydra must carry `SC2_DIFFICULTY` and
`SC2_EXPECTED_DIFFICULTY=CheatVision`; this is checked again against the
frozen runtime at stage execution. Each accepted stage additionally requires
eight real SC2 replay paths under `Flat128_CheatVision_Air`, binding the
effective environment to actual naturally terminated games. The L7 parent training results remain
separate from this new L8 evaluation; any L8 comparison is paired only on
these 32 new seeds.

Status at this initial amendment: **authorized and implementation in validation;
not yet queued or dispatched**. That historical statement is superseded by the
[actual launch and first-stage receipt](qwen-l8-pilot-launch-20260925.json):
source `9f8def1`, dispatched September25 17:53:08.526Beijing, fixed deadline
21:53:08.526Beijing. The first original-Qwen batch alone is accepted (3/8);
the complete paired comparison is still pending.
