"""
Cross-tenant isolation test for 0latency CLI wrapper.

Verifies that atoms written with tenant A credentials are tagged with tenant A tenant_id,
and atoms written with tenant B credentials are tagged with tenant B tenant_id.
This is client-side belt-and-suspenders to server-side isolation enforcement.
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone

from zerolatency_cli.atom import Atom
from zerolatency_cli.storage import write_atom


class TestCrossTenantIsolation:
    """Test that atoms are correctly tagged per-tenant and isolated."""
    
    @pytest.fixture
    def temp_home(self, tmp_path):
        """Create temporary home directory for isolated test."""
        return tmp_path
    
    @pytest.fixture
    def tenant_a_creds(self):
        """Mock credentials for tenant A."""
        return {
            "access_token": "token_tenant_a_test_001",
            "tenant_id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            "issued_at": "2026-05-08T00:00:00Z"
        }
    
    @pytest.fixture
    def tenant_b_creds(self):
        """Mock credentials for tenant B."""
        return {
            "access_token": "token_tenant_b_test_002",
            "tenant_id": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
            "issued_at": "2026-05-08T00:00:00Z"
        }
    
    def test_atoms_tagged_with_correct_tenant_id(self, temp_home, tenant_a_creds, tenant_b_creds):
        """
        CRITICAL SECURITY TEST: Verify atoms are tagged with correct tenant_id.
        
        Each atom written must carry the tenant_id from the credentials used.
        If this fails, cross-tenant data leakage could occur.
        """
        # Track API calls
        cloud_writes = []
        
        def mock_post(url, json=None, headers=None, **kwargs):
            """Mock httpx.Client.post to capture cloud writes."""
            # Capture the request
            cloud_writes.append({
                "url": url,
                "json": json,
                "headers": headers
            })
            
            # Simulate success
            response = MagicMock()
            response.status_code = 201
            return response
        
        # Test tenant A atom write
        with patch("zerolatency_cli.storage.load_credentials", return_value=tenant_a_creds):
            with patch("httpx.Client") as mock_client:
                mock_client.return_value.__enter__.return_value.post = mock_post
                
                with patch("zerolatency_cli.storage.get_db_path", return_value=temp_home / "tenant_a.db"):
                    atom_a = Atom(
                        role="human",
                        content="Test message from tenant A",
                        content_raw=b"Test message from tenant A",
                        timestamp=datetime.now(timezone.utc).isoformat(),
                        agent_id="test_session_a",
                        agent_name="claude-code",
                        agent_version="2.1.0"
                    )
                    write_atom(atom_a)
        
        # Test tenant B atom write
        with patch("zerolatency_cli.storage.load_credentials", return_value=tenant_b_creds):
            with patch("httpx.Client") as mock_client:
                mock_client.return_value.__enter__.return_value.post = mock_post
                
                with patch("zerolatency_cli.storage.get_db_path", return_value=temp_home / "tenant_b.db"):
                    atom_b = Atom(
                        role="human",
                        content="Test message from tenant B",
                        content_raw=b"Test message from tenant B",
                        timestamp=datetime.now(timezone.utc).isoformat(),
                        agent_id="test_session_b",
                        agent_name="claude-code",
                        agent_version="2.1.0"
                    )
                    write_atom(atom_b)
        
        # Verify we captured two writes
        assert len(cloud_writes) == 2, f"Expected 2 cloud writes, got {len(cloud_writes)}"
        
        # Verify tenant A write
        write_a = cloud_writes[0]
        assert write_a["headers"]["Authorization"] == f"Bearer {tenant_a_creds['access_token']}"
        assert write_a["json"]["tenant_id"] == tenant_a_creds["tenant_id"]
        assert write_a["json"]["content"] == "Test message from tenant A"
        
        # Verify tenant B write
        write_b = cloud_writes[1]
        assert write_b["headers"]["Authorization"] == f"Bearer {tenant_b_creds['access_token']}"
        assert write_b["json"]["tenant_id"] == tenant_b_creds["tenant_id"]
        assert write_b["json"]["content"] == "Test message from tenant B"
        
        # CRITICAL: Verify no cross-contamination
        assert write_a["json"]["tenant_id"] != write_b["json"]["tenant_id"], \
            "SECURITY VIOLATION: Tenant IDs must be distinct"
        assert write_a["headers"]["Authorization"] != write_b["headers"]["Authorization"], \
            "SECURITY VIOLATION: Access tokens must be distinct"
        
        print("✓ Cross-tenant isolation verified at client layer")
    
    def test_tenant_id_from_credentials_not_atom(self, temp_home, tenant_a_creds):
        """Verify that tenant_id comes from credentials, not atom initialization."""
        cloud_writes = []
        
        def mock_post(url, json=None, headers=None, **kwargs):
            cloud_writes.append({"json": json, "headers": headers})
            response = MagicMock()
            response.status_code = 201
            return response
        
        with patch("zerolatency_cli.storage.load_credentials", return_value=tenant_a_creds):
            with patch("httpx.Client") as mock_client:
                mock_client.return_value.__enter__.return_value.post = mock_post
                
                with patch("zerolatency_cli.storage.get_db_path", return_value=temp_home / "test.db"):
                    # Create atom WITHOUT tenant_id set
                    atom = Atom(
                        role="human",
                        content="Test",
                        content_raw=b"Test",
                        timestamp=datetime.now(timezone.utc).isoformat(),
                        agent_id="test_session",
                        agent_name="claude-code",
                        agent_version="2.1.0"
                    )
                    assert atom.tenant_id is None  # Should start as None
                    
                    write_atom(atom)
        
        # Verify tenant_id was injected from credentials
        assert len(cloud_writes) == 1
        assert cloud_writes[0]["json"]["tenant_id"] == tenant_a_creds["tenant_id"]
        
        print("✓ Tenant ID correctly injected from credentials")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
