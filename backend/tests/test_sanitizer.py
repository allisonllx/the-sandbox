"""
Test suite for privacy-001: Local Privacy Proxy & Sanitization Engine.

Each test directly verifies a step from the feature_list.json verification checklist:
  ✓ PII types are stripped (email, phone, API key, JWT)
  ✓ Output contains only structural metadata — no raw values
  ✓ Structural extraction works for JSON, CSV, and log text
  ✓ Zero-leak guardrail blocks prohibited chunks
  ✓ No outbound HTTP calls are made during processing (mock enforced via monkeypatch)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

FIXTURES = Path(__file__).parent / "fixtures"

# All known PII values used in tests — none should appear in output.
_PII_VALUES = [
    "john.doe@acmecorp.com",
    "jane.smith@acmecorp.com",
    "415-555-0192",
    "555.867.5309",
    "sk_live_AbCdEfGhIjKlMnOpQrStUvWx",
    "AKIAIOSFODNN7EXAMPLE",
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyXzEyMyJ9.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c",
    "192.168.1.45",
    "jane.smith",
    "john.doe",
]


def _assert_no_pii_in_metadata(metadata_json: str) -> None:
    """Fail the test if any known PII value appears in the serialised metadata."""
    for pii in _PII_VALUES:
        assert pii not in metadata_json, (
            f"PII value '{pii}' leaked into metadata output"
        )


# ---------------------------------------------------------------------------
# Import under test
# ---------------------------------------------------------------------------

from backend.privacy_proxy.sanitizer import sanitize
from backend.privacy_proxy.pii_patterns import scrub
from backend.privacy_proxy.models import InputFormat


# ===========================================================================
# 1. PII masking — regex layer
# ===========================================================================

class TestPIIMasking:
    def test_email_is_stripped(self):
        text = "Contact support at helpdesk@example.com for assistance."
        scrubbed, detections = scrub(text)
        assert "helpdesk@example.com" not in scrubbed
        assert "email" in detections
        assert detections["email"] == 1

    def test_multiple_emails_are_stripped(self):
        text = "Users: alice@corp.com and bob@corp.com both reported the bug."
        scrubbed, detections = scrub(text)
        assert "alice@corp.com" not in scrubbed
        assert "bob@corp.com" not in scrubbed
        assert detections["email"] == 2

    def test_phone_is_stripped(self):
        text = "Call us at 415-555-0192 or 555.867.5309 anytime."
        scrubbed, detections = scrub(text)
        assert "415-555-0192" not in scrubbed
        assert "555.867.5309" not in scrubbed
        assert "phone" in detections

    def test_jwt_is_stripped(self):
        jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyXzEyMyJ9.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
        text = f"Authorization: Bearer {jwt}"
        scrubbed, detections = scrub(text)
        assert jwt not in scrubbed
        assert "jwt" in detections or "bearer_token" in detections

    def test_aws_access_key_is_stripped(self):
        text = "export AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE"
        scrubbed, detections = scrub(text)
        assert "AKIAIOSFODNN7EXAMPLE" not in scrubbed
        assert "aws_access_key" in detections

    def test_api_key_inline_is_stripped(self):
        text = 'config = {"api_key": "s3cr3t-t0ken-abc123xyz456789012"}'
        scrubbed, detections = scrub(text)
        assert "s3cr3t-t0ken-abc123xyz456789012" not in scrubbed
        assert "api_key" in detections

    def test_ipv4_is_stripped(self):
        text = "Request from 10.0.0.5 failed."
        scrubbed, detections = scrub(text)
        assert "10.0.0.5" not in scrubbed
        assert "ipv4" in detections

    def test_clean_text_has_no_detections(self):
        text = "The database has 3 tables and 10_000 rows."
        scrubbed, detections = scrub(text)
        assert scrubbed == text
        assert not detections


# ===========================================================================
# 2. Full sanitizer pipeline — output is structural metadata only
# ===========================================================================

class TestSanitizerOutput:
    def test_output_contains_no_raw_pii(self):
        text = (FIXTURES / "sample_log.txt").read_text()
        metadata = sanitize(text)
        metadata_json = metadata.model_dump_json()
        _assert_no_pii_in_metadata(metadata_json)

    def test_pii_detections_recorded(self):
        text = (FIXTURES / "sample_log.txt").read_text()
        metadata = sanitize(text)
        pii_types = {d.pii_type for d in metadata.pii_detections}
        # The fixture contains emails and an API key
        assert "email" in pii_types
        assert "api_key" in pii_types or "bearer_token" in pii_types

    def test_log_format_detected(self):
        text = (FIXTURES / "sample_log.txt").read_text()
        metadata = sanitize(text)
        assert metadata.format_detected == InputFormat.log

    def test_event_frequencies_extracted_from_log(self):
        text = (FIXTURES / "sample_log.txt").read_text()
        metadata = sanitize(text)
        freq_types = {e.event_type for e in metadata.event_type_frequencies}
        assert "ERROR" in freq_types or "WARN" in freq_types

    def test_row_scale_matches_line_count(self):
        text = (FIXTURES / "sample_log.txt").read_text()
        non_empty_lines = [l for l in text.splitlines() if l.strip()]
        metadata = sanitize(text)
        assert metadata.approximate_row_scale == len(non_empty_lines)

    def test_empty_input_returns_gracefully(self):
        metadata = sanitize("")
        assert metadata.approximate_row_scale is None or metadata.approximate_row_scale == 0
        assert metadata.ner.status.value == "not_run"
        assert metadata.ner.entity_counts == []

    def test_entirely_blocked_input_returns_gracefully(self):
        text = "The password is hunter2\n\nAnother line with password=secret123"
        metadata = sanitize(text)
        assert metadata.blocked_chunk_count >= 1

    def test_extra_guardrail_keyword_blocks_chunk(self):
        text = "Normal log line: status=200\n\nINTERNAL_CODENAME reveals the architecture."
        metadata = sanitize(text, guardrail_keywords=["INTERNAL_CODENAME"])
        assert metadata.blocked_chunk_count >= 1


# ===========================================================================
# 3. JSON structural extraction
# ===========================================================================

class TestJSONExtraction:
    def test_field_names_extracted(self):
        data = json.dumps([
            {"user_id": 1, "score": 0.95, "active": True},
            {"user_id": 2, "score": 0.82, "active": False},
        ])
        metadata = sanitize(data, fmt=InputFormat.json)
        field_names = {f.name for f in metadata.fields}
        assert "user_id" in field_names
        assert "score" in field_names
        assert "active" in field_names

    def test_types_inferred(self):
        data = json.dumps({"count": 42, "ratio": 0.75, "label": "fast", "enabled": True})
        metadata = sanitize(data, fmt=InputFormat.json)
        type_map = {f.name: f.inferred_type for f in metadata.fields}
        assert type_map["count"] == "integer"
        assert type_map["ratio"] == "float"
        assert type_map["label"] == "string"
        assert type_map["enabled"] == "boolean"

    def test_nested_paths_extracted(self):
        data = json.dumps({"user": {"address": {"zip": "00000", "city": "Somewhere"}}})
        metadata = sanitize(data, fmt=InputFormat.json)
        assert any("user" in p for p in metadata.nested_paths)

    def test_pii_in_json_values_stripped(self):
        data = json.dumps({"email": "leaky@corp.com", "user_id": 99})
        metadata = sanitize(data, fmt=InputFormat.json)
        metadata_json = metadata.model_dump_json()
        assert "leaky@corp.com" not in metadata_json


# ===========================================================================
# 4. CSV structural extraction
# ===========================================================================

class TestCSVExtraction:
    def test_headers_become_field_names(self):
        csv_text = "node_id,weight,timestamp\n1,0.5,2024-01-01\n2,0.7,2024-01-02"
        metadata = sanitize(csv_text, fmt=InputFormat.csv)
        field_names = {f.name for f in metadata.fields}
        assert field_names == {"node_id", "weight", "timestamp"}

    def test_row_count_correct(self):
        csv_text = "a,b\n1,2\n3,4\n5,6"
        metadata = sanitize(csv_text, fmt=InputFormat.csv)
        assert metadata.approximate_row_scale == 3


# ===========================================================================
# 5. NER processing notes
# ===========================================================================

class TestNERProcessingNotes:
    def test_note_when_model_unavailable(self, monkeypatch):
        from backend.privacy_proxy import sanitizer as sanitizer_module
        from backend.privacy_proxy.ner_engine import NERResult

        monkeypatch.setattr(
            sanitizer_module,
            "analyze_entities",
            lambda text: NERResult(counts={}, model_available=False),
        )

        metadata = sanitize("Login failed for user John Smith at Acme Corp")
        notes = " ".join(metadata.processing_notes)
        assert metadata.ner.status.value == "skipped"
        assert metadata.ner.model_available is False
        assert "NER pass skipped" in notes
        assert "spaCy model not available" in notes

    def test_note_when_model_runs_but_finds_nothing(self, monkeypatch):
        from backend.privacy_proxy import sanitizer as sanitizer_module
        from backend.privacy_proxy.ner_engine import NERResult

        monkeypatch.setattr(
            sanitizer_module,
            "analyze_entities",
            lambda text: NERResult(counts={}, model_available=True),
        )

        metadata = sanitize("2024-03-12 ERROR status=503 duration_ms=1200")
        notes = " ".join(metadata.processing_notes)
        assert metadata.ner.status.value == "completed_empty"
        assert metadata.ner.model_available is True
        assert metadata.ner.entity_counts == []
        assert "NER pass completed" in notes
        assert "no PERSON, ORG, GPE, or PRODUCT entities" in notes
        assert "not available" not in notes

    def test_note_when_entities_detected(self, monkeypatch):
        from backend.privacy_proxy import sanitizer as sanitizer_module
        from backend.privacy_proxy.ner_engine import NERResult

        monkeypatch.setattr(
            sanitizer_module,
            "analyze_entities",
            lambda text: NERResult(counts={"PERSON": 1, "ORG": 1}, model_available=True),
        )

        metadata = sanitize("Issue reported by John Smith at Acme Corp")
        notes = " ".join(metadata.processing_notes)
        assert metadata.ner.status.value == "completed"
        assert metadata.ner.model_available is True
        assert len(metadata.ner.entity_counts) == 2
        assert metadata.ner_entity_counts == metadata.ner.entity_counts
        assert "NER pass completed" in notes
        assert "2 entity token(s) detected" in notes


# ===========================================================================
# 6. No outbound HTTP during processing
# ===========================================================================

class TestNoNetworkCalls:
    def test_sanitize_makes_no_http_requests(self, monkeypatch):
        """
        Monkeypatch socket.socket to raise if any connection is attempted.
        This proves the sanitizer never makes a network call.
        """
        import socket

        original_connect = socket.socket.connect

        def explode(self, *args, **kwargs):
            raise AssertionError(
                f"sanitize() attempted a network connection to {args} — this violates the zero-trust constraint."
            )

        monkeypatch.setattr(socket.socket, "connect", explode)

        text = (FIXTURES / "sample_log.txt").read_text()
        # Should complete without raising
        metadata = sanitize(text)
        assert metadata is not None
