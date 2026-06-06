# AI Employee — Gold Tier Quick Start

**Version:** 3.0-gold | **Time:** ~45 minutes

---

## Prerequisites

- Python 3.10+
- Claude Code CLI installed
- Linux or macOS (Windows: WSL)
- Gmail account with API access
- LinkedIn developer app
- Twitter/X developer account (optional)
- Meta developer app — Facebook + Instagram (optional)
- Docker (for Odoo ERP, optional)

---

## 1. Install & Setup

```bash
cd /home/asad/piaic/projects/personal_ai_employee

chmod +x setup.sh start.sh stop.sh scripts/*.sh

./setup.sh

pip install -r requirements.txt
```

---

## 2. Configure Environment

```bash
cp .env.example .env
nano .env
```

Minimum required `.env` values:

```bash
# Gmail
GMAIL_CREDENTIALS_PATH=credentials/gmail_credentials.json
GMAIL_TOKEN_PATH=credentials/gmail_token.json

# LinkedIn
LINKEDIN_CLIENT_ID=your_client_id
LINKEDIN_CLIENT_SECRET=your_client_secret
LINKEDIN_REDIRECT_URI=http://localhost:8000/callback
LINKEDIN_TOKEN_PATH=./credentials/linkedin_api_token.json

# Twitter/X
TWITTER_API_KEY=your_api_key
TWITTER_API_SECRET=your_api_secret
TWITTER_ACCESS_TOKEN=your_access_token
TWITTER_ACCESS_SECRET=your_access_secret
TWITTER_BEARER_TOKEN=your_bearer_token

# Meta (Facebook + Instagram)
META_ACCESS_TOKEN=your_long_lived_page_token
META_PAGE_ID=your_facebook_page_id
INSTAGRAM_BUSINESS_ACCOUNT_ID=your_ig_business_id

# Odoo (optional)
ODOO_URL=http://localhost:8069
ODOO_DB=odoo
ODOO_USERNAME=admin
ODOO_PASSWORD=admin

# System
CHECK_INTERVAL=120
MAX_ITERATIONS=10
```

---

## 3. Setup Gmail API

1. Go to https://console.cloud.google.com/apis/credentials
2. Create OAuth 2.0 Client ID
3. Download JSON → save as `credentials/gmail_credentials.json`
4. Enable Gmail API on the project

```bash
mkdir -p credentials
# Save downloaded file as credentials/gmail_credentials.json

# First-time OAuth (opens browser)
python -m src.watchers.run_gmail_watcher ./ai_employee_vault
# Token saved to credentials/gmail_token.json
```

---

## 4. Setup LinkedIn OAuth

```bash
python scripts/setup_linkedin_api.py
# Completes OAuth in browser → saves credentials/linkedin_api_token.json
```

**LinkedIn app requires:**
- Product: Share on LinkedIn
- Product: Sign In with LinkedIn using OpenID Connect
- Redirect URI: `http://localhost:8000/callback`

---

## 5. Setup Meta (Facebook + Instagram)

```bash
python scripts/setup_meta_api.py
# Interactive setup for long-lived token + Page/IG ID discovery
# Saves credentials/meta_api_token.json
```

**Meta app requires:**
- Permissions: `pages_manage_posts`, `instagram_basic`, `instagram_content_publish`
- App must be in development mode or approved for production

---

## 6. Setup Twitter/X

Add keys to `.env` from https://developer.twitter.com/en/portal/dashboard:

```bash
TWITTER_API_KEY=...
TWITTER_API_SECRET=...
TWITTER_ACCESS_TOKEN=...
TWITTER_ACCESS_SECRET=...
TWITTER_BEARER_TOKEN=...
```

> Free API tier blocks posting (402). Basic tier ($100/mo) or higher required for tweet posting.

---

## 7. Setup Odoo (Optional)

```bash
cd docker
docker-compose up -d
# Odoo available at http://localhost:8069 (admin/admin)
# Wait ~60s for first-time DB initialization
cd ..
```

---

## 8. Setup Cron

```bash
./scripts/setup_cron.sh
crontab -l  # Verify jobs installed
```

Installs:
- `*/30 * * * *` — orchestrator check cycle
- `0 7 * * 1` — CEO Weekly Briefing (Monday 7 AM)

---

## 9. Start the System

```bash
./start.sh
```

Expected output:
```
=== Starting AI Employee System (Gold Tier) ===
Starting Watcher Manager...
✓ Watcher Manager started (PID: XXXX)
Starting Orchestrator...
✓ Orchestrator started (PID: XXXX)
System is now running!
```

---

## 10. Verify Health

```bash
python scripts/health_check.py
```

Expected: Gmail MCP ✅, LinkedIn API ✅, Meta API ✅

---

## 11. Test Core Workflows

### Test 1: File Processing (Bronze)

```bash
cat > ai_employee_vault/Inbox/test_task.md << 'EOF'
---
type: task
priority: medium
---
# Test Task
Update the dashboard with a test activity entry.
EOF
```

Wait 30 seconds → check `ai_employee_vault/Done/` and `Dashboard.md`.

### Test 2: Email Processing (Silver)

```bash
# Check detected emails
ls ai_employee_vault/Needs_Action/EMAIL_*.md

# Edit one — check desired actions, add Human Notes, then:
mv ai_employee_vault/Needs_Action/EMAIL_*.md ai_employee_vault/Inbox/
python src/orchestrator/mcp_processor.py ./ai_employee_vault
```

### Test 3: LinkedIn Post (Gold)

```bash
python -m src.orchestrator.skills.post_linkedin '{
  "action": "create_post",
  "content": "Testing Gold Tier AI Employee! #automation #ai"
}'

# Approve it
mv ai_employee_vault/Pending_Approval/LINKEDIN_POST_*.md ai_employee_vault/Approved/
```

### Test 4: Content Calendar (Gold)

```bash
python src/orchestrator/skills/create_content_plan.py
ls ai_employee_vault/Content_Calendar/
# content_calendar_watcher.py picks up scheduled posts at their due time
```

### Test 5: CEO Briefing (Gold)

```bash
python src/orchestrator/skills/generate_ceo_briefing.py ./ai_employee_vault
ls ai_employee_vault/Briefings/
```

### Test 6: Odoo Revenue (Gold)

```bash
python -c "
import sys; sys.path.insert(0, '.')
from src.orchestrator.skills.odoo_accounting import OdooAccountingSkill
skill = OdooAccountingSkill('./ai_employee_vault')
result = skill.get_revenue_summary('2026-04-01', '2026-04-30')
print(result)
"
```

---

## 12. Monitor the System

```bash
# Live logs
tail -f ai_employee_vault/Logs/orchestrator_$(date +%Y-%m-%d).log
tail -f ai_employee_vault/Logs/gmail_watcher_$(date +%Y-%m-%d).log

# Dashboard
cat ai_employee_vault/Dashboard.md

# Audit trail
cat ai_employee_vault/Logs/audit_master.json | python -m json.tool | tail -60
```

---

## Stopping

```bash
./stop.sh
```

---

## Troubleshooting

### Gmail not detecting emails
```bash
ls -la credentials/gmail_token.json
# If missing: re-run gmail watcher for OAuth
python -m src.watchers.run_gmail_watcher ./ai_employee_vault
```

### MCP actions not executing
```bash
tail -50 ai_employee_vault/Logs/mcp_processor_$(date +%Y-%m-%d).log
python src/orchestrator/mcp_processor.py ./ai_employee_vault
```

### LinkedIn auth expired
```bash
python scripts/setup_linkedin_api.py
```

### Meta token invalid
```bash
python scripts/setup_meta_api.py
```

### Odoo connection refused
```bash
cd docker && docker-compose ps
cd docker && docker-compose up -d
```

### Files stuck in Inbox
```bash
rm -f ai_employee_vault/.state/processing.lock
./stop.sh && ./start.sh
```

### Watchers not running
```bash
python src/orchestrator/watcher_manager.py ./ai_employee_vault stop
python src/orchestrator/watcher_manager.py ./ai_employee_vault start
python src/orchestrator/watcher_manager.py ./ai_employee_vault status
```

---

## Success Checklist

- [ ] `./start.sh` runs without errors
- [ ] `python scripts/health_check.py` shows all green
- [ ] File in Inbox moves to Done within 60 seconds
- [ ] Gmail watcher creates `EMAIL_*.md` files in Needs_Action
- [ ] LinkedIn post request lands in Pending_Approval
- [ ] CEO briefing generates with Odoo financial section
- [ ] Audit entries appear in `Logs/audit_master.json`
- [ ] `crontab -l` shows CEO Briefing + orchestrator jobs

---

Gold Tier AI Employee is operational. See `QUICK_REFERENCE.md` for day-to-day commands.
