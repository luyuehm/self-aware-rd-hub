# DEMO_WALKTHROUGH

## Self-Aware R&D Hub 演示讲解稿

这份文档给两种讲法：

- **5 分钟版**：快速讲清楚这套系统是什么
- **15 分钟版**：把主图、SQL 子图、Memory 子图串起来

配合图使用：
- [[CANVAS_INDEX]]
- [[Self-Aware R&D Hub.canvas]]
- [[TiDB SQL Optimization Validation Loop.canvas]]
- [[Memory Recall Writeback Loop.canvas]]

---

## 一、5 分钟版

### 目标
用最短时间讲清楚三件事：

1. 这套系统要解决什么问题
2. 它现在已经做到哪一步
3. 它为什么不是“普通脚本”，而是可演进的闭环系统

### 推荐顺序
1. [[Self-Aware R&D Hub.canvas]]
2. [[TiDB SQL Optimization Validation Loop.canvas]]
3. 最后提一句 [[Memory Recall Writeback Loop.canvas]]

### 讲法模板

#### 开场（30 秒）
这套东西的目标，不是单纯给 SQL 提建议，
而是做一个**自感知研发中枢**：

- 能发现 SQL 问题
- 能做测试库验证
- 能出报告
- 能把高价值案例写回长期记忆

所以它不是一个“单点推荐器”，而是一条**验证闭环 + 记忆闭环**。

#### 第一步：讲总图（2 分钟）
打开：[[Self-Aware R&D Hub.canvas]]

重点只讲主链：

```text
触发 -> 分析 -> 推荐 -> 测试验证 -> 报告 -> 记忆回灌
```

强调三点：
- 左边是触发与编排
- 中间是 SQL / validation 主执行链
- 右边是报告、产物、长期记忆

然后指出现在已经补到 Phase 2：
- parser
- signals
- existing index inspector
- validation gate
- JSON artifacts

一句话总结：

> 这张图讲的是系统级闭环，不只是 SQL 推荐。

#### 第二步：讲 SQL 子图（2 分钟）
打开：[[TiDB SQL Optimization Validation Loop.canvas]]

重点讲这 4 段：

1. `before -> parser / signals`
2. `parser / signals -> recommend`
3. `recommend -> inspector -> gate -> validate`
4. `validate -> compare -> report -> outputs`

这里要强调：
- 现在不是“看 SQL 就直接建议索引”
- 中间多了 **existing indexes inspection**
- 多了 **validation gate**
- 多了更结构化的 `before/recommendation/validation` 产物

一句话总结：

> 它已经从“规则 demo”走到了“可审计的工程原型”。

#### 第三步：提 memory（30 秒）
打开：[[Memory Recall Writeback Loop.canvas]] 或口头提一下。

只讲一句核心原则：

> 历史记忆只做加权，不替代当前验证。

这句话非常重要，因为它定义了这套系统的边界。

#### 收尾（30 秒）
最后一句可以这么说：

> 现在它已经具备主链、验证链、记忆闭环的基本骨架；
> 下一阶段不是重画图，而是把 recall / writeback / runtime evidence 做得更强。

---

## 二、15 分钟版

### 目标
适合：
- 架构评审
- 项目立项讨论
- 和开发一起对齐落地路径

### 推荐顺序
1. [[Self-Aware R&D Hub.canvas]]
2. [[TiDB SQL Optimization Validation Loop.canvas]]
3. [[Memory Recall Writeback Loop.canvas]]
4. 回到 [[CANVAS_INDEX]] 做目录 / 文件 / CLI 收口

---

### Part 1：讲全局问题定义（3 分钟）
打开：[[Self-Aware R&D Hub.canvas]]

#### 要回答的问题
- 为什么需要这套系统？
- 它和“SQL 推荐脚本”有什么不同？

#### 讲法
先说系统想解决的不是单一问题，而是一类研发场景：

- 保存 SQL / DAO / Repo 后，系统能感知候选问题
- 先做解释和验证，而不是直接给激进建议
- 结果要变成报告和产物
- 高价值案例要能沉淀，供下次 recall

然后沿主链讲：

```text
User / IDE / Git
 -> Watcher
 -> Orchestrator
 -> SQL Guardian
 -> Recommender
 -> Validator
 -> Report
 -> Writeback
```

指出这不是线性脚本，而是：
- 有编排层
- 有安全门
- 有报告层
- 有长期记忆层

#### 这里的重点结论

> 总图负责回答“系统为什么是系统，而不是几个脚本拼起来”。

---

### Part 2：讲 SQL 验证闭环（5 分钟）
打开：[[TiDB SQL Optimization Validation Loop.canvas]]

#### 要回答的问题
- SQL 怎么从原文走到 recommendation？
- 为什么这条链比第一版更可信？

#### 讲法
按下面顺序讲：

##### 1. Before EXPLAIN
SQL 先进入 before 阶段。
这里不是直接下结论，而是形成第一份输入材料。

##### 2. Parser + Signals
这一步是 Phase 2 关键升级：

- `sql_feature_extractor.py`
- `explain_signal_analyzer.py`

一个负责把 SQL 变成结构化特征，
一个负责把 explain 变成结构化信号。

这意味着后面的 recommender、report、memory，
都不再各自重复解析 SQL。

##### 3. Recommendation
推荐器不再只看原始 SQL 文本，
而是结合：
- where/order 特征
- explain warning signals
- 历史 recall（未来增强）

##### 4. Inspector + Gate
这是可信度提升最大的地方。

新增了：
- existing index inspector
- validation gate
- validation.yaml

所以现在不是“推荐完就去测”，而是先判断：
- 这个索引是不是已经存在
- 是否被前缀覆盖
- 是否符合测试库、安全门、列数限制等规则

##### 5. Validate + Compare + Report
通过 gate 才进入测试库验证。
然后：
- compare before / after
- 形成 validation.json
- 生成 report

#### 这里的重点结论

> SQL 子图负责回答“为什么这条链已经接近工程原型，而不只是 demo”。

---

### Part 3：讲 memory 闭环（4 分钟）
打开：[[Memory Recall Writeback Loop.canvas]]

#### 要回答的问题
- 系统如何利用历史案例？
- 为什么不会被历史经验带偏？

#### 讲法
按下面顺序讲：

##### 1. Recall Query Features
先强调：recall 不是模糊搜索一句 SQL，
而是基于结构化特征：
- primary_table
- where_cols
- order_cols
- join_cols
- verdict / risk / scene

##### 2. Recall Engine
memory 分两类：
- case memory
- pattern memory

case 适合复盘具体问题，
pattern 适合长期规则加权。

##### 3. Weight / Assist Layer
历史经验进入系统后，不是直接决定答案，
而是影响：
- recommender 权重
- validator 风险提示
- report 的历史解释上下文

##### 4. Runtime Decision
这里要明确讲边界：

> 当前验证结果优先，历史记忆只做辅助。

这是为了避免“历史上成功过，所以这次也一定成功”的错觉。

##### 5. Writeback Gate
并不是每次都写回。
只有：
- improved
- failed
- confirmed_rule
- 高价值、低重复、值得沉淀

才进入长期记忆。

#### 这里的重点结论

> Memory 子图负责回答“系统怎么学习，但又不会让记忆越权”。

---

### Part 4：回到索引文档做收口（3 分钟）
打开：[[CANVAS_INDEX]]

这里不再讲概念，而是讲落地：
- 图对应哪些目录
- 图对应哪些代码文件
- 图对应哪些 CLI 命令
- 当前哪些已经实现，哪些还在规划中

你可以把这一步当作“从图回 repo”的桥。

#### 推荐收尾话术

> 所以这 3 张图并不是汇报 PPT，
> 它们已经能直接指导：
> - 代码目录拆分
> - CLI 联调顺序
> - 产物设计
> - 下一阶段 memory 演进

---

## 三、面对不同对象时怎么讲

### 1. 对产品 / 管理
重点：
- 讲总图
- 少讲 parser 细节
- 强调“闭环”“验证”“长期演进”

一句话：

> 这是一个能持续积累经验的研发辅助系统，而不是一次性脚本。

### 2. 对开发 / 架构师
重点：
- 讲 SQL 子图
- 讲 gate / inspector / artifacts
- 讲模块边界

一句话：

> 重点不在建议本身，而在 recommendation 能否被验证、被审计、被演进。

### 3. 对做 AI / memory 的人
重点：
- 讲 Memory 子图
- 讲 case / pattern 区分
- 讲 writeback policy
- 讲“记忆只做加权”

一句话：

> 关键不是把记忆接进来，而是定义记忆的权限边界。

---

## 四、推荐的最后一句

如果你要做结束陈述，推荐用这句：

> 现在这套系统已经不是“能不能推荐索引”的问题，
> 而是已经具备了：
> **感知、分析、验证、报告、记忆回灌** 的基本闭环。
> 下一阶段的重点，是把 recall 和 runtime evidence 做强，而不是重新定义架构。
