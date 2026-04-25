# Personal AI Employee

An intelligent automation system that processes tasks, manages workflows, and integrates with Obsidian for visual task management. Built with Claude Code and designed for personal productivity and business automation.

![Status](https://img.shields.io/badge/status-production%20ready-brightgreen)
![Version](https://img.shields.io/badge/version-3.0%20(Gold%20Tier)-gold)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)

---

## 🎯 Overview

The Personal AI Employee is a three-tier automation system designed to handle personal and business tasks with increasing levels of sophistication:

- **Bronze Tier** (Complete): File-based task processing with Obsidian integration
- **Silver Tier** (Complete): Email and LinkedIn automation with MCP integration
- **Gold Tier** (Current): Social media, Odoo ERP, CEO briefings, audit logging

---

## ✨ Features (Gold Tier)

### Core Features (Bronze Tier)
- ✅ **Automated Task Processing** - Drop markdown files, get results automatically
- ✅ **Claude Code Integration** - Intelligent task execution with AI reasoning
- ✅ **Agent Skills Framework** - All AI functionality implemented as modular Agent Skills
- ✅ **Obsidian Vault** - Visual task management and monitoring
- ✅ **Real-time Dashboard** - Live system status and activity tracking
- ✅ **Activity Logging** - Comprehensive logs of all operations
- ✅ **Human-in-the-Loop** - Approval workflow for sensitive actions
- ✅ **Configurable Rules** - Customize behavior via Company Handbook

### Silver Tier Features
- ✅ **Gmail Integration** - Automatic email monitoring and processing
- ✅ **LinkedIn Automation** - Official API posting with OAuth 2.0 token management and approval workflow
- ✅ **MCP Server Integration** - Gmail MCP server for external actions
- ✅ **Email Processing Workflow** - Mark as read, archive, reply, delete
- ✅ **Multi-Watcher System** - Simultaneous monitoring of multiple sources
- ✅ **Content Calendar** - Automated LinkedIn content planning and posting
- ✅ **Retry Logic** - Smart retry with exponential backoff for API failures
- ✅ **Edge Case Handling** - Comprehensive validation and error handling
- ✅ **Scheduled Tasks** - Cron/Task Scheduler integration for automation

### New Gold Tier Features
- ✅ **Twitter/X Integration** - Tweepy-based posting skill + mention watcher (HITL-gated)
- ✅ **Facebook + Instagram** - Meta Graph API v21.0 posting + comment watcher
- ✅ **Cross-Platform Content Calendar** - Unified JSON plan drives LI/TW/FB/IG scheduling
- ✅ **Odoo ERP Integration** - XML-RPC revenue/expense queries; draft invoice with HITL approval
- ✅ **Odoo MCP Server** - `odoo-mcp` npm server wired into `.mcp.json`
- ✅ **CEO Weekly Briefing** - Auto-generated Monday briefing with live Odoo financials
- ✅ **Multiple MCP Servers** - Gmail + filesystem + Odoo MCP servers active simultaneously
- ✅ **Ralph Wiggum Stop Hook** - Autonomous session continuation when `Needs_Action/` has pending items
- ✅ **Comprehensive Audit Logging** - Structured JSON audit trail for all external actions
- ✅ **Error Recovery Hardening** - Gmail MCP queuing, LinkedIn retry, vault lock + overflow sync, health check

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10 or higher
- Claude Code CLI installed
- Obsidian (optional, for visualization)
- Linux/Unix environment
- Gmail API credentials (for email features)
- LinkedIn account (for LinkedIn features)

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd personal_ai_employee

# Run setup (creates vault, installs dependencies, configures Obsidian)
./setup.sh

# Install additional Silver Tier dependencies
pip install -r requirements.txt
playwright install  # optional for legacy/manual browser workflows

# Configure environment variables
cp .env.example .env
# Edit .env with your Gmail and LinkedIn credentials

# Setup Gmail API credentials
# 1. Go to https://console.cloud.google.com/apis/credentials
# 2. Create OAuth 2.0 credentials
# 3. Download and save as credentials/gmail_credentials.json

# Setup LinkedIn API OAuth
python scripts/setup_linkedin_api.py
# Token saved to credentials/linkedin_api_token.json

# Setup Meta (Facebook + Instagram) API
python scripts/setup_meta_api.py
# Token saved to credentials/meta_api_token.json

# Setup scheduling (optional)
./scripts/setup_cron.sh  # Linux/Mac
# OR
powershell -ExecutionPolicy Bypass -File scripts/setup_task_scheduler.ps1  # Windows

# Start the system
./start.sh
```

That's it! The system is now monitoring for tasks and emails.

### Create Your First Task

1. Create a file `my_task.md`:
   ```markdown
   # Task: Generate Daily Summary

   ## Task Type
   Information Request

   ## Priority
   Medium

   ## Description
   Create a brief summary with:
   1. Today's date
   2. A motivational quote
   3. Three priorities for the day

   ## Expected Output
   Create daily_summary.md in Done folder

   ---
   *Created: 2026-03-28*
   *Status: Pending*
   ```

2. Drop it in the Inbox:
   ```bash
   cp my_task.md ai_employee_vault/Inbox/
   ```

3. Wait ~30 seconds and check results:
   ```bash
   ls ai_employee_vault/Done/
   ```

---

## 📁 Project Structure

```
personal_ai_employee/
├── setup.sh                    # One-time setup script
├── start.sh                    # Start the system
├── stop.sh                     # Stop the system
├── requirements.txt            # Python dependencies
├── START_HERE.md              # Getting started guide
│
├── .claude/
│   └── tools/
│       └── bronze_tier_skills.json  # Agent Skills manifest
│
├── src/
│   ├── watchers/
│   │   ├── gmail_watcher.py           # Gmail monitoring
│   │   ├── run_gmail_watcher.py       # Gmail watcher entry point
│   │   ├── content_calendar_watcher.py # Cross-platform calendar watcher
│   │   ├── twitter_watcher.py         # Twitter/X mention watcher
│   │   └── meta_watcher.py            # Facebook + Instagram comment watcher
│   │
│   └── orchestrator/
│       ├── watchdog.py                # Process monitor
│       ├── orchestrator.py            # Main orchestrator
│       ├── watcher_manager.py         # Multi-watcher management
│       ├── mcp_processor.py           # MCP action processor
│       └── skills/                    # Agent Skills
│           ├── base_skill.py          # Base class
│           ├── send_email.py          # Email sending
│           ├── process_email_actions.py
│           ├── post_linkedin.py       # LinkedIn posting
│           ├── post_twitter.py        # Twitter/X posting
│           ├── post_facebook.py       # Facebook posting
│           ├── post_instagram.py      # Instagram posting
│           ├── meta_api_client.py     # Meta Graph API client
│           ├── twitter_api_client.py  # Tweepy client
│           ├── linkedin_api_client.py # LinkedIn API client
│           ├── odoo_accounting.py     # Odoo ERP skill
│           ├── generate_ceo_briefing.py # CEO Weekly Briefing
│           ├── audit_logger.py        # Structured audit logging
│           ├── create_content_plan.py # Cross-platform content calendar
│           ├── gmail_retry_handler.py # Retry logic
│           ├── process_needs_action.py
│           ├── update_dashboard.py
│           ├── create_plan.py
│           ├── create_approval_request.py
│           ├── parse_watcher_file.py
│           ├── process_inbox.py
│           └── process_approved_actions.py
│
└── ai_employee_vault/          # Obsidian vault
    ├── Inbox/                  # Drop tasks here
    ├── Done/                   # Completed tasks
    ├── Needs_Action/           # Pending tasks
    ├── Plans/                  # Strategic plans
    ├── Pending_Approval/       # Awaiting approval
    ├── Approved/               # Approved tasks
    ├── Rejected/               # Rejected tasks
    ├── Briefings/              # CEO Weekly Briefings (auto-generated Mondays)
    ├── Content_Calendar/       # Cross-platform scheduled posts
    ├── Logs/                   # Activity logs + audit JSON
    ├── Dashboard.md            # System status
    ├── Company_Handbook.md     # Rules & guidelines
    └── README.md               # Vault guide
```

---

## 📖 Documentation

| Document | Description |
|----------|-------------|
| **[START_HERE.md](docs/START_HERE.md)** | Getting started guide |
| **[GOLD_TIER_PLAN.md](docs/GOLD_TIER_PLAN.md)** | Gold Tier implementation plan |
| **[SILVER_TIER_TESTING_GUIDE.md](docs/SILVER_TIER_TESTING_GUIDE.md)** | Silver Tier testing guide |
| **[SILVER_TIER_DEMO.md](docs/SILVER_TIER_DEMO.md)** | Complete demo results |
| **[EMAIL_WORKFLOW_GUIDE.md](docs/EMAIL_WORKFLOW_GUIDE.md)** | Email processing workflow |
| **[EMAIL_ACTIONS_GUIDE.md](docs/EMAIL_ACTIONS_GUIDE.md)** | Email actions quick reference |
| **[LINKEDIN_SETUP_QUICK_REF.md](docs/LINKEDIN_SETUP_QUICK_REF.md)** | LinkedIn OAuth/API setup quick reference |
| **[LINKEDIN_WATCHER_GUIDE.md](docs/LINKEDIN_WATCHER_GUIDE.md)** | LinkedIn watcher guide |
| **[BRONZE_TIER_DOCS.md](docs/BRONZE_TIER_DOCS.md)** | Bronze Tier technical docs |
| **[QUICK_REFERENCE.md](docs/QUICK_REFERENCE.md)** | System quick reference |
| **[AGENT_SKILLS_QUICK_REFERENCE.md](docs/AGENT_SKILLS_QUICK_REFERENCE.md)** | Agent Skills guide |
| **[AGENT_SKILLS_DOCUMENTATION.md](docs/AGENT_SKILLS_DOCUMENTATION.md)** | Skills technical docs |
| **[CLAUDE.md](CLAUDE.md)** | Claude Code configuration |
| **[TESTING.md](docs/TESTING.md)** | Test scenarios |

---

## 🎨 Obsidian Integration

The system includes a pre-configured Obsidian vault for visual task management.

### Opening the Vault

```bash
# Command line
obsidian ai_employee_vault/

# Or manually in Obsidian:
# File → Open folder as vault → Select ai_employee_vault
```

### Features

- 📊 **Dashboard** - Real-time system status
- 📁 **File Explorer** - Navigate all folders
- 🔗 **Graph View** - Visualize task relationships
- 🔍 **Search** - Find tasks quickly
- 📝 **Templates** - Quick task creation

---

## 🔧 Configuration

### Company Handbook

Edit `ai_employee_vault/Company_Handbook.md` to customize:

- Human-in-the-loop approval rules
- File processing guidelines
- Communication templates
- Security policies
- Decision matrix

### System Settings

Edit `src/orchestrator/orchestrator.py` to adjust:

- Check interval (default: 30 seconds)
- Timeout duration (default: 5 minutes)
- Monitored folders

---

## 📊 System Workflow

```
User drops task file in Inbox
         ↓
Orchestrator detects file (every 30s)
         ↓
Creates instruction for Claude Code
         ↓
Claude Code processes task
         ↓
Creates output files in Done
         ↓
Updates Dashboard & logs
         ↓
Moves original to Done with timestamp
```

---

## 🛠️ Common Commands

```bash
# Start system with live logs
./start.sh

# Stop system
./stop.sh

# Check if running
ps aux | grep -E "watchdog|orchestrator|watcher"

# Start watcher manager (Silver Tier)
python watcher_manager.py ./ai_employee_vault start

# Check watcher status
python watcher_manager.py ./ai_employee_vault status

# Stop watchers
python watcher_manager.py ./ai_employee_vault stop

# Run MCP processor manually
python src/orchestrator/mcp_processor.py ./ai_employee_vault

# Run health check
python scripts/health_check.py

# Generate CEO briefing manually
python src/orchestrator/skills/generate_ceo_briefing.py ./ai_employee_vault

# View live logs
tail -f ai_employee_vault/Logs/orchestrator_$(date +%Y-%m-%d).log
tail -f ai_employee_vault/Logs/gmail_watcher_$(date +%Y-%m-%d).log
tail -f ai_employee_vault/Logs/mcp_processor_$(date +%Y-%m-%d).log

# View audit log
cat ai_employee_vault/Logs/audit_master.json | python -m json.tool | tail -50

# Check Dashboard
cat ai_employee_vault/Dashboard.md

# Open in Obsidian
obsidian ai_employee_vault/
```

---

## 🐛 Troubleshooting

### System not processing files?

```bash
# Check if running
ps aux | grep orchestrator

# Check logs
tail -20 ai_employee_vault/Logs/orchestrator_$(date +%Y-%m-%d).log

# Restart
./stop.sh && ./start.sh
```

### Files stuck in Inbox?

```bash
# Remove processing lock
rm ai_employee_vault/.state/processing.lock

# Restart system
./stop.sh && ./start.sh
```

See [BRONZE_TIER_DOCS.md](docs/BRONZE_TIER_DOCS.md) for complete troubleshooting guide.

---

## 📈 Performance

| Metric | Value |
|--------|-------|
| Detection latency | < 30 seconds |
| Simple task processing | 10-30 seconds |
| Complex task processing | 30-120 seconds |
| Memory usage | ~50-200 MB |
| CPU usage | < 30% |

---

## 🗺️ Roadmap

### ✅ Bronze Tier (Complete)
- File-based task processing
- Claude Code integration
- Obsidian vault
- Dashboard and logging
- Human-in-the-loop approval
- Agent Skills framework

### ✅ Silver Tier (Complete)
- Gmail integration with MCP server
- LinkedIn API posting and calendar-driven automation
- Email processing workflow (mark read, archive, reply, delete)
- Multi-watcher system
- Content calendar automation
- Retry logic and edge case handling
- Scheduled task execution

### ✅ Gold Tier (Complete)
- Twitter/X watcher + HITL posting skill
- Facebook + Instagram via Meta Graph API
- Cross-platform content calendar (LI/TW/FB/IG)
- Odoo Community ERP — revenue/expense queries + draft invoice HITL
- Odoo MCP server integration
- CEO Weekly Briefing with live financial data
- Multiple MCP servers (Gmail + filesystem + Odoo)
- Ralph Wiggum autonomous stop hook
- Comprehensive structured audit logging
- Error recovery hardening + health check utility

---

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Test thoroughly
4. Submit a pull request

---

## 📝 License

[Your License Here]

---

## 🙏 Acknowledgments

- **Claude Code** by Anthropic
- **Obsidian** by Obsidian.md
- **Python watchdog** library
- **psutil** library

---

## 📞 Support

- 📖 **Documentation**: See [BRONZE_TIER_DOCS.md](docs/BRONZE_TIER_DOCS.md)
- 🐛 **Issues**: Check logs first, then GitHub issues
- 💬 **Discussions**: GitHub Discussions

---

## 🎓 Learning Resources

This project demonstrates:
- AI-powered automation
- File system monitoring
- Process orchestration
- Obsidian vault management
- Claude Code integration
- Human-in-the-loop workflows

Perfect for learning about AI-native development and personal automation systems.

---

**Personal AI Employee** | Gold Tier v3.0 | Production Ready | 2026-04-25
