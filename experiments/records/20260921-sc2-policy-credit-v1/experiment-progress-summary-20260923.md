# 当前实验进展与研究判断（2026-09-23 22:04 北京）

本轮只读核验与分析，未修改服务器、冻结部署、预算或队列，未重跑或追加实验。新状态依据[22:04小型凭证](qwen-random-cp8-status-20260923-220401.json)。沿用当前实验分支，不新建方法或实验记录。

## 一句话结论

已经验证修复后的动作与RL链路能在SpB上完成96轮；尚未证明长训稳定提高对战策略。当前运行Qwen每局独立seed长训，完成global27/96，终评未发生。

## 实验分别解决什么问题

| 实验 | 目的 | 已有证据 / 状态 |
|---|---|---|
| 早期Level6原始SpB/D96/C96零更新对照 | 将checkpoint表现与训练曲线分开，同一评测条件比较原始权重和训练权重 | 192局面板已完成；不是重新训练D/C |
| 修复短验收：SpB Level6；Qwen Level6/7 × 同seed/每局独立seed | 验证生成约束、真实动作消费、PPO及自身checkpoint恢复在模型和难度上的可用性 | SpB短验收完成；Qwen四组共128局/8轮PPO，929/929消费回答合法；小样本不证明学习提升 |
| Qwen L7 same-seed至96 | 同step场景一致时，观察长训是否改善配对评测 | 训练609/768；CP2 post7/8 → CP96 eval5/8，没有提升证据。原训练严格终态仍failed，保留六项梯度精度缺口，用户接受后另做CP96终评 |
| SpB L7 same-seed至96 | 检查同一修复协议在SpB的长程稳定性，并对照学习效果 | 严格验收完成；训练445/768；CP2 post3/8 → CP96 eval2/8；训练11,313/11,313消费回答合法 |
| Qwen L7每局独立seed至96 | 降低同step场景/胜负相关性，检查seed分组对学习与评测的影响 | 当前唯一实际运行组，自身native CP8续训，已返回global9–27共19轮PPO，481/481审计消费回答合法；仍需自身CP96终评 |
| SpB L7每局独立seed | 补齐模型×seed分组比较 | 已登记计划，短验收或完整96步的新增预算待确认；没有运行队列/dispatch，不声称已跑 |

Qwen四组短验收证据：[qwen-r4-complete-20260922.json](qwen-r4-complete-20260922.json)。SpB随机组范围：[spb-l7-random197.md](spb-l7-random197.md)。历史L6面板不是当前在跑的实验。

## 共同设置及seed的准确含义

当前三组长训使用Level7 VeryHard，Flat128/Base75689，Terran/Air/canonical BO；8路游戏；T0.8、最多192响应token、top-p1/top-k0、gamma1、combat reward scale0.001、LR1e-6常数零warmup，GiGPO advantage + PPO全actor参数训练。无D+零信号过滤、重采样或early-stop。

same-seed不是全程固定种子：私有Random(0)从0–100有放回，每step抽一个、8局共享，下一step再抽。random则每一局分别抽，允许碰撞。每局独立seed仍保留mixed-UID场景难度混入advantage的限制，不是自动正确的credit估计。

96 step指96轮采样/PPO训练，每轮8个新游戏；游戏中有多次Planner决策，再按mini-batch更新，不等于96次底层AdamW调用，也不是大语料96个epoch。

## 最大的进展

1. **控制并验证了已发现的无效输出/credit失真通道。** 生成期canonical action support约束格式、候选与数量，生成/actor/old-actor/reference采用一致no-thinking支持集；invalid credit在组内中心化后处理，低于0.5实际消费合法率不准PPO。不是事后剥标签/重采样，也不能把历史归零单独归因于no-thinking。
2. **SpB完整96轮给出长期实测证据。** 实际消费11,313条训练回答均合法，plan→queue→本地模型命令、真实PPO、native恢复、checkpoint和零更新终评形成可追溯闭环。合法性主要由协议强制保障，不是模型自己学会格式或战略的证据。
3. **把“训练曲线好看”和“策略真的变强”分开了。** Qwen与SpB的同seed长训均没有在当前配对终评中提升。因此现在的研究瓶颈是任务学习信号与胜负归因，而不是能否获得一条高训练胜率曲线。

Qwen同seed的96批只有63个不同seed，89/96批整批同胜负，提示样本相关性与弱区分信号问题。旧日志大量advantage显示0.000仅说明被舍入，不能声称原始优势严格为零；非零梯度也可能含KL/熵正则贡献。

## 仍然不能下的结论

- CP2与CP96只比较8对曾使用过的seed；两组点估计下降不能证明稳定退化，更不能称改善或盲测泛化。
- 回答合法、已产生本地模型指令不等于全部动作执行成功，也不等于胜负完全由模型计划造成；Executor/自动战斗仍参与。
- SpB约5.17B与Qwen4B并非参数/FLOPs匹配，当前不能宣布线性/混合注意力架构优于Qwen。
- 当前random长训尚无终评，不能用阶段训练胜率宣布随机seed方案有效。当前native CP8恢复也不抹除CP2祖先缺driver RNG的历史非bitwise限制。
- Qwen same96旧严格训练failed及steps7/9/10/56/65/92的原始梯度缺口保持原样，不以新终评通过回写训练验收。

当前Qwen原截止仍为9月25日11:58:40北京；是预算上限，不是预计结束时间。没有新增授权后继。

## 溯源与验证

- [Qwen96设置与结果解释](l7-results-interpretation-20260922.md)
- [SpB96完整设置、结果和曲线说明](spb-l7same-yuque-20260923.md)
- [已发布语雀SCII日志](https://www.yuque.com/yangdage-mu30r/nsahpp/io9ul989o6qkposx)：已含SpB完整设置和蓝色实测/橙色8步均值，本轮没有另改语雀。
- 本轮仅读≤1MiB小型JSON/JSONL、≤4MiB日志尾和精确自有容器状态，不读大CP，不运行GPU诊断。
- 验证：JSON可解析、最新25–27 returned PPO梯度有限正值、update_actor耗时为正、invalid advantage为0；与已提交9–24凭证衔接。19份pre-update audit不能单独证明返回PPO。运行中guardian空槽和未同步root state不被误判失败。
- outcome ledger已出现进行中step28的部分自然局，未把全部158行计作完成28轮或已更新数据。storage使用现有15根receipt，return0/结构化stderr为空；不主动重测或用旧值替代。
- 文档/证据任务，没有修改模型代码，不新增CPU/GPU训练测试。Git验证为JSON校验与diff检查；提交后核验origin分支SHA与工作树状态。
