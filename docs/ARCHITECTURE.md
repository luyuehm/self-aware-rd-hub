# Architecture

## Overview

Current prototype chain:

```text
SQL input
  -> SQL feature extraction
  -> TiDB EXPLAIN
  -> explain signal analysis
  -> candidate index recommendation
  -> existing index inspection
  -> validation gate
  -> test DB validation
  -> compare before/after
  -> report output
```

## Layers

### 1. Input layer
Entry:
- `cli.py`
- `sql/*.sql`

### 2. Parsing layer
Module:
- `parsers/sql_feature_extractor.py`

Purpose:
- convert SQL into reusable structured features

### 3. Explain execution layer
Module:
- `sentinels/tidb_explain_runner.py`

Purpose:
- run `EXPLAIN FORMAT='verbose'`
- return structured success/failure payload

### 4. Explain analysis layer
Module:
- `analyzers/explain_signal_analyzer.py`

Purpose:
- convert raw explain rows into warning signals

### 5. Recommendation layer
Module:
- `recommenders/index_recommender.py`

Purpose:
- build conservative candidate index suggestions

### 6. Existing-index inspection layer
Module:
- `inspectors/existing_index_inspector.py`

Purpose:
- inspect current indexes
- detect exact / prefix coverage

### 7. Validation gate layer
Modules:
- `validators/validation_gate.py`
- `config/validation.yaml`

Purpose:
- decide whether validation is allowed

### 8. Validation execution layer
Module:
- `validators/tidb_index_validator.py`

Purpose:
- test candidate DDL only in test DB
- auto rollback after validation

### 9. Reporting layer
Module:
- `reporters/validation_report_generator.py`

Artifacts:
- `reports/*.json`
- `shadow_fix/*.md`

## Current boundaries

Safe for:
- test DB experiments
- architecture discussion
- iterative rule refinement

Not yet safe for:
- production rollout
- autonomous DDL decisions
- workload-level optimization
- complex SQL tuning authority

## Near-term evolution

Recommended next steps:
1. real TiDB end-to-end validation
2. stronger report schema
3. memory writeback layer
4. watcher / orchestrator layer
5. richer parser and runtime-aware analysis
