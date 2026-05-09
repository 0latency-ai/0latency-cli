#!/usr/bin/env python3
"""Capture a Python REPL session as a test agent fixture."""

import os
import pty
import select
import sys

output_file = "tests/fixtures/cli-bytes/python-repl-test.bytes"
os.makedirs("tests/fixtures/cli-bytes", exist_ok=True)

captured = bytearray()

print(f"Capturing Python REPL session to {output_file}")
print("Will send 10 commands automatically...")

pid, master_fd = pty.fork()

if pid == 0:
    # Child - exec python3
    os.execvp("python3", ["python3", "-i"])

# Parent - automated I/O
import fcntl
import time

# Commands to send
commands = [
    "2 + 2\n",
    "def greet(name): return fHello, {name}\n",
    "greet(World)\n",
    "import sys\n",
    "sys.version\n",
    "[x**2 for x in range(5)]\n",
    "len(test)\n",
    "print(Hello REPL)\n",
    "{key: value}\n",
    "exit()\n"
]

try:
    fcntl.fcntl(master_fd, fcntl.F_SETFL, os.O_NONBLOCK)
    
    for cmd in commands:
        time.sleep(0.5)
        os.write(master_fd, cmd.encode())
        time.sleep(0.5)
        
        # Read response
        try:
            while True:
                data = os.read(master_fd, 1024)
                if data:
                    captured.extend(data)
                else:
                    break
        except (OSError, BlockingIOError):
            pass
    
    time.sleep(1)
    
except Exception as e:
    print(f"Error: {e}")

finally:
    try:
        os.waitpid(pid, 0)
    except:
        pass
    
    with open(output_file, "wb") as f:
        f.write(bytes(captured))
    
    print(f"Captured {len(captured)} bytes to {output_file}")
