# SpB L8 random：失败 run 权重取证与仅补评测方案

状态：`80/264 accepted / sel-b01-cp64 running`（09月30日10:38北京核验）。
用户在完整264局方案及失败权重接用申请之后明确回复“批准”；本次预算已获授权。
此前“继续下一步”仅用于只读取证和小型CPU状态检查，未提前派发GPU。
本方案沿用原 record；旧 r1/r2、原时钟及 failed 结果均不改写。

## 9月30日08:30–08:31北京实测

- 197 八卡0MiB/0%，无本组运行中的GPU任务；四个历史服务容器未触碰。
- r2 short三阶段result/.done/acceptance一致，CP2合同登记19个小文件hash全部匹配。
  r2 long/queue仍failed，准确旧容器exited137/noOOM；long result/.done/metrics缺失。
- 完整返回指标：短训step1–2两条、长训step3–96九十四条，均有binary64-v1。
  不仅检查最后一条；禁止重复/缺步/非有限数，所有已解析指标有限。
  长段梯度范围0.37493400772412616–287.0314712524414；update_actor范围
  6.3330759750679135–159.01566474698484秒；invalidAdvMax不为正、合法率为1。
- 96份pre-update审计与返回步对应；2758/2758审计回答合法。seed reset0–95完整
  匹配私有Random0独立抽取。768个唯一自然结束对局、503胜，无截断；每步返回
  胜率与对局账本一致。预更新审计本身不冒充实际更新，也未重新完整审查command trace。
- CP2/32/64/96各26必要文件非空，总计每套约59.20GiB。实际CPU-only容器读取
  40个小文件：driver Python/NumPy/Torch RNG可恢复；全8rank RNG、scheduler步数、
  dataloader和SC2 reset计数通过。没有读取model/optim大分片，未证明GPU可加载。
- CPU审计容器`5a7db0ff0f7e2a1a4344889365b94886f41b976d3d53efd418e5de6ba9749723`
  exit0、DeviceRequests=null、Devices=[]、两挂载均只读；1CPU/2GiB/120秒上限，
  实际约2.2秒、CUDA未初始化、0游戏/0更新。容器保留，无旧run写入。
- 一次15秒有界严格GNUdu：r1/r2六根加terminal CPU两根共323367902759bytes
  （301.16GiB），return0/空stderr；当前NVMe空闲802001248256bytes（746.92GiB）。
  这些是快照，不是准入预留。无checkpoint删除。

小凭证见[恢复取证](spb-l8random-r2-recovery-audit-20260930.json)。脚本
`inspect_spb_l8random_r2.py host`只在服务器做最多100MiB/60秒流式扫描并返回PPO投影；
本地Git仅登记计数/范围/首尾和指标行hash，不上传完整96行数据或完整日志。
`small`使用远端已核验的审计提交`d1900c26c88311a9a0cea49adda0d1abbd8f96ac`，
固定既有image`sha256:1a497d5721f89bb2e98c0273c4b1495f8fdc6921d589650d090871c11b8d1649`。
CPU模式后增加的host前序合同核对未改变small模式；最终脚本hash记录在凭证中。
8项只读解析器回归通过（缺步、重复、精度、NaN、非正梯度、有界输入等）。

## 能作出的结论

96次真实PPO和完整小状态已有证据，不能因收尾失败就默认必须重跑96步。
但旧r2未通过原终态验收，**不能把它改成completed，也不能把它直接当成accepted parent**。
目前只可提出“基础设施失败run产出的候选权重，使用独立恢复合同补评测”。
其模型本体、实际加载和新GPU收尾路径仍须验证；取证不是成功加载或策略提升证据。

## 待用户确认的一次受控恢复

只补原计划尚未运行的264自然局、0次PPO，不重新训练、不接CP192：

1. CP96原8seed诊断评测，配对自身CP2 post的rank/CPU-CUDA采样RNG；亦作首个
   真实GPU加载与terminal-drain收尾门槛，失败立即阻断全部后继，不另加smoke局。
2. CP2/32/64/96各32局独立selection，合计128局；平局仍选较早step。
3. 原始SpB与固定CP96各64局primary，合计128局；不用selection-best替换CP96。

使用原冻结deployment的两套seed，不换题、无需重跑已完成的Qwen对照：

- selection32 SHA256：`0f47acf2c792395cb17d73d678bbe8ad618b2c89c1ff5a4d85733465fa2a372c`。
- primary64 SHA256：`7a2d619653c24c1ad40b50e9a9aea00a3b264885b70c02b5aff519a7547baebd`。

预算申请：仅197八卡串行；**从首次GPU操作固定8小时／64 GPU小时**，包括加载、
阶段间隔、33个8局批次、验收与收尾；45秒保留收尾，不在阶段间重设。
新增source+output总计**32GiB**；旧r1/r2六根+本修复CPU两根+新source/output两根
共十根整体上限仍**352GiB**，无过滤/排除/旧值回退，失败未知不当0。
当前301.16GiB加新增32GiB约333.16GiB，仍需每阶段严格实测。
入场要求八卡全空/归属清楚、600GiB可用RAM、128GiB可用NVMe、fsync/readback。
不复制checkpoint、不删除任何旧产物，本恢复不执行原条件式CP32清理。

预计约**5–7小时**：已验收pre/post8局分别约10.74/7.52分钟（从manifest至result），
33批外推约4.13–5.90小时，再加启动、权重加载与验收；仅粗估，不保证后续难度或速度。
08:30时原训练+selection截止09月30日10:11:03.278，只剩约1小时41分，不足以
覆盖诊断8局+selection128局。原suite截止16:11:03.278也不改写。
这次申请是**单独的新run预算与失败产物接用授权**，不是假称旧截止尚够或自动延期。

批准的新RUN_ID `sc2-spb-l8random-recovery264-197-20260930-r1`：

- output `/var/jfsCache/sc2-spb-l8random-recovery264-197-20260930-r1`
- source-parent `/var/jfsCache/sc2-spb-l8random-recovery264-197-source-20260930-r1`

启动前必须：恢复合同明确原run failed/exit137及精确来源、核对模型本体hash/完整性；
新固定SHA远端已保存；训练诊断、selection和primary三入口的terminal模式/Hydra/
CPU回归全部通过。仅新根写入，原源/CP只读；不能通过伪造旧result来满足新入口。
每批需实际load返回、8rank RNG/种子匹配、0更新、8自然局/无截断、消费回答结构语义
全合法、准确容器exit0、guardian completed、result=.done=acceptance及有限指标。
任何失败保留现场、阻断后继；不自动重试、不加局、不扩预算、不启动其他难度。
即使补评测通过，也只能报告“failed-run权重的独立恢复评测”，不抹除旧r2严格训练失败。

## 实现与使用

入口 `spb_l8random_recovery197.py prepare-cpu` 只在宿主执行准备、全文件哈希、
模型ZIP CRC、CPU测试和33个真实dry launcher/Hydra检查，以及7种实际无GPU Ray hook检查。
`queue` 只允许首次单次提交：先真实8GPU映射/NCCL预检，再诊断8局，后selection128、primary128。
全部共享第一GPU派发开始的8小时绝对截止和十根存储计量。所有旧根/CP只读挂载；新根写入。
新恢复合同 `approved-failed-spb-l8-r2-evaluation-only-v1` 登记旧failed身份、26文件×4CP的
SHA256/大小/mtime/inode、旧小凭证hash和CPU取证记录hash。新hash是恢复身份冻结，
没有历史tensor checksum可比，不能宣称证明故障前后tensor逐位相同。每阶段重新检查旧状态、
小凭证hash和全部CP文件身份；实际GPU load返回后才接受可用性。

`terminal-drain-v1` 显式启用于新run：fit返回后锁内发布intent，退出阶段不再暂停冻结；
仍须原15秒测量总时限内实际exit0，guardian完成后才宿主CPU执行原recorder，最后原verifier验收。
CP96诊断必须与自身旧CP2post的8rank seed/CPU/CUDA RNG配对；selection与primary仅各自同批
种子配对，二者不混用。primary固定CP96，不替换为验证集best。验证集best仅报告，不删CP。
运行中任一失败立即阻断后继，无自动修复/重启入口。无checkpoint写入，无训练或CP192。

统计预注册沿用原基准：selection每CP32局胜率，平局较早step；primary报告两个64局胜率、
Wilson95%区间、逐seed配对差值/discordant counts和配对bootstrap95%区间。
这些题已被Qwen使用，不称全新盲测；高合法率/训练曲线不证明学习或架构优势。

本地验证（09月30日，GPU尚未派发）：新增恢复入口15项全部通过；恢复/终态/宿主/存储/
评测/精度合计134项，129通过、5项平台或Torch条件跳过。实际Linux CPU必须零跳过后才派发。
命令：`python3 -m unittest test_spb_l8random_recovery197 test_terminal_storage197
test_host_stage197 test_storage_batch197 test_storage_quiescent197 test_l7_host_continuation197
test_policy_credit_storage197 test_policy_credit_storage_coordination197 test_feedback_eval test_metric_precision -q`
（`PYTHONPATH=<local-testdeps>:tests`，`PYTHONDONTWRITEBYTECODE=1`）。

## 实际启动（9月30日）

- 冻结代码 `d6932869ac75a34d6a244c8879c76ab61982d88a` 已推送既有GitHub分支并核对远端SHA。
  前一9b0f4c4仅暂存bundle，未运行CPU/GPU；部署前将整文件hash改为1MiB流式读取，两个bundle均保留计量。
- 四套CP各26文件（共104）SHA256；每套8个model shard ZIP CRC；40个已取证小状态hash一致。
  不执行pickle，不下载/复制checkpoint；此项不能代替实际GPU load。
- 实际宿主112项+无GPU模型/协议114项，均通过、零跳过；33真实dry launcher/Hydra、37源码hash及7个
  Ray worker hook检查通过。9个CPU容器全部exit0/DeviceRequestsnull，无CUDA初始化。
- 09:11:45单次入队；dispatch.start=`1790730706.6293833`，deadline=`1790759506.6293833`，
  即09:11:46→17:11:46北京，包含GPU preflight/33批评测/加载与45秒收尾，不重设。
- 八张唯一GPU映射与NCCL sums28通过；准确诊断容器
  `0141aeb141a545da48c44c4acc8e44043828f0c732c826aabe727215dbf26d7d`
  于09:12:20实际启动。09:14 manifest clean d693286/world8/binary64/terminal-drain-v1；
  此时尚无load返回/result/.done，不将CPU和映射测试冒充诊断通过。
- 此时严格十根323423069883bytes/352GiB，新两根55167124bytes/32GiB；均return0/空stderr。
- 预计整组约14:15–16:15结束（粗估5–7小时），17:11:46是硬截止，不是保证完成时间。
- 09:16更新：`checkpoint_evaluation.json`证实CP96 model/optimizer实际加载返回step96、
  val_only/0更新、原8诊断seed和T0.8；有界日志已见SC2 in_game。仍无result/.done，终态修复尚待首批验收。

[CPU/完整性凭证](spb-l8random-recovery264-cpu-20260930.json)，
[启动/初始GPU凭证](spb-l8random-recovery264-launch-20260930.json)。

### 首批真实GPU终态通过

09:22:44诊断8局的result/.done/acceptance已一致：CP96实际加载返回，0更新，8自然局5胜，
29/29消费回答合法；原8种子与自身旧CP2post全部8rank CPU/CUDA RNG配对。
准确容器0141aeb1于09:22:28退出0、guardian completed/noOOM；terminal intent发布到退出约7.84秒，
39次此前正常存储暂停中，最后一次早于intent约12秒，intent后无再次暂停。
因此新terminal-drain路径通过**一次真实GPU生命周期验证**，不推断所有cgroup/kernel问题根治。

冻结控制器已自动进入 `sel-b00-cp2`，完整ID
`88853e5960975fccfc6a19005ffff4d56370dac80a30c00c8dab6b32c2a25ebb`。
后续依次CP2/32/64/96各32验证局，再原始/固定CP96各64主评测；没有额外入队、重试或删CP。
运行中以host-supervision的stage/completed为准，root queue.completed仅整组结束时同步。
这8个复用诊断样本不作为学习提升证据，也不把旧r2严格训练失败改写为完成。
[小型终态凭证](spb-l8random-recovery264-diagnostic-20260930.json)。

### 09:55只读进度

已验收4批、32/264自然局、0新增PPO：诊断CP96为5/8；CP2 selection前三批分别
5/8、1/8、6/8，合计12/24（50%，尚非完整32局结果）。最后一批`sel-b03-cp2`
运行中，准确容器03370a3a，无OOM/未暂停；实际CP2加载返回、0更新。
四批result/.done/acceptance一致、guardian completed，逐个准确容器exited0；
108/108消费回答合法、无截断。CP32/64/96 selection及原始模型—固定CP96各64局主评测
尚未验收；诊断8局与selection24局不是同一批seed，不能用62.5%对50%宣称训练提升。

最新严格存储新两根440182045bytes/32GiB、全十根323808084804bytes/352GiB，
两者return0/空stderr，存储暂停后已确认恢复；无已观察到的failure文件。
固定17:11:46北京截止不变；整组14:15–16:15仅粗略预计。
本轮仅小型凭证/准确容器只读检查，未修复、重启、派发或删权重；旧r2严格训练failed不改。
[09:55精简凭证](spb-l8random-recovery264-progress-20260930-0955.json)。

## CP2/32/64/96如何评测；Qwen对应实验（9月30日10:23只读核对）

四个CP是同一条原始SpB→random96训练链的四个快照，不是四次独立训练。
各自累计2/32/64/96次collect-and-PPO、对应16/256/512/768训练局；随后分别
冻结权重、使用同一32个selection场景（4批×8局），共128验证局、0新增更新。
CP2是早期训练模型，不是未训练原始模型。加载native loader会读取Adam状态，
但val_only路径不执行optimizer更新，也不保存新CP。

只读核对新恢复根`cpu/sel-b00-cp{2,32,64,96}/resolved_config.json`，四个真实
dry launcher展开的公共参数相同，checkpoint路径分别指向上述旧r2精确CP：

| 参数 | 四组共同值 |
|---|---|
| 难度/地图/对手 | L8 CheatVision / Flat128 / Terran Air；Base75689、canonical BO |
| 推理采样 | do_sample=true，temperature=0.8，top_p=1，top_k=0 |
| 长度上限 | prompt4096 tokens；response192 tokens |
| 验证分组 | 每批8局，四批共32局；八GPU串行执行各批/各CP |
| 权重及更新 | val_only=true，resume_mode=resume_path，save_freq=-1，0更新 |
| 环境恢复 | sc2_checkpoint_resume=false；新验证环境，不接训练场景计数 |
| 场景seed | 固定selection32清单；非每个CP重新抽题，与训练0..100及primary64分离 |
| 采样RNG | 每批初始Torch seed=rank，8rank CPU/CUDA RNG配对；不是每次调用重置 |
| 执行约束 | 相同canonical/no-thinking动作支持、prompt/观测/Executor；reset concurrency1至首次观察，八局仍并行 |

展开配置也包含继承的LR1e-6、PPO epoch1、mini-batch8、micro-batch/GPU1及
`total_training_steps=192`，它们在val_only路径不执行；**不表示训练到CP192或
评测会更新192步**。cpu配置中的model路径是dry-run metadata占位；实际模型/CP身份
以冻结deployment、manifest和checkpoint_evaluation加载返回为准，不将CPU配置冒充GPU加载。
这四个评测checkpoint的科学变量只是权重快照，运行路径/阶段ID等管理字段相应不同。

用于选best的规则仍为32局胜数最高、同分选较早CP；primary固定原始SpB与CP96各64局，
不以验证best替换CP96，不把诊断8局、selection32和primary64混在一起。
验证集复用已完成Qwen benchmark，不能称SpB设计时从未见过的盲测。

### 对应Qwen已经完成，不是L7结果

原始Qwen3-4B-Instruct-2507→L8 random96 r3于9月28日完成并通过训练、selection
及primary全部验收，runtime `ad81511b270f782420208ac8a6f305a141e8042b`。
96实际PPO、768训练局575胜；其CP2/32/64/96在同一32seed均22/32（68.75%）。
逐局胜负也相同，但决策次数不同；不能推出权重/轨迹完全相同或实现故障已定位。
另64seed终评原始Qwen43/64、same96 35/64、random96 45/64。
random相对原始仅+2胜，预登记探索性配对p=.5，未证实学习收益。
random优于same是在本次benchmark上成立的比较，不升级为跨训练种子普遍结论。

Qwen/SpB对齐任务与主要训练超参：L8、每步8局独立Random(0)从0..100有放回抽seed、
96PPO、T0.8/192/top_p1/top_k0、GiGPO、gamma=lambda=1、combat scale.001、
LR1e-6 constant/零warmup、全参数、PPO epoch1、decision mini-batch8/micro-batch/GPU1。
但模型与架构入口不同（Qwen约4B、SpB约5.17B），参数/FLOPs不相等；本次SpB还有
failed-run恢复评测差异，不宣称只是完全等成本替换或bitwise对照。
对照的Qwen训练、验证、64局结果不是当前SpB结果，不混同两个模型。

### 本轮凭证与范围

只读时间1790735029.5306823（2026-09-30 10:23:49北京）。四个selection b00展开配置
SHA256依CP2/32/64/96顺序：

- `f9c5e5f5196d140fae68c11aae72e7db05e6be4aeefa50ed9203166883c798cf`
- `069048c8e7552ff7810442abead3e42f60acff2a9c24abd28cf918e5a6ad962d`
- `808aa2ce2db3bad198d0f9f94b13cf15326947cc4acfdb3b19dfdb2efe42283f`
- `4445b7743e0267ab593ed8b56e18dbbbdae36151566150fa0f905bbfadc888a4`

SpB r2 short/cpu/train2配置hash `334936c08617e5ec3f4d405942634c47ddae15f84830ccb4d01350041b797ef1`；
Qwen r3对应配置hash `7e6a64fca4e509df68ffcfcccf9bb7f4659988d9dabf22c79676cac8d486f36e`。
仅投影相关参数，不导出完整环境变量。此刻host状态显示8批完成、`sel-b03-cp32`
运行中；本轮未逐批重验新增结果，因此不新增SpB胜率结论。旧r2failed不改。
未修改服务器/重启/追加实验/读取权重/删除，也没有更新语雀。

历史Qwen依据：[训练曲线口径](qwen-l8random-r3-curves-20260928.md)、
[完成凭证](qwen-l8random-r3-paired-complete-20260928-1936.json)、
[配对统计](qwen-l8random-paired-statistics-20260928.json)。后两文件SHA256分别为
`5e1be628979c0cb75bbf631a2e769640e5e5f57e29807a0cdbb89a0219923679`及
`94be075402a18fc1fbbe84316359994815f1bd386d28bd4f48544f69288f09a9`。

## 9月30日10:38进度与剩余耗时

只读小型终态与准确当前容器：10批/80自然局通过现有验收，0新PPO；
各批result=.done=acceptance.result，guardian completed、准确归属/原截止一致、
final_state exited0/noOOM。279/279消费回答合法，无截断/非有限指标。
当前`sel-b01-cp64`容器`c0fe45c9fcadaa325b428037e1345b49c566da3fcc82dcf359eba8cab25f90b5`
running/unpaused/noOOM。未读取完整日志、模型权重或重复执行全量verifier。

已完成selection CP2=16/32、CP32=25/32；CP64仅第一批5/8，不能与完整32局比较。
CP96 selection及原始/固定CP96各64局primary尚未完成。当前改善是验证集的中间
观察，不选后验最佳CP替换固定CP96，也不据此宣称最终学习收益或架构优势。

新两根761785812bytes/32GiB、全部十根324129688571bytes/352GiB，
严格计量return0/空stderr、暂停后verified-unpaused，无已观察failure。
前10批含首次dispatch与阶段间隔平均8.5164分钟、中位8.034分钟；仍剩23批，
含正在运行的一批。简单线性外推约13:52:49；考虑后续原始模型及场景耗时差异，
更新保守预计为**9月30日14:00–15:30北京**。不是保证；硬截止仍**17:11:46.629**。
旧训练r2严格failed/exit137保留；本次恢复评测不能补造旧训练终态。
[完整小凭证投影及hash](spb-l8random-recovery264-progress-20260930-1038.json)。

<a id="next-spb-l8-same"></a>
## 下一优先组提案：fresh SpB L8 same96（预算待确认，未入队）

**已被本轮后续用户指示取代，不执行**：“下一组先跑l9的random seed，same seed先不跑”。
下列same预算仅保存提案历史，从未批准、prepare或queue；最新见文末L9优先级。

用户本轮要求“再排一点新实验”。本段将后续优先级与预算落档，但该要求不替代
新高成本多卡预算确认；没有prepare、queue、GPU派发、服务器修改或自动后继。
仅在用户明确批准本段预算、当前recovery264全部验收且197资源准入通过后，
才能用新冻结SHA/唯一RUN_ID单次启动。若前序失败，先交接，不绕过或自动重试。

### 问题与控制变量

当前Qwen L8 same/random均有结果，SpB L8有random训练产物及正在进行的恢复评测，
**尚缺SpB L8 same的96-step RL对照**（既有SpB same是L7，不代替L8）。
因此建议先补齐此格，检验SpB的step内seed分组是否影响固定CP96表现，
不直接从random CP96接CP192或跳到其他level。

从原始约5.17B `Panyuqi/SpikingBrain-2.0-instruct`独立开始，绝不加载已有trained CP。
模型revision/路径、任务协议沿用[原SpB L8方案](spb-l8random96-proposal-20260928.md)。
计划唯一科学变量：训练由每步独立抽8个seed改为私有Random(0)每步从0..100
有放回抽1值复制给8局，即same_uniform101；96步逐项核验。不是固定一个seed跑全程。
仍为L8 CheatVision/Flat128/Base75689/Terran Air/canonical BO、data/train.parquet
在线任务入口、T0.8/response192/top-p1/top-k0、gamma=lambda1、combat.001、
LR1e-6 constant/零warmup、全参数GiGPO、PPO epoch1/decision mini-batch8/
每GPU micro-batch1；canonical/no-thinking、post-centering invalid penalty.1、
消费合法率.5更新门槛，验收仍100%合法。reset concurrency1至首次观察，8局并行，
每次reset只尝试1次，无D+/重采/early-stop。

新运行将需要terminal-drain修复在训练入口的CPU/真实短阶段验证。它相对旧random
失败运行存在基础设施收尾实现差异，必须在effective config/provenance中另列；
不能声称bitwise、完全只有logger/seed变化。既有random来源failed的限制继续披露。

### 拟新增预算（不是既有预算的扩大）

| 组件 | 新自然局 | 新PPO | 硬上限 |
|---|---:|---:|---|
| pre8→fresh train2→post8→own native CP2续至96→eval8 | 792 | 96 | 与selection共用24h/192GPUh、320GiB |
| CP2/32/64/96各相同selection32 | 128 | 0 | 上述24h内，selection另限6h/48GPUh、8GiB子上限 |
| 固定same CP96在相同primary64上评测 | 64 | 0 | 首次primary起6h/48GPUh、32GiB，且不得越过suite截止 |
| 总计 | **984** | **96** | **30h/240GPUh，新增352GiB** |

197八卡串行；96PPO=768训练局，另216评测局。预计约12–16小时，依据上次SpB
训练约8–9小时、目前评测每8局约8.5分钟外推，再留加载/验收余量；不是保证。
GPU预检、加载、保存、间隔、验收与45秒收尾均计入，首GPU操作固定24h/30h
绝对截止，切阶段不重设。当前recovery的截止和十根352GiB账本完全不改。
新训练/selection、primary、source-parent三个整根另计新增352GiB，含bundle、
CPU准备残件、tmp；精确路径/唯一RUN_ID/冻结SHA在批准后的启动记录登记，
正式启动前必须核验路径不存在，不能把本提案当作已部署配置。

仅稀疏保存完整native **CP2/32/64/96**，每套约59.20GiB，峰值约236.82GiB；
本申请保留四套，不删除旧或新权重，best仅写同目录小清单引用，不复制模型。
这不是逐步滑动删除，也不每8步存13套；若后续希望删非best CP，另核对精确范围。
新训练准入：8卡全空无compute PID/归属确认、RAM≥600GiB、空闲NVMe≥416GiB；
评测空闲NVMe≥128GiB、fsync/readback，均启动前重测。历史磁盘快照不当预留。
严格整根GNUdu无重试/排除/过滤/旧值回退，未知不当0；禁止清理来强行满足准入。

### 评测与验收

复用本恢复组的selection32和primary64固定清单及同rank CPU/CUDA RNG初始化；
已验收的原始SpB和random CP96 primary64直接复用，不重跑这128局。
selection32只选best、平局较早CP；主终评始终固定same CP96，不换成best。
预登记主对比same96−random96，次对比same96−原始；同64seed配对胜负、
gain/loss、胜率差、exact two-sided McNemar、100000次配对bootstrap95%CI
（PCG64=2026092801，linear分位数）及各臂Wilson95%CI；次对比标探索性。
此benchmark已被Qwen/SpB使用，不叫全新盲测；单个训练随机流、不同架构参数量
与FLOPs、旧random失败恢复来源均保留，不据单条训练曲线宣称学习/架构优势。

新组必须先通过全部CPU/实际launcher/Hydra/Ray hook/源码hash与干净远端SHA；
短pre/train2/post真实通过、自身完整CP2 driver/rank RNG/sc2_state/native恢复和
parent-readiness通过后才进长段。每阶段result=.done=acceptance、host/guardian/
准确owner容器exit0、world8/binary64/有限指标/无截断；96实际returned PPO+
96审计、有限正梯度/正update_actor/invalidAdv非正、完整seed与合法消费执行链。
四套CP各26必要文件及实际load返回，评测0更新和逐seed/rank RNG配对。
原始baseline复用也必须依当前恢复的已接受凭证；任何失败阻断后继，不自动修复、
重试、加局、CP192、其他level或旧产物删除。技术通过与学习收益分开报告。

本轮仅进度凭证和待批预算文档，无训练代码实现。实际本地`python3`小凭证校验
通过：10批终态/guardian身份与截止、80局/279合法回答、存储上限、CP2/32汇总及
984局/30h×8卡/352GiB预算算术；`git diff --check`通过。未宣称新组CPU/GPU已验证。

<a id="next-l9-random"></a>
## 最新指示：下一组SpB L9 random，same暂不跑

用户在本轮结束前明确调整优先级，并在模型澄清中选择“SpB（沿用当前模型）”。
当前L8 recovery264继续，任何已启动阶段不动；没有same任务被创建或入队，
所以计划调整不涉及停止进程。模型及优先级确认后，用户明确回复“批准”，
以下新预算及fresh起点方案已获授权；实际部署/派发仍须下面的门槛与凭证：

- 建议从原始SpB独立训练L9=`CheatMoney`，不从L8 CP96迁移；原始模型revision
  和只读资产身份沿用前述SpB来源。难度映射依据既有
  `qwen-l9-l10-rl-budget-20260927.md`及实际difficulty适配器。
- 96次在线collect-and-PPO/768训练局；每step8局各自独立抽seed，私有Random0
  从0..100有放回，非same分组。其余任务/优化器/生成协议与SpB L8 random对齐；
  实际冻结配置需另核验，不能用当前Git源码代替旧运行provenance。
- pre/post/eval共24诊断局；CP2/32/64/96各32selection，共128局；原始与固定CP96
  各64个相同L9场景终评，共128局。合计**1048新局/96PPO**。L8相同数字seed的
  结果不能当L9原始baseline复用；不据训练曲线或8局诊断单独判学习收益。
- 预算：197八卡串行，训练+selection24h/192GPUh（selection组件另限6h/48GPUh），
  全组从首次GPU操作固定**30h/240GPUh/新增352GiB**（训练+selection320GiB，
  primary32GiB；selection子目录另限8GiB）。含预检/加载/间隔/CP/45秒收尾，
  primary另受首次该阶段GPU起6h与suite截止较早者约束，切阶段不重设。
  粗估**14–20小时**，L9尚无本模型random实测速度，不保证完成时间。
- CP2/32/64/96四套完整native，按SpB单套59.20GiB峰值236.82GiB估算；保留四套，
  best仅引用，不自动删权重。这是稀疏保存，而非逐步滑动删除。
  训练准入NVMe416GiB、评测128GiB、RAM600GiB、全8卡空闲无compute PID及fsync；
  全部启动前重测，不修改旧队列/旧预算。新source-parent、训练/selection、primary
  三个整根含bundle/CPU/tmp全部计量，新唯一RUN_ID和路径在批准后确定并核验不存在。
  严格du无重试/过滤/排除/旧值回退，未知不当0；旧十根352GiB账本原样保留。
- 当前恢复全链验收后才可接续；本轮新GPU预算已明确确认。CPU/真实launcher/
  Hydra/Ray hook/干净远端SHA、短三阶段与自身nativeCP2门槛、96 returned PPO/
  审计/seed/合法执行链、完整CP及0更新配对评测、终态exit0一致等门槛不放宽。
  新terminal-drain修复必须在训练入口验证，失败run及基础设施差异不抹除。
- 主比较固定CP96−原始SpB，同L9 seed/rank CPU-CUDA RNG配对，沿用上述
  Wilson/paired bootstrap/exact McNemar方案；selection只选best，不换主比较权重。
  训练0..100、selection32、primary64互不重叠，清单在启动前冻结，不能按结果换题。
  同数字seed不同level的成绩不合并；一次训练随机流不证明架构优势。
  不自动接same、L10、CP192，不重试、不删产物、不抢占当前任务；任何失败先交接。

本轮最终仅更新只读进度和待确认计划，没有新CPU/GPU派发，也未改变运行中的deployment。

<a id="l9-approved-launch"></a>
## L9 random批准后的实现与单次准备（2026-09-30）

上一句是提案轮的历史状态。本轮用户批准后开始实现，状态`planned`，不把代码
准备等同于GPU运行。复用原record及当前`codex/fix-terminal-storage-handoff`工作树，
推送到既有远端`codex/fix-sc2-startup-port-race`，不另建实验分支或改变冻结前序。

唯一RUN_ID `sc2-spb-l9random96-197-20260930-r1`，三个新根：

- train/selection：`/var/jfsCache/sc2-spb-l9random96-197-20260930-r1`
- primary：`/var/jfsCache/sc2-spb-l9random-paired128-197-20260930-r1`
- source-parent：`/var/jfsCache/sc2-spb-l9random96-197-source-20260930-r1`，源码在`code`。

10:50只读确认三根不存在；11:04当前前序host已完成12批/96局，正在`sel-b03-cp64`，
没有停止或修改它；NVMe空闲800632496128bytes（时间敏感快照，正式准入重新测）。
前序为冻结`d6932869ac75a34d6a244c8879c76ab61982d88a`的L8 recovery264，
固定截止1790759506.6293833。全33批小终态/result=.done=acceptance/exit0、准确容器与
guardian身份/截止、原始或指定CP加载、natural8及8rank seed/CPU-CUDA RNG配对均通过后
才能放行；任一失败阻断新L9，绝不把failed旧r2训练追认为completed。

新入口（均在本record）：

- `spb_l9random_prepare197.py`：仅宿主、单次无GPU准备；失败保留新根，禁止自动重试。
- `spb_l9random197.py queue`：CPU门槛全部通过后只入队一次，等待前序，不占GPU。
- `spb_l9random197.py`：五阶段训练链，L9=`CheatMoney`，只接自身native CP2。
- `spb_l9random_eval197.py`及`spb_l9random_eval_hook.py`：validation128与primary128。
- `spb_l9random_plan.py`：冻结路径、seed清单/摘要、顺序、CP和分析随机种子。

首次GPU之前核对八卡空闲/RAM/NVMe/fsync，并做八rank唯一CUDA映射/NCCL探针，
探针计入首个24h/30h绝对时钟。前序截止前未通过则失败；通过后资源等待最多4h，
等待不占GPU；阶段内部不刷新train/suite截止。模型、SC2、依赖均只读；仅新owner/tmp/
稳定storage锁可写。三个新根完整计量，旧十根预算不变。实际运行SHA在CPU/queue凭证记录。

训练scientific协议沿用原始SpB L8 random：每step8局私有Random0在0..100有放回独立抽取，
global1..96共768局；L9 Flat128/Base75689/Terran Air/canonicalBO；temperature.8、
max192、top-p1/top-k0、gamma1、combat.001、LR1e-6 constant/zero-warmup；canonical/no-thinking
同support、post-centering invalid credit、.5消费合法率PPO门槛；原始模型5.17B，
revision `sha256:de52e8ef993afc763f9d4fb498e8d8302ef0bc13bd7dfd53c6ae5f77f43698b5`。
原始模型路径与元数据身份使用accepted L7 SpB frozen83f3530模板，基准resolved-config
SHA256 `fe0e3c00571eabc7e625ea192b55f6e360d5a6cb3d53c602085a81bada1fed5b`；
规范化配置只允许难度/低端口/存档/收尾与路径预算控制项改变，其余漂移直接失败。
实际五启动器和32评测启动器各保存effective/resolved config及源码34项hash检查。

复用已有收尾修复`terminal-drain-v1`，新训练与评测均显式选择；旧L8默认入口行为不变。
实际任务返回只发布未验收intent，不伪造result；host等准确容器exit0后由冻结recorder
出result，再原严格verifier验收。收尾等待与du共用原15秒测量预算，不重试/回退/跳过。
这项运行时差异必须报告，不称与旧L8只改变难度或bitwise等价。

checkpoint使用完整native CP2/32/64/96（含driver/rank RNG与sc2_state），单套预计59.20GiB，
四套约236.82GiB；本组禁用prune。best只写小JSON引用，验证32只选best，主终评仍固定CP96。
短三阶段实际通过、accepted-spb-l9-random-full-state-prefix-v1合同及parent-readiness后才长训。
96 actual returned PPO/96审计/96种子、正有限梯度/update_actor时间、invalidAdv非正、
全部消费回答结构语义合法、自然局无截断、26必要文件/CP与全阶段终态才算训练验收。
主效应与统计方法沿用上文，不使用训练胜率或8局诊断替代同seed固定权重的配对比较。

本地检查命令（尚不代替Linux CPU门槛）：
`PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/private/tmp/sc2-spb-l8-testdeps.nzp1NX:tests:. <bundled-python> -m unittest test_spb_l9random197 test_spb_l8random197 test_qwen_l8random197 test_qwen_l8random_retention test_terminal_storage197 test_sc2_policy_resume test_sc2_checkpoint_resume`
实际134项，130通过，4项因本地无Torch跳过。真实Linux必须零跳过且noCUDA，另实际三种
terminal exit0/exit7/hang无GPU容器、host生命周期/批量计量、9类Ray worker hook全部通过。
没有实际Linux结果前不得queue；没有GPU/SC2/returned PPO凭证前不得声称训练已开始。

扩大到模型/宿主全部23个模块的本地尝试共283项，出现6项环境错误（4个模块缺Torch、
2项沙箱禁止本地socket绑定）与8项跳过，**未通过完整门槛**；不能把本地subset通过
写成全部通过。正式准备仍须在固定Linux无GPU环境实际执行两套完整回归、零错误零跳过。
