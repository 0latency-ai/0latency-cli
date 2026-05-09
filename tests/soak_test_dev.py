"""
DEV SHORTCUT — NOT A CP10 PHASE 3 GATE.

This is a 5-minute accelerated soak for fast iteration during development.
It does NOT satisfy the canonical CP10 P3 G11 verification gate, which
requires a 4-hour wall-clock run (see tests/soak_test_4hr.py).

Running this file and claiming G11 PASS is a scope-doc violation.

Scaled down from 4-hour test:
- 50 turns over 5 minutes
- RSS < 500MB
- p95 latency < 50ms
"""

import sys
import time
import psutil
import os
from zerolatency_cli.atom import Atom
from zerolatency_cli.storage import write_atom
from collections import deque


def main():
    print("Starting 5-minute soak test (DEV SHORTCUT - not G11 gate)...", flush=True)
    
    process = psutil.Process()
    atom_count = 0
    target_atoms = 50
    duration_minutes = 5
    duration_seconds = duration_minutes * 60
    interval = duration_seconds / target_atoms  # ~6 seconds per atom
    
    latencies = deque(maxlen=100)
    rss_samples = []
    
    start_time = time.time()
    
    while atom_count < target_atoms:
        # Create test atom
        if atom_count % 5 == 0:
            content = "x" * 10000
        else:
            content = f"Turn {atom_count}: test content"
        
        atom = Atom(
            role="user" if atom_count % 2 == 0 else "assistant",
            content=content,
            content_raw=content.encode(),
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            agent_id="soak-test",
            agent_name="soak",
        )
        
        write_start = time.time()
        write_atom(atom, force_local=True)
        write_latency = (time.time() - write_start) * 1000
        
        latencies.append(write_latency)
        atom_count += 1
        
        if atom_count % 10 == 0:
            mem_info = process.memory_info()
            rss_mb = mem_info.rss / (1024 * 1024)
            rss_samples.append(rss_mb)
            
            sorted_lat = sorted(latencies)
            p95 = sorted_lat[int(len(sorted_lat) * 0.95)] if sorted_lat else 0
            
            print(f"[{atom_count}/{target_atoms}] RSS: {rss_mb:.1f}MB, p95: {p95:.1f}ms", flush=True)
        
        time.sleep(interval)
    
    elapsed = time.time() - start_time
    final_rss = process.memory_info().rss / (1024 * 1024)
    sorted_lat = sorted(latencies)
    p95 = sorted_lat[int(len(sorted_lat) * 0.95)] if sorted_lat else 0
    max_rss = max(rss_samples) if rss_samples else final_rss
    
    print("\nDEV SOAK COMPLETE (5min - NOT G11 GATE)", flush=True)
    print(f"Atoms: {atom_count}, Max RSS: {max_rss:.1f}MB, p95: {p95:.1f}ms", flush=True)
    
    if max_rss < 500 and atom_count == target_atoms and p95 < 50:
        print("DEV TEST PASS (this is NOT the G11 canonical gate)", flush=True)
        sys.exit(0)
    else:
        print(f"DEV TEST FAIL: rss={max_rss:.1f}, atoms={atom_count}, p95={p95:.1f}", flush=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
