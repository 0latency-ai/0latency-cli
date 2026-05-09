"""Generic profile stub (to be implemented in Task 9)."""

from zerolatency_cli.profiles.base import Profile, Atom
from typing import Optional


class GenericProfile(Profile):
    """Generic fallback profile for unknown agents."""
    
    __version__ = "0.1.0"
    __compat_agent_version__ = "unknown"
    agent_name = "generic"
    
    def detect_role(self, buffer: bytes) -> Optional[Atom]:
        # TODO: Implement in Task 9
        pass
    
    def is_complete_turn(self, buffer: bytes) -> bool:
        # TODO: Implement idle-detection in Task 9
        pass
