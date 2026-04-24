# Personal AI Employee - Project Status

**Last Updated:** 2026-04-24  
**Current Branch:** gold-imp  
**Target Tier:** Gold  
**Overall Status:** ✅ Silver complete. Gold tier in progress — 3/11 tasks done.

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
| Edge Cases | ✅ Complete | Retry logic, validation, lock cleanup, restart limits |
| Documentation | ✅ Updated | Core setup/testing docs aligned to API-first flow |

---

## ✅ Latest Confirmed Outcomes (2026-04-24)

1. **Filesystem MCP server integrated** (task 1.3):
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
- Text/link/image posting via official API
- Content-calendar based post workflow
- Approval-gated publishing through vault folders

### System Management
- Multi-watcher lifecycle management (watcher_manager for filesystem + Gmail + LinkedIn)
- Restart limits + stale lock cleanup
- Logging and dashboard update support
- Legacy dashboard static watcher lines auto-cleaned; live status shown in `## Watcher Status`
- Scheduled jobs support on Linux/macOS/Windows (cron active on Linux)

---

## ⚠️ Known Constraints

1. LinkedIn direct message monitoring is not supported for standard app access (requires LinkedIn Partner Program).
2. Gmail MCP auth can drift/fail independently of local Gmail API token validity; startup preflight now detects this early, but runtime re-auth may still be required.
3. Windows Task Scheduler flow is not yet re-validated after Linux-side scheduler fixes (cron is validated and active).

---

## 🥇 Gold Tier Progress

**Plan file:** `GOLD_TIER_PLAN.md` — read this first each session to resume.  
**Last updated:** 2026-04-24

| Task | Phase | Status |
|---|---|---|
| Ralph Wiggum stop hook | 1.1 | `[x]` Complete |
| CEO Weekly Briefing skill | 1.2 | `[x]` Complete |
| Multiple MCP servers (filesystem) | 1.3 | `[x]` Complete |
| Error recovery hardening | 1.4 | `[ ]` Not started |
| Twitter/X watcher + post skill | 2.1 | `[ ]` Not started |
| Facebook + Instagram integration | 2.2 | `[!]` Blocked — Meta app review needed |
| Cross-platform content calendar | 2.3 | `[ ]` Not started |
| Odoo setup + MCP server | 3.1–3.2 | `[ ]` Optional |
| Architecture docs | 4.1 | `[ ]` Not started |
| Comprehensive audit logging | 4.2 | `[ ]` Not started |

**Next action:** Start 1.4 Error recovery hardening. Also create Meta developer app NOW (approval takes days).

---

## 📋 Next Steps (Gold Tier)

> Full plan with file-level details: `GOLD_TIER_PLAN.md`

### Immediate — Phase 1 (start now)
1. **[1.1] Ralph Wiggum stop hook** — ✅ Done. `.claude/hooks/stop.sh` + `.claude/settings.json` + `scripts/start_ralph_wiggum.sh`.
2. **[1.2] CEO Weekly Briefing skill** — `src/orchestrator/skills/generate_ceo_briefing.py` reads Done/ + audit logs → writes `Briefings/YYYY-MM-DD_Monday_Briefing.md`. Add Monday 7 AM cron.
3. **[1.3] Multiple MCP servers** — add filesystem MCP to `.mcp.json`. Route `MCP_FILESYSTEM_*.json` action files in `mcp_processor.py`.
4. **[1.4] Error recovery hardening** — bounded retry on Gmail MCP preflight (3 attempts, 10s backoff). Queue outgoing actions on API-down. Add `scripts/health_check.py`.
5. **[META APP NOW]** — create Meta developer app at developers.facebook.com immediately. App review takes days and blocks Phase 2.2.

### Phase 2 — Social platforms (after Phase 1)
1. **[2.1] Twitter/X** — `pip install tweepy`, create `twitter_api_client.py` + `post_twitter.py` + `twitter_watcher.py`. HITL-gated posting.
2. **[2.2] Facebook + Instagram** — `meta_api_client.py` + posting skills + `meta_watcher.py`. Blocked on Meta app review.
3. **[2.3] Cross-platform calendar** — extend `create_content_plan.py` schema + calendar watcher routing for all platforms.

### Phase 3 — Odoo (optional)
- Docker-based Odoo Community 19 + `mcp-odoo-adv` MCP server + CEO Briefing revenue integration.

### Phase 4 — Polish
- `GOLD_TIER_COMPLETION.md` architecture docs + structured audit logging for all Gold actions.

---

## 📁 Key Files

### Watchers
- `src/watchers/gmail_watcher.py`
- `src/watchers/run_gmail_watcher.py`
- `src/watchers/linkedin_watcher.py`
- `src/watchers/run_linkedin_watcher.py`

### Orchestrator + MCP
- `src/orchestrator/orchestrator.py`
- `src/orchestrator/watcher_manager.py`
- `src/orchestrator/mcp_processor.py`

### Skills
- `src/orchestrator/skills/send_email.py`
- `src/orchestrator/skills/process_email_actions.py`
- `src/orchestrator/skills/process_approved_actions.py`
- `src/orchestrator/skills/post_linkedin.py`
- `src/orchestrator/skills/linkedin_api_client.py`
- `src/orchestrator/skills/gmail_retry_handler.py`

### Config + Scripts
- `.env.example`
- `requirements.txt`
- `scripts/setup_linkedin_api.py`
- `scripts/setup_cron.sh`
- `scripts/setup_task_scheduler.ps1`

### Core Docs
- `README.md`
- `QUICKSTART.md`
- `LINKEDIN_SETUP_QUICK_REF.md`
- `LINKEDIN_API_MIGRATION.md`
- `SILVER_TIER_TESTING_GUIDE.md`

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
