# 2026-09-23｜SpB Level7 same-seed：完整96步设置、曲线与终评

发布目标：[语雀 SCII日志](https://www.yuque.com/yangdage-mu30r/nsahpp/io9ul989o6qkposx)。原文追加，不覆盖9月22日及更早的实验历史。本节将SpB状态更新为已完成；完整指标快照时间为9月23日21:24:20北京，训练于11:45:25结束，终评于11:58:36结束。

## 1. 这个实验要回答什么

检查修复后的生成、动作消费、credit和PPO链路能否在SpB上稳定运行96轮，并观察从自身CP2继续训练后是否提高配对评测表现。它既是长程技术验收，也是有限规模的学习效果对照；不是参数量/FLOPs匹配的大规模架构优劣证明。

## 2. 实际实验设置

| 项目 | 冻结配置 |
|---|---|
| 模型与起点 | 原始Panyuqi/SpikingBrain-2.0-instruct，约5.17B，无本项目SC2-SFT；reference为原始模型。不继承旧Level6 D/C或退化L7权重。 |
| 场景与并行 | Level7 VeryHard；Flat128 / Base75689；Terran / Air；canonical BO；world_size=8。 |
| seed | 私有Python Random(0)，0–100有放回。每个step抽一个seed，8局共享；跨step再抽，前几批49×8、97×8、53×8、5×8。不是全程固定一个seed，也不是每局独立抽seed。 |
| 学习算法 | GiGPO advantage + PPO clipped objective；全actor参数AdamW/FSDP，非LoRA；LR=1e-6常数、零warmup，grad_clip=1。 |
| PPO分批与正则 | global mini-batch=8，每卡micro-batch=1，ppo_epochs=1；KL loss coef=0.01（low_var_kl），entropy=0.001，clip low/high=0.2/0.28。分批单位是决策样本，不是每局只有一个样本。 |
| 生成 | T=0.8，top_p=1，top_k=0，max_response=192，max_prompt=4096；canonical action support，no-thinking同支持集。 |
| 奖励与credit | gamma=1，combat reward scale=0.001；post-centering invalid credit，实际消费合法率低于0.5拒绝PPO。 |
| 其他与恢复 | 无D+零信号过滤、重采样或early-stop；history=0、memory关闭、执行失败反馈关闭。每8步保存CP；从自身完整native CP2恢复模型/Adam/scheduler/dataloader/SC2及RNG，不使用legacy fallback。 |

no-thinking没有简单关掉或回滚：当前约束在生成时限制格式、合法BO候选、数量和闭合预算，生成与actor/old-actor/reference采用一致支持集；不是事后剥标签或重采。合法性受协议保障，不等于模型自己学会了格式，更不能证明内部思考关闭。历史归零也不能单独归因于no-thinking一个变量。

## 3. 路线与完整结果

原始pre8局 → fresh train2（steps1–2，共16局）→ 自身CP2 post8局 → native续训steps3–96（94轮、752局）→ 自身CP96 eval8局。合计768训练局，含三次零更新评测共792个自然完成游戏。

| 部分 | 胜局/局数 | 胜率 | 用途 |
|---|---:|---:|---|
| 原始pre | 4/8 | 50.00% | 零更新评测 |
| 训练steps1–2 | 5/16 | 31.25% | 短训 |
| CP2 post | 3/8 | 37.50% | 零更新配对评测 |
| 训练steps3–96 | 440/752 | 58.51% | 长训 |
| CP96 eval | 2/8 | 25.00% | 零更新配对终评 |
| 完整训练steps1–96 | 445/768 | 57.94% | 训练描述统计，不与评测混合 |

最后8个训练step为29/64（45.31%）。96步训练实际消费回答共11,313条，11,313/11,313合法；终评33/33合法。训练和终评result与.done一致、exit0、clean运行SHA、world8；新增94轮实际PPO及审计、有限正梯度、非正invalid advantage、12个CP清单均验收。CP96终评实际加载返回，8局自然结束且0参数更新，并与CP2 post按原seed/rank/初始CPU-CUDA RNG配对。

96 step是96轮采样/PPO训练，不是大型语料的96个epoch，也不等于恰好96次底层AdamW调用。每轮8局中的多次Planner回答会形成多个决策样本，再按mini-batch训练。全参数训练与交互规模较小可以同时成立。

## 4. 完整折线图口径

蓝色为每step的实测值，橙色为包含当前step在内的向后8步算术均值，从step8开始；不插值、不补零、不把评测拼入训练。steps1–2与3–96来自同一实验自身CP2恢复，96步连续无缺口。下方回答合法率为100%，两条线重合。

发布时附图：`spb-l7same-complete-20260923.png`（1440×1010）；PNG SHA256 `28ed7c967eac1175fb00561d9561ab81ae9897100b6ac58584af98b5baa005b3`。图像是已核验完整快照的本地静态渲染，不是重新运行实验。

## 5. 这些结果说明什么

1. **技术链路稳定性通过本次验收**：没有再出现回答合法率归零，长训、native恢复和终评完整完成；但合法性主要由约束解码保障。
2. **尚无RL提升证据**：同8个评测seed上，CP2的3/8变为CP96的2/8，点估计下降12.5个百分点；只有8对，不能断言稳定退化，更不能称提升。
3. **训练曲线不是因果学习曲线**：step之间换场景seed，step内8局相关。训练胜率起伏、合法率100%或非零梯度都不能证明战略学习；梯度还可能含KL/熵正则贡献。
4. **不能据此宣称架构优势**：执行器/自动战斗参与结果，且SpB5.17B与Qwen4B参数量和FLOPs不等。需更多独立、未参与选择的配对评测及重复运行，才能评估泛化和稳定收益；此建议不构成新增实验派发。

## 6. 溯源与后续边界

实际SpB运行源码为`9cb291ea5f50de205c5d88371e08ce229b7d9d04`；完整快照及绘图代码归档在Git提交[2e3e5b2](https://github.com/CeraveNew/new_SCII/commit/2e3e5b221f4009e3c3989934a522441aa4d895d4)，不是用当前开发HEAD冒充运行时。

- [完整1–96步原始指标快照](https://github.com/CeraveNew/new_SCII/blob/2e3e5b221f4009e3c3989934a522441aa4d895d4/experiments/records/20260921-sc2-policy-credit-v1/spb-l7same-complete-20260923-data.json)
- [图表口径、验证与复现方法](https://github.com/CeraveNew/new_SCII/blob/2e3e5b221f4009e3c3989934a522441aa4d895d4/experiments/records/20260921-sc2-policy-credit-v1/spb-l7same-curve-20260923.md)
- [绘图脚本](https://github.com/CeraveNew/new_SCII/blob/2e3e5b221f4009e3c3989934a522441aa4d895d4/experiments/records/20260921-sc2-policy-credit-v1/plot-spb-l7-curve.mjs)

Qwen每局独立seed是另一组实验，不能把本图当作随机seed结果。截至9月23日21:26:28的已归档快照，其自身CP8续训已返回steps9–14，仍在训练，尚无96步终评结论。SpB每局独立seed仍为待预算确认的计划，不声称已跑。当前更新只整理已保存证据和文档，不重跑、修改或追加GPU实验，不改变语雀分享权限。
