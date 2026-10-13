## 专题补充｜有效率归零与 same/random seed 曲线（2026-09-24）

本节补充机制与证据边界，不改写历史实验。这里“同一步八局用同样 seed”是指八局共享一个游戏 seed，下一步再抽新 seed，不是八局输出或轨迹完全相同。结论先行：旧有效率归零是已观察到的输出／动作协议失效，旧 credit 链路又未保证无效回答受到负向学习信号；seed 曲线差异则涉及组内可比性、场景相关性和评测口径。两者不能合并成“random seed 导致模型崩溃、same seed 已证明学会策略”。

### 1. 那个有效率究竟是什么，为什么会突然到 0？

有效率指回答通过结构与语义检查的比例，不是胜率、GPU利用率或梯度非零率。当前验收以真实消费的有效回答数／真实消费回答总数为准，先于复制补齐和 PPO；旧 console 的比例可能包含补齐样本，不能直接当成相同分母。旧 L7 曲线在 steps48–73 连续26轮记录为0.000；这不是只凭三位小数认定精确零：9月21日13:41的只读诊断，近期1,405条已消费／可评回答中，合法数为0，1,391条出现重复 `</`。它们没有形成合法动作计划，主要故障现象是输出结构退化，而不是模型“没有打赢”。

“突然”是阈值指标的表现，不等于已定位某一个 step 的唯一触发点。完整答案须同时满足标签、动作名、行格式和累计配额；某种重复模式一旦占据输出，即可让整条回答全部判无效。我们没有做隔离每个因素的变点／因果对照，不能声称某次更新、单个 seed 或 no-thinking 一项已被证明是断崖的唯一原因。

已核实的链条分为三层：

1. 生成层缺口：旧 no-thinking mask 排除思考标签，却不是动作语法。它不保证规范动作名、列表格式、数量配额与闭合；原始 SpB 在旧协议下也出现空文本、翻译动作名、缺少列表前缀和超配额重复列表。故“禁止 thinking”不等于“保证合法计划”。
2. 环境结果与动作 credit 脱节：诊断中329条无效记录对应正环境 reward。Executor、自动战斗或既有执行状态仍可产生收益；这些收益不能解释成无效指令的贡献。非法输出时游戏仍能赢，因此只盯胜率看不到计划链路已失效。
3. 旧惩罚不是最终负优势保证：无效回答先在 reward 上减0.1，随后还要经过 GiGPO 组内减均值。若组内都扣同一常数，(R_i−0.1)−mean(R−0.1)=R_i−mean(R)，共同惩罚会被抵消；即使只部分无效，也可能不足以压过正相对回报。episode 分量还按每条轨迹的代表分数构造，不能替代逐回答合法性归因。因而“有 penalty、有非零梯度”并不保证模型在被纠正，存在持续强化无效输出的路径。

上面是观察加可复核机制，不是已经证明所有1,391条重复回答都受到了正梯度强化。缺少旧批次逐 token 最终张量时，不补造精确归因，也不把它解释成所有历史 RL 涨分都是假的。

另一个重要反证：冻结旧 no-thinking／top-p=.9 协议，在 L6 同64个 seed 上比较原始 SpB、D96、C96，三者有效回答分别78/681（11.45%）、80/877（9.12%）、21/837（2.51%）。原始模型也很低，说明不仅是 RL 权重退化；但也不排除训练进一步加重问题。旧 L7 又同时改变了难度与生成协议，不能单独归咎于难度或 no-thinking。

### 2. 现在修复了什么，100%有效率又不代表什么？

修复组合分别堵住上述不同环节：canonical 生成约束保证当前 BO 候选、规范格式、累计数量及192-token内完整闭合；生成／actor／old-actor／reference 使用一致支持，top-p改为1，并对齐 EOS/PAD。GiGPO 全部中心化之后，每条无效回答的有效 token 使用 A_new=min(A,0)−0.1；真实消费合法率低于0.5则在 PPO 之前停止，而不是删掉坏样本继续训练。没有事后剥 thinking、重采回答或放宽解析器。

因此，修复后四条 L7 主训练轨迹的100%消费合法率首先是受限生成协议的工程保证，不是 RL 自己学会格式，更不是战略能力或架构优势。新 credit 是显式辅助目标，也不是无偏的因果贡献估计。组合修复通过不等于每一项的独立效果都已由消融证明；旧失败记录和旧 Qwen same 的六项梯度精度缺口仍然保留。

### 3. 为什么八局同 seed 与八局独立 seed 的训练曲线会不同？

两者都是真实 GiGPO＋PPO，不是“random 不更新、same 才更新”。关键是采样和优势比较的分组。same 每步抽一个 seed 复制给八局；random 每局各抽一次。但已有 random 消融仍把八局放进同一个 UID 的 episode 优势组，并没有做到“每个 seed 各有多条轨迹、各自比较”。

为说明机制，可将回报概念性拆成 R_i=场景难度项(seed_i)+策略／执行交互项+噪声。这不是日志中已分离出的三个测量量。实际 GiGPO 联合优势含 episode 相对分量和 anchor-state 的 step 相对分量，不只是一个 R_i−mean(R)；episode 分量还分摊到轨迹回答数。对 episode 的组内比较而言：

• same：共享 seed 可以抵消一部分共同场景难度，使相对回报更接近“同场景下不同计划”的比较；但策略动作会让后续状态分叉，不能说全程观测相同。如果计划与回报都趋同，任务优势又会很弱，KL／熵项仍可能产生非零梯度。

• random＋mixed UID：容易局与困难局直接参与同一基线比较。较高优势可能来自场景容易，不一定来自计划更好；较低优势可能只是困难局。只有8局时，这会增加噪声和有限批次的错误奖惩风险。step 分量虽按 anchor 分组，但相同或近似 anchor 并不自动消除未来场景差异。此机制不意味着随机 seed 在数学上必然导致有偏或无法学习；随机环境本身是正常 RL 训练方式，问题是当前小样本分组是否提供了足够可比的信号。

• 曲线外观：same 八局相关性很强，常整批0/8或8/8，窗口后段恰遇容易 seed 也可显著抬高均线；random 每步平均八种场景，通常会减弱这种整批跳变，但不保证每次都更平滑。两种方案各96轮768局，抽 seed 的次数和覆盖范围却不同。训练序列、窗口平滑与场景组合本身就能改变线形，不能从“这条上升、那条平”直接判定学习效果。

实际例子：旧 Qwen L7 same 的96批只有63个不同 seed，71批全胜、18批全败、7批混合，89/96批同胜负。768局不是768个独立场景；全胜／全败也不严格等于零任务优势，因为 combat 和逐步回报仍可能不同。旧日志的0.000不能恢复成精确零。

### 4. 数据支持“same 能学、random 学不动”吗？目前不支持

旧 L6 的 D（same）后8步58/64，确有明显后段涨分；但完整训练475/768（61.85%），反而低于 C（random）的567/768（73.83%）。D早期8对评测2/8→4/8是小样本正向线索；C自身CP4→CP96为4/8→4/8，未观察到提升。这既不能说随机组整体表现更差，也不能拿D训练后段的斜率代替固定条件评测。

修复后 L7 的自身 CP2→CP96 配对终评为：Qwen same 7/8→5/8；SpB same 3/8→2/8；Qwen random 8/8→8/8；SpB random 4/8→5/8（终评已于9月24日13:45:08完成，不再是待评）。same 两组没有显示长训收益；Qwen random 已饱和；SpB random 单局变化也不构成可靠提升证据。8对样本小且重复使用，不是盲测，不能据此确定稳定提升或退化。

所以目前最稳妥的表述是：已观察到不同 seed 方案的训练曲线差异，same 有降低组内场景混杂的机制优势，也有高相关和低任务信号的问题；random 扩大覆盖，却在 mixed UID 小组里引入场景噪声。哪一项实际主导了曲线差异，尚未被控制实验分离。参数量／FLOPs、决策次数、执行器、恢复历史和启动时序等限制也未全部消除。

### 5. 下一步怎样验证解释（研究建议，不是新增实验授权）

先用已有逐局数据检查合法性、episode／step 优势、seed和决策次数的关联；不把相关性升级为因果。若另获预算，可用不更新的冻结策略复走相同训练 seed 序列，判断“上涨”有多少来自场景顺序；在相同交互和计算预算下比较 K个seed×每seed多条轨迹、按seed建立优势组的设计；最后在未用于选择的固定评测集上，比较pre／CP2／CP96并做独立重复。仅增加训练步数、改平滑窗口或追求梯度非零不能回答这些问题。本次仅整理文档，不修改运行实验、阈值、分组或预算。

### 可追溯证据

• [旧L7失效诊断与credit修复合同](https://github.com/CeraveNew/new_SCII/blob/f7ca1b629715d2648cdb882e175e1c62aeca276d/experiments/records/20260921-sc2-policy-credit-v1/README.md#why)：1405/1391/329的口径与修复边界；旧运行7236c37。

• [canonical动作支持设计](https://github.com/CeraveNew/new_SCII/blob/f7ca1b629715d2648cdb882e175e1c62aeca276d/docs/decisions/sc2-canonical-action-support.md)：原始模型的真实格式错误与受限策略声明。

• [GiGPO冻结实现](https://github.com/CeraveNew/new_SCII/blob/7236c37b116fd8fbe15db09ccbdcd2e740e4e840/gigpo/core_gigpo.py)：episode与anchor-step两种相对优势，而非把同seed自动等同于相同轨迹。

• [L7同seed结果解释](https://github.com/CeraveNew/new_SCII/blob/f7ca1b629715d2648cdb882e175e1c62aeca276d/experiments/records/20260921-sc2-policy-credit-v1/l7-results-interpretation-20260922.md)、[四组逐step聚合数据](https://github.com/CeraveNew/new_SCII/blob/f7ca1b629715d2648cdb882e175e1c62aeca276d/experiments/records/20260921-sc2-policy-credit-v1/l7-four-arm-curves-20260924-data.json)、[SpB随机终评完成凭证](https://github.com/CeraveNew/new_SCII/blob/f7ca1b629715d2648cdb882e175e1c62aeca276d/experiments/records/20260921-sc2-policy-credit-v1/spb-random-complete-20260924-134554.json)。

• [历史D/C汇总及面板结果](https://github.com/CeraveNew/new_SCII/blob/f7ca1b629715d2648cdb882e175e1c62aeca276d/experiments/records/20260921-sc2-policy-credit-v1/yuque-project-overview-20260923.md)：不同难度／协议分开解读。9月16日另有[逐答credit复算](https://github.com/CeraveNew/new_SCII/blob/f7ca1b629715d2648cdb882e175e1c62aeca276d/experiments/records/20260916-combat-result-reward-v1/temperature-credit-audit.md)证明旧gamma=.95会按Planner调用次数折扣、可能倒置回报排序；D/C后续gamma=1，不能把这个早期问题当作后续随机曲线不升的直接原因。
