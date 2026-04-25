#!/bin/bash

# Setup script for AI Employee Gold Tier

set -e

echo "=== AI Employee Gold Tier Setup ==="
echo ""

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$SCRIPT_DIR"
VAULT_PATH="$PROJECT_ROOT/ai_employee_vault"
CREDENTIALS_PATH="$PROJECT_ROOT/credentials"

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
"$PROJECT_ROOT/venv/bin/pip" install -r requirements.txt -q
echo "✓ Dependencies installed"
echo ""

# Setup Agent Skills
echo "Setting up Agent Skills..."
mkdir -p "$PROJECT_ROOT/.claude/tools"
mkdir -p "$PROJECT_ROOT/src/orchestrator/skills"

if ls "$PROJECT_ROOT"/src/orchestrator/skills/*.py 1> /dev/null 2>&1; then
    chmod +x "$PROJECT_ROOT"/src/orchestrator/skills/*.py
    echo "✓ Skill scripts made executable"
fi
echo ""

# Create vault structure if it doesn't exist
echo "Setting up vault structure..."
mkdir -p "$VAULT_PATH"/{Inbox,Needs_Action,Done,Pending_Approval,Approved,Rejected,Plans,Logs,.state,.obsidian,Content_Calendar,Briefings}
mkdir -p "$CREDENTIALS_PATH"
echo "✓ Vault directories created"
echo "✓ Credentials directory created"
echo ""

# Create Dashboard.md if it doesn't exist
if [ ! -f "$VAULT_PATH/Dashboard.md" ]; then
    echo "Creating Dashboard.md..."
    cat > "$VAULT_PATH/Dashboard.md" << 'EOF'
# AI Employee Dashboard

## Last Updated
_Setup pending_

## System Status
- 🟢 File System Watcher: _Not started_
- 🟡 Gmail Watcher: _Not configured_
- 🟡 LinkedIn Watcher: _Not configured_

## Recent Activity
_No activity yet_

## Pending Actions
_No pending actions_

## Quick Links
- [Needs_Action](./Needs_Action/)
- [Pending_Approval](./Pending_Approval/)
- [Content_Calendar](./Content_Calendar/)
- [Logs](./Logs/)

---
*Dashboard auto-updates when watchers are running*
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
EOF
    echo "✓ Company_Handbook.md created"
else
    echo "✓ Company_Handbook.md already exists"
fi
echo ""

# Environment configuration
echo "=== Environment Configuration ==="
echo ""

ENV_FILE="$PROJECT_ROOT/.env"

if [ -f "$ENV_FILE" ]; then
    echo "✓ .env file already exists"
    read -p "Do you want to reconfigure? (y/N): " RECONFIGURE
    if [[ ! $RECONFIGURE =~ ^[Yy]$ ]]; then
        echo "Using existing .env configuration"
    else
        # Reconfigure
        echo ""
        echo "LinkedIn API Configuration"
        echo "Get credentials from: https://www.linkedin.com/developers/apps"
        echo ""
        read -p "LinkedIn Client ID: " LINKEDIN_CLIENT_ID
        read -p "LinkedIn Client Secret: " LINKEDIN_CLIENT_SECRET
        read -p "LinkedIn Redirect URI [http://localhost:8000/callback]: " LINKEDIN_REDIRECT
        LINKEDIN_REDIRECT=${LINKEDIN_REDIRECT:-http://localhost:8000/callback}

        # Update .env
        sed -i "s/^LINKEDIN_CLIENT_ID=.*/LINKEDIN_CLIENT_ID=$LINKEDIN_CLIENT_ID/" "$ENV_FILE"
        sed -i "s/^LINKEDIN_CLIENT_SECRET=.*/LINKEDIN_CLIENT_SECRET=$LINKEDIN_CLIENT_SECRET/" "$ENV_FILE"
        sed -i "s|^LINKEDIN_REDIRECT_URI=.*|LINKEDIN_REDIRECT_URI=$LINKEDIN_REDIRECT|" "$ENV_FILE"

        echo "✓ .env file updated"
    fi
else
    # Create new .env
    if [ -f "$PROJECT_ROOT/.env.example" ]; then
        cp "$PROJECT_ROOT/.env.example" "$ENV_FILE"
        echo "✓ Created .env from template"
        echo ""
        echo "Please edit .env file and add your credentials:"
        echo "  - LINKEDIN_CLIENT_ID"
        echo "  - LINKEDIN_CLIENT_SECRET"
        echo "  - GMAIL_CREDENTIALS_PATH (optional)"
        echo ""
    fi
fi
echo ""

# LinkedIn OAuth setup
echo "=== LinkedIn API Authentication ==="
echo ""

# Check if credentials are configured
if [ -f "$ENV_FILE" ]; then
    source "$ENV_FILE"
fi

if [ -z "$LINKEDIN_CLIENT_ID" ] || [ -z "$LINKEDIN_CLIENT_SECRET" ] || [ "$LINKEDIN_CLIENT_ID" = "your_client_id_here" ]; then
    echo "⚠ LinkedIn credentials not configured in .env"
    echo ""
    echo "To enable LinkedIn posting:"
    echo "1. Go to https://www.linkedin.com/developers/apps"
    echo "2. Create an app or select existing app"
    echo "3. Enable 'Share on LinkedIn' and 'Sign In with LinkedIn using OpenID Connect'"
    echo "4. Add redirect URI: http://localhost:8000/callback"
    echo "5. Copy Client ID and Client Secret to .env file"
    echo "6. Run: python scripts/setup_linkedin_api.py"
    echo ""
else
    # Check if already authenticated
    if [ -f "$CREDENTIALS_PATH/linkedin_api_token.json" ]; then
        echo "✓ LinkedIn already authenticated"
        echo "  Token: $CREDENTIALS_PATH/linkedin_api_token.json"
        echo ""
        read -p "Re-authenticate? (y/N): " REAUTH
        if [[ $REAUTH =~ ^[Yy]$ ]]; then
            echo ""
            echo "Run: python scripts/setup_linkedin_api.py"
            echo ""
        fi
    else
        echo "LinkedIn credentials found in .env"
        echo ""
        read -p "Authenticate with LinkedIn now? (Y/n): " DO_AUTH
        if [[ ! $DO_AUTH =~ ^[Nn]$ ]]; then
            echo ""
            python3 scripts/setup_linkedin_api.py
        else
            echo ""
            echo "You can authenticate later by running:"
            echo "  python scripts/setup_linkedin_api.py"
            echo ""
        fi
    fi
fi

# Gmail setup check
echo "=== Gmail Setup Check ==="
echo ""

if [ -f "$CREDENTIALS_PATH/gmail_credentials.json" ]; then
    echo "✓ Gmail credentials found"
    if [ -f "$CREDENTIALS_PATH/gmail_token.json" ]; then
        echo "✓ Gmail already authenticated"
    else
        echo "  Run Gmail watcher once to authenticate:"
        echo "  python -m src.watchers.run_gmail_watcher $VAULT_PATH"
    fi
else
    echo "⚠ Gmail credentials not found"
    echo ""
    echo "To enable Gmail monitoring:"
    echo "1. Go to https://console.cloud.google.com/apis/credentials"
    echo "2. Create OAuth 2.0 credentials"
    echo "3. Download and save to: $CREDENTIALS_PATH/gmail_credentials.json"
    echo "4. Run Gmail watcher to authenticate"
fi
echo ""

# Validation
echo "=== Validating Setup ==="
echo ""

validation_failed=0

# Check required directories
required_dirs=("Inbox" "Needs_Action" "Done" "Plans" "Pending_Approval" "Approved" "Rejected" "Logs" ".state" "Content_Calendar" "Briefings")
for dir in "${required_dirs[@]}"; do
    if [ ! -d "$VAULT_PATH/$dir" ]; then
        echo "✗ Missing directory: $dir"
        validation_failed=1
    fi
done

# Check required files
required_files=("Dashboard.md" "Company_Handbook.md")
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
echo "✓ Vault structure created"
echo "✓ Dashboard and handbook configured"
echo "✓ Setup validation passed"
echo ""
echo "Next steps:"
echo ""
echo "1. Configure credentials (edit .env with your keys):"
echo "   - LINKEDIN_CLIENT_ID / LINKEDIN_CLIENT_SECRET"
echo "   - TWITTER_API_KEY / TWITTER_API_SECRET / TWITTER_ACCESS_TOKEN / TWITTER_ACCESS_SECRET / TWITTER_BEARER_TOKEN"
echo "   - META_APP_ID / META_APP_SECRET / META_PAGE_ID / INSTAGRAM_BUSINESS_ACCOUNT_ID"
echo ""
echo "2. Authenticate LinkedIn:"
echo "   venv/bin/python scripts/setup_linkedin_api.py"
echo ""
echo "3. Authenticate Meta (Facebook + Instagram):"
echo "   venv/bin/python scripts/setup_meta_api.py"
echo ""
echo "4. Start all watchers:"
echo "   python -m src.orchestrator.watcher_manager $VAULT_PATH start"
echo ""
echo "5. Or start individual watchers:"
echo "   python -m src.watchers.run_filesystem_watcher $VAULT_PATH"
echo "   python -m src.watchers.run_gmail_watcher $VAULT_PATH"
echo "   python -m src.watchers.run_meta_watcher $VAULT_PATH"
echo "   python -m src.watchers.run_twitter_watcher $VAULT_PATH"
echo ""
echo "6. Set up cron jobs (Linux):"
echo "   bash scripts/setup_cron.sh"
echo ""
echo "7. Open Dashboard:"
echo "   $VAULT_PATH/Dashboard.md"
echo ""
