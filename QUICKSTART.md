# AI Employee - Bronze Tier Quick Start Guide

## Overview

This guide will help you set up and run the Bronze Tier AI Employee system in under 30 minutes.

## Prerequisites

- Python 3.8 or higher
- Claude Code CLI installed
- Linux or macOS (Windows requires WSL)

## Installation Steps

### 1. Clone and Setup

```bash
cd /home/asad/piaic/projects/personal_ai_employee

# Make scripts executable
chmod +x setup.sh start.sh stop.sh

# Run setup
./setup.sh
```

### 2. Verify Installation

```bash
# Check vault structure
ls -la ai_employee_vault/

# Should see:
# - Dashboard.md
# - Company_Handbook.md
# - Inbox/, Needs_Action/, Done/, etc.
```

### 3. Start the System

```bash
./start.sh
```

You should see:
```
=== Starting AI Employee System ===
Starting watchdog process...
✓ Watchdog started (PID: XXXX)
System is now running!
```

### 4. Test the System

Open a new terminal and drop a test file:

```bash
# Create a test task
cat > ai_employee_vault/Inbox/test_task.md << 'EOF'
---
type: task
priority: medium
---

# Test Task

Please process this test task and update the dashboard.

## Details
- This is a test of the file processing workflow
- Should be moved to Needs_Action, then Done
- Dashboard should be updated

## Expected Actions
- [ ] Read this file
- [ ] Update Dashboard.md
- [ ] Move to Done folder
EOF
```

### 5. Monitor the System

```bash
# Watch the logs
tail -f ai_employee_vault/Logs/filesystem_watcher_*.log

# In another terminal
tail -f ai_employee_vault/Logs/orchestrator_*.log

# Check Dashboard
cat ai_employee_vault/Dashboard.md
```

### 6. Verify Processing

After 30-60 seconds, check:

```bash
# File should be in Needs_Action
ls ai_employee_vault/Needs_Action/

# After Claude processes it, should be in Done
ls ai_employee_vault/Done/

# Dashboard should be updated
cat ai_employee_vault/Dashboard.md
```

## Common Workflows

### Workflow 1: Drop a File for Processing

```bash
# Drop any file into Inbox
cp /path/to/document.pdf ai_employee_vault/Inbox/

# System will:
# 1. Detect the file (within 5 seconds)
# 2. Create metadata in Needs_Action
# 3. Trigger Claude (within 30 seconds)
# 4. Process and move to Done
```

### Workflow 2: Request Approval for Sensitive Action

```bash
# Create an approval request
cat > ai_employee_vault/Pending_Approval/payment_request.md << 'EOF'
---
type: approval_request
action: payment
amount: 500.00
recipient: Vendor ABC
---

# Payment Approval Request

Please approve payment of $500 to Vendor ABC for services rendered.

## To Approve
Move this file to /Approved/

## To Reject
Move this file to /Rejected/
EOF

# Review and approve
mv ai_employee_vault/Pending_Approval/payment_request.md \
   ai_employee_vault/Approved/

# System will process the approved action
```

### Workflow 3: Check System Status

```bash
# View Dashboard
cat ai_employee_vault/Dashboard.md

# Check recent logs
tail -20 ai_employee_vault/Logs/orchestrator_*.log

# Check for alerts
cat ai_employee_vault/Logs/ALERTS.md

# View processing state
cat ai_employee_vault/.state/orchestrator_state.json
```

## Stopping the System

```bash
./stop.sh
```

## Troubleshooting

### Problem: System not starting

```bash
# Check Python version
python3 --version  # Should be 3.8+

# Check dependencies
pip3 list | grep -E "watchdog|psutil"

# Reinstall if needed
pip3 install -r requirements.txt
```

### Problem: Files not being detected

```bash
# Check watcher logs
cat ai_employee_vault/Logs/filesystem_watcher_*.log

# Verify Inbox exists
ls -la ai_employee_vault/Inbox/

# Check watcher process
ps aux | grep filesystem_watcher
```

### Problem: Claude not processing

```bash
# Check Claude Code is installed
which claude

# Check orchestrator logs
cat ai_employee_vault/Logs/orchestrator_*.log

# Check for processing lock
ls -la ai_employee_vault/.state/processing.lock

# If stuck, remove lock and restart
rm -f ai_employee_vault/.state/processing.lock
./stop.sh && ./start.sh
```

### Problem: Duplicate processing

```bash
# Check state files
cat ai_employee_vault/.state/filesystem_watcher_state.json

# Reset state if needed (CAUTION: will reprocess all files)
rm ai_employee_vault/.state/*.json
./stop.sh && ./start.sh
```

## Configuration

### Adjust Check Intervals

Edit `start.sh` to change timing:

```bash
# Default: check every 60 seconds
python3 "$PROJECT_ROOT/src/orchestrator/watchdog.py" "$VAULT_PATH" 60

# Faster: check every 30 seconds
python3 "$PROJECT_ROOT/src/orchestrator/watchdog.py" "$VAULT_PATH" 30
```

### Customize Company Handbook

Edit `ai_employee_vault/Company_Handbook.md` to add your rules:

```markdown
## Custom Rules

### Email Handling
- Always CC me on client emails
- Flag emails from VIP clients as urgent

### File Processing
- PDFs go to /Plans/ for review
- Invoices require approval over $100
```

## Next Steps

1. **Customize the handbook** with your specific rules
2. **Test with real files** from your workflow
3. **Monitor for a few days** to ensure stability
4. **Add more watchers** (Gmail, WhatsApp) for Silver tier
5. **Implement MCP servers** for external actions

## Getting Help

- Check logs in `ai_employee_vault/Logs/`
- Review `BRONZE_TIER_IMPLEMENTATION.md` for architecture details
- See `AGENTS.md` for component documentation
- Check `requirements.md` for the full specification

## Success Checklist

- [ ] System starts without errors
- [ ] Files dropped in Inbox are detected
- [ ] Metadata files created in Needs_Action
- [ ] Claude processes files (or instruction file created)
- [ ] Dashboard updates with activity
- [ ] Files move to Done after processing
- [ ] System recovers from manual process kill
- [ ] Logs show no errors
- [ ] Approval workflow works (Pending → Approved → Done)

Congratulations! Your Bronze Tier AI Employee is now operational.
