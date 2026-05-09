"""Tests for backpressure handling and atom queue."""

import time
import threading
from unittest.mock import patch, MagicMock
import pytest

from zerolatency_cli.atom import Atom
from zerolatency_cli.storage import AtomQueue, RetryWorker, write_atom_cloud


def test_atom_queue_basic():
    """Test basic queue operations."""
    queue = AtomQueue()
    
    # Create test atoms
    atoms = []
    for i in range(5):
        atom = Atom(
            role="user",
            content=f"test {i}",
            content_raw=f"test {i}".encode(),
            timestamp="2026-01-01T00:00:00Z",
            agent_id="test",
            agent_name="test",
        )
        atoms.append(atom)
        queue.enqueue(atom)
    
    assert queue.size() == 5
    
    # Dequeue all
    for i in range(5):
        atom = queue.dequeue()
        assert atom is not None
        assert atom.content == f"test {i}"
    
    # Queue should be empty
    assert queue.size() == 0
    assert queue.dequeue() is None


def test_atom_queue_drop_oldest():
    """Test that queue drops oldest when hitting 10K cap."""
    queue = AtomQueue()
    
    # Fill queue to capacity
    for i in range(AtomQueue.MAX_SIZE + 100):
        atom = Atom(
            role="user",
            content=f"atom {i}",
            content_raw=f"atom {i}".encode(),
            timestamp="2026-01-01T00:00:00Z",
            agent_id="test",
            agent_name="test",
        )
        queue.enqueue(atom)
    
    # Queue should be at max size
    assert queue.size() == AtomQueue.MAX_SIZE
    
    # First atom should be the 100th one (first 100 dropped)
    first_atom = queue.dequeue()
    assert "atom 100" in first_atom.content


def test_retry_worker_exponential_backoff():
    """Test that retry worker uses exponential backoff."""
    queue = AtomQueue()
    
    # Create atom
    atom = Atom(
        role="user",
        content="test",
        content_raw=b"test",
        timestamp="2026-01-01T00:00:00Z",
        agent_id="test",
        agent_name="test",
    )
    
    queue.enqueue(atom)
    
    # Mock write_atom_cloud to fail first 3 times, then succeed
    call_count = 0
    call_times = []
    
    def mock_write_cloud(a, token):
        nonlocal call_count
        call_times.append(time.time())
        call_count += 1
        return call_count > 3  # Succeed on 4th try
    
    with patch('zerolatency_cli.storage.write_atom_cloud', side_effect=mock_write_cloud):
        worker = RetryWorker(queue, "fake-token", daemon=False)
        worker.start()
        
        # Wait for retries to complete
        time.sleep(10)  # 1s + 2s + 4s = 7s + overhead
        worker.stop()
        worker.join(timeout=2)
    
    # Should have retried with backoff
    assert call_count >= 3
    
    # Verify exponential backoff (each gap should be ~1s, 2s, 4s)
    if len(call_times) >= 3:
        gap1 = call_times[1] - call_times[0]
        gap2 = call_times[2] - call_times[1]
        assert 0.8 < gap1 < 1.5  # ~1s
        assert 1.5 < gap2 < 3.0  # ~2s


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
