# Self-Aware R&D Hub

![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![Status](https://img.shields.io/badge/status-prototype-orange)
![Database](https://img.shields.io/badge/database-TiDB-00B3A4)

An engineering prototype for explain-driven TiDB SQL optimization validation.

> SQL feature extraction → EXPLAIN analysis → candidate index recommendation → existing-index inspection → validation gate → test-DB validation → report generation

## What this project does

Self-Aware R&D Hub turns a single SQL tuning idea into a repeatable validation workflow.

It is designed for:

- explain-driven SQL analysis
- conservative index recommendation
- gated validation in a test database
- structured report output for review

## Current scope

This project is currently a **prototype**, not a production auto-indexing system.

It is best used for:

- validating optimization ideas
- refining decision rules
- evolving a future workflow

## Key modules

- `parsers/` — SQL feature extraction
- `analyzers/` — explain signal analysis
- `inspectors/` — existing-index inspection
- `recommenders/` — candidate index recommendation
- `validators/` — gate + test-DB validation
- `reporters/` — review-friendly output
- `docs/` — architecture, canvas index, walkthrough

## Quick start

```bash
git clone git@github.com:luyuehm/self-aware-rd-hub.git
cd self-aware-rd-hub
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Architecture docs

Architecture assets for this project live under:

- `docs/README.md`
- `docs/CANVAS_INDEX.md`
- `docs/DEMO_WALKTHROUGH.md`
- `docs/canvas/`

Recommended reading order:

1. `docs/canvas/Self-Aware R&D Hub.canvas`
2. `docs/canvas/TiDB SQL Optimization Validation Loop.canvas`
3. `docs/canvas/Memory Recall Writeback Loop.canvas`
4. `docs/CANVAS_INDEX.md`
5. `docs/DEMO_WALKTHROUGH.md`

## Documentation

- `PHASE2_PLAN.md`
- `docs/README.md`
- `docs/CANVAS_INDEX.md`
- `docs/DEMO_WALKTHROUGH.md`
- `docs/ARCHITECTURE.md`

## Config

- committed example config: `config/tidb.example.yaml`
- local machine config: `config/tidb.local.yaml`
- code defaults to local first, then example


## Demo

Run the minimal end-to-end demo pipeline with one command:

```bash
python3 cli.py demo-run --sql-file sql/sample_query.sql --base-dir . --generate-report
```

This will generate:

- `reports/demo_before.json`
- `reports/demo_recommendation.json`
- `reports/demo_validation.json`
- `shadow_fix/sql_validation_report_*.md` (when `--generate-report` is enabled)
