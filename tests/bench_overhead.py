#!/usr/bin/env python3
"""Performance benchmark: wrapper overhead measurement."""

import subprocess
import time
import statistics
import json
import sys
from pathlib import Path

def run_command(cmd, iterations=10):
    """Run command N times and return latencies in ms."""
    latencies = []
    for _ in range(iterations):
        start = time.time()
        subprocess.run(cmd, shell=True, capture_output=True, check=True)
        latency = (time.time() - start) * 1000  # Convert to ms
        latencies.append(latency)
    return latencies

def main():
    print("Benchmark: Wrapper overhead (--print mode)")
    print("=" * 50)
    
    # Test with small iterations for P1 (full 100-turn test is expensive)
    turns = 10
    
    print(f"\nRunning {turns} iterations of wrapped + bare claude...")
    
    # Wrapped command
    print("\nMeasuring wrapped (0latency claude --print)...")
    wrapped_latencies = run_command(
        '0latency --local claude -- --bare --print "benchmark"',
        iterations=turns
    )
    
    # Bare command
    print("Measuring bare (claude --print)...")
    bare_latencies = run_command(
        'claude --bare --print "benchmark"',
        iterations=turns
    )
    
    # Calculate overhead
    overhead = [w - b for w, b in zip(wrapped_latencies, bare_latencies)]
    
    # Stats
    results = {
        "turns": turns,
        "wrapped_p50_ms": round(statistics.median(wrapped_latencies), 1),
        "wrapped_p95_ms": round(statistics.quantiles(wrapped_latencies, n=20)[18], 1),
        "wrapped_p99_ms": round(max(wrapped_latencies), 1),
        "bare_p50_ms": round(statistics.median(bare_latencies), 1),
        "bare_p95_ms": round(statistics.quantiles(bare_latencies, n=20)[18], 1),
        "overhead_p50_ms": round(statistics.median(overhead), 1),
        "overhead_p95_ms": round(statistics.quantiles(overhead, n=20)[18], 1),
        "overhead_p99_ms": round(max(overhead), 1)
    }
    
    # Display
    print("\n" + "=" * 50)
    print("RESULTS")
    print("=" * 50)
    print(f"Wrapped p50/p95/p99: {results['wrapped_p50_ms']}/{results['wrapped_p95_ms']}/{results['wrapped_p99_ms']} ms")
    print(f"Bare    p50/p95/p99: {results['bare_p50_ms']}/{results['bare_p95_ms']} ms")
    print(f"Overhead p50/p95/p99: {results['overhead_p50_ms']}/{results['overhead_p95_ms']}/{results['overhead_p99_ms']} ms")
    
    # Gate check
    if results['overhead_p95_ms'] < 50:
        print(f"\n✅ Gate G8 PASS: p95 overhead = {results['overhead_p95_ms']}ms < 50ms")
    else:
        print(f"\n❌ Gate G8 FAIL: p95 overhead = {results['overhead_p95_ms']}ms >= 50ms")
        sys.exit(1)
    
    # Save results
    output_file = Path(__file__).parent.parent / "bench" / "results-2026-05-08.json"
    output_file.parent.mkdir(exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to {output_file}")

if __name__ == "__main__":
    main()
