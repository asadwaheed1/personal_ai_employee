# Email Processing Workflow Guide

## Overview

The AI Employee can process emails from Gmail with two flexible workflows. Both support marking as read, archiving, replying, and deleting emails.

---

## Workflow 1: Direct Email File Editing (Recommended)

This is the simplest workflow - edit the email file directly and move it to Inbox.

### Step-by-Step

1. **Email arrives** → Gmail watcher creates file in `Needs_Action/`
   - Example: `EMAIL_20260401_141830_Subject.md`

2. **Review the email** → Open the file in `Needs_Action/`

3. **Check the actions** you want to execute:
   ```markdown
   ## Suggested Actions
   - [ ] Review email content
   - [x] Draft a reply if needed
   - [ ] Forward to relevant party if needed
   - [x] Mark as read in Gmail
   - [x] Archive after processing
   ```

4. **Add your reply** (if replying):
   ```markdown
   ## Human Notes
   Thanks for reaching out! I'll send you the report by end of day.
   ```

5. **Move to Inbox** → Drag the file from `Needs_Action/` to `Inbox/`

6. **Automatic processing** → Within 30 seconds (or immediately if orchestrator is running):
   - Actions executed in Gmail
   - Email file moved to `Done/` with execution summary
   - Dashboard updated

### Example

```markdown
---
type: email
message_id: 19ce2dd364b2189a
from: client@example.com
subject: "Project update request"
---

# Email: "Project update request"

## Sender Information
- **From**: client@example.com
- **Date**: 2026-04-01

## Snippet
Can you send me the latest project update?

## Suggested Actions
- [ ] Review email content
- [x] Draft a reply if needed    ← CHECKED
- [ ] Forward to relevant party
- [x] Mark as read in Gmail      ← CHECKED
- [x] Archive after processing   ← CHECKED

## Human Notes
Sure! The project is on track. Phase 1 complete, working on Phase 2. 
I'll send detailed update by EOD.

## Processing Notes
```

**Result**: Email marked as read, archived, and reply sent with your message.

---

## Workflow 2: Create Task File (Structured)

For more complex scenarios or when you want to keep the original email file unchanged.

### Step-by-Step

1. **Create a task file** in `Inbox/`:

```markdown
# Task: Process Client Email

## Email Reference
- **File**: ai_employee_vault/Needs_Action/EMAIL_20260401_141830_Subject.md
- **Message ID**: 19ce2dd364b2189a

## Actions Required
- [x] Mark as read in Gmail
- [x] Archive after processing
- [x] Reply to email

## Reply Content
Thanks for your email! I'll get back to you soon.

**Reply Subject**: Re: Original Subject

## Expected Output
Execute actions and move files to Done.
```

2. **Save and wait** → Orchestrator processes automatically

3. **Check results** → Both task file and email file moved to `Done/`

---

## Available Actions

| Action | Description | Requires |
|--------|-------------|----------|
| **Mark as read** | Removes UNREAD label in Gmail | Nothing |
| **Archive** | Removes INBOX label (archives) | Nothing |
| **Reply** | Sends reply email | Human Notes content |
| **Delete** | Moves to Gmail trash | Nothing |
| **Forward** | Forwards to another email | Not yet implemented |

---

## Reply Handling

When you check "Draft a reply" and add content to "Human Notes":

- **Your notes** are used as the reply body (sent as-is)
- **Subject** is automatically set to "Re: Original Subject"
- **Reply-To** is automatically extracted from the original sender
- **Thread** is preserved (reply appears in same conversation)

### Reply Example

**Your Human Notes:**
```
Thanks for your email! The project is going well. 
I'll send you a detailed update by end of day.
```

**What gets sent:**
- To: original-sender@example.com
- Subject: Re: Original Subject
- Body: Your exact text from Human Notes
- In-Reply-To: original-message-id (keeps thread)

---

## Tips & Best Practices

### For Reddit/Newsletter Notifications
```markdown
## Suggested Actions
- [x] Mark as read in Gmail
- [x] Archive after processing

## Human Notes
Just a notification, no action needed.
```

### For Client Emails Requiring Reply
```markdown
## Suggested Actions
- [x] Draft a reply if needed
- [x] Mark as read in Gmail
- [x] Archive after processing

## Human Notes
Hi [Name],

Thanks for reaching out! [Your response here]

Best regards,
[Your name]
```

### For Spam/Unwanted Emails
```markdown
## Suggested Actions
- [x] Delete from Gmail

## Human Notes
Spam email, deleting.
```

---

## Execution Flow

```
┌─────────────────────┐
│  Gmail Watcher      │
│  Detects new email  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Needs_Action/      │
│  EMAIL_xxx.md       │
└──────────┬──────────┘
           │
           │ (You edit & check boxes)
           │
           ▼
┌─────────────────────┐
│  Move to Inbox/     │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Orchestrator       │
│  Detects file       │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  process_email_     │
│  actions.py         │
│  - Parse actions    │
│  - Execute Gmail API│
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Gmail Actions      │
│  - Mark as read     │
│  - Archive          │
│  - Send reply       │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Done/              │
│  PROCESSED_xxx.md   │
│  (with summary)     │
└─────────────────────┘
```

---

## Troubleshooting

### Email not processing
- Check file is in `Inbox/` (not `Needs_Action/`)
- Verify orchestrator is running
- Check logs in `Logs/` folder

### Actions failed
- Verify Gmail token exists: `credentials/gmail_token.json`
- Check Gmail API permissions
- Review execution summary in `Done/` folder

### Reply not sent
- Ensure "Draft a reply" is checked
- Verify Human Notes section has content
- Check Gmail send permissions

---

## Command Line Usage

You can also process emails directly via command line:

```bash
# Process email file directly
python -m src.orchestrator.skills.process_email_actions \
  '{"email_file": "ai_employee_vault/Inbox/EMAIL_xxx.md"}'

# Process via task file
python -m src.orchestrator.skills.process_email_actions \
  '{"task_file": "ai_employee_vault/Inbox/task.md"}'

# Specific actions
python -m src.orchestrator.skills.process_email_actions \
  '{"email_file": "ai_employee_vault/Needs_Action/EMAIL_xxx.md", 
    "actions": ["mark_as_read", "archive"]}'
```

---

## Files & Locations

| File | Purpose |
|------|---------|
| `src/orchestrator/skills/process_email_actions.py` | Main skill |
| `src/watchers/gmail_watcher.py` | Email detection |
| `credentials/gmail_token.json` | Gmail API token |
| `Needs_Action/EMAIL_*.md` | Incoming emails |
| `Inbox/` | Files ready to process |
| `Done/PROCESSED_*.md` | Completed emails |

---

## Audit Logging

All email actions (mark_as_read, archive, reply, delete) produce structured audit entries in `Logs/audit_master.json` via the Gold Tier audit logger.

---

**Last Updated**: 2026-04-25
