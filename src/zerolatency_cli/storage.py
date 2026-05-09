"""Storage layer for atoms - sqlite (local) and HTTP (cloud) paths."""

import sqlite3
import json
from pathlib import Path
from typing import Optional
from datetime import datetime, timezone
import httpx

from zerolatency_cli.atom import Atom
from zerolatency_cli.auth import load_credentials, get_credentials_path

# Cloud API endpoint
ATOMS_URL = "https://api.0latency.ai/atoms"

def get_db_path() -> Path:
    """Get path to local database (~/.0latency/local.db)."""
    config_dir = Path.home() / ".0latency"
    return config_dir / "local.db"

def ensure_db() -> None:
    """Ensure local database exists with correct schema."""
    db_path = get_db_path()
    
    # Ensure directory exists
    db_path.parent.mkdir(mode=0o700, exist_ok=True)
    
    # Create database with schema if it doesn't exist
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    cur.execute('''
        CREATE TABLE IF NOT EXISTS atoms (
            id TEXT PRIMARY KEY,
            tenant_id TEXT,
            agent_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            content_raw BLOB NOT NULL,
            verbatim INTEGER NOT NULL DEFAULT 1,
            surface TEXT NOT NULL DEFAULT 'cli',
            agent_name TEXT NOT NULL,
            agent_version TEXT,
            tool_payload TEXT,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            synced_at TIMESTAMP
        )
    ''')
    
    # Create indexes
    cur.execute('''
        CREATE INDEX IF NOT EXISTS idx_atoms_session
        ON atoms(agent_id)
    ''')
    
    cur.execute('''
        CREATE INDEX IF NOT EXISTS idx_atoms_unsynced
        ON atoms(synced_at)
        WHERE synced_at IS NULL
    ''')
    
    conn.commit()
    conn.close()

def write_atom_local(atom: Atom) -> bool:
    """
    Write atom to local sqlite database.
    
    Args:
        atom: Atom to write
        
    Returns:
        True on success, False on failure
    """
    try:
        ensure_db()
        db_path = get_db_path()
        
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        
        cur.execute('''
            INSERT INTO atoms (
                id, tenant_id, agent_id, role, content, content_raw,
                verbatim, surface, agent_name, agent_version, tool_payload,
                created_at, synced_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            atom.id,
            atom.tenant_id,
            atom.agent_id,
            atom.role,
            atom.content,
            atom.content_raw,
            1 if atom.verbatim else 0,
            atom.surface,
            atom.agent_name,
            atom.agent_version,
            atom.tool_payload,
            atom.timestamp,
            None  # synced_at is NULL until uploaded
        ))
        
        conn.commit()
        conn.close()
        return True
    
    except Exception as e:
        print(f"Error writing to local DB: {e}", file=sys.stderr)
        return False

def write_atom_cloud(atom: Atom, access_token: str) -> bool:
    """
    Write atom to cloud API.
    
    Args:
        atom: Atom to write
        access_token: OAuth access token
        
    Returns:
        True on success, False on failure
    """
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.post(
                ATOMS_URL,
                json=atom.to_dict(),
                headers={"Authorization": f"Bearer {access_token}"}
            )
            
            if response.status_code in (200, 201):
                return True
            else:
                print(f"Cloud write failed: {response.status_code}", file=sys.stderr)
                return False
    
    except Exception as e:
        print(f"Cloud write error: {e}", file=sys.stderr)
        return False

def write_atom(atom: Atom, force_local: bool = False) -> None:
    """
    Write atom to storage (local or cloud based on auth state).
    
    Routing logic:
    - If force_local=True OR no credentials: write to sqlite only
    - If authed: attempt cloud write; on failure, write to sqlite with synced_at=NULL
    
    Args:
        atom: Atom to write
        force_local: Force local-only storage (override cloud writes)
    """
    # Check for credentials unless force_local
    creds = None if force_local else load_credentials()
    
    if creds is None:
        # No credentials or force_local - write to sqlite only
        write_atom_local(atom)
    else:
        # Authed - try cloud write
        access_token = creds["access_token"]
        tenant_id = creds.get("tenant_id")
        
        # Set tenant_id on atom if available
        if tenant_id and not atom.tenant_id:
            atom.tenant_id = tenant_id
        
        # Attempt cloud write
        if write_atom_cloud(atom, access_token):
            # Success - also write to local with synced_at set
            # (For P1, we just write to local; P3 will add sync tracking)
            write_atom_local(atom)
        else:
            # Cloud write failed - fallback to local with synced_at=NULL
            print("Cloud write failed, saving locally", file=sys.stderr)
            write_atom_local(atom)

def get_atom_count() -> int:
    """Get total atom count from local database."""
    try:
        ensure_db()
        db_path = get_db_path()
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM atoms")
        count = cur.fetchone()[0]
        conn.close()
        return count
    except:
        return 0

def get_unsynced_count() -> int:
    """Get count of unsynced atoms in local database."""
    try:
        ensure_db()
        db_path = get_db_path()
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM atoms WHERE synced_at IS NULL")
        count = cur.fetchone()[0]
        conn.close()
        return count
    except:
        return 0

import sys
