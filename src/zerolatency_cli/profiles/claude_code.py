"""Claude Code profile stub (to be implemented in Task 5)."""

from zerolatency_cli.profiles.base import Profile, Atom
from typing import Optional


class ClaudeCodeProfile(Profile):
    """Profile for Claude Code CLI."""
    
    __version__ = "0.1.0"
    __compat_agent_version__ = "2.1.136"
    agent_name = "claude-code"
    
    def detect_role(self, buffer: bytes) -> Optional[Atom]:
        # TODO: Implement in Task 5
        pass
    
    def is_complete_turn(self, buffer: bytes) -> bool:
        # TODO: Implement in Task 5
        pass
