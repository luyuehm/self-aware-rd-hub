from __future__ import annotations

import re
from typing import Any, Dict, List


def _normalize_sql(sql: str) -> str:
    return " ".join(sql.strip().rstrip(";").split())


def _extract_tables(sql: str) -> List[str]:
    return re.findall(r"from\s+([a-zA-Z_][\w\.]*)", sql, re.IGNORECASE)


def _extract_where_cols(sql: str) -> List[str]:
    m = re.search(
        r"where\s+(.+?)(?:\s+order\s+by|\s+group\s+by|\s+limit|$)",
        sql, re.IGNORECASE | re.DOTALL,
    )
    if not m:
        return []
    cols: List[str] = []
    for name, _op in re.findall(
        r"([a-zA-Z_][\w\.]*)\s*(=|in|like|>|<|>=|<=)", m.group(1), re.IGNORECASE
    ):
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


def _extract_limit(sql: str) -> int | None:
    m = re.search(r"limit\s+(\d+)", sql, re.IGNORECASE)
    return int(m.group(1)) if m else None


def extract_sql_features(sql: str) -> Dict[str, Any]:
    normalized = _normalize_sql(sql)
    tables = _extract_tables(normalized)
    return {
        "kind": "sql_features",
        "sql": normalized,
        "tables": tables,
        "primary_table": tables[0] if tables else None,
        "where_cols": _extract_where_cols(normalized),
        "order_cols": _extract_order_cols(normalized),
        "join_cols": [],
        "limit": _extract_limit(normalized),
    }
