# L8 Qwen pilot: one approved r6 remainder attempt

Final status at September26 01:03 Beijing: **invalid before GPU dispatch**.
The actual eight CPU/Hydra configs, 96 no-GPU container tests and 71 host
tests passed. The real no-GPU Ray setup hook then failed because the direct
probe omitted `SC2PATH`, although the formal launcher's resolved environment
contains it. No GPU dispatch/queue or new game occurred. The r6 source and
failure are frozen; [exact receipt](qwen-l8-pilot-r6-failure-20260926.json).
The planned `qwen_l8_cuda_probe_v2.py` reads the complete resolved Ray
environment, overrides only the two probe temporary paths, and disables Ray
task retries. Four local environment-contract tests passed with
`python3 -B -m unittest discover -s tests -p 'test_qwen_l8_probe_env.py' -v`.
These tests are separate from a real worker pass. No second r6 CPU-hook or
GPU attempt was launched; the proposed new attempt needs authorization.
The following original plan is retained as history.

September 26, 2026, Beijing. Status: **approved and preparing; not yet GPU
dispatched**. The user approved one new RUN_ID for only the 64 unrun games of
the original twelve-stage, 96-game, zero-update L8 Qwen comparison. The first
four r1 stages / 32 games remain accepted and will not be replayed. r2–r5
each added zero games. r5's CPU hook CLI dispatch failure is recorded in its
own failure receipt; no frozen r5 source or output is modified or rerun.

The only r6 controller change is to dispatch the `cpu-hook` CLI mode to its
actual function. A local regression test invokes that CLI branch. The new
run must then execute the actual eight CPU/Hydra configs, zero-skip no-CUDA
tests, and a separate no-GPU Ray worker with the real launcher's resolved
PYTHONPATH and setup hook. Only a passing worker proof permits a one-shot GPU
identity/NCCL preflight and the eight remaining evaluation stages. The r2
duplicate-GPU failure is not presumed fixed. Every formal stage still needs
correct model/checkpoint load, paired seed/RNG, natural terminal games,
consumed-answer legality, binary64 metrics, replays, result=`.done`, exit0,
and matching owned guardian. No L8 PPO/RL training is authorized.

Output: `/var/jfsCache/sc2-qwen-l8-pilot96-197-20260926-r6`.
Source parent: `/var/jfsCache/sc2-qwen-l8-pilot96-197-source-20260926-r6`.
The first and only GPU dispatch starts a fixed **4 wall-hour / 32 GPU-hour**
deadline shared by preflight and all eight stages. All twelve r1–r6 source
and output roots count together under **32 GiB**, with strict GNUdu, no
exclusions or old-value fallback. Each GPU stage requires eight idle GPUs
without compute PID, 600 GiB available RAM, 128 GiB free NVMe, and
fsync/readback. No deletion, automatic retry, extra game, budget extension,
or successor is authorized. Approval and CPU checks are not GPU proof.

Pre-deployment review corrected the Docker inspection template's closing
delimiter. The exact read-only inspection command succeeded against the
owned r5 CPU container at 00:46 Beijing; all 20 local continuation tests
passed. r6 had not been prepared or dispatched at this check.

The first preparation stopped before deployment creation: the runtime's
shared Git object chain exceeded Git's nesting limit. The source remains
clean at `769e55e`; no r6 container exists. The narrow
`finish_r6_preparation197.py` helper requires exactly this empty scaffold,
materializes the same commit's objects into the new runtime, preserves the
old alternate pointer, checks cleanliness, and completes the original
deployment fields and parent/history checks. It cannot dispatch containers
or run a second prepared experiment. All bytes remain inside the same
twelve counted roots; this is completion of the pre-deployment code copy.
