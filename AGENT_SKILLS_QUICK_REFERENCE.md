# Agent Skills Quick Reference

## Bronze Tier Agent Skills - Quick Start Guide

## Skills Overview

| Skill | Purpose | Usage |
|-------|---------|-------|
| `process_needs_action` | Process files in Needs_Action | `python skills/process_needs_action.py '{"vault_path": "/path/to/vault"}'` |
| `update_dashboard` | Update dashboard status | `python skills/update_dashboard.py '{"vault_path": "/path/to/vault", "status": "operational"}'` |
| `create_plan` | Generate action plans | `python skills/create_plan.py '{"vault_path": "/path/to/vault", "task_description": "..."}'` |
| `create_approval_request` | Create approval requests | `python skills/create_approval_request.py '{"vault_path": "/path/to/vault", "action_type": "payment", ...}'` |
| `parse_watcher_file` | Parse watcher files | `python skills/parse_watcher_file.py '{"file_path": "/path/to/file.md"}'` |
| `process_inbox` | Process Inbox files | `python skills/process_inbox.py '{"vault_path": "/path/to/vault"}'` |
| `process_approved_actions` | Execute approved actions | `python skills/process_approved_actions.py '{"vault_path": "/path/to/vault"}'` |

## Common Usage Patterns

### 1. Process a New Task

```bash
# Drop file in Inbox first, then run:
python src/orchestrator/skills/process_inbox.py '{
  "vault_path": "/home/asad/piaic/projects/personal_ai_employee/ai_employee_vault"
}'
```

### 2. Process Pending Actions

```bash
python src/orchestrator/skills/process_needs_action.py '{
  "vault_path": "/home/asad/piaic/projects/personal_ai_employee/ai_employee_vault"
}'
```

### 3. Create an Approval Request

```bash
python src/orchestrator/skills/create_approval_request.py '{
  "vault_path": "/home/asad/piaic/projects/personal_ai_employee/ai_employee_vault",
  "action_type": "payment",
  "action_details": {
    "amount": 500.00,
    "recipient": "Client A",
    "reference": "INV-001"
  },
  "reason": "Payment for completed services"
}'
```

### 4. Update Dashboard Status

```bash
python src/orchestrator/skills/update_dashboard.py '{
  "vault_path": "/home/asad/piaic/projects/personal_ai_employee/ai_employee_vault",
  "activity_log": "Task completed successfully",
  "status": "operational"
}'
```

### 5. Create a Task Plan

```bash
python src/orchestrator/skills/create_plan.py '{
  "vault_path": "/home/asad/piaic/projects/personal_ai_employee/ai_employee_vault",
  "task_description": "Process monthly invoices and send reminders",
  "priority": "high"
}'
```

### 6. Execute Approved Actions

```bash
python src/orchestrator/skills/process_approved_actions.py '{
  "vault_path": "/home/asad/piaic/projects/personal_ai_employee/ai_employee_vault"
}'
```

## File Paths

- **Vault**: `/home/asad/piaic/projects/personal_ai_employee/ai_employee_vault`
- **Skills**: `/home/asad/piaic/projects/personal_ai_employee/src/orchestrator/skills/`
- **Skills Manifest**: `/home/asad/piaic/projects/personal_ai_employee/.claude/tools/bronze_tier_skills.json`
- **Logs**: `/home/asad/piaic/projects/personal_ai_employee/ai_employee_vault/Logs/`

## Testing Skills

### Test Individual Skills

```bash
# Test process_needs_action
python src/orchestrator/skills/process_needs_action.py '{
  "vault_path": "/home/asad/piaic/projects/personal_ai_employee/ai_employee_vault"
}'

# Test update_dashboard
python src/orchestrator/skills/update_dashboard.py '{
  "vault_path": "/home/asad/piaic/projects/personal_ai_employee/ai_employee_vault",
  "status": "operational"
}'
```

### Test Complete Workflow

```bash
# 1. Create a test file in Inbox
cat > ai_employee_vault/Inbox/test_task.md << 'EOF'
---
type: task
priority: high
---

# Test Task

This is a test task for the AI Employee.
EOF

# 2. Process the inbox
python src/orchestrator/skills/process_inbox.py '{
  "vault_path": "/home/asad/piaic/projects/personal_ai_employee/ai_employee_vault"
}'

# 3. Check Needs_Action
ls -la ai_employee_vault/Needs_Action/

# 4. Process needs action
python src/orchestrator/skills/process_needs_action.py '{
  "vault_path": "/home/asad/piaic/projects/personal_ai_employee/ai_employee_vault"
}'

# 5. Check dashboard
cat ai_employee_vault/Dashboard.md

# 6. Check Done folder
ls -la ai_employee_vault/Done/
```

## Skill Return Format

All skills return JSON in this format:

```json
{
  "success": true,
  "result": {
    // Skill-specific result data
  },
  "timestamp": "2026-03-28T10:30:00"
}
```

On error:

```json
{
  "success": false,
  "error": "Error message here",
  "timestamp": "2026-03-28T10:30:00"
}
```

## Monitoring

### View Skill Logs

```bash
# View today's skill logs
tail -f ai_employee_vault/Logs/skills_$(date +%Y-%m-%d).log

# View all logs
ls -la ai_employee_vault/Logs/
```

### Check Dashboard Status

```bash
cat ai_employee_vault/Dashboard.md
```

## Troubleshooting

### Skill Returns Error

1. Check the log file for details
2. Verify vault_path is correct
3. Ensure required directories exist
4. Check file permissions

### File Not Moving

1. Check if file is locked by another process
2. Verify destination directory exists
3. Check disk space
4. Review log files for errors

### Dashboard Not Updating

1. Verify vault_path is correct
2. Check Dashboard.md file permissions
3. Review skill logs for errors
4. Ensure skill completed successfully

## Bronze Tier Requirements Checklist

- ✅ Obsidian vault with Dashboard.md and Company_Handbook.md
- ✅ One working Watcher script (file system monitoring)
- ✅ Claude Code reading from and writing to vault
- ✅ Basic folder structure (/Inbox, /Needs_Action, /Done)
- ✅ **All AI functionality implemented as Agent Skills**

## Next Steps

1. Test all skills individually
2. Test complete workflow
3. Review logs for any issues
4. Document any custom workflows
5. Prepare for Silver Tier (MCP servers integration)

## Documentation

- Full documentation: `AGENT_SKILLS_DOCUMENTATION.md`
- Implementation summary: `IMPLEMENTATION_SUMMARY.md`
- Testing guide: `TESTING.md`
- Project structure: `PROJECT_STRUCTURE.md`