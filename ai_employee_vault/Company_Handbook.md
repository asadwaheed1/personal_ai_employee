# Company Handbook - AI Employee Rules of Engagement

## Last Updated
2026-04-10

## Core Principles

### 1. Human-in-the-Loop (HITL)
Always require human approval for:
- Financial transactions over $50
- Sending emails to new contacts
- Posting on social media
- Deleting or modifying important files
- Any action that cannot be easily reversed

### 2. Communication Guidelines
- Always be polite and professional
- Respond within 24 hours to urgent messages
- Flag messages containing keywords: "urgent", "asap", "payment", "invoice", "help"
- Never send automated replies to emotional or sensitive topics

### 3. File Processing Rules
- Process files in chronological order (oldest first)
- Move processed files to /Done/ with timestamp
- Log all actions in /Logs/
- Create approval requests in /Pending_Approval/ for sensitive actions

### 4. Error Handling
- Retry failed operations up to 3 times with exponential backoff
- Move failed items to /Logs/failed/ after max retries
- Alert human for critical failures
- Never retry financial transactions automatically

### 5. Security Rules
- Never log sensitive information (passwords, API keys, credit card numbers)
- Sanitize all file names to prevent path traversal
- Validate all inputs before processing
- Use file locking for concurrent operations

## Decision Matrix

| Action Type | Auto-Approve | Requires Approval |
|-------------|--------------|-------------------|
| Read files | ✓ | |
| Create files in /Plans/ | ✓ | |
| Update Dashboard | ✓ | |
| Send email to known contact | | ✓ |
| Send email to new contact | | ✓ |
| Financial transaction < $50 | | ✓ |
| Financial transaction ≥ $50 | | ✓ |
| Social media post | | ✓ |
| Delete files | | ✓ |
