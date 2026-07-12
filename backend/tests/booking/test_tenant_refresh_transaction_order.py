from __future__ import annotations

import ast
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2]

TENANT_SCOPED_API_FILES = [
    BACKEND_DIR / "app/api/admin/resources.py",
    BACKEND_DIR / "app/api/admin/availability.py",
    BACKEND_DIR / "app/api/internal/payments.py",
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
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
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


def test_create_availability_exception_serializes_before_commit() -> None:
    """Readable tenant data must be serialized before commit while search_path is active."""
    path = BACKEND_DIR / "app/api/admin/availability.py"
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    function = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == "create_availability_exception"
    )
    try_node = next(node for node in function.body if isinstance(node, ast.Try))

    data_assignment_line = None
    commit_line = None
    for statement in try_node.body:
        if (
            isinstance(statement, ast.Assign)
            and any(isinstance(target, ast.Name) and target.id == "data" for target in statement.targets)
            and isinstance(statement.value, ast.Call)
            and getattr(statement.value.func, "id", "") == "serialize_availability_exception"
        ):
            data_assignment_line = statement.lineno
        if _is_session_call(statement, "commit"):
            commit_line = statement.lineno

    assert data_assignment_line is not None
    assert commit_line is not None
    assert data_assignment_line < commit_line
