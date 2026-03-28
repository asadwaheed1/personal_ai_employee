# Bronze Tier - Quick Reference Guide

**Version:** 1.0 | **Last Updated:** 2026-03-28

---

## Quick Start

```bash
# Setup (first time only)
./setup.sh

# Start system
./start.sh

# Stop system
./stop.sh
```

---

## Common Commands

### System Management
```bash
# Check if system is running
ps aux | grep -E "watchdog|orchestrator"

# View live logs
tail -f ai_employee_vault/Logs/orchestrator_$(date +%Y-%m-%d).log

# Restart system
./stop.sh && sleep 2 && ./start.sh
```

### Task Management
```bash
# Create a task
cp my_task.md ai_employee_vault/Inbox/

# Check processing status
ls -la ai_employee_vault/Inbox/
ls -la ai_employee_vault/Done/

# View Dashboard
cat ai_employee_vault/Dashboard.md
```

### Obsidian
```bash
# Open vault
obsidian ai_employee_vault/

# Or manually: Open Obsidian → Open folder as vault → Select ai_employee_vault
```

---

## Task Template

```markdown
# Task: [Task Name]

## Task Type
[Information Request / Action / Report / etc.]

## Priority
[High / Medium / Low]

## Description
[What needs to be done]

## Expected Output
[What you expect as result]

## Notes
[Additional context]

---
*Created: YYYY-MM-DD*
*Status: Pending*
```

---

## Folder Structure

| Folder | Purpose |
|--------|---------|
| **Inbox** | Drop new tasks here |
| **Needs_Action** | Tasks requiring processing |
| **Done** | Completed tasks and outputs |
| **Plans** | Strategic plans |
| **Pending_Approval** | Awaiting human approval |
| **Approved** | Approved for execution |
| **Rejected** | Rejected tasks |
| **Logs** | System activity logs |

---

## Workflow

1. **Create task** → Drop `.md` file in Inbox
2. **Wait ~30 seconds** → System detects and processes
3. **Check results** → Look in Done folder
4. **Review activity** → Check Dashboard.md

---

## Troubleshooting

### System not processing files?
```bash
# Check if running
ps aux | grep orchestrator

# Check logs for errors
tail -20 ai_employee_vault/Logs/orchestrator_$(date +%Y-%m-%d).log

# Restart system
./stop.sh && ./start.sh
```

### Files stuck in Inbox?
```bash
# Check processing lock
ls -la ai_employee_vault/.state/processing.lock

# Remove if stuck
rm ai_employee_vault/.state/processing.lock

# Restart
./stop.sh && ./start.sh
```

### Claude Code errors?
```bash
# Test Claude manually
cd ai_employee_vault
claude "Read Dashboard.md"

# Check Claude version
claude --version
```

---

## Key Files

| File | Purpose |
|------|---------|
| `Dashboard.md` | System status and activity |
| `Company_Handbook.md` | Rules and guidelines |
| `README.md` | Vault usage guide |
| `.claude_instruction.md` | Temporary instruction files |

---

## Configuration

### Change check interval
Edit `src/orchestrator/orchestrator.py`:
```python
check_interval = 30  # Change to desired seconds
```

### Modify rules
Edit `ai_employee_vault/Company_Handbook.md`

### Adjust timeout
Edit `src/orchestrator/orchestrator.py`:
```python
timeout=300  # Change to desired seconds
```

---

## Monitoring

### Dashboard Metrics
- System Status (🟢 Operational / 🔴 Error)
- Pending Actions count
- Recent Activity log
- Statistics (processed, queued, failed)

### Log Files
- `orchestrator_YYYY-MM-DD.log` - Processing logs
- `watchdog_YYYY-MM-DD.log` - System health logs
- `activity_YYYY-MM-DD.md` - Human-readable activity

---

## Best Practices

✅ **Do:**
- Use descriptive task names
- Include clear expected outputs
- Review Dashboard regularly
- Archive old logs monthly
- Backup vault weekly

❌ **Don't:**
- Drop non-.md files in Inbox
- Modify files while processing
- Store sensitive data in vault
- Run multiple instances
- Delete .state directory

---

## Performance

| Metric | Typical Value |
|--------|---------------|
| Detection latency | < 30 seconds |
| Simple task | 10-30 seconds |
| Complex task | 30-120 seconds |
| Memory usage | ~50-200 MB |
| CPU usage | < 30% |

---

## Support

📖 **Full Documentation:** `BRONZE_TIER_DOCS.md`
🐛 **Issues:** Check logs first, then GitHub issues
💡 **Tips:** See README.md in vault

---

## Quick Checks

```bash
# Is system healthy?
ps aux | grep -E "watchdog|orchestrator" | wc -l
# Should return 2 or more

# Any files waiting?
ls ai_employee_vault/Inbox/ | wc -l

# Recent activity?
tail -5 ai_employee_vault/Logs/orchestrator_$(date +%Y-%m-%d).log

# System uptime?
ps -p $(pgrep -f watchdog.py) -o etime=
```

---

**Bronze Tier v1.0** | Production Ready | 2026-03-28
