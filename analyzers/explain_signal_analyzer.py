from __future__ import annotations

from typing import Any, Dict, List


def _extract_operators(rows: List[Dict[str, Any]]) -> List[str]:
    ops: List[str] = []
    for row in rows:
        op = str(row.get("id") or "")
        if op:
            ops.append(op)
    return ops


def _extract_max_est_rows(rows: List[Dict[str, Any]]) -> float:
    max_rows = 0.0
    for row in rows:
        try:
            max_rows = max(max_rows, float(row.get("estRows") or 0))
        except Exception:
            pass
    return max_rows


def _classify_scan_type(operators: List[str]) -> str:
    joined = " ".join(operators).lower()
    if "tablefullscan" in joined or ("tablescan" in joined and "index" not in joined):
        return "full_table_scan"
    if "indexrangescan" in joined:
        return "index_range_scan"
    if "indexlookup" in joined:
        return "index_lookup"
    if "point_get" in joined:
        return "point_get"
    return "unknown"


def _uses_index(operators: List[str]) -> bool:
    return "index" in " ".join(operators).lower()


def _sort_risk(sql: str, operators: List[str]) -> bool:
    has_order_by = " order by " in f" {sql.lower()} "
    if not has_order_by:
        return False
    joined = " ".join(operators).lower()
    return "indexrangescan" not in joined and "indexlookup" not in joined


def analyze_explain_signals(raw_explain: Dict[str, Any]) -> Dict[str, Any]:
    if raw_explain.get("status") != "ok":
        return {
            "kind": "explain_signals",
            "status": "fail",
            "signals": ["explain_failed"],
            "scan_type": "unknown",
            "uses_index": False,
            "sort_risk": False,
            "max_est_rows": 0,
            "operators": [],
            "error": raw_explain.get("error"),
        }

    rows = raw_explain.get("rows", [])
    sql = raw_explain.get("sql", "")
    operators = _extract_operators(rows)
    max_est_rows = _extract_max_est_rows(rows)
    scan_type = _classify_scan_type(operators)
    uses_index = _uses_index(operators)
    sort_risk = _sort_risk(sql, operators)

    signals: List[str] = []
    if scan_type == "full_table_scan":
        signals.append("full_table_scan")
    if max_est_rows >= 100_000:
        signals.append("high_row_scan")
    if not uses_index:
        signals.append("index_not_used")
    if sort_risk:
        signals.append("sort_risk")

    return {
        "kind": "explain_signals",
        "status": "warn" if signals else "ok",
        "signals": signals,
        "scan_type": scan_type,
        "uses_index": uses_index,
        "sort_risk": sort_risk,
        "max_est_rows": max_est_rows,
        "operators": operators,
    }
