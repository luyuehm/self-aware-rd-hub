# Phase 2 Plan

## Goal

Phase 2 turns the current SQL optimization prototype into a more structured engineering prototype.

Core additions:
- shared SQL feature extraction
- structured explain signal analysis
- existing index inspection
- validation gate
- clearer JSON artifacts

## Why this phase exists

Phase 1 proved the basic loop could run:

```text
SQL -> explain -> recommend -> validate -> report
```

But Phase 1 still lacked:
- shared parsing
- explicit gate logic
- existing-index inspection
- consistent output structure

## Phase 2 modules

### `parsers/sql_feature_extractor.py`
- normalize SQL
- extract table / where / order / limit

### `analyzers/explain_signal_analyzer.py`
- classify scan type
- extract warning signals
- detect explain failure

### `inspectors/existing_index_inspector.py`
- inspect current indexes
- check exact / prefix coverage

### `validators/validation_gate.py`
- centralize validation policy
- reject wrong DB / denied table / too many columns
- skip exact-existing candidates

### `config/validation.yaml`
- store gate policy in config

## CLI wiring

### `tidb-explain`
```text
sql -> feature extraction -> explain -> signal analysis -> before.json
```

### `recommend-index`
```text
sql + before.json -> recommendation.json
```

### `inspect-indexes`
```text
table -> index snapshot
```

### `validate-index`
```text
sql + before.json + recommendation.json -> coverage -> gate -> validation.json
```

### `generate-report`
```text
before + recommendation + validation -> markdown artifact
```

## Key outputs

### `reports/before.json`
- sql features
- explain signals
- raw explain result

### `reports/recommendation.json`
- target table
- candidate columns
- candidate DDL
- confidence

### `reports/validation.json`
- gate result
- coverage result
- existing indexes
- validation verdict

## Acceptance status

Offline checks completed:
- sql feature extraction
- explain signal analyzer
- existing index inspector
- validation gate
- negative path (`no_candidate_ddl`)

Still pending:
- real TiDB end-to-end validation
- stronger report metadata
- memory writeback loop
- batch / watcher / orchestrator layer
