"""Claude Code role detection profile (hardcoded for P1)."""

import re
import uuid
from typing import Callable, Optional
from zerolatency_cli.atom import Atom

# ANSI CSI sequence regex (Control Sequence Introducer)
ANSI_CSI_PATTERN = re.compile(rb'\x1b\[[0-?]*[ -/]*[@-~]')

class ClaudeCodeProfile:
    """
    Role detection profile for Claude Code CLI.
    
    P1 SCOPE (--print mode only):
    ==============================
    Verified with Claude Code 2.1.136 on 2026-05-08
    
    In --print mode:
    - User atom: Command line arguments (e.g., --print "query")
    - Assistant atom: Complete stdout (ANSI-stripped)
    - Tool calls: Internal only, NOT visible in output
    
    Interactive mode parsing (validated 2026-05-08):
    ==================================================
    - Detects prompt markers (green > with ANSI codes)
    - Splits into user/assistant turns
    - Alternates roles appropriately
    
    Ground truth capture:
    - Tested with: claude --bare --print "List files using Bash"
    - Tool executed: Yes (Bash tool runs)
    - Tool visible in output: No (result incorporated into response text)
    - Conclusion: For P1 --print mode, parse as simple user/assistant pairs
    
    P2 will add:
    - Tool delimiter detection (⏺, ⎿, or actual delimiters from real session)
    - Streaming turn-by-turn atom emission
    """
    
    VERSION_PATTERN = rb'([0-9]+\.[0-9]+\.[0-9]+)\s+\(Claude Code\)'
    # Prompt pattern: green ">" with ANSI codes
    PROMPT_PATTERN = rb'\x1b\[32m>\x1b\[0m '
    
    def __init__(self, agent_id: str, agent_version: Optional[str] = None, user_query: Optional[str] = None):
        """
        Args:
            agent_id: Session-specific agent ID (e.g., 'claude-code-<uuid>')
            agent_version: Claude Code version string (e.g., '2.1.136')
            user_query: For --print mode, the query from command line args
        """
        self.agent_id = agent_id
        self.agent_name = "claude-code"
        self.agent_version = agent_version
        self.user_query = user_query
        self.buffer = bytearray()
        self.user_atom_emitted = False
        self.is_interactive = user_query is None
        
    def strip_ansi(self, data: bytes) -> str:
        """Remove ANSI escape sequences from bytes."""
        stripped = ANSI_CSI_PATTERN.sub(b'', data)
        return stripped.decode('utf-8', errors='replace')
    
    def parse_interactive(self, data: bytes, on_atom: Callable[[Atom], None]):
        """
        Parse interactive session with turn detection.
        
        Splits by prompt markers and emits user/assistant atoms.
        """
        # Split by prompt pattern
        parts = re.split(self.PROMPT_PATTERN, data)
        
        # First part is initial output (version, etc.) - treat as assistant if non-empty
        if parts[0].strip():
            # Skip if it's just the version header
            stripped = self.strip_ansi(parts[0]).strip()
            if stripped and not stripped.startswith("Claude Code"):
                atom = self.create_atom("assistant", parts[0])
                on_atom(atom)
        
        # Remaining parts alternate: user input, assistant response, user input, ...
        # Each part after a prompt split contains: user_input\n...assistant_response
        for i, part in enumerate(parts[1:], start=1):
            if not part.strip():
                continue
            
            # Try to split on first newline to separate user input from assistant response
            lines = part.split(b'\n', 1)
            
            if len(lines) >= 1 and lines[0].strip():
                # User input (the line after the prompt)
                user_atom = self.create_atom("user", lines[0] + b'\n')
                on_atom(user_atom)
            
            if len(lines) == 2 and lines[1].strip():
                # Assistant response (everything after user input until next prompt)
                assistant_atom = self.create_atom("assistant", lines[1])
                on_atom(assistant_atom)
    
    def parse_chunk(self, data: bytes, on_atom: Callable[[Atom], None]):
        """
        Parse a chunk of output data and emit atoms.
        
        Routes to interactive parser or --print mode parser based on configuration.
        
        Args:
            data: Raw bytes from PTY
            on_atom: Callback to receive completed atoms
        """
        if self.is_interactive:
            # Interactive mode: parse turns immediately
            self.parse_interactive(data, on_atom)
        else:
            # --print mode: emit user atom once, then accumulate
            if not self.user_atom_emitted and self.user_query:
                user_atom = self.create_atom(
                    role="user",
                    content_raw=self.user_query.encode('utf-8')
                )
                on_atom(user_atom)
                self.user_atom_emitted = True
            
            # Accumulate output
            self.buffer.extend(data)
        
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
            # Emit complete assistant response (--print mode)
            atom = self.create_atom("assistant", bytes(self.buffer))
            on_atom(atom)
            self.buffer.clear()


def detect_version(data: bytes) -> Optional[str]:
    """Extract version from claude --version output."""
    match = re.search(ClaudeCodeProfile.VERSION_PATTERN, data)
    if match:
        return match.group(1).decode('utf-8')
    return None
