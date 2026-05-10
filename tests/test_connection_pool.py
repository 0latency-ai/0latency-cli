"""Tests for httpx connection pool limit."""

import pytest


def test_connection_pool_configured():
    """Test that httpx client is configured with max_connections=5."""
    # Verify storage.py uses the correct limits configuration
    from zerolatency_cli.storage import write_atom_cloud
    import inspect
    
    # Check that write_atom_cloud source contains limits configuration
    source = inspect.getsource(write_atom_cloud)
    assert "limits=httpx.Limits" in source
    assert "max_connections=5" in source


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
