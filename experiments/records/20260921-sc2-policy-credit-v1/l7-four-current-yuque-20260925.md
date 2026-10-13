# L7 四组训练曲线与配置：语雀发布凭证

2026-09-25 11:00–11:05 北京时间，按用户要求将所附四宫格曲线、对应实验结果、冻结配置和结论边界整理到语雀 `SCII日志` 知识库的新专题页：

- 标题：`L7 四组 RL 训练曲线、配置与 64 局对照（2026-09-25）`
- 已发布页面：https://www.yuque.com/yangdage-mu30r/nsahpp/gir6wg1t482zgxc8
- 图片：`l7-four-current-curves.png`，本地 SHA-256 `1c2bdc63e1569a9492f4e4310614d0917dbbc2ea5c98c59c8137bcd5bcaeb67f`。通过语雀原生附件上传，图像在正文中可见；图片二进制未提交 Git。
- 验证：编辑页显示发布成功，随后打开已发布阅读页，核对图像、四组结果表、训练/终评口径、配置、配对统计和来源链接。

页面明确区分 96 步 × 每步 8 局的训练曲线与独立的同一批 64 个新种子 CP96 终评。四组训练胜局/768 和 CP96 终评胜局/64 分别为 Qwen same fresh `660/768, 53/64`，Qwen random `669/768, 53/64`，SpB same `445/768, 16/64`，SpB random `513/768, 34/64`。配对终评另列原始 Qwen `49/64`、原始 SpB `35/64`，不把训练胜率当成泛化证据。正文同时记载模型与采样、PPO/mini-batch、动作/奖励、seed、checkpoint/恢复及评测配置，并区分机械合法性、技术验收和策略收益。

旧 Qwen same 的梯度精度缺口及严格 `failed` 保留为历史记录；新 fresh run 的完整验收是另一条运行。Qwen random 的旧失败重复局不计入 96 步主曲线，旧 CP2 祖先的非 bitwise 限制不抹除。SpB random 与 same 之间还有启动时序差异，不能宣称严格只改 seed。64 个复用评测种子及模型/FLOPs/Executor 限制均在语雀正文说明。

来源：[fresh Qwen same](qwen-l7same-fresh197.md)、[Qwen random 完成凭证](qwen-random-complete-spb-random-start-20260924.json)、[SpB random 完成凭证](spb-random-complete-20260924-134554.json)、[四组曲线派生记录](l7-four-arm-curves-20260924.md)、[64 种子配对结果](l7-common64-results-20260925.md)。本次只写语雀文档和该小凭证；未访问或修改服务器、权重、冻结实验或运行队列，也未将完整日志/密钥上传。
