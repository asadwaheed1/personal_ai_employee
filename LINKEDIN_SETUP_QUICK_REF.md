# LinkedIn API Setup - Quick Reference

## Current Status
- ✅ LinkedIn OAuth authentication working
- ✅ Token saved at `credentials/linkedin_api_token.json`
- ✅ Live API post validated successfully
- ✅ `linkedin_api_client.py` token exchange supports fallback when PKCE verifier is rejected

---

## Confirmed Setup

### 1) LinkedIn Developer App
In https://www.linkedin.com/developers/apps, ensure:
- Product: **Share on LinkedIn**
- Product: **Sign In with LinkedIn using OpenID Connect**
- Redirect URI: `http://localhost:8000/callback`

### 2) `.env` Configuration
```bash
LINKEDIN_CLIENT_ID=your_client_id
LINKEDIN_CLIENT_SECRET=your_client_secret
LINKEDIN_REDIRECT_URI=http://localhost:8000/callback
LINKEDIN_TOKEN_PATH=./credentials/linkedin_api_token.json
```

### 3) Run OAuth Setup
```bash
python scripts/setup_linkedin_api.py
```

After successful auth, token is persisted to:
- `credentials/linkedin_api_token.json`

---

## Validate Posting

### Create post request (approval workflow)
```bash
python -m src.orchestrator.skills.post_linkedin '{
  "action": "create_post",
  "content": "Hello from my AI Employee! #automation #ai"
}'
```

Move generated approval file from `Pending_Approval/` to `Approved/` to publish.

---

## Troubleshooting

### `invalid_client`
- Re-check `LINKEDIN_CLIENT_ID` and `LINKEDIN_CLIENT_SECRET`
- Confirm both credentials belong to the same LinkedIn app
- Ensure redirect URI matches exactly: `http://localhost:8000/callback`

### Auth code exchange issues with PKCE
- Client now retries token exchange without `code_verifier` automatically if needed
- If auth still fails, rerun:
  ```bash
  python scripts/setup_linkedin_api.py
  ```

### Token missing or expired
```bash
ls -la credentials/linkedin_api_token.json
python scripts/setup_linkedin_api.py
```

---

## Notes
- LinkedIn message monitoring is not supported through standard API access.
- Current LinkedIn watcher is focused on content calendar + posting workflow.

---

**Last Updated:** 2026-04-11
**Status:** Authenticated and validated
