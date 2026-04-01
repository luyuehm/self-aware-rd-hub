#!/usr/bin/env python3
"""Self-Aware R&D Hub Phase 2 CLI"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict

import yaml

# ── existing modules ──────────────────────────────────────
from reporters.validation_report_generator import generate_validation_report
from sentinels.tidb_explain_runner import get_connection, load_tidb_config, run_explain
from validators.tidb_index_validator import validate_candidate_index

# ── phase 2 modules ───────────────────────────────────────
from analyzers.explain_signal_analyzer import analyze_explain_signals
from inspectors.existing_index_inspector import (
    check_candidate_coverage,
    inspect_existing_indexes,
)
from parsers.sql_feature_extractor import extract_sql_features
from recommenders.index_recommender import recommend_index_v2
from validators.validation_gate import evaluate_validation_gate

_VALIDATION_CFG_PATH = Path(__file__).resolve().parent / "config" / "validation.yaml"
_DEFAULT_VALIDATION_CFG: Dict[str, Any] = {
    "require_test_db": True,
    "allow_create_index": True,
    "auto_rollback": True,
    "max_index_columns": 3,
    "skip_if_exact_index_exists": True,
    "skip_if_prefix_covered": False,
    "table_allowlist": [],
    "table_denylist": [],
    "risk_policy": {
        "single_column": "low",
        "two_columns": "medium",
        "three_columns": "medium",
        "more_than_three": "high",
    },
}


def _load_validation_config() -> Dict[str, Any]:
    if _VALIDATION_CFG_PATH.exists():
        return yaml.safe_load(_VALIDATION_CFG_PATH.read_text(encoding="utf-8"))
    return _DEFAULT_VALIDATION_CFG


def _out(obj: Any) -> None:
    print(json.dumps(obj, ensure_ascii=False, indent=2, default=str))


def cmd_tidb_explain(args: argparse.Namespace) -> None:
    sql = Path(args.sql_file).read_text(encoding="utf-8").strip()
    features = extract_sql_features(sql)
    explain_result = run_explain(sql)
    signals = analyze_explain_signals(explain_result)
    _out({
        "version": "phase2.v1",
        "kind": "before_analysis",
        "sql": features["sql"],
        "sql_features": features,
        "signals": signals,
        "raw_explain": explain_result,
    })


def cmd_recommend_index(args: argparse.Namespace) -> None:
    sql = Path(args.sql_file).read_text(encoding="utf-8").strip()
    before = json.loads(Path(args.analysis_json).read_text(encoding="utf-8"))
    features = extract_sql_features(sql)
    signals = before.get("signals", {})
    rec = recommend_index_v2(features, signals)
    _out({"version": "phase2.v1", "kind": "recommendation", **rec})


def cmd_inspect_indexes(args: argparse.Namespace) -> None:
    cfg = load_tidb_config()
    conn = get_connection(cfg)
    try:
        _out(inspect_existing_indexes(conn, args.table))
    finally:
        conn.close()


def cmd_validate_index(args: argparse.Namespace) -> None:
    sql = Path(args.sql_file).read_text(encoding="utf-8").strip()
    before = json.loads(Path(args.before_json).read_text(encoding="utf-8"))
    rec = json.loads(Path(args.recommendation_json).read_text(encoding="utf-8"))
    ddl = rec.get("candidate_ddl")

    if not ddl:
        _out({"version": "phase2.v1", "kind": "validation",
              "status": "skip", "reason": "no_candidate_ddl"})
        return

    features = extract_sql_features(sql)
    candidate_cols = rec.get("suggested_index_cols", [])
    table = rec.get("table") or features.get("primary_table") or ""
    val_cfg = _load_validation_config()
    cfg = load_tidb_config()
    conn = get_connection(cfg)

    try:
        existing = inspect_existing_indexes(conn, table)
        coverage = check_candidate_coverage(existing, candidate_cols)
        gate = evaluate_validation_gate(
            current_db=cfg["database"],
            expected_db=cfg["database"],
            table=table,
            candidate_cols=candidate_cols,
            index_coverage=coverage,
            config=val_cfg,
        )

        if not gate["allowed"]:
            _out({
                "version": "phase2.v1", "kind": "validation",
                "status": gate["action"], "reason": gate["reason"],
                "risk_level": gate["risk_level"],
                "gate": gate, "coverage": coverage,
                "existing_indexes": existing,
            })
            return

        signals = before.get("signals", {})
        result = validate_candidate_index(
            conn=conn, sql=sql, candidate_ddl=ddl,
            expected_db=cfg["database"],
            before_analysis=signals,
            auto_rollback=val_cfg.get("auto_rollback", True),
        )
        _out({
            "version": "phase2.v1", "kind": "validation",
            "gate": gate, "coverage": coverage,
            "existing_indexes": existing,
            **result,
        })
    finally:
        conn.close()


def cmd_generate_report(args: argparse.Namespace) -> None:
    before = json.loads(Path(args.before_json).read_text(encoding="utf-8"))
    rec = json.loads(Path(args.recommendation_json).read_text(encoding="utf-8"))
    val = json.loads(Path(args.validation_json).read_text(encoding="utf-8"))
    generate_validation_report(
        before_analysis=before,
        recommendation=rec,
        validation_result=val,
        base_dir=args.base_dir,
    )


def main() -> None:
    p = argparse.ArgumentParser(description="Self-Aware R&D Hub Phase 2 CLI")
    sub = p.add_subparsers(dest="cmd")

    p1 = sub.add_parser("tidb-explain")
    p1.add_argument("--sql-file", required=True)

    p2 = sub.add_parser("recommend-index")
    p2.add_argument("--sql-file", required=True)
    p2.add_argument("--analysis-json", required=True)

    p3 = sub.add_parser("inspect-indexes")
    p3.add_argument("--table", required=True)

    p4 = sub.add_parser("validate-index")
    p4.add_argument("--sql-file", required=True)
    p4.add_argument("--before-json", required=True)
    p4.add_argument("--recommendation-json", required=True)

    p5 = sub.add_parser("generate-report")
    p5.add_argument("--before-json", required=True)
    p5.add_argument("--recommendation-json", required=True)
    p5.add_argument("--validation-json", required=True)
    p5.add_argument("--base-dir", default=".")

    args = p.parse_args()
    dispatch = {
        "tidb-explain": cmd_tidb_explain,
        "recommend-index": cmd_recommend_index,
        "inspect-indexes": cmd_inspect_indexes,
        "validate-index": cmd_validate_index,
        "generate-report": cmd_generate_report,
    }
    if args.cmd not in dispatch:
        p.print_help()
        return
    dispatch[args.cmd](args)


if __name__ == "__main__":
    main()
