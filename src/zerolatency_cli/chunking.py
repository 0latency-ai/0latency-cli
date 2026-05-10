"""UTF-8-safe chunking for large pastes."""

import sys
from typing import List
from zerolatency_cli.atom import Atom


def chunk_utf8_safe(data: bytes, max_chunk_size: int = 65536) -> List[bytes]:
    """
    Split data into chunks at UTF-8 character boundaries.
    
    Args:
        data: Data to chunk
        max_chunk_size: Maximum chunk size in bytes (default 64KB)
        
    Returns:
        List of chunks, each <= max_chunk_size and UTF-8-safe
    """
    if len(data) <= max_chunk_size:
        return [data]
    
    chunks = []
    pos = 0
    
    while pos < len(data):
        # Calculate chunk end
        end = min(pos + max_chunk_size, len(data))
        
        # If not at the end, scan backwards to find UTF-8 boundary
        if end < len(data):
            # Scan backwards up to 4 bytes to find valid UTF-8 boundary
            # (UTF-8 chars can be 1-4 bytes)
            for i in range(min(4, end - pos)):
                try:
                    # Try to decode from pos to (end - i)
                    chunk = data[pos:end - i]
                    chunk.decode('utf-8')
                    # Success - this is a valid boundary
                    chunks.append(chunk)
                    pos = end - i
                    break
                except UnicodeDecodeError:
                    # Not a valid boundary, try one byte earlier
                    continue
            else:
                # Couldn't find valid boundary in last 4 bytes
                # This shouldn't happen with well-formed UTF-8, but fallback
                chunks.append(data[pos:end])
                pos = end
        else:
            # Last chunk
            chunks.append(data[pos:end])
            pos = end
    
    return chunks


def chunk_atom(atom: Atom, max_chunk_size: int = 65536) -> List[Atom]:
    """
    Chunk an atom if content exceeds max_chunk_size.
    
    Args:
        atom: Atom to potentially chunk
        max_chunk_size: Maximum chunk size in bytes
        
    Returns:
        List of atoms (original if < max_chunk_size, chunked if larger)
    """
    if len(atom.content_raw) <= max_chunk_size:
        return [atom]
    
    # Log warning for very large pastes
    if len(atom.content_raw) > 1_000_000:
        print(f"\nWARNING: Very large paste ({len(atom.content_raw):,} bytes). Chunking...", file=sys.stderr)
    
    # Chunk the raw content
    chunks = chunk_utf8_safe(atom.content_raw, max_chunk_size)
    
    # Create atom for each chunk
    chunked_atoms = []
    for i, chunk in enumerate(chunks):
        # Create new atom with same metadata
        chunked_atom = Atom(
            role=atom.role,
            content=chunk.decode('utf-8', errors='replace'),
            content_raw=chunk,
            timestamp=atom.timestamp,
            agent_id=atom.agent_id,
            agent_name=atom.agent_name,
            agent_version=atom.agent_version,
            verbatim=atom.verbatim,
            surface=atom.surface,
            tool_payload=atom.tool_payload,
            tenant_id=atom.tenant_id,
            chunk_index=i,
            chunk_total=len(chunks),
        )
        chunked_atoms.append(chunked_atom)
    
    return chunked_atoms
