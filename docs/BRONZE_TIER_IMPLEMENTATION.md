# Bronze Tier Implementation - Updated Architecture

## Overview

This document describes the corrected and complete Bronze Tier implementation that addresses all critical failure points identified in the initial design review.

## Key Improvements

### 1. Fixed Watcher-to-Claude Trigger Mechanism

**Problem**: Original design used `subprocess.run(['claude', 'prompt'])` which doesn't work with Claude Code's interactive nature.

**Solution**:
- Orchestrator creates a `.claude_instruction.md` file with processing instructions
- Claude Code is invoked with `--cwd` flag pointing to the vault
- Instructions are read from the file, then cleaned up after processing
- This provides a clear, file-based interface for triggering Claude

### 2. Race Condition Handling

**Problem**: Multiple files arriving simultaneously could cause partial processing or file corruption.

**Solution**:
- Implemented global processing lock using `fcntl.flock()`
- Only one Claude Code instance can run at a time
- Files are sorted by modification time (oldest first)
- Debouncing: watcher waits 0.5s after file creation to ensure complete write
- State persistence prevents duplicate processing after crashes

### 3. Persistent State Management

**Problem**: In-memory state lost on crash, causing duplicate processing.

**Solution**:
- All watchers save state to `/.state/` directory
- State includes processed IDs and timestamps
- State is loaded on startup and saved after each batch
- JSON format for easy debugging and manual recovery

### 4. Complete File Drop Workflow

**Problem**: Unclear distinction between `/Inbox/` and `/Needs_Action/`, missing folder monitoring.

**Solution**:
- **Clarified flow**: `/Inbox/` → `/Needs_Action/` → `/Done/`
- File system watcher monitors `/Inbox/` (or any designated drop folder)
- Watcher creates metadata files in `/Needs_Action/`
- Orchestrator monitors three folders: `/Inbox/`, `/Needs_Action/`, `/Approved/`
- Priority order: Approved > Needs_Action > Inbox

### 5. Human-in-the-Loop Completion

**Problem**: No monitoring of `/Approved/` folder.

**Solution**:
- Orchestrator now monitors `/Approved/` folder
- Approved actions processed with highest priority
- Separate processing context for approved vs. new items
- Clear separation of concerns

### 6. Error Recovery and Retry Logic

**Problem**: No handling of failures, timeouts, or errors.

**Solution**:
- Watchdog process monitors all critical processes
- Auto-restart with exponential backoff
- Max 5 restarts per hour per process
- Alert file created for human notification
- Comprehensive logging at all levels

### 7. Atomic Dashboard Updates

**Problem**: Multiple processes writing to Dashboard.md simultaneously.

**Solution**:
- Global processing lock prevents concurrent Claude runs
- Only one process can update Dashboard at a time
- File locking using `fcntl` for critical operations
- State directory (`.state/`) for coordination

### 8. File System Watcher Edge Cases

**Problem**: Files detected before fully written, temp files processed.

**Solution**:
- `_wait_for_file_complete()` monitors file size stability
- `_is_temp_file()` filters out `.tmp`, `.swp`, `.lock`, etc.
- Initial 0.5s wait after detection
- Proper handling of incomplete writes

### 9. Security and Input Validation

**Problem**: No sanitization of filenames or content.

**Solution**:
- `_sanitize_filename()` removes path traversal attempts
- Regex-based cleaning of special characters
- Length limits (100 chars) on filenames
- Unique ID generation using SHA256 hashing

### 10. Comprehensive Logging

**Problem**: No visibility into system operations.

**Solution**:
- Daily log files for each component
- Structured logging with timestamps
- Error logs with stack traces
- Alert file for critical issues
- Separate logs for: orchestrator, watchdog, each watcher

## Architecture Components

### 1. Base Watcher (`base_watcher.py`)
- Abstract base class for all watchers
- Persistent state management
- File locking utilities
- Filename sanitization
- Logging setup

### 2. File System Watcher (`filesystem_watcher.py`)
- Monitors drop folder using `watchdog` library
- Creates metadata files in `/Needs_Action/`
- Handles multiple file types
- MIME type detection
- Human-readable file size formatting

### 3. Orchestrator (`orchestrator.py`)
- Monitors three folders: Inbox, Needs_Action, Approved
- Triggers Claude Code with context-specific instructions
- Global processing lock
- Priority-based processing
- State persistence

### 4. Watchdog (`watchdog.py`)
- Monitors orchestrator and watcher processes
- Auto-restart on failure
- PID-based process tracking
- Restart count limiting
- Human alerting

### 5. Vault Structure
```
ai_employee_vault/
├── Dashboard.md              # Main status dashboard
├── Company_Handbook.md       # Rules and guidelines
├── Inbox/                    # Drop folder for new files
├── Needs_Action/             # Items awaiting processing
├── Done/                     # Completed items
├── Pending_Approval/         # Items requiring approval
├── Approved/                 # Approved actions
├── Rejected/                 # Rejected actions
├── Plans/                    # Action plans
├── Logs/                     # System logs
│   ├── orchestrator_*.log
│   ├── watchdog_*.log
│   ├── filesystem_watcher_*.log
│   └── ALERTS.md
└── .state/                   # Persistent state
    ├── orchestrator_state.json
    ├── filesystem_watcher_state.json
    └── processing.lock
```

## Workflow Examples

### Example 1: Single File Drop

1. User drops `invoice.pdf` into `/Inbox/`
2. File system watcher detects file (after 0.5s wait)
3. Watcher creates `FILE_20260225_173000_invoice.pdf.md` in `/Needs_Action/`
4. Watcher copies `invoice.pdf` to `/Needs_Action/`
5. Orchestrator detects new file in `/Needs_Action/` (within 30s)
6. Orchestrator acquires processing lock
7. Orchestrator creates `.claude_instruction.md` with context
8. Orchestrator triggers Claude Code
9. Claude reads instruction, processes file, updates Dashboard
10. Claude moves processed file to `/Done/`
11. Orchestrator releases lock

### Example 2: Multiple Files Simultaneously

1. User drops 5 files into `/Inbox/` at once
2. File system watcher detects all 5 (with 0.5s debounce each)
3. Watcher creates 5 metadata files in `/Needs_Action/`
4. Orchestrator detects 5 files (sorted by timestamp)
5. Orchestrator acquires lock
6. Orchestrator triggers Claude with "Process 5 items..."
7. Claude processes all 5 files in order
8. Claude moves all to `/Done/`
9. Orchestrator releases lock

### Example 3: Approval Workflow

1. Claude detects sensitive action (e.g., payment)
2. Claude creates approval request in `/Pending_Approval/`
3. Claude updates Dashboard with "Awaiting approval"
4. Human reviews and moves file to `/Approved/`
5. Orchestrator detects file in `/Approved/` (highest priority)
6. Orchestrator triggers Claude with "Execute approved action"
7. Claude executes action via MCP (future: Bronze uses file-based simulation)
8. Claude logs action and moves to `/Done/`

### Example 4: Process Crash Recovery

1. Orchestrator crashes mid-processing
2. Watchdog detects missing PID (within 60s)
3. Watchdog restarts orchestrator
4. Orchestrator loads state from `.state/orchestrator_state.json`
5. Orchestrator sees unprocessed files still in `/Needs_Action/`
6. Orchestrator resumes processing from where it left off

## Testing Scenarios

### Test 1: Basic File Processing
```bash
# Drop a test file
echo "Test content" > ai_employee_vault/Inbox/test.txt

# Check logs
tail -f ai_employee_vault/Logs/filesystem_watcher_*.log
tail -f ai_employee_vault/Logs/orchestrator_*.log

# Verify file moved to Needs_Action, then Done
```

### Test 2: Concurrent Files
```bash
# Drop 10 files simultaneously
for i in {1..10}; do
    echo "Test $i" > ai_employee_vault/Inbox/test_$i.txt &
done
wait

# Verify all 10 processed
ls ai_employee_vault/Done/
```

### Test 3: Process Recovery
```bash
# Kill orchestrator
pkill -f orchestrator.py

# Wait for watchdog to restart (60s)
# Check logs for restart message
grep "restarted" ai_employee_vault/Logs/watchdog_*.log
```

### Test 4: Lock Contention
```bash
# Try to run two orchestrators simultaneously
python3 src/orchestrator/orchestrator.py ai_employee_vault 30 &
python3 src/orchestrator/orchestrator.py ai_employee_vault 30 &

# Second should skip processing due to lock
grep "Another processing instance" ai_employee_vault/Logs/orchestrator_*.log
```

## Known Limitations (Bronze Tier)

1. **Claude Code Integration**: Assumes Claude Code CLI accepts `--cwd` and prompt arguments. May need adjustment based on actual CLI behavior.

2. **No MCP Integration**: Bronze tier uses file-based workflows only. Actual external actions (email, payments) require Silver/Gold tier MCP servers.

3. **Manual Approval**: Human must manually move files between folders. No UI or notification system.

4. **Single Machine**: All components run on one machine. No distributed processing.

5. **No Ralph Wiggum Loop**: Claude runs once per trigger. Multi-step tasks require multiple orchestrator cycles.

## Success Criteria

Bronze Tier is successful when:

- ✅ Files dropped in `/Inbox/` are automatically detected
- ✅ Metadata files created in `/Needs_Action/`
- ✅ Claude Code processes files and updates Dashboard
- ✅ Processed files moved to `/Done/`
- ✅ Multiple files handled correctly
- ✅ Process crashes recovered automatically
- ✅ No duplicate processing after restart
- ✅ All actions logged
- ✅ File locking prevents corruption

## Next Steps for Silver Tier

1. Implement Gmail watcher
2. Add WhatsApp watcher (Playwright-based)
3. Implement MCP servers for external actions
4. Add Ralph Wiggum loop for multi-step tasks
5. Implement proper notification system
6. Add web UI for approval workflow
