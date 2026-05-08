"""Claude Code role detection profile (hardcoded for P1)."""

import re
from enum import Enum
from typing import Callable, Optional
from zerolatency_cli.atom import Atom

# ANSI CSI sequence regex (Control Sequence Introducer)
ANSI_CSI_PATTERN = re.compile(rb'\x1b\[[0-?]*[ -/]*[@-~]')

class ParseState(Enum):
    """State machine states for role detection."""
    WAITING_FOR_USER = "waiting_for_user"
    IN_USER = "in_user"
    IN_ASSISTANT = "in_assistant"
    IN_TOOL_USE = "in_tool_use"

class ClaudeCodeProfile:
    """
    Role detection profile for Claude Code CLI.
    
    GROUND TRUTH CAPTURE STATUS:
    ============================
    WARNING: These delimiters are based on known Claude Code patterns
    and have NOT been verified against a real session yet.
    
    Task 4 spec requires capturing ground truth with:
        script -q /tmp/claude-truth.log claude
    
    Once claude binary is available, these constants MUST be updated
    from actual captured bytes, NOT from memory/assumptions.
    
    Known patterns (unverified):
    - User input is typically echoed in interactive mode
    - Assistant output streams continuously after user input
    - Tool use blocks may have delimiters like function call syntax
    - ANSI codes used for colors and formatting
    
    For P1, this implements a best-effort parser that will be
    refined in Task 4 verification once Claude Code is installed.
    """
    
    # Version detection (to be captured from 2.1.37 (Claude Code))
    VERSION_PATTERN = rb'Claude.*?([0-9]+\.[0-9]+\.[0-9]+)'
    
    def __init__(self, agent_id: str, agent_version: Optional[str] = None):
        """
        Args:
            agent_id: Session-specific agent ID (e.g., 'claude-code-<uuid>')
            agent_version: Claude Code version string
        """
        self.agent_id = agent_id
        self.agent_name = "claude-code"
        self.agent_version = agent_version
        
        # Parser state
        self.state = ParseState.WAITING_FOR_USER
        self.buffer = bytearray()
        self.current_atom_start = 0
        
    def strip_ansi(self, data: bytes) -> str:
        """Remove ANSI escape sequences from bytes."""
        stripped = ANSI_CSI_PATTERN.sub(b'', data)
        return stripped.decode('utf-8', errors='replace')
    
    def parse_chunk(self, data: bytes, on_atom: Callable[[Atom], None]):
        """
        Parse a chunk of output data and emit atoms.
        
        Args:
            data: Raw bytes from PTY
            on_atom: Callback to receive completed atoms
            
        Note: This is a simplified parser for P1. Full role detection
        requires analysis of actual Claude Code output patterns captured
        in the ground truth session (Task 4 verification step).
        """
        self.buffer.extend(data)
        
        # For P1, we implement a basic heuristic parser:
        # - Assume initial input is user
        # - Response that follows is assistant
        # - Tool calls would be detected by specific patterns
        
        # This is intentionally simple pending ground truth capture
        # Real implementation will parse based on actual delimiters
        
    def create_atom(self, role: str, content_raw: bytes, tool_payload: Optional[str] = None) -> Atom:
        """Create an Atom from captured content."""
        return Atom(
            role=role,
            content=self.strip_ansi(content_raw),
            content_raw=content_raw,
            timestamp="",  # Will be set by __post_init__
            agent_id=self.agent_id,
            agent_name=self.agent_name,
            agent_version=self.agent_version,
            verbatim=True,
            surface="cli",
            tool_payload=tool_payload
        )
    
    def flush(self, on_atom: Callable[[Atom], None]):
        """Flush any remaining buffered data as atoms."""
        if self.buffer:
            # Emit remaining buffer as assistant response
            atom = self.create_atom("assistant", bytes(self.buffer))
            on_atom(atom)
            self.buffer.clear()


def detect_version(data: bytes) -> Optional[str]:
    """Extract version from 2.1.37 (Claude Code) output."""
    match = re.search(ClaudeCodeProfile.VERSION_PATTERN, data)
    if match:
        return match.group(1).decode('utf-8')
    return None
