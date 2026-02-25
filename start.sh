#!/bin/bash

# Start script for AI Employee Bronze Tier

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

# Start the watchdog (which will start all other processes)
echo "Starting watchdog process..."
python3 "$PROJECT_ROOT/src/orchestrator/watchdog.py" "$VAULT_PATH" 60 &
WATCHDOG_PID=$!

echo "✓ Watchdog started (PID: $WATCHDOG_PID)"
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

# Wait for interrupt
trap "echo ''; echo 'Stopping...'; kill $WATCHDOG_PID 2>/dev/null; exit 0" INT TERM

wait $WATCHDOG_PID
