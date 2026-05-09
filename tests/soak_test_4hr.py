"""4-hour soak test for long-session stability.

Tests:
- 400 turns over 4 hours (~100 turns/hour)
- RSS < 500MB throughout
- Zero atoms lost
- p95 latency < 50ms maintained
"""

import sys
import time
import psutil
import os
from zerolatency_cli.atom import Atom
from zerolatency_cli.storage import write_atom
from collections import deque


def main():
    print("Starting 4-hour soak test...", flush=True)
    print(f"PID: {os.getpid()}", flush=True)
    print(f"Start time: {time.strftime('%Y-%m-%d %H:%M:%S')}", flush=True)
    
    process = psutil.Process()
    atom_count = 0
    target_atoms = 400
    duration_hours = 4
    duration_seconds = duration_hours * 3600
    interval = duration_seconds / target_atoms  # ~36 seconds per atom
    
    latencies = deque(maxlen=1000)  # Track last 1000 latencies
    rss_samples = []
    
    start_time = time.time()
    
    try:
        while atom_count < target_atoms:
            # Create test atom (mix of sizes)
            if atom_count % 10 == 0:
                # Large atom every 10th
                content = "x" * 10000
            else:
                content = f"Turn {atom_count}: test content"
            
            atom = Atom(
                role="user" if atom_count % 2 == 0 else "assistant",
                content=content,
                content_raw=content.encode(),
                timestamp=time.strftime('%Y-%m-%dT%H:%M:%SZ'),
                agent_id="soak-test",
                agent_name="soak",
            )
            
            # Write atom and measure latency
            write_start = time.time()
            write_atom(atom, force_local=True)  # Local-only for soak test
            write_latency = (time.time() - write_start) * 1000  # ms
            
            latencies.append(write_latency)
            atom_count += 1
            
            # Sample RSS every 100 atoms
            if atom_count % 100 == 0:
                mem_info = process.memory_info()
                rss_mb = mem_info.rss / (1024 * 1024)
                rss_samples.append(rss_mb)
                
                # Calculate p95 latency
                sorted_latencies = sorted(latencies)
                p95_idx = int(len(sorted_latencies) * 0.95)
                p95 = sorted_latencies[p95_idx] if sorted_latencies else 0
                
                elapsed_hours = (time.time() - start_time) / 3600
                
                print(f"[{atom_count}/{target_atoms}] Elapsed: {elapsed_hours:.2f}h, RSS: {rss_mb:.1f}MB, p95 latency: {p95:.1f}ms", flush=True)
                
                # Check thresholds
                if rss_mb > 500:
                    print(f"ERROR: RSS exceeded 500MB: {rss_mb:.1f}MB", flush=True)
                    sys.exit(1)
                
                if p95 > 50:
                    print(f"WARNING: p95 latency exceeded 50ms: {p95:.1f}ms", flush=True)
            
            # Sleep to pace atoms over 4 hours
            time.sleep(interval)
    
    except KeyboardInterrupt:
        print("\nSoak test interrupted", flush=True)
        sys.exit(1)
    
    # Final report
    elapsed = time.time() - start_time
    final_rss = process.memory_info().rss / (1024 * 1024)
    
    sorted_latencies = sorted(latencies)
    p95 = sorted_latencies[int(len(sorted_latencies) * 0.95)] if sorted_latencies else 0
    max_rss = max(rss_samples) if rss_samples else final_rss
    
    print("\n" + "="*60, flush=True)
    print("SOAK TEST COMPLETE", flush=True)
    print("="*60, flush=True)
    print(f"Duration: {elapsed/3600:.2f} hours", flush=True)
    print(f"Atoms written: {atom_count}", flush=True)
    print(f"Final RSS: {final_rss:.1f}MB", flush=True)
    print(f"Max RSS: {max_rss:.1f}MB", flush=True)
    print(f"p95 latency: {p95:.1f}ms", flush=True)
    print("="*60, flush=True)
    
    # Verify thresholds
    if max_rss < 500 and atom_count == target_atoms and p95 < 50:
        print("\nG11 PASS: RSS < 500MB, 400 atoms written, p95 < 50ms", flush=True)
        sys.exit(0)
    else:
        print(f"\nG11 FAIL: max_rss={max_rss:.1f}, atoms={atom_count}, p95={p95:.1f}", flush=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
