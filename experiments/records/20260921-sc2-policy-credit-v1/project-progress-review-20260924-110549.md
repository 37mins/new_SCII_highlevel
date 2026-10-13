# 项目修复进度、隔夜实验结论与语雀同步核查（2026-09-24）

任务：回答用户进展/总体修复/隔夜结论/语雀同步状态。服务器快照：北京时间
11:05:49.751089；语雀在本轮通过页面DOM只读核对。无实验或语雀写操作。

## 结论

当前实验分支的修复已从CPU/短测推进到真实96步长训、原生恢复和配对终评的
技术验收；不能概括为所有系统问题均已解决，更未证明RL提升或SpB架构优势。
最新工程结果以冻结运行版本和experiment record为准，不把仓库旧根README
中的早期Integrated Fixes状态混同于本轮L7冻结部署。

| L7组别 | 主轨迹训练胜局（每组768局） | 自身CP2 post→CP96 eval | 验收状态 |
|---|---:|---|---|
| Qwen 同seed | 609（79.3%） | 7/8→5/8 | 旧训练严格验收failed，另授权终评完成 |
| SpB 同seed | 445（57.9%） | 3/8→2/8 | 训练和终评完整验收 |
| Qwen 每局独立seed | 669（87.1%） | 8/8→8/8 | 有效前缀、新CP8续段、终评已验收；旧失败保留 |
| SpB 每局独立seed | 513（66.8%） | 4/8→未完成 | 训练完整验收，终评8局待入场 |

数据口径及来源：[四组曲线说明](l7-four-arm-curves-20260924.md)。
Qwen随机669=短训14+旧有效steps3–8的41+新steps9–96的614；
614/704只代表88步新续段，不代表完整1–96。旧失败重复局和失败槽仍计成本。
SpB随机513=短训8+长段505；94步长段结束于09:26:28。

隔夜新增结论：Qwen随机续训与终评完整通过；SpB随机已完成96PPO/768训练局。
随机组训练胜率较同seed组高是描述性现象，不是因果结论；mixed UID难度混入、
启动时序差异和样本相关性仍在。Qwen随机8→8已饱和，不提供长训提升证据；
两组same的8对终评下降不能据此断言稳定退化；SpB随机尚无CP96终评结论。

## 工程修复的已验证部分与边界

- canonical动作约束、no-thinking一致支持集、EOS/PAD对齐及中心化后无效回答
  credit门控已用于修复版真实实验；四组训练实际消费回答均100%合法。
  这验证机械合法性，不证明战略学习，也不等于每条本地生产指令已完成。
- binary64-v1/.17g已修复新日志的小梯度舍入问题；10:20精度回归14项通过、
  零跳过。历史Qwen same steps7/9/10/56/65/92原始值不可恢复，仍failed。
- SC2启动租约串行至首次观察、八局仍并行，已支撑后续Qwen续段与SpB训练
  完成；端口竞态仍是强证据假设，不宣称所有网络或Docker停止问题根治。
- 原生model/optimizer/scheduler/dataloader/driver及rank RNG恢复、种子、真实
  returned PPO、CP清单、host guardian及容器终态链路已有真实证据。
  新SpB完整native CP2链路通过，不消除旧Qwen CP2祖先非bitwise限制。
- 容量监管在工作，但当前资源不足尚未解决；预算批准不是容量/迁移授权。

## 当前服务器状态（11:05只读）

根queue仍为running-unverified/spb-random/long，short已完成；准确
long/host-supervision/state.json为stage-completed、completed=[train96]。
eval96 admission和run目录均不存在。已验收train96的result/.done/acceptance/
manifest/guardian五个SHA256均与[10:48凭证](spb-random-heartbeat-20260924-104827.json)
及原验收一致；未重读训练metrics、完整日志或大checkpoint。
当前严格两根存储样本831,162,453,514bytes/1TiB，return0、空stderr、无
storage-failure；checked_at=1790219123.654346。共同截止仍为
1790356959.0174987（9月26日01:22:39北京），不是完工ETA。

[10:38资源诊断](qwen-l7same-budget-approved-20260924-103801.json)已确认八卡
空闲、可用NVMe810.11GiB，距1084GiB门槛短缺273.89GiB；本轮未重复GPU/磁盘
诊断，不把旧资源快照称为11:05的新测量。SpB最后8局终评仍待入场。
[新Qwen同seed预算](qwen-l7same-rerun-budget-20260924.md)已批准792局/96PPO/
48wallh/384GPUh/1TiB，但尚未prepare、queue、dispatch，48小时未起算。
无新增容量处理授权，不删产物、不迁移、不降门槛、不改现有队列。

## 语雀：今晨结果尚未同步

本轮实际打开并只读检查[SCII日志](https://www.yuque.com/yangdage-mu30r/nsahpp/io9ul989o6qkposx)
正文，而非仅凭本地发布记录推断。页面仍标明状态时间2026-09-23 23:06:52，
页尾显示“昨天23:46”；仍写Qwen随机已到step51/96、SpB随机waiting-predecessor。
这与[昨晚发布凭证](yuque-project-overview-publication-20260923.json)保存的
23:06状态快照一致。已有SpB同seed完整结果与曲线，但缺今晨Qwen随机完成、
SpB随机训练完成/终评待入场、四组最新曲线及新Qwen同seed预算批准状态。
GitHub记录与语雀是不同同步目的地；Git推送成功不代表语雀已更新。
本轮请求是状态核查，没有编辑、发布或改变语雀分享权限。

验证：五个已验收终态哈希比对、小JSON解析、固定deadline及严格storage样本
检查、语雀实际阅读页DOM核对、文档diff检查；无新模型测试、GPU工作或外部发布。
唯一巡检保留。当前待解决事项是容量方案、SpB终评和另行请求后的语雀增量同步。
