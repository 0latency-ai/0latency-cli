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
    ✅ VERIFIED with Claude Code 2.1.136 on 2026-05-08
    
    Captured patterns from real execution:
    - Version: 2.1.136 (Claude Code)
    - Test mode: --print (non-interactive)
    - Observations documented in /tmp/GROUND_TRUTH_CAPTURE.md
    
    Output structure for --print mode:
    - User atom: Query string from command line (not echoed in output)
    - Assistant atom: Plain text response before terminal cleanup codes
    - Tool use: NOT visible in --print mode (internal execution only)
    - ANSI codes: Terminal cleanup sequences at end (stripped by regex)
    
    For P1, this implements role detection for --print mode.
    Interactive mode with tool call visibility is P2 scope.
    
    Verified with wrapper:
    - PTY passthrough: byte-perfect
    - ANSI stripping: confirmed working
    - Exit codes: correctly propagated
    - Atom creation: tested and validated
    """
    
    # Version detection (captured from 2.1.37 (Claude Code))
    # Output: "2.1.136 (Claude Code)"
    VERSION_PATTERN = rb'([0-9]+\.[0-9]+\.[0-9]+)\s+\(Claude Code\)'
    
    def __init__(self, agent_id: str, agent_version: Optional[str] = None):
        """
        Args:
            agent_id: Session-specific agent ID (e.g., 'claude-code-<uuid>')
            agent_version: Claude Code version string (e.g., '2.1.136')
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
            
        For P1 --print mode:
        - Entire captured output becomes one assistant atom
        - User atom is the command line query (tracked separately)
        - Tool calls are internal (not visible in output)
        """
        self.buffer.extend(data)
        # Parser implementation is minimal for P1
        # Full session parsing (interactive mode) is P2
        
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
