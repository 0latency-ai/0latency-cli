"""Tests for large paste chunking."""

import time
import pytest
from zerolatency_cli.atom import Atom
from zerolatency_cli.chunking import chunk_utf8_safe, chunk_atom


def test_small_content_not_chunked():
    """Test that small content is not chunked."""
    data = b"Small content" * 100  # ~1.3KB
    chunks = chunk_utf8_safe(data)
    
    assert len(chunks) == 1
    assert chunks[0] == data


def test_large_content_chunked():
    """Test that large content is chunked at UTF-8 boundaries."""
    # Create 200KB of data
    data = "Test content \u2764\uFE0F " * 20000  # Mix ASCII + emoji
    data_bytes = data.encode('utf-8')
    
    chunks = chunk_utf8_safe(data_bytes, max_chunk_size=65536)
    
    # Should have multiple chunks
    assert len(chunks) >= 3
    
    # Each chunk should be <= 64KB
    for chunk in chunks:
        assert len(chunk) <= 65536
    
    # Reassembly should match original
    reassembled = b''.join(chunks)
    assert reassembled == data_bytes
    
    # Each chunk should be valid UTF-8
    for chunk in chunks:
        chunk.decode('utf-8')  # Should not raise


def test_chunk_atom_1m_chars():
    """Test chunking of 1M-char atom (G4 gate requirement)."""
    # Generate 1M chars with mix of ASCII and multibyte chars
    content = "x" * 950000 + "\u2764\uFE0F" * 25000  # ~1M chars, ~1.1MB bytes
    content_bytes = content.encode('utf-8')
    
    # Create test atom
    atom = Atom(
        role="user",
        content=content,
        content_raw=content_bytes,
        timestamp="2026-01-01T00:00:00Z",
        agent_id="test",
        agent_name="test",
    )
    
    start_time = time.time()
    chunked = chunk_atom(atom)
    elapsed = time.time() - start_time
    
    # Should complete quickly (< 5 seconds per scope doc)
    assert elapsed < 5.0, f"Chunking took {elapsed:.2f}s, expected < 5s"
    
    # Should have multiple chunks (approx 17 for 1.1MB at 64KB/chunk)
    assert len(chunked) >= 15
    assert len(chunked) <= 20
    
    # Chunk metadata should be correct
    for i, chunk in enumerate(chunked):
        assert chunk.chunk_index == i
        assert chunk.chunk_total == len(chunked)
    
    # Reassembly should match original
    reassembled = b''.join(c.content_raw for c in chunked)
    assert reassembled == content_bytes
    
    # All chunks except possibly last should be close to 64KB
    for chunk in chunked[:-1]:
        assert len(chunk.content_raw) >= 60000  # Close to 64KB
        assert len(chunk.content_raw) <= 65536


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
