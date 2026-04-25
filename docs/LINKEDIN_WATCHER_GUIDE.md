# LinkedIn Watcher + API Testing Guide

## Overview

LinkedIn uses the **official LinkedIn API** (OAuth 2.0) for authentication and posting.

In Gold Tier, the LinkedIn-only watcher is replaced by `content_calendar_watcher.py` — a unified watcher that handles all platforms (LinkedIn, Twitter, Facebook, Instagram) from a single content calendar.

Current behavior:
- `content_calendar_watcher.py` checks `Content_Calendar/` for due posts across all platforms
- Creates approval requests per platform in `Pending_Approval/`
- Works with the HITL flow (`Pending_Approval` → `Approved` → publish)

> LinkedIn message monitoring is not supported with standard app access (requires LinkedIn Partner Program).

---

## Prerequisites

1. LinkedIn app configured at https://www.linkedin.com/developers/apps
2. Products enabled:
   - Share on LinkedIn
   - Sign In with LinkedIn using OpenID Connect
3. Redirect URI configured exactly:
   - `http://localhost:8000/callback`
4. `.env` values configured:

```bash
LINKEDIN_CLIENT_ID=your_client_id
LINKEDIN_CLIENT_SECRET=your_client_secret
LINKEDIN_REDIRECT_URI=http://localhost:8000/callback
LINKEDIN_TOKEN_PATH=./credentials/linkedin_api_token.json
LINKEDIN_CHECK_INTERVAL=300
```

---

## 1) Authenticate LinkedIn API

```bash
python scripts/setup_linkedin_api.py
```

Expected result:
- OAuth completes successfully
- Token file exists at `credentials/linkedin_api_token.json`

Verify:

```bash
ls -la credentials/linkedin_api_token.json
```

---

## 2) Validate Posting Skill (HITL)

Create a post request:

```bash
python -m src.orchestrator.skills.post_linkedin '{
  "action": "create_post",
  "content": "Testing LinkedIn API posting workflow from Personal AI Employee."
}'
```

Expected result:
- Approval request file created in `ai_employee_vault/Pending_Approval/`

Approve it:

```bash
mv ai_employee_vault/Pending_Approval/LINKEDIN_POST_*.md ai_employee_vault/Approved/
```

Then run orchestrator (or wait if already running) and confirm published output in logs.

---

## 3) Validate Watcher Calendar Flow

1. Create a scheduled post via skill (`schedule_post` action).
2. Run watcher or watcher manager.
3. Confirm watcher creates approval request for due calendar item.

---

## Troubleshooting

### `invalid_client`
- Confirm `LINKEDIN_CLIENT_ID` and `LINKEDIN_CLIENT_SECRET` are correct and from same app.
- Confirm redirect URI matches exactly: `http://localhost:8000/callback`.
- Re-run auth with a fresh code:
  ```bash
  python scripts/setup_linkedin_api.py
  ```

### Auth exchange inconsistent with PKCE
- Client now supports fallback retry without `code_verifier` when required by app behavior.
- Retry setup flow once with a fresh authorization code.

### Missing token file
```bash
python scripts/setup_linkedin_api.py
ls -la credentials/linkedin_api_token.json
```

---

## Recommended Regression Checks

- Auth setup succeeds and token persists
- Post creation request generates approval file
- Approved request publishes successfully
- Watcher/calendar check creates due approval requests

---

**Last Updated:** 2026-04-25
**Status:** API-first workflow active — unified cross-platform calendar watcher
