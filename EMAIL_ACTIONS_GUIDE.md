# Email Actions Guide

This guide shows how to perform actions on emails in `Needs_Action/` folder.

## Overview

The `process_email_actions.py` skill allows you to:
- Mark emails as read in Gmail
- Archive emails (remove from inbox)
- Reply to emails
- Delete emails (move to trash)

## Method 1: Create a Task File (Recommended)

Create a new markdown file in `Inbox/` with the following format:

```markdown
# Task: Process Email

## Email Reference
- **File**: EMAIL_20260401_141817_Claud_is_robbing_people_with_their_usage_limit.md
- **Message ID**: 19d35448e3b3565c

## Actions Required
- [x] Mark as read in Gmail
- [x] Archive after processing
- [ ] Reply to email
- [ ] Delete from Gmail

## Reply Content
Your reply message here (only if Reply is checked).

**Reply Subject**: Re: Subject

## Expected Output
Execute actions and move email file to Done.
```

Drop this in `Inbox/` and the orchestrator will process it automatically.

## Method 2: Direct Command Line

Execute actions directly:

```bash
# Mark as read and archive
python -m src.orchestrator.skills.process_email_actions '{"email_file": "ai_employee_vault/Needs_Action/EMAIL_xxx.md", "actions": ["mark_as_read", "archive"]}'

# Reply to email
python -m src.orchestrator.skills.process_email_actions '{"email_file": "ai_employee_vault/Needs_Action/EMAIL_xxx.md", "actions": ["reply"], "reply_body": "Thanks for your email!", "reply_subject": "Re: Original Subject"}'

# Process via task file
python -m src.orchestrator.skills.process_email_actions '{"task_file": "ai_employee_vault/Inbox/my_task.md"}'
```

## Available Actions

| Action | Description |
|--------|-------------|
| `mark_as_read` | Removes UNREAD label in Gmail |
| `archive` | Removes INBOX label in Gmail |
| `reply` | Sends a reply email (requires `reply_body`) |
| `delete` | Moves email to Gmail trash |

## How It Works

1. **Detection**: Place task file in `Inbox/`
2. **Processing**: Orchestrator detects file and triggers skill
3. **Execution**: Skill reads email metadata and executes Gmail API actions
4. **Cleanup**: Email file moved to `Done/`, task file archived
5. **Logging**: Activity logged and Dashboard updated

## Example Workflow

1. Gmail watcher detects new email → Creates `Needs_Action/EMAIL_xxx.md`
2. You review email and decide actions
3. Create task file in `Inbox/` with actions checked
4. Orchestrator processes within 30 seconds
5. Email actions executed in Gmail
6. Files moved to `Done/`

## Notes

- Requires Gmail token from watcher setup
- Replies are sent as plain text
- Original email sender is automatically extracted for replies
- Failed actions are logged but don't block other actions
