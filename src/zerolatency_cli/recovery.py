"""Crash recovery via rolling buffer and orphaned session detection."""

import os
import json
import glob
import psutil
from pathlib import Path
from typing import List, Tuple, Optional
from zerolatency_cli.atom import Atom
from zerolatency_cli.storage import write_atom_cloud
from zerolatency_cli.auth import load_credentials

def get_sessions_dir() -> Path:
    """Get path to sessions directory (~/.0latency/sessions)."""
    sessions_dir = Path.home() / ".0latency" / "sessions"
    sessions_dir.mkdir(mode=0o700, exist_ok=True, parents=True)
    return sessions_dir

def get_session_buffer_path(session_id: str) -> Path:
    """Get path to rolling buffer for a session."""
    return get_sessions_dir() / f"{session_id}.jsonl"

def write_atom_to_buffer(atom: Atom, session_id: str) -> None:
    """
    Append atom to rolling buffer and fsync for durability.
    
    Args:
        atom: Atom to write
        session_id: Session ID for this wrapper instance
    """
    buffer_path = get_session_buffer_path(session_id)
    try:
        with open(buffer_path, 'a') as f:
            f.write(json.dumps(atom.to_dict()) + '\n')
            f.flush()
            os.fsync(f.fileno())  # Ensure durability
    except Exception as e:
        print(f"Error writing to rolling buffer: {e}")

def detect_orphaned_sessions() -> List[Tuple[Path, int]]:
    """
    Scan ~/.0latency/sessions/*.jsonl for orphaned sessions.
    
    Returns:
        List of (path, atom_count) tuples for orphaned sessions
    """
    sessions_dir = get_sessions_dir()
    orphaned = []
    
    for jsonl_path in sessions_dir.glob("*.jsonl"):
        # Extract PID from filename (session-<pid>-<uuid>.jsonl or just <uuid>.jsonl)
        # For simplicity, assume all .jsonl files are potentially orphaned
        # and check if they're stale (not actively being written)
        
        # Count atoms in file
        try:
            with open(jsonl_path, 'r') as f:
                atom_count = sum(1 for _ in f)
            if atom_count > 0:
                # Check if file is stale (modified > 5 seconds ago)
                mtime = os.path.getmtime(jsonl_path)
                import time
                if time.time() - mtime > 5:
                    orphaned.append((jsonl_path, atom_count))
        except Exception:
            pass
    
    return orphaned

def import_session(jsonl_path: Path) -> bool:
    """
    Import atoms from a crashed session's rolling buffer.
    
    Args:
        jsonl_path: Path to .jsonl file
        
    Returns:
        True on success, False on failure
    """
    creds = load_credentials()
    if creds is None:
        print("No credentials found - cannot import to cloud. Atoms remain in local buffer.")
        return False
    
    access_token = creds["access_token"]
    imported_count = 0
    
    try:
        with open(jsonl_path, 'r') as f:
            for line in f:
                atom_dict = json.loads(line.strip())
                # Add recovered metadata
                atom_dict['recovered'] = True
                atom = Atom.from_dict(atom_dict)
                
                # Write to cloud
                if write_atom_cloud(atom, access_token):
                    imported_count += 1
                else:
                    print(f"Failed to import atom {atom.id}")
                    return False
        
        # Success - delete the buffer file
        jsonl_path.unlink()
        print(f"Imported {imported_count} atoms from {jsonl_path.name}")
        return True
    
    except Exception as e:
        print(f"Error importing session: {e}")
        return False

def prompt_user_import() -> None:
    """
    Check for orphaned sessions and prompt user to import.
    """
    orphaned = detect_orphaned_sessions()
    
    if not orphaned:
        return
    
    total_atoms = sum(count for _, count in orphaned)
    print(f"\nFound {len(orphaned)} orphaned session(s) ({total_atoms} atoms). Import? [Y/n]: ", end='', flush=True)
    
    import sys
    response = sys.stdin.readline().strip().lower()
    
    if response in ('', 'y', 'yes'):
        for path, _ in orphaned:
            import_session(path)
    else:
        print("Skipping import. Orphaned sessions remain at:")
        for path, count in orphaned:
            print(f"  {path} ({count} atoms)")

def cleanup_session_buffer(session_id: str) -> None:
    """
    Delete rolling buffer file for a cleanly-exited session.
    
    Args:
        session_id: Session ID to clean up
    """
    buffer_path = get_session_buffer_path(session_id)
    try:
        if buffer_path.exists():
            buffer_path.unlink()
    except Exception:
        pass
