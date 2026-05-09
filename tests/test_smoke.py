"""Smoke tests for 0latency CLI."""

import subprocess
import sys

def test_version_command():
    """Test that 0latency --version exits successfully."""
    result = subprocess.run(
        [sys.executable, "-m", "zerolatency_cli", "--version"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    assert "0latency-cli" in result.stdout or "0.1.0" in result.stdout

if __name__ == "__main__":
    test_version_command()
    print("Smoke test passed")
