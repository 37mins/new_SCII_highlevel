# L8 SpB random 96-step RL：启动请求与新预算

最新状态：`failed / short-train2`，2026-09-29 09:41北京只读核验。
队列于9月28日23:49:22因存储计量前guardian暂停请求超时而停止；不是磁盘超额
或OOM的证据。准确train2容器被守护器收尾停止，exit137/OOMKilled=false。
pre已验收5/8、45/45消费回答合法；短训日志返回step2，16自然局7胜，两个
pre-update审计120/120合法，但无result/.done/acceptance，严格短训未通过。
CP2文件清单存在不代表其已通过真实恢复验收；post/长训/选优/主终评全未启动。
八卡09:39均0MiB/0%、无compute PID。本轮不修复、不重启、不派发、不删除，
原预算时钟不变；此前12–20小时ETA不再有效。修复和受控续跑另行授权。
[失败交接凭证](spb-l8random-r1-failure-20260929-0941.json)。

以下为启动时历史：`running-unverified / short-pre`，2026-09-28 23:14:50北京只读核验。
单次queue23:12:07、首次GPU23:12:08.209、pre容器23:12:40启动；
八卡mapping/NCCL已通过，原始SpB已加载并进入L8 SC2/planner，尚无PPO和阶段验收。
运行源码`f7497ab5a1876a5e899f3e620758850c996212d6`，正式准备前已push并核验远端。
训练及选优固定截止9月29日23:12:08.209；suite截止9月30日05:12:08.209北京。
[实际CPU凭证](spb-l8random-r1-cpu-20260928.json)及
[单次启动凭证](spb-l8random-r1-launch-20260928.json)优先于下文提案阶段状态。

2026-09-28 用户在完整预算与保留范围后回复“批准”。
批准1048局/96PPO/30h/240GPUh/352GiB及仅本组非best CP32的定点删除，
不是旧组清理或自动重试授权。实际CPU/queue/GPU凭证随后记录；不能把本段当启动凭证。
此前用户要求“现在把这个实验跑上”；
这是新的 SpB L8 训练，不是已完成的 SpB L7 random，也不是 Qwen L8 的零更新评测。
提案轮仅做只读资源/资产尺寸核对；本批准轮新增适配器与回归，实际派发另留凭证。
下述数值预算及本组精确保留/删除范围已获确认。
不借用旧 Qwen / SpB 的剩余预算，不把旧授权解释成无限重试或扩量。

## 当前队列与资源（时间敏感）

9月28日22:24:53北京，197 上 Qwen L8 random r3 整个队列与主终评均
`completed / exit0`；八张 A100-80GB 显存/利用率为0、无 compute PID。
四个历史服务容器仍运行，未停止或修改。可用 NVMe 774.24GiB、RAM756.53GiB。
原始 SpB 模型路径存在，拟用三个新根不存在。
[只读凭证](spb-l8random-proposal-check-20260928.json)。此快照不是资源预留。

## 科学问题与一致协议

主问题：原始 SpB 在 L8 用每局独立场景 seed 做96次真实PPO后，固定CP96是否
优于其未训练原始模型？采用训练外固定种子配对终评，不能只看训练曲线。

- 原始 `Panyuqi/SpikingBrain-2.0-instruct`（约5.17B），来源
  `/data/yangjinyue/sc2-spb2-level7-20260814/model`；历史资产 revision
  `sha256:de52e8ef993afc763f9d4fb498e8d8302ef0bc13bd7dfd53c6ae5f77f43698b5`。
  新部署必须核验模型清单，不能加载任何 L7/L8 已训练 CP 作为初始权重。
- 以已完成 Qwen L8 random 冻结 `ad81511b270f782420208ac8a6f305a141e8042b`
  的任务协议为对照；切换模型及其必要架构入口，不修改奖励、执行器或生成支持集。
  SpB 入口 SWA dropout=0、per-call state shaping 关闭，实际 effective config 冻结核对。
- L8=`CheatVision`，Flat128/Base75689/Terran Air/canonical BO，在线
  `data/train.parquet` 入口；96次 collect-and-PPO，不是96遍离线数据集。
- 私有 `Random(0)`，每step从0..100有放回独立抽8值，
  `independent_uniform101 / mixed_seed_ablation`，完整核验 reset0..95。
  初始两批49,97,53,5,33,65,62,51及100,38,61,45,74,27,64,17。
- T0.8/max response192/top-p1/top-k0；gamma1/combat0.001/LR1e-6 constant、
  zero warmup；full parameters、PPO epochs1、decision mini-batch8/micro-batch1/world8。
  canonical/no-thinking、post-centering invalid penalty0.1、消费合法率0.5更新门槛；
  最终验收要求所有消费回答结构和语义100%合法。
- reset concurrency1直到首次观察，八局仍并行，reset attempts1；无D+、重采、
  early-stop或隐式超参搜索。模型参数量/FLOPs差异显式保留，单次实验不能证明架构优势。
  mixed UID 的 advantage 可能混入场景难度差异，不为本组另改奖励抵消。

## 分阶段新增预算（已批准）

| 组件 | 自然局 | PPO | 硬时限 / 八卡GPU小时 | 新产物硬上限 |
|---|---:|---:|---|---:|
| pre8→fresh train2→post8→ownCP2续至96→eval8 | 792 | 96 | 与选优共用24h / 192GPUh | 与选优共用320GiB |
| CP2/32/64/96各32局独立验证 | 128 | 0 | 上述24h内，组件另限6h / 48GPUh | 上述320GiB内，子目录另限8GiB |
| 原始SpB与本次CP96各64局配对终评 | 128 | 0 | 6h / 48GPUh | 32GiB |
| 整组 | **1048** | **96** | **30h / 240GPUh** | **352GiB** |

训练局为768；余下280局为24诊断+128选优+128主终评，全部零更新。
粗略排期12–20小时，不保证；首段实测后再更新ETA。硬上限不是预计耗时或必须占满时长。
训练+选优24h、suite30h从首次GPU操作（包括映射预检）固定绝对时钟；主终评另受
首次终评GPU起6h与suite截止的较早者约束。加载、阶段间隔、预检、CP写入均计入；
不在切阶段/续CP2时重设，45秒收尾。CPU准备时间单独记录，不冒充GPU训练。

## checkpoint 与存储

只stat既有 SpB nativeCP96：每套63,570,346,205bytes（59.20GiB）；四套估算
236.82GiB，不能用 Qwen 的46.42GiB估算SpB。只保存CP2/32/64/96完整native状态，
不每8步保存13套。320GiB训练/选优上限保留约83GiB供其余产物；超限即停止，不删旧组。

拟沿用 latest2+validation-best：训练不中途为选优暂停，训练结束才评测四个候选。
保留 `{CP2, CP64, CP96, best}`，同目录引用，不复制。以独立32局胜数选best，同分
留较早CP；主终评仍固定CP96，不以best替代。完整选优验收与无活跃读取检查后，
唯一可删对象为**本新组CP32且它不是best时**，须本次授权涵盖该范围；删除不可恢复。
峰值仍四套，不声称单套更小或始终只保留两套。旧L7/L8/L9/L10任何产物均不删除。
原生保存格式不改；阶段终态/26必要文件/native状态验收、fsync后发布原子小清单，
半写CP不发布、不评测、不清理；完整日志/指标/小状态凭证始终保留。

训练首次和阶段准入拟要求空闲NVMe≥416GiB、评测≥128GiB、RAM≥600GiB、八卡
全空且无compute PID、任务归属及fsync/readback通过；部署时再实时复核。
不是放宽旧队列门槛，而是独立新预算；禁止改旧冻结部署。

## 评测、解释与验收门槛

技术诊断沿用原八seed，不据这8局判断学习收益。独立验证32与训练0..100、诊断8、
主终评64互不重叠，复用Qwen L8 random已冻结验证清单，不由SpB结果选择。
原始SpB/CP96使用Qwen L8 random的同一64个训练外主测试seed；不重跑Qwen。
该64已经见过Qwen结果，应称复用benchmark，不能宣传为本次设计完全未见的新确认集。
SpB内同seed/同rank/相同CPU-CUDA采样RNG逐项配对；跨架构相同初始化不等于相同
随机数消费轨迹或等FLOPs。保存清单hash、固定顺序和统计方案后才GPU派发。

预登记主对比为SpB CP96−原始SpB，报告逐seed gain/loss、胜率差、exact two-sided
McNemar和100000次配对bootstrap95%区间（PCG64种子2026092801，linear分位数），
单臂Wilson95%区间；平局计非胜且单列。与现有Qwen random45/64的比较仅探索性，
没有SpB L8 same训练对照，因此本组不能单独判定SpB same/random差异。

部署前必须通过模型/恢复合同/保留/预算/seed回归、宿主CPU测试、五训练阶段及
验证/终评所有实际启动器和Hydra展开、Ray worker hook、模型入口和源码哈希核对；
新L8 SpB full-state CP2合同不可冒用L7 legacy合同。CPU测试和GPU映射不冒充PPO。
短三阶段严格验收、CP2 driver/rank RNG/sc2_state完整且真实parent-readiness通过，
才准入长段；不得legacy fallback或跳过短验收。

每阶段result/.done/acceptance与host/guardian/准确owner容器exit0一致，clean冻结SHA、
world8/binary64-v1、自然终局无截断；96真实returned PPO+96审计/有限正梯度与正update
时间/invalid advantage≤0、全合法消费回答、planner→queue→本地DepotMarine执行链。
CP2→long及评测CP均需实际load返回、正确global step和全rank RNG配对小凭证。
所有指标必须有限，运行/验收成功与学习有效分别报告。

## 实施边界与拟用身份

复用原record及`codex/fix-sc2-startup-port-race`，不新开实验分支。
拟RUN_ID `sc2-spb-l8random96-197-20260928-r1`，仅197八卡串行。
三个精确计量根（当前均不存在）：

1. `/var/jfsCache/sc2-spb-l8random96-197-20260928-r1`
2. `/var/jfsCache/sc2-spb-l8random-paired128-197-20260928-r1`
3. `/var/jfsCache/sc2-spb-l8random96-197-source-20260928-r1`

source为第三根下`code`，选优在训练根内；整个根计量含bundle/CPU/准备残件/tmp，
严格du不重试、不筛选/排除、不用旧值回退，未知不算0。新实现/测试、最终配置和
冻结SHA必须另有凭证；本提案不是可直接派发的冻结deployment。
仅在新预算获批且全部准入通过后单次启动；任一失败阻断所有后继并交接。
不停止其他任务、不自动修复重启、不自动重试、不接CP192或L9/L10。

提案轮验证：只读GPU/容器/前序小状态、磁盘/RAM、原始模型路径与历史manifest、
准确CP目录file-stat；预算算术与JSON语法/diff。当时未运行新实验CPU/GPU测试。

## 实施入口与验证

训练入口 `spb_l8random197.py`、评测入口 `spb_l8random_eval197.py`，
种子/阶段定义 `spb_l8random_plan.py`。薄适配器复用已验证L8 queue、真实PPO验收、
无GPU hook和原生checkpoint保留控制；只在当前进程安装SpB profile，不修改旧部署。
恢复新增严格 `accepted-spb-l8-random-full-state-prefix-v1` 合同，拒绝Qwen、
L7难度、same seed、legacy RNG缺口或其他目标步。原有合同保持原样。
共用入口增加显式模型/预算参数，默认Qwen行为由既有回归覆盖。

新source从已推送clean SHA恢复到上述唯一source-parent/code。宿主执行
`python3 -B <record>/spb_l8random_prepare197.py`：单次prepare、host回归、
模型无GPU回归、五训练启动器、16终评+16验证启动器、三个训练和六个评测worker
hook，全程不派发GPU；任何失败保存preparation.json并停止，不重试同名容器。
CPU全部通过后，在唯一tmux socket/session中单次执行
`python3 -B <record>/spb_l8random197.py queue`。
队列首次八卡mapping/NCCL预检计入首派时钟，成功后才pre→train2→post→long→eval8
→validation32→精确保留→paired64。现有Qwen全部终态/owner容器作为只读前序门槛。

启动器逐项对比历史SpB L7实际resolved_config（SHA256
`fe0e3c00571eabc7e625ea192b55f6e360d5a6cb3d53c602085a81bada1fed5b`），
只准L8难度及已登记的rendezvous/路径/保存/时限控制差异，其他训练语义不得漂移。
大权重不读入本地；仅正式模型进程加载它们。

本地143项回归全部通过、零跳过；覆盖旧Qwen默认入口及新SpB档位、原始权重路径、
准确native CP2合同、失败阻断/共享时钟/禁止重复派发、固定种子、精确保留边界。
[本地回归与新只读健康快照](spb-l8random-local-preflight-20260928.json)。

服务器一次性准备实际通过：模型/控制器195项、host71项，均零跳过且无CUDA；
五训练、16主终评、16选优启动器/Hydra展开，以及9个worker hook通过，14个CPU
容器exited0、DeviceRequests=null、无OOM。长段actual_parent_verified=false是
等待自身未来CP2的门槛，不能当失败或跳过。原Qwen全终态前序小凭证与准确容器通过。
新三根首轮71,400,055bytes/352GiB、计量return0、空stderr，非永久占用量。
运行中的MFU=0来自估算器不支持SSESWAMoBA，不能解释成GPU未工作或回答无效。
SC2日志复用Qwen3-30B显示名称不代表模型；模型权威为SpB manifest与实际模型类。
