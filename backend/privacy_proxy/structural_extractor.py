"""
Extracts structural metadata from sanitized (PII-scrubbed) text.

Handles three input shapes:
  - JSON   : single object or array of objects
  - CSV    : header row + data rows
  - Log    : unstructured lines with level/component/kv patterns

The extractor NEVER returns cell values — only structural descriptors
(field names, inferred types, row counts, nested paths, event frequencies).
"""

from __future__ import annotations

import csv
import io
import json
import re
from collections import Counter
from typing import Any

from .models import EventFrequency, FieldMetadata, InputFormat


# ---------------------------------------------------------------------------
# Type inference
# ---------------------------------------------------------------------------

_DATETIME_RE = re.compile(
    r"""(?x)
    \d{4}-\d{2}-\d{2}           # date: 2024-01-15
    (?:[T\s]\d{2}:\d{2}         # optional time
    (?::\d{2}(?:\.\d+)?)?
    (?:Z|[+-]\d{2}:?\d{2})?)?
    """
)
_INT_RE = re.compile(r"^-?\d+$")
_FLOAT_RE = re.compile(r"^-?\d+\.\d+$")
_BOOL_VALUES = {"true", "false", "yes", "no", "1", "0"}


def _infer_type(value: Any) -> str:
    if value is None:
        return "unknown"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "float"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    s = str(value).strip()
    if not s or s.lower() in ("null", "none", "na", "n/a", ""):
        return "unknown"
    if s.lower() in _BOOL_VALUES:
        return "boolean"
    if _INT_RE.match(s):
        return "integer"
    if _FLOAT_RE.match(s):
        return "float"
    if _DATETIME_RE.match(s):
        return "datetime"
    return "string"


# ---------------------------------------------------------------------------
# JSON extractor
# ---------------------------------------------------------------------------

def _nested_paths(obj: Any, prefix: str = "", depth: int = 0) -> list[str]:
    """Collect dot-notation paths for all nested keys up to depth 4."""
    if depth > 4 or not isinstance(obj, dict):
        return []
    paths: list[str] = []
    for k, v in obj.items():
        path = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            paths.append(path)
            paths.extend(_nested_paths(v, path, depth + 1))
        elif isinstance(v, list) and v and isinstance(v[0], dict):
            paths.append(f"{path}[]")
            paths.extend(_nested_paths(v[0], f"{path}[]", depth + 1))
    return paths


def _fields_from_record(record: dict[str, Any]) -> dict[str, list[str]]:
    """Map field name → list of observed types from a single record."""
    result: dict[str, list[str]] = {}
    for k, v in record.items():
        result[k] = [_infer_type(v)]
    return result


def extract_json(text: str) -> dict[str, Any]:
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        return {"error": str(exc), "format": InputFormat.json}

    records: list[dict] = []
    if isinstance(data, list):
        records = [r for r in data if isinstance(r, dict)]
    elif isinstance(data, dict):
        records = [data]

    if not records:
        return {
            "format": InputFormat.json,
            "fields": [],
            "nested_paths": [],
            "row_scale": 0,
            "event_frequencies": [],
        }

    # Aggregate field types across all records
    type_map: dict[str, Counter] = {}
    null_map: dict[str, int] = {}
    for rec in records:
        for name, types in _fields_from_record(rec).items():
            type_map.setdefault(name, Counter()).update(types)
            if types[0] == "unknown":
                null_map[name] = null_map.get(name, 0) + 1

    fields = []
    for name, counter in type_map.items():
        dominant_type = counter.most_common(1)[0][0]
        sample_count = sum(counter.values()) - null_map.get(name, 0)
        fields.append(
            FieldMetadata(
                name=name,
                inferred_type=dominant_type,
                nullable=null_map.get(name, 0) > 0,
                sample_count=sample_count,
            )
        )

    nested = list(dict.fromkeys(_nested_paths(records[0])))  # dedup, order-preserving

    return {
        "format": InputFormat.json,
        "fields": fields,
        "nested_paths": nested,
        "row_scale": len(records),
        "event_frequencies": [],
    }


# ---------------------------------------------------------------------------
# CSV extractor
# ---------------------------------------------------------------------------

def extract_csv(text: str) -> dict[str, Any]:
    reader = csv.reader(io.StringIO(text))
    rows = list(reader)
    if not rows:
        return {"format": InputFormat.csv, "fields": [], "nested_paths": [], "row_scale": 0, "event_frequencies": []}

    headers = rows[0]
    data_rows = rows[1:]

    type_map: dict[str, Counter] = {h: Counter() for h in headers}
    null_map: dict[str, int] = {h: 0 for h in headers}

    for row in data_rows:
        for i, h in enumerate(headers):
            val = row[i] if i < len(row) else ""
            t = _infer_type(val)
            type_map[h].update([t])
            if t == "unknown":
                null_map[h] += 1

    fields = []
    for h in headers:
        dominant = type_map[h].most_common(1)[0][0] if type_map[h] else "unknown"
        sample_count = sum(type_map[h].values()) - null_map.get(h, 0)
        fields.append(
            FieldMetadata(
                name=h,
                inferred_type=dominant,
                nullable=null_map.get(h, 0) > 0,
                sample_count=sample_count,
            )
        )

    return {
        "format": InputFormat.csv,
        "fields": fields,
        "nested_paths": [],
        "row_scale": len(data_rows),
        "event_frequencies": [],
    }


# ---------------------------------------------------------------------------
# Log extractor
# ---------------------------------------------------------------------------

_LOG_LEVEL_RE = re.compile(
    r"\b(CRITICAL|ERROR|ERR|WARN(?:ING)?|INFO|DEBUG|TRACE|FATAL)\b",
    re.IGNORECASE,
)
_COMPONENT_RE = re.compile(r"\[([a-zA-Z0-9_\-\.]+)\]")
_KV_RE = re.compile(r'([a-zA-Z_][a-zA-Z0-9_]*)=(?:"[^"]*"|\'[^\']*\'|\S+)')
_JSON_BLOB_RE = re.compile(r"\{.*?\}", re.DOTALL)


def extract_log(text: str) -> dict[str, Any]:
    lines = [ln for ln in text.splitlines() if ln.strip()]

    level_counter: Counter[str] = Counter()
    component_counter: Counter[str] = Counter()
    kv_fields: dict[str, Counter] = {}

    for line in lines:
        # Log levels
        for m in _LOG_LEVEL_RE.finditer(line):
            level_counter[m.group(1).upper()] += 1

        # Bracketed components like [api_service]
        for m in _COMPONENT_RE.finditer(line):
            component_counter[m.group(1)] += 1

        # Inline key=value pairs (field name extraction)
        for m in _KV_RE.finditer(line):
            key = m.group(1)
            val_raw = m.group(0).split("=", 1)[1].strip("\"' ")
            t = _infer_type(val_raw)
            kv_fields.setdefault(key, Counter()).update([t])

        # Inline JSON blobs — extract their keys too
        for blob_match in _JSON_BLOB_RE.finditer(line):
            try:
                blob = json.loads(blob_match.group(0))
                if isinstance(blob, dict):
                    for k, v in blob.items():
                        t = _infer_type(v)
                        kv_fields.setdefault(k, Counter()).update([t])
            except json.JSONDecodeError:
                pass

    fields = [
        FieldMetadata(
            name=k,
            inferred_type=counter.most_common(1)[0][0],
            sample_count=sum(counter.values()),
        )
        for k, counter in kv_fields.items()
    ]

    event_freqs: list[EventFrequency] = []
    for label, count in sorted(level_counter.items(), key=lambda x: -x[1]):
        event_freqs.append(EventFrequency(event_type=label, count=count))
    for label, count in sorted(component_counter.items(), key=lambda x: -x[1]):
        event_freqs.append(EventFrequency(event_type=f"[{label}]", count=count))

    return {
        "format": InputFormat.log,
        "fields": fields,
        "nested_paths": [],
        "row_scale": len(lines),
        "event_frequencies": event_freqs,
    }


# ---------------------------------------------------------------------------
# Format detection
# ---------------------------------------------------------------------------

def detect_format(text: str) -> InputFormat:
    stripped = text.strip()
    if stripped.startswith(("{", "[")):
        return InputFormat.json
    # Heuristic: if first non-empty line has commas and looks like a header
    first_line = stripped.splitlines()[0] if stripped.splitlines() else ""
    if "," in first_line and not _LOG_LEVEL_RE.search(first_line):
        return InputFormat.csv
    return InputFormat.log


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def extract(text: str, fmt: InputFormat = InputFormat.auto) -> dict[str, Any]:
    """
    Extract structural metadata from sanitized text.

    Args:
        text: PII-scrubbed text (output of the sanitizer, not raw input)
        fmt:  Caller-specified format, or InputFormat.auto to detect

    Returns a dict with keys: format, fields, nested_paths, row_scale,
    event_frequencies.
    """
    resolved = fmt if fmt != InputFormat.auto else detect_format(text)

    if resolved == InputFormat.json:
        return extract_json(text)
    if resolved == InputFormat.csv:
        return extract_csv(text)
    return extract_log(text)
