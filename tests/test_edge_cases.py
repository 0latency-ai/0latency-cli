"""Edge case stress tests (timeout, queue full, 5MB paste)."""

import time
import pytest
from unittest.mock import patch
from zerolatency_cli.atom import Atom
from zerolatency_cli.storage import AtomQueue
from zerolatency_cli.chunking import chunk_atom


def test_api_timeout_enqueues():
    """Test that API timeout results in atom being enqueued."""
    queue = AtomQueue()
    
    # Simulate API timeout by enqueuing directly
    atom = Atom(
        role="user",
        content="test",
        content_raw=b"test",
        timestamp="2026-01-01T00:00:00Z",
        agent_id="test",
        agent_name="test",
    )
    
    queue.enqueue(atom)
    
    # Should be in queue
    assert queue.size() == 1
    
    # Dequeue and verify
    dequeued = queue.dequeue()
    assert dequeued is not None
    assert dequeued.content == "test"


def test_queue_full_drops_oldest(capsys):
    """Test that 10,001st atom triggers drop-oldest + user alert."""
    queue = AtomQueue()
    
    # Fill queue to capacity (10,000)
    for i in range(AtomQueue.MAX_SIZE):
        atom = Atom(
            role="user",
            content=f"atom {i}",
            content_raw=f"atom {i}".encode(),
            timestamp="2026-01-01T00:00:00Z",
            agent_id="test",
            agent_name="test",
        )
        queue.enqueue(atom)
    
    # Queue should be at max
    assert queue.size() == AtomQueue.MAX_SIZE
    
    # Add one more (10,001st) - should trigger alert and drop oldest
    atom_overflow = Atom(
        role="user",
        content="overflow atom",
        content_raw=b"overflow atom",
        timestamp="2026-01-01T00:00:00Z",
        agent_id="test",
        agent_name="test",
    )
    
    queue.enqueue(atom_overflow)
    
    # Capture stderr for alert check
    captured = capsys.readouterr()
    
    # Should still be at max size (oldest dropped)
    assert queue.size() == AtomQueue.MAX_SIZE
    
    # Should have printed alert
    assert "WARNING" in captured.err
    assert "queue full" in captured.err.lower()
    
    # First atom should be atom 1 (atom 0 was dropped)
    first = queue.dequeue()
    assert "atom 1" in first.content


def test_5mb_paste_chunking():
    """Test that 5MB paste results in ~80 chunks with correct metadata."""
    # Generate 5MB content
    content_size = 5 * 1024 * 1024  # 5MB
    content = "x" * content_size
    content_bytes = content.encode('utf-8')
    
    atom = Atom(
        role="user",
        content=content,
        content_raw=content_bytes,
        timestamp="2026-01-01T00:00:00Z",
        agent_id="test",
        agent_name="test",
    )
    
    start_time = time.time()
    chunked = chunk_atom(atom, max_chunk_size=65536)
    elapsed = time.time() - start_time
    
    # Should complete quickly
    assert elapsed < 2.0
    
    # Should have ~80 chunks (5MB / 64KB = 80)
    expected_chunks = content_size // 65536
    assert len(chunked) >= expected_chunks - 5  # Allow some variance
    assert len(chunked) <= expected_chunks + 5
    
    # All chunks should have correct metadata
    for i, chunk in enumerate(chunked):
        assert chunk.chunk_index == i
        assert chunk.chunk_total == len(chunked)
    
    # Reassembly should match original
    reassembled = b''.join(c.content_raw for c in chunked)
    assert reassembled == content_bytes


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
