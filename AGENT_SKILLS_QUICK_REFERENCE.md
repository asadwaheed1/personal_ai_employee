# Agent Skills Quick Reference

**Version:** 3.0-gold | **Last Updated:** 2026-04-25

All AI functionality is implemented as Agent Skills. Skills accept JSON params and return `{"success": bool, "result": {...}, "timestamp": "..."}`.

---

## Bronze Tier Skills

| Skill | Purpose |
|-------|---------|
| `process_needs_action` | Process files in Needs_Action |
| `update_dashboard` | Update Dashboard.md status |
| `create_plan` | Generate structured action plans |
| `create_approval_request` | Create HITL approval requests |
| `parse_watcher_file` | Extract metadata from watcher files |
| `process_inbox` | Process files in Inbox |
| `process_approved_actions` | Execute approved actions |

---

## Silver Tier Skills

| Skill | Purpose |
|-------|---------|
| `send_email` | Send email via Gmail MCP |
| `process_email_actions` | Parse email file → create MCP action files |
| `post_linkedin` | LinkedIn posting with HITL approval |
| `linkedin_api_client` | LinkedIn API OAuth + posting client |
| `create_content_plan` | Cross-platform content calendar |
| `gmail_retry_handler` | Retry decorator for transient Gmail errors |

---

## Gold Tier Skills

| Skill | Purpose |
|-------|---------|
| `post_twitter` | Twitter/X posting with HITL approval |
| `twitter_api_client` | Tweepy client (API v2 + v1.1 media) |
| `post_facebook` | Facebook Page posting with HITL approval |
| `post_instagram` | Instagram Business posting with HITL approval |
| `meta_api_client` | Meta Graph API v21.0 client |
| `odoo_accounting` | Odoo ERP revenue/expense/invoice via XML-RPC |
| `generate_ceo_briefing` | CEO Weekly Briefing with Odoo financials |
| `audit_logger` | Structured JSON audit logging for all external actions |

---

## Usage Examples

### Post to LinkedIn (HITL)
```bash
python -m src.orchestrator.skills.post_linkedin '{
  "action": "create_post",
  "content": "Post text here #automation"
}'
# Move Pending_Approval/LINKEDIN_POST_*.md → Approved/ to publish
```

### Post to Twitter/X (HITL)
```bash
python -m src.orchestrator.skills.post_twitter '{
  "action": "create_post",
  "content": "Tweet text here (max 280 chars)"
}'
```

### Post to Facebook (HITL)
```bash
python -m src.orchestrator.skills.post_facebook '{
  "action": "create_post",
  "content": "Facebook post text"
}'
```

### Post to Instagram (HITL — needs public image URL)
```bash
python -m src.orchestrator.skills.post_instagram '{
  "action": "create_post",
  "caption": "Caption here",
  "image_url": "https://example.com/image.jpg"
}'
```

### Cross-Platform Content Calendar
```bash
python src/orchestrator/skills/create_content_plan.py
# Generates JSON + MD files in Content_Calendar/ for LI/TW/FB/IG
# content_calendar_watcher.py picks them up at scheduled time
```

### Odoo Revenue Query
```python
from src.orchestrator.skills.odoo_accounting import OdooAccountingSkill
skill = OdooAccountingSkill('./ai_employee_vault')
result = skill.get_revenue_summary(date_from='2026-04-01', date_to='2026-04-30')
```

### Create Draft Invoice (HITL)
```python
result = skill.create_draft_invoice(
    partner_id=...,
    lines=[{"name": "Service", "price_unit": 1500.0, "quantity": 1}]
)
# Creates DRAFT only — writes approval file to Pending_Approval/
```

### Generate CEO Briefing
```bash
python src/orchestrator/skills/generate_ceo_briefing.py ./ai_employee_vault
# Writes to ai_employee_vault/Briefings/YYYY-MM-DD_Monday_Briefing.md
```

### Audit Logger (used internally by all skills)
```python
from src.orchestrator.skills.audit_logger import AuditLogger
logger = AuditLogger('./ai_employee_vault')
logger.log_action(
    platform='twitter',
    action='post_tweet',
    status='success',
    details={'tweet_id': '...'}
)
# Appends to Logs/audit_YYYY-MM-DD.json + Logs/audit_master.json
```

### Process Email Actions
```bash
python -m src.orchestrator.skills.process_email_actions '{
  "email_file": "ai_employee_vault/Needs_Action/EMAIL_xxx.md"
}'
```

### Update Dashboard
```bash
python src/orchestrator/skills/update_dashboard.py '{
  "vault_path": "/path/to/vault",
  "activity_log": "Task completed",
  "status": "operational"
}'
```

---

## Skill Manifest

```
.claude/tools/bronze_tier_skills.json   # Skills manifest

src/orchestrator/skills/
├── base_skill.py                       # Base class + _log_audit helper
├── audit_logger.py                     # Gold: structured audit logging
├── generate_ceo_briefing.py            # Gold: CEO Weekly Briefing
├── odoo_accounting.py                  # Gold: Odoo ERP integration
├── post_twitter.py                     # Gold: Twitter/X posting
├── twitter_api_client.py               # Gold: Tweepy client
├── post_facebook.py                    # Gold: Facebook posting
├── post_instagram.py                   # Gold: Instagram posting
├── meta_api_client.py                  # Gold: Meta Graph API client
├── post_linkedin.py                    # Silver: LinkedIn posting
├── linkedin_api_client.py              # Silver: LinkedIn API client
├── send_email.py                       # Silver: email sending
├── process_email_actions.py            # Silver: email parsing + MCP routing
├── create_content_plan.py              # Silver/Gold: content calendar
├── gmail_retry_handler.py              # Silver: Gmail retry decorator
├── process_needs_action.py             # Bronze: process queue
├── update_dashboard.py                 # Bronze: dashboard updates
├── create_plan.py                      # Bronze: action plans
├── create_approval_request.py          # Bronze: HITL requests
├── parse_watcher_file.py               # Bronze: parse watcher output
├── process_inbox.py                    # Bronze: inbox processing
└── process_approved_actions.py         # Bronze: execute approved
```

---

## BaseSkill Pattern

```python
from src.orchestrator.skills.base_skill import BaseSkill

class MySkill(BaseSkill):
    def execute(self, params):
        # All skills have access to:
        # self.vault_path     — Path to vault
        # self._log_audit(...)  — Write structured audit entry
        # self.logger         — Standard Python logger
        pass
```

---

## Full Documentation

See `AGENT_SKILLS_DOCUMENTATION.md` for complete schema reference.
