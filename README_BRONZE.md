# Personal AI Employee - Bronze Tier

This project implements a Personal AI Employee using Claude Code as the reasoning engine and Obsidian as the knowledge base and dashboard.

## Overview

The Personal AI Employee is designed as a digital full-time equivalent (FTE) that operates autonomously to manage personal and business tasks. It uses:

- **Claude Code**: The reasoning engine
- **Obsidian**: Memory and dashboard
- **Python Watchers**: Sensors for external events
- **File-Based Workflows**: State management and coordination

## Bronze Tier Features

✅ **Implemented**:
- File system watcher for drop folder monitoring
- Orchestrator for coordinating Claude Code processing
- Watchdog for automatic process recovery
- Persistent state management (no duplicate processing)
- File locking (prevents race conditions)
- Human-in-the-loop approval workflow
- Comprehensive logging and alerting
- Dashboard updates

## Quick Start

```bash
# 1. Setup
./setup.sh

# 2. Install dependencies
pip3 install -r requirements.txt

# 3. Start the system
./start.sh

# 4. Test by dropping a file
echo "Test task" > ai_employee_vault/Inbox/test.md

# 5. Monitor logs
tail -f ai_employee_vault/Logs/*.log

# 6. Stop the system
./stop.sh
```

See [QUICKSTART.md](QUICKSTART.md) for detailed instructions.

## Documentation

- **[QUICKSTART.md](QUICKSTART.md)**: Get started in 30 minutes
- **[BRONZE_TIER_IMPLEMENTATION.md](BRONZE_TIER_IMPLEMENTATION.md)**: Complete architecture details
- **[TESTING.md](TESTING.md)**: Comprehensive testing guide
- **[PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)**: File organization and design decisions
- **[CLAUDE.md](CLAUDE.md)**: Claude Code configuration
- **[AGENTS.md](AGENTS.md)**: Agent architecture documentation
- **[requirements.md](requirements.md)**: Full hackathon requirements

## Architecture

```
External Event (file drop)
    ↓
File System Watcher (detects within 5s)
    ↓
Creates metadata in /Needs_Action/
    ↓
Orchestrator (polls every 30s)
    ↓
Triggers Claude Code with instruction file
    ↓
Claude processes and updates Dashboard
    ↓
Files moved to /Done/
    ↓
Watchdog ensures all processes running
```

## Key Improvements Over Initial Design

1. **Fixed Claude Code Integration**: Uses instruction files instead of broken subprocess calls
2. **Race Condition Handling**: Global processing lock prevents concurrent runs
3. **Persistent State**: Survives crashes, prevents duplicate processing
4. **Complete Approval Workflow**: Monitors /Approved/ folder for human decisions
5. **Error Recovery**: Watchdog auto-restarts failed processes
6. **Atomic Operations**: File locking prevents corruption
7. **Edge Case Handling**: Temp file filtering, incomplete write detection
8. **Security**: Filename sanitization, input validation
9. **Comprehensive Logging**: Daily logs per component with alerts

## Project Structure

```
personal_ai_employee/
├── ai_employee_vault/          # Obsidian vault
│   ├── Dashboard.md
│   ├── Company_Handbook.md
│   ├── Inbox/                  # Drop files here
│   ├── Needs_Action/
│   ├── Done/
│   ├── Pending_Approval/
│   ├── Approved/
│   ├── Logs/
│   └── .state/
├── src/
│   ├── watchers/
│   │   ├── base_watcher.py
│   │   └── filesystem_watcher.py
│   └── orchestrator/
│       ├── orchestrator.py
│       └── watchdog.py
├── setup.sh
├── start.sh
└── stop.sh
```

## Requirements

- Python 3.8+
- Claude Code CLI
- Linux or macOS (Windows requires WSL)

### Python Dependencies

```
watchdog>=3.0.0
psutil>=5.9.0
```

Install with: `pip3 install -r requirements.txt`

## Testing

Run the comprehensive test suite:

```bash
# See TESTING.md for all tests
# Example: Single file test
echo "Test" > ai_employee_vault/Inbox/test.md
sleep 40
ls ai_employee_vault/Done/
```

## Success Criteria (Bronze Tier)

- ✅ Files dropped in Inbox are detected automatically
- ✅ Metadata files created in Needs_Action
- ✅ Claude Code processes files
- ✅ Dashboard updates with activity
- ✅ Files move to Done after processing
- ✅ Multiple files handled without corruption
- ✅ System recovers from crashes
- ✅ No duplicate processing
- ✅ Approval workflow complete

## Troubleshooting

### System not starting
```bash
# Check Python version
python3 --version

# Reinstall dependencies
pip3 install -r requirements.txt

# Check logs
cat ai_employee_vault/Logs/watchdog_*.log
```

### Files not being processed
```bash
# Check watcher is running
ps aux | grep filesystem_watcher

# Check orchestrator logs
cat ai_employee_vault/Logs/orchestrator_*.log

# Remove stuck lock
rm -f ai_employee_vault/.state/processing.lock
./stop.sh && ./start.sh
```

See [TESTING.md](TESTING.md) for more troubleshooting scenarios.

## Next Steps (Silver Tier)

- [ ] Gmail watcher implementation
- [ ] WhatsApp watcher (Playwright-based)
- [ ] MCP servers for external actions
- [ ] Ralph Wiggum loop for multi-step tasks
- [ ] Web UI for approval workflow

## Contributing

This is a hackathon project. See `requirements.md` for the full specification and judging criteria.

## License

Educational project for PIAIC Hackathon 0.

## Contact

For questions or issues, check the documentation files or review the logs in `ai_employee_vault/Logs/`.
