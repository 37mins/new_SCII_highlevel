# Clarifying fresh Qwen and corrected SpB retraining

September24 23:12Beijing, local archived-evidence review only. No server access,
new experiment, runtime mutation, checkpoint operation or Yuque publication.

## Terminology

The phrase "new fresh rerun accepted" referred to the September24 Qwen same
run, not to an unperformed SpB rerun. Fresh means a new SC2 RL run initialized
from the released Qwen3-4B-Instruct-2507 weights; it does NOT mean random weight
initialization/pretraining from scratch, and does not use old trained CP2/CP96.
It trains its own steps1–2, then resumes its own new nativeCP2 for steps3–96.

That Qwen rerun addressed an audit gap: six old same-run gradients had been
rounded by a three-decimal logger, so their required full-precision values could
not be recovered. The new run records binary64 metrics for every actual PPO
iteration. The historical run remains strict-failed; fresh acceptance does not
retroactively repair it, promise learning gain, or imply bitwise replay.

Accepted means the declared technical gates passed: actual returned PPO,
finite positive gradient/update durations, natural outcomes and consumed-answer
checks, native checkpoint/load provenance, and matching result/.done/acceptance
with owned-container terminal states. It is not an assertion of improved policy.
See [approved fresh definition](qwen-l7same-rerun-budget-20260924.md),
[actual fresh completion](qwen-l7same-fresh-complete-20260924.json).

## Corrected SpB long training was actually rerun

The low-validity historical SpB protocol and the corrected runs below are not
the same experiment version. Historical diagnosis includes0/1405 recent
consumed/evaluable valid answers and1391 repeated-closing-pattern responses;
old failures remain recorded. The
[validity analysis](yuque-validity-seed-analysis-20260924.md) distinguishes
observed output degeneration from unproven single-cause explanations.

Both corrected SpB conditions begin from original SpikingBrain-2.0-instruct
(approximately5.17B), not old L6 D/C or degenerated L7 checkpoints. Each follows
pre8 -> fresh train2(16games) -> ownCP2post8 -> ownCP2-to96(752games)
-> ownCP96eval8:96reported PPO iterations,768training games,792total natural
games including three8-game zero-update evaluations. A PPO iteration is not
necessarily one underlying AdamW/minibatch call.

| Corrected SpB condition | Training completion | Consumed training answers valid/total | CP2post -> CP96eval |
| --- | --- | --- | --- |
| same, runtime9cb291e | September23 11:45:25Beijing,96iterations/768games; terminal eval11:58:36 | 11313/11313 | 3/8 -> 2/8 |
| random, runtime83f3530 | September24 09:26:28Beijing,96iterations/768games; terminal eval13:45:08 after admission wait | 1959/1959 | 4/8 -> 5/8 |

Sources: [SpB same provenance and metrics](spb-l7same-curve-20260923.md),
[same terminal acceptance](l7-spb-complete-qwen-random-start-20260923.json),
[random96training totals](spb-random-train96-complete-20260924-093505.json),
[random terminal eval](spb-random-complete-20260924-134554.json).
The random train-completion receipt's pending-eval wording is a09:35 snapshot;
the later13:45 terminal receipt supersedes that state without rewriting history.

These corrected runs use canonical action-support constraints with matching
generation/training support, aligned EOS/PAD/top-p1, post-centering invalid
credit and the pre-PPO consumed-validity gate. Full validity is primarily a
protocol guarantee, not proof that RL learned formatting unaided. Different
historical startup/restoration settings preclude a claim of a seed-only or
bitwise comparison. The same3->2 and random4->5 eight-pair results do not
establish stable training benefit or degradation.

Validation: loaded archived JSON summaries and checked96/768 plus11313/11313
and1959/1959 against their cited records; no model tests were rerun. This is a
terminology/provenance clarification, not a new result or an experiment launch.
