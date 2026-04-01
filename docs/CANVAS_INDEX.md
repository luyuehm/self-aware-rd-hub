# CANVAS_INDEX

## Self-Aware R&D Hub 图谱索引

这份文档是这套架构图的总导航。

它回答 4 个问题：

1. 现在有哪些 canvas
2. 每张图主要讲什么
3. 每张图对应项目里的哪些目录 / 文件
4. 每张图对应哪些 CLI 命令或产物

---

## 一、总览

当前共有 3 张核心图：

1. [[Self-Aware R&D Hub.canvas]]
2. [[TiDB SQL Optimization Validation Loop.canvas]]
3. [[Memory Recall Writeback Loop.canvas]]

推荐阅读顺序：

```text
总架构图
  -> SQL 验证子图
  -> Memory 闭环子图
```

也就是：

```text
Self-Aware R&D Hub
  -> TiDB SQL Optimization Validation Loop
  -> Memory Recall Writeback Loop
```

---

## 二、图 1：Self-Aware R&D Hub.canvas

### 文件路径
- `/Users/macbook/vscode/obsidian-vault/Self-Aware R&D Hub.canvas`

### 这张图讲什么
这是**总架构图**。

适合回答：
- 整个系统从触发到报告的主链是什么
- SQL 优化链和 memory 闭环怎么接在一起
- 风险边界、shadow_fix、报告、长期记忆分别在什么位置
- 当前 Phase 2 已落地了哪些工程模块

### 适合什么场景
- 第一次给别人介绍这套系统
- 截图讲全局设计
- 讨论“现在做到哪一层了”
- 从概念层切换到工程层

### 图中核心块
- User / IDE / Git
- File Watcher
- R&D Hub Orchestrator
- Infra Sentinel
- SQL Performance Guardian
- Memory Recall
- Index Recommender
- Test DB Validator
- Validation Report Generator
- shadow_fix / reports
- Memory Writeback
- LanceDB / Long-term Memory
- Phase 2：parser / signals / inspector / gate / artifacts / CLI

### 对应项目目录
建议映射到：

```text
projects/self-aware-rd-hub/
├── cli.py
├── config/
├── parsers/
├── analyzers/
├── inspectors/
├── sentinels/
├── recommenders/
├── validators/
├── reporters/
├── reports/
└── shadow_fix/
```

### 对应代码 / 文件
- `cli.py`
- `parsers/sql_feature_extractor.py`
- `analyzers/explain_signal_analyzer.py`
- `inspectors/existing_index_inspector.py`
- `recommenders/index_recommender.py`
- `validators/validation_gate.py`
- `validators/tidb_index_validator.py`
- `reporters/validation_report_generator.py`
- `config/validation.yaml`
- `config/tidb.yaml`

### 对应产物
- `reports/before.json`
- `reports/recommendation.json`
- `reports/validation.json`
- `shadow_fix/sql_validation_report.md`

### 对应 CLI 命令
- `python cli.py tidb-explain ...`
- `python cli.py recommend-index ...`
- `python cli.py inspect-indexes ...`
- `python cli.py validate-index ...`
- `python cli.py generate-report ...`

### 下一跳建议
从这张图继续往下看：
- 想看 **SQL 验证链细节** → 打开 [[TiDB SQL Optimization Validation Loop.canvas]]
- 想看 **长期学习 / recall / writeback** → 打开 [[Memory Recall Writeback Loop.canvas]]

---

## 三、图 2：TiDB SQL Optimization Validation Loop.canvas

### 文件路径
- `/Users/macbook/vscode/obsidian-vault/TiDB SQL Optimization Validation Loop.canvas`

### 这张图讲什么
这是 **SQL 优化验证闭环子图**。

它把总图里的 SQL 主链单独展开，重点回答：
- SQL 是怎么进入验证链的
- `before.json` 怎么形成
- explain 信号如何转成 recommendation
- existing indexes 和 gate 如何介入
- validation / compare / report / outputs 怎么收口

### 适合什么场景
- 讲 SQL 验证链细节
- 和开发同学对齐模块职责
- 对照 CLI 跑一遍真实链路
- 看 Phase 2 比 Phase 1 多了什么

### 图中核心块
- Input / Watcher
- Historical Recall
- Before EXPLAIN
- SQL Performance Analysis
- Index Recommender
- Validation Gate
- Test DB Validator
- Compare Result
- Validation Report
- Outputs
- Phase 2：Feature Extractor / Signal Analyzer / Existing Index Inspector / validation.yaml

### 对应项目目录
```text
projects/self-aware-rd-hub/
├── parsers/
├── analyzers/
├── inspectors/
├── recommenders/
├── validators/
├── reporters/
└── reports/
```

### 对应代码 / 文件
- `parsers/sql_feature_extractor.py`
- `analyzers/explain_signal_analyzer.py`
- `inspectors/existing_index_inspector.py`
- `recommenders/index_recommender.py`
- `validators/validation_gate.py`
- `validators/tidb_index_validator.py`
- `config/validation.yaml`
- `config/tidb.yaml`

### 对应 JSON / 报告
- `reports/before.json`
- `reports/recommendation.json`
- `reports/validation.json`
- `shadow_fix/sql_validation_report.md`

### 最关键的 CLI 顺序
```bash
python cli.py tidb-explain --sql-file sql/sample_query.sql > reports/before.json
python cli.py recommend-index --sql-file sql/sample_query.sql --analysis-json reports/before.json > reports/recommendation.json
python cli.py validate-index --sql-file sql/sample_query.sql --before-json reports/before.json --recommendation-json reports/recommendation.json > reports/validation.json
python cli.py generate-report --before-json reports/before.json --recommendation-json reports/recommendation.json --validation-json reports/validation.json --base-dir .
```

### 这张图的阅读重点
优先看这几段：

1. `before -> parser / signals`
2. `parser / signals -> recommend`
3. `recommend -> inspector -> gate -> validate`
4. `validate -> compare -> report -> outputs`

### 下一跳建议
- 想回到全局 → [[Self-Aware R&D Hub.canvas]]
- 想看历史经验如何进入 recommendation / report → [[Memory Recall Writeback Loop.canvas]]

---

## 四、图 3：Memory Recall Writeback Loop.canvas

### 文件路径
- `/Users/macbook/vscode/obsidian-vault/Memory Recall Writeback Loop.canvas`

### 这张图讲什么
这是 **记忆召回 / 回写闭环子图**。

它重点回答：
- recall query 是怎么形成的
- case memory 和 pattern memory 怎么区分
- 历史经验怎么辅助 recommendation / validation / report
- 什么样的结果值得写回长期记忆
- 为什么“记忆不能替代当前验证”

### 适合什么场景
- 讲系统如何越用越聪明
- 讨论 recall / writeback 策略
- 设计 LanceDB memory schema
- 区分 case memory 与 pattern memory

### 图中核心块
- Trigger
- Recall Query Features
- Recall Query Builder
- Memory Recall Engine
- Weight / Assist Layer
- Runtime Decision
- Report / Explainability
- Writeback Policy Gate
- Case Memory
- Pattern Memory
- LanceDB / Long-term Store
- Boundaries / Future Evolution

### 推荐的工程映射
当前项目里还没有完全落地，但建议未来收口到：

```text
projects/self-aware-rd-hub/
├── memory/
│   ├── recall/
│   ├── writeback/
│   ├── schemas/
│   └── policies/
└── reports/
```

或者更轻量一点：

```text
projects/self-aware-rd-hub/
├── memory/
│   ├── recall_engine.py
│   ├── recall_query_builder.py
│   ├── writeback_policy.py
│   ├── case_memory_store.py
│   └── pattern_memory_store.py
```

### 和当前产物的关系
这张图依赖这些上游产物：
- `before.json`
- `recommendation.json`
- `validation.json`
- `sql_validation_report.md`

这些产物决定：
- 是否 worth_writeback
- 写 case 还是写 pattern
- 下次 recall 用什么特征

### 关键原则
- 记忆只做加权，不替代当前验证
- 历史成功不等于这次一定成功
- 历史失败不等于这次一定失败
- recall 不能绕过 validation gate
- writeback 需要去噪和去重

### 下一跳建议
- 想看 memory 如何嵌回总链 → [[Self-Aware R&D Hub.canvas]]
- 想看 memory 具体辅助 SQL 验证哪一步 → [[TiDB SQL Optimization Validation Loop.canvas]]

---

## 五、图 ↔ 目录 ↔ 命令 对照表

| 图 | 核心目录 | 代表文件 | 代表命令 |
|---|---|---|---|
| Self-Aware R&D Hub | `cli.py` `parsers/` `analyzers/` `inspectors/` `validators/` `reporters/` | `cli.py`, `validation_gate.py` | `python cli.py --help` |
| TiDB SQL Optimization Validation Loop | `parsers/` `analyzers/` `inspectors/` `recommenders/` `validators/` | `sql_feature_extractor.py`, `existing_index_inspector.py` | `tidb-explain / recommend-index / validate-index` |
| Memory Recall Writeback Loop | `memory/`（建议未来新增） | `recall_engine.py`, `writeback_policy.py` | 暂未完全实装 |

---

## 六、推荐讲解顺序

### 如果面对产品 / 管理 / 架构讨论
按这个顺序：

1. [[Self-Aware R&D Hub.canvas]]
2. [[TiDB SQL Optimization Validation Loop.canvas]]
3. [[Memory Recall Writeback Loop.canvas]]

### 如果面对开发 / 联调 / 落代码
按这个顺序：

1. [[TiDB SQL Optimization Validation Loop.canvas]]
2. [[Self-Aware R&D Hub.canvas]]
3. [[Memory Recall Writeback Loop.canvas]]

### 如果面对长期演进 / 智能化方向
按这个顺序：

1. [[Memory Recall Writeback Loop.canvas]]
2. [[Self-Aware R&D Hub.canvas]]
3. [[TiDB SQL Optimization Validation Loop.canvas]]

---

## 七、当前落地状态

### 已经落地
- 主图
- SQL 子图
- Memory 子图
- Phase 2 颜色分层
- 主图 / 子图口径统一

### 已经实现到工程里的部分
- `sql_feature_extractor.py`
- `explain_signal_analyzer.py`
- `existing_index_inspector.py`
- `validation_gate.py`
- `config/validation.yaml`
- `cli.py` Phase 2 命令接线

### 还适合继续补的资产
- 图内跳转说明 note
- `README` 中加入图索引入口
- memory 子系统真实代码目录
- 图对应的 demo walkthrough 文档

---

## 八、一句话总结

这 3 张图现在已经能组成一套完整叙事：

```text
主图负责讲全局
SQL 子图负责讲验证闭环
Memory 子图负责讲长期学习闭环
```

从现在开始，它们不只是“演示图”，而是：

- 可以指导代码落地
- 可以指导目录规划
- 可以指导 CLI 联调
- 可以指导下一阶段的 memory 演进
