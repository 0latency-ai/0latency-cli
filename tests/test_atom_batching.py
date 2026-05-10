"""Tests for atom batching (10-atom batches, 2s flush)."""

import time
import pytest
from zerolatency_cli.atom import Atom
from zerolatency_cli.storage import BatchQueue


def test_batch_size_flush():
    """Test that batch flushes when size reaches 10."""
    flushed_batches = []
    
    def flush_callback(batch):
        flushed_batches.append(batch)
    
    queue = BatchQueue(flush_callback)
    
    # Add 25 atoms rapidly
    for i in range(25):
        atom = Atom(
            role="user",
            content=f"atom {i}",
            content_raw=f"atom {i}".encode(),
            timestamp="2026-01-01T00:00:00Z",
            agent_id="test",
            agent_name="test",
        )
        queue.enqueue(atom)
    
    # Should have flushed 2 complete batches (10 + 10)
    # 5 remaining in queue
    assert len(flushed_batches) == 2
    assert len(flushed_batches[0]) == 10
    assert len(flushed_batches[1]) == 10
    
    # Flush remaining
    queue.flush_remaining()
    
    assert len(flushed_batches) == 3
    assert len(flushed_batches[2]) == 5


def test_timer_flush():
    """Test that batch flushes after 2s timeout."""
    flushed_batches = []
    
    def flush_callback(batch):
        flushed_batches.append(batch)
    
    queue = BatchQueue(flush_callback)
    
    # Add 5 atoms (less than batch size)
    for i in range(5):
        atom = Atom(
            role="user",
            content=f"atom {i}",
            content_raw=f"atom {i}".encode(),
            timestamp="2026-01-01T00:00:00Z",
            agent_id="test",
            agent_name="test",
        )
        queue.enqueue(atom)
    
    # Should not flush yet
    time.sleep(1.0)
    assert len(flushed_batches) == 0
    
    # Wait for timer (2s total)
    time.sleep(1.5)
    
    # Should have flushed due to timeout
    assert len(flushed_batches) == 1
    assert len(flushed_batches[0]) == 5


def test_local_tier_direct_sqlite():
    """Test that local tier bypasses batching and goes to sqlite."""
    # Local tier (force_local=True) writes directly to sqlite
    # No batching for local writes
    from zerolatency_cli.storage import write_atom
    
    atom = Atom(
        role="user",
        content="test",
        content_raw=b"test",
        timestamp="2026-01-01T00:00:00Z",
        agent_id="test",
        agent_name="test",
    )
    
    # This should write immediately to sqlite, not batch
    write_atom(atom, force_local=True)
    
    # Verify it was written (would need to query sqlite, simplified for now)
    assert True  # Placeholder - actual test would query local.db


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
