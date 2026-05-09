#!/usr/bin/env python3
"""Capture Claude Code output using --print mode."""

import subprocess
import os

output_file = "tests/fixtures/cli-bytes/claude-real-session.bytes"
os.makedirs("tests/fixtures/cli-bytes", exist_ok=True)

prompts = [
    "What is 2+2?",
    "Write a Python function to add two numbers",
    "Write a function to check if a number is prime",
    "Explain what a linked list is in one sentence",
    "What is the capital of France?",
    "How do I reverse a string in Python?",
    "Write SELECT * FROM users",
    "What is JSON?",
    "Give me hello world in JavaScript",
    "Explain recursion briefly"
]

captured = bytearray()

# Add header
captured.extend(b"Claude Code 2.1.136\n")

home = os.environ.get("HOME", "/root")
orig_path = os.environ.get("PATH", "/usr/bin")
path = f"{home}/.local/bin:{orig_path}"

for i, prompt in enumerate(prompts, 1):
    print(f"Turn {i}/{len(prompts)}: {prompt[:40]}...")
    
    # Add prompt marker (simulating interactive mode)
    captured.extend(f"\x1b[32m>\x1b[0m {prompt}\n".encode())
    
    try:
        # Run claude --print
        result = subprocess.run(
            ["claude", "--print", prompt],
            capture_output=True,
            timeout=30,
            env={**os.environ, "PATH": path}
        )
        
        # Capture output
        if result.stdout:
            captured.extend(result.stdout)
        
        captured.extend(b"\n")
        
    except Exception as e:
        print(f"  Error: {e}")
        captured.extend(f"  Error: {e}\n".encode())

with open(output_file, "wb") as f:
    f.write(bytes(captured))

print(f"\nCaptured {len(captured)} bytes to {output_file}")
