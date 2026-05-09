"""OAuth device-code authentication flow."""

import json
import os
import time
from pathlib import Path
from typing import Optional, Dict
import httpx

# API endpoints
DEVICE_CODE_URL = "https://api.0latency.ai/oauth/device/code"
DEVICE_TOKEN_URL = "https://api.0latency.ai/oauth/device/token"

# Credentials storage
def get_credentials_path() -> Path:
    """Get path to credentials file (~/.0latency/credentials)."""
    home = Path.home()
    config_dir = home / ".0latency"
    return config_dir / "credentials"

def ensure_config_dir() -> Path:
    """Ensure ~/.0latency directory exists with mode 0700."""
    config_dir = Path.home() / ".0latency"
    config_dir.mkdir(mode=0o700, exist_ok=True)
    # Verify permissions
    current_mode = config_dir.stat().st_mode & 0o777
    if current_mode != 0o700:
        os.chmod(config_dir, 0o700)
    return config_dir

def load_credentials() -> Optional[Dict]:
    """
    Load credentials from ~/.0latency/credentials.
    
    Returns:
        Dict with access_token, tenant_id, issued_at, or None if not found/invalid.
    """
    creds_path = get_credentials_path()
    if not creds_path.exists():
        return None
    
    try:
        with open(creds_path, 'r') as f:
            creds = json.load(f)
        
        # Validate required fields
        required = ["access_token", "tenant_id", "issued_at"]
        if all(k in creds for k in required):
            return creds
        return None
    except (json.JSONDecodeError, OSError):
        return None

def save_credentials(access_token: str, tenant_id: str, issued_at: str) -> None:
    """
    Save credentials to ~/.0latency/credentials with mode 0600.
    
    Args:
        access_token: OAuth access token
        tenant_id: Tenant UUID
        issued_at: ISO 8601 timestamp
    """
    ensure_config_dir()
    creds_path = get_credentials_path()
    
    creds = {
        "access_token": access_token,
        "tenant_id": tenant_id,
        "issued_at": issued_at
    }
    
    # Write with mode 0600
    with open(creds_path, 'w') as f:
        json.dump(creds, f, indent=2)
    
    # Ensure file permissions are 0600
    os.chmod(creds_path, 0o600)

def device_code_flow(timeout: int = 600) -> bool:
    """
    Run OAuth device-code flow.
    
    Args:
        timeout: Maximum time to wait for approval (default 600s = 10 min)
    
    Returns:
        True if authentication succeeded, False otherwise.
    """
    # Step 1: Request device code
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.post(DEVICE_CODE_URL, json={})
            response.raise_for_status()
            data = response.json()
    except (httpx.HTTPError, json.JSONDecodeError) as e:
        print(f"Error requesting device code: {e}")
        return False
    
    device_code = data["device_code"]
    user_code = data["user_code"]
    verification_uri = data["verification_uri"]
    expires_in = data["expires_in"]
    interval = data["interval"]
    
    # Step 2: Display code to user
    print(f"Open {verification_uri} in your browser")
    print(f"Enter code: {user_code}")
    print("Waiting for approval...")
    
    # Step 3: Poll for token
    start_time = time.time()
    while time.time() - start_time < min(timeout, expires_in):
        time.sleep(interval)
        
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.post(
                    DEVICE_TOKEN_URL,
                    json={"device_code": device_code}
                )
                
                # Success - token granted
                if response.status_code == 200:
                    token_data = response.json()
                    access_token = token_data["access_token"]
                    tenant_id = token_data.get("tenant_id", "")
                    issued_at = token_data.get("issued_at", "")
                    
                    # Save credentials
                    save_credentials(access_token, tenant_id, issued_at)
                    
                    print("Authentication successful!")
                    return True
                
                # Check for pending or error responses
                elif response.status_code == 400:
                    try:
                        error_data = response.json()
                        error_type = error_data.get("detail", {})
                        if isinstance(error_type, dict):
                            error_code = error_type.get("error", "")
                        else:
                            error_code = str(error_type)
                        
                        # Still pending authorization
                        if error_code in ("authorization_pending", "invalid_grant"):
                            continue
                        
                        # Slow down polling
                        elif error_code == "slow_down":
                            time.sleep(interval)  # Extra delay
                            continue
                        
                        # Expired or denied
                        elif error_code in ("expired_token", "access_denied"):
                            print(f"Error: {error_code.replace('_', ' ')}")
                            return False
                        
                        # Unknown 400 error
                        else:
                            print(f"Error: {error_code or error_data}")
                            return False
                    except (json.JSONDecodeError, KeyError):
                        print(f"Unexpected 400 response: {response.text}")
                        return False
                
                # Denied or expired (older API versions)
                elif response.status_code in (202, 403, 410):
                    if response.status_code == 202:
                        continue  # Pending
                    error_msg = response.json().get("detail", "Authorization denied or expired")
                    print(f"Error: {error_msg}")
                    return False
                
                # Other error
                else:
                    print(f"Unexpected response: {response.status_code}")
                    return False
        
        except httpx.HTTPError as e:
            print(f"Network error: {e}")
            # Continue polling on network errors
            continue
    
    # Timeout
    print("Timeout waiting for approval")
    return False
