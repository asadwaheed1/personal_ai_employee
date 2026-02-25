#!/bin/bash

# Stop script for AI Employee Bronze Tier

set -e

echo "=== Stopping AI Employee System ==="
echo ""

# Kill all processes by PID files
PID_DIR="/tmp/ai_employee_pids"

if [ -d "$PID_DIR" ]; then
    for pid_file in "$PID_DIR"/*.pid; do
        if [ -f "$pid_file" ]; then
            PID=$(cat "$pid_file")
            PROCESS_NAME=$(basename "$pid_file" .pid)

            if ps -p $PID > /dev/null 2>&1; then
                echo "Stopping $PROCESS_NAME (PID: $PID)..."
                kill $PID 2>/dev/null || true
                sleep 1

                # Force kill if still running
                if ps -p $PID > /dev/null 2>&1; then
                    echo "Force stopping $PROCESS_NAME..."
                    kill -9 $PID 2>/dev/null || true
                fi
            fi

            rm -f "$pid_file"
        fi
    done
fi

# Also kill watchdog if running
WATCHDOG_PID=$(pgrep -f "watchdog.py" || true)
if [ ! -z "$WATCHDOG_PID" ]; then
    echo "Stopping watchdog (PID: $WATCHDOG_PID)..."
    kill $WATCHDOG_PID 2>/dev/null || true
fi

echo ""
echo "✓ All processes stopped"
echo ""
