# Personal AI Employee - Project Status

**Last Updated:** 2026-04-22  
**Current Branch:** silver-imp  
**Target Tier:** Silver  
**Overall Status:** ✅ Silver requirements complete; approved-email MCP routing fixed; subprocess kill hardened to prevent orphan processes.

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

## ✅ Latest Confirmed Outcomes (2026-04-22)

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

## 📋 Next Steps (Prioritized)

### Immediate (2026-04-22 onward)
1. **Run strict HITL E2E drill** — place email in `Approved/` with Human Notes reply body, verify: MCP JSON created → Gmail MCP executes reply + mark_as_read → `Done/PROCESSED_*` + `Done/EXECUTED_MCP_*` artifacts present.
2. **Keep Gmail MCP startup preflight mandatory (no bypass)** — treat startup as failed if preflight fails.
3. **Add bounded retry/backoff in Gmail MCP preflight** — reduce false startup aborts from short-lived network blips.
4. **Stabilize `Needs_Action` drain for important/uncertain emails** — decide policy: keep, auto-route to `Pending_Approval`, or generate manual-review task. Prevent repeated "auto-processing completed" loops with unchanged review set.
5. **Dashboard truthfulness hardening** — surface MCP final execution outcomes from `Done/EXECUTED_MCP_*.json` separately from queue-time counts; add per-item action trace in Recent Activity.
6. **Publish incident runbook for transient Gmail MCP auth-refresh failures** — triage order: `gmail_get_profile` check → DNS/HTTPS → restart validation → re-auth steps.

### Follow-up
1. **LinkedIn regression checks**
   - Add/maintain tests for auth exchange path (including no-`code_verifier` fallback behavior).
   - Add smoke test for token refresh behavior in long-running flow.

2. **Cleanup + hardening**
   - Remove temporary auth artifacts (e.g., `credentials/linkedin_pkce_verifier.txt`) after confirmation.

3. **Windows scheduler parity check**
   - Re-validate `scripts/setup_task_scheduler.ps1` execution path after payload updates.

4. **Documentation maintenance**
   - Update docs to include project-level Gmail MCP setup/auth path caveat and verification commands.
   - Keep API-first LinkedIn guidance consistent across quickstart/testing/reference docs.
   - Ensure startup docs reference watcher_manager-based `start.sh`/`stop.sh` behavior.

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
