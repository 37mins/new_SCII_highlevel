# SpB L8 random：用户要求重启后的只读核对与预算边界

最新状态覆盖下方启动记录：r2已在9月29日18:53:19因收尾暂停失败而failed。
9月29日晚仅开发[默认关闭的终态交接修复](spb-l8random-terminal-repair-20260929.md)，
没有重启r2、没有新的GPU实验、未改写失败状态。以下10:13启动状态保留为历史。

最新状态：**r2已单次派发，short/pre运行中**，2026-09-29 10:13:50北京核验。
运行冻结SHA`12f3600ca8e6e8edabc460de70860baeef2b5146`在服务器准备前已push并核验。
host79/model195项Linux CPU回归零跳过；五种CPU生命周期/故障注入与一次暂停四账户
真实文件写入试验通过；五训练+16验证+16主终评启动器、九worker hook全部通过。
单次queue10:11:02，首次GPU10:11:03.278；八GPU唯一映射/NCCL通过；准确pre容器
10:11:36启动，实际SC2 in_game已观察。尚无pre result/.done或返回PPO。
新训练/选优固定截止9月30日10:11:03.278，suite截止9月30日16:11:03.278北京。
GPU容器实际一次pause→四账户du→unpause成功；六根64540698052bytes/352GiB。
这不保证底层cgroup冻结永不再失败；失败仍阻断后继，不自动重试。
[CPU实际凭证](spb-l8random-r2-cpu-20260929.json)和
[单次启动凭证](spb-l8random-r2-launch-20260929.json)为最新权威状态。

以下09:52核对与提案保留为历史，不再表示正在等待本次授权。

状态：`restart-requested / awaiting-renewed-budget`。2026-09-29 09:50–09:52北京。
用户要求“那你快重启实验啊”，已明确要求修复并受控重启；这不自动延长原绝对
截止或抹除已消耗的对局。本轮尚未修改运行代码、创建服务器目录/容器、入队或派发GPU。

更新：用户随后明确回复“允许”，确认本文件的一次r2新增1048局/96PPO、
30h/240GPUh新时钟与旧新六根合计352GiB。状态转为`approved / CPU-preparation-pending`。
具体实际准备与派发只能由后续CPU/launch凭证证明；以上09:52是历史只读快照。

## 本次修复与风险边界

09:55只读Docker daemon日志确认原始错误：
`OCI runtime pause failed: timeout of 10s reached waiting for the cgroup to freeze`。
所以不是仅客户端等待或存储空间不足。cgroup中具体哪个任务阻碍冻结未被原凭证捕获，
不能宣称唯一底层原因已根治。

开发隔离分支`codex/fix-guardian-batch-sampling`，起点
`4436fd113ba34c9689655281ebb95eefd302f5cb`；原experiment record及冻结r1不变。
代码验证后整合并推送约定`codex/fix-sc2-startup-port-race`，不把新分支当新实验。

修复guardian收到pause失败却继续发resume、覆盖首个异常的问题，并在收尾前立即
向宿主返回首错，终态保存失败操作、Docker错误与实际观测state。
新增仅SpB r2显式启用的`storage_batch197.sample`：先取得元数据锁，再一次冻结，
依次执行原四账户的精确GNUdu，全部通过并恢复后才发布成功。整个批次共用原15秒
上限（比原来每账户单独15秒更严格）；无重试、过滤、排除、旧值回退或限额放宽。
旧默认采样入口不变。这减少每轮4次冻结为1次，是有界风险缓解，不保证底层冻结
再不超时；再次超时仍按原规则停止本组，不吞错继续训练。

必须在新根实际跑通：host回归、五场景CPU生命周期/故障注入、四账户独立文件写入
CPU容器试验，以及全部模型/启动器/worker-hook CPU门槛。CPU不替代GPU证明。
训练/种子/奖励/动作/checkpoint内容不改；暂停频次改变属于运行控制差异，
不声称与r1的墙钟时序或训练轨迹bitwise等价。

## 当前事实

- 197八卡显存0MiB、利用率0%，compute-apps为空。四个历史服务容器仍运行，未触碰。
- 原r1 queue与`spb-random/short/host-supervision/state.json`仍failed；completed只有pre。
  精确train2容器`4775300d3d2d3a66f671bf78e80b7d4784b20ab9cf1ed812dbead11882f269d2`
  仍exited137、OOMKilled=false、Paused=false，owner与旧short根一致。
- 09:51可用NVMe823080284160bytes（766.55GiB），MemAvailable815650865152bytes
  （759.63GiB）。这是时间敏感快照，不是准入预留。
- 三个静止旧根一次严格`timeout 15s du -sb -- <三精确根>`返回0、无stderr：
  train64432989310、paired945239、source-parent25775629bytes；合计64459710178bytes。
  未读取checkpoint张量或完整日志，未将历史计量值当作当前值。
- 原训练/选优截止仍9月29日23:12:08.209；suite截止仍9月30日05:12:08.209。
  当前训练窗口约13小时20分；仅按已返回step2的630.806秒/步外推，96步约16.82小时，
  尚未计额外加载、诊断、128局选优和128局主终评。该单步外推不保证后续速度。
- 原r1已消耗pre8+短训16=24自然局。首次GPU预检至failed终态的八卡墙钟包络约
  4.9655GPUh（包括间隔，不是逐卡利用率积分）；失败短训及旧CP2不标为通过。

## 故障边界与尚未完成的工作

原失败详见[09:41凭证](spb-l8random-r1-failure-20260929-0941.json)。本轮只读查看
准确容器23:48:40–23:49:30的Docker事件：23:48:45四对pause/unpause；随后23:49:11
和23:49:22出现kill，23:49:22 stop/die。返回窗口没有23:49:00成功pause事件；
不能据事件缺失证明具体daemon根因。

源码另确认：quiesce在pause请求未成功时仍用已耗尽的同一allowance请求resume，
可能用后一个错误覆盖首个错误；guardian在失败分支未保存当次pause后的观测状态。
这些是诊断/收尾问题，不足以宣称已修复最初Docker暂停失败。必须先有针对性的
回归与容器验证，不延长单次采样限制、不绕过静止计量、不接受未知存储占用。

CP2虽有文件清单，但无train2 result/.done/acceptance，不能跳过原短训门槛直接
续到96。本方案因此请求从原始SpB重新完成短训和96步，而非伪造r1终态或接用未验收CP2。

## 一次r2方案（数字预算待确认，不是启动凭证）

- 仍仅197八卡串行、原始SpB、L8、每局独立seed；训练/奖励/动作/评测协议保持原提案。
- 新增1048自然局、96PPO，其中重复旧pre8+train2的24局明确计费；跨r1/r2累计1072局。
- r2从首次GPU操作固定30小时/240GPUh；训练+选优24小时/192GPUh，主终评最多
  6小时/48GPUh且不超过suite截止。旧r1约4.9655GPUh另保留，合计包络上限约244.9655。
- 旧r1及新r2六根合计仍限352GiB：旧新训练+source根合计320GiB，旧新主终评根
  合计32GiB；不排除旧失败残件。四套新nativeCP约236.82GiB加旧约60.03GiB，
  尚有约23GiB训练侧余量，严格计量超限即失败。准入仍训练416GiB/评测128GiB空闲。
- 预计全链约22–26小时，仅粗估；不把硬截止当ETA，不保证成功。
- 修复与完整CPU/实际容器预检通过、clean冻结SHA已同步后，唯一新RUN_ID单次派发。
  旧失败产物保留、不停止他人、不自动重试、不接CP192/L9/L10、不跳过短训验收。
  仅继承原有本新组非best CP32的条件式保留规则，不增加旧产物删除授权。

拟用三个新根，09:52均只读确认不存在，未创建：

1. `/var/jfsCache/sc2-spb-l8random96-197-20260929-r2`
2. `/var/jfsCache/sc2-spb-l8random-paired128-197-20260929-r2`
3. `/var/jfsCache/sc2-spb-l8random96-197-source-20260929-r2`

## 本轮验证

仅只读SSH、精确容器inspect/events、GPU使用、df/free、三个静止根du、队列及host终态，
并审阅guardian/采样源码。首次查询误用了不存在的`short/host-supervision.json`，
随后使用实际`short/host-supervision/state.json`确认终态；缺文件未被当成新运行失败。
无新代码测试、无CPU容器、无GPU工作。预算更新待用户确认；原r1截止未改。
