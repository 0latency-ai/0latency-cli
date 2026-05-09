"""Codex profile stub (to be implemented in Task 6)."""

from zerolatency_cli.profiles.base import Profile, Atom
from typing import Optional


class CodexProfile(Profile):
    """Profile for OpenAI Codex CLI."""
    
    __version__ = "0.1.0"
    __compat_agent_version__ = "0.130.0"
    agent_name = "codex"
    
    def detect_role(self, buffer: bytes) -> Optional[Atom]:
        # TODO: Implement in Task 6
        pass
    
    def is_complete_turn(self, buffer: bytes) -> bool:
        # TODO: Implement in Task 6
        pass
