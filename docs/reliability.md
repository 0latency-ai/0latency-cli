# Reliability Guide (v0.3.0)

CP10 Phase 3 reliability hardening for production-ready wrapper.

## Eight Core Reliability Features

1. **Crash Recovery**: Rolling buffer + auto-import (zero atom loss)
2. **Backpressure**: Local queue (10K cap) + exp backoff
3. **Interactive Prompts**: Y/N, password passthrough
4. **Large Paste**: UTF-8-safe 64KB chunking
5. **Long-Session Bounds**: Ring buffers (RSS < 500MB)
6. **Tool-Call Chains**: Multi-tool atomization
7. **Async Background**: Non-blocking long commands
8. **Atom Batching**: 10-atom OR 2s flush

## Run Tests

```bash
pytest tests/test_*.py -v
python3 tests/soak_test_5min.py  # 5-min scaled soak
```

## Trade-Offs

- Crash recovery: +5-10% overhead for durability
- Backpressure: 10K cap with drop-oldest
- Prompts: Heuristic-based detection
- Chunking: Client-side reassembly needed
- Ring buffers: Last 100 turns only

See individual test files for details.
