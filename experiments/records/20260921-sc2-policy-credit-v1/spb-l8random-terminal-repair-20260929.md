# SpB L8 random r2：收尾与存储暂停互斥修复

9月30日：用户要求“继续下一步”，先做失败r2的只读取证，不派发GPU。
入口 `inspect_spb_l8random_r2.py host`：对指定console做最多100MiB/60秒流式
扫描，仅返回真实PPO指标投影及匹配行hash，不下载/保存完整日志；同时核验小账本
和CP文件清单。`small`模式仅CPU读取每个小于1MiB的SC2/driver/dataloader/rank
RNG文件，model/optim只stat，不做权重加载。输出仅stdout，不调用finish/verifier写入，
不创建旧run的result/.done/acceptance，也不把failed CP自动晋级。
该检查不替代模型/Adam本体的完整性及真实GPU加载检查；恢复评测仍需单独确认。

状态：`CPU-validated candidate / GPU-unverified`，不是实验重启。
9月29日23:54:55北京：修复代码5849c94已push并用ls-remote核验同一完整SHA，
197真实Linux97项CPU回归零跳过，三类实际CPU容器探针全部通过。
[完整小凭证](spb-l8random-terminal-cpu-20260929.json)。
用户要求“继续修复啊”。开发分支 `codex/fix-terminal-storage-handoff`，起点
`612a4fdae9a1319359eef29b411dab5f40828135`；完成后同步既有实验分支。
沿用原 record；不修改冻结 r1/r2、预算、队列、失败结果，不新派发 GPU。

## 事实与推断边界

9月29日23:13:14北京时间，只读确认197八卡0MiB/0%、无compute-app，准确r2
train96容器仍exited137、OOMKilled=false。宿主Docker29.1.3、kernel5.15.0-97，
cgroup2，/var/jfsCache为XFS/noquota。本轮没有修改这些系统配置。

23:20:29读取35行以内的Docker故障时间窗日志：18:53:07 daemon明确报告
`OCI runtime pause failed: timeout of 10s reached waiting for the cgroup to freeze`；
18:53:19明确报告SIGTERM后10秒仍未退出，随后force stop。准确容器、预算及CP
清单见[保留的失败凭证](spb-l8random-r2-failure-20260929-2252.json)。
本轮只读取两个有界尾部（entry7000bytes、console1800bytes），确认最后内容包含
returned step96、`Final validation metrics: None`、训练进度96/96。CP96模型rank0/7
仅stat：访问时间分别18:52:45.497/45.493，修改时间18:52:47.601/47.437。
没有读取模型张量或完整日志；这不是完整checkpoint可加载性证明。

确定的触发链是：最后训练返回后 → 存储暂停失败 → guardian停止容器 → recorder
终态缺失。收尾与freezer并发是本次针对的风险窗口；具体阻碍冻结的线程/内核原因
没有被事发凭证捕获，不能声称是唯一根因或已根治。模型hash读取也没有直接证据
可以认定为触发源。Linux文档说明冻结是异步完成、应等frozen确认，不能把发出
请求当作已静止：[cgroup v2 freezer](https://cdn.kernel.org/doc/html/latest/admin-guide/cgroup-v2.html#core-interface-files)。

## 最小修复与入口

新deployment必须显式设置 `terminal_handoff: terminal-drain-v1` 才启用。
本轮**没有**给任一生产prepare默认配置加入该字段。旧路径仍按原暂停规则运行。

1. `TaskRunner.run` 在 `trainer.fit()` 正常返回后、局部trainer/Ray actor销毁前，
   调用 `agent_system/sc2_terminal_handoff.py`。通过原有稳定 `.storage.lock` 的
   shared锁独占创建并fsync小型 `runs/<stage>/terminal-intent.json`。
   该凭证明确 `experiment_accepted=false`，不是result/.done或GPU退出证明。
2. 宿主 `storage_batch197.sample` 仍先持exclusive锁。锁覆盖“检查intent →
   pause/等待退出 → 精确du → unpause”整个窗口。这样publisher不能插入到
   “已判断无intent，但尚未pause”的窗口，也不会冻结持有shared锁的publisher。
3. 无intent：仍一次verified pause计量全部账户。有intent：不再pause收尾，
   只等**同一完整ID、owner匹配的容器**实际exited0，之后才静态du。
   退出等待与所有du**共用原15秒**，不另加宽限、不取旧值、不live-du fallback。
   超时、非零退出、暂停状态、identity不符仍失败并由原guardian回收。
4. `SC2_FINALIZATION_MODE=terminal-drain-v1` 使shell保留真实pipeline退出码并
   退出，不在GPU容器内做耗时的最终recorder扫描/hash。宿主必须先通过guard
   completed+准确容器exit0，再运行冻结 `scripts/run_record.py finish`，仍受原
   绝对截止约束；前后静态计量，随后调用原完整verifier。算法/指标/CP必要文件
   门槛未放宽。已有result文件拒绝覆盖，failed guardian/exit137拒绝调用recorder。

`host_stage197.terminal_launch/terminal_options` 成对配置子进程与宿主。
通用 `supervise_part` 和Qwen/SpB共用L8训练入口已接入**默认关闭**的开关。
配置归一化只忽略这条显式运行锁路径，不忽略科学协议字段。系统资产清单从34
扩至37个源码文件，补入主入口/launcher/terminal helper并更新变更文件hash。
selection/primary有各自入口，不能因训练入口支持就宣称后继已完成新配置验收。

## 验证与限制

本机Python3.12，`PYTHONDONTWRITEBYTECODE=1`，依赖路径
`/private/tmp/sc2-spb-l8-testdeps.nzp1NX`；命令：

```sh
PYTHONPATH=/private/tmp/sc2-spb-l8-testdeps.nzp1NX:tests:scripts:experiments/records/20260921-sc2-policy-credit-v1 \
python3 -m unittest -q test_terminal_storage197 test_storage_batch197 test_host_stage197 \
  test_storage_quiescent197 test_policy_credit_storage197 test_policy_credit_storage_coordination197 \
  test_l7_host_continuation197 test_metric_precision test_sc2_policy_resume \
  test_spb_l8random197 test_qwen_l8random197 test_qwen_l8random_retention
```

190项：186通过，4项GNUdu/Linux专用跳过；18项新终态回归全部通过，含真实
publisher子进程、锁两种交错顺序、零退出/非零退出/超时、假intent、禁止覆盖、
finalizer失败阻断后继、shell退出码保留。`bash -n`、`git diff --check`和37项源码
hash核验通过。最初新增测试发现多构造了未使用的pause context，已修正；未发起
实际Docker/GPU暂停。尝试扩展全模型回归257项时，4个模块因本机无Torch导入失败，
2个socket测试受沙箱限制，另8项跳过；不能算完整模型回归通过。

随后已完成新建小型CPU验证目录、固定已存在image、0GPU/0游戏/0PPO的三种Docker
生命周期探针，入口 `tests/terminal_storage_probe197.py`。每容器1CPU/256MiB、
无网络/read-only rootfs，无GPU设备，源码+产物合计256MiB，整项5分钟上限。
只停止探针自己创建的准确ID容器并保留容器及证据；未修改共享运行时/旧实验。
源码tar的SHA256在服务器解包前核验。首次97项Linux回归中，一项因源码archive
不含历史Git对象而失败；补入**只读**旧r2源码GIT_DIR后，97项全部通过、零跳过。
未伪造Git历史、未改旧source，首次失败也未派发探针容器。三类CPU探针在23:53
首次执行：exit0正常完成；exit7及hang都阻断finalizer/verifier；后者超过原15秒
后guardian仅停止其准确测试容器。三容器DeviceRequests=null、无GPU设备、无OOM，
最终全部exited（0/7/137）。正常收尾前的CPU暂停成功，intent后无新增pause。
严格GNUdu一次返回0/空stderr：测试产物22867bytes、源码/包42033665bytes，
合计42056532bytes/256MiB。23:54八卡仍0MiB/0%。实际探针使用小型fixture与
finalizer回调，不冒充真实模型、Ray/CUDA teardown或完整模型回归。
真实GPU下是否能在15秒内退出仍未验证，训练中（非终态）的freezer失败也未根治。

## 旧CP96和后继交接

r2的queue/long仍failed，不能补写exit0或把96/96日志当作严格验收。CP2/32/64/96
文件保留，不删除。短训和长训合计768自然局/503胜是临时统计，不是新学习结论。

不应因为收尾监控失败就自动重跑全部96PPO。优先准备独立、只读的CP96取证及
恢复评测合同：核对完整returned metrics/审计/seed与CP本体，再由用户确认是否
允许使用“基础设施失败run的已核验权重”补剩余评测。即使评测通过，旧r2仍failed，
不抹除来源限制。剩余原计划为eval96的8局、4CP×32选优128局、原始/CP96各64主
终评128局，共264局/0更新；**本轮未授权或执行这项受控交接**，也未扩时/扩预算。
