#\!/usr/bin/env python3
"""Capture raw bytes from an interactive Claude Code session."""

import os
import sys
import pty
import select
import signal

output_file = "tests/fixtures/interactive_session_raw.bin"

# Create fixtures directory
os.makedirs("tests/fixtures", exist_ok=True)

captured = bytearray()

def on_data(data: bytes):
    """Capture data callback."""
    captured.extend(data)

print(f"Starting Claude Code capture. Output will be saved to {output_file}")
print("Conduct a ~10-turn session, then exit with Ctrl+D or /exit")
print("=" * 60)

# Fork with PTY
pid, master_fd = pty.fork()

if pid == 0:
    # Child - exec claude
    os.execvp("claude", ["claude"])

# Parent - tee I/O
import fcntl
import termios
import tty

# Save terminal settings
try:
    original_tty = termios.tcgetattr(sys.stdin)
except:
    original_tty = None

try:
    # Set to raw mode
    if original_tty:
        tty.setraw(sys.stdin.fileno())
    
    # Set master_fd non-blocking
    flags = fcntl.fcntl(master_fd, fcntl.F_GETFL)
    fcntl.fcntl(master_fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)
    
    while True:
        try:
            readable, _, _ = select.select([sys.stdin, master_fd], [], [])
            
            if sys.stdin in readable:
                data = os.read(sys.stdin.fileno(), 1024)
                if data:
                    os.write(master_fd, data)
            
            if master_fd in readable:
                try:
                    data = os.read(master_fd, 1024)
                    if data:
                        os.write(sys.stdout.fileno(), data)
                        captured.extend(data)
                except OSError as e:
                    if e.errno == 5:  # EIO
                        break
                    raise
        except KeyboardInterrupt:
            pass

finally:
    # Restore terminal
    if original_tty:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, original_tty)
    
    # Wait for child
    os.waitpid(pid, 0)
    
    # Save captured data
    with open(output_file, wb) as f:
        f.write(bytes(captured))
    
    print(f"\n\nCaptured {len(captured)} bytes to {output_file}")
