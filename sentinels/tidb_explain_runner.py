from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import pymysql
import yaml


CONFIG_PATH = Path(__file__).resolve().parents[1] / "config" / "tidb.yaml"


def load_tidb_config(path: str | None = None) -> Dict[str, Any]:
    cfg_path = Path(path) if path else CONFIG_PATH
    return yaml.safe_load(cfg_path.read_text(encoding="utf-8"))


def get_connection(config: Dict[str, Any]):
    return pymysql.connect(
        host=config["host"],
        port=int(config.get("port", 4000)),
        user=config["user"],
        password=config.get("password", ""),
        database=config["database"],
        connect_timeout=int(config.get("connect_timeout", 5)),
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True,
    )


def run_explain(sql: str, config_path: str | None = None) -> Dict[str, Any]:
    sql = sql.strip().rstrip(";")
    config = load_tidb_config(config_path)

    try:
        conn = get_connection(config)
        with conn.cursor() as cur:
            cur.execute(f"EXPLAIN FORMAT='verbose' {sql}")
            rows = cur.fetchall()
        conn.close()
        return {
            "kind": "tidb_explain",
            "status": "ok",
            "sql": sql,
            "rows": rows,
            "risk": "L1",
        }
    except Exception as e:
        return {
            "kind": "tidb_explain",
            "status": "fail",
            "sql": sql,
            "error": str(e),
            "risk": "L1",
        }
