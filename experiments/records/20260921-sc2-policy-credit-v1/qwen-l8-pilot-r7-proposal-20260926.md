# Proposed r7 completion of the same L8 comparison

Superseded before implementation: user chose fresh Qwen L8 same96 RL instead.
This r7 evaluation proposal remains unapproved and must not be queued.

Status: **not authorized and not deployed**. r1 retains 32 accepted games;
r2–r6 added zero games. The latest r6 failed in the no-GPU Ray hook because
the direct probe omitted SC2PATH from the launcher's runtime environment.
The corrected v2 probe copies the full actual CPU/Hydra-resolved Ray
environment, changes only TMPDIR/RAY_TMPDIR to its isolated short path, and
uses zero Ray task retries. Four local contract tests passed. A real worker
pass is still required before GPU admission. Source/runtime copies should
use independent Git objects to avoid shared-alternate nesting.

Proposed scope: one new r7 RUN_ID, only stages 5–12 / the remaining 64 natural
games, 0 optimizer updates, node197 eight GPUs serial. New output and source
parent would be `/var/jfsCache/sc2-qwen-l8-pilot96-197-20260926-r7` and
`/var/jfsCache/sc2-qwen-l8-pilot96-197-source-20260926-r7`. All fourteen
r1–r7 roots would remain under the same 32 GiB aggregate ceiling.

The first actual GPU dispatch would start a fixed 4 wall-hour / 32 GPU-hour
clock; r6 never dispatched a GPU or started that clock. An actual no-GPU Ray
hook pass, full launch/config checks and unchanged parent/history evidence
are required, followed by one eight-GPU identity/NCCL check and the eight
formal evaluation stages. No deletion, automatic retry, extra game or L8 RL
training is included. The original released/sameCP96/randomCP96 protocol,
paired seeds, natural-game, legality, precision and final acceptance gates
remain the same.
