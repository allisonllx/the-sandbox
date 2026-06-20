"""Lightweight Python syntax validation for Monaco live diagnostics."""

from __future__ import annotations

import ast
import py_compile
import tempfile
from pathlib import Path


def validate_python(path: str, content: str) -> list[dict]:
    """Return Monaco-compatible diagnostics for *content*."""
    if not path.endswith(".py"):
        return []

    diagnostics: list[dict] = []

    try:
        ast.parse(content, filename=path)
    except SyntaxError as exc:
        diagnostics.append(
            {
                "line": exc.lineno or 1,
                "column": (exc.offset or 1),
                "message": exc.msg or "Syntax error",
                "severity": "error",
            }
        )
        return diagnostics

    with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as tmp:
        tmp_path = Path(tmp.name)
        tmp.write(content.encode("utf-8"))

    try:
        py_compile.compile(str(tmp_path), doraise=True)
    except py_compile.PyCompileError as exc:
        diagnostics.append(
            {
                "line": 1,
                "column": 1,
                "message": str(exc),
                "severity": "error",
            }
        )
    finally:
        tmp_path.unlink(missing_ok=True)

    return diagnostics
