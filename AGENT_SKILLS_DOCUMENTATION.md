# Bronze Tier Agent Skills Documentation

## Overview

This document describes the Claude Code Agent Skills implementation for the Bronze Tier Personal AI Employee. All AI functionality is now implemented as Agent Skills, meeting the Bronze Tier requirement from `requirements.md`.

## Architecture

### Skills Structure

```
.claude/tools/
└── bronze_tier_skills.json (Skills manifest)

src/orchestrator/skills/
├── __init__.py
├── base_skill.py (Base class for all skills)
├── process_needs_action.py
├── update_dashboard.py
├── create_plan.py
├── create_approval_request.py
├── parse_watcher_file.py
├── process_inbox.py
└── process_approved_actions.py
```

### Skill Execution Pattern

All skills follow this pattern:

1. **Skill Manifest** (`.claude/tools/bronze_tier_skills.json`):
   - Defines available skills
   - Specifies input schemas
   - Maps skills to implementation scripts

2. **Base Skill Class** (`base_skill.py`):
   - Provides common functionality (logging, file I/O)
   - Handles error handling and result formatting
   - Standardizes skill execution

3. **Individual Skills** (`*.py`):
   - Implement specific functionality
   - Accept JSON parameters
   - Return structured results

## Available Skills

### 1. process_needs_action

**Purpose**: Process files in the Needs_Action directory and update dashboard

**Category**: file_processing

**Input Schema**:
```json
{
  "vault_path": "string (required)",
  "files": ["string"] (optional)
}
```

**Returns**:
```json
{
  "success": true,
  "result": {
    "processed_count": 5,
    "files_processed": ["file1.md", "file2.md"]
  },
  "timestamp": "2026-03-28T10:30:00"
}
```

**Functionality**:
- Reads files from Needs_Action directory
- Extracts metadata from YAML frontmatter
- Creates plans for complex tasks
- Generates approval requests for sensitive actions
- Moves processed files to Done folder
- Updates dashboard with processing results

**Usage Example**:
```bash
python src/orchestrator/skills/process_needs_action.py '{
  "vault_path": "/path/to/vault"
}'
```

### 2. update_dashboard

**Purpose**: Update the Dashboard.md file with current status and activity

**Category**: reporting

**Input Schema**:
```json
{
  "vault_path": "string (required)",
  "activity_log": "string (optional)",
  "summary": "string (optional)",
  "status": "operational|processing|error|idle (optional)"
}
```

**Returns**:
```json
{
  "success": true,
  "result": {
    "dashboard_path": "/path/to/vault/Dashboard.md",
    "status": "operational",
    "activity_added": true,
    "summary_updated": true
  },
  "timestamp": "2026-03-28T10:30:00"
}
```

**Functionality**:
- Updates system status with emoji indicators
- Adds timestamp for last update
- Appends new activities to Recent Activity section
- Updates summary section
- Counts pending actions from Needs_Action and Pending_Approval

**Usage Example**:
```bash
python src/orchestrator/skills/update_dashboard.py '{
  "vault_path": "/path/to/vault",
  "activity_log": "Processed 3 files",
  "status": "operational"
}'
```

### 3. create_plan

**Purpose**: Generate structured action plans for processing tasks

**Category**: planning

**Input Schema**:
```json
{
  "vault_path": "string (required)",
  "task_description": "string (required)",
  "files_to_process": ["string"] (optional),
  "priority": "low|medium|high|urgent (optional)"
}
```

**Returns**:
```json
{
  "success": true,
  "result": {
    "plan_id": "PLAN_20260328_103000",
    "plan_path": "/path/to/vault/Plans/PLAN_20260328_103000.md",
    "task_description": "Process invoice files",
    "priority": "high"
  },
  "timestamp": "2026-03-28T10:30:00"
}
```

**Functionality**:
- Auto-detects task type (file_processing, approval_workflow, etc.)
- Generates appropriate steps based on task type
- Estimates processing time
- Creates plan file in Plans directory
- Includes completion criteria and notes

**Usage Example**:
```bash
python src/orchestrator/skills/create_plan.py '{
  "vault_path": "/path/to/vault",
  "task_description": "Process monthly invoices",
  "priority": "high"
}'
```

### 4. create_approval_request

**Purpose**: Generate approval request files for sensitive actions

**Category**: approval

**Input Schema**:
```json
{
  "vault_path": "string (required)",
  "action_type": "payment|email|file_delete|system_change (required)",
  "action_details": {
    "key": "value"
  },
  "reason": "string (required)",
  "expires_in_hours": "integer (optional, default: 24)"
}
```

**Returns**:
```json
{
  "success": true,
  "result": {
    "approval_id": "APPROVAL_20260328_103000",
    "approval_path": "/path/to/vault/Pending_Approval/APPROVAL_20260328_103000.md",
    "action_type": "payment",
    "expires_at": "2026-03-29T10:30:00"
  },
  "timestamp": "2026-03-28T10:30:00"
}
```

**Functionality**:
- Creates detailed approval request file
- Includes risk assessment based on action type
- Provides approval/rejection instructions
- Sets expiration time
- Documents reviewer decision

**Usage Example**:
```bash
python src/orchestrator/skills/create_approval_request.py '{
  "vault_path": "/path/to/vault",
  "action_type": "payment",
  "action_details": {
    "amount": 500.00,
    "recipient": "Client A",
    "reference": "INV-001"
  },
  "reason": "Payment for completed invoice"
}'
```

### 5. parse_watcher_file

**Purpose**: Extract information from watcher-generated files

**Category**: parsing

**Input Schema**:
```json
{
  "file_path": "string (required)",
  "file_type": "email|file_drop|system_event|manual|auto (optional)"
}
```

**Returns**:
```json
{
  "success": true,
  "result": {
    "file_path": "/path/to/file.md",
    "file_name": "file.md",
    "file_type": "email",
    "parsed_fields": {
      "from": "sender@example.com",
      "subject": "Invoice #123",
      "priority": "high"
    },
    "email_content": "Email body...",
    "suggested_actions": ["Reply", "Forward"],
    "parsed_at": "2026-03-28T10:30:00",
    "file_size": 1024
  },
  "timestamp": "2026-03-28T10:30:00"
}
```

**Functionality**:
- Auto-detects file type if not specified
- Extracts YAML frontmatter metadata
- Parses file-specific fields based on type
- Extracts suggested actions
- Returns structured data for processing

**Usage Example**:
```bash
python src/orchestrator/skills/parse_watcher_file.py '{
  "file_path": "/path/to/email_file.md",
  "file_type": "email"
}'
```

### 6. process_inbox

**Purpose**: Process files dropped in the Inbox folder

**Category**: file_processing

**Input Schema**:
```json
{
  "vault_path": "string (required)",
  "files": ["string"] (optional)
}
```

**Returns**:
```json
{
  "success": true,
  "result": {
    "processed_count": 3,
    "moved_to_needs_action": 2,
    "moved_to_done": 1,
    "files_processed": ["file1.md", "file2.md", "file3.md"]
  },
  "timestamp": "2026-03-28T10:30:00"
}
```

**Functionality**:
- Monitors Inbox folder for new files
- Determines processing requirements based on content
- Moves files to Needs_Action for further processing or Done for simple files
- Creates metadata files for files moved to Needs_Action
- Updates dashboard with processing results

**Usage Example**:
```bash
python src/orchestrator/skills/process_inbox.py '{
  "vault_path": "/path/to/vault"
}'
```

### 7. process_approved_actions

**Purpose**: Execute approved actions from the Approved folder

**Category**: execution

**Input Schema**:
```json
{
  "vault_path": "string (required)",
  "files": ["string"] (optional)
}
```

**Returns**:
```json
{
  "success": true,
  "result": {
    "processed_count": 2,
    "execution_results": [
      {
        "file": "APPROVAL_payment_001.md",
        "action": "payment",
        "result": {
          "status": "logged",
          "message": "Payment action approved and logged"
        }
      }
    ]
  },
  "timestamp": "2026-03-28T10:30:00"
}
```

**Functionality**:
- Reads approved action files
- Executes actions based on type (payment, email, file, system)
- Logs execution results to audit trail
- Archives approved files to Done with execution summary
- Updates dashboard with execution status

**Note**: In Bronze Tier, actions are logged but actual execution (sending emails, processing payments) requires MCP servers (Silver/Gold tier).

**Usage Example**:
```bash
python src/orchestrator/skills/process_approved_actions.py '{
  "vault_path": "/path/to/vault"
}'
```

## Integration with Existing Implementation

### Orchestrator Integration

The existing orchestrator can now call agent skills instead of using direct subprocess calls:

**Before** (subprocess approach):
```python
result = subprocess.run(['claude', '--dangerously-skip-permissions', 'prompt'])
```

**After** (skill approach):
```python
import subprocess
import json

params = {"vault_path": str(self.vault_path)}
result = subprocess.run([
    'python',
    'src/orchestrator/skills/process_needs_action.py',
    json.dumps(params)
], capture_output=True, text=True)
```

### Skill Invocation Patterns

#### Direct Command Line
```bash
python src/orchestrator/skills/update_dashboard.py '{
  "vault_path": "/path/to/vault",
  "status": "operational"
}'
```

#### From Python Code
```python
from src.orchestrator.skills.update_dashboard import UpdateDashboardSkill

skill = UpdateDashboardSkill("/path/to/vault")
result = skill.execute({
    "activity_log": "Task completed",
    "status": "operational"
})
```

#### From Claude Code
Claude Code can invoke skills directly when properly configured in the skills manifest.

## Bronze Tier Requirements Compliance

### Requirements from requirements.md

✅ **Obsidian vault with Dashboard.md and Company_Handbook.md**
- Implemented: Vault structure created with all required files

✅ **One working Watcher script (Gmail OR file system monitoring)**
- Implemented: File system watcher in `src/watchers/filesystem_watcher.py`

✅ **Claude Code successfully reading from and writing to the vault**
- Implemented: All skills use base_skill.py for file I/O

✅ **Basic folder structure: /Inbox, /Needs_Action, /Done**
- Implemented: All folders created in vault

✅ **All AI functionality should be implemented as Agent Skills**
- **NOW COMPLIANT**: 7 agent skills created with proper manifest

### Skill Manifest

The skills manifest (`.claude/tools/bronze_tier_skills.json`) defines:
- File Management Skills (via base_skill.py)
- Processing Skills (all individual skills)
- Input schemas for validation
- Implementation mappings

## Testing

### Unit Testing Skills

Each skill can be tested independently:

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

# Test create_plan
python src/orchestrator/skills/create_plan.py '{
  "vault_path": "/home/asad/piaic/projects/personal_ai_employee/ai_employee_vault",
  "task_description": "Test task",
  "priority": "medium"
}'
```

### Integration Testing

Test the complete workflow:

1. Drop a file in `/Inbox`
2. Run `process_inbox` skill
3. Verify file moved to `/Needs_Action`
4. Run `process_needs_action` skill
5. Verify dashboard updated
6. Check `/Done` folder for processed files

## Logging

All skills log to:
```
ai_employee_vault/Logs/skills_YYYY-MM-DD.log
```

Log entries include:
- Skill name
- Parameters received
- Execution status
- Errors with stack traces

## Error Handling

All skills include:
- Try/catch blocks for error handling
- Structured error responses
- Detailed logging
- Graceful failure modes

## Next Steps (Silver Tier)

To advance to Silver Tier, add:

1. **Email MCP Server**: Integrate with Gmail API for actual email operations
2. **WhatsApp Watcher**: Add WhatsApp monitoring via Playwright
3. **Enhanced Skills**: Create skills that use MCP servers for external actions
4. **Ralph Wiggum Loop**: Implement persistent task completion loop

## Summary

The Bronze Tier Agent Skills implementation provides:

- ✅ 7 fully functional agent skills
- ✅ Proper skill manifest and documentation
- ✅ Base class for consistency
- ✅ Comprehensive error handling
- ✅ Detailed logging
- ✅ Compliance with all Bronze Tier requirements
- ✅ Foundation for Silver/Gold tier expansion

All AI functionality is now implemented as Agent Skills, meeting the requirement from `requirements.md`.