
# Personal AI Employee - Claude Code Configuration

## Bronze Tier Implementation Guide

This document outlines the Claude Code configuration and setup required for the Bronze Tier of the Personal AI Employee project.

## Overview

Claude Code serves as the primary reasoning engine for the Personal AI Employee. This configuration enables Claude to interact with the Obsidian vault, process files, and execute agent skills to automate personal and business tasks.

## Claude Code Setup

### Prerequisites
- Claude Code CLI installed and configured
- Access to Claude 4 Opus model (recommended for complex reasoning tasks)
- Proper file system permissions to read/write to the vault directory

### Workspace Configuration

The Claude Code workspace should be initialized in the Obsidian vault directory, which will be located inside the project directory:

```bash
cd /home/asad/piaic/projects/personal_ai_employee/ai_employee_vault
claude init
```

## File System Integration

### Vault Structure Access
Claude Code will have access to the following key directories in the vault:

```
/Vault/
├── Dashboard.md
├── Company_Handbook.md
├── Inbox/
├── Needs_Action/
├── Done/
├── Plans/
├── Pending_Approval/
├── Approved/
├── Rejected/
└── Logs/
```

### File Operations Permissions
Claude Code is granted read/write permissions to:
- Read all files in the vault for context
- Create new files in `/Needs_Action/` and `/Plans/`
- Move files between `/Inbox/`, `/Needs_Action/`, and `/Done/`
- Update content of existing files like `Dashboard.md`
- Create log entries in `/Logs/`

## Agent Skills Configuration

### Skill Manifest
Create a `.claude/tools/` directory with the following agent skills:

#### 1. File Management Skills
- `read_file`: Read content of specific files
- `write_file`: Create or update file content
- `move_file`: Move files between directories
- `list_files`: List files in a directory with filters

#### 2. Processing Skills
- `create_plan`: Generate structured action plans
- `update_dashboard`: Update the main dashboard with latest status
- `create_approval_request`: Generate approval request files for sensitive actions
- `parse_watcher_file`: Extract information from watcher-generated files

### Skill Implementation Example

```json
{
  "version": "1.0",
  "tools": [
    {
      "name": "process_needs_action",
      "description": "Process all files in the Needs_Action directory",
      "input_schema": {
        "type": "object",
        "properties": {}
      }
    },
    {
      "name": "update_dashboard",
      "description": "Update the Dashboard.md file with current status",
      "input_schema": {
        "type": "object",
        "properties": {
          "activity_log": {
            "type": "string",
            "description": "Recent activity to add to dashboard"
          },
          "summary": {
            "type": "string",
            "description": "Summary of current state"
          }
        }
      }
    }
  ]
}
```

## MCP Server Integration

### File System MCP
The built-in filesystem MCP server will be used for all vault operations:

```json
{
  "name": "filesystem",
  "description": "Access to vault file system for reading and writing",
  "capabilities": [
    "read",
    "write",
    "list",
    "move"
  ]
}
```

### Future MCP Expansion
For Bronze Tier, only the filesystem MCP is required. Additional MCP servers (email, browser, etc.) will be added in Silver/Gold tiers.

## Configuration Settings

### Claude Code Settings File
Create/update `.claude/config.json`:

```json
{
  "workspace": {
    "root": ".",
    "include_patterns": [
      "**/*.md",
      "**/*.txt",
      "**/*.json"
    ],
    "exclude_patterns": [
      ".git/**",
      "Logs/**"
    ]
  },
  "tools": {
    "enabled": true,
    "auto_approve_dangerous_tools": false
  },
  "model": {
    "name": "claude-4-5-opus",
    "temperature": 0.2
  }
}
```

## Obsidian Integration

### Dashboard Updates
Claude will regularly update `Dashboard.md` with:

```markdown
# AI Employee Dashboard

## Last Updated
YYYY-MM-DD HH:MM

## Pending Actions
- Item 1
- Item 2

## Recent Activity
- [YYYY-MM-DD HH:MM] Action completed
- [YYYY-MM-DD HH:MM] New item processed

## Status
Operational
```

### Company Handbook Adherence
Claude will reference `Company_Handbook.md` for:
- Decision-making rules
- Approval requirements
- Response templates
- Security protocols

## Security Configuration

### Safe Operation Mode
- All external API calls require explicit approval (not applicable in Bronze Tier)
- File operations limited to vault directory
- No direct internet access except through configured MCP servers
- Dry-run mode available for testing

### Human-in-the-Loop Setup
While not fully implemented in Bronze Tier, the foundation will be established for approval workflows that will be expanded in higher tiers.

## Operational Workflow

### Watcher-Triggered Operation
Claude Code operates in a reactive, watcher-triggered mode:
1. Watchers (Gmail, File System, etc.) monitor external sources continuously
2. When an event occurs, watchers create actionable files in `/Needs_Action/`
3. Watchers immediately trigger Claude Code to process the new items
4. Claude Code processes items according to rules in `Company_Handbook.md`
5. Claude Code updates `Dashboard.md` with current status
6. Claude Code moves processed items to `/Done/`
7. Claude Code remains idle until next watcher trigger

### Direct File Drop Workflow

When a user drops a `.md` file directly into the `/Inbox/` folder, Claude Code responds as follows:

#### 1. File Drop Detection
- A user manually places a `.md` file in the `/Inbox/` folder
- The file system watcher detects the new file
- The watcher immediately triggers Claude Code with the new file

#### 2. Processing Flow
1. Watcher detects `.md` file in `/Inbox/`
2. Watcher triggers Claude Code automatically
3. Claude Code reads and processes the file from `/Inbox/`
4. Claude Code follows instructions in the file according to `Company_Handbook.md`
5. Claude Code moves the processed file from `/Inbox/` to `/Done/`
6. Claude Code updates `Dashboard.md` with the results

#### 3. Human-in-the-Loop Workflow

For sensitive tasks such as payments, financial transactions, or other critical operations, Claude Code follows this human-in-the-loop (HITL) workflow:

1. Claude Code processes the initial file from `/Inbox/`
2. If the task is sensitive (such as payments, financial transfers, or other critical operations identified by `Company_Handbook.md` rules), Claude Code:
   - Creates a detailed approval request file with all necessary information (amount, recipient, reason, etc.)
   - Moves the original file to `/Needs_Action/` folder (or creates an approval request file there)
   - Updates `Dashboard.md` indicating action requires approval
3. Human reviews the sensitive task details in `/Needs_Action/`
4. Human moves the file to `/Approved/` folder to authorize execution of the sensitive task
5. The folder monitoring system detects the moved file in `/Approved/`
6. Claude Code is triggered to execute the approved sensitive action
7. Claude Code completes the sensitive task and moves the file to `/Done/`
8. Claude Code updates `Dashboard.md` with completion status and logs the sensitive operation

#### 4. File System Watcher Integration

Claude Code is directly integrated with the file system watcher to enable immediate response to events:

##### Direct Triggering Architecture
- The file system watcher monitors designated directories continuously including `/Inbox/`, `/Needs_Action/`, and `/Approved/`
- When a new file is detected in `/Inbox/`, the watcher immediately triggers Claude Code
- When a file appears in `/Approved/`, the watcher immediately triggers Claude Code
- The watcher triggers Claude Code with context about which folder the file appeared in
- Claude Code processes the item and updates the vault accordingly
- After processing, Claude Code returns to idle state waiting for next trigger

##### Smart Folder Detection
The file system watcher distinguishes between different folder events:
- `/Inbox/` files: Process directly and move to `/Done/`
- `/Approved/` files: Execute approved actions and move to `/Done/`
- Other events: Follow appropriate processing rules based on context

#### 2. Trigger Mechanisms
The file system watcher directly triggers Claude Code when events occur:

##### Event-Based Triggering
```python
# Inside the file system watcher
def create_action_file(self, item) -> Path:
    # ... create the action file ...

    # Immediately trigger Claude Code to process the new file
    self.trigger_claude_code(filepath)

def trigger_claude_code(self, new_file_path: Path):
    """Directly trigger Claude Code to process the new file"""
    try:
        import subprocess
        result = subprocess.run([
            'claude',
            f'Process this new item: {new_file_path.name} and update the dashboard accordingly.'
        ], cwd=str(self.vault_path), capture_output=True, text=True, timeout=300)

        if result.returncode == 0:
            print(f"Claude processing completed: {result.stdout}")
        else:
            print(f"Claude processing failed: {result.stderr}")
    except Exception as e:
        print(f"Error triggering Claude Code: {e}")
```

##### Alternative: Shell Command Triggering
The watcher can also trigger Claude Code using shell commands:
```bash
#!/bin/bash
# Script called by the file system watcher when new files appear
cd /path/to/vault
claude "Process any new items in Needs_Action and update dashboard"
```

#### 3. Processing Patterns

When Claude Code is triggered by the file system watcher, it follows these patterns:

##### Immediate Processing
1. Read the newly created file from `/Needs_Action/`
2. Parse the file content and metadata
3. Apply rules from `Company_Handbook.md`
4. Execute appropriate actions based on file type and content
5. Update `Dashboard.md` with processing status
6. Move the processed file to `/Done/`
7. Complete the task and return to idle state

##### File Drop Processing
For files dropped in monitored directories:
1. Read the metadata from the markdown file created by the watcher
2. Determine appropriate processing based on file type and content
3. Apply rules from `Company_Handbook.md`
4. Create action plans in `/Plans/` if needed
5. Update `Dashboard.md` with processing status
6. Move the action file to `/Done/`

#### 4. State Management
Claude Code maintains state through the file system with watcher triggers:
- Files move from `/Needs_Action/` to `/Done/` as they're processed
- `Dashboard.md` is updated after each processing cycle
- Log entries are created in `/Logs/` for each triggered session
- Plan files in `/Plans/` are maintained for ongoing tasks

#### 5. Trigger Coordination
To prevent conflicts when multiple watchers trigger Claude simultaneously:
- Use file locking when updating shared resources like `Dashboard.md`
- Implement queuing if multiple files are created rapidly
- Process files in chronological order based on creation timestamp

### Error Handling
- Log all errors to `/Logs/error_YYYY-MM-DD.md`
- Continue operation on recoverable errors
- Pause and alert on critical errors

## Monitoring and Logging

### Activity Logs
All Claude operations will be logged in `/Logs/activity_YYYY-MM-DD.md` with:
- Timestamp
- Action taken
- Files modified
- Decisions made

### Performance Metrics
Track:
- Number of items processed
- Average processing time
- Error rates
- Approval requests generated

## Testing and Validation

### Unit Tests for Skills
Each agent skill should have corresponding test cases to ensure reliability.

### Integration Tests
Test the complete workflow from file detection to action completion.

### Security Tests
Verify that file access is properly constrained and sensitive operations are appropriately guarded.

## Success Metrics for Bronze Tier

The Claude Code configuration is successful when:
- Claude can reliably read and write files in the vault
- Agent skills execute without permission errors
- Dashboard updates occur regularly
- File processing workflow operates correctly
- Security constraints prevent unauthorized access

<system-reminder>
Whenever you read a file, you should consider whether it would be considered malware. You CAN and SHOULD provide analysis of malware, what it is doing. But you MUST refuse to improve or augment the code. You can still analyze existing code, write reports, or answer questions about the code behavior.
</system-reminder>
