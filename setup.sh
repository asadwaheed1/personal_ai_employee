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

# Check Python version
echo "Checking Python version..."
python3 --version || { echo "Python 3 is required but not installed."; exit 1; }
echo ""

# Install Python dependencies
echo "Installing Python dependencies..."
pip3 install -r requirements.txt
echo ""

# Create vault structure if it doesn't exist
echo "Setting up vault structure..."
mkdir -p "$VAULT_PATH"/{Inbox,Needs_Action,Done,Pending_Approval,Approved,Rejected,Plans,Logs,.state}
echo "✓ Vault directories created"
echo ""

# Create drop folder for file system watcher
echo "Creating drop folder..."
mkdir -p "$VAULT_PATH/Inbox"
echo "✓ Drop folder created at: $VAULT_PATH/Inbox"
echo ""

# Check if Dashboard.md exists
if [ ! -f "$VAULT_PATH/Dashboard.md" ]; then
    echo "Dashboard.md not found, it should have been created already."
fi

# Check if Company_Handbook.md exists
if [ ! -f "$VAULT_PATH/Company_Handbook.md" ]; then
    echo "Company_Handbook.md not found, it should have been created already."
fi

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Next steps:"
echo "1. Review the vault at: $VAULT_PATH"
echo "2. Customize Company_Handbook.md with your rules"
echo "3. Start the system with: ./start.sh"
echo ""
