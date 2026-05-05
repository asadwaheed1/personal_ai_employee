# Personal AI Employee - Project Status

**Last Updated:** 2026-05-04  
**Current Branch:** gold-imp  
**Target Tier:** Gold  
**Overall Status:** ✅ Gold complete + image generation pipeline active. Gemini Imagen → Imgur/catbox → real image URLs for FB/IG/LI posts. All platforms posting live.

---

## 📊 Completion Summary

| Area | Status | Notes |
|---|---|---|
| Gmail Watcher | ✅ Complete | Unread detection + action file generation |
| LinkedIn Integration | ✅ Complete | Official API v2 + OAuth + posting flow |
| Orchestrator | ✅ Complete | Handles Inbox/Needs_Action/Approved/MCP actions |
| MCP Processing | ✅ Complete | External email actions executed via MCP workflow |
| HITL Approval | ✅ Complete | Pending_Approval → Approved/Rejected path |
| Scheduling | ✅ Complete | Cron installed + scheduled commands smoke-tested |
| Error recovery hardening | ✅ Complete | Retry logic, validation, overflow queue, health check |
| Twitter/X Integration | ✅ Complete | Tweepy client, posting skill, mention watcher (disabled from calendar — free API blocked) |
| Facebook + Instagram | ✅ Complete | Meta API client, FB/IG posting skills, activity watcher — live-tested 2026-04-30 |
| Cross-platform Calendar| ✅ Complete | Gemini AI generates platform-specific content; LI/FB/IG active, Twitter excluded |
| Comprehensive Audit | ✅ Complete | Structured JSON logging for all external actions |
| MCP fallback (direct API) | ✅ Complete | Gmail direct API fallback when MCP tool unavailable in session |
| HITL approval flow | ✅ Fixed | Social posts in Approved/ now parse content + post live correctly |
| Documentation | ✅ Updated | DEMO.md + status.md aligned to Gold requirements |
| Image generation pipeline | ✅ Complete | Gemini Imagen → Imgur/catbox → real image_url for FB/IG/LI calendar posts (2026-05-04) |

---

## ✅ Latest Confirmed Outcomes (2026-04-30) — Bug Fixes + Demo Hardening

1. **MCP signal detection fixed** (`mcp_processor.py`):
   - Root cause: `'error:'` was in `failure_signals` → "Done. Message marked read." classified as failure.
   - Fix: split into hard failures (MCP not loaded — always fail, set `mcp_unavailable: True`) vs soft failures (overridden by success signal).
   - Success signals expanded: `'done.'`, `'done!'`, `'marked read'`, `'message marked'` added.
   - Result: false-failure rate eliminated; success messages no longer misread.

2. **Gmail direct API fallback added** (`mcp_processor.py`):
   - New `_execute_gmail_action_direct()` — uses `google-api-python-client` + existing `gmail_token.json`, no MCP subprocess.
   - Supports: `modify_email` (archive, mark_read), `trash_email`.
   - Triggered automatically when MCP returns `mcp_unavailable: True`.
   - Eliminates "gmail_mark_read tool not available" permanent failures.

3. **Social post Approved folder flow fixed** (`process_approved_actions.py`):
   - Root cause: `_execute_skill()` looked for JSON sidecar `Approved/{id}.json` — never exists for social posts. Fell back to `{'action': 'execute_approved'}` with no content → silent fail.
   - Fix: new `_execute_social_post()` parses content from approval `.md` directly (`_parse_md_code_block`, `_parse_md_bold_field`) and calls skill class directly (no subprocess).
   - All 4 platforms fixed: Facebook, Instagram, LinkedIn, Twitter.

4. **`require_approval` key mismatch fixed** (all 4 social skills):
   - Skills checked `requires_approval` (with s); callers passed `require_approval` (no s).
   - Fix: `params.get('requires_approval', params.get('require_approval', True))` in all 4 skills.

5. **Facebook page token fixed** (`post_facebook.py`, `post_instagram.py`):
   - Root cause: `get_pages()` API call failing → "Could not find access token" error.
   - Fix: read `page_access_token` from `credentials/meta_api_token.json` first; API call only as fallback.

6. **Live posting re-confirmed (2026-04-30)**:
   - Facebook ✅ `698457253346943_122171996522861671`
   - Instagram ✅ `18114009202742765`

7. **DEMO.md created**: Gold-tier-only demo guide with exact commands, mapped to each requirement.

---

## ✅ Latest Confirmed Outcomes (2026-05-04) — Image Generation Pipeline

1. **`generate_image.py` skill created** (`src/orchestrator/skills/generate_image.py`):
   - Calls `imagen-3.0-generate-001` via `google-genai` SDK.
   - Uploads image bytes to Imgur (if `IMGUR_CLIENT_ID` set) with catbox.moe fallback (no key required).
   - Returns `{'success': True, 'image_url': 'https://...'}`.

2. **`content_calendar_watcher.py` auto-generates images**:
   - For FB/IG/LI posts with `image_prompt` and no `image_url`: calls `GenerateImageSkill` before writing action file.
   - Real `image_url` embedded in `Needs_Action/SCHEDULED_*.md` action file.
   - Instagram: URL required, shown as hard field. Facebook/LinkedIn: URL shown, optional.

3. **`post_facebook.py` uses image URL**:
   - New `post_photo_to_facebook_page` method in `meta_api_client.py` (uses `/{page_id}/photos` endpoint).
   - When `image_url` present, routes to photo post instead of feed post.

4. **`post_linkedin.py` uses image URL**:
   - Downloads `image_url` to temp file → uploads via LinkedIn asset registration API.
   - Temp file cleaned up in `finally` block.

5. **`create_content_plan.py` generates `image_prompt` for all 3 platforms** (LinkedIn added).

6. **`process_approved_actions.py` parses `image_url`** for FB and LI in `_execute_social_post`.

---

## ✅ Latest Confirmed Outcomes (2026-04-26) — System Hardening + AI Content

1. **Startup bug fixed** (`orchestrator.py:523`): `...` truncation broke `try` block — restored full processing logic.

2. **Watcher ABC fix** (`twitter_watcher.py`, `meta_watcher.py`): Added missing `check_for_updates` + `create_action_file` abstract method implementations — all 5 watchers now start cleanly.

3. **stop.sh updated**: Kill pattern now covers `twitter`, `meta`, `content_calendar` watchers (was only `filesystem|gmail|linkedin`).

4. **Health dashboard auto-updates on preflight**: `watcher_manager.py` calls `_update_health_dashboard()` after every preflight pass or fail — no more stale April 24 health status.

5. **Gmail archive bug fixed**: `process_email_actions.py` key transform was capitalizing `removeLabelIds` → `RemoveLabelIds`, causing `mcp_processor.py` param lookup to return empty labels. Archive instruction now hardcoded with explicit `removeLabels: ["INBOX"]`.

6. **Gemini AI content generation** (`create_content_plan.py`):
   - Replaced static hardcoded templates with `gemini-3-flash-preview` API calls.
   - Platform-specific tone: LinkedIn = first-person individual developer (no company name), Facebook = casual/warm, Instagram = lifestyle/visual.
   - Image prompts generated for FB + IG posts.
   - `google-genai>=1.0.0` added to `requirements.txt`; `GEMINI_API_KEY` added to `.env`.
   - Twitter excluded from calendar generation (free API tier blocked).

7. **Live posting confirmed (2026-04-26)**:
   - LinkedIn ✅ `urn:li:share:7454075831061999616` — posts as individual (`urn:li:person`), not company.
   - Facebook ✅ `698457253346943_122171523488861671`
   - Instagram ✅ `18104942089822106`

---

## ✅ Latest Confirmed Outcomes (2026-04-25) — Odoo Integration

1. **Odoo Community 17 running via Docker** (task 3.1):
   - `docker/docker-compose.yml` — Odoo 17 + PostgreSQL 15, port 8069.
   - `docker/odoo.conf` — DB config pointing to postgres container.
   - DB initialized with base + account modules (47 chart-of-accounts entries, 24 existing journal entries).
   - XML-RPC auth confirmed: UID 2, full `account.move` access.

2. **Odoo accounting skill created** (`src/orchestrator/skills/odoo_accounting.py`):
   - `get_revenue_summary()` — reads posted customer invoices for any period via XML-RPC.
   - `get_expense_summary()` — reads posted vendor bills.
   - `create_draft_invoice()` — creates DRAFT invoice only; writes HITL approval file to `Pending_Approval/`.
   - Live test: returned 4 invoices totaling $143,175 for April 2026.

3. **Odoo MCP server added** (`odoo-mcp` npm package):
   - `.mcp.json` updated — 3 MCP servers: gmail, filesystem, odoo.
   - Odoo MCP env: `ODOO_URL=http://localhost:8069`, `ODOO_DB=odoo`, `ODOO_USERNAME=admin`.
   - `.env` updated with `ODOO_URL/DB/USERNAME/PASSWORD`.

4. **CEO Briefing extended with Odoo financial section**:
   - `generate_ceo_briefing.py` — `_fetch_odoo_financials()` pulls revenue + expenses via XML-RPC.
   - `_render_odoo_section()` renders financial table (revenue, collected, outstanding, expenses, net).
   - Gracefully degrades when Odoo unavailable ("Odoo not configured").
   - Live test: briefing `2026-04-25_Monday_Briefing.md` shows $70,150 revenue for 2026-04-18→25.

---

## ✅ Latest Confirmed Outcomes (2026-04-25)

1. **Live API testing completed:**
   - Facebook (GeekNova page, ID: 698457253346943) — post confirmed live via `meta_api_client.post_to_facebook_page`.
   - Instagram (GeekNova IG, ID: 17841426989901806) — post confirmed live (post_id: 18528304957079270).
   - Twitter/X — auth verified (OAuth 1.0a), posting blocked by free API tier (402 Payment Required). Code correct.
   - tweepy 4.16.0 installed in venv (was missing despite being in requirements.txt).
   - Meta credentials saved to `credentials/meta_api_token.json` with page token + IG ID.
   - `.env` updated: `META_ACCESS_TOKEN`, `META_PAGE_ID=698457253346943`, `INSTAGRAM_BUSINESS_ACCOUNT_ID=17841426989901806`.

2. **setup.sh updated to Gold Tier:**
   - Header updated from "Silver" to "Gold".
   - `Briefings/` directory added to vault structure creation + validation.
   - Next steps updated to include Twitter, Meta setup scripts, cron, and all watcher commands.

3. **requirements.txt header updated** to Gold Tier.

4. **GOLD_TIER_PLAN.md** — "Full cross-domain integration" marked `[x]` (was stale `[ ]`; 2.3 complete).

---

## ✅ Latest Confirmed Outcomes (2026-04-24)

1. **Comprehensive audit logging implemented** (task 4.2):
   - `src/orchestrator/skills/audit_logger.py` — new skill to handle structured JSON logging.
   - `BaseSkill` — added `_log_audit` helper to ensure all skills can easily log external actions.
   - All social posting skills (LinkedIn, Twitter, Facebook, Instagram) and email skills now produce structured audit entries in `vault/Logs/audit_*.json`.
   - `audit_master.json` — maintains a consolidated history of the last 1000 actions for easy parsing.

2. **Meta (Facebook + Instagram) integration implemented** (task 2.2):
   - `src/orchestrator/skills/meta_api_client.py` — handles Graph API v21.0, long-lived tokens, and Page/Instagram discovery.
   - `src/orchestrator/skills/post_facebook.py` — posts to FB Pages with HITL approval and calendar support.
   - `src/orchestrator/skills/post_instagram.py` — posts to Instagram Business accounts (requires public image URL).
   - `src/watchers/meta_watcher.py` — monitors FB/IG comments and creates `Needs_Action` items.
   - `scripts/setup_meta_api.py` — interactive setup for token exchange and Page/IG discovery.

2. **Cross-platform content calendar implemented** (task 2.3):
   - `create_content_plan.py` — updated to generate per-platform post files for LinkedIn, Twitter, Facebook, and Instagram.
   - `src/watchers/content_calendar_watcher.py` — new unified watcher (replacing LinkedIn watcher) that monitors for all scheduled platform posts.
   - `process_approved_actions.py` — updated routing to call specific social media posting skills upon approval.

3. **Twitter/X integration implemented** (task 2.1):
   - `src/orchestrator/skills/twitter_api_client.py` — uses `tweepy` for API v2 (tweets/mentions) and v1.1 (media).
   - `src/orchestrator/skills/post_twitter.py` — supports immediate posting, calendar scheduling, and HITL-gated execution.
   - `src/watchers/twitter_watcher.py` — polls mentions every 15m; creates `Needs_Action/TWITTER_MENTION_*.md` with metrics.
   - `src/orchestrator/watcher_manager.py` — integrated `twitter_watcher` into the standard lifecycle management.
   - `create_content_plan.py` — updated to support `platforms: ['linkedin', 'twitter']` generating per-platform calendar entries.

2. **Error recovery & Graceful degradation hardened** (task 1.4):

   - **Gmail MCP Queuing**: Failed Gmail MCP actions with transient errors (timeout, token, network) now renamed to `QUEUED_MCP_GMAIL_*.json` in `Needs_Action/` for autonomous retry.
   - **LinkedIn Resilience**: `PostLinkedInSkill` now detects transient API errors and returns `status: retry`. Orchestrator skips archiving to `Done/` for these files, leaving them in `Approved/` for the next cycle.
   - **Vault Lock Handling**: Added `_handle_vault_locked` to Orchestrator. If lock acquisition fails, pending item counts are logged to `/tmp/vault_overflow/`.
   - **Overflow Synchronization**: `_sync_from_overflow` automatically moves overflow logs back to `vault/Logs/Overflow/` when the vault is successfully unlocked.
   - **Health Check Utility**: Created `scripts/health_check.py` to verify Gmail MCP and LinkedIn API status, with automatic `Dashboard.md` health-table updates.
   - Verified: killing network mid-run queues Gmail actions; manual health check correctly reports API status on Dashboard.

2. **Filesystem MCP server integrated** (task 1.3):
   - `.mcp.json` — added `@modelcontextprotocol/server-filesystem` server scoped to vault path.
   - `.claude/settings.local.json` — filesystem server enabled + 10 tool allowlist added.
   - `mcp_processor.py` — `_create_filesystem_instruction` now maps each tool (`read_file`, `write_file`, `list_directory`, `create_directory`, `move_file`, `search_files`, `delete_file`, `get_file_info`) to specific MCP prompts.
   - `_execute_filesystem_action` post-processes data-returning tools (read/list/search/info): if returncode=0 + non-empty output → success, even without text confirmation signal.
   - Added filesystem success signals to shared parser (`[file]`, `[directory]`, `directory contents`, `written to`, `deleted successfully`, etc.).
   - End-to-end tested: `list_directory` → `success: true` with real vault data; `write_file` → `success: true`, file verified on disk. All 3 test action files archived to Done/.

2. **CEO Weekly Briefing skill implemented** (task 1.2):
   - `src/orchestrator/skills/generate_ceo_briefing.py` — scans Done/ (last 7 days), audit logs, Content_Calendar, Pending_Approval, Needs_Action → generates structured briefing.
   - Sections: Executive Summary, Email Activity, LinkedIn Activity, Completed Tasks, Pending Items, Anomalies, Next Week Preparation.
   - Anomaly detection: high Needs_Action backlog (>20), approval queue backup (>5), audit errors, zero completions.
   - `ai_employee_vault/Briefings/` folder created.
   - Monday 7 AM cron added to `scripts/setup_cron.sh`.
   - Smoke-tested against live vault: 46 tasks completed, 45 pending, 2 anomalies detected — output correct.

2. **Ralph Wiggum stop hook implemented** (task 1.1):
   - `.claude/hooks/stop.sh` — activates only when `/tmp/ralph_wiggum` session file exists; injects continuation prompt if `Needs_Action/` has pending files; exits silently when done or max iterations reached.
   - `.claude/settings.json` — wires `Stop` hook to `stop.sh`.
   - `scripts/start_ralph_wiggum.sh` — session starter; supports `needs_action` and `done_file` check modes.
   - `.env` — added `MAX_ITERATIONS=10`.
   - Tested: hook exits 0 silently when no session file; injects continuation prompt with correct pending count when session active.

---

## ✅ Previously Confirmed Outcomes (2026-04-22)

1. **Approved-email MCP routing fixed** (`process_approved_actions.py`):
   - `type: email` files in `Approved/` now route to `process_email_actions.py` skill instead of falling through to "generic" handler.
   - `process_email_actions.py` parses Human Notes (reply body) + checked Suggested Actions, creates `MCP_EMAIL_*.json` files in `Needs_Action/`, archives email to `Done/PROCESSED_*`.
   - MCP processor executes JSON files via Gmail MCP server in next orchestrator cycle (mark_as_read, reply, draft_reply, archive, delete).
   - Archive double-write prevented: main loop skips `_archive_approval_file` when status is `mcp_queued` (skill already moved file).
   - Cron fallback (`*/15 * * * *`) now also routes correctly via same code path.

2. **Subprocess kill hardened** (`mcp_processor.py`, `orchestrator.py`):
   - Old pattern: `os.killpg(process.pid, SIGTERM)` + `time.sleep(2)` left orphan processes (pipes never drained, zombie risk).
   - New pattern: `os.getpgid(process.pid)` → `SIGTERM` to whole process group → `communicate(timeout=10)` to drain pipes → `SIGKILL` fallback if still alive → final `communicate()` to reap.
   - Eliminates orphan `claude` + `gmail-mcp-server` child processes after timeout.
   - Orchestrator monitoring loop unblocks correctly after 300s MCP timeout instead of hanging indefinitely.

3. Dashboard update behavior changed to event-driven only:
   - `watcher_manager` no longer writes `Dashboard.md` on every poll loop iteration.
   - Dashboard updates only when files are actually processed (moved between folders) or a watcher is restarted.
   - Gmail/LinkedIn watchers now immediately update dashboard after detecting new items (`_notify_dashboard` in `base_watcher.py`).
2. Dashboard Recent Activity deduplication applied:
   - All intake events (`Needs_Action`, `Inbox`, `Approved`, `MCP`, `Email auto-processing`) now track last-reported counts in orchestrator instance state.
   - Dashboard entry is only written when a count actually changes (e.g., 31→32), not on every identical poll cycle.
3. Recent Activity capped at 25 entries, newest on top:
   - `_add_activity` in `update_dashboard.py` prepends new entries and trims list to 25.
4. LinkedIn content calendar default posting time changed from 9 AM to 12 PM:
   - `optimal_times` list in `create_content_plan.py` updated; all future generated calendars start at 12 PM.
   - All existing calendar entries in W15, W16, W17 (JSON + MD files) backfilled to `T12:00:00`.
   - `Dashboard.md` content schedule reference also updated.

---

## ✅ Previously Confirmed Outcomes (2026-04-21)

1. Confirmed startup preflight gate correctly blocks runtime when Gmail MCP auth-refresh fails:
   - Failure observed in watcher manager logs: `❌ STARTUP PREFLIGHT FAILED: Gmail MCP authentication check failed`
   - Root error during preflight/profile check: `request to https://oauth2.googleapis.com/token failed, reason:`
   - Startup aborted as intended (watchers stopped).
2. Confirmed this incident was not orchestrator business-logic specific:
   - Direct Gmail MCP profile check failed during incident window with same OAuth token-endpoint error.
   - Network diagnostics later showed DNS resolution + HTTPS reachability healthy.
3. Confirmed recovery without code changes:
   - Direct Gmail MCP profile check succeeded after transient window.
   - Fresh startup preflight then passed at `2026-04-20 12:26:05`: `✅ Startup preflight passed: Gmail MCP authentication healthy`.
4. Previously delivered Silver hardening still in place:
   - Approved-folder execution path works without restart.
   - Direct approved-email skill execution path queues actions correctly.
   - Orchestrator loop remains integrated in watcher manager runtime.
   - Low-priority/newsletter auto-processing remains active.
   - MCP failure-text classification remains strict in `mcp_processor`.
5. Fixed email routing behavior for post-intake processing:
   - Auto-processed emails are removed from `Needs_Action` and archived to `Done`.
   - Emails with `requires_approval: true` are routed to `Pending_Approval` (no longer left in `Needs_Action`).
   - `Needs_Action` now acts as active queue, not long-term storage.
6. Added dashboard event-level visibility from orchestrator loop:
   - Logs/dashboard activity now include `Needs_Action` intake, `Inbox` intake, `Approved` intake, MCP execution results, and email auto-processing outcome counts.
   - Auto-processing log now reports explicit counters: `processed`, `kept_for_review`, `moved_to_pending_approval`.
   - Dashboard pending counts remain auto-refreshed from `Needs_Action` + `Pending_Approval`.
7. Verified no filename-duplicate email markdown artifacts across `Needs_Action` and `Done` in current vault snapshot.
   - Check result: `DUPLICATE_EMAIL_COUNT=0` for `EMAIL_*.md` base-name comparison.
8. Startup duplication behavior clarified and hardened:
   - Repeated preflight log lines were from repeated start/shutdown cycles and in-flight preflight finishing after shutdown signal, not concurrent active duplicate managers.
   - Added single-instance guard in `start.sh` to block duplicate watcher-manager launches.
9. Claude subprocess lifecycle hardened for timeout cleanup:
   - Replaced blocking `subprocess.run(... timeout=...)` paths with `Popen + communicate(timeout)` for Claude invocations in orchestrator + MCP processor.
   - On timeout, process group now gets `SIGTERM` then `SIGKILL` fallback, reducing orphan/background memory usage.
10. Approved-email action/reporting fixes applied:
   - `process_email_actions` now parses "Draft a reply" separately, skips reply/draft with explicit reason when reply body missing, and treats unchecked forward-target as skipped instead of unknown.
   - Done-file execution summary now renders markdown "Actions Taken" (human-readable) instead of raw JSON blob.
11. Gmail label-update MCP instruction normalized:
   - MCP prompt now maps to Gmail label tool semantics (`messageId`, `removeLabels`, `addLabels`) to reduce modify-label parameter mismatch.
   - Remaining "Requested entity was not found" failures still possible when message ID is stale/inaccessible in connected mailbox context.

---

## 🏗️ Key Architectural Decisions

### AD-001: MCP-first external email actions (2026-04-02)
**Decision:** Email actions are executed through MCP action files instead of direct API calls from skills.

**Why:** Silver requirement compliance, clearer separation of concerns, improved auditability.

**Impact:**
- Skills create MCP action files in `Needs_Action/`
- MCP processor executes actions and archives results
- External action trail is explicit and reviewable

### AD-002: Dedicated MCP processor (2026-04-02)
**Decision:** Keep MCP execution in `src/orchestrator/mcp_processor.py` and invoke via orchestrator loop.

**Why:** Isolation of integration logic, easier testing, extensible for additional MCP servers.

**Impact:** Complete end-to-end MCP workflow now functional.

### AD-003: LinkedIn API-first integration (2026-04-10 → 2026-04-11 validation)
**Decision:** Use official LinkedIn API + OAuth, not browser automation.

**Why:** Reliability, maintainability, security, production suitability.

**Impact:**
- OAuth token storage at `credentials/linkedin_api_token.json`
- Posting validated with live share
- Message monitoring removed from standard flow (Partner Program required)

---

## 🔧 Current Operational Capabilities

### Email
- Monitor unread Gmail messages
- Create actionable files for orchestrator
- Process actions: mark as read, archive, reply, delete
- Send email through skill flow with HITL guardrails

### LinkedIn
- OAuth authentication via setup script
- Text + image posting via official API v2
- Image URL: downloaded from public URL → uploaded via LinkedIn asset registration API
- Content-calendar based post workflow with AI-generated `image_prompt`
- Approval-gated publishing through vault folders

### Facebook
- Posts to FB Page via Meta Graph API v21.0
- Text posts (`/feed`) and photo posts (`/photos`) depending on whether `image_url` is present
- Page token read from `credentials/meta_api_token.json`; live API fallback

### Instagram
- Posts to Instagram Business account via container API
- Requires public `image_url` — auto-generated by `GenerateImageSkill` from calendar `image_prompt`

### Image Generation
- `generate_image.py` — Gemini `imagen-3.0-generate-001` → image bytes → catbox.moe upload (or Imgur if `IMGUR_CLIENT_ID` set)
- Called automatically by `content_calendar_watcher.py` for FB/IG/LI posts when `image_prompt` is present
- Returns public URL embedded in action file, flows through HITL → posting skill

### Twitter/X
- Auth verified (OAuth 1.0a via tweepy)
- Posting blocked by free API tier (402) — code correct, excluded from content calendar

### Odoo Accounting
- Revenue + expense reads via XML-RPC
- Draft invoice creation (HITL-gated, never auto-posts)
- MCP server configured (`odoo-mcp` npm package)
- CEO Briefing includes Odoo financial section

### Content Calendar
- `create_content_plan.py` → Gemini generates platform-specific copy + `image_prompt` for LI/FB/IG
- `content_calendar_watcher.py` picks up due posts, auto-generates images, creates action files
- Approval flow: `Needs_Action/` → human moves to `Approved/` → skill posts live

### System Management
- Multi-watcher lifecycle: filesystem, Gmail, LinkedIn, Twitter, Meta, content_calendar
- Restart limits + stale lock cleanup
- Logging and dashboard update support
- Scheduled jobs: cron active on Linux (orchestrator every 2m, briefing Monday 7 AM, calendar check daily noon)

---

## ⚠️ Known Constraints

1. LinkedIn direct message monitoring is not supported for standard app access (requires LinkedIn Partner Program).
2. Gmail MCP auth can drift/fail independently of local Gmail API token validity; startup preflight now detects this early, but runtime re-auth may still be required.
3. Windows Task Scheduler flow is not yet re-validated after Linux-side scheduler fixes (cron is validated and active).

---

## 🥇 Gold Tier Progress

**Plan file:** `GOLD_TIER_PLAN.md` — read this first each session to resume.  
**Last updated:** 2026-05-04

| Task | Phase | Status |
|---|---|---|
| Ralph Wiggum stop hook | 1.1 | `[x]` Complete |
| CEO Weekly Briefing skill | 1.2 | `[x]` Complete |
| Multiple MCP servers (filesystem) | 1.3 | `[x]` Complete |
| Error recovery hardening | 1.4 | `[x]` Complete |
| Twitter/X watcher + post skill | 2.1 | `[x]` Complete |
| Facebook + Instagram integration | 2.2 | `[x]` Complete |
| Cross-platform content calendar | 2.3 | `[x]` Complete |
| Odoo setup + MCP server | 3.1–3.2 | `[x]` Complete |
| Architecture docs | 4.1 | `[x]` Complete |
| Comprehensive audit logging | 4.2 | `[x]` Complete |

**Next action:** All Gold Tier tasks complete + image generation pipeline added. No remaining items.

---

## 📁 Key Files

### Watchers
- `src/watchers/gmail_watcher.py`
- `src/watchers/filesystem_watcher.py`
- `src/watchers/content_calendar_watcher.py` — unified social calendar watcher + image auto-gen
- `src/watchers/meta_watcher.py`
- `src/watchers/twitter_watcher.py`

### Orchestrator + MCP
- `src/orchestrator/orchestrator.py`
- `src/orchestrator/watcher_manager.py`
- `src/orchestrator/mcp_processor.py`

### Skills — Social
- `src/orchestrator/skills/post_linkedin.py` — text + image (URL → temp file → asset upload)
- `src/orchestrator/skills/post_facebook.py` — text or photo post depending on `image_url`
- `src/orchestrator/skills/post_instagram.py` — photo post (image_url required)
- `src/orchestrator/skills/post_twitter.py`
- `src/orchestrator/skills/linkedin_api_client.py`
- `src/orchestrator/skills/meta_api_client.py` — FB feed + photo + IG container APIs
- `src/orchestrator/skills/twitter_api_client.py`

### Skills — AI + Content
- `src/orchestrator/skills/generate_image.py` — Gemini Imagen → catbox/Imgur → public URL
- `src/orchestrator/skills/create_content_plan.py` — Gemini content + image_prompt for LI/FB/IG
- `src/orchestrator/skills/generate_ceo_briefing.py`

### Skills — Email + Orchestration
- `src/orchestrator/skills/send_email.py`
- `src/orchestrator/skills/process_email_actions.py`
- `src/orchestrator/skills/process_approved_actions.py`
- `src/orchestrator/skills/gmail_retry_handler.py`
- `src/orchestrator/skills/odoo_accounting.py`
- `src/orchestrator/skills/audit_logger.py`

### Config + Scripts
- `.env.example`
- `.mcp.json` — gmail + filesystem + odoo MCP servers
- `requirements.txt`
- `scripts/setup_linkedin_api.py`
- `scripts/setup_meta_api.py`
- `scripts/setup_cron.sh`
- `scripts/health_check.py`

### Core Docs
- `README.md`
- `QUICKSTART.md`
- `DEMO.md` — Gold Tier demo guide with exact commands
- `docs/status.md` — this file

---

## 🎯 Silver Requirements Check

| Requirement | Status |
|---|---|
| Two or more watcher scripts | ✅ |
| LinkedIn posting automation | ✅ |
| Plan creation capability | ✅ |
| Working MCP server for external action | ✅ |
| Human-in-the-loop approval workflow | ✅ |
| Basic scheduling setup | ✅ |
| AI functionality as skills | ✅ |

**Silver Tier:** ✅ Complete

---

*Status file intentionally compressed to keep only high-signal, operationally relevant information.*
