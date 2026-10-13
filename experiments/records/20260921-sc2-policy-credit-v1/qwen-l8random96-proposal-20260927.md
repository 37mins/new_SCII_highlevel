# L8 Qwen random 96-step RL：已批准预算与实施

## 9月28日19:36：全链完成；random优于same，未证实优于原始模型

queue于19:20:29.526completed/exit0，主终评192/192自然局、零更新，
原始/same96/random96分别43/64、35/64、45/64。预登记random−same配对
11改善/1退步、+15.625pp、exact p=.00635；探索性random−原始2改善/0退步、
p=.5，不能称学习收益已证实。32验证四CP逐局胜负相同但决策次数不同；
实际不同CP加载凭证已核对，参数增量未读取验证。旧18:54及18:38运行中为历史。
本轮没有派发后继/自动接CP192/服务器修改。
[完整分析与小凭证](l8random-flat-validation-spb-review-20260928.md)。

## 9月28日18:38：96步训练与选优已验收，主终评进行中

训练链于15:33:35完成：2+94=96条真实返回PPO、96审计/96独立seed批次，
768自然训练局575胜（74.87%）；3566/3566消费回答合法，梯度与update_actor
时间均有限正值，invalidAdv非正。五阶段result=.done=acceptance、准确容器及
guardian exited0/completed；监控只读小凭证，没有重复读取权重或完整日志验收。
原八局诊断pre/CP2/CP96均6/8。独立32验证CP2/32/64/96均22/32，按预定同分
规则选CP2；不能称越训越好。冻结队列完成全部选优后只删除自身CP32，释放
49,843,591,036bytes（46.42GiB），不可恢复；CP2/64/96与全部旧组保留。

主终评128/192局已验收，正在b05-original；比较原始/same96/random96的同一批
新64seed，全部零更新。不把尚不齐的各臂局数作为最终比较，不改变固定样本数。
按已完成批次速度粗估还需约1小时（19:30–20:00北京），不是保证；该组件固定
硬截止22:57:08.465北京，suite原29日07:45:15.466不变。18:31资源快照八卡
12526–12670MiB、95–97%瞬时利用率，九根约142.49GiB/288GiB、strictdu成功，
无storage-failure凭证。本轮无服务器写操作/重试/清理/新实验。

[当前小凭证](qwen-l8random-r3-status-20260928-1838.json)、
[逐步曲线与复现](qwen-l8random-r3-curves-20260928.md)。

## 最新实际状态：9月28日09:48北京，r3已单次启动

冻结runtime/controller `ad81511b270f782420208ac8a6f305a141e8042b` 已推送，
部署前用准确完整SHA的 `git push --dry-run --porcelain` 核验远端up-to-date；
`ls-remote`曾TLS失败，没有关闭TLS校验。r3单次prepare和CPU门槛通过：
实际host71＋model283项，零跳过/noCUDA；15个CPU容器exited0/noOOM/
DeviceRequests=null；45个真实启动器/Hydra配置及10个真实Ray worker hook通过。
历史same配置的固定哈希单文件只读挂载和仅seed两项科学差异比较实际通过。
long的actual_parent_verified=false仍是等待未来自身CP2，不是准入失败。

L10五阶段小终态/准确容器门控通过后，09:45:14单次入队，09:45:15.466首次
GPU派发。八个唯一CUDA设备/NCCL检查completed/exit0；pre准确容器
`719101af8b913254e5a816998ab6cb5743e4039490c973e80c71cbf278558305`
于09:46:04启动，owner为新r3/qwen-random/short。clean冻结SHA/world8/
binary64-v1/原始Qwen manifest和Flat128/CheatVision/Air实际in_game/planner已见。
截至09:48仍pre零更新，没有pre result/.done/acceptance或实际返回PPO；
guardian空终态槽正常，不冒称短验收或长训已完成。

首次GPU固定时钟：训练＋选优截止 **9月29日01:45:15.466**，整组截止
**9月29日07:45:15.466**（均北京），45秒收尾；主评最多6小时且不越过suite。
预计整组约10–15小时，即9月28日19:45至29日00:45，非保证和非硬截止。
09:46存储小凭证九根154,735,775bytes/288GiB，严格du return0/空stderr；
09:48四个计量receipt根没有storage-failure文件。r1/r2和旧组未删除或重试。
本轮未执行任何checkpoint清理；后续仅允许合同内自身非best CP32的一次淘汰。

凭证：[实际CPU](qwen-l8random-r3-cpu-20260928.json)、
[首次派发与GPU/SC2](qwen-l8random-r3-launch-20260928.json)。
下面各历史“未部署/待授权”状态不覆盖本段；冻结运行不跟随后续记录提交修改。

<a id="r3-approved"></a>

## 9月28日：受控 r3 已明确批准

用户在 r2 失败交接和“新 r3 单次启动，预算不增加”请求后回复“批准”。
复用原 record/branch，冻结新的 SHA，不修改或重试 r1/r2。新三根：

- train：`/var/jfsCache/sc2-qwen-l8random96-197-20260928-r3`
- primary：`/var/jfsCache/sc2-qwen-l8random-paired192-197-20260928-r3`
- source：`/var/jfsCache/sc2-qwen-l8random96-197-source-20260928-r3`

原 r1/r2 六根全部保留，与新三根合计九根严格计量；选优仍在新 train/selection。
训练选优各代 train/source 合计限256GiB，主评各代 eval/source 合计限32GiB，
suite九根去重合计288GiB；8GiB选优包含在训练预算内。游戏/时限不变：
1112自然局/96PPO，训练＋选优16h/128GPUh（选优最多4h/32GPUh），主评6h/48GPUh，
总22h/176GPUh。首次GPU才固定时钟；352GiB训练/128GiB评测、600GiB RAM、
八卡全空归属、fsync/readback等入场门槛不变。不删除旧组、自动重试或接CP192。

修正仅历史same配置的只读路径：prepare先核对保留前缀链接真实目标，CPU容器
仅挂载真正的15,297字节配置文件，绑定SHA256
`77cd457af0cfc64f0ebe0aab690e33af5af7958e336b13cb396766bd0ac7efa6`。
不会挂载整个旧r1可写树，不通过跳过baseline比较放行。原始Qwen/独立seed96、
独立32验证best、最终三臂64测试、CP2/32/64/96完整格式和保留算法都不变，
仅将“自身新组”的精确保护/清理边界改为r3；只有r3自己的非best CP32可能淘汰。

09:29:54北京只读快照：L10 queue completed/exit0，long/train96准确容器exited0，
八卡0MiB/0%且无compute进程；磁盘802,096,992,256bytes可用，RAM796,597,856KiB；
r3三根均不存在、历史配置hash匹配。仍须五阶段终态/归属验收、全部实际CPU
门槛和临派发资源复核，不能把空卡/批准写成已启动。
下面 r2 的“待r3授权”及旧路径是历史记录，当前以本段和后续r3实际凭证为准。

### 最新状态：9月28日00:01:58，r2 CPU 准入失败、未入队

冻结 `ce17791` 已推送核验并单次准备。实际 host71、model/controller282 项
零跳过/noCUDA；short 三个真实启动器/Hydra 与 34 源码哈希通过，但随后历史 same
配置比较读取失败：same r2 的 cpu/train2 是指向保留 same r1 的绝对符号链接，
CPU 容器只挂载了 r2 short，导致链接目标不可见。准确 CPU 容器 exit1/noOOM、
DeviceRequests=null；整体准入失败，后续 long/选优/主评 CPU 与 Ray hook 未执行。
无 queue/dispatch、0 新 GPU/对局/PPO，没有清理 checkpoint；L10 正常保持运行。

本地修正为固定哈希的真实配置单文件只读挂载，并在 host 准备前核对链接目标；
不改实验协议或历史配置、不扩大到整个旧根挂载。134项本地测试130通过/4项
本机 Torch 缺失跳过；宿主只读 normalized 配置比较确认仅授权 seed 两项差异。
修正未部署、r2不重试。需授权受控新r3，r1+r2+r3九根一起计量，预算仍
1112局/96PPO、16h/128GPUh/256GiB训练选优＋6h/48GPUh/32GiB主评、suite22h/
176GPUh/288GiB；GPU时钟尚未启动。不自动重试、不删旧产物、不动L10、不接CP192。
详见[r2失败小凭证](qwen-l8random-r2-cpu-failure-20260928.json)。

## 最新批准：r2、独立验证选 best 与精确新组保留

用户明确批准受控 r2 及新增 128 局选优；下方 r1 与“待批准”段落为历史，不再作为
当前预算或派发依据。r1 不重试；新 r2 实施/CPU 门槛通过后，单次排在 L10 完整
验收之后，不中断或改动 L10。

| 阶段 | 自然局 | PPO | 硬上限 | 存储上限 |
|---|---:|---:|---|---:|
| 原始 Qwen→L8 random96＋原八局三次诊断 | 792 | 96 | 与选优共用16h/128GPUh | 与选优共用256GiB |
| CP2/32/64/96 各独立验证32局 | 128 | 0 | 组件内最多4h/32GPUh | 训练根内最多8GiB |
| 原始/same96/random96同新64seed主终评 | 192 | 0 | 6h/48GPUh | 32GiB |
| 合计 | **1112** | **96** | **22h/176GPUh** | **288GiB** |

新 roots 为 `/var/jfsCache/sc2-qwen-l8random96-197-20260927-r2`、
`/var/jfsCache/sc2-qwen-l8random-paired192-197-20260927-r2`、
`/var/jfsCache/sc2-qwen-l8random96-197-source-20260927-r2`；r1 对应三根残件全部保留
并与 r2 一起精确计量。选优在新训练根的 `selection/`，没有第七个计量根。
352GiB 训练/128GiB 评测入场门槛不变。预计总 10–15 小时，非保证/非硬截止。

训练长段连续完成后再独立选优，避免改变训练 seed/RNG；保存 CP2/32/64/96 全部
native 状态，不修改 FSDP 或 PPO trainer，不启用旧的先删后写轮转。host 完整验收
并 fsync 后原子发布 CP 清单，选优和清理只接受已发布清单。32 validation seeds
和固定 rank CPU/CUDA RNG 与最终64测试分离；best 按胜局数、同分较早步。
最终保留 latest2（64/96）＋best＋受保护 CP2/final96；只有新 r2 CP32 可能在全部
选优阶段终态后被删。峰值最多四套；旧模型/r1残件/L10/历史组不删。
删除不可恢复，保留完整清单和原验收；已删 CP32 不再宣称可原生恢复/实物重验。
主科学结论仍固定 CP96 对比，best 不自动替换测试对象或接 CP192。
详见[已批准实施合同](checkpoint-storage-design-20260927.md)。

CPU 入口：原训练的 model/host 回归、short/long 启动器与三个 Ray hook；主评的
24 启动器/三个 hook；选优用 `qwen_l8random_eval197.py cpu-command --selection`
检查16启动器及 `cpu-hook-command b00-cp{2,32,64,96} --selection` 四个 hook。
全部要求 noCUDA/零跳过、源码34哈希、正确 Hydra/seed/load 模式；未真实执行前
不得称通过。独立验证、保留和主评任一失败均停止后继，不自动重试。

23:27补充：用户允许新组滚动保存并保留best。为避免用训练曲线或最终测试集选档，
已提出独立32seed × 四个候选CP的128局选优方案及+4h/32GPUh预算，尚未批准。
[滚动/best合同与补充预算](checkpoint-storage-design-20260927.md#rolling-best-policy)。
下文为原已批准预算；不能把未批准的新增验证纳入现有运行或提前部署/删除。

状态更新（2026-09-27 23:16:49北京）：**approved / r1已准备，CPU凭证写入失败 /
尚未入队、派发GPU或新增游戏；受控r2待授权**。
实测host71及模型/控制器265项均通过、零跳过，但模型测试结束后的凭证保存误用
只读suite根，CPU容器exit1，因此整体CPU准入未通过。尚未执行launcher/Hydra或
Ray hook；没有GPU probe、训练或评测。L10 long/train96保持运行、不受影响。
本地已将凭证移到short可写owner并增加实际Docker挂载回归；117项本地测试
113通过、4项因本机Torch依赖跳过，尚未部署/重试。详见
[实际失败与修正凭证](qwen-l8random-cpu-failure-20260927.json)。
用户在本方案后明确回复“批准”，同时要求分析checkpoint存储。
批准范围包括本文件训练、三模型新64seed终评、CP2/32/64/96四套完整存档和入场门槛。
后续model-only存档建议见[存储设计](checkpoint-storage-design-20260927.md)，它尚未实施，
不替换本次已批准的完整native存档。以下22:32段落是批准前历史只读快照。
用户要求下一优先项为原始Qwen独立L8 random训练，与已完成L8 same96对照；
先只读核对，不打断已启动任务，训练与后续固定权重终评预算须再次确认。
现有L10保持原样；新组沿用本record和既有实验分支。r1不能再次启动；受控新RUN_ID
获准且CPU/源码/资源门槛全部通过后才可单次入队。

## 197当前队列与调整影响

[2026-09-27 22:32:33北京只读快照](qwen-l8random-priority-status-20260927.json)：

- L9已完成原96步训练及r3最后8局验收；当前队列level10、short/train2，pre已通过。
- L10于22:19:00.308首次GPU派发；pre8为1/8自然胜、0更新，short/train2准确容器
  `46628739500b0d715ec00a603d7aab0172a0b8d7221746a27b57bf69a5579657`
  于22:27:22.339启动，实查running/unpaused/noOOM。八卡各12716–12900MiB，
  瞬时利用率均100%，八个Ray worker在计算log-prob。此采样未见已返回PPO行，
  不把train2活动、GPU利用率或pre结果当已完成更新数。
- L10原授权仍为792局/96PPO、12wallh/96GPUh/256GiB，固定截止9月28日
  10:19:00.308；L9/L10 suite原24h/192GPUh/512GiB与12:11:48截止不变。
  r1/r2/r3九根一起计量，当前202100048561bytes，严格du成功且stderr空。
- 冻结controller5152bbb的queue只包含L9→L10，L10结束后终态退出，未排CP192
  或新L9/L10。当前处于已启动L10，不适用“尚未启动时调整顺序”分支。
  **不修改其后续post/long/eval，也不抢占卡。**

建议优先级为：当前L10原样运行并完成交接 → 新预算获批的L8 random96与固定评测
→ 看配对结果再决定其他L9/L10。现在没有实际插入/创建新队列。L10失败时先保留
交接，不自动修复或绕过失败；任何后续启动都要确认终态、归属和资源已安全释放。
此轮仅SSH只读小state/manifest/result/计量凭证、准确Docker inspect、GPU查询、
磁盘/RAM快照和128KiB日志尾，未修改服务器、停止进程、删除产物或占用额外GPU。

## 实验问题与对照

问题：在同样L8任务、原始权重、96次在线PPO与768训练局下，step内独立场景抽样
相对same分组，是否改变最终固定权重的配对评测表现？不是用训练曲线判断效果。

对照是已验收的L8 same96：runtime`eef0f049bb09b7a51188ae67a6c35436a3bf055f`、
continuation controller`db60d075879750cabf30a38c555d1c3aaaf104c1`；原始→ownCP2→CP96，
96返回PPO、441/768训练胜，完整验收见
[L8 same记录](qwen-l8same-fresh197-20260926.md#completed-september26-1652-beijing)。
对照CP96路径：`/var/jfsCache/sc2-qwen-l8same96-197-20260926-r2/qwen-same/long/runs/train96/checkpoints/global_step_96`。
它只在终评阶段只读加载，不能作为random训练的初始权重。

新训练从发布原始`Qwen/Qwen3-4B-Instruct-2507`、revision
`cdbee75f17c01a7cc42f958dc650907174af0554`独立开始，不能加载任何L7/L8已训练权重。
这是**96次collect-and-PPO在线迭代**，不是L7random权重在L8的零更新评测、
也不是96遍离线大数据集或CP96→192续训。

计划任务协议与same保持：L8=`CheatVision`，Flat128/Base75689/Terran Air/canonicalBO；
相同SC2 build/地图、模型/tokenizer、prompt/观测/动作support/no-thinking、Executor、
`data/train.parquet`在线入口及其哈希。T0.8/maxresponse192/top-p1/top-k0；
gamma1/combat0.001/LR1e-6 constant/zero warmup；fullparams、PPO epochs1、
decision mini-batch8/micro-batch1/world8；post-centering invalid penalty0.1、
真实消费合法率0.5的更新前门槛，最终验收全消费回答100%合法。
SC2_RESET_CONCURRENCY1至首次观察、八局并行、reset尝试1；无D+、重采、early-stop。
实际effective config必须与历史冻结same配置逐项diff，除批准的差异外不允许漂移。

唯一计划科学因素：`same_uniform101`每step私有Random(0)抽0..100一值复制八局，
改为`independent_uniform101`每step连续独立抽八值（有放回，允许偶然重复，不是强制
八个不同seed），显式`mixed_seed_ablation`。首批49,97,53,5,33,65,62,51；第二批
100,38,61,45,74,27,64,17。ownCP2长续从reset2接36,17,96,12,79,32,68,90，
逐项验证reset0..95，不能按same的两次抽样位置恢复random的16次抽样位置。
两组均为768局，但场景覆盖与组内相关性不同，不声称训练场景多重集相同；
mixed UID内相对advantage可能混入场景难度差异，这正是消融的限制，不改奖励去抵消它。

## 训练阶段与固定权重评测

训练整组：pre8零更新→fresh train2两步16局→自身CP2 post8零更新→
自身完整nativeCP2续训3..96（94步752局）→自身CP96诊断eval8零更新。
合计**792新增自然局 = 768训练 + 24诊断评测，96返回PPO**。
pre/post/eval沿用same的原八诊断seed，仅作技术链路与小样本诊断，不作主结论。

主终评另加一批**64个全新场景seed**，三组固定权重各64局，共192局、0更新：
原始Qwen / 已完成L8 same CP96 / 新L8 random CP96。保留原始模型对照以区分
“random优于same”与“random真的优于未训练模型”。不用CP192，不新增same训练。

- 在任何新训练派发前生成并提交seed清单/hash和统计方案；与结果无关，排除训练
  0..100、原八诊断seed、历史L7common64、L8pilot和已使用的L8common64等已知评测集。
  不直接把旧common64成绩拼到新64上；本方案三组都会在同一批新64上实际评测。
- 八批×八局，批次内三组串行、轮换模型顺序，共24独立阶段；同seed、同rank，
  固定相同初始CPU/CUDA采样RNG和生成配置，同一冻结评测运行时，全部零更新。
- 主对比预登记为randomCP96−sameCP96的配对胜率差，报告逐局gain/loss、
  配对95%bootstrap区间和exact two-sided McNemar；原始模型对比为明确的次要探索性
  分析，不作多个未校正的确认性声明。单臂胜率给Wilson区间，平局另列且计非胜。
  bootstrap用固定分析RNG、100000次配对重抽，算法和seed在启动前冻结。
- 固定样本量，不看结果加局或选择最好checkpoint；64对也可能统计功效不足。
  同一模型的一次same/random训练对照不能证明跨训练随机种子稳定性或架构优势。

## 新增预算（本轮已明确批准）

仅197八张A100，训练与评测串行，前序终态/资源交接后才允许单次启动。

| 阶段 | 新自然局 | 新返回PPO | 预计耗时 | 硬上限 | 新产物上限 |
|---|---:|---:|---|---|---:|
| random短验收+96步+诊断eval | 792 | 96 | 6–9小时 | 12小时 / 96 GPUh | 256GiB |
| 三模型同64新seed固定终评 | 192 | 0 | 2–3小时 | 6小时 / 48 GPUh | 32GiB |
| 总计 | **984** | **96** | **8–12小时** | **18小时 / 144 GPUh** | **288GiB** |

预计依据已完成same96步timers约6h13m与common64的192局实测约2h25m；不是保证。
随机分组可能改变批内最慢局、响应数和更新耗时。12h/6h是资源上限，不是学习门槛。
新套件首GPU操作（含预检）固定18h绝对截止，训练受首dispatch+12h约束；
终评第一次GPU派发固定6h，且不得越过套件18h截止。所有加载/等待/存档/间隔/探针
计入、各阶段共享原时钟、45秒收尾，不因切阶段重置或借用L9/L10剩余预算。
获批、L10交接且本地/实际CPU门槛通过后，首次入场至多等待4h且不占GPU；逾期交接。

### 存储取舍必须一并批准

L8 same保留CP2及CP8..96共13套，实际整组约605.75GiB，上限1TiB/训练入场1084GiB。
当前空闲796807553024bytes=742.08GiB，L10还会写四套CP。按其余近256GiB预算
保守预留后仅约486.23GiB可用；这不是入场保证，也不能直接沿用旧1084GiB门槛启动。

推荐仅本次random保留**CP2、CP32、CP64、CP96**四套完整native CP，各26必要文件。
每套实测约46.42GiB，四套约185.68GiB，训练全新source/output/bundle/CPU/日志/replay/
tmp一起限256GiB；终评全新根限32GiB，整套所有新根唯一清单合计288GiB，不漏source
或准备残件。首次训练入场要求**352GiB可用**（整套288+64余量），每个训练阶段维持
此门槛，零更新评测至少128GiB；不改任何旧队列资源门槛。每阶段另需八卡全空/
无computePID、600GiB RAM、fsync/readback；strict GNUdu无过滤/重试/排除/旧值回退，
未知不是0。实际容量不足则等待/交接，不删数据或临时放宽门槛。

这是**已批准的运维差异**：保存频率、恢复粒度与wall-clock/资源上限不同，
不改变96次在线PPO、奖励、优化器或游戏数，但不能称bitwise等价或绝对只有seed变化。
如坚持13套存档与原门槛完全一致，则需训练1TiB+评测32GiB、整套1056GiB及1120GiB
初始空闲；当前无容量，须先另行解决存储，不能删除旧产物凑预算。

## 启动前与最终验收门槛

1. 先获训练+终评+稀疏保存+新门槛明确批准；之后才冻结唯一新RUN_ID/source/output。
   clean SHA先push并独立核验；r1已按此准备，但CPU凭证写入失败，未入队。
2. 以历史L8same冻结runtime为比较基线，只引入已批准seed消融与必要验收/存档配置；
   批准前缺**Qwen L8 random完整nativeCP2恢复合同**，本轮已最小新增并回归难度/模型/
   seed模式/driver与rank RNG绑定。不能把L7random legacy或L8same合同改个路径冒用。
   不因已有L7random实现就声称L8random已可直接上线；不修改运行中L10冻结代码。
3. 本地回归、实际197无GPU模型/host零跳过、全部真实launcher/Hydra/源码哈希、
   no-GPU Ray worker hook；精确归属/八UUID/NCCL零模型零游戏GPU预检后才游戏。
   CPU与预检通过不等于SC2或PPO通过。
4. short三阶段完整result=.done=acceptance/host/container/guardian exited0，
   自身CP2的26文件、native driver+八rank RNG、SC2 reset2与dataloader/scheduler完整；
   parent-readiness实际通过才长段，禁止legacy fallback或旧训练权重导入。
5. 训练共96条实际returned PPO、96审计和96精确seed批次，768自然局不截断；
   梯度和update_actor时间有限正值，invalidAdv≤0，所有消费回答结构/语义合法、
   canonical/no-thinking token/mask正确，plan→queue→本地Depot/Marine命令证据；
   四套CP完整、实际load返回，原八诊断seed及rank CPU/CUDA RNG配对，eval零更新。
6. 主终评三组64/64自然局、每阶段result=.done=acceptance/exit0、无截断、有限
   binary64指标、实际加载正确权重、seed和RNG成对、全部消费回答合法、0更新。
   最终报告效应量/区间/逐局配对；合法率、非零梯度、训练胜率不作为学习成功证明。
7. 任一门槛失败停止后继并保留交接，不自动修复/重试/扩预算、不删旧产物、不自动
   接CP192或其他L9/L10，不用“卡要占满”替代科学问题。

批准前验证仅：只读SSH查询exit0、正确owner/running/原截止核对、冻结queue顺序审阅、
历史same与common64记录溯源、预算算术/本地JSON检查。未执行新训练CPU或GPU测试，
更未派发本方案。新预算与代码/正式配置须在用户确认后才实施。

## 批准后的独立实现

训练入口`qwen_l8random197.py`，终评入口`qwen_l8random_eval197.py`；唯一训练root
`/var/jfsCache/sc2-qwen-l8random96-197-20260927-r1`，终评root
`/var/jfsCache/sc2-qwen-l8random-paired192-197-20260927-r1`，共享source-parent
`/var/jfsCache/sc2-qwen-l8random96-197-source-20260927-r1`。
三根全部计入288GiB；共享source保守同时计入训练256GiB和终评32GiB，suite只算一次。
两个组件共享训练root的稳定storage锁；终评只读挂载模型/训练root，只有自己的root/tmp及锁可写。
L10队列/owner/guardian/全部五阶段小型验收均须completed/exit0；运行中的L10不修改。
无新增GPU前四小时等待从L10交接且CPU通过起算；训练、终评、suite时钟见预算段。

主终评64seed及24阶段次序固定在`qwen_l8random_plan.py`：
SHA256 `7a2d619653c24c1ad40b50e9a9aea00a3b264885b70c02b5aff519a7547baebd`，
生成RNG2026092708；排除已登记0..100/诊断8/L7common64/L8pilot32/旧L8common64。
统计bootstrap RNG2026092709、100000次配对重抽、percentile95%区间（linear quantile），
exact McNemar；无discordant pairs时p=1。计划和算法在新GPU派发前冻结，不事后换seed。

相对历史L8same的核心`agent_system/verl/configs/scripts/data`差异仅native恢复合同扩展
及对应source manifest；checkpoint manager和PPO trainer哈希仍与历史same一致。
新增`accepted-qwen-l8-random-full-state-prefix-v1`绑定Qwen/CheatVision/independent/mixed/
native driver RNG。实际CPU配置还须以normalized_protocol对历史same逐项比较，仅允许
seed_protocol与seed_group_mode科学差异及已登记的路径/存档/预算控制差异。

常用入口（仅在一次正式准备中调用；不作为重试指令）：`prepare`；实际host
`host-regressions`；无GPU `regressions-command 0`、`cpu-command 0/1`及
`cpu-hook-command 0 pre`、`0 train2`、`1 train96`；终评`cpu-command`与前三臂CPUhook。
CPU通过后host `queue` 单次等待L10。短验收后自动native CP2 parent-cpu，训练结束
核对每套小状态、完整26文件及实际返回PPO，再进入终评。任一失败阻断全部后继。

最初本地29项新控制器/合同测试已通过，之后扩展至116项（112通过、4本机Torch跳过）。
实现提交`1fbe6e1ecc9f39b22d69ad38df165fcc1dd61b8d`已push并独立dry-run核验
远端准确fullSHA一致；197 r1从该SHA准备。实际host71、模型/控制器265项零跳过，
但模型CPU容器凭证写只读根失败；测试通过不冒充整体CPU准入通过。

### r1 CPU失败交接（23:16:49北京）

准确CPU容器`bae1b326597da3f58f31439c89138606e614ca995fedfc962deb3e47643aed36`，
DeviceRequests=null、exit1/noOOM；错误为凭证原子临时文件在suite只读挂载下触发EROFS。
三根严格du成功、stderr空，合计50,184,762bytes；queue/dispatch/readiness尚不存在。
L10准确long/train96容器仍为`5c6dad7a7beff07053574400d6bd5a090fbc92db1f77a0ff70abc0b1f723befd`，
running-unverified，原截止不变。未改变其源码、容器或队列。

本地修正仅CPU凭证路径及对应读取，新增真实Docker挂载边界回归；117项测试
113通过、4本机Torch跳过、diff检查通过。尚未在服务器部署或重试。
下一步需明确批准受控r2：唯一新RUN_ID/冻结SHA，保留r1全部残件，新旧六根合计
仍受训练256GiB、终评32GiB、suite288GiB原上限；原984局/96PPO和12h/6h/18h、
96/48/144GPUh不增加，首次GPU时钟尚未启动。仍先全部CPU门槛、再等待L10成功交接，
不重试r1、不自动重试r2、不删产物、不接CP192。
