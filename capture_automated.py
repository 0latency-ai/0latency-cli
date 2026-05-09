#!/usr/bin/env python3
"""Automated capture of CLI agent sessions using pexpect."""

import sys
import time
import pexpect

def capture_claude_session():
    """Capture a Claude Code session."""
    output_file = "tests/fixtures/cli-bytes/claude-real-session.bytes"
    
    print(f"Capturing Claude Code session to {output_file}")
    
    # Start Claude Code with logging
    child = pexpect.spawn("claude", encoding="utf-8", timeout=60)
    
    # Open file to write raw bytes
    with open(output_file, "wb") as f:
        # Set logfile to capture everything
        child.logfile_read = f
        
        # Wait for initial prompt
        time.sleep(3)
        
        # Turn 1: Simple math
        child.send("What is 2+2?\r")
        child.expect(".*", timeout=20)
        time.sleep(2)
        
        # Turn 2: Code request
        child.send("Write a Python function to add two numbers\r")
        child.expect(".*", timeout=20)
        time.sleep(2)
        
        # Turn 3: Follow-up
        child.send("Add a docstring\r")
        child.expect(".*", timeout=20)
        time.sleep(2)
        
        # Turn 4: List files (tool use)
        child.send("List files in current directory\r")
        child.expect(".*", timeout=20)
        time.sleep(2)
        
        # Turn 5: Simple question
        child.send("What is Python?\r")
        child.expect(".*", timeout=20)
        time.sleep(2)
        
        # Turn 6: Code question
        child.send("How to reverse a string?\r")
        child.expect(".*", timeout=20)
        time.sleep(2)
        
        # Turn 7: Concept
        child.send("Explain a variable\r")
        child.expect(".*", timeout=20)
        time.sleep(2)
        
        # Turn 8: SQL
        child.send("Write SELECT * FROM users\r")
        child.expect(".*", timeout=20)
        time.sleep(2)
        
        # Turn 9: Quick
        child.send("What is JSON?\r")
        child.expect(".*", timeout=20)
        time.sleep(2)
        
        # Turn 10: Final
        child.send("Hello world in JS\r")
        child.expect(".*", timeout=20)
        time.sleep(2)
        
        # Exit
        child.send("/exit\r")
        time.sleep(1)
        
    child.close()
    print(f"Captured session to {output_file}")

if __name__ == "__main__":
    capture_claude_session()
