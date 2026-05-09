#!/usr/bin/env python3
"""Profile dispatch performance benchmark - measures parse_chunk overhead."""

import sys
import time
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from zerolatency_cli.profiles.claude_code import ClaudeCodeProfile
from zerolatency_cli.profiles.generic import GenericProfile
from zerolatency_cli.atom import Atom


def percentile(data, p):
    """Calculate percentile (0-100)."""
    if not data:
        return 0
    sorted_data = sorted(data)
    k = (len(sorted_data) - 1) * (p / 100)
    f = int(k)
    c = f + 1
    if c >= len(sorted_data):
        return sorted_data[-1]
    d0 = sorted_data[f] * (c - k)
    d1 = sorted_data[c] * (k - f)
    return d0 + d1


def benchmark_profile(profile_class, fixture_path, turns=100):
    """
    Benchmark profile parsing performance.
    
    Measures parse_chunk() + flush() overhead by running N iterations
    on the fixture bytes.
    """
    # Load fixture once
    with open(fixture_path, "rb") as f:
        fixture_bytes = f.read()
    
    latencies_ms = []
    
    for _ in range(turns):
        atoms_collected = []
        
        def collect(atom):
            atoms_collected.append(atom)
        
        # Create profile with appropriate signature
        if profile_class.__name__ == "GenericProfile":
            profile = profile_class(agent_id="bench", agent_version="test")
        else:
            profile = profile_class(agent_id="bench", agent_version="test", user_query=None)
        
        start = time.perf_counter()
        profile.parse_chunk(fixture_bytes, collect)
        profile.flush(collect)
        latency = (time.perf_counter() - start) * 1000  # ms
        
        latencies_ms.append(latency)
    
    return {
        "iterations": turns,
        "p50_ms": round(percentile(latencies_ms, 50), 2),
        "p95_ms": round(percentile(latencies_ms, 95), 2),
        "p99_ms": round(percentile(latencies_ms, 99), 2),
        "min_ms": round(min(latencies_ms), 2),
        "max_ms": round(max(latencies_ms), 2),
    }


def main():
    print("=" * 70)
    print("CP10 P2 ADDENDUM: Profile Dispatch Performance Benchmark")
    print("=" * 70)
    print("Measures: parse_chunk() + flush() latency per profile")
    print("Budget: p95 < 50ms per profile")
    print()
    
    turns = 100
    results = {}
    
    # Benchmark Claude Code profile
    print(f"Benchmarking ClaudeCodeProfile ({turns} iterations)...")
    fixture_claude = Path(__file__).parent / "fixtures" / "cli-bytes" / "claude-real-session.bytes"
    results["claude_code"] = benchmark_profile(ClaudeCodeProfile, fixture_claude, turns=turns)
    results["claude_code"]["profile"] = "ClaudeCodeProfile"
    results["claude_code"]["fixture"] = str(fixture_claude)
    
    # Benchmark Generic profile  
    print(f"Benchmarking GenericProfile ({turns} iterations)...")
    # Use a simple fixture for generic (create minimal test bytes)
    test_bytes = b"Test input\n> Response\nMore output\n"
    fixture_generic = Path("/tmp/generic-fixture.bytes")
    fixture_generic.write_bytes(test_bytes)
    results["generic"] = benchmark_profile(GenericProfile, fixture_generic, turns=turns)
    results["generic"]["profile"] = "GenericProfile"
    results["generic"]["fixture"] = str(fixture_generic)
    
    # Display results
    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)
    
    all_pass = True
    for profile_key, stats in results.items():
        profile_name = stats["profile"]
        print(f"\n{profile_name}:")
        print(f"  p50 = {stats['p50_ms']}ms")
        print(f"  p95 = {stats['p95_ms']}ms")
        print(f"  p99 = {stats['p99_ms']}ms")
        print(f"  range = [{stats['min_ms']}ms, {stats['max_ms']}ms]")
        
        # Gate check
        if stats['p95_ms'] < 50:
            print(f"  ✅ PASS: p95 = {stats['p95_ms']}ms < 50ms")
        else:
            print(f"  ❌ FAIL: p95 = {stats['p95_ms']}ms >= 50ms")
            all_pass = False
    
    # Overall gate
    print("\n" + "=" * 70)
    if all_pass:
        print("✅ PASS: All profiles meet p95 < 50ms dispatch budget")
        exit_code = 0
    else:
        print("❌ FAIL: Some profiles exceed p95 < 50ms budget")
        exit_code = 1
    
    # Save results
    output_file = Path(__file__).parent.parent / "bench" / ("results-cp10-p2-addendum-" + time.strftime("%Y-%m-%d") + ".json")
    output_file.parent.mkdir(exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to {output_file}")
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
