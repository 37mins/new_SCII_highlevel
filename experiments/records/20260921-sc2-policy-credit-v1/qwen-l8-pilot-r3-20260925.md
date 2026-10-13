# L8 Qwen pilot: one newly authorized r3 remainder

September 25, 2026, Beijing. Status: **approved, implementation/preflight in progress;
not yet prepared, queued, or dispatched**. This note supersedes only the old
one-shot authorization limit for the new run. It does not turn either failed
run into a success or approve L8 RL training.

The r1 L8 screen accepted 32 natural games in its first four eight-game
stages, then failed before another game at Torch rendezvous `EADDRINUSE`.
The authorized r2 continuation accepted zero new games and failed before its
first game because NCCL saw all eight ranks on CUDA device 10000. The actual
per-rank cause was not captured. An r2-only setup-hook import of
`WorkerHelper` (which imports a module that probes CUDA) is a plausible
regression because Ray GPU visibility is assigned later; that is a hypothesis,
not a proven exclusive root cause. The original records and run roots remain
untouched.

The user has now explicitly approved **one new r3 attempt** of only the eight
unrun stages / 64 games, on node197 using eight GPUs serially, zero optimizer
updates, at most **4 wall hours / 32 GPU hours from the first r3 GPU entry**.
All six r1/r2/r3 source and output roots count together under **32 GiB**.
The r3 first dispatch starts a new, fixed four-hour deadline shared by its
GPU visibility/NCCL preflight and all eight games stages; this is a new
budget, not a reset or reinterpretation of the expired r1 deadline. No
deletion, automatic retry, extra games, budget extension, successor, or L8
RL training is authorized. The accepted 32 games are read-only predecessors,
never replayed by r3.

The only new source change moves the opt-in low-port allocation into
`WorkerHelper._get_free_port`, called when the Ray actor is constructed,
instead of importing `WorkerHelper` in the early Ray setup hook. This retains
the low-port ledger mitigation without the hook's premature `torch.cuda`
probe. It does not alter the Qwen weights, SC2 environment, prompt, action
support, evaluation seeds, temperature, or zero-update protocol. The new
`qwen_l8_cuda_probe.py` runs eight one-GPU Ray actors under the same setup
hook, requiring eight distinct CUDA UUIDs and a successful eight-rank NCCL
all-reduce before any natural game. It loads no model and runs no SC2 game or
optimizer. A failed preflight closes the queue with no game successor.

`qwen_l8_remainder3_197.py` is the unique r3 controller and stage entry.
It checks the r1 accepted-prefix receipts, r2 failure receipts/container,
both retained CP96 parents, clean frozen runtime, real launcher/Hydra and
zero-skip CPU tests. Admission and every stage require eight idle GPUs with
no compute PID, 600 GiB available RAM, 128 GiB free NVMe, six-root strict
storage measurement and fsync/readback. The new roots are
`/var/jfsCache/sc2-qwen-l8-pilot96-197-20260925-r3` and
`/var/jfsCache/sc2-qwen-l8-pilot96-197-source-20260925-r3`.
The 32 new L8 seeds, twelve-stage order, three model identities and
`Flat128_CheatVision_Air` setting remain frozen by the original
`qwen_l8_plan.py`; r3 starts at `b01-random-cp96` and runs only the last eight
stages. Acceptance still requires actual CP96 load, eight naturally
terminated games, zero updates, full-precision finite metrics, all consumed
answers legal, exact seed and rank CPU/CUDA RNG pairing, eight replay paths,
result=`.done`, exit 0 and matching guardian/owner.

The source SHA, CPU/GPU-preflight, dispatch and final outcome must be added
as separate actual receipts. Approval, this plan, and CPU tests are not proof
that the new experiment is running.

## Actual fail-closed r3 outcome

The frozen `0c49f2b` source passed eight actual CPU/Hydra launchers,
86 no-GPU container tests and 71 host tests, all zero skip. r3 dispatched
once at 23:11:36.289 Beijing, with fixed deadline September 26 03:11:36.289.
The owned eight-GPU preflight container exited1 after about 1.4 seconds,
without OOM; the supervisor and queue failed and launched no evaluation
stage. Thus r3 added **zero natural games and zero updates**. The original
32 accepted games remain intact. [Compact evidence](qwen-l8-pilot-r3-failure-20260925.json).

The preflight used a long `ray.init(_temp_dir=...)` path under the full root.
Its Ray session contained only `node_ip_address.json`, with no process logs.
A separate no-GPU container using the same runtime reproduced a precise
`OSError: AF_UNIX path length cannot exceed 107 bytes` at Ray's plasma-store
socket preparation for the same long prefix, while a short `/tmp/raydiag`
path initialized Ray successfully. This is strong direct evidence for the
preflight-specific failure, but the original GPU stderr was unavailable:
the container used log-driver `none` and the preflight omitted an entry-log
redirect. The probe did not reach CUDA identity or NCCL, so r2's device
mapping failure is **not yet re-tested or resolved**. The r3 one-shot
authorization has been consumed; do not restart its container or queue.
