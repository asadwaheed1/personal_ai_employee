#!/bin/bash
# Ralph Wiggum stop hook
# Only activates when /tmp/ralph_wiggum session file exists.
# Injects continuation prompt if pending work remains; exits silently when done.

SESSION_FILE="/tmp/ralph_wiggum"
VAULT_PATH="/home/asad/piaic/projects/personal_ai_employee/ai_employee_vault"

if [ ! -f "$SESSION_FILE" ]; then
    exit 0
fi

# Parse session state
MAX_ITER=$(python3 -c "import json; d=json.load(open('$SESSION_FILE')); print(d.get('max_iter', 10))" 2>/dev/null || echo 10)
ITER=$(python3 -c "import json; d=json.load(open('$SESSION_FILE')); print(d.get('iter', 0))" 2>/dev/null || echo 0)
CHECK_TYPE=$(python3 -c "import json; d=json.load(open('$SESSION_FILE')); print(d.get('check_type', 'needs_action'))" 2>/dev/null || echo "needs_action")
TASK=$(python3 -c "import json; d=json.load(open('$SESSION_FILE')); print(d.get('task', 'Process pending items'))" 2>/dev/null || echo "Process pending items")
DONE_SIGNAL=$(python3 -c "import json; d=json.load(open('$SESSION_FILE')); print(d.get('done_signal', ''))" 2>/dev/null || echo "")

if [ "$ITER" -ge "$MAX_ITER" ]; then
    echo "[Ralph Wiggum] Max iterations ($MAX_ITER) reached. Stopping." >&2
    rm -f "$SESSION_FILE"
    exit 0
fi

# Check completion
COMPLETE=false

if [ "$CHECK_TYPE" = "done_file" ] && [ -n "$DONE_SIGNAL" ]; then
    if [ -f "$VAULT_PATH/Done/$DONE_SIGNAL" ]; then
        COMPLETE=true
    fi
elif [ "$CHECK_TYPE" = "needs_action" ]; then
    PENDING=$(find "$VAULT_PATH/Needs_Action" -maxdepth 1 \
        \( -name "EMAIL_*.md" -o -name "LINKEDIN_*.md" -o -name "TWITTER_*.md" -o -name "META_*.md" \) \
        2>/dev/null | wc -l)
    if [ "$PENDING" -eq 0 ]; then
        COMPLETE=true
    fi
fi

if [ "$COMPLETE" = true ]; then
    rm -f "$SESSION_FILE"
    exit 0
fi

# Increment iteration counter
NEW_ITER=$((ITER + 1))
python3 -c "
import json
with open('$SESSION_FILE') as f:
    d = json.load(f)
d['iter'] = $NEW_ITER
with open('$SESSION_FILE', 'w') as f:
    json.dump(d, f)
" 2>/dev/null

# Count pending items for context
PENDING=$(find "$VAULT_PATH/Needs_Action" -maxdepth 1 \
    \( -name "EMAIL_*.md" -o -name "LINKEDIN_*.md" -o -name "TWITTER_*.md" -o -name "META_*.md" \) \
    2>/dev/null | wc -l)

echo "Continue task (iteration $NEW_ITER/$MAX_ITER): $TASK. ${PENDING} files still pending in Needs_Action/. Process remaining files and update Dashboard.md when done."
