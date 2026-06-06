# Project Structure

```
personal_ai_employee/
├── README.md                           # Project overview
├── CLAUDE.md                           # Claude Code configuration
├── AGENTS.md                           # Agent architecture documentation
├── requirements.md                     # Full project requirements
├── BRONZE_TIER_IMPLEMENTATION.md       # Updated architecture details
├── QUICKSTART.md                       # Quick start guide
├── TESTING.md                          # Comprehensive testing guide
├── requirements.txt                    # Python dependencies
├── setup.sh                            # Setup script
├── start.sh                            # Start script
├── stop.sh                             # Stop script
│
├── ai_employee_vault/                  # Obsidian vault
│   ├── Dashboard.md                    # Main dashboard
│   ├── Company_Handbook.md             # Rules and guidelines
│   ├── Inbox/                          # Drop folder for new files
│   ├── Needs_Action/                   # Items awaiting processing
│   ├── Done/                           # Completed items
│   ├── Pending_Approval/               # Items requiring approval
│   ├── Approved/                       # Approved actions
│   ├── Rejected/                       # Rejected actions
│   ├── Plans/                          # Action plans
│   ├── Logs/                           # System logs
│   │   ├── orchestrator_YYYY-MM-DD.log
│   │   ├── watchdog_YYYY-MM-DD.log
│   │   ├── filesystem_watcher_YYYY-MM-DD.log
│   │   └── ALERTS.md
│   └── .state/                         # Persistent state
│       ├── orchestrator_state.json
│       ├── filesystem_watcher_state.json
│       └── processing.lock
│
└── src/                                # Source code
    ├── watchers/                       # Watcher implementations
    │   ├── base_watcher.py             # Abstract base class
    │   ├── filesystem_watcher.py       # File system watcher
    │   └── run_filesystem_watcher.py   # Entry point
    │
    └── orchestrator/                   # Orchestration layer
        ├── orchestrator.py             # Main orchestrator
        └── watchdog.py                 # Process monitor
```

## File Descriptions

### Documentation Files

- **README.md**: Project overview and introduction
- **CLAUDE.md**: Claude Code configuration and integration details
- **AGENTS.md**: Complete agent architecture documentation
- **requirements.md**: Full hackathon requirements and specifications
- **BRONZE_TIER_IMPLEMENTATION.md**: Updated architecture with all fixes
- **QUICKSTART.md**: Step-by-step guide to get started quickly
- **TESTING.md**: Comprehensive testing scenarios and validation

### Configuration Files

- **requirements.txt**: Python package dependencies
- **setup.sh**: Automated setup script
- **start.sh**: System startup script
- **stop.sh**: System shutdown script

### Vault Files

- **Dashboard.md**: Real-time system status and activity log
- **Company_Handbook.md**: Rules, guidelines, and decision matrix

### Source Code

#### Watchers (`src/watchers/`)

- **base_watcher.py**: Abstract base class with:
  - Persistent state management
  - File locking utilities
  - Filename sanitization
  - Logging setup
  - Error handling

- **filesystem_watcher.py**: File system monitoring with:
  - Watchdog library integration
  - Temp file filtering
  - MIME type detection
  - Metadata file creation
  - File size formatting

- **run_filesystem_watcher.py**: Entry point for running the watcher

#### Orchestrator (`src/orchestrator/`)

- **orchestrator.py**: Main coordination logic with:
  - Multi-folder monitoring
  - Global processing lock
  - Priority-based processing
  - Claude Code integration
  - State persistence

- **watchdog.py**: Process monitoring with:
  - PID-based tracking
  - Auto-restart logic
  - Restart count limiting
  - Human alerting
  - Graceful shutdown

## Key Design Decisions

### 1. File-Based Communication
All components communicate through the file system, making the system:
- Easy to debug (just look at files)
- Resilient (state persists across crashes)
- Transparent (humans can see everything)

### 2. Global Processing Lock
Prevents concurrent Claude Code runs, ensuring:
- No race conditions
- No file corruption
- Predictable behavior

### 3. Persistent State
All state saved to JSON files, providing:
- Crash recovery
- No duplicate processing
- Audit trail

### 4. Priority-Based Processing
Folders processed in order: Approved > Needs_Action > Inbox
- Urgent actions handled first
- Clear workflow progression
- Human approvals prioritized

### 5. Watchdog Pattern
Separate process monitors workers, ensuring:
- Automatic recovery
- High availability
- Minimal downtime

## Data Flow

```
1. External Event (file drop)
   ↓
2. File System Watcher detects
   ↓
3. Metadata file created in Needs_Action
   ↓
4. Orchestrator detects new file (30s polling)
   ↓
5. Orchestrator acquires processing lock
   ↓
6. Orchestrator creates instruction file
   ↓
7. Orchestrator triggers Claude Code
   ↓
8. Claude reads instruction and processes
   ↓
9. Claude updates Dashboard
   ↓
10. Claude moves files to Done
    ↓
11. Orchestrator releases lock
    ↓
12. Watchdog verifies all processes running
```

## State Management

### Watcher State
```json
{
  "processed_ids": ["abc123", "def456", ...],
  "last_updated": "2026-02-25T17:40:00Z"
}
```

### Orchestrator State
```json
{
  "last_check": "2026-02-25T17:40:00Z",
  "processed_count": 42
}
```

### Processing Lock
- File: `.state/processing.lock`
- Contains: Timestamp of lock acquisition
- Mechanism: `fcntl.flock()` for atomic locking

## Logging Strategy

### Log Levels
- **INFO**: Normal operations (file detected, processing started)
- **WARNING**: Recoverable issues (process restart, lock contention)
- **ERROR**: Failures requiring attention (crash, timeout)

### Log Rotation
- Daily log files (one per component)
- Format: `component_YYYY-MM-DD.log`
- Retention: Manual cleanup (consider adding rotation later)

### Alert File
- Special file: `Logs/ALERTS.md`
- Contains: Critical issues requiring human attention
- Format: Markdown for easy reading

## Security Considerations

### File System Security
- Vault directory should have restricted permissions (700)
- State directory not world-readable
- PID files in `/tmp` (consider moving to vault)

### Input Validation
- All filenames sanitized
- Path traversal prevented
- File size limits (future enhancement)

### Process Isolation
- Each component runs as separate process
- Crash in one doesn't affect others
- Watchdog ensures recovery

## Performance Characteristics

### Expected Throughput
- File detection: < 5 seconds
- Orchestrator trigger: < 30 seconds
- Total latency: 35-60 seconds per file

### Resource Usage
- Memory: ~50-100MB per process
- CPU: Minimal (mostly idle)
- Disk: Logs grow ~1MB/day

### Scalability Limits (Bronze Tier)
- Max files/hour: ~120 (limited by 30s polling)
- Max concurrent files: Unlimited (queued)
- Max file size: Limited by disk space

## Future Enhancements (Silver/Gold Tier)

### Silver Tier Additions
- Gmail watcher
- WhatsApp watcher
- MCP servers for external actions
- Ralph Wiggum loop for multi-step tasks
- Web UI for approvals

### Gold Tier Additions
- Multiple MCP servers
- Cross-domain integration
- Weekly business audits
- Odoo accounting integration
- Social media integration

## Maintenance Tasks

### Daily
- Check `ALERTS.md` for critical issues
- Review Dashboard for activity

### Weekly
- Review logs for errors
- Check disk space usage
- Verify all processes running

### Monthly
- Rotate/archive old logs
- Review and update Company_Handbook
- Test recovery procedures

## Development Workflow

### Adding a New Watcher

1. Create new file in `src/watchers/`
2. Inherit from `BaseWatcher`
3. Implement `check_for_updates()` and `create_action_file()`
4. Add to watchdog process definitions
5. Test thoroughly
6. Update documentation

### Modifying Processing Logic

1. Update `Company_Handbook.md` with new rules
2. Test with Claude Code manually
3. Verify Dashboard updates correctly
4. Check logs for errors
5. Document changes

### Debugging Issues

1. Check relevant log files
2. Verify state files are correct
3. Check for stuck locks
4. Review recent file activity
5. Test with minimal example
