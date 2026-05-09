"""Generic fallback profile for unknown CLI agents."""

import re
import time
from typing import Callable, Optional
from zerolatency_cli.profiles.base import Profile, Atom as ProfileAtom
from zerolatency_cli.atom import Atom


class GenericProfile(Profile):
    """
    Generic fallback profile for unknown CLI agents.
    
    Uses idle-detection for turn boundaries: > 2s of idle on stdout
    indicates end of a turn. No agent-specific parsing - just captures
    stdin (user) and stdout (assistant) as-is.
    """
    
    __version__ = "0.1.0"
    __compat_agent_version__ = "unknown"
    agent_name = "generic"
    
    # Idle threshold: 2 seconds of no output = turn complete
    IDLE_THRESHOLD_SECONDS = 2.0
    
    def __init__(self, agent_id: Optional[str] = None, agent_version: Optional[str] = None):
        self.agent_id = agent_id or "generic"
        self.agent_version = agent_version or "unknown"
        self.buffer = bytearray()
        self.last_output_time = time.time()
    
    # ========================================================================
    # Profile ABC Implementation
    # ========================================================================
    
    def detect_role(self, buffer: bytes) -> Optional[ProfileAtom]:
        """
        Detect role from buffer.
        
        For generic profile, simple heuristic:
        - Lines with common REPL prompts (>>>, $, >) = user
        - Everything else = assistant
        """
        lines = buffer.split(b'\n')
        
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            
            # Check for common prompt patterns
            prompt_markers = [b'>>>', b'>>', b'$ ', b'> ']
            is_user = any(stripped.startswith(marker) for marker in prompt_markers)
            
            return ProfileAtom(
                role="user" if is_user else "assistant",
                content=stripped.decode('utf-8', errors='replace'),
                content_raw=stripped,
                metadata={}
            )
        
        return None
    
    def is_complete_turn(self, buffer: bytes) -> bool:
        """Check if buffer contains a complete turn."""
        return len(buffer.strip()) > 0
    
    def extract_metadata(self, buffer: bytes) -> dict:
        """Extract metadata from buffer."""
        return {
            "agent_type": "generic",
            "detection_method": "idle-threshold"
        }
    
    # ========================================================================
    # Streaming API for live capture
    # ========================================================================
    
    def parse_chunk(self, data: bytes, on_atom: Callable[[Atom], None]):
        """Parse a chunk of output data using idle detection."""
        if not data:
            return
        
        self.buffer.extend(data)
        self.last_output_time = time.time()
    
    def check_idle_and_flush(self, on_atom: Callable[[Atom], None], force: bool = False):
        """Check if idle threshold reached and flush if so."""
        current_time = time.time()
        idle_duration = current_time - self.last_output_time
        
        if (force or idle_duration >= self.IDLE_THRESHOLD_SECONDS) and self.buffer:
            atom = self.create_atom("assistant", bytes(self.buffer))
            on_atom(atom)
            self.buffer.clear()
    
    def create_atom(self, role: str, content_raw: bytes) -> Atom:
        """Create an Atom from captured content."""
        return Atom(
            role=role,
            content=content_raw.decode('utf-8', errors='replace'),
            content_raw=content_raw,
            timestamp="",
            agent_id=self.agent_id,
            agent_name=self.agent_name,
            agent_version=self.agent_version,
            verbatim=True,
            surface="cli",
            tool_payload=None
        )
    
    def flush(self, on_atom: Callable[[Atom], None]):
        """Flush any remaining buffered data as atoms."""
        self.check_idle_and_flush(on_atom, force=True)
