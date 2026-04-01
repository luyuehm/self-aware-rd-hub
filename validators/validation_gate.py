from __future__ import annotations

from typing import Any, Dict, List


def _risk_level(candidate_cols: List[str], policy: Dict[str, str]) -> str:
    n = len(candidate_cols)
    if n <= 1:
        return policy.get("single_column", "low")
    if n == 2:
        return policy.get("two_columns", "medium")
    if n == 3:
        return policy.get("three_columns", "medium")
    return policy.get("more_than_three", "high")


def evaluate_validation_gate(
    *,
    current_db: str,
    expected_db: str,
    table: str,
    candidate_cols: List[str],
    index_coverage: Dict[str, Any],
    config: Dict[str, Any],
) -> Dict[str, Any]:
    policy = config.get("risk_policy", {})
    risk = _risk_level(candidate_cols, policy)

    def deny(reason: str, action: str = "deny") -> Dict[str, Any]:
        return {"kind": "validation_gate", "allowed": False,
                "reason": reason, "risk_level": risk, "action": action}

    if config.get("require_test_db", True) and current_db != expected_db:
        return deny("wrong_database")
    if not config.get("allow_create_index", False):
        return deny("create_index_disabled")

    denylist = config.get("table_denylist", [])
    if denylist and table in denylist:
        return deny("table_denied")

    allowlist = config.get("table_allowlist", [])
    if allowlist and table not in allowlist:
        return deny("table_not_allowlisted")

    max_cols = int(config.get("max_index_columns", 3))
    if len(candidate_cols) > max_cols:
        return deny("too_many_index_columns")

    coverage_status = index_coverage.get("status")
    if coverage_status == "exact_exists" and config.get("skip_if_exact_index_exists", True):
        return deny("exact_index_exists", action="skip")
    if coverage_status == "prefix_covered" and config.get("skip_if_prefix_covered", False):
        return deny("prefix_covered", action="skip")

    return {"kind": "validation_gate", "allowed": True,
            "reason": "passed", "risk_level": risk, "action": "validate"}
