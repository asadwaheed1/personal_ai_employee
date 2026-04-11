#!/bin/bash

# Start script for AI Employee (all watchers via Watcher Manager)

set -e

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$SCRIPT_DIR"
VAULT_PATH="$PROJECT_ROOT/ai_employee_vault"

echo "=== Starting AI Employee System ==="
echo ""
echo "Vault: $VAULT_PATH"
echo ""

# Check if vault exists
if [ ! -d "$VAULT_PATH" ]; then
    echo "Error: Vault not found at $VAULT_PATH"
    echo "Please run ./setup.sh first"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "$PROJECT_ROOT/venv" ]; then
    echo "Error: Virtual environment not found"
    echo "Please run ./setup.sh first"
    exit 1
fi

# Start Watcher Manager (starts filesystem, Gmail, and LinkedIn watchers)
echo "Starting watcher manager..."
"$PROJECT_ROOT/venv/bin/python" -m src.orchestrator.watcher_manager "$VAULT_PATH" start &
MANAGER_PID=$!

echo "✓ Watcher manager started (PID: $MANAGER_PID)"
echo ""
echo "System is now running!"
echo ""
echo "Monitoring:"
echo "  - Inbox: $VAULT_PATH/Inbox"
echo "  - Needs_Action: $VAULT_PATH/Needs_Action"
echo "  - Approved: $VAULT_PATH/Approved"
echo ""
echo "Logs: $VAULT_PATH/Logs"
echo ""
echo "To stop the system, run: ./stop.sh"
echo "Or press Ctrl+C"
echo ""
echo "=== Live Activity Log ==="
echo ""

# Wait for watcher manager log file to be created
sleep 2

# Tail the watcher manager log to show real-time activity
LOG_FILE="$VAULT_PATH/Logs/watcher_manager_$(date +%Y-%m-%d).log"
tail -f "$LOG_FILE" 2>/dev/null &
TAIL_PID=$!

# Wait for interrupt
trap "echo ''; echo 'Stopping...'; kill $TAIL_PID 2>/dev/null; kill $MANAGER_PID 2>/dev/null; exit 0" INT TERM

wait $MANAGER_PID
