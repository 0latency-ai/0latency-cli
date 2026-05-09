"""Tests for profile registry and loading."""

import pytest
from pathlib import Path
import tempfile
import sys

from zerolatency_cli.profiles import load_profile, AGENT_TO_PROFILE
from zerolatency_cli.profiles.base import Profile
from zerolatency_cli.profiles.claude_code import ClaudeCodeProfile
from zerolatency_cli.profiles.codex import CodexProfile
from zerolatency_cli.profiles.gemini_cli import GeminiCliProfile
from zerolatency_cli.profiles.aider import AiderProfile
from zerolatency_cli.profiles.generic import GenericProfile


def test_load_builtin_claude_code():
    """Test loading built-in Claude Code profile."""
    profile = load_profile("claude")
    assert isinstance(profile, ClaudeCodeProfile)
    assert profile.agent_name == "claude-code"
    assert profile.__compat_agent_version__ == "2.1.136"


def test_load_builtin_codex():
    """Test loading built-in Codex profile."""
    profile = load_profile("codex")
    assert isinstance(profile, CodexProfile)
    assert profile.agent_name == "codex"


def test_load_builtin_gemini():
    """Test loading built-in Gemini CLI profile."""
    profile = load_profile("gemini")
    assert isinstance(profile, GeminiCliProfile)
    assert profile.agent_name == "gemini-cli"


def test_load_builtin_aider():
    """Test loading built-in Aider profile."""
    profile = load_profile("aider")
    assert isinstance(profile, AiderProfile)
    assert profile.agent_name == "aider"


def test_unknown_agent_returns_generic():
    """Test that unknown agent names return GenericProfile."""
    profile = load_profile("unknown-agent")
    assert isinstance(profile, GenericProfile)
    assert profile.agent_name == "generic"


def test_profile_abc_cannot_instantiate():
    """Test that Profile ABC cannot be instantiated directly."""
    with pytest.raises(TypeError, match="Can't instantiate abstract class"):
        Profile()


def test_user_override_precedence(tmp_path, monkeypatch):
    """Test that user override takes precedence over built-in."""
    # Create temporary user profiles directory
    user_profiles_dir = tmp_path / ".0latency" / "profiles"
    user_profiles_dir.mkdir(parents=True)
    
    # Monkeypatch Path.home() to return tmp_path
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    
    # Create a user override profile
    override_file = user_profiles_dir / "claude_code.py"
    override_file.write_text("""
from zerolatency_cli.profiles.base import Profile, Atom
from typing import Optional

class ClaudeCodeProfile(Profile):
    __version__ = "999.0.0"
    __compat_agent_version__ = "custom"
    agent_name = "custom-claude"
    
    def detect_role(self, buffer: bytes) -> Optional[Atom]:
        return None
    
    def is_complete_turn(self, buffer: bytes) -> bool:
        return False
""")
    
    # Load profile - should get the user override
    profile = load_profile("claude")
    assert profile.agent_name == "custom-claude"
    assert profile.__version__ == "999.0.0"


def test_agent_to_profile_mapping():
    """Test the AGENT_TO_PROFILE mapping."""
    assert AGENT_TO_PROFILE["claude"] == "claude_code"
    assert AGENT_TO_PROFILE["codex"] == "codex"
    assert AGENT_TO_PROFILE["gemini"] == "gemini_cli"
    assert AGENT_TO_PROFILE["aider"] == "aider"
