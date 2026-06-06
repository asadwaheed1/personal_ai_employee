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

### 1.4 Error Recovery & Graceful Degradation Hardening `[x]`
**What:** Strengthen existing partial coverage. Each component degrades independently.  
**Why:** Explicit Gold requirement.  
**Implementation:**
1. **Gmail MCP Queuing**: Transient failures queue actions as `QUEUED_MCP_GMAIL_*.json` for auto-retry.
2. **LinkedIn Resilience**: `post_linkedin.py` returns `retry` status; Orchestrator keeps post in `Approved/`.
3. **Vault Lock Handling**: Added `_handle_vault_locked` to Orchestrator to log pending counts to `/tmp/vault_overflow/`.
4. **Overflow Sync**: `_sync_from_overflow` recovers logs when vault is unlocked.
5. **Health Check**: Created `scripts/health_check.py` to verify Gmail MCP and LinkedIn API status, updates Dashboard.md.
6. **Preflight**: (Skipped reattempt as per user instruction).

**Files modified:**
- `src/orchestrator/mcp_processor.py` (Gmail queuing)
- `src/orchestrator/orchestrator.py` (Vault lock & overflow sync)
- `src/orchestrator/skills/post_linkedin.py` (Retry status)
- `scripts/health_check.py` (New)

**Done when:** Killing Gmail MCP mid-run does not crash orchestrator; queued items process on recovery.

---

## Phase 2 — Social Platform Integrations (Est. 3-5 days)

### 2.1 Twitter/X Integration `[x]`
**What:** Post tweets, monitor mentions, generate weekly engagement summary.  
**Why:** Explicit Gold requirement.  
**API:** Twitter API v2 (Free tier: 1,500 tweet writes/month, read limited)  
**Implementation:**
1. **API Client**: `src/orchestrator/skills/twitter_api_client.py` uses `tweepy` for v2 (tweets/mentions) and v1.1 (media).
2. **Posting Skill**: `src/orchestrator/skills/post_twitter.py` handles immediate/scheduled/approved tweets.
3. **Mention Watcher**: `src/watchers/twitter_watcher.py` polls mentions every 15m; creates `Needs_Action` items.
4. **Lifecycle**: Integrated into `WatcherManager` and `create_content_plan.py`.

**Files created/modified:**
- `src/orchestrator/skills/twitter_api_client.py`
- `src/orchestrator/skills/post_twitter.py`
- `src/watchers/twitter_watcher.py`
- `src/watchers/run_twitter_watcher.py`
- `src/orchestrator/watcher_manager.py`
- `requirements.txt` (added tweepy)

**Done when:** Content calendar entry with `platform: twitter` gets approved → tweet posted → logged in audit.

---

### 2.2 Facebook + Instagram Integration `[x]`
**What:** Post to Facebook Page + Instagram Business, generate engagement summary.  
**Why:** Explicit Gold requirement.  
**Implementation:**
1. **API Client**: `src/orchestrator/skills/meta_api_client.py` handles Graph API v21.0, tokens, and discovery.
2. **Posting Skills**: `post_facebook.py` and `post_instagram.py` for HITL-gated publishing.
3. **Watcher**: `src/watchers/meta_watcher.py` monitors comments/mentions.
4. **Setup**: `scripts/setup_meta_api.py` for interactive authentication.

**Files created/modified:**
- `src/orchestrator/skills/meta_api_client.py`
- `src/orchestrator/skills/post_facebook.py`
- `src/orchestrator/skills/post_instagram.py`
- `src/watchers/meta_watcher.py`
- `src/watchers/run_meta_watcher.py`
- `scripts/setup_meta_api.py`
- `src/orchestrator/watcher_manager.py`
- `src/orchestrator/skills/create_content_plan.py`

**Done when:** Content calendar entry with `platform: facebook` approved → FB post published + Instagram post published → engagement logged.

---

### 2.3 Cross-Platform Content Calendar `[x]`
**What:** Unified calendar covers LinkedIn + Twitter + Facebook + Instagram. Single plan drives all platforms.  
**Why:** Required for multi-platform Gold req. Prevents duplicate calendar files per platform.  
**Implementation:**
1. **Plan Generator**: `create_content_plan.py` now generates per-platform post files (`LINKEDIN_POST_*.json`, etc.).
2. **Unified Watcher**: `src/watchers/content_calendar_watcher.py` monitors for all platform-specific posts (replacing the LinkedIn-only watcher).
3. **Smart Routing**: `process_approved_actions.py` identifies the platform from metadata and routes to the specific posting skill.

**Files modified:**
- `src/orchestrator/skills/create_content_plan.py`
- `src/watchers/content_calendar_watcher.py` (new unified watcher)
- `src/orchestrator/watcher_manager.py` (swapped watchers)
- `src/orchestrator/skills/process_approved_actions.py` (routing)

**Done when:** Single `create_content_plan` generates multi-platform calendar; watcher routes to correct skill per platform.

---

## Phase 3 — Odoo Accounting Integration (Est. 5+ days, Optional)

### 3.1 Odoo Community Setup `[x]`
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

### 3.2 Odoo MCP Server Integration `[x]`
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

### 4.1 Architecture Documentation `[x]`
**What:** Document Gold tier architecture decisions, lessons learned.  
**Why:** Explicit Gold submission requirement.  
**Implementation:**
- Created `GOLD_TIER_COMPLETION.md` with Mermaid architecture diagram.
- Documented key features: multi-platform posting, resilience, and autonomous loops.
- Outlined component responsibilities and integration patterns.

**Done when:** `GOLD_TIER_COMPLETION.md` exists with complete architecture + decisions.

---

### 4.2 Comprehensive Audit Logging `[x]`
**What:** Structured JSON audit for every Gold-tier action. Queryable, 90-day retention.  
**Why:** Explicit Gold requirement. Silver has partial audit.  
**Implementation:**
1. **Audit Skill**: Created `src/orchestrator/skills/audit_logger.py` to handle structured JSON records.
2. **Unified Base**: Added `_log_audit` helper to `BaseSkill` class.
3. **Full Integration**: All social posting and email skills now log to `vault/Logs/audit_*.json`.
4. **Master Log**: Maintains `audit_master.json` with the latest 1000 entries for rapid analysis.

**Done when:** All external actions produce a queryable JSON audit entry.

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
| Full cross-domain integration (Personal + Business) | 2.3 | `[x]` |
| Odoo accounting + MCP integration | 3.1 + 3.2 | `[x]` |
| Facebook + Instagram integration | 2.2 | `[x]` |
| Twitter/X integration | 2.1 | `[x]` |
| Multiple MCP servers | 1.3 | `[x]` |
| Weekly CEO Briefing generation | 1.2 | `[x]` |
| Error recovery + graceful degradation | 1.4 | `[x]` |
| Comprehensive audit logging | 4.2 | `[x]` |
| Ralph Wiggum autonomous loop | 1.1 | `[x]` |
| Architecture documentation | 4.1 | `[x]` |
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
