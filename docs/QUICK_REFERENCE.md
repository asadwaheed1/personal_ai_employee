# Personal AI Employee — Quick Reference

**Version:** 3.0-gold | **Last Updated:** 2026-04-25

---

## System Control

```bash
./start.sh                          # Start everything
./stop.sh                           # Stop everything
python scripts/health_check.py      # API health + dashboard update
ps aux | grep -E "watchdog|orchestrator|watcher"  # Check running
```

---

## Vault Folders

| Folder | Purpose |
|--------|---------|
| **Inbox** | Drop tasks here |
| **Needs_Action** | Active processing queue |
| **Pending_Approval** | HITL gate — review here |
| **Approved** | Move here to authorize execution |
| **Rejected** | Rejected actions |
| **Done** | Completed tasks + executed actions |
| **Plans** | Strategic plans |
| **Briefings** | CEO Weekly Briefings (auto Mon 7 AM) |
| **Content_Calendar** | Cross-platform scheduled posts |
| **Logs** | Orchestrator + audit JSON |

---

## Common Commands

### Email
```bash
# View unprocessed emails
ls ai_employee_vault/Needs_Action/EMAIL_*.md

# Run MCP processor manually
python src/orchestrator/mcp_processor.py ./ai_employee_vault

# View MCP processor logs
tail -f ai_employee_vault/Logs/mcp_processor_$(date +%Y-%m-%d).log
```

### Social Media
```bash
# Generate cross-platform content calendar (LI + TW + FB + IG)
python src/orchestrator/skills/create_content_plan.py

# View scheduled posts
ls ai_employee_vault/Content_Calendar/

# Poll Twitter mentions manually
python src/watchers/twitter_watcher.py ./ai_employee_vault

# Poll FB/IG comments manually
python src/watchers/meta_watcher.py ./ai_employee_vault
```

### Odoo ERP
```bash
# Start Odoo Docker stack
cd docker && docker-compose up -d

# Stop Odoo
cd docker && docker-compose down

# Odoo UI (browser)
# http://localhost:8069 — admin / admin
```

### CEO Briefing
```bash
# Generate briefing manually (writes to Briefings/)
python src/orchestrator/skills/generate_ceo_briefing.py ./ai_employee_vault

# View latest briefing
ls -t ai_employee_vault/Briefings/ | head -1 | xargs -I{} cat ai_employee_vault/Briefings/{}
```

### Audit Log
```bash
# View last 20 audit entries
cat ai_employee_vault/Logs/audit_master.json | python -m json.tool | tail -80

# Count actions by platform
grep -o '"platform": "[^"]*"' ai_employee_vault/Logs/audit_master.json | sort | uniq -c
```

### Logs
```bash
tail -f ai_employee_vault/Logs/orchestrator_$(date +%Y-%m-%d).log
tail -f ai_employee_vault/Logs/gmail_watcher_$(date +%Y-%m-%d).log
tail -f ai_employee_vault/Logs/watcher_manager_$(date +%Y-%m-%d).log
cat ai_employee_vault/Dashboard.md
```

---

## HITL Approval Flow

```
Skill creates approval request → Pending_Approval/
Review + edit if needed
Move to Approved/ → orchestrator executes
Result archived to Done/
```

```bash
# Approve a pending item
mv ai_employee_vault/Pending_Approval/ITEM_*.md ai_employee_vault/Approved/

# Reject
mv ai_employee_vault/Pending_Approval/ITEM_*.md ai_employee_vault/Rejected/
```

---

## Social Posting (Manual)

```bash
# LinkedIn
python -m src.orchestrator.skills.post_linkedin '{"action": "create_post", "content": "Your post text"}'

# Twitter/X
python -m src.orchestrator.skills.post_twitter '{"action": "create_post", "content": "Your tweet text"}'

# Facebook
python -m src.orchestrator.skills.post_facebook '{"action": "create_post", "content": "Your post text"}'

# Instagram (needs public image URL)
python -m src.orchestrator.skills.post_instagram '{"action": "create_post", "caption": "Caption", "image_url": "https://..."}'
```

All generate approval request in `Pending_Approval/` — move to `Approved/` to publish.

---

## Watcher Manager

```bash
python src/orchestrator/watcher_manager.py ./ai_employee_vault start
python src/orchestrator/watcher_manager.py ./ai_employee_vault stop
python src/orchestrator/watcher_manager.py ./ai_employee_vault status
```

---

## Autonomous Mode (Ralph Wiggum)

```bash
./scripts/start_ralph_wiggum.sh     # Start autonomous processing
# Keeps Claude running while Needs_Action/ has pending items
# MAX_ITERATIONS controlled in .env
```

---

## Credential Setup

```bash
python scripts/setup_linkedin_api.py    # LinkedIn OAuth
python scripts/setup_meta_api.py        # Facebook + Instagram
# Twitter: set keys in .env directly (no setup script needed)
# Odoo: credentials in .env + docker/.env
```

---

## Scheduling

```bash
./scripts/setup_cron.sh     # Install all cron jobs
crontab -l                  # View active jobs
# Cron schedule:
# */30 * * * *  orchestrator check
# 0 7 * * 1    CEO Weekly Briefing (Monday 7 AM)
```

---

## Troubleshooting

### Files stuck in Inbox
```bash
rm ai_employee_vault/.state/processing.lock
./stop.sh && ./start.sh
```

### Gmail MCP auth failure
```bash
python scripts/health_check.py
# If failed: re-authorize via Claude Code MCP session
```

### LinkedIn token expired
```bash
python scripts/setup_linkedin_api.py
```

### Meta token expired
```bash
python scripts/setup_meta_api.py
```

### Odoo connection failed
```bash
cd docker && docker-compose ps
cd docker && docker-compose up -d
```

### Orphan processes
```bash
pkill -f "mcp_processor|gmail_watcher|watcher_manager"
./start.sh
```

---

## Key Files

| File | Purpose |
|------|---------|
| `Dashboard.md` | Live system status |
| `Company_Handbook.md` | Rules and guidelines |
| `.mcp.json` | MCP server config (Gmail + filesystem + Odoo) |
| `.env` | All API credentials |
| `credentials/linkedin_api_token.json` | LinkedIn OAuth token |
| `credentials/meta_api_token.json` | Facebook + Instagram token |
| `Logs/audit_master.json` | Consolidated audit trail |

---

**Gold Tier v3.0** | Production Ready | 2026-04-25
