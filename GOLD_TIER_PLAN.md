# Gold Tier Implementation Plan

**Created:** 2026-04-24  
**Branch:** silver-imp → gold-imp (create when starting)  
**Reference:** requirements.md §Gold Tier  
**Status file:** status.md (update after each task completes)

---

## Progress Legend
- `[ ]` Not started
- `[~]` In progress
- `[x]` Complete
- `[!]` Blocked / needs decision

---

## Phase 1 — Quick Wins (Est. 1-2 days)

### 1.1 Ralph Wiggum Stop Hook `[x]`
**What:** Autonomous multi-step task loop. Claude keeps iterating until task file moves to `Done/`.  
**Why:** Explicit Gold requirement. Needed for CEO briefing + audit to run without babysitting.  
**How:**
1. Check if plugin exists: `~/.claude/plugins/ralph-wiggum/` or via Claude Code plugin registry
2. If plugin absent — implement custom stop hook in `.claude/hooks/stop.sh`:
   - Read `TASK_COMPLETE` promise from stdout OR check if triggering file moved to `Done/`
   - If not complete and iterations < MAX_ITER → re-inject prompt, return non-zero exit
   - If complete → exit 0
3. Wire hook in `.claude/settings.json`:
   ```json
   "hooks": {
     "Stop": [{"type": "command", "command": "bash .claude/hooks/stop.sh"}]
   }
   ```
4. Add `MAX_ITERATIONS=10` env var to `.env`
5. Test: drop file in `Inbox/`, verify Claude loops until moves to `Done/`

**Files to create/modify:**
- `.claude/hooks/stop.sh` (new)
- `.claude/settings.json` (add hook)
- `.env` (add MAX_ITERATIONS)

**Done when:** Claude processes multi-file `Needs_Action` batch without manual re-trigger.

---

### 1.2 CEO Weekly Briefing Skill `[x]`
**What:** Autonomous weekly executive summary. Reads vault state, generates `Briefings/YYYY-MM-DD_Monday_Briefing.md`.  
**Why:** Explicit Gold requirement. Differentiates from Silver.  
**How:**
1. Create `src/orchestrator/skills/generate_ceo_briefing.py`:
   - Reads `Done/` folder (last 7 days) → completed task count, categories
   - Reads `Logs/audit_*.json` (last 7 days) → email/LinkedIn/MCP action counts
   - Reads `ai_employee_vault/Content_Calendar/` → posts published vs planned
   - Reads `Company_Handbook.md` → business goals/targets
   - Generates structured `Briefings/YYYY-MM-DD_Monday_Briefing.md` per template
2. Template sections: Executive Summary, Email Activity, LinkedIn Activity, Completed Tasks, Pending Items, Anomalies, Next Week Prep
3. Create `ai_employee_vault/Briefings/` folder
4. Add cron job: `0 7 * * 1` (Monday 7 AM) → runs briefing skill
5. Register in orchestrator skills registry

**Files to create/modify:**
- `src/orchestrator/skills/generate_ceo_briefing.py` (new)
- `ai_employee_vault/Briefings/` (new folder)
- `scripts/setup_cron.sh` (add Monday 7 AM job)
- `src/orchestrator/orchestrator.py` (register skill)

**Done when:** Monday cron produces `Briefings/YYYY-MM-DD_Monday_Briefing.md` with real data from vault.

---

### 1.3 Multiple MCP Servers `[x]`
**What:** Expand beyond Gmail MCP. Add filesystem MCP + optionally calendar MCP.  
**Why:** Gold req: "Multiple MCP servers for different action types."  
**How:**
1. Add filesystem MCP to `.mcp.json`:
   ```json
   {
     "mcpServers": {
       "gmail": { ... existing ... },
       "filesystem": {
         "command": "npx",
         "args": ["-y", "@modelcontextprotocol/server-filesystem", "/home/asad/piaic/projects/personal_ai_employee/ai_employee_vault"]
       }
     }
   }
   ```
2. Optional: add `@modelcontextprotocol/server-google-calendar` if Google Calendar creds available
3. Update `.claude/settings.local.json` allowlist with filesystem MCP tools
4. Test: Claude can list/read vault files via MCP (not just direct Python)
5. Update mcp_processor.py to route `type: filesystem` action files

**Files to modify:**
- `.mcp.json`
- `.claude/settings.local.json`
- `src/orchestrator/mcp_processor.py` (filesystem action routing)

**Done when:** `mcp_processor.py` can execute filesystem MCP actions from `Needs_Action/MCP_FILESYSTEM_*.json`.

---

### 1.4 Error Recovery & Graceful Degradation Hardening `[ ]`
**What:** Strengthen existing partial coverage. Each component degrades independently.  
**Why:** Explicit Gold requirement.  
**How:**
1. Gmail MCP down → queue outgoing to `Needs_Action/QUEUED_EMAIL_*.json`, retry on next cycle
2. LinkedIn API down → log to `Logs/`, keep calendar entry as pending, retry next watcher cycle
3. Orchestrator crash → watchdog.py already restarts; verify restart picks up mid-queue items
4. Vault locked → write to `/tmp/vault_overflow/`, sync on next run
5. Add `health_check.py` script: pings Gmail MCP + LinkedIn API, writes status to `Dashboard.md`
6. Add bounded retry/backoff to Gmail MCP preflight (3 attempts, 10s backoff) — listed in Silver next steps

**Files to modify:**
- `src/orchestrator/orchestrator.py` (overflow queue)
- `src/watchers/gmail_watcher.py` (retry preflight)
- `src/watchers/linkedin_watcher.py` (API down handling)
- `scripts/health_check.py` (new)

**Done when:** Killing Gmail MCP mid-run does not crash orchestrator; queued items process on recovery.

---

## Phase 2 — Social Platform Integrations (Est. 3-5 days)

### 2.1 Twitter/X Integration `[ ]`
**What:** Post tweets, monitor mentions, generate weekly engagement summary.  
**Why:** Explicit Gold requirement.  
**API:** Twitter API v2 (Free tier: 1,500 tweet writes/month, read limited)  
**How:**
1. Create Twitter developer app at developer.twitter.com → get API keys
2. Add env vars: `TWITTER_API_KEY`, `TWITTER_API_SECRET`, `TWITTER_ACCESS_TOKEN`, `TWITTER_ACCESS_SECRET`, `TWITTER_BEARER_TOKEN`
3. Install: `pip install tweepy` → add to `requirements.txt`
4. Create `src/orchestrator/skills/twitter_api_client.py`:
   - OAuth 1.0a for write (post tweets)
   - Bearer token for read (search mentions)
   - Methods: `post_tweet()`, `get_mentions()`, `get_engagement_stats()`
5. Create `src/orchestrator/skills/post_twitter.py` skill:
   - Reads `Content_Calendar/` for Twitter-tagged posts
   - HITL: creates `Pending_Approval/TWITTER_*.md` before posting
   - On approval: posts via API, logs to audit
6. Create `src/watchers/twitter_watcher.py`:
   - Polls mentions every 15 min (rate limit aware)
   - Creates `Needs_Action/TWITTER_MENTION_*.md` for important mentions
7. Extend content calendar schema to include `platform: twitter` entries
8. Add watcher to `watcher_manager.py`
9. Add cron: `*/15 * * * *` Twitter mention check

**Files to create:**
- `src/orchestrator/skills/twitter_api_client.py`
- `src/orchestrator/skills/post_twitter.py`
- `src/watchers/twitter_watcher.py`
- `src/watchers/run_twitter_watcher.py`

**Files to modify:**
- `requirements.txt` (add tweepy)
- `.env` / `.env.example` (Twitter keys)
- `src/orchestrator/watcher_manager.py` (add Twitter watcher)
- `src/orchestrator/skills/create_content_plan.py` (multi-platform)
- `scripts/setup_cron.sh` (Twitter mention cron)

**Done when:** Content calendar entry with `platform: twitter` gets approved → tweet posted → logged in audit.

---

### 2.2 Facebook + Instagram Integration `[ ]`
**What:** Post to Facebook Page + Instagram Business, generate engagement summary.  
**Why:** Explicit Gold requirement.  
**API:** Meta Graph API v21.0  
**Prerequisites (BLOCKING):** Meta developer app requires app review for `pages_manage_posts` + `instagram_content_publish` permissions. Allow 1-7 days for review.  
**How:**
1. Create Meta developer app at developers.facebook.com
2. Configure: Facebook Login, Pages API, Instagram Basic Display
3. Get permissions: `pages_read_engagement`, `pages_manage_posts`, `instagram_basic`, `instagram_content_publish`
4. Add env vars: `META_APP_ID`, `META_APP_SECRET`, `META_ACCESS_TOKEN`, `META_PAGE_ID`, `INSTAGRAM_BUSINESS_ACCOUNT_ID`
5. Install: `pip install requests` (already present)
6. Create `src/orchestrator/skills/meta_api_client.py`:
   - OAuth token management (long-lived token refresh)
   - Methods: `post_to_facebook()`, `post_to_instagram()`, `get_page_insights()`
7. Create `src/orchestrator/skills/post_facebook.py` skill
8. Create `src/orchestrator/skills/post_instagram.py` skill  
9. Create `src/watchers/meta_watcher.py`:
   - Polls Facebook Page comments/mentions
   - Polls Instagram mentions
   - Creates `Needs_Action/META_*.md` files
10. Extend content calendar for `platform: facebook` and `platform: instagram`
11. Add watcher to `watcher_manager.py`

**Files to create:**
- `src/orchestrator/skills/meta_api_client.py`
- `src/orchestrator/skills/post_facebook.py`
- `src/orchestrator/skills/post_instagram.py`
- `src/watchers/meta_watcher.py`
- `src/watchers/run_meta_watcher.py`
- `scripts/setup_meta_api.py` (OAuth setup helper)

**Files to modify:**
- `requirements.txt`
- `.env` / `.env.example`
- `src/orchestrator/watcher_manager.py`
- `src/orchestrator/skills/create_content_plan.py`

**Done when:** Content calendar entry with `platform: facebook` approved → FB post published + Instagram post published → engagement logged.

---

### 2.3 Cross-Platform Content Calendar `[ ]`
**What:** Unified calendar covers LinkedIn + Twitter + Facebook + Instagram. Single plan drives all platforms.  
**Why:** Required for multi-platform Gold req. Prevents duplicate calendar files per platform.  
**How:**
1. Extend `create_content_plan.py`:
   - Calendar JSON schema adds `platforms: ["linkedin", "twitter", "facebook", "instagram"]` per entry
   - Content adapted per platform (280 char limit for Twitter, visual focus for Instagram)
2. Extend `linkedin_watcher.py` → rename/refactor to `content_calendar_watcher.py`:
   - Routes posts to correct platform skill based on `platforms` field
   - Handles per-platform approval files
3. Update existing W15/W16/W17 calendars to new schema (migration script)

**Files to modify:**
- `src/orchestrator/skills/create_content_plan.py`
- `src/watchers/linkedin_watcher.py` → extend (keep LinkedIn, add routing)
- `ai_employee_vault/Content_Calendar/CALENDAR_*.json` (schema migration)

**Done when:** Single `create_content_plan` generates multi-platform calendar; watcher routes to correct skill per platform.

---

## Phase 3 — Odoo Accounting Integration (Est. 5+ days, Optional)

### 3.1 Odoo Community Setup `[!]`
**What:** Self-hosted Odoo Community 19+ with accounting module.  
**Why:** Gold requirement for accounting system integration.  
**Decision needed:** Local install vs Docker. Recommend Docker for isolation.  
**How:**
1. Install Docker if not present
2. `docker-compose.yml` for Odoo 19 + PostgreSQL
3. Configure accounting module
4. Create demo company + chart of accounts
5. Generate API key for JSON-RPC access

**Files to create:**
- `docker/docker-compose.yml`
- `docker/odoo.conf`

**Done when:** `http://localhost:8069` serves Odoo with accounting module active + API accessible.

---

### 3.2 Odoo MCP Server Integration `[!]`
**What:** MCP server wrapping Odoo JSON-RPC API. Claude can read/write accounting records.  
**Why:** Gold requirement: "integrate via MCP server using Odoo's JSON-RPC APIs."  
**Reference:** `https://github.com/AlanOgic/mcp-odoo-adv`  
**How:**
1. Clone/install `mcp-odoo-adv` MCP server
2. Configure `.mcp.json`:
   ```json
   "odoo": {
     "command": "node",
     "args": ["/path/to/mcp-odoo-adv/index.js"],
     "env": {
       "ODOO_URL": "http://localhost:8069",
       "ODOO_DB": "odoo",
       "ODOO_USERNAME": "admin",
       "ODOO_PASSWORD": "..."
     }
   }
   ```
3. Add env vars to `.env`
4. Create `src/orchestrator/skills/odoo_accounting.py` skill:
   - `get_revenue_summary()` — reads invoices for period
   - `get_expense_summary()` — reads expenses
   - `create_draft_invoice()` — draft only, needs HITL approval to post
5. Extend CEO Briefing to pull Odoo revenue data

**Files to create:**
- `src/orchestrator/skills/odoo_accounting.py`
- `docker/docker-compose.yml`

**Files to modify:**
- `.mcp.json`
- `.env` / `.env.example`
- `src/orchestrator/skills/generate_ceo_briefing.py` (add Odoo revenue section)

**Done when:** CEO Briefing includes revenue figures pulled live from Odoo invoices via MCP.

---

## Phase 4 — Documentation & Polish (Est. 0.5 days)

### 4.1 Architecture Documentation `[ ]`
**What:** Document Gold tier architecture decisions, lessons learned.  
**Why:** Explicit Gold submission requirement.  
**How:**
1. Create `GOLD_TIER_COMPLETION.md`:
   - Architecture diagram (ASCII) with all platforms
   - Key decisions (why Twitter API v2, why Meta Graph API, Ralph Wiggum pattern used)
   - Lessons learned
   - Known limitations
2. Update `README.md` → Gold tier features section
3. Update `AGENTS.md` → new skills documented

**Done when:** `GOLD_TIER_COMPLETION.md` exists with complete architecture + decisions.

---

### 4.2 Comprehensive Audit Logging `[ ]`
**What:** Structured JSON audit for every Gold-tier action. Queryable, 90-day retention.  
**Why:** Explicit Gold requirement. Silver has partial audit.  
**How:**
1. Extend `update_dashboard.py` to write structured JSON per action:
   ```json
   {
     "timestamp": "ISO8601",
     "action_type": "tweet_post|facebook_post|instagram_post|odoo_invoice",
     "actor": "claude_code",
     "platform": "twitter|facebook|instagram|odoo",
     "target": "...",
     "approval_status": "approved|auto",
     "approved_by": "human",
     "result": "success|failure",
     "error": null
   }
   ```
2. Create `scripts/audit_cleanup.sh`: deletes audit JSON older than 90 days
3. Add weekly cron for cleanup

**Files to modify:**
- `src/orchestrator/skills/update_dashboard.py`
- `scripts/setup_cron.sh`

**Files to create:**
- `scripts/audit_cleanup.sh`

---

## Execution Order (Dependency-aware)

```
1.1 Ralph Wiggum    ──→  enables autonomous execution of everything below
1.2 CEO Briefing    ──→  standalone, can parallel with 1.3
1.3 Multiple MCP    ──→  unblocks filesystem actions
1.4 Error Recovery  ──→  can parallel with 1.2 and 1.3
        │
        ▼
2.1 Twitter/X       ──→  no blockers, start after Phase 1
2.2 Facebook/IG     ──→  BLOCKED on Meta app review, start app creation NOW
2.3 Cross-platform  ──→  depends on 2.1 + 2.2 complete
        │
        ▼
3.1 Odoo Setup      ──→  optional, start only if Phase 2 complete
3.2 Odoo MCP        ──→  depends on 3.1
        │
        ▼
4.1 Docs            ──→  last
4.2 Audit Logging   ──→  can be done in parallel with Phase 2
```

---

## Environment Variables Needed (add to .env)

```bash
# Twitter/X
TWITTER_API_KEY=
TWITTER_API_SECRET=
TWITTER_ACCESS_TOKEN=
TWITTER_ACCESS_SECRET=
TWITTER_BEARER_TOKEN=

# Meta (Facebook + Instagram)
META_APP_ID=
META_APP_SECRET=
META_ACCESS_TOKEN=
META_PAGE_ID=
INSTAGRAM_BUSINESS_ACCOUNT_ID=

# Odoo (optional)
ODOO_URL=http://localhost:8069
ODOO_DB=odoo
ODOO_USERNAME=admin
ODOO_PASSWORD=

# Ralph Wiggum
MAX_ITERATIONS=10
```

---

## Gold Tier Requirements Checklist

| Requirement | Phase | Status |
|---|---|---|
| All Silver requirements | — | ✅ Complete |
| Full cross-domain integration (Personal + Business) | 2.3 | `[ ]` |
| Odoo accounting + MCP integration | 3.1 + 3.2 | `[ ]` |
| Facebook + Instagram integration | 2.2 | `[ ]` |
| Twitter/X integration | 2.1 | `[ ]` |
| Multiple MCP servers | 1.3 | `[x]` |
| Weekly CEO Briefing generation | 1.2 | `[x]` |
| Error recovery + graceful degradation | 1.4 | `[ ]` |
| Comprehensive audit logging | 4.2 | `[ ]` |
| Ralph Wiggum autonomous loop | 1.1 | `[x]` |
| Architecture documentation | 4.1 | `[ ]` |
| All AI as Agent Skills | ongoing | ✅ (Silver) |

---

## Session Resume Instructions

**Read this file first each session.** Then:
1. Check checkboxes above — find first `[ ]` or `[~]` item
2. Check `status.md` → `## Gold Tier Progress` section for last completed task + any blockers
3. Continue from where previous session stopped
4. Mark tasks `[x]` in this file + update `status.md` after each task completes

**Action item for EVERY session start:**
- `META_APP_REVIEW`: Create Meta developer app NOW (review takes days). Don't wait until Phase 2.
