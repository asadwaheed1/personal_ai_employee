# Personal AI Employee - Silver Tier Demo Script

**Date:** 2026-04-15  
**Tier:** Silver  
**Duration:** ~15 minutes

---

## Pre-Demo Checklist

### 1. Start the System
```bash
cd /home/asad/piaic/projects/personal_ai_employee
./start.sh
```

### 2. Verify Watchers Running
```bash
ps aux | grep watcher
```
**Expected:** See 3 processes - filesystem_watcher, gmail_watcher, linkedin_watcher

### 3. Open Dashboard
```bash
cat ai_employee_vault/Dashboard.md
```

### 4. Clear Previous Demo Files (Optional)
```bash
rm -f ai_employee_vault/Inbox/*.md
rm -f ai_employee_vault/Needs_Action/*.json
rm -f ai_employee_vault/Pending_Approval/*.md
rm -f ai_employee_vault/Approved/*.md
```

---

## Demo Flow 1: Gmail Auto-Processing (5 minutes)

### What You'll Show
Automated email monitoring, action file creation, and MCP execution without human approval.

### Steps

**1. Send Test Email**
- Open Gmail in browser
- Send email to your monitored account
- Subject: `Test: AI Employee Demo - Mark as Read`
- Body: `This email will be automatically processed by my AI employee system.`

**2. Explain While Waiting (~60 seconds)**
> "The Gmail watcher polls every minute. When it detects this unread email, it will create an action file in the Inbox folder."

**3. Show Action File Created**
```bash
ls -la ai_employee_vault/Inbox/
cat ai_employee_vault/Inbox/GMAIL_*.md
```

**4. Explain Orchestrator Processing**
> "The orchestrator runs every 30 seconds. It reads this action file, determines it's a simple 'mark as read' action that doesn't need approval, and creates an MCP action file."

**5. Show MCP Action File**
```bash
ls -la ai_employee_vault/Needs_Action/
cat ai_employee_vault/Needs_Action/MCP_*.json
```

**6. Show Execution Result**
```bash
ls -la ai_employee_vault/Done/
cat ai_employee_vault/Done/EXECUTED_MCP_*.json
```

**7. Verify in Gmail**
- Refresh Gmail
- Show email is now marked as read
- Point out: "No manual intervention required"

---

## Demo Flow 2: Human-in-the-Loop Approval (5 minutes)

### What You'll Show
Sensitive actions require human approval before execution.

### Steps

**1. Create Sensitive Action File**
```bash
cat > ai_employee_vault/Inbox/GMAIL_reply_demo.md << 'EOF'
---
type: gmail_action
action: reply
message_id: test_demo_message
timestamp: 2026-04-15T17:45:00Z
---

# Gmail Reply Action

**From:** demo@example.com
**Subject:** Important Business Question

## Original Message
Can you send me the quarterly report?

## Proposed Reply
Thank you for your inquiry. I will review the quarterly report and send it to you by end of day.

Best regards,
Asad
EOF
```

**2. Explain the File**
> "I've created an action file that requests sending an email reply. This is a sensitive action because it involves external communication."

**3. Wait for Orchestrator (~30 seconds)**
```bash
watch -n 5 'ls -la ai_employee_vault/Pending_Approval/'
```

**4. Show File Moved to Pending_Approval**
```bash
cat ai_employee_vault/Pending_Approval/GMAIL_reply_demo.md
```

**5. Explain HITL Gate**
> "The system recognized this as a sensitive action and moved it to Pending_Approval. It will NOT execute until I manually approve it."

**6. Human Approval Step (Show on Camera)**
```bash
mv ai_employee_vault/Pending_Approval/GMAIL_reply_demo.md ai_employee_vault/Approved/
```

**7. Explain**
> "By moving the file to the Approved folder, I'm authorizing the system to execute this action."

**8. Wait for Processing (~30 seconds)**

**9. Show Execution**
```bash
ls -la ai_employee_vault/Done/
cat ai_employee_vault/Done/EXECUTED_MCP_*.json
```

**10. Key Point**
> "This human-in-the-loop workflow ensures sensitive actions never execute automatically. I maintain control over critical operations."

---

## Demo Flow 3: LinkedIn Content Publishing (5 minutes)

### What You'll Show
Content calendar management and LinkedIn posting with approval workflow.

### Steps

**1. Show Content Plan**
```bash
cat > ai_employee_vault/Plans/content_plan.json << 'EOF'
{
  "posts": [
    {
      "date": "2026-04-15",
      "content": "Excited to share my Personal AI Employee project! 🤖\n\nBuilt an autonomous system that:\n✅ Monitors Gmail automatically\n✅ Manages LinkedIn content\n✅ Requires human approval for sensitive actions\n\nSilver tier complete! #AI #Automation #ProductivityHack",
      "status": "pending"
    }
  ]
}
EOF
```

**2. Explain Content Calendar**
> "I maintain a content calendar in JSON format. The system checks this daily and creates posts for today's date."

**3. Trigger LinkedIn Skill**
```bash
source venv/bin/activate
python -m src.orchestrator.skills.post_linkedin --vault-path ai_employee_vault
```

**4. Show Approval Request Created**
```bash
ls -la ai_employee_vault/Pending_Approval/
cat ai_employee_vault/Pending_Approval/LINKEDIN_POST_*.md
```

**5. Explain**
> "LinkedIn posts always require approval. The system created this approval request with the full post content for review."

**6. Review and Approve**
```bash
# Show the content first
cat ai_employee_vault/Pending_Approval/LINKEDIN_POST_*.md

# Then approve
mv ai_employee_vault/Pending_Approval/LINKEDIN_POST_*.md ai_employee_vault/Approved/
```

**7. Wait for Processing (~30 seconds)**

**8. Show Execution Result**
```bash
cat ai_employee_vault/Done/LINKEDIN_POST_*.md
```

**9. Show Live LinkedIn Post**
- Open LinkedIn in browser
- Navigate to your profile
- Show the newly published post
- Point out timestamp matches execution time

**10. Key Point**
> "The system used the official LinkedIn API with OAuth authentication. This is production-ready, not browser automation."

---

## Demo Flow 4: Dashboard Overview (2 minutes)

### What You'll Show
Centralized monitoring and activity tracking.

### Steps

**1. Show Dashboard**
```bash
cat ai_employee_vault/Dashboard.md
```

**2. Highlight Key Sections**

**Watcher Status:**
> "Shows all three watchers are running and when they last checked."

**Recent Activity:**
> "Chronological log of all actions processed today."

**Pending Items:**
> "Any items waiting for approval or processing."

**Metrics:**
> "Summary statistics - emails processed, posts published, approval rate."

**3. Show Real-Time Update**
```bash
# Trigger dashboard update
source venv/bin/activate
python src/orchestrator/skills/dashboard_update.py ai_employee_vault

# Show updated dashboard
cat ai_employee_vault/Dashboard.md
```

---

## Closing Points

### Architecture Highlights
1. **Three Watchers:** Gmail, LinkedIn, Filesystem - all running independently
2. **MCP Integration:** External actions executed through Model Context Protocol
3. **HITL Workflow:** Sensitive actions require explicit human approval
4. **Vault-Based State:** All state managed through Obsidian markdown files
5. **Scheduled Automation:** Cron jobs handle recurring tasks

### Silver Tier Requirements Met
- ✅ Multiple watcher scripts (3 active)
- ✅ LinkedIn posting automation
- ✅ Plan creation capability
- ✅ Working MCP server (Gmail)
- ✅ Human-in-the-loop approval workflow
- ✅ Basic scheduling setup (cron)
- ✅ AI functionality as skills

### What's Next (Gold Tier Preview)
- Advanced reasoning with multi-step planning
- Calendar integration for meeting management
- Proactive task suggestions based on patterns
- Enhanced error recovery and retry logic
- Multi-channel communication orchestration

---

## Cleanup After Demo

```bash
# Stop all watchers
./stop.sh

# Verify stopped
ps aux | grep watcher
```

---

## Troubleshooting

### Watchers Not Running
```bash
# Check logs
tail -f logs/orchestrator.log
tail -f logs/gmail_watcher.log
tail -f logs/linkedin_watcher.log
```

### Gmail Not Detecting Email
```bash
# Manually trigger Gmail watcher
source venv/bin/activate
python -m src.watchers.run_gmail_watcher
```

### LinkedIn Auth Issues
```bash
# Re-authenticate
python scripts/setup_linkedin_api.py
```

### MCP Execution Failing
```bash
# Check Gmail MCP authentication
ls -la ~/.gmail-mcp/
# Re-authenticate if needed
```

---

**End of Demo Script**
