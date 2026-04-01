from __future__ import annotations

from typing import Any, Dict

from sentinels.sql_performance_guardian import analyze_tidb_explain
from validators.explain_compare import compare_explain


def ensure_test_db(current_db: str, expected_db: str):
    if current_db != expected_db:
        raise RuntimeError(f"Refusing validation: current db={current_db}, expected test db={expected_db}")


def _execute_sql(conn, sql: str):
    with conn.cursor() as cur:
        cur.execute(sql)
    conn.commit()


def _run_explain(conn, sql: str):
    with conn.cursor() as cur:
        cur.execute(f"EXPLAIN FORMAT='verbose' {sql.strip().rstrip(';')}")
        return cur.fetchall()


def validate_candidate_index(conn, sql: str, candidate_ddl: str, expected_db: str, before_analysis: Dict[str, Any], auto_rollback: bool = True) -> Dict[str, Any]:
    rollback_sql = None
    created = False

    with conn.cursor() as cur:
        cur.execute("SELECT DATABASE() AS db")
        row = cur.fetchone()
        current_db = row["db"] if row else None

    ensure_test_db(current_db, expected_db)

    try:
        _execute_sql(conn, candidate_ddl)
        created = True

        parts = candidate_ddl.strip().split()
        index_name = parts[2]
        table_name = parts[4].split("(")[0]
        rollback_sql = f"DROP INDEX {index_name} ON {table_name};"

        raw_after = {
            "kind": "tidb_explain",
            "status": "ok",
            "sql": sql.strip().rstrip(";"),
            "rows": _run_explain(conn, sql),
            "risk": "L1",
        }
        after_analysis = analyze_tidb_explain(raw_after)
        after_analysis["sql"] = raw_after["sql"]
        after_analysis["raw_explain"] = raw_after

        return {
            "status": "ok",
            "candidate_ddl": candidate_ddl,
            "rollback_sql": rollback_sql,
            "after_analysis": after_analysis,
            "compare": compare_explain(before_analysis, after_analysis),
            "created": created,
        }
    finally:
        if auto_rollback and created and rollback_sql:
            _execute_sql(conn, rollback_sql)
