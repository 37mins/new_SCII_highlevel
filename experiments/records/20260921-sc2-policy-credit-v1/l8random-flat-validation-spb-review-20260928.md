# L8 random 平坦验证诊断与 SpB random 对照

核验时间：2026-09-28 19:36:25北京。仅sc2-a100-197只读小凭证，本地计算；
不读权重/完整日志、不新增游戏、不修复/重启/删除。复用原record与实验分支。

## 结论：学习收益未证实，不等于已定位训练实现故障

四个CP在32独立验证局中都是22胜，而且按同一seed排序后，所有六对checkpoint
比较的逐局胜负差异都是0。并非仅仅碰巧总胜场相同；这批验证没有检测到胜负改善。
但不能将32个二值终局相同解释为模型权重、动作分布或整条轨迹完全相同。

实际load小凭证分别指向本组CP2/32/64/96，loaded_global_step匹配、加载返回、
0更新；四组初始全8rank CPU/CUDA RNG及场景seed一致。16阶段独立result=.done=
acceptance、clean冻结ad81511/world8/binary64，16准确容器和guardian全部exited0。
CP32现已按授权删除，这些是删除前实际评测的保留凭证，不声称当前实物可重验。

| checkpoint | 验证胜局 | 策略决策/消费回答 | 与CP2逐局决策次数不同的局数 |
|---|---:|---:|---:|
| CP2 | 22/32 | 178 | — |
| CP32 | 22/32 | 130 | 32/32 |
| CP64 | 22/32 | 132 | 31/32 |
| CP96 | 22/32 | 130 | 32/32 |

决策次数差异排除了“已观察到整条轨迹完全相同”的说法，但不单独证明差异源于
参数学习；环境时序等也可能影响轨迹。96真实返回PPO/正有限梯度是执行证据，
不是独立的参数增量校验，也不是有益策略学习证据。本轮没有读取大CP比较张量。

## L8新64seed三臂主终评已经完成

整组queue于**19:20:29.526北京**completed/exit0，主终评24阶段/192自然局，
0更新、无平局/截断，1155/1155消费回答合法。主终评24个准确容器/guardian
全部exited0；各阶段result=.done=acceptance、正确实际模型加载、seed/RNG匹配。
连同选优，共40个准确终态容器核验通过；未重跑冻结完整日志verifier。

| 固定模型 | 同一64新seed胜局 | 胜率 | Wilson95%区间 |
|---|---:|---:|---:|
| 原始Qwen | 43/64 | 67.19% | 55.00%–77.43% |
| L8 same CP96 | 35/64 | 54.69% | 42.57%–66.27% |
| L8 random CP96 | 45/64 | 70.31% | 58.23%–80.09% |

预登记主对比random−same：逐局11改善/1退步，**+15.625pp**，配对bootstrap95%
[6.25,26.5625]pp，exact双侧McNemar **p=0.00634765625**。支持本次固定benchmark
上的random优于same；仅一次训练/条件，不升级为跨训练种子稳定优势或架构证据。

原始权重比较均为预先标记的次要探索性分析，未多重校正：

- random−原始：2改善/0退步，+3.125pp，bootstrap[0,7.8125]pp，p=0.5；
  **没有证实相对原始模型的学习收益**，也不能反过来宣称总体等效或绝对无收益。
- same−原始：2改善/10退步，−12.5pp，bootstrap[−23.4375,−3.125]pp，
  未校正p=0.03857421875；描述为本次退步信号，不作为额外确认性声明。

算法遵循派发前冻结qwen_l8random_plan.py：PCG64 seed2026092709、100000次
配对重抽、linear percentile；稀疏discordance的bootstrap不是exact test反演。
主样本固定64，不因结果追加、不用validation-best替换CP96。

## 对应SpB random是L7，不是本次L8

已完成的是修正版L7原始SpB独立起训96PPO、768局513胜（66.80%），
1959/1959消费回答合法。前/中/后32步训练胜率为147/256、181/256、185/256
（57.42%→70.70%→72.27%），虽然训练分段均值上升，独立评测并未证实收益。

历史L7 common64：原始SpB35/64；sameCP96为16/64；randomCP96为34/64。
random−原始逐局8改善/9退步，−1.5625pp，bootstrap95%[−14.0625,10.9375]pp，
exact p=1、Holm p=1。same−原始2改善/21退步，Holm p≈0.000198，有明确退步证据。
原八局random诊断CP2 4/8→CP96 5/8不能推翻64局对照。
本record未见已启动/完成的SpB L8 random长训；不能把L7结果当同难度L8架构对照。

历史依据：[L7配对终评](l7-common64-results-20260925.md)、
[96步训练小数据](l7-four-arm-curves-20260924-data.json)、
[SpB全链结束](spb-random-complete-20260924-134554.json)。不同L7/L8评测seed不合并统计。

## 下一步边界与复现

建议先定位“更新是否有效影响决策、为何未改善任务”，不要直接加长训练掩盖问题。
尚未验证的候选包括：参数变化幅度/同步、相同观测下的策略分布变化、reward与
advantage是否鼓励有效计划、执行器是否掩盖计划差异。独立seed的mixed UID场景
难度混入advantage也是既有限制，但本轮不能认定它是唯一原因。更深入参数比较
或模型推理需要另行确定只读资源范围，本轮未执行、未安排任何新实验。

- [只读采集器](collect-l8random-paired-diagnostic.py)：每文件最多128KiB；40阶段
  的小终态/加载/manifest/RNG/guardian和Docker归属；246个小来源记录SHA256。
- [紧凑完成与逐局凭证](qwen-l8random-r3-paired-complete-20260928-1936.json)。
- [分析脚本](analyze-l8random-paired.py)与[统计结果](qwen-l8random-paired-statistics-20260928.json)。

实际执行：`ssh sc2-a100-197 'python3 -B -' < collect-l8random-paired-diagnostic.py`
成功；bundled Python3 `-B analyze-l8random-paired.py`通过，NumPy2.3.5；
冻结统计plan与运行SHA的git diff为空。源码AST、JSON、独立BigInt精确检验、
192局/1155合法消费合计与git diff检查通过。没有运行新的模型测试。
