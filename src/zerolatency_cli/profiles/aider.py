"""Aider profile stub (to be implemented in Task 8)."""

from zerolatency_cli.profiles.base import Profile, Atom
from typing import Optional


class AiderProfile(Profile):
    """Profile for Aider CLI."""
    
    __version__ = "0.1.0"
    __compat_agent_version__ = "0.86.2"
    agent_name = "aider"
    
    def detect_role(self, buffer: bytes) -> Optional[Atom]:
        # TODO: Implement in Task 8
        pass
    
    def is_complete_turn(self, buffer: bytes) -> bool:
        # TODO: Implement in Task 8
        pass
    
    def extract_metadata(self, buffer: bytes) -> dict:
        # TODO: Extract file_changes for Aider in Task 8
        return {}
