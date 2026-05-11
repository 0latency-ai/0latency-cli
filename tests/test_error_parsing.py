"""Tests for error envelope parsing (CP9 P2 T2+T3)."""

import pytest
from zerolatency_cli.error_parsing import parse_error_envelope, print_error, print_next_action, APIError


def test_parse_new_error_envelope():
    """Test parsing CP9 P2 error envelope structure."""
    response = {
        "detail": {
            "error": {
                "code": "INVALID_API_KEY",
                "message": "API key is invalid",
                "hint": "Check your key at https://app.0latency.ai",
                "docs_url": "https://0latency.ai/docs/troubleshooting#invalid-api-key"
            }
        }
    }
    
    error = parse_error_envelope(response)
    assert error is not None
    assert error.code == "INVALID_API_KEY"
    assert error.message == "API key is invalid"
    assert error.hint == "Check your key at https://app.0latency.ai"
    assert error.docs_url == "https://0latency.ai/docs/troubleshooting#invalid-api-key"


def test_parse_legacy_plain_string_detail():
    """Test backward compatibility with plain string detail."""
    response = {
        "detail": "Invalid API key"
    }
    
    error = parse_error_envelope(response)
    assert error is not None
    assert error.code == "UNKNOWN"
    assert error.message == "Invalid API key"
    assert error.hint == ""
    assert error.docs_url == ""


def test_parse_malformed_response():
    """Test graceful handling of malformed responses."""
    # Empty response
    error = parse_error_envelope({})
    assert error is None
    
    # Missing error key
    error = parse_error_envelope({"detail": {}})
    assert error is None
    
    # Invalid structure
    error = parse_error_envelope({"detail": {"error": "not a dict"}})
    assert error is None


def test_error_format_for_display():
    """Test error formatting for terminal output."""
    error = APIError(
        code="TEST_ERROR",
        message="Test error message",
        hint="Try this solution",
        docs_url="https://docs.example.com/error"
    )
    
    formatted = error.format_for_display()
    assert "Test error message" in formatted
    assert "Try this solution" in formatted
    assert "https://docs.example.com/error" in formatted
    assert "\033[31m" in formatted  # Red color for error
    assert "\033[2m" in formatted   # Dim for hint
    assert "\033[34m" in formatted  # Blue for link


def test_next_action_present(capsys):
    """Test next_action display when present."""
    response = {
        "id": "atom_123",
        "status": "created",
        "next_action": {
            "type": "try_recall",
            "suggested_query": "Sarah Starbucks",
            "example_command": "0latency memory recall 'Sarah Starbucks'"
        }
    }
    
    print_next_action(response)
    captured = capsys.readouterr()
    
    assert "✓ Memory stored" in captured.out
    assert "Sarah Starbucks" in captured.out
    assert "0latency memory recall" in captured.out


def test_next_action_absent(capsys):
    """Test graceful handling when next_action absent."""
    response = {
        "id": "atom_123",
        "status": "created"
    }
    
    # Should not raise, should not print anything
    print_next_action(response)
    captured = capsys.readouterr()
    
    assert captured.out == ""
    assert captured.err == ""


def test_next_action_malformed(capsys):
    """Test graceful handling of malformed next_action."""
    # next_action not a dict
    print_next_action({"next_action": "invalid"})
    
    # next_action missing suggested_query
    print_next_action({"next_action": {"type": "recall"}})
    
    # Should not raise
    captured = capsys.readouterr()
    # No output expected for malformed data
