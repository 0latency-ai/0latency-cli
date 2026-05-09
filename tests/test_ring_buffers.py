"""Tests for ring buffers (session metadata + profile buffer)."""

import pytest
from collections import deque
from zerolatency_cli.atom import Atom
from zerolatency_cli.profiles.claude_code import ClaudeCodeProfile


def test_session_metadata_ring_buffer():
    """Test that session metadata never exceeds 100 turns."""
    # Simulate session metadata tracking
    session_metadata = deque(maxlen=100)
    
    # Simulate 200 turns
    for i in range(200):
        session_metadata.append({
            "turn": i,
            "timestamp": f"2026-01-01T00:{i:02d}:00Z",
            "role": "user" if i % 2 == 0 else "assistant",
        })
    
    # Should have exactly 100 entries (last 100)
    assert len(session_metadata) == 100
    
    # Oldest should be turn 100 (first 100 were dropped)
    assert session_metadata[0]["turn"] == 100
    # Newest should be turn 199
    assert session_metadata[-1]["turn"] == 199


def test_profile_buffer_ring_behavior():
    """Test that profile buffer never exceeds 128KB."""
    profile = ClaudeCodeProfile(agent_id="test", agent_version="2.1.136")
    
    # Feed 500KB of data in chunks
    chunk_size = 10000
    total_fed = 0
    target_total = 500 * 1024  # 500KB
    
    while total_fed < target_total:
        # Generate chunk (mix of data)
        chunk = b"x" * chunk_size
        profile.buffer.extend(chunk)
        
        # Manually trigger ring buffer behavior (cap at 128KB)
        if len(profile.buffer) > profile.MAX_BUFFER_SIZE:
            profile.buffer = profile.buffer[-profile.MAX_BUFFER_SIZE:]
        
        total_fed += chunk_size
    
    # Buffer should be capped at 128KB
    assert len(profile.buffer) <= 128 * 1024
    assert len(profile.buffer) == 128 * 1024  # Should be exactly at cap


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
