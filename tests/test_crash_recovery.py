"""Tests for crash recovery via rolling buffer."""

import os
import sys
import time
import signal
import subprocess
import json
from pathlib import Path
import pytest

from zerolatency_cli.recovery import (
    get_sessions_dir,
    get_session_buffer_path,
    detect_orphaned_sessions,
    write_atom_to_buffer,
    cleanup_session_buffer,
)
from zerolatency_cli.atom import Atom


def test_rolling_buffer_write():
    """Test that atoms are written to rolling buffer and fsynced."""
    session_id = "test-session-001"
    sessions_dir = get_sessions_dir()
    
    # Create test atoms
    atom1 = Atom(
        role="user",
        content="test input",
        content_raw=b"test input",
        timestamp="2026-01-01T00:00:00Z",
        agent_id="test-agent",
        agent_name="test",
    )
    
    atom2 = Atom(
        role="assistant",
        content="test output",
        content_raw=b"test output",
        timestamp="2026-01-01T00:00:01Z",
        agent_id="test-agent",
        agent_name="test",
    )
    
    # Write atoms to buffer
    write_atom_to_buffer(atom1, session_id)
    write_atom_to_buffer(atom2, session_id)
    
    # Verify buffer file exists and has 2 lines
    buffer_path = get_session_buffer_path(session_id)
    assert buffer_path.exists()
    
    with open(buffer_path, 'r') as f:
        lines = f.readlines()
    
    assert len(lines) == 2
    
    # Verify atoms can be deserialized
    atom1_dict = json.loads(lines[0])
    atom2_dict = json.loads(lines[1])
    
    assert atom1_dict['role'] == 'user'
    assert atom2_dict['role'] == 'assistant'
    
    # Cleanup
    cleanup_session_buffer(session_id)
    assert not buffer_path.exists()


def test_orphaned_session_detection():
    """Test detection of orphaned sessions after crash."""
    session_id = "test-orphaned-session"
    
    # Create a fake orphaned session
    atom = Atom(
        role="user",
        content="orphaned atom",
        content_raw=b"orphaned atom",
        timestamp="2026-01-01T00:00:00Z",
        agent_id="test-agent",
        agent_name="test",
    )
    
    write_atom_to_buffer(atom, session_id)
    
    # Wait to ensure file is stale (> 5 seconds old)
    # For testing, we'll just manually set mtime
    buffer_path = get_session_buffer_path(session_id)
    old_time = time.time() - 10  # 10 seconds ago
    os.utime(buffer_path, (old_time, old_time))
    
    # Detect orphaned sessions
    orphaned = detect_orphaned_sessions()
    
    assert len(orphaned) >= 1
    
    # Find our test session
    found = False
    for path, count in orphaned:
        if session_id in str(path):
            assert count == 1
            found = True
            break
    
    assert found, f"Test session {session_id} not found in orphaned sessions"
    
    # Cleanup
    cleanup_session_buffer(session_id)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
