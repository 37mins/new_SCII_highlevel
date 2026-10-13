# 已绘图同 seed 中间 checkpoint 定点清理

实际完成：13:35:56北京时间320文件全部删除、逻辑1,133,818,614,080bytes；
可用空间由869,850,730,496升为2,003,669,897,216bytes（1866.06GiB）。
532保留文件stat及8小凭证哈希不变，详见[执行结果](plotted-checkpoint-prune-20260924-receipt.json)。
13:36:13原冻结SpB队列自动启动eval96，未手工dispatch或重启。
用户随后明确批准将本清理说明、精确路径/大小清单、定点脚本和小凭证
上传CeraveNew/new_SCII的codex/fix-sc2-startup-port-race；不含权重/密钥/完整日志。

2026-09-24 用户明确要求“你看看我们实验一些存过图的权重就删了吧，然后再把实验跑上”。
该授权只覆盖经核实不再承担续训/终评的已绘图权重；不是任意旧目录清理许可。
本次不降低1084GiB磁盘门槛，不改变原SpB队列、截止或预算，不停止任何进程。

## 精确范围与后果

[冻结文件清单](plotted-checkpoint-prune-20260924-plan.json)登记320个文件：
旧Qwen same和SpB same两组long/train96的CP16、24、32、40、48、56、
64、72、80、88，每套8个model和8个optim分片。
逻辑大小1,133,818,614,080bytes，已分配空间约1055.95GiB。
不读取大权重内容；清单保存大小、分配大小、inode、device、硬链接数，
不把这些元数据称为权重内容哈希。

保留CP2/CP8/CP96、所有小状态/driver和rank RNG、tokenizer/config、
全部指标、自然局记录、审计、日志、曲线、成功和失败凭证。
全部random组、当前SpB ownCP96、原始模型和冻结source均不在删除范围。
两个已绘图train96 metrics哈希分别为
Qwen 081c7440f21d9501070b2e2186d721ae5bda3de5ddde395b558b351c8257fecd、
SpB c12d9d2089e13537b5287bceb7a5a3919d385d11e09b387240aa7ee33559e6f7。
曲线来源见[l7-four-arm-curves-20260924.md](l7-four-arm-curves-20260924.md)。

删除不制作权重备份，执行后这些中间checkpoint不可恢复续训，也不再满足
完整CP重新验收条件。历史验收保留其当时有效性；不回写成“仍有全部权重”。
旧Qwen梯度精度缺口和strict failed仍保留，删除不会使历史失败转为成功。

## 已执行预检与后续

13:16:36北京时间只读清单：8GPU空闲、无computePID，空闲NVMe810.11GiB；
4个长期运行容器没有候选路径的挂载。13:33:05只读执行精确清单检查通过：
320候选与532保留文件stat一致、8份小凭证哈希一致、无打开FD或内存映射引用。
冻结plan文件SHA256为0e7f49cbc93f3c88f8cc9becd73d1db6acab8ff3193afd76a7ebcce1447484d1。
此段仅为预检，删除结果必须以随后独立receipt为准。

[单次脚本](prune_plotted_same_197.py)默认只读，读取stdin清单；只有--apply才逐文件unlink。
硬编码精确两根和20套CP/320文件集合，拒绝symlink、变更stat、硬链接、
运行中挂载或打开引用；执行前全部通过才删除，逐文件再查stat，无递归删除。
失败保留部分执行日志，不自动重试。
执行后核验320目标缺失、532保留文件和8份小凭证不变及剩余容量。

空间恢复后由原SpB冻结队列自行完成8局终评，无重复dispatch。
新Qwen same按[已批准预算](qwen-l7same-rerun-budget-20260924.md)准备独立fresh短+96，
须自己的CPU/实际启动器/Hydra/源码哈希及前序SpB完整验收通过，才单次派发。
本次容量授权取代预算文档中“尚无清理许可”的历史状态，不取代其他安全或预算约束。
