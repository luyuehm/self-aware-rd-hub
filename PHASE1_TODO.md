# Self-Aware R&D Hub · Phase 1 TODO

## 目标
打通最小 SQL 验证闭环：

```text
SQL
→ before explain
→ candidate index
→ test-db validate
→ markdown report
```

---

# 0. 初始化项目骨架

## TODO
- [ ] 创建项目目录 `projects/self-aware-rd-hub/`
- [ ] 创建子目录：
  - [ ] `config/`
  - [ ] `sentinels/`
  - [ ] `recommenders/`
  - [ ] `validators/`
  - [ ] `reporters/`
  - [ ] `reports/`
  - [ ] `shadow_fix/`
  - [ ] `sql/`
- [ ] 创建 `sql/sample_query.sql`
- [ ] 创建 `requirements.txt`
- [ ] 创建 `cli.py`

## 验收
- [ ] 目录结构齐
- [ ] `python3 cli.py --help` 不报错

---

# 1. 配置 TiDB 连接

## 文件
- [ ] `config/tidb.yaml`

## TODO
- [ ] 写入：
  - [ ] `host`
  - [ ] `port`
  - [ ] `user`
  - [ ] `password`
  - [ ] `database`
  - [ ] `connect_timeout`
- [ ] 确认这是**测试库 / 开发库**
- [ ] 不要写生产库配置

## 验收
- [ ] 能成功读到 YAML
- [ ] 手工测试能连通 TiDB

---

# 2. 实现 `tidb_explain_runner.py`

## 文件
- [ ] `sentinels/tidb_explain_runner.py`

## TODO
- [ ] 读取 `config/tidb.yaml`
- [ ] 建立 PyMySQL 连接
- [ ] 执行：
  ```sql
  EXPLAIN FORMAT=verbose <sql>
  ```
- [ ] 返回结构化结果：
  - [ ] `kind`
  - [ ] `status`
  - [ ] `sql`
  - [ ] `rows`
- [ ] 失败时返回：
  - [ ] `status=fail`
  - [ ] `error`

## 验收
- [ ] 对 `sql/sample_query.sql` 能产出 explain 结果
- [ ] 断开 DB 时也能输出结构化错误，而不是直接 traceback

---

# 3. 在 `cli.py` 中接入 `tidb-explain`

## 文件
- [ ] `cli.py`

## TODO
- [ ] 加子命令：
  - [ ] `tidb-explain --sql-file`
- [ ] 读取 SQL 文件
- [ ] 调 `tidb_explain_runner.run_explain`
- [ ] 打印 JSON 到 stdout

## 验收
- [ ] 能执行：
  ```bash
  python3 cli.py tidb-explain --sql-file sql/sample_query.sql > reports/before.json
  ```
- [ ] `reports/before.json` 是合法 JSON

---

# 4. 实现 `sql_performance_guardian` 的最小分析逻辑

## 文件
- [ ] `sentinels/sql_performance_guardian.py`

## TODO
- [ ] 解析 explain rows
- [ ] 提取 operator/id
- [ ] 判断：
  - [ ] `full_table_scan`
  - [ ] `high_row_scan`
  - [ ] `index_not_used`
- [ ] 输出：
  - [ ] `warnings`
  - [ ] `plan_summary.max_est_rows`
  - [ ] `plan_summary.operators`

## 验收
- [ ] `before.json` 中能看到 warnings
- [ ] 能分清：
  - [ ] explain 成功但有风险
  - [ ] explain 失败

---

# 5. 实现 `index_recommender.py`

## 文件
- [ ] `recommenders/index_recommender.py`

## TODO
- [ ] 从 SQL 中提取：
  - [ ] table
  - [ ] where_cols
  - [ ] order_cols
- [ ] 先只支持简单场景：
  - [ ] 单表
  - [ ] where 等值过滤
  - [ ] order by 单列
- [ ] 生成：
  - [ ] `suggested_index_cols`
  - [ ] `candidate_ddl`
  - [ ] `confidence`
- [ ] 规则保持保守
  - [ ] where 列优先
  - [ ] order by 列其次
  - [ ] 最多 2~3 列

## 验收
- [ ] 对 `orders where user_id ... order by created_at` 生成：
  - [ ] `(user_id, created_at)` 候选
- [ ] 不会空口生成离谱超宽索引

---

# 6. 在 `cli.py` 中接入 `recommend-index`

## TODO
- [ ] 加子命令：
  - [ ] `recommend-index --sql-file --analysis-json`
- [ ] 读取 SQL 文件
- [ ] 读取 `before.json`
- [ ] 调 `index_recommender.recommend_index`
- [ ] 输出 JSON

## 验收
- [ ] 能执行：
  ```bash
  python3 cli.py recommend-index \
    --sql-file sql/sample_query.sql \
    --analysis-json reports/before.json > reports/recommendation.json
  ```
- [ ] `reports/recommendation.json` 中有 `candidate_ddl`

---

# 7. 实现 `explain_compare.py`

## 文件
- [ ] `validators/explain_compare.py`

## TODO
- [ ] 接收 before / after 两份 analysis
- [ ] 比较：
  - [ ] `before_rows`
  - [ ] `after_rows`
  - [ ] `ratio`
  - [ ] `before_ops`
  - [ ] `after_ops`
  - [ ] `improved_rows`
  - [ ] `improved_ops`
  - [ ] `verdict`

## 验收
- [ ] 能正确识别：
  - [ ] rows 下降
  - [ ] operator 从 `TableFullScan` 变成 `IndexRangeScan / IndexLookUp`

---

# 8. 实现 `tidb_index_validator.py`

## 文件
- [ ] `validators/tidb_index_validator.py`

## TODO
- [ ] 只允许对**测试库**执行
- [ ] 加 `ensure_test_db()`
- [ ] 执行候选 `CREATE INDEX`
- [ ] 跑 after explain
- [ ] 调 `explain_compare.compare_explain`
- [ ] 生成：
  - [ ] `rollback_sql`
  - [ ] `after_analysis`
  - [ ] `compare`
- [ ] 默认支持 `auto_rollback=true`

## 验收
- [ ] 能执行候选索引验证
- [ ] 能输出 `validation.json`
- [ ] 能回滚索引
- [ ] 如果不是测试库，会明确拒绝执行

---

# 9. 在 `cli.py` 中接入 `validate-index`

## TODO
- [ ] 加子命令：
  - [ ] `validate-index --sql-file --before-json --recommendation-json`
- [ ] 读取 SQL / before / recommendation
- [ ] 读取 `candidate_ddl`
- [ ] 调 `tidb_index_validator.validate_candidate_index`
- [ ] 输出 JSON

## 验收
- [ ] 能执行：
  ```bash
  python3 cli.py validate-index \
    --sql-file sql/sample_query.sql \
    --before-json reports/before.json \
    --recommendation-json reports/recommendation.json > reports/validation.json
  ```
- [ ] `reports/validation.json` 中有：
  - [ ] `candidate_ddl`
  - [ ] `rollback_sql`
  - [ ] `compare`

---

# 10. 实现 `validation_report_generator.py`

## 文件
- [ ] `reporters/validation_report_generator.py`

## TODO
- [ ] 读取：
  - [ ] `before.json`
  - [ ] `recommendation.json`
  - [ ] `validation.json`
- [ ] 生成 markdown 报告
- [ ] 报告必须包含：
  - [ ] SQL 原文
  - [ ] before warnings
  - [ ] candidate ddl
  - [ ] after summary
  - [ ] ratio
  - [ ] verdict
  - [ ] rollback sql
- [ ] 写入 `shadow_fix/`

## 验收
- [ ] 能生成：
  - [ ] `shadow_fix/sql_validation_report_<ts>.md`
- [ ] 报告人类可读，不是 JSON dump

---

# 11. 在 `cli.py` 中接入 `generate-report`

## TODO
- [ ] 加子命令：
  - [ ] `generate-report --before-json --recommendation-json --validation-json --base-dir`
- [ ] 调 `generate_validation_report()`
- [ ] 输出写入路径

## 验收
- [ ] 能执行：
  ```bash
  python3 cli.py generate-report \
    --before-json reports/before.json \
    --recommendation-json reports/recommendation.json \
    --validation-json reports/validation.json \
    --base-dir .
  ```
- [ ] `shadow_fix/` 下有最终报告

---

# 12. 跑通第一条完整链

## TODO
按顺序执行：

- [ ] `tidb-explain`
- [ ] `recommend-index`
- [ ] `validate-index`
- [ ] `generate-report`

## 最终验收
- [ ] 有 `reports/before.json`
- [ ] 有 `reports/recommendation.json`
- [ ] 有 `reports/validation.json`
- [ ] 有 `shadow_fix/sql_validation_report_<ts>.md`
- [ ] 整条链没有碰生产
- [ ] 候选索引能自动回滚
- [ ] 报告中能看出优化是否有效

---

# Phase 1 明确不做

## 禁止扩项
- [ ] 不做 watcher
- [ ] 不做 memory writeback
- [ ] 不做 recall
- [ ] 不做 orchestrator
- [ ] 不做 infra sentinel
- [ ] 不做 EXPLAIN ANALYZE
- [ ] 不做 UI
- [ ] 不做自动正式 DDL

一句话：

> **先把最小闭环跑通，再谈自感知和记忆增强。**

---

# Phase 1 Done Definition

当下面这句话成立，第一阶段就算完成：

> 给一条 SQL，系统能在测试库里验证候选索引，并产出一份可读的 markdown 报告。
