"""Claude Code profile with role detection."""

import re
from typing import Callable, Optional
from zerolatency_cli.profiles.base import Profile, Atom as ProfileAtom
from zerolatency_cli.atom import Atom

# ANSI CSI sequence regex
ANSI_CSI_PATTERN = re.compile(rb"\x1b\[[0-?]*[ -/]*[@-~]")


class ClaudeCodeProfile(Profile):
    """
    Role detection profile for Claude Code CLI.
    
    Implements both:
    1. Profile ABC interface (detect_role, is_complete_turn) for fixture testing
    2. P1 streaming API (parse_chunk, flush) for live capture
    
    Tested with Claude Code 2.1.136.
    """
    
    __version__ = "0.2.0"
    __compat_agent_version__ = "2.1.136"
    agent_name = "claude-code"
    
    VERSION_PATTERN = rb"([0-9]+\.[0-9]+\.[0-9]+)\s+\(Claude Code\)"
    # Prompt pattern: green ">" with ANSI codes
    PROMPT_PATTERN = re.compile(rb"\x1b\[32m>\x1b\[0m ")
    # Interactive PTY prompt marker (UTF-8 ❯)
    PROMPT_MARKER = b"\xe2\x9d\xaf"

    
    def __init__(self, agent_id: Optional[str] = None, agent_version: Optional[str] = None, 
                 user_query: Optional[str] = None):
        """
        Args:
            agent_id: Session-specific agent ID (e.g., "claude-code-<uuid>")
            agent_version: Claude Code version string (e.g., "2.1.136")
            user_query: For --print mode, the query from command line args
        """
        self.agent_id = agent_id or "claude-code"
        self.agent_version = agent_version or self.__compat_agent_version__
        self.user_query = user_query
        self.buffer = bytearray()
        self.user_atom_emitted = False
        self.is_interactive = user_query is None
    
    # ========================================================================
    # Profile ABC Implementation (for fixture testing)
    # ========================================================================
    
    def detect_role(self, buffer: bytes) -> Optional[ProfileAtom]:
        """
        Detect role from buffer.
        
        For testing against complete fixture buffers. Returns the first
        detected atom (user or assistant).
        """
        # Split by prompt pattern
        parts = re.split(self.PROMPT_PATTERN, buffer)
        
        # Skip header if present
        if parts[0].strip() and not parts[0].strip().startswith(b"Claude Code"):
            # First part is assistant content
            return ProfileAtom(
                role="assistant",
                content=self.strip_ansi(parts[0]),
                content_raw=parts[0],
                metadata={}
            )
        
        # Look for first user/assistant pair
        for part in parts[1:]:
            if not part.strip():
                continue
            
            lines = part.split(b"\n", 1)
            if len(lines) >= 1 and lines[0].strip():
                # User input
                return ProfileAtom(
                    role="user",
                    content=self.strip_ansi(lines[0]),
                    content_raw=lines[0],
                    metadata={}
                )
        
        return None
    
    def is_complete_turn(self, buffer: bytes) -> bool:
        """Check if buffer contains at least one complete turn."""
        cleaned = self.strip_script_header(buffer)
        if self.PROMPT_MARKER in cleaned:
            parts = cleaned.split(self.PROMPT_MARKER)
            for part in parts[1:]:
                text = self.strip_ansi(part).strip()
                if text and len(text) > 3:
                    lines_split = text.split("\n", 1)
                    if lines_split[0].strip():
                        return ProfileAtom(role="user", content=lines_split[0].strip(),
                                         content_raw=part[:200], metadata={})
        parts = re.split(self.PROMPT_PATTERN, cleaned)
        for part in parts[1:]:
            if not part.strip():
                continue
            lines_split = part.split(b"\n", 1)
            if len(lines_split) >= 1 and lines_split[0].strip():
                return ProfileAtom(role="user", content=self.strip_ansi(lines_split[0]),
                                 content_raw=lines_split[0], metadata={})
        return None

    def extract_metadata(self, buffer: bytes) -> dict:
        """Extract metadata from buffer."""
        metadata = {}
        
        # Check for tool use markers (dim text)
        if b"\x1b[2m" in buffer:
            metadata["has_tool_use"] = True
        
        return metadata
    
    def strip_script_header(self, data: bytes) -> bytes:
        """Strip script command header/footer if present."""
        if data.startswith(b"Script started on"):
            first_newline = data.find(b"\n")
            if first_newline > 0:
                data = data[first_newline + 1:]
        if b"Script done on" in data:
            footer_start = data.rfind(b"Script done on")
            if footer_start > 0:
                data = data[:footer_start]
        return data
    
    # ========================================================================
    # P1 Streaming API (for backward compatibility)
    # ========================================================================
    
    def strip_ansi(self, data: bytes) -> str:
        """Remove ANSI escape sequences from bytes."""
        stripped = ANSI_CSI_PATTERN.sub(b"", data)
        return stripped.decode("utf-8", errors="replace")
    
    def parse_interactive(self, data: bytes, on_atom: Callable[[Atom], None]):
        """Parse interactive PTY session with turn detection."""
        # Strip script header/footer
        cleaned = self.strip_script_header(data)
        
        # Find all prompt positions
        prompt_positions = []
        pos = 0
        while True:
            idx = cleaned.find(self.PROMPT_MARKER, pos)
            if idx == -1:
                break
            prompt_positions.append(idx)
            pos = idx + len(self.PROMPT_MARKER)
        
        if not prompt_positions:
            # Fall back to legacy pattern
            parts = re.split(self.PROMPT_PATTERN, cleaned)
            if len(parts) > 1:
                for part in parts[1:]:
                    if not part.strip():
                        continue
                    lines = part.split(b"\n", 1)
                    if len(lines) >= 1 and lines[0].strip():
                        user_atom = self.create_atom("user", lines[0])
                        on_atom(user_atom)
                    if len(lines) == 2 and lines[1].strip():
                        assistant_atom = self.create_atom("assistant", lines[1])
                        on_atom(assistant_atom)
            return
        
        # Process segments between prompts
        for i in range(len(prompt_positions)):
            start = prompt_positions[i] + len(self.PROMPT_MARKER)
            end = prompt_positions[i + 1] if i + 1 < len(prompt_positions) else len(cleaned)
            
            segment = cleaned[start:end]
            text = self.strip_ansi(segment).strip()
            
            if not text:
                continue
            
            # Split into lines
            lines = text.split("\n")
            
            # First non-empty line is user input
            user_line = None
            user_idx = 0
            for idx, line in enumerate(lines):
                if line.strip() and len(line.strip()) > 3:
                    user_line = line.strip()
                    user_idx = idx
                    break
            
            if user_line:
                user_atom = self.create_atom("user", user_line.encode("utf-8"))
                on_atom(user_atom)
            
            # Remaining non-empty lines are assistant response
            assistant_lines = []
            for idx in range(user_idx + 1, len(lines)):
                line = lines[idx].strip()
                if line:
                    assistant_lines.append(line)
            
            if assistant_lines:
                assistant_text = " ".join(assistant_lines)
                if len(assistant_text) > 10:
                    assistant_atom = self.create_atom("assistant", assistant_text.encode("utf-8"))
                    on_atom(assistant_atom)
    
    def parse_chunk(self, data: bytes, on_atom: Callable[[Atom], None]):
        """
        Parse a chunk of output data and emit atoms.
        
        P1 streaming API for live capture.
        """
        if self.is_interactive:
            self.parse_interactive(data, on_atom)
        else:
            # --print mode
            if not self.user_atom_emitted and self.user_query:
                user_atom = self.create_atom(
                    role="user",
                    content_raw=self.user_query.encode("utf-8")
                )
                on_atom(user_atom)
                self.user_atom_emitted = True
            
            self.buffer.extend(data)
    
    def create_atom(self, role: str, content_raw: bytes, tool_payload: Optional[str] = None) -> Atom:
        """Create an Atom from captured content."""
        return Atom(
            role=role,
            content=self.strip_ansi(content_raw),
            content_raw=content_raw,
            timestamp="",
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
            atom = self.create_atom("assistant", bytes(self.buffer))
            on_atom(atom)
            self.buffer.clear()


def detect_version(data: bytes) -> Optional[str]:
    """Extract version from claude --version output."""
    match = re.search(ClaudeCodeProfile.VERSION_PATTERN, data)
    if match:
        return match.group(1).decode("utf-8")
    return None
