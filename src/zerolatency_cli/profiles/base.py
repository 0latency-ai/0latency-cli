"""Base profile ABC for agent-specific role detection."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class Atom:
    """
    Atom represents a single user/assistant/tool turn in a conversation.
    
    This is a simplified version for the Profile interface.
    The full Atom class in atom.py has additional fields.
    """
    role: str  # "user" | "assistant" | "tool_use"
    content: str
    content_raw: bytes
    metadata: dict


class Profile(ABC):
    """
    Abstract base class for agent-specific CLI output parsers.
    
    Each agent (Claude Code, Codex, Gemini CLI, Aider) has its own profile
    that implements role detection based on that agent's render format.
    
    Profiles are buffer-based, not stream-based, making them testable
    against fixtures without requiring live sessions.
    """
    
    __version__: str = "0.0.0"
    __compat_agent_version__: str = "unknown"
    agent_name: str = ""  # e.g., "claude-code", "codex", "gemini-cli", "aider"
    
    @abstractmethod
    def detect_role(self, buffer: bytes) -> Optional[Atom]:
        """
        Detect role and extract content from a buffer.
        
        Args:
            buffer: Raw bytes from the agent's output
            
        Returns:
            Atom if a complete turn is detected, None otherwise
        """
        ...
    
    @abstractmethod
    def is_complete_turn(self, buffer: bytes) -> bool:
        """
        Check if buffer contains a complete conversation turn.
        
        Args:
            buffer: Raw bytes from the agent's output
            
        Returns:
            True if the buffer contains a complete user or assistant turn
        """
        ...
    
    def extract_metadata(self, buffer: bytes) -> dict:
        """
        Extract agent-specific metadata from buffer.
        
        Optional method - profiles can override to extract additional
        metadata like file changes (Aider), tool calls, etc.
        
        Args:
            buffer: Raw bytes from the agent's output
            
        Returns:
            Dictionary of metadata fields
        """
        return {}
