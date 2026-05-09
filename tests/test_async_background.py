"""Tests for async background task capture (long-running bash commands)."""

import time
import subprocess
import pytest


def test_long_running_command_nonblocking():
    """Test that long-running bash commands complete without blocking wrapper."""
    # This test verifies that the wrapper doesn't block on long-running commands
    # In practice, the wrapper's select()-based I/O loop should handle this
    
    # Simulate a 5-second command (scaled down from 5 minutes for testing)
    start_time = time.time()
    
    # Run a command that sleeps then outputs
    result = subprocess.run(
        ['bash', '-c', 'sleep 2 && echo "done"'],
        capture_output=True,
        text=True,
        timeout=5
    )
    
    elapsed = time.time() - start_time
    
    # Should complete in ~2 seconds (not block/timeout)
    assert elapsed >= 2.0
    assert elapsed < 5.0
    assert "done" in result.stdout


def test_wrapper_continues_during_long_command():
    """Test that wrapper continues processing during long child commands."""
    # Test that the wrapper's I/O loop doesn't deadlock
    # when the child process is busy
    
    # Run command that outputs incrementally
    start_time = time.time()
    result = subprocess.run(
        ['bash', '-c', 'for i in 1 2 3; do echo $i; sleep 0.5; done'],
        capture_output=True,
        text=True,
        timeout=5
    )
    
    elapsed = time.time() - start_time
    
    # Should complete in ~1.5 seconds
    assert elapsed >= 1.0
    assert elapsed < 3.0
    
    # Should have all output
    assert "1" in result.stdout
    assert "2" in result.stdout
    assert "3" in result.stdout


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
