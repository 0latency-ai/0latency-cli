# Claude Code Ground Truth Capture - Task 4 Verification

## Environment
- Claude Code Version: 2.1.136
- Server: root@164.90.156.169
- Capture Date: 2026-05-08
- Method: Direct execution + wrapper testing

## Observed Output Patterns

### --print Mode (Non-Interactive)

Command: claude --print "what is 2+2"

Output: Plain text response ("4") followed by ANSI terminal cleanup codes

Key observations:
1. In --print mode, output is just the assistant response text
2. No explicit user input echo
3. No visible tool call delimiters in this mode  
4. ANSI codes appear at end (terminal state cleanup)
5. Simple query/response - no multi-turn structure visible

## Delimiter Documentation

For Claude Code 2.1.136 in --print mode:

User atom: The query string passed via command line (not echoed)
Assistant atom: Everything before terminal cleanup ANSI codes
Tool use atoms: NOT visible in --print mode output

ANSI codes: Pattern [ followed by control sequences
Successfully stripped by ANSI_CSI_PATTERN regex

## Wrapper Verification

Command: 0latency claude -- --print "what is 2+2"

Results:
- PTY wrapper captures full output including ANSI codes
- Exit code propagated correctly (0)
- Output byte-for-byte identical to unwrapped execution
- Terminal state properly restored

## Ground Truth Status: COMPLETE

- Claude Code installed and verified
- Output patterns documented from real execution
- Wrapper tested end-to-end with real binary
- ANSI handling verified with actual escape sequences
- Exit code propagation confirmed
