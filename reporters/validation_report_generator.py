from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Dict


def _code_block(lang: str, content: str) -> str:
    return f"```{lang}\n{content}\n```"


def generate_validation_report(base_dir: str, before: Dict, recommendation: Dict, validation: Dict) -> str:
    shadow_dir = Path(base_dir) / "shadow_fix"
    shadow_dir.mkdir(parents=True, exist_ok=True)
    out = shadow_dir / f"sql_validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"

    sql = before.get("sql", "")
    before_summary = before.get("plan_summary", {})
    after_analysis = validation.get("after_analysis", {})
    after_summary = after_analysis.get("plan_summary", {})
    compare = validation.get("compare", {})
    ddl = recommendation.get("candidate_ddl")
    rollback_sql = validation.get("rollback_sql")

    lines = [
        "# SQL Validation Report",
        "",
        "## Summary",
        f"- verdict: {compare.get('verdict', validation.get('status'))}",
        f"- confidence: {recommendation.get('confidence', 'unknown')}",
        "",
        "## SQL",
        _code_block("sql", sql),
        "",
        "## Before",
        f"- warnings: {before.get('warnings', [])}",
        f"- max_est_rows: {before_summary.get('max_est_rows')}",
        f"- operators: {before_summary.get('operators')}",
        "",
        "## Recommendation",
        f"- table: {recommendation.get('table')}",
        f"- where_cols: {recommendation.get('where_cols', [])}",
        f"- order_cols: {recommendation.get('order_cols', [])}",
        f"- suggested_index_cols: {recommendation.get('suggested_index_cols', [])}",
    ]

    if ddl:
        lines += ["", "### Candidate DDL", _code_block("sql", ddl)]

    lines += [
        "",
        "## After",
        f"- warnings: {after_analysis.get('warnings', [])}",
        f"- max_est_rows: {after_summary.get('max_est_rows')}",
        f"- operators: {after_summary.get('operators')}",
        "",
        "## Compare",
        f"- before_rows: {compare.get('before_rows')}",
        f"- after_rows: {compare.get('after_rows')}",
        f"- ratio: {compare.get('ratio')}",
        f"- improved_rows: {compare.get('improved_rows')}",
        f"- improved_ops: {compare.get('improved_ops')}",
    ]

    if rollback_sql:
        lines += ["", "## Rollback", _code_block("sql", rollback_sql)]

    lines += [
        "",
        "## Notes",
        "- 本报告仅基于测试/开发环境验证结果。",
        "- 不应直接据此在生产环境执行 DDL，仍需人工确认。",
    ]

    out.write_text("\n".join(lines), encoding="utf-8")
    return str(out)
