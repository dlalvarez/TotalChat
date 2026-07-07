#!/usr/bin/env python3
"""Validate TotalChat SDD governance structure.

This check is intentionally conservative: it verifies that required governance
files are present and that local/generated artifacts are not accidentally
tracked or staged for commit.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_PATHS = [
    "README.md",
    "backend/pyproject.toml",
    "docs/CONSTITUTION.md",
    "docs/ROADMAP.md",
    "docs/DECISIONS.md",
    "docs/ACCEPTED_DEVIATIONS.md",
    "docs/IMPLEMENTATION_SEQUENCE.md",
    "specs",
]

REQUIRED_SPEC_FILES = ("spec.md", "plan.md", "tasks.md")

FORBIDDEN_PARTS = {
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    ".venv",
    "__pycache__",
    "build",
    "coverage",
    "dist",
    "htmlcov",
    "node_modules",
}

FORBIDDEN_NAMES = {
    ".coverage",
    ".env",
    ".env.local",
    ".DS_Store",
}

FORBIDDEN_SUFFIXES = (".log", ".pyc", ".pyo")


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def git_paths(args: list[str]) -> list[Path]:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=ROOT,
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []

    return [ROOT / line for line in result.stdout.splitlines() if line]


def is_forbidden(path: Path) -> bool:
    rel_path = path.relative_to(ROOT)
    return (
        any(part in FORBIDDEN_PARTS for part in rel_path.parts)
        or path.name in FORBIDDEN_NAMES
        or path.suffix in FORBIDDEN_SUFFIXES
    )


def check_required_paths(errors: list[str]) -> None:
    for required in REQUIRED_PATHS:
        path = ROOT / required
        if not path.exists():
            errors.append(f"Missing required path: {required}")


def check_specs(errors: list[str]) -> None:
    specs_dir = ROOT / "specs"
    if not specs_dir.is_dir():
        return

    spec_folders = [path for path in specs_dir.iterdir() if path.is_dir()]
    if not spec_folders:
        errors.append("Specs directory exists but contains no spec folders")
        return

    for folder in sorted(spec_folders):
        for required_file in REQUIRED_SPEC_FILES:
            spec_file = folder / required_file
            if not spec_file.is_file():
                errors.append(f"Missing {required_file} in {rel(folder)}")


def check_forbidden_git_paths(errors: list[str]) -> None:
    tracked = git_paths(["ls-files"])
    staged = git_paths(["diff", "--cached", "--name-only"])

    forbidden_tracked = sorted(rel(path) for path in tracked if is_forbidden(path))
    forbidden_staged = sorted(rel(path) for path in staged if is_forbidden(path))

    if forbidden_tracked:
        errors.append("Forbidden tracked files found: " + ", ".join(forbidden_tracked))
    if forbidden_staged:
        errors.append("Forbidden staged files found: " + ", ".join(forbidden_staged))


def main() -> int:
    errors: list[str] = []

    check_required_paths(errors)
    check_specs(errors)
    check_forbidden_git_paths(errors)

    if errors:
        print("SDD scope check failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("SDD scope check passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
