# AI Employee - Silver Tier Quick Start Guide

## Overview

This guide will help you set up and run the Silver Tier AI Employee system in under 30 minutes.

## Prerequisites

- Python 3.8 or higher
- Claude Code CLI installed
- Linux or macOS (Windows requires WSL)
- Gmail account with API access (optional but recommended)
- LinkedIn account (optional)

## Installation Steps

### 1. Clone and Setup

```bash
cd /home/asad/piaic/projects/personal_ai_employee

# Make scripts executable
chmod +x setup.sh start.sh stop.sh

# Run setup
./setup.sh
```

### 2. Configure Credentials

```bash
# Copy environment template
cp .env.example .env

# Edit with your credentials
nano .env
```

Add your credentials:
```bash
# Gmail API
GMAIL_CREDENTIALS_PATH=credentials/gmail_credentials.json

# LinkedIn (optional)
LINKEDIN_USERNAME=your_email@example.com
LINKEDIN_PASSWORD=your_password
```

### 3. Setup Gmail API (Recommended)

1. Go to https://console.cloud.google.com/apis/credentials
2. Create a new project or select existing
3. Enable Gmail API
4. Create OAuth 2.0 credentials
5. Download credentials and save as `credentials/gmail_credentials.json`

### 4. First-Time Authentication (IMPORTANT)

**Gmail OAuth (Required on first run):**

Before running `./start.sh`, you must authenticate Gmail once:

```bash
# Run Gmail watcher manually for first-time OAuth
python -m src.watchers.run_gmail_watcher ./ai_employee_vault

# A browser window will open for Google authentication
# Sign in and grant permissions
# After successful auth, press Ctrl+C to stop
```

This creates `credentials/gmail_token.json` which will be used automatically by `./start.sh`.

**LinkedIn Authentication (If configured):**

LinkedIn watcher may require manual login on first run due to CAPTCHA/security challenges:
- The watcher opens a browser window (non-headless mode)
- Complete any CAPTCHA or security verification manually
- The session is saved for future runs
- After first successful login, subsequent runs are automatic

**Note:** After first-time authentication is complete, `./start.sh` will work smoothly without manual intervention.

### 5. Verify Installation

```bash
# Check vault structure
ls -la ai_employee_vault/

# Should see:
# - Dashboard.md
# - Company_Handbook.md
# - Inbox/, Needs_Action/, Done/, MCP_Actions/, etc.
```

### 6. Start the System

```bash
./start.sh
```

You should see:
```
=== Starting AI Employee System ===
Starting Watcher Manager...
✓ Watcher Manager started (PID: XXXX)
Starting Orchestrator...
✓ Orchestrator started (PID: XXXX)
System is now running!

Active Components:
  - Watcher Manager (manages Gmail & LinkedIn watchers)
  - Orchestrator (processes actions and MCP requests)
```

### 7. Test the System

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

### 8. Monitor the System

```bash
# Watch the orchestrator logs
tail -f ai_employee_vault/Logs/orchestrator_*.log

# In another terminal, watch watcher logs
tail -f ai_employee_vault/Logs/watcher_manager_*.log

# Check Dashboard
cat ai_employee_vault/Dashboard.md
```

### 9. Verify Processing

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
# 1. Filesystem watcher detects the file (within 5 seconds)
# 2. Create metadata in Needs_Action
# 3. Orchestrator processes (within 30 seconds)
# 4. Process and move to Done
```

### Workflow 2: Email Processing

```bash
# Gmail watcher automatically detects new emails
# Creates email files in Needs_Action

# To process an email:
# 1. Open the email file in Needs_Action
# 2. Check the boxes for desired actions:
#    - [x] Mark as read
#    - [x] Archive
#    - [x] Reply (add your notes in Human Notes section)
# 3. Move file to Inbox
# 4. Orchestrator processes actions via MCP server
```

### Workflow 3: LinkedIn Monitoring

```bash
# LinkedIn watcher monitors messages automatically
# Creates action files for messages with business keywords

# System will:
# 1. Detect messages with keywords (project, opportunity, etc.)
# 2. Create action file in Needs_Action
# 3. Wait for your review and approval
# 4. Process approved actions
```

### Workflow 4: Request Approval for Sensitive Action

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

### Workflow 5: Check System Status

```bash
# View Dashboard
cat ai_employee_vault/Dashboard.md

# Check watcher status
cat ai_employee_vault/.state/watcher_manager_state.json

# Check recent logs
tail -20 ai_employee_vault/Logs/orchestrator_*.log

# View MCP action status
ls -la ai_employee_vault/MCP_Actions/

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
pip3 list | grep -E "google-auth|playwright|psutil"

# Reinstall if needed
pip3 install -r requirements.txt
playwright install
```

### Problem: Gmail watcher not working

```bash
# Check credentials exist
ls -la credentials/gmail_credentials.json

# Check watcher logs
cat ai_employee_vault/Logs/gmail_watcher_*.log

# Verify .env configuration
cat .env | grep GMAIL

# Check watcher process
ps aux | grep gmail_watcher
```

### Problem: LinkedIn watcher not working

```bash
# Check credentials in .env
cat .env | grep LINKEDIN

# Check watcher logs
cat ai_employee_vault/Logs/linkedin_watcher_*.log

# LinkedIn may require manual login first time
# Run in non-headless mode to complete security challenges
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

### Problem: MCP actions not executing

```bash
# Check MCP_Actions folder
ls -la ai_employee_vault/MCP_Actions/

# Check orchestrator logs for MCP processing
grep "MCP" ai_employee_vault/Logs/orchestrator_*.log

# Verify MCP processor is running
ps aux | grep orchestrator

# Check for stale locks
ls -la ai_employee_vault/.state/*.lock
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
cat ai_employee_vault/.state/watcher_manager_state.json

# Reset state if needed (CAUTION: will reprocess all files)
rm ai_employee_vault/.state/*.json
./stop.sh && ./start.sh
```

### Problem: Watcher keeps restarting

```bash
# Check watcher manager logs
cat ai_employee_vault/Logs/watcher_manager_*.log

# Check restart count in state
cat ai_employee_vault/.state/watcher_manager_state.json

# If max restarts reached, check individual watcher logs
cat ai_employee_vault/Logs/gmail_watcher_*.log
cat ai_employee_vault/Logs/linkedin_watcher_*.log
```

## Configuration

### Adjust Check Intervals

Edit watcher configuration in the code:

```python
# Gmail watcher: src/watchers/gmail_watcher.py
check_interval = 120  # seconds (default: 2 minutes)

# LinkedIn watcher: src/watchers/linkedin_watcher.py
check_interval = 300  # seconds (default: 5 minutes)

# Filesystem watcher: src/watchers/filesystem_watcher.py
check_interval = 5  # seconds (default: 5 seconds)
```

### Setup Scheduled Tasks

```bash
# Linux/Mac - Setup cron jobs
./scripts/setup_cron.sh

# Windows - Setup Task Scheduler
powershell -ExecutionPolicy Bypass -File scripts/setup_task_scheduler.ps1
```

Scheduled tasks include:
- Hourly: Check content calendar
- Daily 9 AM: LinkedIn posting
- Weekly Sunday 6 PM: Generate content calendar
- Every 15 minutes: Process approved actions
- Daily 8 AM: Dashboard update

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
2. **Test with real emails** - send test emails to monitored account
3. **Test LinkedIn monitoring** - send test messages with keywords
4. **Monitor for a few days** to ensure stability
5. **Setup scheduling** for automated tasks
6. **Review MCP actions** to understand external integrations

## Silver Tier Features

### Active Watchers
- **Filesystem Watcher**: Monitors Inbox for dropped files
- **Gmail Watcher**: Monitors unread emails, creates action files
- **LinkedIn Watcher**: Monitors messages for business opportunities

### Email Processing
- Mark as read
- Archive emails
- Reply with custom notes
- Delete emails
- All actions via Gmail MCP server

### MCP Integration
- All external actions use MCP servers
- Gmail MCP for email operations
- Action files in MCP_Actions folder
- Automatic execution and result tracking

### Human-in-the-Loop
- Approval workflow for sensitive actions
- Email replies require human notes
- LinkedIn posts require approval
- Financial transactions flagged

### Scheduling
- Automated cron jobs for regular tasks
- Content calendar generation
- Scheduled LinkedIn posting
- Regular dashboard updates

## Getting Help

- Check logs in `ai_employee_vault/Logs/`
- Review `status.md` for current implementation status
- See `EMAIL_WORKFLOW_GUIDE.md` for email processing
- See `LINKEDIN_WATCHER_GUIDE.md` for LinkedIn setup
- Check `SILVER_TIER_EDGE_CASES_FIXED.md` for edge case handling
- Review `requirements.md` for full specification

## Success Checklist

- [ ] System starts without errors
- [ ] Watcher Manager starts all watchers
- [ ] Files dropped in Inbox are detected
- [ ] Gmail watcher detects new emails (if configured)
- [ ] LinkedIn watcher monitors messages (if configured)
- [ ] Metadata files created in Needs_Action
- [ ] Orchestrator processes files
- [ ] MCP actions execute successfully
- [ ] Dashboard updates with activity
- [ ] Watcher status shows in Dashboard
- [ ] Files move to Done after processing
- [ ] Email actions work (mark read, archive, reply)
- [ ] System recovers from manual process kill
- [ ] Logs show no errors
- [ ] Approval workflow works (Pending → Approved → Done)
- [ ] Scheduled tasks execute (if configured)

Congratulations! Your Silver Tier AI Employee is now operational.
