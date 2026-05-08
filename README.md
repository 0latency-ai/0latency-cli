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

# Authenticate with 0Latency cloud
0latency login

# Check status
0latency status
```

## License

MIT
