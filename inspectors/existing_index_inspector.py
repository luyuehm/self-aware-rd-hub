from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, List


def inspect_existing_indexes(conn, table: str) -> Dict[str, Any]:
    query = """
    SELECT INDEX_NAME, COLUMN_NAME, SEQ_IN_INDEX, NON_UNIQUE
    FROM information_schema.statistics
    WHERE table_schema = DATABASE() AND table_name = %s
    ORDER BY INDEX_NAME, SEQ_IN_INDEX
    """
    grouped: Dict[str, List[str]] = defaultdict(list)
    uniqueness: Dict[str, str] = {}

    with conn.cursor() as cur:
        cur.execute(query, (table,))
        for row in cur.fetchall():
            name = row["INDEX_NAME"]
            grouped[name].append(row["COLUMN_NAME"])
            uniqueness[name] = "non_unique" if row["NON_UNIQUE"] else "unique"

    indexes = [
        {"index_name": k, "columns": v, "uniqueness": uniqueness[k]}
        for k, v in grouped.items()
    ]
    return {"kind": "existing_indexes", "table": table, "indexes": indexes}


def check_candidate_coverage(
    existing_index_info: Dict[str, Any], candidate_cols: List[str]
) -> Dict[str, Any]:
    candidate = list(candidate_cols)
    exact_match = None
    prefix_match = None

    for idx in existing_index_info.get("indexes", []):
        cols = idx["columns"]
        if cols == candidate:
            exact_match = idx
            break
        if len(cols) >= len(candidate) and cols[: len(candidate)] == candidate:
            prefix_match = idx

    if exact_match:
        return {
            "kind": "index_coverage",
            "status": "exact_exists",
            "matched_index": exact_match["index_name"],
            "matched_columns": exact_match["columns"],
            "action": "skip",
        }
    if prefix_match:
        return {
            "kind": "index_coverage",
            "status": "prefix_covered",
            "matched_index": prefix_match["index_name"],
            "matched_columns": prefix_match["columns"],
            "action": "review",
        }
    return {
        "kind": "index_coverage",
        "status": "not_covered",
        "matched_index": None,
        "matched_columns": [],
        "action": "allow",
    }
