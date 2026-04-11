#!/bin/bash

# Setup script for AI Employee Bronze Tier

set -e

echo "=== AI Employee Bronze Tier Setup ==="
echo ""

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$SCRIPT_DIR"
VAULT_PATH="$PROJECT_ROOT/ai_employee_vault"

echo "Project root: $PROJECT_ROOT"
echo "Vault path: $VAULT_PATH"
echo ""

# Check prerequisites
echo "Checking prerequisites..."
if ! command -v python3 &> /dev/null; then
    echo "✗ Python 3 is required but not installed."
    exit 1
fi
echo "✓ Python 3 found"

if ! command -v claude &> /dev/null; then
    echo "⚠ Warning: Claude Code CLI not found in PATH"
    echo "  The system requires Claude Code to process files."
    echo "  Install via npm: npm install -g @anthropic/claude-code"
else
    echo "✓ Claude Code CLI found"
fi
echo ""

# Create virtual environment if it doesn't exist
if [ ! -d "$PROJECT_ROOT/venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$PROJECT_ROOT/venv"
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi
echo ""

# Install Python dependencies
echo "Installing Python dependencies..."
"$PROJECT_ROOT/venv/bin/pip" install -r requirements.txt
echo "✓ Dependencies installed"
echo ""

# Setup Agent Skills
echo "Setting up Agent Skills..."
mkdir -p "$PROJECT_ROOT/.claude/tools"
mkdir -p "$PROJECT_ROOT/src/orchestrator/skills"

if [ -f "$PROJECT_ROOT/.claude/tools/bronze_tier_skills.json" ]; then
    echo "✓ Skills manifest found"
else
    echo "⚠ Warning: Skills manifest (.claude/tools/bronze_tier_skills.json) not found"
fi

if ls "$PROJECT_ROOT"/src/orchestrator/skills/*.py 1> /dev/null 2>&1; then
    chmod +x "$PROJECT_ROOT"/src/orchestrator/skills/*.py
    echo "✓ Skill scripts made executable"
else
    echo "⚠ Warning: No skill scripts found in src/orchestrator/skills/"
fi
echo ""

# Create vault structure if it doesn't exist
echo "Setting up vault structure..."
mkdir -p "$VAULT_PATH"/{Inbox,Needs_Action,Done,Pending_Approval,Approved,Rejected,Plans,Logs,.state,.obsidian}
echo "✓ Vault directories created"
echo ""

# Create Dashboard.md if it doesn't exist
if [ ! -f "$VAULT_PATH/Dashboard.md" ]; then
    echo "Creating Dashboard.md..."
    cat > "$VAULT_PATH/Dashboard.md" << 'EOF'
# AI Employee Dashboard

## Last Updated
$(date +%Y-%m-%d\ %H:%M)

## System Status
🟢 Operational

## Pending Actions
No pending actions

## Recent Activity
- [$(date +%Y-%m-%d\ %H:%M)] Dashboard initialized

## Statistics
- Total Items Processed: 0
- Items in Queue: 0
- Failed Items: 0

## Quick Links
- [[Company_Handbook]]
- [[README]]
EOF
    echo "✓ Dashboard.md created"
else
    echo "✓ Dashboard.md already exists"
fi
echo ""

# Create Company_Handbook.md if it doesn't exist
if [ ! -f "$VAULT_PATH/Company_Handbook.md" ]; then
    echo "Creating Company_Handbook.md..."
    cat > "$VAULT_PATH/Company_Handbook.md" << 'EOF'
# Company Handbook - AI Employee Rules of Engagement

## Last Updated
$(date +%Y-%m-%d)

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

## Response Templates

### Email Reply Template
```
Subject: Re: [Original Subject]

Dear [Name],

[Response content]

Best regards,
[Your Name]

---
This email was drafted with AI assistance.
```

### Approval Request Template
```
---
type: approval_request
action: [action_type]
priority: [high/medium/low]
created: [timestamp]
expires: [timestamp]
---

## Action Details
[Detailed description]

## To Approve
Move this file to /Approved/

## To Reject
Move this file to /Rejected/
```
EOF
    echo "✓ Company_Handbook.md created"
else
    echo "✓ Company_Handbook.md already exists"
fi
echo ""

# Create README.md for Obsidian
if [ ! -f "$VAULT_PATH/README.md" ]; then
    echo "Creating README.md..."
    cat > "$VAULT_PATH/README.md" << 'EOF'
# AI Employee Vault - Obsidian Guide

Welcome to the Personal AI Employee vault! This Obsidian workspace is designed to work seamlessly with the automated AI Employee system.

## 📁 Folder Structure

### 📥 **Inbox**
Drop new task files here. The AI Employee monitors this folder and automatically processes files every 30 seconds.

### ⚡ **Needs_Action**
Files that require processing but may need additional context or decisions.

### ✅ **Done**
Completed tasks and generated outputs are stored here with timestamps.

### 📋 **Plans**
Strategic plans and multi-step workflows created by the AI Employee.

### ⏳ **Pending_Approval**
Tasks requiring human approval before execution (payments, emails, etc.).

### ✓ **Approved**
Approved tasks ready for execution.

### ❌ **Rejected**
Tasks that were rejected and won't be executed.

### 📊 **Logs**
System activity logs and processing history.

## 🎯 Quick Start

1. **View Dashboard**: Open `Dashboard.md` to see current system status
2. **Create a Task**: Create a new `.md` file in the Inbox folder
3. **Monitor Activity**: Watch the Dashboard update automatically
4. **Review Results**: Check the Done folder for completed tasks

## 📝 Task File Template

```markdown
# Task: [Task Name]

## Task Type
[Information Request / Action / Report / etc.]

## Priority
[High / Medium / Low]

## Description
[Detailed description of what needs to be done]

## Expected Output
[What you expect as a result]

## Notes
[Any additional context]

---
*Created: YYYY-MM-DD*
*Status: Pending*
```

## 🔗 Key Files

- [[Dashboard]] - System status and recent activity
- [[Company_Handbook]] - Rules and guidelines for the AI Employee

## 🚀 System Integration

The AI Employee system runs in the background and:
- Monitors Inbox, Needs_Action, and Approved folders
- Processes files automatically using Claude Code
- Updates the Dashboard in real-time
- Logs all activities

## 💡 Tips

- Use Obsidian's graph view to visualize task relationships
- Tag tasks with `#urgent`, `#payment`, `#email` for easy filtering
- Link related tasks using `[[Task Name]]` syntax
- Keep the Dashboard open to monitor system activity

---
*Last Updated: $(date +%Y-%m-%d)*
EOF
    echo "✓ README.md created"
else
    echo "✓ README.md already exists"
fi
echo ""

# Create Obsidian configuration
echo "Setting up Obsidian configuration..."
if [ ! -f "$VAULT_PATH/.obsidian/app.json" ]; then
    cat > "$VAULT_PATH/.obsidian/app.json" << 'EOF'
{
  "showLineNumber": true,
  "foldHeading": true,
  "foldIndent": true,
  "showFrontmatter": true,
  "showUnsupportedFiles": false,
  "attachmentFolderPath": "Done",
  "newFileLocation": "folder",
  "newFileFolderPath": "Inbox",
  "alwaysUpdateLinks": true,
  "useMarkdownLinks": true,
  "promptDelete": true,
  "vimMode": false,
  "spellcheck": true,
  "spellcheckLanguages": ["en-US"],
  "livePreview": true,
  "readableLineLength": true,
  "strictLineBreaks": false,
  "showIndentGuide": true,
  "defaultViewMode": "preview"
}
EOF
    echo "✓ Obsidian app.json created"
else
    echo "✓ Obsidian app.json already exists"
fi
echo ""

# Validation step
echo "Validating setup..."
validation_failed=0

# Check required directories
required_dirs=("Inbox" "Needs_Action" "Done" "Plans" "Pending_Approval" "Approved" "Rejected" "Logs" ".state")
for dir in "${required_dirs[@]}"; do
    if [ ! -d "$VAULT_PATH/$dir" ]; then
        echo "✗ Missing directory: $dir"
        validation_failed=1
    fi
done

# Check required files
required_files=("Dashboard.md" "Company_Handbook.md" "README.md")
for file in "${required_files[@]}"; do
    if [ ! -f "$VAULT_PATH/$file" ]; then
        echo "✗ Missing file: $file"
        validation_failed=1
    fi
done

if [ $validation_failed -eq 0 ]; then
    echo "✓ All required directories and files present"
else
    echo "✗ Setup validation failed"
    exit 1
fi
echo ""

echo ""
echo "=== Setup Complete ==="
echo ""
echo "✓ Virtual environment created"
echo "✓ Python dependencies installed"
echo "✓ Agent Skills structure verified"
echo "✓ Vault structure created"
echo "✓ Dashboard.md configured"
echo "✓ Company_Handbook.md configured"
echo "✓ README.md created"
echo "✓ Obsidian configuration ready"
echo "✓ Setup validation passed"
echo ""
echo "Next steps:"
echo "1. Start the system: ./start.sh"
echo "2. Open Obsidian: obsidian $VAULT_PATH"
echo "3. Drop task files in: $VAULT_PATH/Inbox"
echo "4. Monitor Dashboard.md for activity"
echo ""
echo "The AI Employee will automatically process files every 30 seconds."
echo ""
