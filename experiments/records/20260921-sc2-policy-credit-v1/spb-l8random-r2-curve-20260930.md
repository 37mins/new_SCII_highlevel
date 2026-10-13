# SpB L8 random r2：96步训练胜率曲线

采集时间：2026-09-30 10:11:40北京。RUN_ID
`sc2-spb-l8random96-197-20260929-r2`；实际训练runtime
`12f3600ca8e6e8edabc460de70860baeef2b5146`，仅节点`sc2-a100-197`。
这是用户要求的已执行96步RL曲线，不是recovery264零更新补评测曲线。
原r2终态仍为failed/exit137，长段result/.done/metrics缺失；绘图不补造这些文件。

## 口径与观察

- step1–2为本组fresh短训；step3–96由自己的完整nativeCP2续训，紫线位于2与3之间。
  96个实际返回PPO已由[先前完整取证](spb-l8random-r2-recovery-audit-20260930.json)确认。
  不混入旧r1重复局，也不将预更新审计单独作为更新证据。
- 每步8个自然结束训练对局，蓝线为该步胜局/8；橙线为含当前步的最近8步胜局/64，
  从step8开始，不对前7步填充、插值或外推。纵轴完整0–100%。
- 96步共503/768胜（65.49%），最近8步35/64胜（54.69%）。step1–32为148/256
  （57.81%），step33–64为194/256（75.78%），step65–96为161/256（62.89%）。
  描述上前期上升、中期较高、后期回落，并非持续改善。
- 每局独立从0..100有放回抽seed，私有Random(0)，不同step的场景难度变化。
  固定权重的独立验证及原始模型—CP96配对终评均不入本图；不能据此宣称策略学习、
  泛化提升或后期退化已被证明。原训练收尾基础设施失败也不等于模型学习失败。
- 本轮仅读取小账本和状态；未读取/复制权重、未重扫完整console、未派发新实验或修复服务器。

## 数据来源与复现

[小型数据快照](spb-l8random-r2-curve-20260930-data.json)仅包含96个step的胜数/局数、
汇总与13个小凭证的路径/大小/hash，不是完整指标或游戏轨迹导出。
SHA256：`4ae70574001d932dd71abbd02d0ca5d518783022a786093e8c46044d6bdc0eee`。

[只读采集器](collect-spb-l8random-r2-curve.py)每文件限制1MiB，重新核对两段manifest、
seed、outcome、audit的8个SHA256与早先96步实际返回指标取证相同，再验证每批env0..7、
完整自然终局、无截断、连续96step、独立seed序列和96审计2758/2758合法回答。
短训result/.done/acceptance一致；旧长段失败状态及终态文件缺失仍被保留。
未重新扫描大日志，实际返回PPO证据引用上述取证记录，不夸大本轮检查范围。

[绘图脚本](plot-spb-l8random-r2-curve.mjs)使用既有L7/L8配色与SVG+sharp静态绘图，
验证96个点、89个rolling点、累计和最近8步计数。图中明确failed、续训边界和非终评口径。
PNG/SVG仅保存在本地visualizations目录，不入普通Git历史。

```sh
ssh -o BatchMode=yes -o ConnectTimeout=10 sc2-a100-197 'python3 -B -' < collect-spb-l8random-r2-curve.py
node plot-spb-l8random-r2-curve.mjs spb-l8random-r2-curve-20260930-data.json /absolute/output/spb-l8random-r2-96step-20260930.png
```

已实际执行4项采集器测试：
`PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_spb_l8random_curve.py' -v`。
自然批次、缺失/重复env、截断/未结束/未知结果、错误reset检查均通过。
绘图命令实际成功，1500×1000 PNG已视觉检查，无文本裁切/遮挡。
图像SHA256：`7bea539a3a0c0b7462639d30b278def28da5fa9b7eea3efa1a323b8aae42e5d7`。
