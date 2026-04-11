#!/bin/bash
# Setup cron jobs for AI Employee scheduling
# Run this script to configure automated tasks

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
VAULT_PATH="${PROJECT_DIR}/ai_employee_vault"

echo "Setting up AI Employee cron jobs..."
echo "Project directory: $PROJECT_DIR"
echo "Vault path: $VAULT_PATH"
echo ""

# Check if running on Linux/Mac
if [[ "$OSTYPE" != "linux-gnu"* ]] && [[ "$OSTYPE" != "darwin"* ]]; then
    echo "Error: This script is for Linux/Mac only"
    echo "For Windows, use setup_task_scheduler.ps1"
    exit 1
fi

# Check if crontab is available
if ! command -v crontab &> /dev/null; then
    echo "Error: crontab not found. Please install cron."
    exit 1
fi

# Create backup of existing crontab
if crontab -l &> /dev/null; then
    echo "Creating backup of existing crontab..."
    crontab -l > "$PROJECT_DIR/cron_backup_$(date +%Y%m%d_%H%M%S).txt"
fi

# Build new crontab entries
PYTHON_PATH=$(which python3)
CRON_ENTRIES="# AI Employee - Automated Tasks
# Generated: $(date)
# Project: $PROJECT_DIR

# Environment variables
SHELL=/bin/bash
PATH=/usr/local/bin:/usr/bin:/bin:$HOME/.local/bin
VAULT_PATH=$VAULT_PATH

# Daily content calendar check (run every hour)
# This checks if any posts are due and creates approval requests
0 * * * * cd \"$PROJECT_DIR\" && $PYTHON_PATH -m src.orchestrator.skills.create_content_plan '{\"action\": \"check_calendar\", \"vault_path\": \"$VAULT_PATH\"}' >> \"$VAULT_PATH/Logs/calendar_cron.log\" 2>&1

# Daily LinkedIn post at 9:00 AM (only on weekdays)
# Posts business content to generate sales
0 9 * * 1-5 cd \"$PROJECT_DIR\" && $PYTHON_PATH -m src.orchestrator.skills.post_linkedin '{\"action\": \"check_calendar\", \"vault_path\": \"$VAULT_PATH\"}' >> \"$VAULT_PATH/Logs/linkedin_cron.log\" 2>&1

# Weekly content planning (Sundays at 6:00 PM)
# Generates content calendar for the upcoming week
0 18 * * 0 cd \"$PROJECT_DIR\" && $PYTHON_PATH -m src.orchestrator.skills.create_content_plan '{\"num_posts\": 5, \"vault_path\": \"$VAULT_PATH\"}' >> \"$VAULT_PATH/Logs/content_plan_cron.log\" 2>&1

# Process approved actions every 15 minutes
# Checks /Approved/ folder and executes actions
*/15 * * * * cd \"$PROJECT_DIR\" && $PYTHON_PATH -m src.orchestrator.skills.process_approved_actions '{\"vault_path\": \"$VAULT_PATH\"}' >> \"$VAULT_PATH/Logs/approved_actions_cron.log\" 2>&1

# Daily dashboard update at 8:00 AM
# Updates dashboard with current status
0 8 * * * $PYTHON_PATH \"$PROJECT_DIR/scripts/dashboard_update.py\" >> \"$VAULT_PATH/Logs/dashboard_cron.log\" 2>&1

# End of AI Employee cron jobs
"

echo "The following cron jobs will be added:"
echo "========================================"
echo "$CRON_ENTRIES"
echo ""
echo "========================================"
echo ""

# Ask for confirmation
read -p "Do you want to add these cron jobs? (y/n): " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled. No changes made."
    exit 0
fi

# Add to crontab
if crontab -l &> /dev/null; then
    # Append to existing crontab
    (crontab -l; echo "$CRON_ENTRIES") | crontab -
else
    # Create new crontab
    echo "$CRON_ENTRIES" | crontab -
fi

echo ""
echo "Cron jobs installed successfully!"
echo ""
echo "Current crontab:"
crontab -l
echo ""
echo "To edit: crontab -e"
echo "To remove all: crontab -r"
echo ""
echo "Logs will be written to: $VAULT_PATH/Logs/"
