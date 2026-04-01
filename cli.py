#!/usr/bin/env python3
"""Self-Aware R&D Hub Phase 2 CLI"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict

import yaml

from reporters.validation_report_generator import generate_validation_report
from sentinels.tidb_explain_runner import get_connection, load_tidb_config, run_explain
from validators.tidb_index_validator import validate_candidate_index

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


def _read_sql(path: str) -> str:
    return Path(path).read_text(encoding="utf-8").strip()


def _run_before_analysis(sql: str) -> Dict[str, Any]:
    features = extract_sql_features(sql)
    explain_result = run_explain(sql)
    signals = analyze_explain_signals(explain_result)
    return {
        "version": "phase2.v1",
        "kind": "before_analysis",
        "sql": features["sql"],
        "sql_features": features,
        "signals": signals,
        "raw_explain": explain_result,
    }


def _run_recommendation(sql: str, before: Dict[str, Any]) -> Dict[str, Any]:
    features = extract_sql_features(sql)
    signals = before.get("signals", {})
    return {"version": "phase2.v1", "kind": "recommendation", **recommend_index_v2(features, signals)}


def _run_validation(sql: str, before: Dict[str, Any], rec: Dict[str, Any]) -> Dict[str, Any]:
    ddl = rec.get("candidate_ddl")
    if not ddl:
        return {
            "version": "phase2.v1",
            "kind": "validation",
            "status": "skip",
            "reason": "no_candidate_ddl",
        }

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
            return {
                "version": "phase2.v1",
                "kind": "validation",
                "status": gate["action"],
                "reason": gate["reason"],
                "risk_level": gate["risk_level"],
                "gate": gate,
                "coverage": coverage,
                "existing_indexes": existing,
            }

        signals = before.get("signals", {})
        result = validate_candidate_index(
            conn=conn,
            sql=sql,
            candidate_ddl=ddl,
            expected_db=cfg["database"],
            before_analysis=signals,
            auto_rollback=val_cfg.get("auto_rollback", True),
        )
        return {
            "version": "phase2.v1",
            "kind": "validation",
            "gate": gate,
            "coverage": coverage,
            "existing_indexes": existing,
            **result,
        }
    finally:
        conn.close()


def cmd_tidb_explain(args: argparse.Namespace) -> None:
    _out(_run_before_analysis(_read_sql(args.sql_file)))


def cmd_recommend_index(args: argparse.Namespace) -> None:
    sql = _read_sql(args.sql_file)
    before = json.loads(Path(args.analysis_json).read_text(encoding="utf-8"))
    _out(_run_recommendation(sql, before))


def cmd_inspect_indexes(args: argparse.Namespace) -> None:
    cfg = load_tidb_config()
    conn = get_connection(cfg)
    try:
        _out(inspect_existing_indexes(conn, args.table))
    finally:
        conn.close()


def cmd_validate_index(args: argparse.Namespace) -> None:
    sql = _read_sql(args.sql_file)
    before = json.loads(Path(args.before_json).read_text(encoding="utf-8"))
    rec = json.loads(Path(args.recommendation_json).read_text(encoding="utf-8"))
    _out(_run_validation(sql, before, rec))


def cmd_generate_report(args: argparse.Namespace) -> None:
    before = json.loads(Path(args.before_json).read_text(encoding="utf-8"))
    rec = json.loads(Path(args.recommendation_json).read_text(encoding="utf-8"))
    val = json.loads(Path(args.validation_json).read_text(encoding="utf-8"))
    report_path = generate_validation_report(
        base_dir=args.base_dir,
        before=before,
        recommendation=rec,
        validation=val,
    )
    _out({"kind": "report", "status": "ok", "report_path": report_path})


def cmd_demo_run(args: argparse.Namespace) -> None:
    sql = _read_sql(args.sql_file)
    base_dir = Path(args.base_dir)
    reports_dir = base_dir / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    before = _run_before_analysis(sql)
    rec = _run_recommendation(sql, before)
    val = _run_validation(sql, before, rec)

    before_path = reports_dir / "demo_before.json"
    rec_path = reports_dir / "demo_recommendation.json"
    val_path = reports_dir / "demo_validation.json"

    before_path.write_text(json.dumps(before, ensure_ascii=False, indent=2), encoding="utf-8")
    rec_path.write_text(json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8")
    val_path.write_text(json.dumps(val, ensure_ascii=False, indent=2), encoding="utf-8")

    report_path = None
    if args.generate_report:
        report_path = generate_validation_report(
            base_dir=str(base_dir),
            before=before,
            recommendation=rec,
            validation=val,
        )

    _out({
        "kind": "demo_run",
        "status": "ok",
        "sql_file": args.sql_file,
        "before_json": str(before_path),
        "recommendation_json": str(rec_path),
        "validation_json": str(val_path),
        "report_path": report_path,
        "summary": {
            "signals": before.get("signals", {}).get("signals", []),
            "candidate_ddl": rec.get("candidate_ddl"),
            "validation_status": val.get("status"),
            "validation_reason": val.get("reason"),
        },
    })


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

    p6 = sub.add_parser("demo-run")
    p6.add_argument("--sql-file", required=True)
    p6.add_argument("--base-dir", default=".")
    p6.add_argument("--generate-report", action="store_true")

    args = p.parse_args()
    dispatch = {
        "tidb-explain": cmd_tidb_explain,
        "recommend-index": cmd_recommend_index,
        "inspect-indexes": cmd_inspect_indexes,
        "validate-index": cmd_validate_index,
        "generate-report": cmd_generate_report,
        "demo-run": cmd_demo_run,
    }
    if args.cmd not in dispatch:
        p.print_help()
        return
    dispatch[args.cmd](args)


if __name__ == "__main__":
    main()
