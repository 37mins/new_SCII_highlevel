# SCII 项目进展与实验总览

> 状态核验：北京时间 **2026-09-23 23:06:52**。本文按“目标—版本—实验—证据—结论”组织；运行中数据是该时刻快照，不是完成结果。仓库：[CeraveNew/new_SCII](https://github.com/CeraveNew/new_SCII)。

## 1. 一页看懂当前进展

**目标：**在公平、可复现的 SC2 条件下，比较 SpikingBrain 与 Qwen，并判断收益究竟来自模型、RL、seed 分组，还是提示词、约束解码与执行器。最终希望证明线性／混合注意力的优势，但目前还没有达到这一证据标准。

**目前最大的进展是训练与验收链路变得可检查，而不是已经证明胜率提升。**修复后的 SpB Level7 同 seed 实验完整跑完96轮及终评，训练实际消费的11,313条回答全部合法；完整指标、恢复状态、真实 PPO 和终评可以追溯。合法性主要由生成约束保障，不能算作模型自己学会了战略。

| 实验 | 当前状态 | 回答的问题 | 已有关键证据 |
| --- | --- | --- | --- |
| Qwen L7，同 step 同 seed，96轮 | 训练结束；历史严格训练验收缺口保留，另行终评通过 | 同场景组内训练能否带来收益？ | 训练609/768；CP2→CP96配对评测7/8→5/8，未显示提升 |
| SpB L7，同 step 同 seed，96轮 | 完整验收完成，只读保留 | 同一修复协议能否在SpB稳定长训？ | 训练445/768；CP2→CP96为3/8→2/8；训练回答11,313/11,313合法 |
| Qwen L7，每局独立 seed | 正在从自身原生CP8续训，快照已返回step51/96 | 减少批内同场景相关性后，训练与终评怎样变化？ | 本次steps9–51：344自然局302胜，1082/1082消费回答合法；尚无CP96终评 |
| SpB L7，每局独立 seed | 已单次排队，等待当前Qwen完整验收 | 补齐“模型×seed模式”的对照 | waiting-predecessor，未GPU派发；不是已开跑 |

**已排顺序：当前Qwen随机组训练＋终评完整通过 → 原始SpB随机组短验收 → 自身CP2续到96 → CP96配对终评。**任一前序失败即阻断后继，不自动重试或跳过。

## 2. 读结果前先统一口径

- **难度不能混用：**早期Hard是Level5；D/C是Level6 Harder；当前四组对照是Level7 VeryHard。不同生成协议和难度的胜率不拼成统一排名。
- **训练与评测分开：**训练rollout用于更新；pre、post、eval均为零参数更新的独立阶段。训练胜率高不等于配对评测提高。
- **96 step不是96个大数据epoch：**每轮新采8局、收集多次Planner决策，再做PPO小批量训练；96轮对应768训练局，不等于恰好96次底层AdamW调用。当前是真实全参数RL后训练，但仍是单一地图／对手下的小规模研究。
- **合法≠执行成功≠学会战略：**回答结构语义合法、进入合法队列、发出本地指令、最终获胜是不同层次。Executor与自动战斗仍影响结果。
- **主线成本≠尝试成本：**恢复时只拼接有效prefix和新suffix；失败、重复完成局和失败派发槽另记，不能隐藏重试成本。

## 3. 版本与GitHub commit索引

下列短SHA均链接到完整不可变commit。**运行源码、工程修复、结果归档是三种不同对象**；当前分支HEAD不能替代历史实际runtime。表中描述性版本名不是新造的正式发布tag。

### 3.1 早期基线与发布点

| 历史标记／版本 | commit | 含义与边界 |
| --- | --- | --- |
| baseline/qwen-core-v1 | [df8fed8](https://github.com/CeraveNew/new_SCII/commit/df8fed8ccd1b1e7aa31953b9ed900466cc5526f9) | Qwen SC2-SFT基线结果归档；实际评测runtime为[d32c21a](https://github.com/CeraveNew/new_SCII/commit/d32c21a9df2a79ad7156d698cde352c297b2e9d2) |
| baseline/spb2-system-v1 | [5586789](https://github.com/CeraveNew/new_SCII/commit/55867897852a8937191125bd3ef56a739127be85) | 原始通用SpB system基线结果归档；两批runtime为[ac83dd2](https://github.com/CeraveNew/new_SCII/commit/ac83dd2b7489f71a6e87dd1900e355fbe5f918d0)、[624bd28](https://github.com/CeraveNew/new_SCII/commit/624bd2825014807d62a97bc8b01a77f968334ef5) |
| v1.0.0（正式tag） | [df1cbb0](https://github.com/CeraveNew/new_SCII/commit/df1cbb0a648da70d3835ca82612b3ba5fd1ab605) | Qwen Level5可复现基线发布点，不是当前Level7修复协议 |
| 修复前主线存档 | [d42096e](https://github.com/CeraveNew/new_SCII/commit/d42096e2fe7f375b25d16b30fd151df10bbab308) | 旧系统对照的历史锚点 |
| Integrated Fixes v1 | [1f2d8b5](https://github.com/CeraveNew/new_SCII/commit/1f2d8b5ac25d13cb4dc2b735725806fa713bb092) | 自然终局、terminal credit、完整回答格式奖励、生成位置与unit-ID等修复整合；当时协议与当前192-token/gamma1版本不同 |

前两个baseline名称来自历史记录／本地tag；本轮远端tag查询未列出同名tag，因此这里提供commit锚点，不宣称远端tag仍存在。v1.0.0的远端tag已核对。

### 3.2 学习协议与实际实验版本

| 版本／实验 | 实际commit | 核心变化或用途 |
| --- | --- | --- |
| D：SpB L6同seed | [e13e1fb](https://github.com/CeraveNew/new_SCII/commit/e13e1fbdf84171172d7eeace826fca599c41ea63) | T=.8、gamma=1、combat=.001；不开D+过滤 |
| D+候选 | [ca028ce](https://github.com/CeraveNew/new_SCII/commit/ca028ce328dc757ddf32c78ededead21deeefca4) | 原始组分数无有效差异则跳过PPO，不是按输赢过滤 |
| C后段恢复／CP96终评 | [2f4a597](https://github.com/CeraveNew/new_SCII/commit/2f4a597e15f6fb6216fe5929d07f3ac685e53108) | L6每局随机seed；含thinking的整条回答判无效，不剥后缀；不代表C所有历史阶段都使用此SHA |
| 旧L7 no-thinking／L6三模型面板 | [7236c37](https://github.com/CeraveNew/new_SCII/commit/7236c37b116fd8fbe15db09ccbdcd2e740e4e840) | top-p=.9＋旧no-thinking支持约束，尚无新的canonical动作约束 |
| canonical动作约束实现 | [0172fb9](https://github.com/CeraveNew/new_SCII/commit/0172fb9b334cea91f1e92c0c545f721afe281671) | 限格式、候选动作、数量与闭合预算；生成及PPO概率支持集匹配 |
| EOS/PAD对齐修复 | [bed7a3e](https://github.com/CeraveNew/new_SCII/commit/bed7a3e5a755f5b2ca0ad0977c54ca2cfa837594) | 生成和teacher侧终止／填充token一致；不是改reward |
| SpB L6修复短验收 | [ce8b938](https://github.com/CeraveNew/new_SCII/commit/ce8b938341cd5b881b4dea8446ad570ed7509f78) | 32局、2轮PPO真实验收 |
| Qwen四组短验收 | [019a8b3](https://github.com/CeraveNew/new_SCII/commit/019a8b3a60aa093d61fccfb4293625e300a2894e)、[2f95c9f](https://github.com/CeraveNew/new_SCII/commit/2f95c9fd505bd4529070ff4988c5c9efcb111b53) | 前者L6 same；后者其余L6 random／L7 same／L7 random |
| Qwen L7 same96训练 | [279d549](https://github.com/CeraveNew/new_SCII/commit/279d5496464de29e14c64924ccb829147351efbd) | 自身CP2→96；六项历史梯度证据缺口保留 |
| Qwen same CP96仅终评 | [469c77e](https://github.com/CeraveNew/new_SCII/commit/469c77eb9c767f6db87dc4701401805fa22b46e2) | binary64-v1日志；只做8局零更新终评，不重训96步 |
| SpB L7 same96实际完成版 | [9cb291e](https://github.com/CeraveNew/new_SCII/commit/9cb291ea5f50de205c5d88371e08ce229b7d9d04) | host监管、分阶段容器、native恢复；旧Qwen random r4也用此SHA但后来失败，不能统称通过 |
| SC2启动租约修复 | [b81dc55](https://github.com/CeraveNew/new_SCII/commit/b81dc55cc3da5c8b5f1d3dc3b5bf770873128cc6) | 合作worker启动串行至首次观察，八局仍并行；端口竞态为强证据假设，不是所有网络问题已根治 |
| 当前Qwen random CP8续训 | [3415428](https://github.com/CeraveNew/new_SCII/commit/34154283a8298ac4fbaab1c63770a6b81f7d375c) | 原生CP8→96；当前真实运行版本 |
| 已排SpB random短＋96 | [83f3530](https://github.com/CeraveNew/new_SCII/commit/83f3530765babe048035524ddf1651291810818a) | 原始SpB独立起步，严格等待Qwen完整验收 |

主要开发线依次为codex/feature-combat-result-reward、codex/fix-invalid-policy-credit、codex/fix-quiescent-storage、codex/fix-sc2-startup-port-race；这是开发历史，不是把四个分支HEAD当成四个实验模型。相关后期编排来源另固定为[9a7b0fa](https://github.com/CeraveNew/new_SCII/commit/9a7b0faca5b145a891ad211f189121e4949f0eab)。

### 3.3 结果归档版本

| 归档 | commit | 内容 |
| --- | --- | --- |
| C96完成与曲线 | [4717ec4](https://github.com/CeraveNew/new_SCII/commit/4717ec4fdfcd47d3f650d867fd25b32d0798a7a5) | C主线与配对终评证据，不是训练源码版本 |
| SpB完整1–96步曲线 | [2e3e5b2](https://github.com/CeraveNew/new_SCII/commit/2e3e5b221f4009e3c3989934a522441aa4d895d4) | 完整指标快照、绘图脚本与说明；实际训练仍是9cb291e |
| SpB随机后继入队凭证 | [8e9b327](https://github.com/CeraveNew/new_SCII/commit/8e9b327ebe662bacbcfa3d708c381b5616f939ec) | 排队状态归档；不等于GPU已经启动 |

## 4. 实验路线：每一步为什么做

### 4.1 早期Level5系统基线：先证明能跑和能复现

Qwen使用SC2-SFT checkpoint-1248_verlfix，SpB使用原始通用SpikingBrain-2.0-instruct，**不能把两者都标为SC2-SFT**。在当时的Hard、compact6投影执行器、96-token／20环境步上限等旧系统条件下，Qwen为11/16（68.75%），SpB为12/16（75%）。Wilson 95%区间分别为44.40–85.84%、50.50–89.82%；配对为8局都赢、1局都输、SpB独赢4局、Qwen独赢3局，差1/16，精确McNemar p=1。

这说明两条系统路径可运行，不证明架构优势：模型训练经历、参数量和执行器投影等存在限制，也不是当前Level7协议。旧[Qwen3-4B](https://huggingface.co/Qwen/Qwen3-4B)资产家族与当前[Qwen3-4B-Instruct-2507](https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507)不是同一实验权重版本。

### 4.2 D：改善探索与奖励排序，而不是只盯训练胜率

针对旧L6实验中频繁0/8或8/8、计划趋同及折扣排序问题，D同时调整temperature .4→.8、gamma .95→1，增加combat系数.001。战损项为“本次敌方被击杀价值增量－本次我方损失价值增量”，首次Planner调用只建立计数基准，避免重复计分。系数是候选设计，不是已证明最优；组合改动也不能证明每项各自有效。

D从原始SpB起步、每step同seed八局，top-p=.9／192token，GiGPO＋PPO；无项目SFT、D+过滤或early-stop。step8配对独评从2/8到4/8，reward −31.829→−12.371，真实回答有效数35/44→61/68，是8对的小样本正向线索。

完整96步于9月19日结束：475/768胜（61.85%），平均reward −2.958；最后8步58/64、reward20.472，但step83、85仍为0/8。主线拼接1–40、41–72、73–96，不混入失败续跑分支。**后段训练涨分不能替代终评。**

![D训练历史主曲线](https://cdn.nlark.com/yuque/0/2026/png/35080177/1789820027804-5719aabf-b9c2-48e1-be0a-0f3ad0935be9.png)

### 4.3 D+：尝试避免无任务信号时仍做更新

D+在组内减均值之前检查episode／step原始分数差，避免将约5.72e−6浮点残差当作信号。仅当启用分支有真实差异且联合advantage非零才整批进入原PPO，否则跳过更新。不是按0/8或8/8过滤，不重写loss或凭空创造奖励差异。

预算上限是96个采样批／768局，不保证96个更新step；被跳过批次仍计入交互、时间和训练描述统计，不无限补采。此候选保留hold／失败历史，**没有作为当前修复协议启用**。过滤后高胜率、低KL或非零advantage均不独立证明学习改善。

### 4.4 C：每局独立抽seed，检查场景相关性

C沿用D学习配置，从原始SpB独立起步；私有Random(0)连续从0–100有放回抽样，允许碰撞，不是每step重置随机流。首批49,97,53,5,33,65,62,51；仍将八局放在同一个UID优势组，因此场景难度可能混入advantage。

路线为train4→CP4独评→自身CP4续到96→CP96同8seed独评；没有补做C原始模型独评。主线768局567胜（73.83%），平均reward5.785，最后8步41/64。有效主线使用原1–56＋恢复57–96；失败重复部分不混入，含短训与获批重复尝试成本共832局。

CP4→CP96均4/8，reward −13.135→−13.085；8局自然终止、零更新，未观察到胜率提升。后段将含thinking的整条回答判无效，不剥后缀、不重采；C没有启用后来的L7 no-thinking生成协议。

![C完整训练曲线](https://cdn.nlark.com/yuque/0/2026/png/35080177/1789905386692-c8574a13-0208-484e-bd26-e06a41dba66b.png)

### 4.5 固定模型面板与合法率归零：区分协议问题和模型问题

L6原始SpB／D96／C96共同64seed零更新面板共192局：31/64、28/64、27/64；回答有效数为78/681（11.45%）、80/877（9.12%）、21/837（2.51%）。这是旧no-thinking＋top-p=.9协议，不是历史未加mask的L6生成，也不是当前canonical＋top-p1。

连原始模型在该协议下也合法率低，说明不能把低合法率全部归为RL权重退化，亦不能依据早期局部结果说C96更好。面板没有证明D/C提升，也没有统计上明确证明稳定下降；D/C相对原始的配对McNemar p分别约.581／.388。

旧L7同时改变难度和生成协议，不能称“仅难度变化”，也不能把断崖单独归因于no-thinking。修复组合包括：canonical动作约束、top-p1和一致概率支持、EOS/PAD对齐、组内中心化后的无效动作credit修正及消费合法率门槛。没有事后剥输出、重采回答或悄悄改奖励。

### 4.6 修复短验收：先确认真实执行和PPO，再长训

SpB L6短验收32局／2轮PPO，160/160消费回答合法，配对pre→post为6/8→5/8。Qwen四组共128局／8轮PPO，929/929消费回答合法：

| Qwen短组 | pre→自身CP2 post | 用途 |
| --- | --- | --- |
| L6 same | 8/8→8/8 | 同seed技术验收 |
| L6 random | 8/8→8/8 | 每局随机seed技术验收 |
| L7 same | 7/8→7/8 | 提高难度、同seed |
| L7 random | 7/8→8/8 | 提高难度、每局随机 |

这些结果证明短链路可以真实执行、更新和恢复，不证明两步已学会战略。短验收先前失败、修复与新RUN_ID均保留，没有把CPU通过当GPU通过。

## 5. Level7长训：已完成结果与当前验证

### 5.1 Qwen same96：训练高胜率，但配对终评没有提升

原始Qwen3-4B-Instruct-2507，前2轮8/16胜，后94轮601/752胜；完整609/768（79.30%）。原始pre、CP2、CP96分别7/8、7/8、5/8；实际消费回答合法数49/49、69/69、23/23。

CP2→96逐对为5对继续赢、1对继续输、2对赢变输、0对输变赢。点估计下降25个百分点；8对样本不足以断言稳定退化，但显然不是提升证据。

96批仅63个不同seed，71批全胜、18批全败、7批混合，89/96批同胜负。旧后94轮中70轮advantage极值显示0.000，但三位小数不能证明精确零；非零梯度也可能来自KL／熵。768局不能当成768个独立场景。

**严格证据缺口保留：**steps7、9、10、56、65、92原始梯度不可恢复；旧训练终态仍failed。用户仅接受这六项历史缺口后允许另做CP96零更新终评，不是把旧训练改判通过。父CP2缺driver RNG，属于已披露的非逐位续训。

### 5.2 SpB same96：完整技术验收通过，仍无学习收益证据

原始SpB5.17B、原始reference，不继承旧L6或退化L7权重。9月23日11:45:25训练结束，11:58:36终评结束。

| 阶段 | 胜局／自然局 | 性质 |
| --- | --- | --- |
| 原始pre | 4/8（50%） | 零更新 |
| steps1–2 | 5/16（31.25%） | 短训 |
| CP2 post | 3/8（37.50%） | 零更新配对评测 |
| steps3–96 | 440/752（58.51%） | 自身native CP2恢复长训 |
| CP96 eval | 2/8（25%） | 零更新配对终评 |
| 训练完整1–96 | 445/768（57.94%） | 不混入评测的描述统计 |

最后8步29/64；训练11,313/11,313回答合法，终评33/33。新增94轮真实PPO／审计、有限正梯度、invalid advantage非正、12套CP清单、result=.done、exit0、clean SHA／world8均通过；实际CP96加载与原seed/rank/CPU-CUDA RNG配对通过。

CP2→96下降12.5个百分点，仅8对不能断言稳定退化。**技术成功与学习成功必须分开：这次修复后的SpB完整链路通过，但还没有证据表明长训改善了战略表现。**

**完整折线图：蓝色逐step实测，橙色包含当前步的向后8步算术均值，从step8开始；不插值、不补零、不拼入评测。**steps1–2和3–96沿自身CP2连续拼接；合法率100%时两线重合。下图由已保存快照静态重画，没有重跑实验。

![SpB L7 same完整1–96步：蓝色实测、橙色8步均值](https://cdn.nlark.com/yuque/0/2026/png/35080177/1790171231366-346b66af-1360-4f4c-9389-31fc9a97771b.png)

### 5.3 当前Qwen random与已排SpB random：补齐seed消融

Qwen随机组只续自己的原生CP8，不继承same96。9月23日21:06:39实际启动，23:06:52已返回step51；本次steps9–51共344自然局302胜（87.79%），1082/1082消费回答合法，仍在训练。已保存CP16/24/32/40/48必要文件清单；阶段result／done尚未生成，不能提前写成验收通过或认定学习提升。

本次计划global9–96共88轮704局＋终评8局；原失败r4的有效prefix和失败证据保留。用户批准额外40个重复完成局＋8个失败派发槽，不能称免费重试。CP8有原生driver/rank RNG，但更早CP2祖先的非逐位恢复限制不会因此消失。

新SpB随机组已于9月23日排入唯一后继：原始模型pre8→fresh train2两轮16→自身CP2 post8→native续94轮752局→CP96 eval8；合计792局／96轮，48wall小时／384GPU小时／1TiB含加载、短训、阶段间隔与终评。只在Qwen训练＋终评严格验收后自动放行，不预占空卡。

当前Qwen绝对截止为9月25日11:58:40；SpB首次入场到期9月25日12:58:40，入场后48小时固定时钟。**这些是预算上限，不是完工ETA。**

## 6. 当前Level7统一设置与有意差异

| 项目 | 冻结设置 |
| --- | --- |
| 模型 | SpB：Panyuqi/SpikingBrain-2.0-instruct，约5.17B；Qwen：Qwen3-4B-Instruct-2507，revision cdbee75f17c01a7cc42f958dc650907174af0554；各自原始reference |
| 环境 | Level7 VeryHard；Flat128／Base75689；Terran／Air；canonical BO；world_size=8 |
| 学习 | GiGPO advantage＋PPO clipped objective；全actor参数AdamW/FSDP，非LoRA；LR=1e−6常数、零warmup，gamma=1，combat=.001 |
| PPO | mini-batch=8、每卡micro=1、ppo_epochs=1；KL coef=.01（low_var_kl）、entropy=.001、grad_clip=1、clip low/high=.2/.28；分批单位是决策样本 |
| 生成 | T=.8、top-p=1、top-k=0、回答192、prompt4096；canonical action support＋no-thinking同支持集 |
| 质量控制 | post-centering invalid credit；消费合法率低于.5拒绝PPO；无D+过滤、重采或early-stop |
| 其他 | history=0、memory关闭、执行失败反馈关闭；每8步完整CP；评测0更新 |
| same seed | 私有Random(0)，0–100有放回；每step一个seed供八局共享：49×8、97×8、53×8、5×8… |
| random seed | 同一随机流每局各抽一次，允许重复；前两批49,97,53,5,33,65,62,51与100,38,61,45,74,27,64,17；native续reset2为36,17,96,12,79,32,68,90 |
| 配对终评seed | 605183188,1075501356,2084414326,2203880230,3000371298,949752300,3225036469,2823708076；与各自CP2 post配对，不借用另一组 |

no-thinking没有简单关掉或回滚：当前生成时约束格式、合法BO候选、数量与闭合预算，actor／old-actor／reference采用一致支持集；不是事后删thinking标签或剥答案，也不能证明模型内部思考关闭。

随机seed的mixed UID是明确消融例外，场景难度仍可能混入advantage。新SpB随机组还使用启动串行到首次观察的修复，而已完成SpB同seed没有这一时序设置，因此不能说严格只有seed一个变化，亦未证明GPU暂停／启动时序等价。

## 7. 工程进展、失败与仍需回答的问题

### 已取得的工程进展

1. 把生成、解析、动作消费、队列和本地模型指令分开留证；修复协议下短验收与SpB完整长训未再出现回答合法率归零。
2. 保存模型、Adam、scheduler、dataloader、SC2计数和随机状态；新native CP可追踪续训种子，不拿缺失状态假装逐位重放。
3. binary64-v1记录避免把小梯度舍入成0.000；pre-update审计与真实returned PPO、最终metrics及终态分别核验。
4. 输出放NVMe；host sampler＋独立guardian、分阶段容器、容量共享锁及精确计入根增强可控性。测量失败是未知，不当零、不用旧值替代。
5. 每轮原子commit、GitHub同步和远端SHA核对；失败、不提升和批准的重复成本同样留档。

### 不能抹去的限制

- 旧存储du失败、容器exit137／Docker stop超时、SC2启动失败均保留，不能一概写成模型失败。新启动租约不等于所有网络／停止问题根治，NVMe也不是后端彻底修复。
- 六项Qwen same旧梯度缺口和旧failed终态仍在；当前CP8恢复不抹去祖先非bitwise历史。
- 小样本8对终评已反复使用，不是盲测；尚缺更充分的未参与选择评测与独立重复。
- 参数量、FLOPs、运行时和执行器贡献尚未全部对齐，不能从Qwen高于SpB的系统胜率推导架构优劣。
- 同seed高相关、random组混入难度、弱任务优势和强执行器均可能影响归因。更多步数、合法率100%或非零梯度都不能独立证明战略学习。

**下一步研究重点：**先完成已授权的随机seed两组，按各自CP2→96配对结果判断是否有收益，再决定是否需要扩大评测或调整credit／执行器边界；本条研究建议不代表追加实验已获启动授权。

## 8. 证据、图表复现与历史附图

- [早期Qwen基线记录](https://github.com/CeraveNew/new_SCII/blob/df8fed8ccd1b1e7aa31953b9ed900466cc5526f9/experiments/records/20260815-qwen-core-v1/README.md)
- [Integrated Fixes v1说明](https://github.com/CeraveNew/new_SCII/blob/1f2d8b5ac25d13cb4dc2b735725806fa713bb092/docs/integrated-fixes-v1.md)
- [D／C奖励与训练记录](https://github.com/CeraveNew/new_SCII/tree/4717ec4fdfcd47d3f650d867fd25b32d0798a7a5/experiments/records/20260916-combat-result-reward-v1)
- [L6三模型面板及失败交接](https://github.com/CeraveNew/new_SCII/blob/8e9b327ebe662bacbcfa3d708c381b5616f939ec/experiments/records/20260921-sc2-policy-credit-v1/terminal197-20260921.md)
- [L7结果分析及归因限制](https://github.com/CeraveNew/new_SCII/blob/8e9b327ebe662bacbcfa3d708c381b5616f939ec/experiments/records/20260921-sc2-policy-credit-v1/l7-results-interpretation-20260922.md)
- [SpB完整1–96步原始指标快照](https://github.com/CeraveNew/new_SCII/blob/2e3e5b221f4009e3c3989934a522441aa4d895d4/experiments/records/20260921-sc2-policy-credit-v1/spb-l7same-complete-20260923-data.json)
- [SpB图表口径与复现说明](https://github.com/CeraveNew/new_SCII/blob/2e3e5b221f4009e3c3989934a522441aa4d895d4/experiments/records/20260921-sc2-policy-credit-v1/spb-l7same-curve-20260923.md)／[绘图脚本](https://github.com/CeraveNew/new_SCII/blob/2e3e5b221f4009e3c3989934a522441aa4d895d4/experiments/records/20260921-sc2-policy-credit-v1/plot-spb-l7-curve.mjs)
- [当前Qwen原生CP8恢复与启动修复](https://github.com/CeraveNew/new_SCII/blob/8e9b327ebe662bacbcfa3d708c381b5616f939ec/experiments/records/20260921-sc2-policy-credit-v1/sc2-startup-race197.md)
- [SpB每局随机seed授权与队列](https://github.com/CeraveNew/new_SCII/blob/8e9b327ebe662bacbcfa3d708c381b5616f939ec/experiments/records/20260921-sc2-policy-credit-v1/spb-l7-random197.md)

以下两张为原文保留的历史补充图，不将其与当前Level7协议拼接为一条曲线；解释以图内标注及对应历史记录为准。

![原文历史补充图A](https://cdn.nlark.com/yuque/0/2026/png/35080177/1789981336488-10977cd7-e611-4612-ad47-d7a2936e5e2c.png)

![原文历史补充图B](https://cdn.nlark.com/yuque/0/2026/png/35080177/1789980664381-d7e6eb96-db54-4a58-af47-368411926df7.png)

本次为文档重组与已有证据整理：原文先本地备份，保留全部五张历史图，合并重复设置并替换过期的“正在跑／待批准”描述。不重跑实验、不修改冻结部署、不改变语雀访问权限。
