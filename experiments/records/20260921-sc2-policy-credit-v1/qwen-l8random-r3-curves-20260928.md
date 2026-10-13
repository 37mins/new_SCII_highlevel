# L8 Qwen random r3：完整96步曲线与当前终评进度

采集时间：2026-09-28 18:38:11北京；节点仅sc2-a100-197。
RUN_ID=sc2-qwen-l8random96-197-20260928-r3，runtime/controller
`ad81511b270f782420208ac8a6f305a141e8042b`。本轮仅只读查询和本地绘图留档，
没有服务器修改、重试、训练派发或手动删除。

## 进展与结果口径

- 短验收及长段到CP96全部通过，训练链15:33:35结束。96次真实返回PPO、768自然
  训练局575胜（74.87%），消费回答3566/3566合法。最近8步47/64胜（73.44%）。
- 原八局诊断原始/CP2/CP96都是6/8；各0更新，CP2/96实际加载返回。
- 独立32seed选优：CP2/32/64/96都是22/32（68.75%），同分按预登记规则留CP2。
  这批验证未显示随checkpoint增长的胜率提升，不代表所有策略行为完全相同。
- 主测试为原始/same96/random96三组、各同一批全新64seed。已验收16/24批、
  128/192局，正在b05-original；未完成，不据局数不齐的中间成绩下最终结论。
  按已完成批次速度估计约19:30–20:00结束；实际固定硬截止22:57:08.465北京。
- 冻结队列在选优全部验收后执行授权保留规则：留下CP2/64/96，仅删除本组CP32，
  释放49,843,591,036bytes（46.42GiB），不可恢复；完整指标/seed/验收清单及
  原有其他组全部保留。不能再声称CP32实物存在或可续训。

## 图中两类数据必须分开

上图蓝线为每个global step的8局训练胜率；橙线为包括当前步的最近8步均值，
恰好64训练局，从step8开始，不填充早期点。紫色虚线是自身nativeCP2续训边界。
step1–2与3–96属于同一条有效新训练链，没有拼入r1/r2的失败CPU记录。
每step的8个场景seed来自私有Random(0)从0..100有放回连续抽取，允许偶然重复；
不是强制8个不同seed。曲线随场景难度变化，不可单独证明策略学习。

下图仅四个固定checkpoint在同一独立32seed验证集上的结果，全部0更新。
点之间虚线仅连接已测点，不代表中间checkpoint也被测过；验证用于选best，
不混入训练曲线或三臂主测试。最终主比较仍固定CP96，不因best=CP2更换测试对象。
一次same/random训练和小验证集不能证明稳定泛化或架构优势。

## 证据、复现与实际验证

- [紧凑绘图快照](qwen-l8random-r3-curve-20260928-1838-data.json)：仅逐步胜负、
  选定PPO标量和小凭证provenance，非完整训练日志/完整指标导出；138个来源文件
  记录路径、bytes和SHA256。数据SHA256：
  `6af5a38b70f16450ec3e891c73c1a78f7ecc29ef96b7142bb1bedcee41b08ded`。
- [只读采集器](collect-l8random-curve.py)：每文件最多1MiB；核对96连续step、
  每批env0..7、自然终局、不截断、随机seed序列、最终metrics胜率、正有限梯度/
  update_actor、invalidAdv≤0、valid_action_ratio=1、96审计数；五阶段result=
  done=acceptance、guardian及准确Docker exited0。选优清单hash与32局计分吻合。
  不读权重/console，不导入训练代码，不在服务器写文件；不替代全套冻结verifier。
- [绘图脚本](plot-l8random-curve.mjs)：复用既有L8静态SVG+sharp方法；校验step、
  每批胜数/局数、累计总数、rolling8和预定best同分规则后生成PNG/SVG。已实际
  运行并视觉检查，未见文字裁切、重叠或数据补点。
- [状态/容器/资源摘要](qwen-l8random-r3-status-20260928-1838.json)：CPU和训练均
  不是当前占卡工作；当前为零更新固定权重主终评。18:31采样八卡12526–12670MiB、
  95–97%瞬时利用率，strictdu正常、无storage-failure；不是永久资源状态。

在本record目录执行（输出目录需已存在）：

```sh
ssh sc2-a100-197 'python3 -B -' < collect-l8random-curve.py
node plot-l8random-curve.mjs qwen-l8random-r3-curve-20260928-1838-data.json /absolute/output/l8-qwen-random96-20260928-1838.png
```

交付PNG：`l8-qwen-random96-20260928-1838.png`，SHA256
`8dab468e8b21d62edd04aa50928d76e4144633a0bc637b9d9f6e8b0f856236eb`。
图像在本地visualizations目录提供，不上传大型图像、权重或完整日志。
