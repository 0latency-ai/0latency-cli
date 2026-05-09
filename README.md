# 0latency CLI

Verbatim CLI capture wrapper for Claude Code, Codex, Gemini CLI, and Aider. Captures all user inputs and agent outputs as role-tagged atoms, stored locally or synced to the 0Latency cloud memory platform.

## Installation

```bash
pip install -e .
```

## Usage

```bash
# Wrap Claude Code session (writes to cloud if authenticated)
0latency claude

# Wrap Claude Code with local-only storage
0latency --local claude

# Dry-run mode (show what would be captured)
0latency --explain claude

# Authenticate with 0Latency cloud
0latency login

# Check status
0latency status

# Pass arguments to Claude Code
0latency claude --print "what is 2+2"
0latency claude /path/to/project
```

## Commands

- `0latency claude [args...]` - Wrap Claude Code session with verbatim capture
- `0latency login` - Authenticate with OAuth device-code flow
- `0latency status` - Show auth state, storage info, and sync status

## Flags

- `--local` - Force local-only storage (override cloud writes)
- `--explain` - Dry-run mode showing what would be captured
- `--version` - Show version information
- `--help` - Show help message

## License

MIT
