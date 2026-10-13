# L9 验收修复与 L10 受控接续（r2/r3）

最新状态（9月27日22:20:19北京）：**r3已单次启动，L9终评通过，L10正在pre**。
L9仅新增8局、0更新，22:18:59完成；L10首次GPU派发22:19:00，pre容器22:19:34启动。
修复整组与阶段入场凭证名冲突，保留r1/r2，不增加局数、预算或截止。
下文r2方案与失败历史原样保留；r3的差异、实际启动与验收见末尾。

状态：**r2 failed，尚未启动终评或L10**。用户9月27日明确回复“允许”，
批准修复验收、原预算内接续L9终评与L10，**不重跑已完成的96步**。
21:40:02单次入队后，保留训练验收和GPU预检通过；21:40:38因交接入口
重复fsync文件名失败，0新增局/0新增PPO。下文原方案保留，末尾为终态交接。

## 范围与不可改变的边界

- 保留L9 r1：pre8、train2共16、post8、long752，合计784自然局/96PPO。
  old queue/host `failed`以及旧result原样保留，不改成成功。
- 新L9 r2只跑自身CP96最后8局、0更新；与旧ownCP2post原八seed/全rank RNG配对。
- L9完整保留验收+新eval验收后，新L10 r2从**原始Qwen**起训：
  pre8→train2(16)→ownCP2post8→native3..96(752)→ownCP96eval8，共792局/96PPO。
  不是L9权重迁移、不是L8 CP192起训；same_uniform101、L10 CheatInsane及其余协议不变。
- 新增只有800局/96PPO，加保留784局/96PPO，仍是原套件1584局/192PPO。
- L9固定start1790482308.224269、deadline1790525508.224269
  （9月28日00:11:48北京）；套件固定deadline1790568708.224269（12:11:48）。
  不重设。L10首次GPU预检才开始自己的12h，且受套件截止截断；45秒收尾。
- 各级96GPUh/256GiB、整组192GPUh/512GiB均不增加；新旧产物一起计量。
  不删除、不停止他人、不自动重试，不接其他组。

21:14只读健康：197八卡0MiB/0%/无computePID，旧准确tmux已结束；
可用RAM815528284160bytes、磁盘796961521664bytes。旧常驻容器未动。
每阶段仍重新门控：八卡全空/600GiB RAM/fsync-readback；eval128GiB空闲，
train/preflight320GiB。此次不是从头申请整组，已有L9权重占用继续计入，
不把旧576GiB首套件入场检查重新当作新预算。

## 根目录、冻结与只读继承

新RUN_ID：`sc2-qwen-l9same96-197-20260927-r2`、
`sc2-qwen-l10same96-197-20260927-r2`，均位于`/var/jfsCache/`。
新source-parent：`/var/jfsCache/sc2-qwen-l9l10same96-197-source-20260927-r2`，代码`code`。
保留对应r1的两个output和一个source-parent，**六个完整根合计512GiB**。
每级该级r1+r2 output加两个共享source-parent共四根≤256GiB；shared source保守双计。
不过滤、排除、重试或回退旧计量值。source/bundle/CPU残件均包含。

模型/训练runtime仍只读`1c6cf60b111570ef13f9817d0b1b16fb774546f5`，
新controller从本分支`ba1da8c`继续，只修验收和新增薄交接入口，不改PPO/模型源码。
新runtime是指向各自旧冻结runtime的只读链接。L9旧四个run及CPU配置只读继承；
只在新L9 long写eval96，不在旧路径写acceptance、deployment、state或日志。
各容器仅准确新part/tmp/新L9稳定storage锁可写；全部旧三根额外只读挂载。

## 修复与门槛

`qwen_l9l10_same197.checkpoint_inventory`不再假设result包含全部中间CP。
它要求最终CP清单完整，拒绝额外checkpoint/结果键，逐项检查全部26必要文件，
已登记尺寸必须匹配；中间model/optim分片尺寸须与最终同rank同类型一致。
小状态独立记录SHA256，大权重只stat，不伪造原result条目。

新`qwen_l9l10_continue197.py`还在无GPU容器逐套检查CP32/64/96小native状态：
globalstep、driver Python/NumPy/Torch RNG、每rank CPU/CUDA RNG及scheduler步数、
训练环境reset位置和dataloader；从不反序列化model/Adam大分片。
保留L9的四个原容器/guardian必须准确owner、原截止、completed/exit0；oldfailed错误
必须恰为本次CP32键错误，eval没有发生，L10从未dispatch，否则拒绝交接。
修复后的完整四阶段verifier以write=False运行一次，含原有真实PPO/审计/seed/合法性/
replay/加载门槛；保留验收只写新root，不能把历史failed覆盖。
新L10每次train96完成后也先做同一native CPU检查，再做完整验收；失败阻断终评。

## CPU与启动顺序

1. 本地回归；干净controller commit推送既有分支并独立核验SHA。
2. 新source/output准备一次；实际197 host回归与无GPU模型/控制器回归（零跳过）。
3. 四个part的实际launcher/Hydra/源码校验，其中L9短段没有新阶段。
   L9 eval96、L10 pre/train2/train96四个真实无GPU Ray hook；旧训练不执行。
4. 无GPU检查L9三个CP native小状态；host完整保留验收。
5. 新tmux单次queue：L9 eval环境八UUID/NCCL零游戏预检→L9 eval8；
   全部通过后L10预检→原始pre→train2→post→ownnativeCP2 long→eval96。
   新任一失败不自动重启/派发，保留交接。

本地实际测试：`PYTHONPATH=/private/tmp/sc2-qwen-native-testdeps-20260924:tests:.`
配合bundled Python `-B -m unittest test_qwen_l9l10_same197 test_qwen_l9l10_continue197 test_host_stage197 -q`，
72项通过、0跳过。覆盖实际final-only结果清单、缺字段/错分片/缺native状态/错seed/
零梯度、旧截止、六根计量、只读挂载、禁止L9重训、失败阻断L10、禁止重复queue。
CPU测试不替代GPU/SC2/PPO，实际CPU和派发凭证另附。
追加本地兼容回归：同命令加入`test_qwen_l8same_continue197`、
`test_qwen_l7same_fresh197`、`test_sc2_policy_resume`，108项通过、0跳过。

入口：`qwen_l9l10_continue197.py prepare|host-regressions|queue|verify-retained`；
命令生成器`cpu-command LEVEL INDEX`、`regressions-command 9 0`、
`cpu-hook-command LEVEL INDEX STAGE`、`retained-cpu-command 9 1`。
所有正式阶段仍使用冻结源码、独立准确container和host guardian。

## r2 terminal failure September27 21:40:38 Beijing

冻结controller为`5261ff5d6fee665fec78a97de4c5bfd9a79b4fc5`，启动前已push既有
`codex/fix-sc2-startup-port-race`并通过`git ls-remote`独立核验。模型runtime未变。
实际197 host71项、模型/控制器231项（含continuation19项）零跳过；四part共六个新阶段
实际launcher/Hydra配置、34源码哈希、四真实无GPU Ray hook均通过。十个准确CPU容器
均exited0/DeviceRequests=null，无CUDA初始化；CP32/64/96的driver RNG、八rank RNG、
scheduler/global/reset位置和78个必要文件独立清单通过。[小CPU凭证](qwen-l9-l10-r2-cpu-20260927.json)。

21:40:02仅入队一次，socket`sc2_qwen_l9l10same96_197_20260927_r2`，
session`qwen_l9l10same96_197_r2`。21:40:04四阶段完整保留verifier以write=False通过，
新root保存`retained-acceptance.json`：784自然局/96真实PPO；旧r1的failed状态未改。
这修正了原CP32清单KeyError造成的验收阻断，但**不等于L9最终终评完成**。

L9 eval环境八GPU预检容器
`4ef0996c8aee36a782df0003218ae573dec3e137b3c64007e2b5989d4c8e23f1`
于21:40:05开始、21:40:30 exited0/noOOM；八个不同CUDA UUID、NCCL和为28。
模型未加载、0游戏/0更新。host预检completed/exit0，随后正式阶段入场在21:40:38失败。

直接原因：新queue先以`eval96`调用arm入场，已创建`fsync-eval96`；预检结束后
host supervisor逐阶段又以`eval96`入场，`open('xb')`拒绝同名文件。
因此尚未到docker create，L9 eval目录、entry日志、准确eval容器均不存在，L10无dispatch。
这不是GPU故障、SC2故障、OOM或策略失败，是本轮新交接代码的命名错误。
原有queue单测mock了`m.admit`，未覆盖真实fsync与调度顺序，是测试缺口。

本地最小复现实际调用`m.admit`，仅mock资源/计量/归属外部边界：
`eval96 → gpu-preflight → eval96`，第二个eval96确实抛FileExistsError。
复现仅临时目录、0服务器操作；没有修改或重复启动r2。
后续修复必须区分arm与stage的入场凭证名，并用真实admission顺序回归；不能改为
覆盖旧凭证、删除冲突文件后重跑或跳过每阶段资源门槛。

21:44:55只读确认八卡0MiB/0%/无computePID，新tmux已退出；旧常驻任务未动。
六根严格GNUdu最新201989208291bytes/512GiB，return0、stderr空，不回退旧值。
详见[失败及GPU释放凭证](qwen-l9-l10-r2-failure-20260927.json)。

本次0新增自然局/0新增PPO，GPU预检耗时仍属于原预算；原L9截止9月28日00:11:48、
套件截止12:11:48不延长，所有r1/r2产物保留且继续计量。未自动修复重试。
下一次如获授权，须新冻结提交、新RUN_ID并将新旧全部根合并计量，仍只补L9终评8局、
通过后L10 fresh792局/96PPO；不重训L9，不增加对局或预算，不接其他实验。

## r3 authorized admission repair

用户已明确批准新r3单次接续。代码从记录提交`9ad6836`继续，模型runtime仍为
`1c6cf60b111570ef13f9817d0b1b16fb774546f5`，训练/评测/seed/保存频率完全不变。
只修改controller：`admit`的资源检查仍按实际stage执行，增加独立`receipt_name`，
整组初入场使用`arm`、GPU预检使用`gpu-preflight`、正式阶段使用本stage名称。
仍使用exclusive创建与真实fsync/readback，重复同一stage照样拒绝；不删除旧探针。
L9整组初入场仍按eval128GiB门槛，不能因更名误切换为训练320GiB或绕过资源检查。

新output：`/var/jfsCache/sc2-qwen-l9same96-197-20260927-r3`、
`/var/jfsCache/sc2-qwen-l10same96-197-20260927-r3`；共享source-parent
`/var/jfsCache/sc2-qwen-l9l10same96-197-source-20260927-r3`，代码子目录`code`。
r1/r2/r3共**九个完整根≤512GiB**；每级三个output与三个共享source共六根≤256GiB。
全部r1/r2根额外只读挂载，旧权重、runtime、记录和失败状态不改动；新路径不存在才创建。
沿用原L9截止9月28日00:11:48、suite截止12:11:48，45秒收尾；L10自身仍至多12h且
不能超过suite。L9只补8局零更新；L10通过全部前序后才fresh792局/96PPO。

r3前序还必须是准确r2的`FileExistsError: fsync-eval96`，queue/host无completed阶段、
无eval run/entry、L10无dispatch；正确原deadline及准确GPU预检container/guardian exited0。
冻结r2 retained-acceptance的SHA256必须匹配已记录凭证，r2源码clean5261ff5；
任何不同状态拒绝接续。然后再进行原r1完整保留验收与native小状态检查，不伪造旧成功。

21:54:41只读健康：197八卡0MiB/0%/无computePID，旧四个常驻容器未动，
RAM815628681216bytes可用、磁盘796931207168bytes空闲；三个r3根均不存在。
时间敏感快照不替代逐阶段入场门控。

本地先运行新`test_real_admission_full_queue_order_uses_unique_receipts`，在旧代码上
准确复现FileExistsError（red）；修复后连同兼容测试**112项通过/0跳过**（green）。
命令为bundled Python，`PYTHONPATH=/private/tmp/sc2-qwen-native-testdeps-20260924:tests:.`
与`-B -m unittest test_qwen_l9l10_same197 test_qwen_l9l10_continue197 test_host_stage197
test_qwen_l8same_continue197 test_qwen_l7same_fresh197 test_sc2_policy_resume -q`。
新测试实际执行完整queue的admission/fsync/readback顺序，仅mock外部资源与Docker边界；
同时验证重复stage拒绝覆盖、精确r2失败门控、活跃旧预检/已有L10派发拒绝，以及九根计量。
这仍是CPU测试，不替代服务器实际入口、GPU或游戏证据。运行前须再次完成实际host回归、
无GPU模型/控制器回归、六启动器/四Ray hook/三CP小native检查；通过后才单次queue。

## r3 actual launch and L9 completion

冻结controller`5152bbb74def8d0bd54d172c70bf18dfa2fed90a`已推送既有分支，
部署前独立`git ls-remote`核验准确SHA；模型/训练runtime仍为`1c6cf60`，没有改训练协议。
实际197 host71项、模型/控制器235项、零跳过/无CUDA；四part/六真实launcher和Hydra/
34源码哈希、四真实无GPU Ray hook、CP32/64/96 native小状态与78必要文件均通过。
十个准确CPU容器exited0/DeviceRequests=null。本地112项回归记录在
[CPU凭证](qwen-l9-l10-r3-cpu-20260927.json)，不能当PPO或策略学习证据。

22:11:22.318仅入队一次，socket`sc2_qwen_l9l10same96_197_20260927_r3`，
session`qwen_l9l10same96_197_r3`。新保留验收SHA256为
`c9f8fca36270b9ed81215593bbc54adcfade5012da72d7402a85c4a111c85426`，
确认原L9四阶段784自然局/96真实PPO；原r1/r2 failed状态原样保留。
整组`arm`与正式`eval96`两套独立admission均通过，都是八空卡/600GiB RAM/
128GiB磁盘/fsync门槛。L9八UUID/NCCL预检exited0，0局/0更新。

L9准确终评容器`db89a044643fb16eef47d1e7d0fd078be7674b55747320c87893b3e415019eeb`
于22:11:58.832启动，22:18:58.704 exited0/noOOM；host/guardian/arm completed/exit0。
自身CP96实际load返回，**8自然局3胜、145/145实际消费回答合法、0更新、无截断**；
result=.done=acceptance，binary64-v1有限指标，八rank原评测seed与CPU-CUDA RNG均与
ownCP2post配对。控制器在22:18:59.756完成L9 arm，然后自动进入L10。
L9训练总计297/768胜；复用8seed诊断pre7/8→CP2post5/8→CP96 3/8，没有学习提升证据。
终评37.5%的描述性Wilson95%区间约13.7%–69.4%，不替代配对效应检验或泛化估计。
仅八个复用样本不能据此断言普遍退化或架构结论；合法性/梯度/技术验收不替代学习评估。

L10于**22:19:00.308首次GPU派发**，start`1790518740.3084953`，固定自身截止
`1790561940.3084953`（9月28日10:19:00.308北京），仍受原suite截止12:11:48约束。
L10 GPU预检容器`e7af4072b905f1f66d8c251fb7b8d8f13285be4d159b8953e9bbaecbfdceb129`
exited0；随后short/pre准确容器
`81f569504ced33a87902f6a5a455f27060690404f4fc90be6cdc8709bb88446b`
于22:19:34.213启动，22:20:19实查running/unpaused/noOOM。
目前仅pre8零更新，**尚不声称L10已返回PPO**。同一冻结队列中后续是fresh train2→
ownCP2post→ownnativeCP2 train3..96→ownCP96eval，不需要另派任务；任一失败阻断后继。
原始Qwen3-4B、CheatInsane、same_uniform101、96在线PPO/768训练+24评测局不变，
并非L9/L8权重迁移，也不是离线大数据集96epoch。

22:20最新九个完整根严格GNUdu为202044805211bytes（约188.17GiB）/512GiB，
return0、stderr空；不排除r1/r2/source/CPU残件，不回退旧计量值。
原L9截止、suite截止、各级96GPUh/256GiB与suite192GPUh/512GiB、45秒收尾均未增加。
不删除、不重训L9、不重复入队、不自动重试，旧常驻服务未动。
具体小状态、精确容器、原截止、加载、result、RNG配对与计量见
[r3启动和L9完成凭证](qwen-l9-l10-r3-launch-20260927.json)。
