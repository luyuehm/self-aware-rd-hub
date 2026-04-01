from __future__ import annotations

import re
from typing import Any, Dict, List


def _extract_table(sql: str) -> str:
    m = re.search(r"from\s+([a-zA-Z_][\w]*)", sql, re.IGNORECASE)
    return m.group(1) if m else "your_table"


def _extract_where_cols(sql: str) -> List[str]:
    m = re.search(r"where\s+(.+?)(?:\s+order\s+by|\s+group\s+by|\s+limit|$)", sql, re.IGNORECASE | re.DOTALL)
    if not m:
        return []
    clause = m.group(1)
    cols: List[str] = []
    for name, _op in re.findall(r"([a-zA-Z_][\w\.]*)\s*(=|in|like|>|<|>=|<=)", clause, re.IGNORECASE):
        col = name.split(".")[-1]
        if col not in cols:
            cols.append(col)
    return cols


def _extract_order_cols(sql: str) -> List[str]:
    m = re.search(r"order\s+by\s+(.+?)(?:\s+limit|$)", sql, re.IGNORECASE | re.DOTALL)
    if not m:
        return []
    cols: List[str] = []
    for part in m.group(1).split(","):
        token = part.strip().split()[0]
        col = token.split(".")[-1]
        if col not in cols:
            cols.append(col)
    return cols


def recommend_index(sql: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
    table = _extract_table(sql)
    where_cols = _extract_where_cols(sql)
    order_cols = _extract_order_cols(sql)
    warnings = analysis.get("warnings", [])

    suggested: List[str] = []
    for col in where_cols + order_cols:
        if col not in suggested:
            suggested.append(col)

    candidate_ddl = None
    if suggested and any(w in warnings for w in ["full_table_scan", "high_row_scan", "index_not_used"]):
        cols = suggested[:3]
        idx_name = f"idx_{table}_{'_'.join(cols)}"
        candidate_ddl = f"CREATE INDEX {idx_name} ON {table}({', '.join(cols)});"

    return {
        "table": table,
        "where_cols": where_cols,
        "order_cols": order_cols,
        "suggested_index_cols": suggested[:3],
        "candidate_ddl": candidate_ddl,
        "confidence": "medium" if candidate_ddl else "low",
    }


def recommend_index_v2(features: dict, signals: dict) -> dict:
    """Phase 2 recommender: uses pre-extracted features + signal dict."""
    table = features.get("primary_table") or "unknown_table"
    where_cols = features.get("where_cols", [])
    order_cols = features.get("order_cols", [])
    warning_signals = signals.get("signals", [])

    suggested: list = []
    for col in where_cols + order_cols:
        if col not in suggested:
            suggested.append(col)

    candidate_ddl = None
    if suggested and any(
        s in warning_signals
        for s in ["full_table_scan", "high_row_scan", "index_not_used"]
    ):
        cols = suggested[:3]
        idx_name = f"idx_{table}_{'_'.join(cols)}"
        candidate_ddl = f"CREATE INDEX {idx_name} ON {table}({', '.join(cols)});"

    return {
        "table": table,
        "where_cols": where_cols,
        "order_cols": order_cols,
        "suggested_index_cols": suggested[:3],
        "candidate_ddl": candidate_ddl,
        "confidence": "medium" if candidate_ddl else "low",
    }
