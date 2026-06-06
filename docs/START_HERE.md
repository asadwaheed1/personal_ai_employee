# Personal AI Employee — Gold Tier v3.0

Production-ready AI employee: email, LinkedIn, Twitter/X, Facebook, Instagram, Odoo ERP, CEO briefings, HITL approvals, autonomous operation.

## What You Have

All three tiers complete:

| Tier | Capabilities |
|------|-------------|
| **Bronze** | File-based task processing, Obsidian vault, dashboard, HITL approval workflow |
| **Silver** | Gmail + LinkedIn automation, MCP servers, content calendar, retry logic, cron scheduling |
| **Gold** | Twitter/X, Facebook, Instagram, Odoo ERP, CEO briefings, cross-platform calendar, audit logging, autonomous stop hook |

## 5-Minute Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Setup vault + cron
./setup.sh
./scripts/setup_cron.sh

# 3. Configure credentials
cp .env.example .env
# Edit .env — add Gmail, LinkedIn, Twitter, Meta, Odoo credentials

# 4. Authenticate APIs
python scripts/setup_linkedin_api.py     # LinkedIn OAuth
python scripts/setup_meta_api.py         # Facebook + Instagram tokens

# 5. Start the system
./start.sh

# 6. Verify health
python scripts/health_check.py
```

## What Happens When You Start

1. **Watcher Manager** launches Gmail watcher + content calendar watcher
2. **Orchestrator** polls vault folders every 30s
3. **Gmail Watcher** monitors inbox → creates `Needs_Action/EMAIL_*.md`
4. **Content Calendar Watcher** monitors scheduled posts → routes to social skills
5. **Ralph Wiggum Hook** keeps Claude running while `Needs_Action/` has pending items
6. **Monday 7 AM cron** generates CEO Weekly Briefing with live Odoo financials

## Vault Structure

```
ai_employee_vault/
├── Inbox/              ← Drop tasks here
├── Needs_Action/       ← Active processing queue
├── Pending_Approval/   ← HITL gate (review here)
├── Approved/           ← Move here to authorize
├── Rejected/           ← Rejected actions
├── Done/               ← Completed tasks
├── Plans/              ← Strategic plans
├── Briefings/          ← CEO Weekly Briefings (auto Mon 7 AM)
├── Content_Calendar/   ← Cross-platform scheduled posts
├── Logs/               ← Orchestrator + audit JSON logs
└── Dashboard.md        ← Live system status
```

## Key Scripts

```bash
# System control
./start.sh                                          # Start everything
./stop.sh                                           # Stop everything
python scripts/health_check.py                      # API health + dashboard update

# Content
python src/orchestrator/skills/create_content_plan.py   # Generate cross-platform calendar
python src/orchestrator/skills/generate_ceo_briefing.py ./ai_employee_vault  # Manual briefing

# Watchers (manual)
python src/watchers/twitter_watcher.py ./ai_employee_vault   # Poll Twitter mentions
python src/watchers/meta_watcher.py ./ai_employee_vault      # Poll FB/IG comments

# Audit
cat ai_employee_vault/Logs/audit_master.json | python -m json.tool | tail -50

# MCP processor (manual)
python src/orchestrator/mcp_processor.py ./ai_employee_vault

# Logs
tail -f ai_employee_vault/Logs/orchestrator_$(date +%Y-%m-%d).log
```

## Quick Navigation

| Goal | Document |
|------|----------|
| Full setup walkthrough | [QUICKSTART.md](QUICKSTART.md) |
| Gold Tier task breakdown | [GOLD_TIER_PLAN.md](GOLD_TIER_PLAN.md) |
| Silver Tier testing | [SILVER_TIER_TESTING_GUIDE.md](SILVER_TIER_TESTING_GUIDE.md) |
| Email workflow | [EMAIL_WORKFLOW_GUIDE.md](EMAIL_WORKFLOW_GUIDE.md) |
| LinkedIn setup | [LINKEDIN_SETUP_QUICK_REF.md](LINKEDIN_SETUP_QUICK_REF.md) |
| Agent Skills reference | [AGENT_SKILLS_QUICK_REFERENCE.md](AGENT_SKILLS_QUICK_REFERENCE.md) |
| Bronze architecture | [BRONZE_TIER_DOCS.md](BRONZE_TIER_DOCS.md) |
| Test scenarios | [TESTING.md](TESTING.md) |

## HITL Approval Flow

Sensitive actions (invoice creation, social posts, email replies) require human approval:

1. Skill writes approval request → `Pending_Approval/`
2. Review the file, edit if needed
3. Move to `Approved/` → orchestrator executes
4. Result archived to `Done/`

## Social Posting

Post immediately or via content calendar:

```bash
# Create a cross-platform content plan (LI + TW + FB + IG)
python src/orchestrator/skills/create_content_plan.py

# Files land in Content_Calendar/ — calendar watcher picks them up at scheduled time
# Each platform post goes through HITL approval before publishing
```

## Odoo ERP

Odoo Community 17 runs via Docker:

```bash
cd docker && docker-compose up -d   # Start Odoo on port 8069
# CEO Briefing auto-pulls revenue + expenses via XML-RPC
# Draft invoices created via HITL approval flow
```

## Autonomous Mode (Ralph Wiggum)

```bash
./scripts/start_ralph_wiggum.sh     # Start autonomous processing session
# Stop hook keeps Claude running while Needs_Action/ has pending items
# Max iterations controlled by MAX_ITERATIONS in .env
```

## Status

✅ **Bronze Tier**: Complete  
✅ **Silver Tier**: Complete  
✅ **Gold Tier**: Complete  

**Version**: 3.0-gold | **Date**: 2026-04-25
