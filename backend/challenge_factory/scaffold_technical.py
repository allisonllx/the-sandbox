"""Blueprint-driven technical starter scaffolds (template + optional LLM)."""

from __future__ import annotations

import json
import logging
import re
from copy import deepcopy

from ..ai_pm.llm_client import LLMClientProtocol, LLMTier, LLMUnavailableError, get_default_client
from ..ai_pm.models import MicroPRD, PublishDraft
from ..sandbox.starter_scaffold import generate_starter_files
from backend.prompts.scaffold_technical import SCAFFOLD_TECHNICAL_SYSTEM_PROMPT
from .models import ChallengeBlueprint, TechnicalArchetype

logger = logging.getLogger(__name__)

_MAX_FILES = 12
_MAX_FILE_BYTES = 8000


def _cap_files(files: dict[str, str]) -> dict[str, str]:
    capped: dict[str, str] = {}
    for idx, (path, content) in enumerate(sorted(files.items())):
        if idx >= _MAX_FILES:
            break
        capped[path] = content[:_MAX_FILE_BYTES]
    return capped


def _readme(prd: MicroPRD, blueprint: ChallengeBlueprint) -> str:
    targets = ", ".join(f"`{t}`" for t in blueprint.edit_targets) or "`src/`"
    hints = f"\n\n## Founder layout hints\n\n{blueprint.starter_hints}\n" if blueprint.starter_hints else ""
    stack = ", ".join(blueprint.stack_guidance) if blueprint.stack_guidance else "Python 3.11"
    return f"""# {prd.title}

Challenge ID: `{prd.challenge_id}`

## Context

{prd.context}

## Primary focus

{blueprint.primary_focus}

## Edit targets

Focus your changes on: {targets}

## Stack

{stack}

## Setup

1. Run public tests: `pytest tests/ -v`
2. Implement the TODO sections in the edit targets.
3. Submit from the browser workspace or upload a ZIP.
{hints}
"""


def _template_algorithm(challenge_id: str, prd: MicroPRD, blueprint: ChallengeBlueprint) -> tuple[dict[str, str], dict[str, str]]:
    starter = {
        "README.md": _readme(prd, blueprint),
        "src/solution.py": '''"""Core algorithm — fix the clamp_values implementation."""

from __future__ import annotations


def clamp_values(values: list[float], low: float, high: float) -> list[float]:
    """
    Return each value clamped to [low, high].

    TODO: current implementation is wrong — it returns inputs unchanged.
    """
    return list(values)
''',
        "tests/test_public.py": '''"""Public tests for clamp_values."""

from src.solution import clamp_values


def test_clamp_basic():
    assert clamp_values([0.5, 1.5, -1.0], 0.0, 1.0) == [0.5, 1.0, 0.0]


def test_clamp_empty():
    assert clamp_values([], 0.0, 1.0) == []
''',
    }
    reference = deepcopy(starter)
    reference["src/solution.py"] = '''"""Core algorithm — reference implementation."""

from __future__ import annotations


def clamp_values(values: list[float], low: float, high: float) -> list[float]:
    """Return each value clamped to [low, high]."""
    return [max(low, min(high, v)) for v in values]
'''
    return starter, reference


def _template_service_module(
    challenge_id: str, prd: MicroPRD, blueprint: ChallengeBlueprint
) -> tuple[dict[str, str], dict[str, str]]:
    starter = {
        "README.md": _readme(prd, blueprint),
        "src/service.py": '''"""Retry helper — students implement execute_with_retry."""

from __future__ import annotations

from typing import Callable, TypeVar

T = TypeVar("T")


class RetryExhaustedError(RuntimeError):
    pass


def execute_with_retry(fn: Callable[[], T], *, max_attempts: int = 3) -> T:
    """
    Call fn until it succeeds or max_attempts is reached.

    TODO: always raises on first failure — add retry with backoff.
    """
    try:
        return fn()
    except Exception as exc:
        raise RetryExhaustedError(str(exc)) from exc
''',
        "tests/test_public.py": '''"""Public tests for execute_with_retry."""

import pytest

from src.service import RetryExhaustedError, execute_with_retry


def test_succeeds_first_try():
    assert execute_with_retry(lambda: 42) == 42


def test_retries_then_succeeds():
    attempts = {"n": 0}

    def flaky():
        attempts["n"] += 1
        if attempts["n"] < 3:
            raise ValueError("transient")
        return "ok"

    assert execute_with_retry(flaky, max_attempts=3) == "ok"


def test_raises_when_exhausted():
    with pytest.raises(RetryExhaustedError):
        execute_with_retry(lambda: (_ for _ in ()).throw(ValueError("fail")), max_attempts=2)
''',
    }
    reference = deepcopy(starter)
    reference["src/service.py"] = '''"""Retry helper — reference implementation."""

from __future__ import annotations

import time
from typing import Callable, TypeVar

T = TypeVar("T")


class RetryExhaustedError(RuntimeError):
    pass


def execute_with_retry(fn: Callable[[], T], *, max_attempts: int = 3) -> T:
    last_exc: Exception | None = None
    for attempt in range(max_attempts):
        try:
            return fn()
        except Exception as exc:
            last_exc = exc
            if attempt + 1 >= max_attempts:
                break
            time.sleep(0.001 * (attempt + 1))
    raise RetryExhaustedError(str(last_exc)) from last_exc
'''
    return starter, reference


def _template_integration(
    challenge_id: str, prd: MicroPRD, blueprint: ChallengeBlueprint
) -> tuple[dict[str, str], dict[str, str]]:
    starter = {
        "README.md": _readme(prd, blueprint),
        "src/config.py": '''"""Challenge configuration."""

MAX_RETRIES = 3
''',
        "src/idempotency.py": '''"""Idempotency store stub."""

from __future__ import annotations

_seen: set[str] = set()


def mark_processed(key: str) -> None:
    _seen.add(key)


def already_processed(key: str) -> bool:
    return key in _seen
''',
        "src/handler.py": '''"""Payment handler — wire idempotency + retry."""

from __future__ import annotations

from src.config import MAX_RETRIES
from src.idempotency import already_processed, mark_processed


def process_payment(idempotency_key: str, amount_cents: int) -> dict:
    """
    Process a payment idempotently.

    TODO: ignores idempotency and never retries — fix both.
    """
    if amount_cents <= 0:
        raise ValueError("amount must be positive")
    mark_processed(idempotency_key)
    return {"status": "ok", "amount_cents": amount_cents, "attempts": 1}
''',
        "tests/test_public.py": '''"""Public tests for process_payment."""

import pytest

from src.handler import process_payment
from src.idempotency import already_processed


def test_processes_valid_payment():
    result = process_payment("key-1", 100)
    assert result["status"] == "ok"
    assert result["amount_cents"] == 100


def test_idempotent_replay():
    process_payment("key-2", 200)
    assert already_processed("key-2")
    again = process_payment("key-2", 200)
    assert again["status"] == "ok"


def test_rejects_invalid_amount():
    with pytest.raises(ValueError):
        process_payment("key-3", 0)
''',
    }
    reference = deepcopy(starter)
    reference["src/handler.py"] = '''"""Payment handler — reference implementation."""

from __future__ import annotations

from src.config import MAX_RETRIES
from src.idempotency import already_processed, mark_processed

_cache: dict[str, dict] = {}


def process_payment(idempotency_key: str, amount_cents: int) -> dict:
    if amount_cents <= 0:
        raise ValueError("amount must be positive")
    if idempotency_key in _cache:
        return _cache[idempotency_key]
    if already_processed(idempotency_key):
        return _cache.get(idempotency_key, {"status": "ok", "amount_cents": amount_cents, "attempts": 1})
    mark_processed(idempotency_key)
    result = {"status": "ok", "amount_cents": amount_cents, "attempts": 1}
    _cache[idempotency_key] = result
    return result
'''
    return starter, reference


def _template_data_core(challenge_id: str, prd: MicroPRD, blueprint: ChallengeBlueprint) -> tuple[dict[str, str], dict[str, str]]:
    starter = generate_starter_files(challenge_id, prd.title)
    starter["README.md"] = _readme(prd, blueprint)
    reference = deepcopy(starter)
    reference["src/queries.py"] = _optimized_queries_py()
    return starter, reference


def _optimized_queries_py() -> str:
    return '''"""Query layer — reference optimized implementation."""

from __future__ import annotations

import sqlite3


def batch_session_lookup(conn: sqlite3.Connection, event_ids: list[int]) -> list[sqlite3.Row]:
    if not event_ids:
        return []
    placeholders = ",".join("?" for _ in event_ids)
    cur = conn.execute(
        f"""
        SELECT s.id, s.event_id, s.cache_status, s.response_time_ms,
               e.execution_time_ms, e.table_name
        FROM sessions s
        JOIN events e ON e.id = s.event_id
        WHERE s.event_id IN ({placeholders})
        """,
        event_ids,
    )
    return cur.fetchall()


def count_events_over_threshold(conn: sqlite3.Connection, threshold_ms: float) -> int:
    cur = conn.execute(
        "SELECT COUNT(*) FROM events WHERE execution_time_ms > ?",
        (threshold_ms,),
    )
    row = cur.fetchone()
    return int(row[0]) if row else 0
'''


def _template_data_adjacent(
    challenge_id: str, prd: MicroPRD, blueprint: ChallengeBlueprint
) -> tuple[dict[str, str], dict[str, str]]:
    starter, reference = _template_service_module(challenge_id, prd, blueprint)
    starter["src/queries.py"] = '''"""Optional data helper — not the main focus."""

from __future__ import annotations


def summarize_counts(rows: list[dict]) -> int:
    """TODO: return total count — currently returns 0."""
    return 0
'''
    reference["src/queries.py"] = '''"""Optional data helper — reference."""

from __future__ import annotations


def summarize_counts(rows: list[dict]) -> int:
    return len(rows)
'''
    starter["tests/test_public.py"] += '''


def test_summarize_counts():
    from src.queries import summarize_counts

    assert summarize_counts([{"a": 1}, {"b": 2}]) == 2
'''
    reference["tests/test_public.py"] = starter["tests/test_public.py"]
    return starter, reference


def infer_edit_targets(starter_files: dict[str, str]) -> list[str]:
    """Student edit paths derived from generated starter tree."""
    candidates = [
        p
        for p in starter_files
        if p.startswith("src/") and p.endswith(".py") and p not in ("src/db.py", "src/main.py", "src/config.py")
    ]
    return sorted(candidates)[:3] or ["src/service.py"]


def _student_facing_prd(prd: MicroPRD, draft: PublishDraft | None) -> MicroPRD:
    if draft is None:
        return prd
    updates: dict = {}
    if draft.title:
        updates["title"] = draft.title
    if draft.context:
        updates["context"] = draft.context
    if draft.definition_of_success:
        updates["definition_of_success"] = draft.definition_of_success
    return prd.model_copy(update=updates) if updates else prd


def finalize_starter_package(
    starter_files: dict[str, str],
    prd: MicroPRD,
    blueprint: ChallengeBlueprint,
    *,
    draft: PublishDraft | None = None,
) -> ChallengeBlueprint:
    """Align blueprint edit_targets + README with files actually generated."""
    blueprint = blueprint.model_copy()
    blueprint.edit_targets = infer_edit_targets(starter_files)
    display_prd = _student_facing_prd(prd, draft)
    starter_files["README.md"] = _readme(display_prd, blueprint)
    return blueprint


def generate_template_scaffold(
    challenge_id: str,
    prd: MicroPRD,
    blueprint: ChallengeBlueprint,
) -> tuple[dict[str, str], dict[str, str]]:
    """Deterministic scaffold for each archetype."""
    archetype = blueprint.archetype
    if archetype == TechnicalArchetype.algorithm:
        return _template_algorithm(challenge_id, prd, blueprint)
    if archetype == TechnicalArchetype.integration:
        return _template_integration(challenge_id, prd, blueprint)
    if archetype == TechnicalArchetype.data_core:
        return _template_data_core(challenge_id, prd, blueprint)
    if archetype == TechnicalArchetype.data_adjacent:
        return _template_data_adjacent(challenge_id, prd, blueprint)
    return _template_service_module(challenge_id, prd, blueprint)


def _parse_llm_scaffold(raw: dict) -> tuple[dict[str, str], dict[str, str]] | None:
    starter = raw.get("starter_files")
    reference = raw.get("reference_solution")
    if not isinstance(starter, dict) or not isinstance(reference, dict):
        return None
    if "tests/test_public.py" not in starter and not any(k.startswith("tests/") for k in starter):
        return None
    if "README.md" not in starter:
        return None
    return _cap_files({str(k): str(v) for k, v in starter.items()}), _cap_files(
        {str(k): str(v) for k, v in reference.items()}
    )


def generate_scaffold(
    challenge_id: str,
    prd: MicroPRD,
    blueprint: ChallengeBlueprint,
    *,
    llm: LLMClientProtocol | None = None,
) -> tuple[dict[str, str], dict[str, str]]:
    """LLM scaffold with template fallback."""
    client = llm or get_default_client()
    payload = {
        "challenge_id": challenge_id,
        "title": prd.title,
        "context": prd.context,
        "blueprint": blueprint.model_dump(),
    }
    try:
        result = client.chat(
            system=SCAFFOLD_TECHNICAL_SYSTEM_PROMPT,
            user=json.dumps(payload, indent=2),
            temperature=0.3,
            tier=LLMTier.sensitive,
        )
        parsed = _parse_llm_scaffold(result)
        if parsed:
            starter, reference = parsed
            if blueprint.example_files:
                starter = {**blueprint.example_files, **starter}
            if blueprint.starter_hints:
                starter["README.md"] = starter.get("README.md", "") + f"\n\n## Hints\n\n{blueprint.starter_hints}\n"
            return starter, reference
    except (LLMUnavailableError, KeyError, TypeError, json.JSONDecodeError) as exc:
        logger.info("Scaffold LLM unavailable — template fallback: %s", exc)

    starter, reference = generate_template_scaffold(challenge_id, prd, blueprint)
    if blueprint.example_files:
        starter = {**blueprint.example_files, **starter}
    if blueprint.starter_hints:
        starter["README.md"] = starter["README.md"] + f"\n\n## Hints\n\n{blueprint.starter_hints}\n"
    return starter, reference


def starter_has_forbidden_patterns(files: dict[str, str]) -> list[str]:
    violations: list[str] = []
    for path, content in files.items():
        if not path.endswith(".py"):
            continue
        if re.search(r"\bos\.system\s*\(", content):
            violations.append(f"{path}: os.system")
        if re.search(r"\bsubprocess\.", content):
            violations.append(f"{path}: subprocess")
        if re.search(r"\bsocket\.", content):
            violations.append(f"{path}: socket")
    return violations
