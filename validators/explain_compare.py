from __future__ import annotations

from typing import Any, Dict, List


def _operators(plan: Dict[str, Any]) -> List[str]:
    return plan.get("plan_summary", {}).get("operators", [])


def _max_rows(plan: Dict[str, Any]) -> float:
    return float(plan.get("plan_summary", {}).get("max_est_rows", 0) or 0)


def compare_explain(before: Dict[str, Any], after: Dict[str, Any]) -> Dict[str, Any]:
    before_rows = _max_rows(before)
    after_rows = _max_rows(after)
    before_ops = _operators(before)
    after_ops = _operators(after)

    improved_rows = after_rows < before_rows if before_rows and after_rows else False
    improved_ops = any("index" in op.lower() for op in after_ops) and any("tablescan" in op.lower() for op in before_ops)
    ratio = round(before_rows / after_rows, 2) if before_rows and after_rows else None

    return {
        "before_rows": before_rows,
        "after_rows": after_rows,
        "before_ops": before_ops,
        "after_ops": after_ops,
        "improved_rows": improved_rows,
        "improved_ops": improved_ops,
        "ratio": ratio,
        "verdict": "improved" if (improved_rows or improved_ops) else "not_clear",
    }
