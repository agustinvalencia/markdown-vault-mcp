"""Tests for context tool response truncation."""

import json

from mdvault_mcp_server.tools.context import _truncate_context_day


class TestTruncateContextDay:
    def test_small_response_unchanged(self):
        data = {"date": "2026-03-15", "summary": {"tasks_completed": 3}, "activity": []}
        raw = json.dumps(data)
        result = _truncate_context_day(raw)
        assert json.loads(result) == data

    def test_activity_truncated(self):
        data = {
            "date": "2026-03-09",
            "activity": [{"note": f"entry-{i}"} for i in range(50)],
        }
        raw = json.dumps(data)
        result = _truncate_context_day(raw)
        parsed = json.loads(result)
        # 15 items + 1 truncation notice
        assert len(parsed["activity"]) == 16
        assert "truncated" in parsed["activity"][-1]["note"]

    def test_modified_notes_truncated(self):
        data = {
            "date": "2026-03-09",
            "modified_notes": [f"notes/{i}.md" for i in range(30)],
        }
        raw = json.dumps(data)
        result = _truncate_context_day(raw)
        parsed = json.loads(result)
        assert len(parsed["modified_notes"]) == 16
        assert "truncated" in parsed["modified_notes"][-1]

    def test_invalid_json_passthrough(self):
        raw = "not json"
        assert _truncate_context_day(raw) == "not json"

    def test_error_passthrough(self):
        raw = "Error: index not found"
        assert _truncate_context_day(raw) == raw

    def test_exact_limit_not_truncated(self):
        data = {"activity": [{"note": f"e-{i}"} for i in range(15)]}
        raw = json.dumps(data)
        result = _truncate_context_day(raw)
        parsed = json.loads(result)
        assert len(parsed["activity"]) == 15

    def test_hard_truncate_safety_net(self):
        """Extremely large fields trigger the hard character limit."""
        data = {"big_field": "x" * 20000}
        raw = json.dumps(data)
        result = _truncate_context_day(raw)
        assert len(result) <= 8100  # MAX_CONTEXT_CHARS + truncation notice
        assert result.endswith("(response truncated)")
