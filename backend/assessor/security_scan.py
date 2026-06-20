"""Static security scan on submitted source — runs before container execution."""

from __future__ import annotations

import re

_FORBIDDEN: list[tuple[str, str]] = [
    (r"\bos\.system\s*\(", "os.system"),
    (r"\bsubprocess\.(run|Popen|call)\([^)]*shell\s*=\s*True", "subprocess with shell=True"),
    (r"\beval\s*\(", "eval()"),
    (r"\bexec\s*\(", "exec()"),
    (r"__import__\s*\(", "__import__"),
    (r"open\s*\(\s*['\"]/?etc/", "reading /etc"),
    (r"socket\.socket\s*\(", "raw socket"),
]


def scan_submission(files: dict[str, str]) -> tuple[int, list[str]]:
    """
    Return (security_baseline_score 0–100, violation messages).

    Scans Python sources only — track-standard baseline, not sponsor taste.
    """
    violations: list[str] = []
    py_files = [p for p in files if p.endswith(".py")]

    if not py_files:
        return 50, ["No Python files in submission for security scan."]

    for path in py_files:
        content = files[path]
        for pattern, label in _FORBIDDEN:
            if re.search(pattern, content):
                violations.append(f"{path}: forbidden pattern {label}")

    if not violations:
        return 100, []

    # Deduct 25 points per violation, floor at 0
    score = max(0, 100 - 25 * len(violations))
    return score, violations
