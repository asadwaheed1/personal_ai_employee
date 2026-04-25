# Testing Guide - Bronze Tier AI Employee

## Overview

This document provides comprehensive testing scenarios to validate the Bronze Tier implementation.

## Test Environment Setup

```bash
# Navigate to project
cd /home/asad/piaic/projects/personal_ai_employee

# Ensure system is running
./start.sh

# Open multiple terminals for monitoring
# Terminal 1: Watcher logs
tail -f ai_employee_vault/Logs/filesystem_watcher_*.log

# Terminal 2: Orchestrator logs
tail -f ai_employee_vault/Logs/orchestrator_*.log

# Terminal 3: Watchdog logs
tail -f ai_employee_vault/Logs/watchdog_*.log
```

## Test Suite

### Test 1: Single File Processing

**Objective**: Verify basic file detection and processing

```bash
# Create test file
cat > ai_employee_vault/Inbox/test_single.md << 'EOF'
---
type: test
priority: low
---

# Single File Test

This is a test of single file processing.
EOF

# Expected behavior:
# 1. Watcher detects file within 5 seconds
# 2. Metadata file created in Needs_Action within 5 seconds
# 3. Orchestrator triggers Claude within 30 seconds
# 4. File moved to Done after processing

# Verify
sleep 40
ls ai_employee_vault/Needs_Action/FILE_*test_single*
ls ai_employee_vault/Done/
```

**Success Criteria**:
- ✅ File detected in watcher logs
- ✅ Metadata file created in Needs_Action
- ✅ Orchestrator triggered in logs
- ✅ File eventually in Done folder

### Test 2: Multiple Concurrent Files

**Objective**: Verify handling of simultaneous file drops

```bash
# Drop 10 files at once
for i in {1..10}; do
    cat > ai_employee_vault/Inbox/test_concurrent_$i.md << EOF
---
type: test
id: $i
---

# Concurrent Test $i

Testing concurrent file processing.
EOF
done

# Wait for processing
sleep 60

# Verify all files processed
echo "Files in Needs_Action:"
ls ai_employee_vault/Needs_Action/ | wc -l

echo "Files in Done:"
ls ai_employee_vault/Done/ | wc -l

# Check for duplicates in state
cat ai_employee_vault/.state/filesystem_watcher_state.json | jq '.processed_ids | length'
```

**Success Criteria**:
- ✅ All 10 files detected
- ✅ All 10 metadata files created
- ✅ No duplicate processing
- ✅ All files eventually in Done
- ✅ State file contains 10 unique IDs

### Test 3: Large File Handling

**Objective**: Verify proper handling of large files

```bash
# Create a large file (10MB)
dd if=/dev/urandom of=ai_employee_vault/Inbox/large_file.bin bs=1M count=10

# Wait for detection
sleep 10

# Verify metadata created
ls -lh ai_employee_vault/Needs_Action/FILE_*large_file*

# Check metadata content
cat ai_employee_vault/Needs_Action/FILE_*large_file*.md
```

**Success Criteria**:
- ✅ Large file detected after complete write
- ✅ Metadata shows correct file size
- ✅ Original file copied to Needs_Action
- ✅ No corruption or partial reads

### Test 4: Temporary File Filtering

**Objective**: Verify temp files are ignored

```bash
# Create temporary files
touch ai_employee_vault/Inbox/.hidden_file
touch ai_employee_vault/Inbox/document.tmp
touch ai_employee_vault/Inbox/file.swp
touch ai_employee_vault/Inbox/download.crdownload

# Wait
sleep 10

# Verify no metadata files created
ls ai_employee_vault/Needs_Action/FILE_*hidden* 2>/dev/null && echo "FAIL: Hidden file processed" || echo "PASS: Hidden file ignored"
ls ai_employee_vault/Needs_Action/FILE_*tmp* 2>/dev/null && echo "FAIL: Temp file processed" || echo "PASS: Temp file ignored"
```

**Success Criteria**:
- ✅ No metadata files for temp files
- ✅ Watcher logs show files ignored
- ✅ No errors in logs

### Test 5: Process Crash Recovery

**Objective**: Verify system recovers from crashes

```bash
# Get orchestrator PID
ORCH_PID=$(cat /tmp/ai_employee_pids/orchestrator.pid)
echo "Orchestrator PID: $ORCH_PID"

# Kill orchestrator
kill $ORCH_PID

# Wait for watchdog to detect and restart (60 seconds)
sleep 65

# Verify restart
NEW_PID=$(cat /tmp/ai_employee_pids/orchestrator.pid)
echo "New Orchestrator PID: $NEW_PID"

# Check logs for restart message
grep "restarted" ai_employee_vault/Logs/watchdog_*.log

# Drop a test file to verify functionality
echo "Test after restart" > ai_employee_vault/Inbox/test_recovery.md

# Wait and verify processing
sleep 40
ls ai_employee_vault/Done/*recovery*
```

**Success Criteria**:
- ✅ Watchdog detects crashed process
- ✅ Process restarted within 60 seconds
- ✅ New PID assigned
- ✅ System continues processing files
- ✅ Alert created in ALERTS.md

### Test 6: State Persistence

**Objective**: Verify state survives restarts

```bash
# Process some files
for i in {1..5}; do
    echo "Test $i" > ai_employee_vault/Inbox/state_test_$i.txt
done

sleep 40

# Save current state
cp ai_employee_vault/.state/filesystem_watcher_state.json /tmp/state_backup.json

# Stop system
./stop.sh

# Start system
./start.sh

sleep 10

# Compare states
diff /tmp/state_backup.json ai_employee_vault/.state/filesystem_watcher_state.json

# Try to reprocess same files (should be ignored)
for i in {1..5}; do
    echo "Test $i" > ai_employee_vault/Inbox/state_test_$i.txt
done

sleep 40

# Check for duplicates
ls ai_employee_vault/Needs_Action/ | grep state_test | wc -l
```

**Success Criteria**:
- ✅ State file preserved after restart
- ✅ Processed IDs maintained
- ✅ No duplicate processing of same files
- ✅ State file updated with new items

### Test 7: File Locking

**Objective**: Verify concurrent processing prevention

```bash
# Start two orchestrator instances manually
python3 src/orchestrator/orchestrator.py ai_employee_vault 30 &
PID1=$!

sleep 2

python3 src/orchestrator/orchestrator.py ai_employee_vault 30 &
PID2=$!

# Wait a bit
sleep 10

# Check logs for lock messages
grep "Another processing instance" ai_employee_vault/Logs/orchestrator_*.log

# Kill manual instances
kill $PID1 $PID2 2>/dev/null

# Verify lock released
ls ai_employee_vault/.state/processing.lock 2>/dev/null && echo "FAIL: Lock not released" || echo "PASS: Lock released"
```

**Success Criteria**:
- ✅ Second instance detects lock
- ✅ Second instance skips processing
- ✅ No file corruption
- ✅ Lock released after processing

### Test 8: Approval Workflow

**Objective**: Verify human-in-the-loop approval process

```bash
# Create approval request
cat > ai_employee_vault/Pending_Approval/test_approval.md << 'EOF'
---
type: approval_request
action: test_action
priority: high
created: 2026-02-25T17:40:00Z
---

# Test Approval Request

This is a test of the approval workflow.

## To Approve
Move this file to /Approved/

## To Reject
Move this file to /Rejected/
EOF

# Wait a moment
sleep 5

# Approve the request
mv ai_employee_vault/Pending_Approval/test_approval.md \
   ai_employee_vault/Approved/

# Wait for orchestrator to detect (30 seconds)
sleep 35

# Verify processing
grep "approved" ai_employee_vault/Logs/orchestrator_*.log

# Check if moved to Done
ls ai_employee_vault/Done/*approval*
```

**Success Criteria**:
- ✅ Approval request created
- ✅ File moved to Approved folder
- ✅ Orchestrator detects approved file
- ✅ Approved action processed with priority
- ✅ File moved to Done after execution

### Test 9: Dashboard Updates

**Objective**: Verify Dashboard.md is updated correctly

```bash
# Record initial dashboard state
cp ai_employee_vault/Dashboard.md /tmp/dashboard_before.md

# Process some files
for i in {1..3}; do
    echo "Dashboard test $i" > ai_employee_vault/Inbox/dashboard_test_$i.md
done

# Wait for processing
sleep 60

# Compare dashboards
diff /tmp/dashboard_before.md ai_employee_vault/Dashboard.md

# Check for updates
grep "dashboard_test" ai_employee_vault/Dashboard.md
```

**Success Criteria**:
- ✅ Dashboard updated after processing
- ✅ Recent activity section shows new items
- ✅ Statistics updated
- ✅ Timestamp updated

### Test 10: Error Handling

**Objective**: Verify graceful error handling

```bash
# Create a file with invalid characters in name
touch "ai_employee_vault/Inbox/test<>invalid:name.md"

# Wait for processing
sleep 10

# Check logs for sanitization
grep "sanitize" ai_employee_vault/Logs/filesystem_watcher_*.log

# Verify file processed with sanitized name
ls ai_employee_vault/Needs_Action/FILE_*invalid*

# Create a file that will cause processing error
cat > ai_employee_vault/Inbox/error_test.md << 'EOF'
---
type: error_test
---

# Error Test

This file is designed to test error handling.
Intentionally malformed content: {{{{INVALID}}}}
EOF

# Wait and check error logs
sleep 40
grep -i "error\|exception" ai_employee_vault/Logs/orchestrator_*.log | tail -5
```

**Success Criteria**:
- ✅ Invalid filenames sanitized
- ✅ Errors logged with stack traces
- ✅ System continues operating
- ✅ Failed items logged appropriately

## Performance Tests

### Test 11: Throughput Test

**Objective**: Measure system throughput

```bash
# Create 50 files
START_TIME=$(date +%s)

for i in {1..50}; do
    echo "Throughput test $i" > ai_employee_vault/Inbox/throughput_$i.md
done

# Wait for all to process
sleep 120

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

# Count processed files
PROCESSED=$(ls ai_employee_vault/Done/FILE_*throughput* 2>/dev/null | wc -l)

echo "Processed $PROCESSED files in $DURATION seconds"
echo "Throughput: $(echo "scale=2; $PROCESSED / $DURATION" | bc) files/second"
```

**Success Criteria**:
- ✅ All 50 files processed
- ✅ No errors in logs
- ✅ Reasonable throughput (>0.5 files/second)

### Test 12: Memory Leak Test

**Objective**: Verify no memory leaks over time

```bash
# Get initial memory usage
ORCH_PID=$(cat /tmp/ai_employee_pids/orchestrator.pid)
INITIAL_MEM=$(ps -o rss= -p $ORCH_PID)

echo "Initial memory: $INITIAL_MEM KB"

# Process many files
for batch in {1..10}; do
    for i in {1..10}; do
        echo "Memory test batch $batch file $i" > ai_employee_vault/Inbox/mem_test_${batch}_${i}.md
    done
    sleep 30
done

# Get final memory usage
FINAL_MEM=$(ps -o rss= -p $ORCH_PID)
echo "Final memory: $FINAL_MEM KB"

# Calculate increase
INCREASE=$((FINAL_MEM - INITIAL_MEM))
PERCENT=$(echo "scale=2; ($INCREASE / $INITIAL_MEM) * 100" | bc)

echo "Memory increase: $INCREASE KB ($PERCENT%)"
```

**Success Criteria**:
- ✅ Memory increase < 50%
- ✅ No continuous growth pattern
- ✅ Processes remain stable

## Test Report Template

After running tests, document results:

```markdown
# Test Report - Bronze Tier AI Employee

**Date**: 2026-02-25
**Tester**: [Your Name]
**System**: [OS and Python version]

## Test Results

| Test | Status | Notes |
|------|--------|-------|
| Single File Processing | ✅ PASS | |
| Multiple Concurrent Files | ✅ PASS | |
| Large File Handling | ✅ PASS | |
| Temporary File Filtering | ✅ PASS | |
| Process Crash Recovery | ✅ PASS | |
| State Persistence | ✅ PASS | |
| File Locking | ✅ PASS | |
| Approval Workflow | ✅ PASS | |
| Dashboard Updates | ✅ PASS | |
| Error Handling | ✅ PASS | |
| Throughput Test | ✅ PASS | 0.8 files/sec |
| Memory Leak Test | ✅ PASS | 15% increase |

## Issues Found

[List any issues discovered]

## Recommendations

[List any improvements needed]
```

## Cleanup After Testing

```bash
./stop.sh
rm -rf ai_employee_vault/Inbox/*
rm -rf ai_employee_vault/Needs_Action/*
rm -rf ai_employee_vault/Done/*
rm -rf ai_employee_vault/Logs/*
rm -rf ai_employee_vault/.state/*.json
./start.sh
```

---

## Gold Tier Tests

### Test 13: Social Media Posting — HITL Flow

```bash
# LinkedIn
python -m src.orchestrator.skills.post_linkedin '{"action": "create_post", "content": "Gold test #automation"}'
ls ai_employee_vault/Pending_Approval/LINKEDIN_POST_*.md

# Facebook
python -m src.orchestrator.skills.post_facebook '{"action": "create_post", "content": "Gold FB test"}'
ls ai_employee_vault/Pending_Approval/FACEBOOK_POST_*.md

# Approve both
mv ai_employee_vault/Pending_Approval/LINKEDIN_POST_*.md ai_employee_vault/Approved/
mv ai_employee_vault/Pending_Approval/FACEBOOK_POST_*.md ai_employee_vault/Approved/
```

**Success Criteria**: Approval files created → execution logged → post_id in Done/ result.

### Test 14: Cross-Platform Content Calendar

```bash
python src/orchestrator/skills/create_content_plan.py
ls ai_employee_vault/Content_Calendar/
# Expected: JSON plan + per-platform MD files (LI/TW/FB/IG)
```

**Success Criteria**: Calendar files generated for all 4 platforms.

### Test 15: Odoo Accounting Integration

```bash
python -c "
import sys; sys.path.insert(0, '.')
from src.orchestrator.skills.odoo_accounting import OdooAccountingSkill
skill = OdooAccountingSkill('./ai_employee_vault')
print(skill.get_revenue_summary('2026-04-01', '2026-04-30'))
print(skill.get_expense_summary('2026-04-01', '2026-04-30'))
"
```

**Success Criteria**: Returns dict with total amounts + invoice count (requires Odoo Docker running).

### Test 16: CEO Weekly Briefing

```bash
python src/orchestrator/skills/generate_ceo_briefing.py ./ai_employee_vault
ls ai_employee_vault/Briefings/
# Open latest briefing and verify sections present
```

**Success Criteria**: Briefing contains Executive Summary, Email Activity, Odoo Financials, Anomalies.

### Test 17: Audit Logging

```bash
# Run any social post test, then:
cat ai_employee_vault/Logs/audit_master.json | python -m json.tool | tail -40
```

**Success Criteria**: Structured JSON entries with `platform`, `action`, `status`, `timestamp` fields.

### Test 18: Health Check

```bash
python scripts/health_check.py
cat ai_employee_vault/Dashboard.md | grep -A5 "Health"
```

**Success Criteria**: Health check runs, Dashboard health table updated.

### Test 19: Ralph Wiggum Autonomous Mode

```bash
./scripts/start_ralph_wiggum.sh

# Drop test file to Needs_Action
cat > ai_employee_vault/Needs_Action/TEST_$(date +%s).md << 'EOF'
---
type: task
priority: low
---
# Test autonomous processing
EOF
# Expected: stop hook detects pending item → injects continuation prompt
```

**Success Criteria**: Claude continues processing without manual restart.

### Test 20: Multiple MCP Servers

```bash
cat .mcp.json
# Expected: gmail, filesystem, and odoo servers listed

# Test filesystem MCP action
cat > ai_employee_vault/Needs_Action/MCP_FILESYSTEM_test_$(date +%s).json << 'EOF'
{
  "mcp_server": "filesystem",
  "tool": "list_directory",
  "timestamp": "2026-04-25T00:00:00Z",
  "status": "pending",
  "params": {"path": "./ai_employee_vault/Done"},
  "result": null
}
EOF

python src/orchestrator/mcp_processor.py ./ai_employee_vault
ls ai_employee_vault/Done/EXECUTED_MCP_FILESYSTEM_*.json
```

**Success Criteria**: Filesystem MCP action executes and returns directory listing.

---

**Last Updated**: 2026-04-25 | Bronze ✅ Silver ✅ Gold ✅
