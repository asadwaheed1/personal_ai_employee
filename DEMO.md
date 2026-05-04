# Gold Tier Demo Guide

**Branch:** `gold-imp` | **Date:** 2026-04-30  
**Prereq:** `.env` filled, `venv` active, `./setup.sh` already run.

> **All commands are self-contained** — each block `cd`s to project root via subshell. Run from any directory.

Gold Tier requirements (from `docs/requirements.md`):
- Full cross-domain integration (Personal + Business)
- Odoo Community accounting via MCP / XML-RPC
- Facebook + Instagram posting + activity summary
- Twitter/X posting + summary
- Multiple MCP servers
- Weekly Business + Accounting Audit → CEO Briefing
- Error recovery and graceful degradation
- Comprehensive audit logging
- Ralph Wiggum loop (autonomous multi-step task completion)
- Architecture documentation

---

## 0. Start the System

```bash
(cd ~/piaic/projects/personal_ai_employee && ./start.sh)
```

Watch for:
```
✅ Startup preflight passed: Gmail MCP authentication healthy
```

All 5 watchers start: filesystem, Gmail, LinkedIn, Twitter, Meta, content_calendar.

**Stop:**
```bash
(cd ~/piaic/projects/personal_ai_employee && ./stop.sh)
```

---

## 1. Facebook + Instagram Posting (Meta API)

**Requirement:** "Integrate Facebook and Instagram and post messages and generate summary"

**What it shows:** `meta_api_client.py` calls Meta Graph API v21.0 → posts to FB Page + IG Business account → audit entry written.

### Facebook

```bash
(cd ~/piaic/projects/personal_ai_employee && venv/bin/python -c "
from src.orchestrator.skills.post_facebook import PostFacebookSkill
skill = PostFacebookSkill('ai_employee_vault')
result = skill.execute({
    'content': 'Gold Tier demo — AI Employee live on Facebook. #AIEmployee #PIAIC',
    'require_approval': False
})
print(result)
")
```

### Instagram

```bash
(cd ~/piaic/projects/personal_ai_employee && venv/bin/python -c "
from src.orchestrator.skills.post_instagram import PostInstagramSkill
skill = PostInstagramSkill('ai_employee_vault')
result = skill.execute({
    'content': 'Gold Tier demo — AI Employee live on Instagram! #AIEmployee',
    'image_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/2/2f/Culinary_fruits_front_view.jpg/1200px-Culinary_fruits_front_view.jpg',
    'require_approval': False
})
print(result)
")
```

> **Note:** Instagram requires a direct non-redirecting image URL (no URL shorteners, no picsum.photos redirects). Use a direct CDN URL or a publicly hosted image.

**Confirmed live post IDs (2026-04-26):**
- Facebook: `698457253346943_122171523488861671`
- Instagram: `18104942089822106`

**Summary:** `meta_watcher.py` polls FB/IG comments every cycle → writes `Needs_Action/META_ACTIVITY_*.md` with engagement metrics.

---

## 2. Twitter/X Integration

**Requirement:** "Integrate Twitter (X) and post messages and generate summary"

Twitter code complete (`post_twitter.py`, `twitter_watcher.py`). Free API tier blocks `/2/tweets` (402). Show auth + code:

```bash
(cd ~/piaic/projects/personal_ai_employee && venv/bin/python -c "
from src.orchestrator.skills.twitter_api_client import TwitterAPIClient
import os; from dotenv import load_dotenv; load_dotenv()
client = TwitterAPIClient(
    os.getenv('TWITTER_API_KEY'), os.getenv('TWITTER_API_SECRET'),
    os.getenv('TWITTER_ACCESS_TOKEN'), os.getenv('TWITTER_ACCESS_SECRET'),
    os.getenv('TWITTER_BEARER_TOKEN')
)
print('Auth OK:', client.verify_credentials())
")
```

Show skill files exist:
```bash
ls ~/piaic/projects/personal_ai_employee/src/orchestrator/skills/post_twitter.py \
   ~/piaic/projects/personal_ai_employee/src/orchestrator/skills/twitter_api_client.py \
   ~/piaic/projects/personal_ai_employee/src/watchers/twitter_watcher.py
```

`twitter_watcher.py` polls mentions every 15m → writes `Needs_Action/TWITTER_MENTION_*.md` with metrics. Excluded from content calendar (free API blocked at tweet endpoint).

---

## 3. Cross-Platform Content Calendar (Gemini AI)

**Requirement:** "Full cross-domain integration" — AI generates platform-specific content across all channels.

**What it shows:** Single skill call → `gemini-2.0-flash-preview` generates distinct copy per platform (LinkedIn = first-person technical, Facebook = casual/warm, Instagram = lifestyle/visual + image prompt).

```bash
(cd ~/piaic/projects/personal_ai_employee && venv/bin/python -c "
from src.orchestrator.skills.create_content_plan import CreateContentPlanSkill
skill = CreateContentPlanSkill('ai_employee_vault')
result = skill.execute({
    'num_posts': 2,
    'platforms': ['linkedin', 'facebook', 'instagram'],
    'week_start': '2026-05-05'
})
print(result)
")
```

View generated calendar:
```bash
cat ~/piaic/projects/personal_ai_employee/ai_employee_vault/Content_Calendar/CALENDAR_2026-W19.md
```

`content_calendar_watcher.py` monitors this file → auto-routes approved posts to `PostLinkedInSkill`, `PostFacebookSkill`, `PostInstagramSkill` at scheduled time.

---

## 4. CEO Weekly Briefing + Business Audit

**Requirement:** "Weekly Business and Accounting Audit with CEO Briefing generation"

**What it shows:** `generate_ceo_briefing.py` scans Done/ (7 days) + audit logs + Content_Calendar + Pending_Approval + Odoo financials → writes structured executive briefing with anomaly detection.

```bash
(cd ~/piaic/projects/personal_ai_employee && venv/bin/python -c "
from src.orchestrator.skills.generate_ceo_briefing import GenerateCEOBriefingSkill
skill = GenerateCEOBriefingSkill('ai_employee_vault')
result = skill.execute({'date': '2026-04-30'})
print(result)
")
```

```bash
cat ~/piaic/projects/personal_ai_employee/ai_employee_vault/Briefings/2026-04-30_Monday_Briefing.md
```

**Sections to highlight:**
- Executive Summary (7-day task stats)
- Social Media Activity (LI/FB/IG posts, engagement)
- Pending Items + anomaly flags (backlog >20, approval queue >5)
- **Odoo Financial Summary** (revenue, expenses, net) ← Gold-specific
- Next Week Preparation

Cron fires this every Monday at 7 AM:
```bash
crontab -l | grep briefing
```

---

## 5. Odoo Accounting Integration (MCP)

**Requirement:** "Create an accounting system in Odoo Community and integrate via MCP server using Odoo's JSON-RPC APIs"

**Prereq: Start Odoo Docker:**

```bash
docker compose -f ~/piaic/projects/personal_ai_employee/docker/docker-compose.yml up -d
```
Wait ~30s. Odoo runs on port 8069. Check `.mcp.json` — 3 MCP servers: `gmail`, `filesystem`, `odoo`.

### Revenue Summary (XML-RPC read)

```bash
(cd ~/piaic/projects/personal_ai_employee && venv/bin/python -c "
from src.orchestrator.skills.odoo_accounting import OdooAccountingSkill
skill = OdooAccountingSkill('ai_employee_vault')
result = skill.execute({
    'action': 'revenue_summary',
    'date_from': '2026-04-01',
    'date_to': '2026-04-30'
})
print(result)
")
```

Live test returned: 4 invoices totaling \$143,175 for April 2026.

### Expense Summary

```bash
(cd ~/piaic/projects/personal_ai_employee && venv/bin/python -c "
from src.orchestrator.skills.odoo_accounting import OdooAccountingSkill
skill = OdooAccountingSkill('ai_employee_vault')
result = skill.execute({
    'action': 'expense_summary',
    'date_from': '2026-04-01',
    'date_to': '2026-04-30'
})
print(result)
")
```

### Draft Invoice (HITL-gated — never auto-posts)

```bash
(cd ~/piaic/projects/personal_ai_employee && venv/bin/python -c "
from src.orchestrator.skills.odoo_accounting import OdooAccountingSkill
skill = OdooAccountingSkill('ai_employee_vault')
result = skill.execute({
    'action': 'create_draft_invoice',
    'partner_name': 'Demo Client',
    'amount': 5000,
    'description': 'Gold Tier consulting — demo invoice'
})
print(result)
")
```

Show: `Pending_Approval/ODOO_INVOICE_*.json` created. Draft only in Odoo — no posting until human approves.

### Multiple MCP Servers

```bash
cat ~/piaic/projects/personal_ai_employee/.mcp.json
```

Shows: `gmail-mcp-server`, `@modelcontextprotocol/server-filesystem`, `odoo-mcp` — all 3 active.

---

## 6. Comprehensive Audit Logging

**Requirement:** "Comprehensive audit logging"

Every external action (FB post, IG post, LI post, Odoo call) → structured JSON entry.

```bash
ls -lt ~/piaic/projects/personal_ai_employee/ai_employee_vault/Logs/audit_*.json | head -3
python3 -m json.tool ~/piaic/projects/personal_ai_employee/ai_employee_vault/Logs/audit_master.json | head -80
```

Fields: `timestamp`, `skill`, `action`, `platform`, `result`, `external_id`. Master log keeps last 1000 entries.

---

## 7. Error Recovery and Graceful Degradation

**Requirement:** "Error recovery and graceful degradation"

**What to show:**

- **Transient Gmail MCP failure** → action renamed `QUEUED_MCP_GMAIL_*.json`, retried next cycle automatically.
- **LinkedIn API transient error** → skill returns `status: retry`, orchestrator leaves file in `Approved/` instead of archiving to `Done/` — retried next pass.
- **Vault lock contention** → overflow logged to `/tmp/vault_overflow/`, synced back when lock releases.
- **Health check** updates Dashboard with live API status:

```bash
(cd ~/piaic/projects/personal_ai_employee && venv/bin/python scripts/health_check.py ai_employee_vault)
```

```bash
grep -A 10 "Health" ~/piaic/projects/personal_ai_employee/ai_employee_vault/Dashboard.md
```

---

## 8. Ralph Wiggum Loop (Autonomous Multi-Step)

**Requirement:** "Ralph Wiggum loop for autonomous multi-step task completion"

**How it works:** Stop hook in `.claude/hooks/stop.sh` — when `/tmp/ralph_wiggum` session file exists, intercepts Claude's exit → checks if `Needs_Action/` still has pending files → re-injects continuation prompt → loops until done or MAX_ITERATIONS reached.

```bash
# Show hook wired up
cat ~/piaic/projects/personal_ai_employee/.claude/settings.json | python3 -m json.tool | grep -A5 Stop

# Show hook script
cat ~/piaic/projects/personal_ai_employee/.claude/hooks/stop.sh

# Start a Ralph loop session
bash ~/piaic/projects/personal_ai_employee/scripts/start_ralph_wiggum.sh
```

Hook exits silently (no session file). Activate:
```bash
touch /tmp/ralph_wiggum
ls ~/piaic/projects/personal_ai_employee/ai_employee_vault/Needs_Action/ | wc -l
```

MAX_ITERATIONS=10 set in `.env`.

---

## 9. Architecture Documentation

**Requirement:** "Documentation of your architecture and lessons learned"

```bash
ls ~/piaic/projects/personal_ai_employee/docs/
head -30 ~/piaic/projects/personal_ai_employee/docs/status.md
```

Key docs: `GOLD_TIER_PLAN.md`, `docs/status.md` (architectural decisions AD-001 → AD-003), `README.md`, `QUICKSTART.md`.

---

## 10. Cron Schedule (Scheduling)

```bash
crontab -l
```

Active jobs:
- `*/2 * * * *` — orchestrator cycle
- `0 7 * * 1` — CEO briefing (Monday 7 AM)
- `0 12 * * *` — content calendar watcher check

---

## Gold Tier Checklist

| Requirement | Feature | Evidence |
|---|---|---|
| Full cross-domain integration | Gemini content calendar LI+FB+IG | `Content_Calendar/CALENDAR_*.md` |
| Odoo accounting via MCP | Revenue/expense read, draft invoice | Odoo port 8069, `Pending_Approval/ODOO_*` |
| Facebook + Instagram | `PostFacebookSkill`, `PostInstagramSkill` | Live post IDs, meta_watcher |
| Twitter/X | `post_twitter.py`, `twitter_watcher.py`, auth verified | 402 = free API limit, not code bug |
| Multiple MCP servers | gmail + filesystem + odoo | `.mcp.json` |
| CEO Briefing + Audit | `GenerateCEOBriefingSkill` | `Briefings/*.md` with Odoo financials |
| Error recovery | Queuing, retry, vault overflow | `QUEUED_MCP_*`, health check |
| Audit logging | `audit_master.json` | Structured JSON, 1000-entry rolling |
| Ralph Wiggum loop | Stop hook + session file | `.claude/hooks/stop.sh` |
| Architecture docs | `docs/status.md`, AD-001–003 | Decisions + lessons |
| Agent Skills | All features as `*Skill` classes | `src/orchestrator/skills/` |
