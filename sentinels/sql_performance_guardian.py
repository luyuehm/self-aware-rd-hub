from __future__ import annotations

from typing import Any, Dict, List


def analyze_tidb_explain(explain_result: Dict[str, Any]) -> Dict[str, Any]:
    if explain_result.get("status") != "ok":
        return {
            "kind": "sql_check",
            "status": "fail",
            "warnings": ["explain_failed"],
            "error": explain_result.get("error"),
            "plan_summary": {"max_est_rows": 0, "operators": []},
            "risk": "L1",
        }

    rows = explain_result.get("rows", [])
    operators: List[str] = []
    max_est_rows = 0.0
    warnings: List[str] = []

    for row in rows:
        op = str(row.get("id") or row.get("operator info") or row.get("task") or "")
        if op:
            operators.append(op)
        est = row.get("estRows") or 0
        try:
            max_est_rows = max(max_est_rows, float(est or 0))
        except Exception:
            pass

    joined = " ".join(operators).lower()
    if "tablescan" in joined:
        warnings.append("full_table_scan")
    if max_est_rows >= 100000:
        warnings.append("high_row_scan")
    if "index" not in joined:
        warnings.append("index_not_used")

    return {
        "kind": "sql_check",
        "status": "warn" if warnings else "ok",
        "warnings": warnings,
        "plan_summary": {
            "max_est_rows": max_est_rows,
            "operators": operators,
        },
        "risk": "L1",
    }
