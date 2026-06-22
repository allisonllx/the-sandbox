"""Validate generated challenge packages before publish."""

from __future__ import annotations

import ast
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from ..assessor.security_scan import scan_submission
from ..sandbox.validate import validate_python
from .models import ChallengeBlueprint, DataPlane, ValidationReport
from .scaffold_technical import starter_has_forbidden_patterns
from .workspace_sufficiency import check_browser_workspace_sufficiency


def _parse_pytest_summary(output: str) -> tuple[int, int, int]:
    passed = failed = 0
    for match in re.finditer(r"(\d+) passed", output):
        passed = int(match.group(1))
    for match in re.finditer(r"(\d+) failed", output):
        failed = int(match.group(1))
    total = passed + failed
    return passed, failed, total


def _syntax_check(files: dict[str, str]) -> list[str]:
    errors: list[str] = []
    for path, content in files.items():
        if not path.endswith(".py"):
            continue
        diags = validate_python(path, content)
        for diag in diags:
            errors.append(f"{path}:{diag.get('line', 1)}: {diag.get('message', 'syntax error')}")
        try:
            ast.parse(content, filename=path)
        except SyntaxError as exc:
            errors.append(f"{path}:{exc.lineno}: {exc.msg}")
    return errors


def _run_pytest(workspace: Path) -> tuple[int, str, str]:
    tests_dir = workspace / "tests"
    if not tests_dir.exists():
        return 1, "", "No tests/ directory"
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short"],
        cwd=str(workspace),
        capture_output=True,
        text=True,
        timeout=30,
    )
    return proc.returncode, proc.stdout, proc.stderr


def validate_package(
    starter_files: dict[str, str],
    reference_solution: dict[str, str],
    blueprint: ChallengeBlueprint,
    *,
    dataset_path: str | None = None,
    fixture_files: dict[str, str] | None = None,
) -> ValidationReport:
    """Run syntax, security, and pytest checks against reference solution."""
    errors: list[str] = []

    if not starter_files:
        return ValidationReport(passed=False, errors=["starter_files is empty"])

    required = {"README.md"}
    missing = required - set(starter_files.keys())
    if missing:
        errors.append(f"Missing required starter files: {sorted(missing)}")

    test_files = [p for p in starter_files if p.startswith("tests/") and p.endswith(".py")]
    if not test_files:
        errors.append("starter must include at least one tests/*.py file")

    forbidden = starter_has_forbidden_patterns(starter_files)
    if forbidden:
        errors.extend(f"starter forbidden pattern: {v}" for v in forbidden)

    errors.extend(check_browser_workspace_sufficiency(starter_files, blueprint))

    syntax_errors = _syntax_check(starter_files)
    errors.extend(syntax_errors)

    security_score, security_violations = scan_submission(starter_files)

    if errors:
        return ValidationReport(
            passed=False,
            security_score=security_score,
            security_violations=security_violations,
            errors=errors,
        )

    merged = dict(starter_files)
    for path, content in reference_solution.items():
        merged[path] = content

    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        for rel, content in merged.items():
            target = work / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")

        if blueprint.data_plane == DataPlane.sqlite and dataset_path:
            db_src = Path(dataset_path)
            if db_src.exists():
                shutil.copy(db_src, work / "sandbox.sqlite")
            else:
                errors.append(f"dataset not found: {dataset_path}")

        if fixture_files:
            for rel, content in fixture_files.items():
                target = work / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(content, encoding="utf-8")

        exit_code, stdout, stderr = _run_pytest(work)
        passed, failed, total = _parse_pytest_summary(stdout + stderr)

        if exit_code != 0 and total == 0:
            errors.append("pytest did not run any tests")
            if stderr:
                errors.append(stderr.strip()[:500])

        return ValidationReport(
            passed=exit_code == 0 and not errors,
            test_count=total,
            tests_passed=passed,
            tests_failed=failed,
            security_score=security_score,
            security_violations=security_violations,
            errors=errors,
            stdout=stdout[:4000],
            stderr=stderr[:2000],
        )
