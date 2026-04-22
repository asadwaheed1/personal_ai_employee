# Personal AI Employee

An intelligent automation system that processes tasks, manages workflows, and integrates with Obsidian for visual task management. Built with Claude Code and designed for personal productivity and business automation.

![Status](https://img.shields.io/badge/status-production%20ready-brightgreen)
![Version](https://img.shields.io/badge/version-1.0%20(Bronze%20Tier)-blue)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)

---

## 🎯 Overview

The Personal AI Employee is a three-tier automation system designed to handle personal and business tasks with increasing levels of sophistication:

- **Bronze Tier** (Current): File-based task processing with Obsidian integration
- **Silver Tier** (Planned): Email and calendar integration
- **Gold Tier** (Planned): Advanced automation with external APIs

---

## ✨ Features (Bronze Tier)

- ✅ **Automated Task Processing** - Drop markdown files, get results automatically
- ✅ **Claude Code Integration** - Intelligent task execution with AI reasoning
- ✅ **Agent Skills Framework** - All AI functionality implemented as modular Agent Skills
- ✅ **Obsidian Vault** - Visual task management and monitoring
- ✅ **Real-time Dashboard** - Live system status and activity tracking
- ✅ **Activity Logging** - Comprehensive logs of all operations
- ✅ **Human-in-the-Loop** - Approval workflow for sensitive actions
- ✅ **Configurable Rules** - Customize behavior via Company Handbook
- ✅ **Live Monitoring** - Real-time log display when running

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10 or higher
- Claude Code CLI installed
- Obsidian (optional, for visualization)
- Linux/Unix environment

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd personal_ai_employee

# Run setup (creates vault, installs dependencies, configures Obsidian)
./setup.sh

# Start the system
./start.sh
```

That's it! The system is now monitoring for tasks.

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
│   └── orchestrator/
│       ├── watchdog.py         # Process monitor
│       ├── orchestrator.py     # Main orchestrator
│       └── skills/             # Agent Skills
│           ├── base_skill.py   # Base class
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
    ├── Logs/                   # Activity logs
    ├── Dashboard.md            # System status
    ├── Company_Handbook.md     # Rules & guidelines
    └── README.md               # Vault guide
```

---

## 📖 Documentation

| Document | Description |
|----------|-------------|
| **[START_HERE.md](START_HERE.md)** | Getting started guide |
| **[BRONZE_TIER_DOCS.md](BRONZE_TIER_DOCS.md)** | Complete technical documentation |
| **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** | System quick reference |
| **[AGENT_SKILLS_QUICK_REFERENCE.md](AGENT_SKILLS_QUICK_REFERENCE.md)** | Agent Skills guide |
| **[AGENT_SKILLS_DOCUMENTATION.md](AGENT_SKILLS_DOCUMENTATION.md)** | Skills technical docs |
| **[CLAUDE.md](CLAUDE.md)** | Claude Code configuration |
| **[TESTING.md](TESTING.md)** | Test scenarios |

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
ps aux | grep -E "watchdog|orchestrator"

# View live logs
tail -f ai_employee_vault/Logs/orchestrator_$(date +%Y-%m-%d).log

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

See [BRONZE_TIER_DOCS.md](BRONZE_TIER_DOCS.md) for complete troubleshooting guide.

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

### 🚧 Silver Tier (Planned)
- Gmail integration
- Calendar sync
- WhatsApp monitoring
- Automated email responses
- Advanced task templates

### 🔮 Gold Tier (Future)
- External API integrations
- Multi-user support
- Advanced analytics
- Custom workflows
- Mobile app

---

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Test thoroughly
4. Submit a pull request

---

## 📝 License

This project is licensed under the GPL License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Claude Code** by Anthropic
- **Obsidian** by Obsidian.md
- **Python watchdog** library
- **psutil** library

---

## 📞 Support

- 📖 **Documentation**: See [BRONZE_TIER_DOCS.md](BRONZE_TIER_DOCS.md)
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

**Personal AI Employee** | Bronze Tier v1.0 | Production Ready | 2026-03-28
