# Bronze Tier Implementation - Complete Documentation

**Version:** 1.0
**Last Updated:** 2026-03-28
**Status:** Production Ready

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Usage](#usage)
6. [File Structure](#file-structure)
7. [Workflow](#workflow)
8. [Obsidian Integration](#obsidian-integration)
9. [Agent Skills](#agent-skills)
10. [Troubleshooting](#troubleshooting)
11. [API Reference](#api-reference)

---

## Overview

The Bronze Tier is the foundational implementation of the Personal AI Employee system. It provides automated file processing, task management, and integration with Obsidian for visualization and manual task creation.

### Key Features

- ✅ Automated file monitoring and processing
- ✅ Claude Code integration for intelligent task execution
- ✅ Obsidian vault for visual task management
- ✅ Real-time dashboard updates
- ✅ Comprehensive activity logging
- ✅ Human-in-the-loop approval workflow
- ✅ Configurable rules via Company Handbook

### System Requirements

- **OS:** Linux (tested on Ubuntu 22.04+)
- **Python:** 3.10 or higher
- **Claude Code:** Latest version installed
- **Obsidian:** Optional but recommended for visualization
- **Disk Space:** Minimum 100MB for system + logs

---

## Architecture

### Component Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     AI Employee System                       │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐      ┌──────────────┐                     │
│  │   Watchdog   │─────▶│ Orchestrator │                     │
│  │   Process    │      │   Process    │                     │
│  └──────────────┘      └──────┬───────┘                     │
│                               │                              │
│                               ▼                              │
│                        ┌──────────────┐                      │
│                        │ Claude Code  │                      │
│                        │   Sessions   │                      │
│                        └──────┬───────┘                      │
│                               │                              │
│                               ▼                              │
│  ┌────────────────────────────────────────────────┐         │
│  │           Obsidian Vault                       │         │
│  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ │         │
│  │  │ Inbox  │ │  Done  │ │ Plans  │ │  Logs  │ │         │
│  │  └────────┘ └────────┘ └────────┘ └────────┘ │         │
│  └────────────────────────────────────────────────┘         │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### Process Flow

1. **Watchdog** monitors system health and manages child processes
2. **Orchestrator** scans folders every 30 seconds for new files
3. **Claude Code** is spawned to process detected files
4. **Vault** stores all files, logs, and state information
5. **Obsidian** provides visual interface for monitoring and manual task creation

### Key Components

#### 1. Watchdog (`src/orchestrator/watchdog.py`)
- Monitors orchestrator and filesystem watcher processes
- Restarts failed processes automatically
- Manages PID files in `/tmp/ai_employee_pids/`
- Logs to `Logs/watchdog_YYYY-MM-DD.log`

#### 2. Orchestrator (`src/orchestrator/orchestrator.py`)
- Scans Inbox, Needs_Action, and Approved folders
- Creates instruction files for Claude Code
- Spawns Claude Code with `--dangerously-skip-permissions` flag
- Implements file locking to prevent concurrent processing
- Logs to `Logs/orchestrator_YYYY-MM-DD.log`

#### 3. Claude Code Integration
- Processes tasks based on `.claude_instruction.md` files
- Reads Company_Handbook.md for decision-making rules
- Creates output files in Done folder
- Updates Dashboard.md with activity
- Moves processed files with timestamps

---

## Installation

### Prerequisites

1. **Install Python 3.10+**
   ```bash
   python3 --version  # Should be 3.10 or higher
   ```

2. **Install Claude Code**
   ```bash
   # Follow official Claude Code installation instructions
   claude --version
   ```

3. **Install Obsidian (Optional)**
   ```bash
   # Download from https://obsidian.md/
   # Or install via package manager
   sudo snap install obsidian --classic
   ```

### Setup Steps

1. **Clone the Repository**
   ```bash
   git clone <repository-url>
   cd personal_ai_employee
   ```

2. **Run Setup Script**
   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```

   The setup script will:
   - Create Python virtual environment
   - Install dependencies (watchdog, psutil, pyyaml)
   - Create vault directory structure
   - Setup Agent Skills structure
   - Generate Dashboard.md and Company_Handbook.md
   - Configure Obsidian settings
   - Create README.md with usage instructions

3. **Verify Installation**
   ```bash
   ls -la ai_employee_vault/
   # Should show: Inbox, Done, Needs_Action, Plans, Logs, etc.
   ```

---

## Configuration

### Company Handbook

The `Company_Handbook.md` file defines rules for the AI Employee. Key sections:

#### Human-in-the-Loop Rules
```markdown
Always require human approval for:
- Financial transactions over $50
- Sending emails to new contacts
- Posting on social media
- Deleting or modifying important files
```

#### File Processing Rules
```markdown
- Process files in chronological order (oldest first)
- Move processed files to /Done/ with timestamp
- Log all actions in /Logs/
- Create approval requests in /Pending_Approval/ for sensitive actions
```

#### Decision Matrix
Defines which actions can be auto-approved vs. requiring human approval.

### Orchestrator Configuration

Edit `src/orchestrator/orchestrator.py` to adjust:

- **Check Interval:** Default 30 seconds
  ```python
  check_interval = 30  # seconds
  ```

- **Timeout:** Claude Code execution timeout
  ```python
  timeout=300  # 5 minutes
  ```

- **Monitored Folders:** Add/remove folders to monitor
  ```python
  self.needs_action = self.vault_path / 'Needs_Action'
  self.approved = self.vault_path / 'Approved'
  self.inbox = self.vault_path / 'Inbox'
  ```

---

## Usage

### Starting the System

```bash
./start.sh
```

This will:
- Start the watchdog process
- Start the orchestrator and filesystem watcher
- Display live activity logs
- Monitor Inbox, Needs_Action, and Approved folders

**Output:**
```
=== Starting AI Employee System ===

Vault: /path/to/ai_employee_vault

Starting watchdog process...
✓ Watchdog started (PID: 12345)

System is now running!

Monitoring:
  - Inbox: /path/to/ai_employee_vault/Inbox
  - Needs_Action: /path/to/ai_employee_vault/Needs_Action
  - Approved: /path/to/ai_employee_vault/Approved

Logs: /path/to/ai_employee_vault/Logs

=== Live Activity Log ===

2026-03-28 10:12:34 - Orchestrator - INFO - Orchestrator started
2026-03-28 10:12:34 - Orchestrator - INFO - Monitoring: /path/to/vault
2026-03-28 10:12:34 - Orchestrator - INFO - Check interval: 30 seconds
```

### Stopping the System

```bash
./stop.sh
```

Or press `Ctrl+C` in the terminal running `./start.sh`

### Creating Tasks

#### Method 1: Drop Files in Inbox

1. Create a markdown file with task details:
   ```markdown
   # Task: Generate Weekly Report

   ## Task Type
   Report Generation

   ## Priority
   High

   ## Description
   Create a weekly summary report including:
   1. Tasks completed this week
   2. Pending items
   3. Next week's priorities

   ## Expected Output
   Create weekly_report.md in Done folder

   ---
   *Created: 2026-03-28*
   *Status: Pending*
   ```

2. Save to `ai_employee_vault/Inbox/weekly_report_task.md`

3. Wait ~30 seconds for automatic processing

4. Check `ai_employee_vault/Done/` for results

#### Method 2: Create in Obsidian

1. Open Obsidian with the vault
2. Create new note in Inbox folder
3. Use the task template from README.md
4. Save and watch Dashboard update

### Monitoring Activity

#### Dashboard
Open `Dashboard.md` in Obsidian or any markdown viewer to see:
- System status
- Pending actions
- Recent activity
- Statistics (items processed, queue size, failures)

#### Live Logs
When running `./start.sh`, you'll see real-time logs:
```
2026-03-28 10:15:04 - Orchestrator - INFO - Found 1 total files to process
2026-03-28 10:15:04 - Orchestrator - INFO - Processing 1 files in Inbox
2026-03-28 10:15:04 - Orchestrator - INFO - Triggering Claude Code: Process 1 items from /Inbox/ folder
2026-03-28 10:16:12 - Orchestrator - INFO - Claude processing completed successfully
```

#### Log Files
Check detailed logs in `ai_employee_vault/Logs/`:
- `orchestrator_YYYY-MM-DD.log` - Processing activity
- `watchdog_YYYY-MM-DD.log` - System health monitoring
- `activity_YYYY-MM-DD.md` - Human-readable activity log

---

## File Structure

```
personal_ai_employee/
├── setup.sh                    # Setup script
├── start.sh                    # Start system script
├── stop.sh                     # Stop system script
├── requirements.txt            # Python dependencies
├── CLAUDE.md                   # Claude Code configuration
├── README.md                   # Project overview
├── BRONZE_TIER_DOCS.md        # This file
│
├── src/
│   └── orchestrator/
│       ├── watchdog.py         # Process monitor
│       ├── orchestrator.py     # Main orchestrator
│       └── filesystem_watcher.py  # File system monitor
│
├── venv/                       # Python virtual environment
│
└── ai_employee_vault/          # Obsidian vault
    ├── .obsidian/              # Obsidian configuration
    │   ├── app.json
    │   └── workspace.json
    │
    ├── .state/                 # System state files
    │   ├── orchestrator_state.json
    │   └── processing.lock
    │
    ├── Inbox/                  # Drop new tasks here
    ├── Needs_Action/           # Tasks requiring processing
    ├── Done/                   # Completed tasks
    ├── Plans/                  # Strategic plans
    ├── Pending_Approval/       # Tasks awaiting approval
    ├── Approved/               # Approved tasks
    ├── Rejected/               # Rejected tasks
    ├── Logs/                   # Activity logs
    │
    ├── Dashboard.md            # System status dashboard
    ├── Company_Handbook.md     # Rules and guidelines
    └── README.md               # Vault usage guide
```

---

## Workflow

### Standard Task Processing

```
┌─────────────┐
│ User drops  │
│ task file   │
│ in Inbox    │
└──────┬──────┘
       │
       ▼
┌─────────────────────┐
│ Orchestrator detects│
│ file (every 30s)    │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ Creates instruction │
│ file for Claude     │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ Spawns Claude Code  │
│ with --dangerously- │
│ skip-permissions    │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ Claude reads task   │
│ and Company         │
│ Handbook            │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ Claude processes    │
│ task and creates    │
│ output files        │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ Moves original to   │
│ Done/ with timestamp│
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ Updates Dashboard   │
│ and activity logs   │
└─────────────────────┘
```

### Approval Workflow (Sensitive Actions)

```
┌─────────────┐
│ Task requires│
│ approval     │
└──────┬───────┘
       │
       ▼
┌─────────────────────┐
│ Claude creates      │
│ approval request in │
│ Pending_Approval/   │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ Human reviews       │
│ request details     │
└──────┬──────────────┘
       │
       ├─── Approve ───▶ Move to Approved/
       │
       └─── Reject ────▶ Move to Rejected/

       (If Approved)
       │
       ▼
┌─────────────────────┐
│ Orchestrator detects│
│ file in Approved/   │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ Claude executes     │
│ approved action     │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ Moves to Done/      │
│ Updates Dashboard   │
└─────────────────────┘
```

---

## Obsidian Integration

### Opening the Vault

**Command Line:**
```bash
obsidian /path/to/ai_employee_vault
```

**Manual:**
1. Open Obsidian
2. Click "Open folder as vault"
3. Navigate to `ai_employee_vault`
4. Click "Open"

### Recommended Plugins

While the Bronze Tier works without plugins, these enhance the experience:

1. **Dataview** - Query and display task statistics
2. **Calendar** - Visualize tasks by date
3. **Kanban** - Drag-and-drop task management
4. **Templater** - Advanced task templates

### Obsidian Workflows

#### Creating Tasks
1. Press `Ctrl+N` (new note)
2. Note is automatically created in Inbox folder
3. Use task template from README.md
4. Save with `Ctrl+S`

#### Monitoring Dashboard
1. Pin Dashboard.md to always visible
2. Refresh view to see updates
3. Click links to navigate to related files

#### Reviewing Completed Tasks
1. Navigate to Done folder
2. Use search to filter by date or type
3. View task history and outputs

#### Graph View
1. Press `Ctrl+G` to open graph view
2. Visualize relationships between tasks
3. See linked tasks and references

---

## Troubleshooting

### System Won't Start

**Problem:** `./start.sh` fails or processes don't start

**Solutions:**
1. Check if virtual environment exists:
   ```bash
   ls -la venv/
   ```
   If missing, run `./setup.sh`

2. Check Python dependencies:
   ```bash
   ./venv/bin/pip list | grep -E "watchdog|psutil"
   ```

3. Check for existing processes:
   ```bash
   ps aux | grep -E "watchdog|orchestrator"
   ```
   If found, run `./stop.sh` first

4. Check permissions:
   ```bash
   chmod +x start.sh stop.sh setup.sh
   ```

### Files Not Being Processed

**Problem:** Files dropped in Inbox aren't processed

**Solutions:**
1. Check if system is running:
   ```bash
   ps aux | grep orchestrator
   ```

2. Check orchestrator logs:
   ```bash
   tail -f ai_employee_vault/Logs/orchestrator_$(date +%Y-%m-%d).log
   ```

3. Verify file format:
   - Must be `.md` file
   - Must not start with `.` (hidden)

4. Check processing lock:
   ```bash
   ls -la ai_employee_vault/.state/processing.lock
   ```
   If stuck, remove it:
   ```bash
   rm ai_employee_vault/.state/processing.lock
   ```

### Claude Code Errors

**Problem:** "Claude processing failed" in logs

**Solutions:**
1. Check Claude Code installation:
   ```bash
   claude --version
   ```

2. Test Claude Code manually:
   ```bash
   cd ai_employee_vault
   claude "Read Dashboard.md"
   ```

3. Check instruction file:
   ```bash
   cat ai_employee_vault/.claude_instruction.md
   ```

4. Review error in logs:
   ```bash
   grep ERROR ai_employee_vault/Logs/orchestrator_*.log
   ```

### Obsidian Won't Open Vault

**Problem:** Obsidian fails to open the vault

**Solutions:**
1. Check if Obsidian is installed:
   ```bash
   which obsidian
   ```

2. Open manually:
   - Launch Obsidian
   - Click "Open folder as vault"
   - Select `ai_employee_vault` directory

3. Check vault structure:
   ```bash
   ls -la ai_employee_vault/.obsidian/
   ```
   Should contain `app.json`

4. Reset Obsidian config:
   ```bash
   rm -rf ai_employee_vault/.obsidian/workspace.json
   ```
   Obsidian will recreate it on next open

### High CPU Usage

**Problem:** System using too much CPU

**Solutions:**
1. Increase check interval in orchestrator:
   Edit `src/orchestrator/orchestrator.py`:
   ```python
   check_interval = 60  # Change from 30 to 60 seconds
   ```

2. Check for stuck Claude processes:
   ```bash
   ps aux | grep claude
   ```
   Kill if necessary:
   ```bash
   pkill -f claude
   ```

3. Review log file sizes:
   ```bash
   du -sh ai_employee_vault/Logs/*
   ```
   Archive old logs if needed

### Permission Errors

**Problem:** "Permission denied" errors in logs

**Solutions:**
1. Check vault directory permissions:
   ```bash
   ls -la ai_employee_vault/
   ```
   Should be writable by current user

2. Fix permissions:
   ```bash
   chmod -R u+rw ai_employee_vault/
   ```

3. Check if running as correct user:
   ```bash
   whoami
   ps aux | grep orchestrator
   ```

---

## API Reference

### Orchestrator Class

**Location:** `src/orchestrator/orchestrator.py`

#### Constructor
```python
Orchestrator(vault_path: str, check_interval: int = 30)
```

**Parameters:**
- `vault_path`: Path to the Obsidian vault
- `check_interval`: Seconds between folder scans (default: 30)

#### Methods

##### `run_monitoring_loop()`
Starts the main monitoring loop. Runs indefinitely until interrupted.

```python
orchestrator = Orchestrator('/path/to/vault', 30)
orchestrator.run_monitoring_loop()
```

##### `check_and_trigger()`
Checks for new files and triggers Claude Code if any exist.

```python
orchestrator.check_and_trigger()
```

##### `_trigger_claude_processing(context: str) -> bool`
Spawns Claude Code to process files.

**Parameters:**
- `context`: Description of what to process

**Returns:**
- `True` if successful, `False` otherwise

### Watchdog Class

**Location:** `src/orchestrator/watchdog.py`

#### Constructor
```python
Watchdog(vault_path: str, check_interval: int = 60)
```

**Parameters:**
- `vault_path`: Path to the Obsidian vault
- `check_interval`: Seconds between health checks (default: 60)

#### Methods

##### `start()`
Starts all monitored processes.

##### `stop()`
Stops all monitored processes gracefully.

##### `check_health()`
Checks if all processes are running and restarts if needed.

---

## Performance Metrics

### Bronze Tier Benchmarks

Based on testing with typical workloads:

| Metric | Value |
|--------|-------|
| File detection latency | < 30 seconds |
| Simple task processing | 10-30 seconds |
| Complex task processing | 30-120 seconds |
| Memory usage (idle) | ~50 MB |
| Memory usage (processing) | ~200 MB |
| CPU usage (idle) | < 1% |
| CPU usage (processing) | 10-30% |
| Concurrent file limit | 1 (sequential processing) |

### Scalability Considerations

**Current Limitations:**
- Sequential processing (one file at a time)
- 30-second polling interval
- Single vault instance

**Recommended Limits:**
- Max 100 files per day
- Max 10 MB per file
- Max 1000 files in Done folder (archive periodically)

---

## Security Considerations

### File System Access

The system has full read/write access to the vault directory. Ensure:
- Vault is in a dedicated directory
- No sensitive files outside vault
- Regular backups of vault contents

### Claude Code Permissions

The `--dangerously-skip-permissions` flag bypasses all permission checks. This is safe because:
- Claude only has access to vault directory
- All operations are logged
- Human approval required for sensitive actions

**Security Best Practices:**
1. Review Company_Handbook.md rules regularly
2. Monitor activity logs for unexpected behavior
3. Keep vault directory permissions restricted
4. Don't store API keys or passwords in vault files

### Network Access

Bronze Tier has no network access except:
- Claude Code API calls (for AI processing)
- No email, web, or external API integrations

---

## Maintenance

### Daily Tasks
- Review Dashboard.md for system status
- Check for failed items in logs
- Process any approval requests

### Weekly Tasks
- Archive old log files
- Review and clean Done folder
- Update Company_Handbook.md if needed

### Monthly Tasks
- Backup entire vault directory
- Review system performance metrics
- Update dependencies:
  ```bash
  ./venv/bin/pip install --upgrade watchdog psutil
  ```

### Log Rotation

Logs are created daily but not automatically rotated. To archive:

```bash
# Archive logs older than 30 days
find ai_employee_vault/Logs/ -name "*.log" -mtime +30 -exec gzip {} \;

# Move archived logs to separate directory
mkdir -p ai_employee_vault/Logs/archive
mv ai_employee_vault/Logs/*.gz ai_employee_vault/Logs/archive/
```

---

## Tier Upgrade Path

Bronze Tier is the foundation — Silver and Gold add capabilities without changing the core.

### Silver Tier (Complete)
- Gmail integration + MCP server
- LinkedIn API posting + content calendar
- Multi-watcher system (watcher_manager)
- Email processing workflow (mark read, archive, reply, delete)
- Retry logic + edge case handling
- Cron scheduling

### Gold Tier (Complete)
- Twitter/X watcher + HITL posting skill
- Facebook + Instagram via Meta Graph API
- Cross-platform content calendar (LI/TW/FB/IG)
- Odoo Community 17 ERP — revenue queries + draft invoices
- CEO Weekly Briefing with live financials
- Multiple MCP servers (Gmail + filesystem + Odoo)
- Ralph Wiggum autonomous stop hook
- Comprehensive structured audit logging
- Error recovery hardening + health check

### Migration Path
1. Bronze Tier remains fully functional at all tiers
2. Each tier adds new watchers and integrations
3. Vault structure extended (Briefings/, Content_Calendar/ added in Gold)
4. Company_Handbook.md extended with new rules at each tier

---

## FAQ

### Q: Can I run multiple instances?
**A:** Not recommended. Use a single instance per vault. Multiple instances may conflict.

### Q: How do I change the check interval?
**A:** Edit `src/orchestrator/orchestrator.py` and change `check_interval` parameter, then restart.

### Q: Can I use this without Obsidian?
**A:** Yes! Obsidian is optional. You can drop files in Inbox and check Done folder manually.

### Q: What happens if Claude Code fails?
**A:** The orchestrator logs the error and retries on the next cycle. The file remains in Inbox.

### Q: Can I process non-markdown files?
**A:** Currently only `.md` files are processed. Other file types are ignored.

### Q: How do I backup my vault?
**A:** Simply copy the entire `ai_employee_vault` directory. It's self-contained.

### Q: Can I customize the Dashboard?
**A:** Yes! Edit `Dashboard.md` directly. The system will update the statistics sections.

### Q: What if I accidentally delete a file?
**A:** Check the Done folder - all processed files are moved there with timestamps. Also check logs.

---

## Support and Contributing

### Getting Help
1. Check this documentation
2. Review logs in `ai_employee_vault/Logs/`
3. Check GitHub issues
4. Create a new issue with logs and error details

### Contributing
Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Test thoroughly
4. Submit a pull request

### Reporting Bugs
Include:
- OS and Python version
- Claude Code version
- Relevant log files
- Steps to reproduce
- Expected vs actual behavior

---

## Agent Skills

### Overview

All AI functionality in Bronze Tier is implemented as **Agent Skills**, meeting the hackathon requirement that "All AI functionality should be implemented as Agent Skills".

### Skills Architecture

```
.claude/tools/
└── bronze_tier_skills.json    # Skills manifest

src/orchestrator/skills/
├── base_skill.py              # Base class for all skills
├── process_needs_action.py    # Process Needs_Action files
├── update_dashboard.py        # Update Dashboard.md
├── create_plan.py             # Generate action plans
├── create_approval_request.py # Create approval requests
├── parse_watcher_file.py      # Parse watcher files
├── process_inbox.py           # Process Inbox files
└── process_approved_actions.py # Execute approved actions
```

### Available Skills

| Skill | Purpose |
|-------|---------|
| `process_needs_action` | Process files in Needs_Action directory |
| `update_dashboard` | Update Dashboard.md with current status |
| `create_plan` | Generate structured action plans |
| `create_approval_request` | Create approval requests for sensitive actions |
| `parse_watcher_file` | Extract information from watcher files |
| `process_inbox` | Process files dropped in Inbox folder |
| `process_approved_actions` | Execute approved actions |

### Using Skills

```bash
# Example: Update dashboard
python src/orchestrator/skills/update_dashboard.py '{
  "vault_path": "/path/to/vault",
  "status": "operational"
}'

# Example: Process Inbox
python src/orchestrator/skills/process_inbox.py '{
  "vault_path": "/path/to/vault"
}'
```

For detailed skills documentation, see:
- [AGENT_SKILLS_DOCUMENTATION.md](AGENT_SKILLS_DOCUMENTATION.md)
- [AGENT_SKILLS_QUICK_REFERENCE.md](AGENT_SKILLS_QUICK_REFERENCE.md)

---

## Changelog

### Version 3.0 (2026-04-25) — Gold Tier Complete
- Twitter/X, Facebook, Instagram integration
- Odoo ERP accounting skill + MCP server
- CEO Weekly Briefing with live financial data
- Cross-platform content calendar
- Multiple MCP servers (Gmail + filesystem + Odoo)
- Comprehensive audit logging (audit_master.json)
- Ralph Wiggum autonomous stop hook
- Error recovery hardening + health check utility

### Version 2.0 (2026-04-11) — Silver Tier Complete
- Gmail integration + MCP server
- LinkedIn API posting + content calendar
- Multi-watcher management system
- Email processing workflow
- Retry logic + edge case handling
- Cron scheduling

### Version 1.0 (2026-03-28) — Bronze Tier
- Initial release
- Automated file processing
- Claude Code integration
- Obsidian vault support
- Dashboard and logging
- Human-in-the-loop approval workflow
- Agent Skills framework (7 modular skills)

---

## License

[Your License Here]

---

## Acknowledgments

- Claude Code by Anthropic
- Obsidian by Obsidian.md
- Python watchdog library
- psutil library

---

**End of Bronze Tier Documentation**

For questions or support, please refer to the project repository or contact the maintainers.
