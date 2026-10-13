# L7 四组已结束训练曲线与当前进展（2026-09-24）

图表数据状态：10:00:37 北京；交付前重新核验：10:09:50 北京。
本次只读分析，没有服务器写操作、重跑、重复派发或额外实验。沿用当前实验 record 和分支。

## 图表与口径

本图覆盖本轮 Qwen/SpB × 同 seed/每局独立 seed 四组 L7 训练，
不是把历史 D/C、L6 短验收等不同协议混为同一训练曲线。

- 蓝线：每个 global step 的 8 个真实自然局胜率。
- 橙虚线：过去 8 个已完成 step 的算术均值（64 局），从 step8 开始。
- 紫虚线：自身 CP2 恢复边界；Qwen 随机另标 CP8 恢复边界。
- 红方框：Qwen 同 seed 的六项历史梯度精度缺口，胜率观察仍然有效，
  但不因此改判该训练严格验收通过。
- 各组恰好 96 个点；没有插值、补零、失败重跑重复计数或把评测混入训练。
- 消费回答合法率各组均为 100%，列在面板下方而不重复画四条平线。

| 组别 | 主轨迹训练胜局 | 实际消费回答合法 | 自身 CP2 post → CP96 eval | 状态 |
|---|---:|---:|---|---|
| Qwen 同 seed | 609/768（79.3%） | 4995/4995 | 7/8 → 5/8 | 训练已结束，旧严格验收仍 failed；另授权终评完成 |
| SpB 同 seed | 445/768（57.9%） | 11313/11313 | 3/8 → 2/8 | 训练和终评完整验收 |
| Qwen 每局独立 seed | 669/768（87.1%） | 2508/2508 | 8/8 → 8/8 | 有效前缀、新续训和终评验收完成 |
| SpB 每局独立 seed | 513/768（66.8%） | 1959/1959 | 4/8 → 待评 | 训练完整验收；最后8局终评待入场 |

Qwen 随机主轨迹的 669 胜准确分解为：short1–2 的14/16、旧运行有效3–8的41/48、
新原生CP8恢复9–96的614/704。614/704从未代表完整1–96总计。
旧失败运行完成的重复9–13及失败派发槽仍保留在资源预算/失败记录中，
只是从主轨迹曲线排除，不宣称免费重试或旧failed r4通过。

## 当前进展

[10:09:50只读凭证](l7-curves-status-20260924-100950.json)：
SpB长段host仍为 stage-completed，completed=[train96]，
eval96入场凭证和run目录均不存在；根queue仍指向long/running-unverified。
已验收train96的result、.done、acceptance、manifest、guardian五个哈希均未变化。
按已核验冻结控制流，当前等原入场条件，具体未满足资源未得到凭证，不猜测GPU/RAM/磁盘原因。
现有采样两根合计831,162,453,513 bytes，低于1 TiB，return0/空stderr/无failure。
固定共同截止仍为9月26日01:22:39北京，不是ETA。
唯一10分钟巡检保留，没有新建、删除或改动监控。

## 数据来源与复现

[图表精简数据](l7-four-arm-curves-20260924-data.json)只含384行按step聚合的
wins/games/实际消费回答计数与源文件SHA256，不含新完整原始metrics、checkpoint、
完整日志或密钥；本次未上传新完整实验数据。

Qwen五个准确训练段仅重新只读小型metrics/outcomes/seeds/audit/manifest以绘图，
每文件上限1 MiB。逐段按全局步筛选，核对8个不同env索引、自然终止、无截断、
Random(0)协议序列、metrics成功率与outcomes一致、有效回答审计与正update_actor时间。
Qwen同seed梯度三位小数缺口没有修复或豁免。
Qwen随机旧prefix只取3–8，新suffix只取9–96，无重复。

SpB同seed直接复用已授权保存的完整旧快照；
SpB随机从已提交short2与长94验收小凭证中的batch summary/audit派生，
没有为绘图再次读取其全部训练日志、metrics或大CP。
每个本地源记录哈希及Qwen远端小源文件哈希均保存在图表数据中。

图文件保存在当前任务可视化目录：
`/Users/yangjinyue/.codex/visualizations/2026/09/03/01a06605-4e2f-7052-925a-e3bf70ef2b4b/l7-four-arm-curves-20260924.png`
（同名SVG）。图二进制未加入Git；脚本与小数据可重建。

```bash
node experiments/records/20260921-sc2-policy-credit-v1/plot-l7-four-arm-curves.mjs \
  experiments/records/20260921-sc2-policy-credit-v1/l7-four-arm-curves-20260924-data.json \
  /absolute/output/l7-four-arm-curves-20260924.png
```

脚本复用既有蓝/橙和trailing8约定，依赖sharp。
默认使用当前桌面bundled路径，其他机器可设置SC2_SHARP_MODULE为sharp模块路径。

已执行验证：bundled Node语法检查；JSON解析；四组96连续步和768自然局、
胜局与消费计数合计断言；SVG→PNG渲染；PNG人工视觉检查；git diff --check。
默认shell没有node命令，语法检查随后使用明确的bundled Node成功执行；
这不是实验或绘图数据失败。
图表数据SHA256：53a65a5dfad001c9e1eb23b902dc71c99e19ce077f1b8b0b8230d6295b1cd94f。
PNG SHA256：d19ae632005504643430b9744186444df3caa0474ab2c16da80409b7a8323ba9。
SVG SHA256：8106ba82b5b0631ce4d261eae1fa7eabbc84f037873652d21cf15ca3f13a479f。

## 结论边界

同seed每批共享场景导致较强相关性；random仍存在mixed UID难度混入advantage限制。
SpB随机相对同seed还改变启动租约串行时序，不能称严格只变seed或时序等价。
Qwen随机CP2祖先缺driver RNG的非bitwise限制以及所有历史失败均不抹除。
8对评测样本很小，Qwen随机8→8已经饱和；SpB随机尚无终评。
训练高胜率、受约束100%合法率和正梯度均不证明策略学习或架构优势，
参数量/FLOPs不匹配和Executor参与等限制继续保留。
