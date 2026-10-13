# Level7 修复协议、Qwen96步结果与 SpB 续训解释

核验时间：2026-09-22 23:07 北京。任务类型：只读配置/结果分析与用户指定语雀文档更新；没有改动运行配置、停止/重启实验或追加 GPU 工作。

证据快照：[l7-settings-analysis-20260922-2307.json](l7-settings-analysis-20260922-2307.json)。
发布目标：[语雀 SCII日志](https://www.yuque.com/yangdage-mu30r/nsahpp/io9ul989o6qkposx)，追加日期章节，保留全部原有 D/C 历史文字与图片。

## 核心结论

受约束生成下的回答合法性、真实动作消费和参数更新链路已有运行证据；Qwen 继续到96步没有在当前8对评测中表现出提升。训练高胜率、合法率100%、非零梯度不能替代策略能力验收，也不能证明架构优势。

## 当前 SpB 的实际设置

当前 run 为 `sc2-l7-followup197-20260922-r4/spb-same/long`，实际运行源码 `9cb291ea5f50de205c5d88371e08ce229b7d9d04`，clean/world_size=8。这是短验收后加载自己的完整 CP2；不是旧 Level6 D/C 或退化 Level7 checkpoint。

| 项目 | 实际配置 |
|---|---|
| 模型 | 原始 `Panyuqi/SpikingBrain-2.0-instruct`，约5.17B，无项目 SC2-SFT；原始 reference |
| 场景 | Level7 VeryHard，Flat128 / Base75689，Terran / Air，canonical BO |
| seed | 私有 Python Random(0)，0–100有放回；每轮一个 seed、8局共享，跨轮再抽；49×8、97×8、53×8、5×8… |
| 算法 | GiGPO advantage + PPO clipped objective；全 actor 参数 AdamW/FSDP，LoRA rank默认0 |
| 学习率 | 1e-6，constant，零 warmup；grad_clip=1 |
| PPO分批 | 配置全局 mini-batch=8，每卡 micro-batch=1，ppo_epochs=1；此处是决策样本分批，不是每个游戏仅一个训练样本 |
| 正则/clip | KL loss启用、coef=0.01、low_var_kl；entropy=0.001；clip low/high=0.2/0.28 |
| 生成 | T=0.8，top_p=1，top_k=0，max_response=192，max_prompt=4096 |
| 奖励 | gamma=1，combat reward scale=0.001 |
| 生成/credit修复 | canonical action support，no-thinking同支持集；post-centering invalid credit；实际消费合法率<0.5拒绝PPO |
| 未启用 | D+零信号过滤、重采样、early-stop；history=0，memory=off，执行失败反馈关闭 |

路线：pre8 → train2两轮16局 → CP2 post8 → 续 global3..96共94轮752局 → CP96 eval8；总768训练局，含三次评测为792局。

短段真实结果：pre4/8、train2共5/16、post3/8；32自然局、243/243消费回答合法。4/8→3/8并非提升证据，样本也很小。

23:07快照：已完成 global step3/96，console为实际 update_actor 返回后的 binary64-v1 指标；grad_norm=71.69441684087117，update_actor=240.23491866141558秒，消费合法率1，invalid advantage max=0。长段 result/.done 尚不存在，不能写成长期验收完成。实际模型、Adam、dataloader、SC2/driver RNG恢复源为自身 checkpoint，非 legacy fallback。

no-thinking **没有简单关掉或回滚**。当前在生成时限制格式、合法BO候选、数量和闭合预算；生成与actor/old-actor/reference采用一致支持集。不是事后剥标签、截取答案或重采。合法性主要受协议保障，并非证明模型自己学会格式，也不证明内部思考关闭。

## 96 step 不等于96次底层优化器调用

准确口径是 **96轮采样与PPO训练**：每轮8局新游戏，游戏中多次Planner调用产生多条prompt-response决策样本，再拆分mini-batch优化。

- 不是大型固定语料的96个epoch；配置中的 `trainer.total_epochs=96` 是此运行的外层数据迭代设置，不能解释成大语料全量遍历96遍。
- 不是一定只有96次 `AdamW.optimizer.step()`。冻结训练代码在每次actor更新内部按mini-batch循环调用优化器；总调用次数需对实际决策样本分批另行计数，本轮不虚报该数字。
- 冻结 `ppo_epochs=1` 意味该次actor更新中的PPO数据遍历次数为1，不意味着全程只更新一次。
- 全参数RL与小交互预算同时成立；不是LoRA小适配器训练，也不是大规模预训练。

代码证据来自Qwen实际训练SHA `279d5496464de29e14c64924ccb829147351efbd`，不是用当前HEAD代替历史：`verl/workers/actor/dp_actor.py` 中 `update_policy` 的mini-batch/epoch循环与 `_optimizer_step`；`verl/workers/fsdp_workers.py` 的按world-size归一化及 `AdamW(actor_module_fsdp.parameters())`；冻结 `ppo_trainer.yaml` 默认 `ppo_epochs=1`、`lora_rank=0`。当前SpB有效配置也未覆盖这两个默认项。

大规模训练同样通常通过mini-batch进行。规模差别主要在交互/样本/token总量、任务覆盖、独立随机性、重复训练、评测样本和算力。本次单一地图/对手配置的768局不能代表广泛SC2能力。仅增加步数不会自动修复弱任务信号或执行器归因。

## Qwen96 的完成结果

模型为原始 `Qwen/Qwen3-4B-Instruct-2507`，revision `cdbee75f17c01a7cc42f958dc650907174af0554`，不是旧SC2-SFT模型。

| 部分 | 自然局 | 胜局 | 胜率 |
|---|---:|---:|---:|
| 父训练global1–2 | 16 | 8 | 50.00% |
| 续训练global3–96 | 752 | 601 | 79.92% |
| 完整96轮训练 | 768 | 609 | 79.30% |

训练退出0/result=.done与旧严格terminal验收通过是不同事实：后者仍failed，见下方精度缺口。

| 相同8个评测seed | 胜/总局 | 合法/消费回答 | 评测更新 |
|---|---:|---:|---:|
| 原始Qwen pre | 7/8 | 49/49 | 0 |
| Qwen CP2 post | 7/8 | 69/69 | 0 |
| Qwen CP96 eval | 5/8 | 23/23 | 0 |

各评测均自然终止。CP2/CP96的rank、seed、初始CPU/CUDA RNG凭证实际配对。逐对转移为5赢→赢、1输→输、2赢→输、0输→赢；点估计下降25个百分点。只有8对已使用过的seed，既不能称提升，也不能断言稳定退化；不是盲测面板。不把训练609/768与评测5/8当作同一抽样分布直接比较。

## 同seed相关性与学习信号

本轮从原始两段小型 `training_seeds.jsonl`、`episode_outcomes.jsonl` 汇总，并核对96批Random(0)序列：

- 96批仅63个不同游戏seed；每批仍8局共享seed。768局不是768个独立场景。
- 71批全胜、18批全败，仅7批胜负混合；89/96批整批同胜负。
- 续训94行旧metrics中，70行advantage的min/max都显示为0.000。旧三位小数日志不能证明原始值严格为0，但配合批内同胜负，提示任务区分信号可能长期很弱。

全胜/全败本身并不必然令advantage为0，因为战损和step分支回报仍可有差异。非零梯度也可能来自KL/熵正则，不能当作任务学习收益。旧metrics中lr显示0.000同样是精度损失，不能说真实学习率为0；冻结lr为1e-6。

已验证合法计划进入队列并产生本地模型指令，不等于证明模型独立决定胜负；自动执行/战斗仍参与结果。当前SpB5.17B与Qwen4B参数量/FLOPs也不相等，只能说协议与交互预算尽量匹配，不能据此证明架构优势。

## 必须保留的证据与范围限制

1. Qwen旧训练严格terminal仍为failed：steps7、9、10、56、65、92的原始梯度因三位小数日志不可恢复。用户接受特定缺口后只另行做CP96零更新终评，未回写旧记录，未改判严格训练通过。新SpB binary64-v1日志不降低有限正梯度门槛。
2. Qwen父CP2缺driver RNG，SC2计数由verified legacy ledger迁移；原模型/Adam/rank RNG/dataloader实际加载但不是bitwise replay。SpB当前CP2有native完整状态，不使用该豁免。
3. 当前已挂队列仍是SpB L7 same长训/终评 → Qwen L7 random从其自身CP2长训/终评。Qwen random短验收已完成，长训尚无dispatch；不能写成已完成随机seed96步。
4. 新SpB L7 random已在[计划记录](spb-l7-random197.md)登记，预算选择尚未确认，没有prepare/dispatch。本文不是扩张实验授权。
5. mixed-seed UID是已声明消融例外；随机每局seed可分散相关性，却仍可能把场景难度混入advantage，不是自动修复credit。

研究判断：完成现有受控比较后，更充分的未参与选择的配对评测、重复运行和任务信号审计，比仅延长step或看饱和胜率更能判断RL是否有效。这是分析建议，不是新增已授权队列。

## 本轮验证与发布

通过SSH别名仅读取冻结配置/manifest、小型result/.done/种子/自然局/metrics及1MiB有界console尾；未读取大checkpoint，未调用GPU诊断，未修改服务器。JSON汇总保存证据路径和SHA256；本报告由原始计数复算。

语雀使用用户指定Safari中的现有文档原位追加，未覆盖历史内容、未改变分享权限。发布结果以[本轮发布凭证](l7-yuque-publication-20260922.json)为准。记录沿用 `codex/fix-quiescent-storage`，不创建新实验分支或平行实验record。
