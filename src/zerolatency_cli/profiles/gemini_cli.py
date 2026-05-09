"""Gemini CLI profile stub (to be implemented in Task 7)."""

from zerolatency_cli.profiles.base import Profile, Atom
from typing import Optional


class GeminiCliProfile(Profile):
    """Profile for Google Gemini CLI."""
    
    __version__ = "0.1.0"
    __compat_agent_version__ = "0.41.2"
    agent_name = "gemini-cli"
    
    def detect_role(self, buffer: bytes) -> Optional[Atom]:
        # TODO: Implement in Task 7
        pass
    
    def is_complete_turn(self, buffer: bytes) -> bool:
        # TODO: Implement in Task 7
        pass
