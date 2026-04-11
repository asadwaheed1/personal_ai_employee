# AI Employee - Silver Tier Quick Start Guide

## Overview

This guide will help you set up and run the Silver Tier AI Employee system with Gmail and LinkedIn integration in under 45 minutes.

## Prerequisites

- Python 3.10 or higher
- Claude Code CLI installed
- Linux or macOS (Windows requires WSL)
- Gmail account with API access
- LinkedIn account (optional)
- Google Cloud Console access (for Gmail API)

## Installation Steps

### 1. Clone and Setup

```bash
cd /home/asad/projects/personal_ai_employee

# Make scripts executable
chmod +x setup.sh start.sh stop.sh scripts/*.sh

# Run setup
./setup.sh

# Install Silver Tier dependencies
pip install -r requirements.txt
playwright install
```

### 2. Configure Environment Variables

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your credentials
nano .env
```

Add the following to `.env`:
```bash
# Gmail Configuration
GMAIL_CREDENTIALS_PATH=credentials/gmail_credentials.json
GMAIL_TOKEN_PATH=credentials/gmail_token.json

# LinkedIn Configuration (optional)
LINKEDIN_EMAIL=your-email@example.com
LINKEDIN_PASSWORD=your-password

# System Configuration
DRY_RUN=false
CHECK_INTERVAL=120
```

### 3. Setup Gmail API Credentials

```bash
# Create credentials directory
mkdir -p credentials

# Follow these steps:
# 1. Go to https://console.cloud.google.com/apis/credentials
# 2. Create a new project or select existing
# 3. Enable Gmail API
# 4. Create OAuth 2.0 Client ID credentials
# 5. Download JSON and save as credentials/gmail_credentials.json
```

### 4. Verify Installation

```bash
# Check vault structure
ls -la ai_employee_vault/

# Should see:
# - Dashboard.md
# - Company_Handbook.md
# - Inbox/, Needs_Action/, Done/, etc.

# Verify dependencies
python -c "import google.auth; import playwright; print('Dependencies OK')"
```

### 5. Start the System

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

### 6. Start Watchers (Silver Tier)

```bash
# Start watcher manager
python watcher_manager.py ./ai_employee_vault start

# Check watcher status
python watcher_manager.py ./ai_employee_vault status
```

You should see:
```
Watcher Status:
------------------------------------------------------------
gmail_watcher:
  Status: running
  PID: XXXX
  Restarts: 0

linkedin_watcher:
  Status: running
  PID: XXXX
  Restarts: 0
```

### 7. Authorize Gmail (First Time Only)

```bash
# Run Gmail watcher manually for first-time OAuth
python -m src.watchers.run_gmail_watcher ./ai_employee_vault

# Follow the browser prompt to authorize
# Token will be saved to credentials/gmail_token.json
```

### 8. Test the System

#### Test 1: File Processing (Bronze Tier)

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

#### Test 2: Email Processing (Silver Tier)

Send a test email to your Gmail account, then:

```bash
# Check if email was detected
ls -la ai_employee_vault/Needs_Action/EMAIL_*.md

# Process an email
cat > ai_employee_vault/Needs_Action/EMAIL_test.md << 'EOF'
---
type: email
message_id: test_12345
thread_id: test_12345
---

# Email: Test Email

## Suggested Actions
- [x] Mark as read
- [x] Archive
- [ ] Reply
- [ ] Delete

## Human Notes
This is a test email processing.
EOF

# Move to Inbox to trigger processing
mv ai_employee_vault/Needs_Action/EMAIL_test.md ai_employee_vault/Inbox/
```

#### Test 3: MCP Processor (Silver Tier)

```bash
# Run MCP processor to execute email actions
python src/orchestrator/mcp_processor.py ./ai_employee_vault

# Check results
ls -la ai_employee_vault/Done/EXECUTED_MCP_*.json
```

### 9. Monitor the System

```bash
# Watch orchestrator logs
tail -f ai_employee_vault/Logs/orchestrator_$(date +%Y-%m-%d).log

# Watch Gmail watcher logs
tail -f ai_employee_vault/Logs/gmail_watcher_$(date +%Y-%m-%d).log

# Watch MCP processor logs
tail -f ai_employee_vault/Logs/mcp_processor_$(date +%Y-%m-%d).log

# Watch watcher manager logs
tail -f ai_employee_vault/Logs/watcher_manager_$(date +%Y-%m-%d).log

# Check Dashboard
cat ai_employee_vault/Dashboard.md
```

### 10. Verify Processing

After 30-60 seconds, check:

```bash
# File should be in Needs_Action
ls ai_employee_vault/Needs_Action/

# After Claude processes it, should be in Done
ls ai_employee_vault/Done/

# Check for MCP actions
ls ai_employee_vault/Needs_Action/MCP_*.json

# Check executed MCP actions
ls ai_employee_vault/Done/EXECUTED_MCP_*.json

# Dashboard should be updated
cat ai_employee_vault/Dashboard.md
```

### 11. Setup Scheduling (Optional)

```bash
# Linux/Mac
./scripts/setup_cron.sh

# Windows (PowerShell as Administrator)
powershell -ExecutionPolicy Bypass -File scripts/setup_task_scheduler.ps1

# Verify cron jobs
crontab -l
```

## Common Workflows

### Workflow 1: Drop a File for Processing (Bronze Tier)

```bash
# Drop any file into Inbox
cp /path/to/document.pdf ai_employee_vault/Inbox/

# System will:
# 1. Filesystem watcher detects the file (within 5 seconds)
# 2. Create metadata in Needs_Action
# 3. Orchestrator processes (within 30 seconds)
# 4. Process and move to Done
```

### Workflow 2: Process Incoming Emails (Silver Tier)

```bash
# Gmail watcher automatically:
# 1. Monitors unread emails every 2 minutes
# 2. Creates EMAIL_*.md files in Needs_Action
# 3. Flags sensitive emails for approval

# To process an email:
# 1. Open the email file in Needs_Action
# 2. Check the actions you want (mark as read, archive, reply, delete)
# 3. Add notes in "Human Notes" section
# 4. Move file to Inbox

# MCP processor will:
# 1. Create MCP action files
# 2. Execute actions via Gmail MCP server
# 3. Move files to Done with results
```

### Workflow 3: LinkedIn Content Posting (Silver Tier)

```bash
# Create content calendar
python -m src.orchestrator.skills.create_content_plan

# Review generated calendar
cat ai_employee_vault/Plans/content_calendar_*.md

# Post to LinkedIn (with approval)
python -m src.orchestrator.skills.post_linkedin '{
  "content": "Your post content here",
  "schedule_time": "2026-04-03T12:00:00"
}'

# Approve the post
mv ai_employee_vault/Pending_Approval/LINKEDIN_POST_*.md \
   ai_employee_vault/Approved/
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
python watcher_manager.py ./ai_employee_vault status

# Check recent logs
tail -20 ai_employee_vault/Logs/orchestrator_$(date +%Y-%m-%d).log

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
python3 --version  # Should be 3.10+

# Check dependencies
pip3 list | grep -E "watchdog|psutil|google-auth|playwright"

# Reinstall if needed
pip3 install -r requirements.txt
playwright install
```

### Problem: Gmail watcher not working

```bash
# Check credentials exist
ls -la credentials/gmail_credentials.json
ls -la credentials/gmail_token.json

# Re-authorize Gmail
rm credentials/gmail_token.json
python -m src.watchers.run_gmail_watcher ./ai_employee_vault

# Check Gmail watcher logs
tail -50 ai_employee_vault/Logs/gmail_watcher_$(date +%Y-%m-%d).log

# Verify Gmail API is enabled in Google Cloud Console
```

### Problem: MCP actions not executing

```bash
# Check MCP processor logs
tail -50 ai_employee_vault/Logs/mcp_processor_$(date +%Y-%m-%d).log

# Run MCP processor manually
python src/orchestrator/mcp_processor.py ./ai_employee_vault

# Check for MCP action files
ls -la ai_employee_vault/Needs_Action/MCP_*.json

# Verify Gmail MCP server is configured in Claude Code
```

### Problem: Watchers not running

```bash
# Check watcher status
python watcher_manager.py ./ai_employee_vault status

# Check watcher logs
tail -50 ai_employee_vault/Logs/watcher_manager_$(date +%Y-%m-%d).log

# Restart watchers
python watcher_manager.py ./ai_employee_vault stop
python watcher_manager.py ./ai_employee_vault start
```

### Problem: Files not being detected

```bash
# Check watcher logs
cat ai_employee_vault/Logs/filesystem_watcher_*.log

# Verify Inbox exists
ls -la ai_employee_vault/Inbox/

# Check watcher process
ps aux | grep watcher
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

### Problem: LinkedIn watcher fails

```bash
# LinkedIn has strong anti-automation measures
# Check logs for security challenges
tail -50 ai_employee_vault/Logs/linkedin_watcher_$(date +%Y-%m-%d).log

# Run in non-headless mode for manual intervention
# Edit src/watchers/linkedin_watcher.py: headless=False

# Consider using LinkedIn API instead for production
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
# Default: check every 60 seconds
python3 "$PROJECT_ROOT/src/orchestrator/watchdog.py" "$VAULT_PATH" 60

# Faster: check every 30 seconds
python3 "$PROJECT_ROOT/src/orchestrator/watchdog.py" "$VAULT_PATH" 30
```

Edit `.env` for watcher intervals:

```bash
# Gmail watcher check interval (seconds)
GMAIL_CHECK_INTERVAL=120

# LinkedIn watcher check interval (seconds)
LINKEDIN_CHECK_INTERVAL=300
```

### Customize Company Handbook

Edit `ai_employee_vault/Company_Handbook.md` to add your rules:

```markdown
## Custom Rules

### Email Handling
- Always CC me on client emails
- Flag emails from VIP clients as urgent
- Auto-archive promotional emails after marking as read

### File Processing
- PDFs go to /Plans/ for review
- Invoices require approval over $100

### LinkedIn Posting
- Post only on weekdays between 9 AM - 5 PM
- Require approval for all posts mentioning clients
```

### Configure MCP Servers

Ensure Gmail MCP server is configured in Claude Code:

```bash
# Check MCP server configuration
cat ~/.config/claude/mcp_servers.json

# Should include gmail server configuration
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
