from __future__ import annotations

import ast
from pathlib import Path

TENANT_SCOPED_API_FILES = [
    Path("backend/app/api/admin/resources.py"),
    Path("backend/app/api/admin/availability.py"),
    Path("backend/app/api/internal/payments.py"),
]


def _is_session_call(node: ast.AST, method: str) -> bool:
    return (
        isinstance(node, ast.Expr)
        and isinstance(node.value, ast.Call)
        and isinstance(node.value.func, ast.Attribute)
        and node.value.func.attr == method
        and isinstance(node.value.func.value, ast.Name)
        and node.value.func.value.id == "session"
    )


def test_tenant_scoped_refreshes_happen_before_commit() -> None:
    """SET LOCAL search_path is transaction-scoped, so refresh must not run after commit."""
    violations: list[str] = []
    for path in TENANT_SCOPED_API_FILES:
        tree = ast.parse(path.read_text(), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Try):
                continue
            commit_seen = False
            for statement in node.body:
                if _is_session_call(statement, "commit"):
                    commit_seen = True
                if _is_session_call(statement, "refresh") and commit_seen:
                    violations.append(f"{path}:{statement.lineno}")

    assert not violations, "session.refresh() must stay before session.commit() for tenant-scoped endpoints: " + ", ".join(violations)
