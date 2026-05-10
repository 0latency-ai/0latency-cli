"""Tests for interactive prompt passthrough."""

import pytest
from zerolatency_cli.prompts import is_interactive_prompt


def test_yn_prompts_detected():
    """Test that Y/N prompts are detected as interactive."""
    # Various Y/N prompt formats
    prompts = [
        b"Delete file? [Y/n]: ",
        b"Delete file? [y/N]: ",
        b"Continue? (Y/n) ",
        b"Proceed? (y/N) ",
        b"\x1b[32mContinue?\x1b[0m [Y/n]: ",  # With ANSI codes
    ]
    
    for prompt in prompts:
        assert is_interactive_prompt(prompt), f"Failed to detect: {prompt}"


def test_password_prompts_detected():
    """Test that password prompts are detected as interactive."""
    prompts = [
        b"Enter password: ",
        b"Password: ",
        b"Enter passphrase: ",
        b"enter your password: ",  # lowercase
        b"\x1b[1mPassword:\x1b[0m ",  # With ANSI codes
    ]
    
    for prompt in prompts:
        assert is_interactive_prompt(prompt), f"Failed to detect: {prompt}"


def test_regular_text_not_detected():
    """Test that regular text is NOT detected as interactive prompt."""
    non_prompts = [
        b"This is regular output",
        b"Yes or no?",  # Question but not a prompt format
        b"The answer is yes",
        b"Processing files...",
        b"Error: file not found",
    ]
    
    for text in non_prompts:
        assert not is_interactive_prompt(text), f"False positive: {text}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
