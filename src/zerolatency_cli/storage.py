"""Storage layer for atoms - sqlite (local) and HTTP (cloud) paths."""

import sys
import sqlite3
import json
from pathlib import Path
from typing import Optional, List
from datetime import datetime, timezone
import threading
import time
from collections import deque
import httpx

from zerolatency_cli.atom import Atom
from zerolatency_cli.auth import load_credentials, get_credentials_path
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
        with httpx.Client(timeout=10.0, limits=httpx.Limits(max_connections=5)) as client:
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



class AtomQueue:
    """Thread-safe queue for atoms with 10K cap and drop-oldest policy."""
    
    MAX_SIZE = 10000
    
    def __init__(self):
        self.queue: deque[Atom] = deque(maxlen=self.MAX_SIZE)
        self.lock = threading.Lock()
        self._alerted_full = False
    
    def enqueue(self, atom: Atom) -> None:
        """Add atom to queue. Drop oldest if at capacity."""
        with self.lock:
            if len(self.queue) >= self.MAX_SIZE and not self._alerted_full:
                print(f"\nWARNING: Atom queue full ({self.MAX_SIZE} atoms). Dropping oldest.", file=sys.stderr)
                self._alerted_full = True
            self.queue.append(atom)
    
    def dequeue(self) -> Optional[Atom]:
        """Remove and return oldest atom from queue."""
        with self.lock:
            if len(self.queue) > 0:
                return self.queue.popleft()
            return None
    
    def size(self) -> int:
        """Return current queue size."""
        with self.lock:
            return len(self.queue)


class RetryWorker(threading.Thread):
    """Background thread that retries failed atom writes with exponential backoff."""
    
    BACKOFF_SCHEDULE = [1, 2, 4, 8, 16, 32, 60]
    
    def __init__(self, queue: AtomQueue, access_token: str, daemon: bool = True):
        super().__init__(daemon=daemon)
        self.queue = queue
        self.access_token = access_token
        self.running = True
    
    def run(self):
        """Main loop: dequeue atoms and retry with backoff."""
        while self.running:
            atom = self.queue.dequeue()
            if atom is None:
                time.sleep(0.1)
                continue
            
            for delay in self.BACKOFF_SCHEDULE:
                if write_atom_cloud(atom, self.access_token):
                    break
                time.sleep(delay)
            else:
                self.queue.enqueue(atom)
                print(f"Atom {atom.id} failed all retries, re-enqueued", file=sys.stderr)
    
    def stop(self):
        """Signal worker to stop."""
        self.running = False


# Global queue and worker
_atom_queue: Optional[AtomQueue] = None
_retry_worker: Optional[RetryWorker] = None
_queue_lock = threading.Lock()


def get_or_create_queue(access_token: str) -> tuple[AtomQueue, RetryWorker]:
    """Get or create global atom queue and retry worker."""
    global _atom_queue, _retry_worker
    
    with _queue_lock:
        if _atom_queue is None:
            _atom_queue = AtomQueue()
            _retry_worker = RetryWorker(_atom_queue, access_token)
            _retry_worker.start()
        return _atom_queue, _retry_worker

def write_atom(atom: Atom, force_local: bool = False) -> None:
    """
    Write atom to storage (local or cloud based on auth state).
    
    Routing logic:
    - If force_local=True OR no credentials: write to sqlite only
    - If authed: attempt cloud write; on failure, enqueue for retry (max 10K queue)
    """
    creds = None if force_local else load_credentials()
    
    if creds is None:
        write_atom_local(atom)
    else:
        access_token = creds["access_token"]
        tenant_id = creds.get("tenant_id")
        
        if tenant_id and not atom.tenant_id:
            atom.tenant_id = tenant_id
        
        if write_atom_cloud(atom, access_token):
            write_atom_local(atom)
        else:
            queue, worker = get_or_create_queue(access_token)
            queue.enqueue(atom)
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



class BatchQueue:
    """Batching queue for atoms (10-atom batches or 2s timeout)."""
    
    BATCH_SIZE = 10
    FLUSH_INTERVAL = 2.0  # seconds
    
    def __init__(self, flush_callback):
        self.queue: List[Atom] = []
        self.lock = threading.Lock()
        self.flush_callback = flush_callback
        self.first_enqueue_time: Optional[float] = None
        self.timer_thread = None
        self._start_timer()
    
    def _start_timer(self):
        """Start background timer thread for periodic flush."""
        def timer_loop():
            while True:
                time.sleep(0.1)  # Check every 100ms
                self._check_flush()
        
        self.timer_thread = threading.Thread(target=timer_loop, daemon=True)
        self.timer_thread.start()
    
    def _check_flush(self):
        """Check if batch should be flushed due to timeout."""
        with self.lock:
            if len(self.queue) == 0:
                return
            
            if self.first_enqueue_time is None:
                return
            
            elapsed = time.time() - self.first_enqueue_time
            if elapsed >= self.FLUSH_INTERVAL:
                self._flush()
    
    def enqueue(self, atom: Atom):
        """Add atom to batch queue."""
        with self.lock:
            if len(self.queue) == 0:
                self.first_enqueue_time = time.time()
            
            self.queue.append(atom)
            
            # Flush if batch size reached
            if len(self.queue) >= self.BATCH_SIZE:
                self._flush()
    
    def _flush(self):
        """Flush current batch (must hold lock)."""
        if len(self.queue) == 0:
            return
        
        batch = self.queue[:]
        self.queue.clear()
        self.first_enqueue_time = None
        
        # Call flush callback without holding lock
        self.lock.release()
        try:
            self.flush_callback(batch)
        finally:
            self.lock.acquire()
    
    def flush_remaining(self):
        """Force flush any remaining atoms."""
        with self.lock:
            self._flush()
