"""Atom dataclass and serialization."""

import json
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Optional

@dataclass
class Atom:
    """Represents a captured interaction atom (user input, assistant output, or tool use)."""
    
    # Core fields
    role: str  # 'user' | 'assistant' | 'tool_use'
    content: str  # ANSI-stripped text
    content_raw: bytes  # Original bytes with ANSI codes
    
    # Metadata
    timestamp: str  # ISO 8601 UTC
    agent_id: str  # e.g., 'claude-code-<session_uuid>'
    agent_name: str  # e.g., 'claude-code'
    agent_version: Optional[str] = None
    
    # Flags
    verbatim: bool = True
    surface: str = 'cli'
    
    # Optional tool data
    tool_payload: Optional[str] = None  # JSON string if role='tool_use'
    
    # Crash recovery metadata
    recovered: bool = False  # True if atom was imported from orphaned session
    
    # Interactive prompt metadata
    is_interactive_prompt: bool = False  # True if this is an interactive prompt (for future detection)
    
    # Chunking metadata
    chunk_index: Optional[int] = None  # Position in chunk sequence (0-indexed)
    chunk_total: Optional[int] = None  # Total number of chunks
    
    # Tool-call chain metadata
    tool_call_index: Optional[int] = None  # Position in tool-call chain (0-indexed)
    tool_call_total: Optional[int] = None  # Total tool calls in chain
    
    # Database fields
    id: Optional[str] = None  # UUID, generated if not provided
    tenant_id: Optional[str] = None  # Set from credentials
    
    def __post_init__(self):
        """Generate ID and ensure timestamp is set."""
        if self.id is None:
            self.id = str(uuid.uuid4())
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        # Convert bytes to base64 for JSON
        if isinstance(data['content_raw'], bytes):
            import base64
            data['content_raw'] = base64.b64encode(data['content_raw']).decode('ascii')
        return data
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Atom':
        """Create Atom from dictionary."""
        # Convert base64 back to bytes if needed
        if isinstance(data.get('content_raw'), str):
            import base64
            data['content_raw'] = base64.b64decode(data['content_raw'])
        return cls(**data)
