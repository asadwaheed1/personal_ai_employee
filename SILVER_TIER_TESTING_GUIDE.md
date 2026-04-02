# Silver Tier Testing Guide

**Date**: 2026-04-02
**Status**: Ready for Testing
**Branch**: silver-imp

---

## 🎯 Overview

This guide provides step-by-step instructions for testing all Silver Tier components, including the newly implemented MCP processor and edge case handling.

---

## 📋 Pre-Testing Checklist

### 1. Environment Setup

```bash
# Ensure you're on the correct branch
git checkout silver-imp

# Pull latest changes
git pull origin silver-imp

# Install/update dependencies
pip install -r requirements.txt

# Verify Claude Code is installed
claude --version
```

### 2. Configuration Verification

```bash
# Check .env file exists and is configured
cat .env | grep -E "GMAIL|LINKEDIN"

# Verify Gmail credentials exist
ls -la credentials/gmail_credentials.json
ls -la credentials/gmail_token.json

# Verify vault structure
ls -la ai_employee_vault/
```

---

## 🧪 Test Suite

### Test 1: MCP Processor - Basic Functionality

**Objective**: Verify MCP processor can detect and process MCP action files

**Steps**:

1. Create a test MCP action file:
```bash
cat > ai_employee_vault/Needs_Action/MCP_EMAIL_test_$(date +%Y%m%d_%H%M%S).json <<'EOF'
{
  "mcp_server": "gmail",
  "tool": "send_email",
  "timestamp": "2026-04-02T07:00:00Z",
  "status": "pending",
  "params": {
    "to": "test@example.com",
    "subject": "MCP Test Email",
    "body": "This is a test email sent via MCP processor."
  },
  "result": null,
  "executed_at": null
}
EOF
```

2. Run MCP processor manually:
```bash
python src/orchestrator/mcp_processor.py ./ai_employee_vault
```

3. Verify results:
```bash
# Check for processed file in Done folder
ls -la ai_employee_vault/Done/EXECUTED_MCP_EMAIL_test_*

# View the result
cat ai_employee_vault/Done/EXECUTED_MCP_EMAIL_test_*.json | jq
```

**Expected Result**:
- File moved from Needs_Action to Done
- File renamed with EXECUTED_ prefix
- Result field populated with execution status
- executed_at timestamp added
- Status changed to "completed" or "failed"

---

### Test 2: Email Validation

**Objective**: Verify email validation catches invalid inputs

**Test 2.1: Invalid Email Format**
```bash
python -m src.orchestrator.skills.send_email '{
  "to": "invalid-email-format",
  "subject": "Test",
  "body": "Test body"
}'
```

**Expected**: ValueError: Invalid email address

**Test 2.2: Empty Body**
```bash
python -m src.orchestrator.skills.send_email '{
  "to": "test@example.com",
  "subject": "Test",
  "body": "   "
}'
```

**Expected**: ValueError: Email body is required and cannot be empty

**Test 2.3: Invalid CC Email**
```bash
python -m src.orchestrator.skills.send_email '{
  "to": "test@example.com",
  "cc": ["invalid-cc"],
  "subject": "Test",
  "body": "Test body"
}'
```

**Expected**: ValueError: Invalid CC email address

---

### Test 3: Attachment Handling

**Objective**: Verify attachment validation and size limits

**Test 3.1: Non-existent Attachment**
```bash
python -m src.orchestrator.skills.send_email '{
  "to": "test@example.com",
  "subject": "Test with Attachment",
  "body": "Test body",
  "attachments": ["/nonexistent/file.pdf"]
}'
```

**Expected**: Warning logged, attachment removed, email still sent

**Test 3.2: Large Attachment (if you have a test file)**
```bash
# Create a 30MB test file
dd if=/dev/zero of=/tmp/large_file.bin bs=1M count=30

python -m src.orchestrator.skills.send_email '{
  "to": "test@example.com",
  "subject": "Test with Large Attachment",
  "body": "Test body",
  "attachments": ["/tmp/large_file.bin"]
}'
```

**Expected**: Warning logged, attachment skipped (exceeds 25MB limit)

---

### Test 4: Orchestrator MCP Integration

**Objective**: Verify orchestrator detects and processes MCP actions automatically

**Steps**:

1. Create multiple test MCP action files:
```bash
for i in {1..3}; do
  cat > ai_employee_vault/Needs_Action/MCP_EMAIL_test_${i}_$(date +%Y%m%d_%H%M%S).json <<EOF
{
  "mcp_server": "gmail",
  "tool": "modify_email",
  "timestamp": "$(date -Iseconds)",
  "status": "pending",
  "params": {
    "message_id": "test_message_${i}",
    "removeLabelIds": ["UNREAD"]
  },
  "result": null,
  "executed_at": null
}
EOF
  sleep 1
done
```

2. Start orchestrator:
```bash
python src/orchestrator/orchestrator.py ./ai_employee_vault 10
```

3. Monitor logs:
```bash
# In another terminal
tail -f ai_employee_vault/Logs/orchestrator_$(date +%Y-%m-%d).log
tail -f ai_employee_vault/Logs/mcp_processor_$(date +%Y-%m-%d).log
```

4. Wait 10-15 seconds, then check results:
```bash
ls -la ai_employee_vault/Done/EXECUTED_MCP_*
```

**Expected Result**:
- Orchestrator detects MCP action files
- MCP processor executes them
- Files moved to Done with results
- Logs show processing activity

---

### Test 5: Retry Logic

**Objective**: Verify Gmail retry handler works (requires mock or real API)

**Note**: This test requires actual Gmail API interaction or mocking

**Manual Test**:
1. Temporarily disable network to simulate failure
2. Attempt to send email
3. Re-enable network
4. Verify retry succeeds

**Expected**: Automatic retry with exponential backoff

---

### Test 6: Stale Lock Cleanup

**Objective**: Verify orchestrator cleans up stale locks

**Steps**:

1. Create a stale lock file:
```bash
mkdir -p ai_employee_vault/.state
echo "2026-04-01T00:00:00Z" > ai_employee_vault/.state/processing.lock
# Make it old
touch -t 202604010000 ai_employee_vault/.state/processing.lock
```

2. Start orchestrator:
```bash
python src/orchestrator/orchestrator.py ./ai_employee_vault 10
```

3. Check logs:
```bash
grep "Stale lock" ai_employee_vault/Logs/orchestrator_$(date +%Y-%m-%d).log
```

**Expected Result**:
- Log message: "Stale lock file detected"
- Lock file removed
- Orchestrator acquires new lock

---

### Test 7: Watcher Manager Restart Limits

**Objective**: Verify watcher manager prevents infinite restart loops

**Steps**:

1. Create a failing watcher script:
```bash
cat > /tmp/failing_watcher.py <<'EOF'
#!/usr/bin/env python3
import sys
print("Starting watcher...")
sys.exit(1)  # Immediately fail
EOF
chmod +x /tmp/failing_watcher.py
```

2. Modify watcher_manager.py temporarily to add this watcher:
```python
manager.register_watcher(
    'test_failing_watcher',
    [sys.executable, '/tmp/failing_watcher.py']
)
```

3. Start watcher manager:
```bash
python src/orchestrator/watcher_manager.py ./ai_employee_vault start
```

4. Monitor logs:
```bash
tail -f ai_employee_vault/Logs/watcher_manager_$(date +%Y-%m-%d).log
```

**Expected Result**:
- Watcher restarts up to 10 times
- After 10 restarts, status changes to "failed_max_restarts"
- No more restart attempts
- Log message: "exceeded max restarts"

---

### Test 8: Email Processing Workflow (End-to-End)

**Objective**: Test complete email processing workflow with MCP

**Steps**:

1. Create a test email file:
```bash
cat > ai_employee_vault/Needs_Action/EMAIL_test_$(date +%Y%m%d_%H%M%S).md <<'EOF'
---
type: email
message_id: test_message_12345
thread_id: test_thread_12345
priority: medium
---

# Email: Test Subject

## Email Details
- **From**: sender@example.com
- **To**: you@example.com
- **Subject**: Test Subject
- **Date**: 2026-04-02

## Email Body
This is a test email body.

## Suggested Actions
- [x] Mark as read
- [x] Archive
- [ ] Reply
- [ ] Delete

## Human Notes
(Add your notes here)
EOF
```

2. Process the email:
```bash
python -m src.orchestrator.skills.process_email_actions '{
  "email_file": "ai_employee_vault/Needs_Action/EMAIL_test_*.md"
}'
```

3. Verify MCP actions created:
```bash
ls -la ai_employee_vault/Needs_Action/MCP_EMAIL_mark_as_read_*
ls -la ai_employee_vault/Needs_Action/MCP_EMAIL_archive_*
```

4. Run MCP processor:
```bash
python src/orchestrator/mcp_processor.py ./ai_employee_vault
```

5. Verify results:
```bash
ls -la ai_employee_vault/Done/EXECUTED_MCP_EMAIL_*
ls -la ai_employee_vault/Done/PROCESSED_EMAIL_test_*
```

**Expected Result**:
- Email file processed
- MCP action files created for mark_as_read and archive
- MCP actions executed
- All files moved to Done
- Execution summary added to email file

---

### Test 9: Integration Test (Full System)

**Objective**: Test complete system with all components running

**Steps**:

1. Start all components:
```bash
# Terminal 1: Orchestrator
python src/orchestrator/orchestrator.py ./ai_employee_vault 30

# Terminal 2: Watcher Manager (if using watchers)
python src/orchestrator/watcher_manager.py ./ai_employee_vault start

# Terminal 3: Monitor logs
tail -f ai_employee_vault/Logs/*.log
```

2. Drop a test task in Inbox:
```bash
cat > ai_employee_vault/Inbox/test_task_$(date +%Y%m%d_%H%M%S).md <<'EOF'
# Task: Send Test Email

## Task Type
Email

## Priority
Medium

## Description
Send a test email to verify the system is working.

## Details
- To: test@example.com
- Subject: System Test
- Body: This is a test email from the AI Employee system.

---
*Created: 2026-04-02*
*Status: Pending*
EOF
```

3. Wait 30-60 seconds and monitor:
```bash
# Check if file moved
ls -la ai_employee_vault/Inbox/
ls -la ai_employee_vault/Done/

# Check for MCP actions
ls -la ai_employee_vault/Needs_Action/MCP_*

# Check Dashboard
cat ai_employee_vault/Dashboard.md
```

**Expected Result**:
- Task file detected by orchestrator
- Claude processes the task
- MCP action file created (if email requires sending)
- MCP processor executes the action
- All files moved to Done
- Dashboard updated

---

## 🔍 Verification Checklist

After running tests, verify:

- [ ] MCP processor detects and processes MCP action files
- [ ] Email validation catches invalid inputs
- [ ] Attachment validation works (existence, size limits)
- [ ] Orchestrator integrates with MCP processor
- [ ] Retry logic handles failures gracefully
- [ ] Stale locks are cleaned up automatically
- [ ] Watcher manager prevents infinite restarts
- [ ] Email processing workflow creates MCP actions
- [ ] End-to-end integration works smoothly
- [ ] All logs are created and contain expected entries
- [ ] Dashboard updates correctly
- [ ] No errors in logs (except expected validation errors)

---

## 🐛 Troubleshooting

### MCP Processor Not Finding Files

**Issue**: MCP processor reports 0 files found

**Solution**:
```bash
# Check file naming
ls -la ai_employee_vault/Needs_Action/MCP_*.json

# Verify JSON format
cat ai_employee_vault/Needs_Action/MCP_*.json | jq
```

### Orchestrator Not Processing MCP Actions

**Issue**: MCP actions remain in Needs_Action

**Solution**:
```bash
# Check orchestrator logs
tail -50 ai_employee_vault/Logs/orchestrator_$(date +%Y-%m-%d).log

# Verify MCP processor import
python -c "from src.orchestrator.mcp_processor import MCPProcessor; print('OK')"

# Check for lock file
ls -la ai_employee_vault/.state/processing.lock
```

### Email Validation Errors

**Issue**: Valid emails rejected

**Solution**:
```bash
# Test email validation directly
python -c "
from src.orchestrator.skills.send_email import SendEmailSkill
skill = SendEmailSkill('./ai_employee_vault')
print(skill._validate_email('test@example.com'))
"
```

### Retry Logic Not Working

**Issue**: No retries on failures

**Solution**:
```bash
# Check retry handler import
python -c "from src.orchestrator.skills.gmail_retry_handler import with_gmail_retry; print('OK')"

# Verify decorator is applied
grep -n "@with_gmail_retry" src/orchestrator/skills/send_email.py
```

---

## 📊 Success Criteria

Silver Tier testing is successful when:

1. ✅ MCP processor executes all action types (send_email, modify_email, etc.)
2. ✅ Email validation prevents invalid inputs
3. ✅ Attachment handling works correctly
4. ✅ Orchestrator automatically processes MCP actions
5. ✅ Retry logic handles transient failures
6. ✅ Stale locks are cleaned up
7. ✅ Watcher restarts are limited
8. ✅ End-to-end workflow completes successfully
9. ✅ No unexpected errors in logs
10. ✅ All files end up in correct folders (Done, etc.)

---

## 🚀 Next Steps After Testing

Once all tests pass:

1. Update README.md to reflect Silver Tier completion
2. Create release notes
3. Tag the release: `git tag v2.0-silver-tier`
4. Push to remote: `git push origin silver-imp --tags`
5. Consider merging to main branch
6. Begin Gold Tier planning

---

**Testing Status**: Ready for execution
**Last Updated**: 2026-04-02
