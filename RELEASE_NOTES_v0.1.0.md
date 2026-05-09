# v0.1.0 — Wrapper Foundation

## Overview

First production release of 0latency CLI wrapper. Provides transparent PTY-based interception for Claude Code with role detection, OAuth authentication, and local-first storage.

**Key Metrics:**
- Performance overhead: p95 5ms (0.5% overhead vs native)
- Platform support: macOS, Linux
- Claude Code version tested: 2.1.136

## Features by Task

### Task 1: Repository Skeleton & Python Package
- Python package structure (`src/zerolatency_cli/`)
- pyproject.toml with dependencies
- Entry point: `0latency` command

### Task 2: CLI Surface
- Subcommands: `claude`, `login`, `status`
- Pass-through wrapper: `0latency claude <args>` proxies to native `claude`
- Help and version flags

### Task 3: PTY-based Stdio Interception
- Transparent PTY wrapping via `PTYWrapper` class
- Signal handling (SIGWINCH for terminal resize)
- Raw terminal mode for authentic behavior
- Non-blocking I/O with select() for low latency

### Task 4: Claude Code Role Detection
- Profile-based parser (`ClaudeCodeProfile`)
- ANSI escape sequence stripping
- --print mode: user/assistant atom pairs
- Ground truth validated against Claude Code 2.1.136

### Task 5: OAuth Device-Code Authentication
- Device code flow implementation
- Credentials storage: `~/.0latency/credentials` (mode 0600)
- Endpoints: `/oauth/device/code`, `/oauth/device/token`
- 10-minute approval timeout

### Task 6: Storage Layer
- Local SQLite: `~/.0latency/local.db`
- Cloud writes to `https://api.0latency.ai/atoms`
- Automatic fallback: cloud failure → local sqlite
- Schema: atoms table with tenant_id, agent_id, role, content, timestamps

### Task 7: Status Command
- `0latency status`: shows auth state, atom counts, sync status
- Displays: tenant_id, total atoms, unsynced atoms
- No-credentials behavior: shows local-only stats

### Task 8: Performance Benchmark
- Overhead measurement: `tests/bench_overhead.py`
- p95 latency: 5ms (0.5% overhead)
- Methodology: 1000 iterations, compare wrapped vs native

## Scope Notes

### Included (P1)
- PTY transparency for stdout/stderr/stdin
- --print mode parsing (verified)
- Local-first architecture (offline-capable)
- OAuth device-code flow
- Basic role detection (user/assistant)

### Deferred to P2
- Interactive mode turn-by-turn parsing (scaffolded, not shipped)
- Tool delimiter detection in interactive sessions
- Streaming atom emission during long responses
- Profile abstraction (multi-agent support)

## Installation

```bash
pip install 0latency-cli
```

## Quick Start

```bash
# Authenticate
0latency login

# Wrap Claude Code
0latency claude --print "What is 2+2?"

# Check status
0latency status
```

## Known Limitations

- Interactive mode parser emits single assistant atom (P2 will add turn detection)
- No retry logic for cloud writes (P2)
- No background sync daemon (P2)
- macOS/Linux only (Windows not tested)

## Commits

Changelog for commits included in v0.1.0:

- `7d511b9` Task 1 - Repo skeleton + Python package layout
- `da11be9` Task 2 - CLI surface (claude/login/status subcommands)
- `e05ab09` Task 3 - PTY-based stdio interception
- `09dea15` Task 4 - Claude Code role detection (framework + ANSI handling)
- `3d9a492` Task 4 Ground Truth Verification - Claude Code 2.1.136
- `9d7dcad` Phase B - Task 4 completion: --print mode role detection
- `b4b0f20` Task 5: OAuth device-code authentication flow
- `4753ee0` Task 6: Storage layer (sqlite + cloud paths)
- `a075453` Task 7: 0latency status command
- `31621b1` Task 8: Performance benchmark - minimal overhead verified
- `d646af8` Fix: Move import sys to top of storage.py
- `bb55fcf` Merge CP10 P1: Wrapper foundation

## Links

- Repository: https://github.com/0latency-ai/0latency-cli
- Documentation: https://0latency.ai/docs
- API: https://api.0latency.ai
- Issues: https://github.com/0latency-ai/0latency-cli/issues
