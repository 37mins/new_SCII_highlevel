# Qwen L9 / L10 RL 长训：已批准预算与单次队列

最新状态（9月27日22:20:19北京）：已批准的r3受控接续完成L9终评（3/8、0更新、
result/.done/acceptance及准确host/guardian/container全通过）；保留原96步训练，
不重复训练。L10于22:19:00自动派发，22:19:34启动pre8零更新，后续fresh96步RL
已在同一冻结队列中，尚不声称已返回PPO。L10固定硬截止9月28日10:19:00，
原suite截止12:11:48不变。r1/r2失败和原预算保留，全部九个根计入原512GiB。
见[接续及完成详情](qwen-l9-l10-continuation-20260927.md#r3-actual-launch-and-l9-completion)
与[小凭证](qwen-l9-l10-r3-launch-20260927.json)。下文旧状态为历史快照。

状态（9月27日20:49–20:55北京）：**L9已执行96/96次PPO，但长段严格验收失败；CP96终评和L10未启动，八卡空闲**。
训练容器20:28:32正常exit0、result=.done；验收器随后因
`KeyError: checkpoints/global_step_32/data.pt`失败。结果清单仅列最终CP96，
验收器却从同一清单索引中间CP32/64；stat确认三套各26必要文件存在且非空，
不是已经证明权重内容完整。训练768局297胜，不能将进程完成写成整组验收通过。
本轮只读留证与绘图，没有修复、重跑、改冻结状态或重新派发。
[失败凭证](qwen-l9-acceptance-failure-20260927.json)；
[曲线与解释](l8-l9-curves-20260927.md)。原截止和失败阻断边界不变。
10:58单次队列自动在L8完成后接续，没有重复派发。
用户要求追加 L9/L10，并明确选择“RL 长训，先给训练预算”。之前提出的
384 局零更新迁移评测没有获选，不执行。沿用本 experiment record 和既有分支。

## 建议范围与目的

- 两组独立实验：L9=`CheatMoney`，L10=`CheatInsane`。映射来自本仓库
  `agent_system/environments/env_package/sc2_online_restored/SC2ArenaDyStrategy/tools/constants.py`
  的一基难度顺序，以及环境对 `Difficulty` 枚举的同名解析；正式启动时还须核验
  冻结依赖中的实际枚举与生成配置、manifest 和 replay。
- **建议各自从原始 Qwen3-4B-Instruct-2507 开始**，revision
  `cdbee75f17c01a7cc42f958dc650907174af0554`。不从 L8 CP192 开始，也不把
  L9 权重传给 L10。这是两个难度的 fresh 学习实验，不是逐级迁移训练。
- 沿用 L8 的 `same_uniform101`：私有 Random(0)，每个训练 step 从0..100
  抽一个场景 seed，复制到八局；下一 step 重新抽。两组各自从 reset0 开始，
  完整记录并验证 reset0..95；不是 step 内八局独立 random。
- 每组 pre8零更新 → fresh train2（16局、2次返回 PPO）→ ownCP2 post8零更新
  → ownnativeCP2 train3..96（752局、94次返回 PPO）→ ownCP96 eval8零更新。
  合计每组 **96次真实在线 collect-and-PPO 迭代 / 768训练局 / 24评测局**；
  两组合计 **192次迭代 / 1,536训练局 / 48评测局 = 1,584新增自然局**。
  global step 不等同于单个底层 Adam 调用，也不是遍历大离线数据集96epoch。
- `data/train.parquet` 沿用原内容和哈希，用作现有在线 SC2 入口；不新增公开数据集。
  Flat128/Base75689/Terran Air/canonicalBO；T0.8/maxresponse192/top-p1/top-k0；
  gamma1/combat0.001；LR1e-6 constant/zero warmup；fullparams、PPO epochs1、
  decision mini-batch8/micro-batch1/world8。canonical/no-thinking、invalid-credit
  和合法率门槛、Executor、SC2_RESET_CONCURRENCY1至首次观察、八局并行及
  reset尝试1不变；无D+、重采、early-stop。正式 effective config 须逐项冻结。
- 对照是每级自己的原始 pre / CP2 / CP96，不用跨难度的训练胜率当学习证据。
  八个复用评测 seed 只作小样本诊断；报告逐局配对 gain/loss，不能宣称泛化、
  架构优势或“攻克”该难度。额外 common64 强评测不在本预算内。

## 已批准的排队和时间预算

当前 L8 common64 全链真实验收后，再 **L9 → L10 串行**，仅197八卡。
不打断当前 L8，不与其抢卡，不为了占卡启动无意义负载。前序或任一级失败即
阻断全部后继，保留证据等用户决定；不自动重试、修复重启或接其他实验。

- 预计每级6–10小时，两级12–20小时，依据已完成 L8 96-step 的约6h13m
  step timers 和后续96-step的5h40m整组实测估算。更高难度可能改变局长，
  加载、等待、存档和终评另有波动；不是保证完成时间或收敛承诺。
- 每级最多12wallh /96GPUh；两级整组最多 **24wallh /192GPUh**。
  第一组首次GPU操作（含预检）固定全组24h绝对截止；每级首GPU操作固定
  自身12h截止，阶段共享、不重设，且均不得超过全组截止。L9结束后等待L10
  入场也消耗全组时钟。各截止预留45秒收尾。
- 初次等待 L8 成功终态和资源入场最多24小时，不持卡；未满足则不启动，
  不默默延长。该上限随本预算批准，并在冻结配置记录。

## 不删旧产物的磁盘预算

10:17:32北京只读容量检查：可用NVMe **850,856,951,808bytes（约792.4GiB）**；
可用RAM **704,592,752,640bytes（约656.2GiB）**。这是时间敏感快照，须入场重查。
L8每套完整CP实测49,843,590,588bytes（约46.42GiB），仅文件名/stat清单，
没有读取模型/optimizer内容。按每8步保留两组CP预计超出现有容量。

建议只保存每组 **CP2、CP32、CP64、CP96** 四套完整nativeCP（各26必要文件）。
每组CP预计199,374,362,352bytes（约185.68GiB），两组约371.36GiB。
每组全部新source/output及bundle/runtime/CPU/临时文件/日志/replay合计硬限
**256GiB**；两组所有新根合计硬限 **512GiB**，不排除准备残件或计量失败。
这是新的保存频率与恢复粒度：发生故障时不能假定存在CP8/16等，不覆盖历史记录。
不删旧权重、不改旧门槛、不把不足算成0、不以估计替代实际GNUdu严格计量。

新队列首次GPU预检前要求至少576GiB空闲（512GiB整组上限+64GiB余量）；
每级训练入场至少320GiB（256+64）空闲；零更新评测至少128GiB。
每阶段同时要求八卡空闲且无computePID、600GiB可用RAM、fsync/readback通过。
存储实际超过任一上限、计量失败或资源不足不放宽门槛。所有新root精确清单、
RUN_ID、截止和冻结SHA须批准后再落实；不改当前运行中的L8队列。

## 启动与验收要求

批准后才实现薄编排、完整effective config、回归和实际无GPU入口检查；
不修改已冻结deployment。源码clean commit先同步远端并核验SHA。CPU结果不能
当GPU/PPO证据；首次GPU预检计入预算。short三阶段全部通过、自身完整nativeCP2
driver/rank RNG/sc2_state与parent-readiness后才long；不允许legacy fallback。
真实模型/optimizer/scheduler/dataloader和RNG加载返回、每级96 returned PPO和
96审计/seed行、有限正梯度/正update_actor时间/invalidAdv<=0、自然局无截断、
全消费结构语义合法无thinking、plan→queue→本地Depot/Marine与worker tokenizer/
mask证据均保留。全部精确container/guardian/host终态与result/.done/acceptance
完成exit0及四套完整CP清单后才技术验收，不用胜率替代执行证据。

## 当前占用证据

[10:12:56只读快照](qwen-l9-l10-budget-status-20260927.json)：当前L8common64
已验收32/192局、4/24阶段，正在b01-cp192；八个ray worker各占约5.1–5.2GiB。
瞬时GPU利用率0%不代表空闲，八卡仍有computePID且准确owner容器运行。
这一轮只读检查与预算文档，没有派发L9/L10、删除、停止或服务器写操作。

## 批准后的冻结实现与启动门控

用户对上述方案明确回复“批准”。源码从本分支 `601482e5c2a32250822c73617c1ddf80ad6bf356`
继续；新入口 [qwen_l9l10_same197.py](qwen_l9l10_same197.py)，完整实际环境预检
[qwen_l9l10_training_probe.py](qwen_l9l10_training_probe.py)。复用本仓库已有
L8/fresh launchers、短验收观察器、host sampler/guardian 和 native CP loader，
不更换训练算法/依赖/许可证。共享核心唯一扩展是两个明确opt-in的L9/L10完整
CP2恢复合同版本：绑定各自难度，不允许L7/L8或跨级合同冒用；旧合同行为不变。
源码哈希清单随之更新，旧冻结deployment不变。

准确 RUN_ID / output：

- `sc2-qwen-l9same96-197-20260927-r1`，`/var/jfsCache/sc2-qwen-l9same96-197-20260927-r1`。
- `sc2-qwen-l10same96-197-20260927-r1`，`/var/jfsCache/sc2-qwen-l10same96-197-20260927-r1`。
- 共享新source-parent `/var/jfsCache/sc2-qwen-l9l10same96-197-source-20260927-r1`，
  代码子目录 `code`。每级有独立runtime clone（`--no-local`，无旧alternates链）。

合计严格测量以上三个完整根512GiB；各级自身完整output加整个共享source-parent
各256GiB，shared source保守计入两级，但suite只计一次。套件queue/lock/共同凭证
位于L9根，因此也计入L9；每级`arm-storage`、L9`suite-storage`保存完整计量结果。
所有新子进程使用L9根的同一稳定`.storage.lock`，只有准确part/tmp和该锁可写；
两个父root/runtime/source、模型与依赖只读。L10不得写L9产物。

两级各含`qwen-same/short`、`qwen-same/long`。十个独立阶段容器，另各一个
零游戏/零更新八UUID/NCCL预检；每级首次GPU预检即开始自身12h预算，L9还固定
suite24h。L10等待也计入suite。队列不重复准备、不允许已有dispatch或queue状态。

前序固定 `/var/jfsCache/sc2-qwen-l8-common192-197-20260927-r1`，源码
`e01594ecd3ea7b43d2296b371fd340f9d575ab3a`，截止1790495189.9456112。
等待其原host/controller对全部24阶段完成验收，检查精确container/guardian、
queue/state、result/.done/acceptance、小manifest/load/seed/RNG配对凭证；不改旧队列
的historical successor字段，不重新读取全日志或大CP以重复验收。任何failed阻断。
L9五阶段全部真实通过后才派发L10，L10也从原始权重重新开始。

批准后本地命令（bundled Python，PYTHONPATH含现有临时OmegaConf与tests）：
`-B -m unittest test_qwen_l9l10_same197 test_qwen_l8same_fresh197 test_qwen_l7same_fresh197 test_sc2_policy_resume test_l7_followup197 test_qwen_l8_common64_197 test_host_stage197 -q`，
**141项通过、0跳过**（含拒绝仅审计无返回PPO、零梯度/非有限invalidAdv、缺native state、
多余CP和错seed的回归）。这不是实际Linux/GPU证据。正式服务器还必须完成实际host回归、
无GPU模型/控制器回归、十个真实launcher/Hydra、34源码哈希、每级pre/train2/train96
三个真实Ray worker hook检查；只加载metadata，不载大权重、不进入SC2或CUDA。
post/eval还通过完整实际launcher配置检查，后续实际GPUload与RNG配对另验收。
所有失败留存并阻断，不在同一RUN_ID修改冻结代码重试。

CLI：`prepare`一次创建两级；`host-regressions`；`regressions-command 9 0`；
`cpu-command <9|10> <0|1>`；`cpu-hook-command <9|10> <0|1> <stage>`；
全部通过后`queue`在独立tmux中仅单次调用。prepare/queue不要求位置参数；其他
模式必须指定级别和short/long索引，防止历史入口分派错误。
启动/CPU/queue凭证另行追加，不能用此实现说明冒充已经运行。

## 实际 CPU 验收与单次入队（9月27日10:59:51北京）

冻结 runtime/controller `1c6cf60b111570ef13f9817d0b1b16fb774546f5` 已成功推送
既有 `codex/fix-sc2-startup-port-race` 分支，并在部署前用独立 `git ls-remote`
核验准确SHA。两级runtime/source均clean；未修改旧deployment或当前L8运行。

实际197宿主执行`host-regressions`：71项通过、0跳过；准确无GPU容器执行
`regressions`：211项通过、0跳过、CUDA未初始化。随后四个`cpu`容器通过
十阶段真实launcher/Hydra/34源码哈希和实际SC2 Difficulty枚举9/10检查；
六个`cpu-hook`容器通过各级pre/train2/train96的真实Ray worker导入。
11个准确容器均exited0、DeviceRequests=null；hook确认0CUDA设备、0模型加载、
0自然局、0更新。小凭证：[CPU验收](qwen-l9-l10-cpu-20260927.json)。
长段`actual_parent_verified=false`正常等待各自未来完整CP2；继承helper中
“SpB”文字只是历史标签，实际恢复合同和路径为本次Qwen各级，不代表已通过parent gate。

10:58:40仅调用一次冻结`queue`，独立tmux socket
`sc2_qwen_l9l10same96_197_20260927_r1` / session `qwen_l9l10same96_197_r1`。
10:59:51实查进程存活，`queue-state.phase=waiting-predecessor`，三个dispatch
文件（suite/L9/L10）均不存在：尚无新GPU、SC2或PPO，GPU时钟未开始。
前序L8 host已验收12/24阶段、96/192自然局，正在b04-cp96；root queue中的
completed空数组是尚未结束同步，不据此抹除host已完成阶段。

新两级arm分别49,777,727与49,739,324bytes，suite三完整根74,895,717bytes；
各自严格GNUdu return0、stderr空、无storage-failure，低于256/256/512GiB。
等待初次入场截止1790563688.7018523，不占GPU；成功入场后才固定12h/24h
GPU预算时钟，不能把等待上限当作预计训练结束时间。
只派发已批准队列，不删产物、不自动重试或接其他组。
[队列/前序/存储小凭证](qwen-l9-l10-queue-20260927.json)。

## 20:22只读进度核验

[小凭证](qwen-l9-l10-status-20260927-2022.json)：前序L8common64于12:11:26
完成192局、0更新，queue/state/host全completed/exit0；冻结控制器前序验收通过。
原始模型46/64（71.875%），L8CP96 35/64（54.6875%），L8CP192 37/64（57.8125%）。
24阶段result=.done=acceptance，全8批seed/rank RNG配对；原始→CP96为5增胜/16失胜，
原始→CP192为5/14，CP96→CP192为3/1。此批样本中训练权重低于原始，不支持提升结论。

L9于12:11:48.224自动首次GPU派发，short三阶段全部通过（pre7/8、train2训练16/16、
post5/8；这里只作小样本诊断），自己的完整nativeCP2和parent-readiness通过。
12:33:57长段准确容器启动；actual model/optimizer/dataloader load返回global2/reset2，
next53×8、source=checkpoint。20:21:49最近1MiB日志尾显示实际returned92/93/94，
梯度和update_actor时间有限正值、invalidAdv=0；最后global94梯度0.0015642508230614891、
update_actor46.104998870752752秒。global95通过pre-update credit gate只算待更新，
不能把93条长段audit算成93次已返回PPO。尚无train96 result/acceptance或eval96。
CP32、64目录已出现，此轮未读取大权重；不是完整长阶段checkpoint最终验收。

八个worker仍占各约5.1–5.3GiB显存，准确容器running/unpaused、无OOM；console持续
更新。瞬时利用率0%不是无任务。严格计量L9新根+source约141.6GiB/256GiB，GNUdu
return0/空stderr，没有storage-failure；suite也在512GiB内。L10无dispatch，等待L9
训练和终评验收完成。依据近几步4–7分钟耗时，L9含存档终评估计20:40–21:10结束；
此为估计，不保证。原固定L9硬截止为9月28日00:11:48，整组为9月28日12:11:48。
本轮无服务器写操作、重启、删除、补跑或预算变更。
