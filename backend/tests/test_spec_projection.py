"""Tests for TechnicalChallengeSpec → Micro-PRD projection."""

from __future__ import annotations

from backend.challenge_factory.challenge_spec import infer_spec_heuristic
from backend.challenge_factory.spec_projection import format_spec_context, spec_success_criteria, spec_to_microprd
from backend.tests.test_triage import _make_metadata


class TestSpecProjection:
    def test_stream_parser_brief_is_specific_not_source_label(self):
        metadata = _make_metadata(
            ["file_size_bytes", "chunk_count", "oom", "memory_mb"],
            row_scale=4,
        )
        spec = infer_spec_heuristic(metadata, suggested_title="Memory-bounded JSONL parser")
        prd = spec_to_microprd(
            spec,
            challenge_id="stream-1",
            brand_proxy="DataStream",
            metadata=metadata,
        )

        ctx = prd.context.lower()
        assert "sample — stream_parser" not in ctx
        assert "jsonl" in ctx or "memory" in ctx or "stream" in ctx
        assert "**scenario:**" in ctx
        assert "**your task:**" in ctx
        assert "parses valid lines" not in ctx  # old terse DoD line

        joined = " ".join(prd.definition_of_success).lower()
        assert "malformed" in joined or "stream" in joined
        assert "preserve existing function signatures" not in joined

    def test_stream_parser_brief_includes_typed_examples(self):
        metadata = _make_metadata(
            ["file_size_bytes", "chunk_count", "oom", "memory_mb"],
            row_scale=4,
        )
        spec = infer_spec_heuristic(metadata)
        assert len(spec.examples) >= 2

        prd = spec_to_microprd(spec, challenge_id="stream-1", metadata=metadata)
        ctx = prd.context

        assert "**Examples:**" in ctx
        assert "Iterable[str]" in ctx
        assert "list[dict]" in ctx
        assert "json object per line" in ctx.lower() or "one json object" in ctx.lower()
        assert "not-valid-json" in ctx or "malformed" in ctx.lower()

    def test_format_spec_context_includes_background_and_constraints(self):
        metadata = _make_metadata(["file_size_bytes", "oom"], row_scale=4)
        spec = infer_spec_heuristic(metadata)
        context = format_spec_context(spec, metadata=metadata)

        assert spec.startup_pain_point.split(".")[0].lower() in context.lower()
        assert "`file_size_bytes`" in context
        assert "memory bounded" in context.lower()

    def test_success_criteria_include_definition_of_done_and_tests(self):
        metadata = _make_metadata(["file_size_bytes", "oom"], row_scale=4)
        spec = infer_spec_heuristic(metadata)
        criteria = spec_success_criteria(spec)

        assert any("public tests" in line.lower() for line in criteria)
        assert len(criteria) >= len(spec.definition_of_done)
