#!/usr/bin/env python3
import subprocess
import os

output_file = "tests/fixtures/cli-bytes/codex-real-session.bytes"

prompts = [
    "What is 2+2?",
    "Write a Python function to multiply two numbers",
    "Write a function to find the maximum in a list",
    "Explain what a hash table is briefly",
    "What is the difference between a list and a tuple?",
    "How do I sort a list in Python?",
    "Write a SELECT query for a products table",
    "What is REST?",
    "Give me a for loop in Python",
    "Explain inheritance"
]

captured = bytearray()
captured.extend(b"codex-cli 0.130.0\n")

for i, prompt in enumerate(prompts, 1):
    print(f"Turn {i}/{len(prompts)}: {prompt[:40]}...")
    captured.extend(f"$ {prompt}\n".encode())
    
    try:
        result = subprocess.run(
            ["codex", "exec", prompt],
            capture_output=True,
            timeout=30
        )
        if result.stdout:
            captured.extend(result.stdout)
        captured.extend(b"\n")
    except Exception as e:
        print(f"  Error: {e}")
        captured.extend(f"Error: {e}\n".encode())

with open(output_file, "wb") as f:
    f.write(bytes(captured))

print(f"\nCaptured {len(captured)} bytes to {output_file}")
