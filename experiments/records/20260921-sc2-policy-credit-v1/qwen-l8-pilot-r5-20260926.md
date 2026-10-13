# L8 Qwen pilot: one authorized r5 remainder attempt

September 26, 2026, Beijing. Status: **approved; preparing the new frozen
run, not yet dispatched**. The user approved exactly one new attempt of the
eight remaining eight-game stages / 64 natural games on node197. The first
four r1 stages / 32 games remain accepted and are not replayed. r2, r3 and
r4 added zero games. Their failed runs and evidence remain untouched.

The r4 GPU preflight started Ray with a short socket path but its worker
setup hook could not import `feedback_eval`. The direct probe had omitted
the `PYTHONPATH` that `run_qwen_seed_arm.sh` and `train_sc2.sh` export into
the real Ray runtime. r5 reads the actual CPU/Hydra-resolved first-stage
`ray_init.runtime_env.env_vars.PYTHONPATH` and passes that exact value into
the probe's Ray worker environment. A separate no-GPU Ray worker must first
run the same setup hook successfully and prove that `feedback_eval` loaded,
CUDA did not initialize, and no model/game/update occurred. Only then may
the eight-GPU identity/NCCL preflight run. This fixes the r4 instrumentation
parity error; it does **not** presume that r2's duplicate-GPU failure is fixed.

The frozen L8 evaluation protocol remains unchanged: released Qwen,
same-seed CP96 and random-seed CP96 are compared on the original 32 new
paired `Flat128_CheatVision_Air` seeds. r5 runs only stages 5–12 of the
original twelve-stage order, eight games each, with zero optimizer updates.
Actual stage acceptance still requires the correct model/checkpoint load,
paired seed and rank CPU/CUDA RNG, natural terminal episodes, all consumed
answers legal, finite binary64 metrics, replays, result=`.done`, exit0 and
matching owned guardian. No L8 RL training is authorized.

The new output root is
`/var/jfsCache/sc2-qwen-l8-pilot96-197-20260926-r5`; its isolated source
parent is `/var/jfsCache/sc2-qwen-l8-pilot96-197-source-20260926-r5`.
The single r5 dispatch gets a fixed **4 wall-hour / 32 GPU-hour** deadline
from first GPU entry, shared by GPU preflight and all eight formal stages.
All ten r1–r5 source and output roots count together under **32 GiB**.
No deletion, automatic retry, additional game, budget extension or successor
is authorized. Each GPU stage requires eight idle GPUs with no compute PID,
600 GiB available RAM, 128 GiB free NVMe, strict GNUdu and fsync/readback.
Formal dispatch also requires a clean GitHub-frozen SHA, exact historical
terminal receipts, actual eight CPU/Hydra launchers, zero-skip no-CUDA
container/host tests, and the new no-GPU Ray hook proof.

The source SHA, CPU/Ray tests, dispatch and terminal result must be separate
actual receipts. Approval, this plan and local tests do not prove a GPU run.

September 26 00:34 Beijing terminal correction: r5 is **invalid before GPU
dispatch**. Its eight actual CPU/Hydra configs, 93 no-CUDA container tests and
71 host tests passed, but the separate CPU-hook command exited1 at a CLI
dispatch typo (`globals()['cpu-hook']`). No Ray worker hook proof was made;
there is no `dispatch.json` or formal queue, and r5 added 0 games/0 updates.
The r1 accepted 32 games remain. Do not restart or edit this frozen r5 run.
[Compact exact failure receipt](qwen-l8-pilot-r5-failure-20260926.json).
