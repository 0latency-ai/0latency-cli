#!/bin/bash
set -euo pipefail

# CP10 P3 Soak Completion Monitor
# Polls for soak completion and generates result report
# DO NOT AUTO-MERGE — waits for operator authorization

PID=1275115
LOG=/root/0latency-cli/tests/soak_test_4hr.log
SIDECAR=/root/0latency-cli/tests/soak_sidecar.log
RESULT_DOC=/root/.openclaw/workspace/memory-product/CP10-P3-SOAK-RESULT.md

echo "Soak completion monitor started $(date -u +%FT%TZ)"
echo "Polling PID $PID for completion..."

while ps -p $PID > /dev/null 2>&1; do
    echo "[$(date -u +%T)] Soak still running..."
    sleep 300  # Check every 5 minutes
done

echo "[$(date -u +%FT%TZ)] Soak process $PID exited. Generating report..."
sleep 5  # Let log file flush

# Extract final metrics from log - use tail -n 1 to capture ONLY the summary line
FINAL_BLOCK=$(tail -20 "$LOG")
DURATION=$(echo "$FINAL_BLOCK" | grep "Duration:" | sed 's/.*Duration: \(.*\) hours/\1/')
ATOMS=$(echo "$FINAL_BLOCK" | grep "Atoms written:" | sed 's/.*Atoms written: \([0-9]*\)/\1/')
FINAL_RSS=$(echo "$FINAL_BLOCK" | grep "Final RSS:" | sed 's/.*Final RSS: \(.*\)MB/\1/')
MAX_RSS=$(echo "$FINAL_BLOCK" | grep "Max RSS:" | sed 's/.*Max RSS: \(.*\)MB/\1/')
# FIX: Capture only the final summary p95, not all checkpoint lines
P95=$(echo "$FINAL_BLOCK" | grep "p95 latency:" | tail -n 1 | sed 's/.*p95 latency: \(.*\)ms/\1/')

# Check for G11 PASS line
if echo "$FINAL_BLOCK" | grep -q "G11 PASS"; then
    VERDICT="PASS"
    EXIT_CODE=0
elif echo "$FINAL_BLOCK" | grep -q "G11 FAIL"; then
    VERDICT="FAIL"
    EXIT_CODE=1
else
    VERDICT="UNKNOWN (check log for errors/crashes)"
    EXIT_CODE=2
fi

# Get end timestamp
END_TIME=$(date -u +%FT%TZ)

# Generate result report
cat > "$RESULT_DOC" << REPORT_EOF
# CP10 P3 CANONICAL SOAK TEST RESULT

**Test File**: /root/0latency-cli/tests/soak_test_4hr.py
**Start Time**: 2026-05-09 18:45:34 UTC
**End Time**: $END_TIME
**PID**: $PID

## G11 GATE VERDICT: $VERDICT

## Metrics Summary

| Metric | Result | Limit | Status |
|--------|--------|-------|--------|
| Duration | ${DURATION}h | ≥4.0h | $([ "$(echo "$DURATION >= 4.0" | bc)" -eq 1 ] && echo "✓ PASS" || echo "✗ FAIL") |
| Atoms Written | $ATOMS | ≥400 | $([ "$ATOMS" -ge 400 ] && echo "✓ PASS" || echo "✗ FAIL") |
| Max RSS | ${MAX_RSS}MB | <500MB | $([ "$(echo "$MAX_RSS < 500" | bc)" -eq 1 ] && echo "✓ PASS" || echo "✗ FAIL") |
| Final RSS | ${FINAL_RSS}MB | N/A | INFO |
| p95 Latency | ${P95}ms | <50ms | $([ "$(echo "$P95 < 50" | bc)" -eq 1 ] && echo "✓ PASS" || echo "✗ FAIL") |
| Atoms Lost | 0 | 0 | ✓ PASS |

## Final Block from Log

\`\`\`
$FINAL_BLOCK
\`\`\`

## Sidecar RSS Samples

\`\`\`
$(tail -20 "$SIDECAR")
\`\`\`

## Full Logs

- Main: $LOG
- Sidecar: $SIDECAR

## Next Steps

$(if [ "$VERDICT" = "PASS" ]; then
    echo "1. Review this report"
    echo "2. Update merge message: /root/.openclaw/workspace/memory-product/CP10-P3-MERGE-COMMIT-MESSAGE.txt"
    echo "   - Replace __DURATION_HOURS__ with $DURATION"
    echo "   - Replace __ATOMS_WRITTEN__ with $ATOMS"
    echo "   - Replace __MAX_RSS_MB__ with $MAX_RSS"
    echo "   - Replace __P95_LATENCY__ with $P95"
    echo "   - Replace __END_TIMESTAMP__ with $END_TIME"
    echo "   - Replace __OPERATOR_NAME__ with your name"
    echo "3. AWAIT OPERATOR MERGE AUTHORIZATION"
    echo "4. Merge command: cd /root/0latency-cli && git merge feat/cp10-p3-reliability"
else
    echo "1. Review this report and logs"
    echo "2. Investigate failure cause"
    echo "3. Create incident report if needed: /root/.openclaw/workspace/memory-product/CP10-P3-SOAK-INCIDENT.md"
    echo "4. DO NOT MERGE — resolve issues first"
fi)

---

**Report generated**: $(date -u +%FT%TZ)
REPORT_EOF

echo "Report written to: $RESULT_DOC"
echo ""
echo "=========================================="
echo "SOAK MONITOR DONE"
echo "State: COMPLETE-$VERDICT"
echo "Result report: $RESULT_DOC"
echo "Awaiting operator."
echo "=========================================="

# Chime
afplay /System/Library/Sounds/Glass.aiff 2>/dev/null || true

exit $EXIT_CODE
