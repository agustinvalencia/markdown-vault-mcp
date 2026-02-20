
import datetime
from pathlib import Path
import yaml
import pytest
from mdvault_mcp_server.tools.frontmatter import update_note_metadata, try_parse_datetime

def test_try_parse_datetime():
    """Test that ISO strings are parsed to datetime objects."""
    iso_str = "2026-01-25T21:44:54"
    dt = try_parse_datetime(iso_str)
    assert isinstance(dt, datetime.datetime)
    assert dt.year == 2026
    assert dt.month == 1
    assert dt.day == 25
    assert dt.hour == 21

    # Test non-date string
    non_date = "hello world"
    assert try_parse_datetime(non_date) == non_date

def test_update_metadata_datetime_serialization(tmp_path):
    """
    Test that updating metadata with a datetime string results in 
    an unquoted timestamp in the YAML frontmatter.
    Ref: https://github.com/agustinvalencia/markdown-vault-mcp/issues/10
    """
    # Create a dummy note
    note_path = tmp_path / "test_note.md"
    note_path.write_text("---\ntitle: Test\n---\n\nContent", encoding="utf-8")

    updates = {
        "created_at": "2026-01-25T21:44:54",
        "deadline": "2026-02-01T12:00:00"
    }

    # Apply updates
    new_content = update_note_metadata(note_path, updates)

    # Verify content strings (regex or simple check)
    # We expect `created_at: 2026-01-25 21:44:54` (unquoted)
    # Note: python-frontmatter/PyYAML might output slightly different formats depending on config,
    # but definitely NOT quoted.
    
    assert "created_at: 2026-01-25 21:44:54" in new_content
    assert "created_at: '" not in new_content
    assert 'created_at: "' not in new_content
    
    # Verify by parsing back
    # If we parse it back, it should be a datetime object
    # But checking the string representation confirms the "unquoted" requirement for mdv validate.

