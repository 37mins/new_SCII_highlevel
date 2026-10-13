#!/usr/bin/env bash
# Thin Qwen counterpart of the pinned 9a7b0fa native eight-rank seed launcher.
set -euo pipefail
source_dir=${1:?frozen Qwen runtime}
shift
test "$(git -C "${source_dir}" rev-parse HEAD)" = "${SOURCE_SHA:?frozen SHA}"
test -z "$(git -C "${source_dir}" status --porcelain)"
if [[ "${DRY_RUN:-0}" != 1 ]]; then test "${SC2_COMBAT_LONG_AUTHORIZED:-0}" = 1; fi
export PYTHON_BIN=${PYTHON_BIN:?verified Python}
export CONFIG_PATH=${source_dir}/configs/qwen3-4b-instruct-2507-level5.env
export EXTRA_PYTHONPATH=${source_dir}/experiments/records/20260916-combat-result-reward-v1:${source_dir}/experiments/records/20260911-execution-failure-feedback-v1:${source_dir}/experiments/records/20260910-spb-fsdp-layer-wrap-v1:${source_dir}/experiments/records/20260908-g2-planner-handoff-v1:${source_dir}/experiments/records/20260906-integrated-fixes-v1:${LONG_DEPENDENCY_PATH:?dependencies}
export CUDA_VISIBLE_DEVICES=0,1,2,3,4,5,6,7 N_GPUS_PER_NODE=8
export CPATH=/usr/include/python3.12:/usr/include
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
export SC2_DIFFICULTY=${SC2_DIFFICULTY:?declared level} SC2_AI_BUILD=Air SC2_ENV_SEED=0 SC2_ROLLOUT_N=8
export SC2_MAX_STEPS=0 SC2_FIXED_BO_PREFIX_LIMIT=-1 SC2_STEP_SHAPING_MODE=off
export BO_PROFILE=canonical EVAL_ONLY=0 SPB_DISABLE_SWA_DROPOUT=0
export SC2_ORIGINAL_BO_SEGMENT=1 SC2_CLARIFY_BO_QUOTA=1 SC2_EXECUTION_FAILURE_FEEDBACK=0
export SC2_PLAN_SEGMENT_MAX=6 SC2_PLAN_BULLET_MAX=6
export MAX_PROMPT_LENGTH=4096 MAX_RESPONSE_LENGTH=192 TOTAL_EPOCHS=2 SAVE_FREQ=2
export PPO_DIAGNOSTICS=0 ROLLOUT_LOGPROB_DIAGNOSTICS=0
export TMPDIR=/tmp TRITON_CACHE_DIR=/tmp/triton HF_HOME=/tmp/hf WANDB_MODE=disabled
unset SC2_GAME_TIME_LIMIT SC2_RNG_PREFIX_TARGET SC2_COMMAND_TRACE_DIR
exec bash "${source_dir}/scripts/train_sc2.sh" \
    "+ray_init.runtime_env.env_vars.SC2_SEED_PYTHON_RANDOM='1'" \
    "+ray_init.runtime_env.env_vars.SC2_RESET_RETRIES='1'" \
    "+ray_init.runtime_env.env_vars.SC2_RESET_CONCURRENCY='1'" \
    "+ray_init.runtime_env.env_vars.SC2_PRESERVE_VALID_BO='1'" \
    "+ray_init.runtime_env.env_vars.SC2_ENABLE_AIR_OPTIONS='1'" \
    "+ray_init.runtime_env.env_vars.SC2_COMBAT_REWARD_SCALE='0.001'" \
    +actor_rollout_ref.actor.fsdp_config.mixed_precision.param_dtype=fp32 \
    +actor_rollout_ref.actor.fp32_normalization=True \
    +actor_rollout_ref.ref.fsdp_config.model_dtype=fp32 \
    +actor_rollout_ref.ref.fsdp_config.mixed_precision.param_dtype=fp32 \
    +actor_rollout_ref.ref.fp32_normalization=True \
    ++actor_rollout_ref.rollout.fsdp_layer_wrap=True \
    ++env.prompt_response_log_max_prompt_chars=0 ++ray_init.num_cpus=32 \
    trainer.sc2_skip_zero_signal=False trainer.sc2_signal_max_attempts=3 trainer.sc2_signal_max_batches=0 \
    actor_rollout_ref.rollout.temperature=0.8 algorithm.gamma=1.0 \
    trainer.del_local_ckpt_after_load=False trainer.resume_mode=disable \
    +trainer.sc2_checkpoint_resume="${SC2_CHECKPOINT_RESUME:-False}" "$@"
