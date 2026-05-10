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

## Reliability Features (v0.3.0)

Production-hardened for long-running sessions and adverse conditions:

- **Crash Recovery**: Zero atom loss via rolling buffer + auto-import
- **Backpressure Handling**: Local queue (10K cap) with exponential backoff retry
- **Large Paste Support**: UTF-8-safe chunking up to 1M+ characters
- **Long-Session Stability**: Ring buffers keep RSS < 500MB in 4+ hour sessions
- **Interactive Prompts**: Y/N and password prompts pass through (not captured)
- **Tool-Call Tracking**: Multi-tool chains atomized with sequence metadata
- **Async Background**: Non-blocking capture for long-running bash commands
- **Atom Batching**: API efficiency via 10-atom batches or 2s flush

See [docs/reliability.md](docs/reliability.md) for details and verification.
