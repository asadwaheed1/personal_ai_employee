#!/bin/bash
# Start a Ralph Wiggum autonomous loop session.
# Usage:
#   ./scripts/start_ralph_wiggum.sh "Process all pending emails"
#   ./scripts/start_ralph_wiggum.sh "Generate CEO briefing" done_file "2026-04-28_Monday_Briefing.md"
#
# check_type values:
#   needs_action  — stops when Needs_Action/ has no EMAIL_/LINKEDIN_/TWITTER_/META_ files (default)
#   done_file     — stops when ai_employee_vault/Done/<done_signal> exists

set -euo pipefail

TASK="${1:-Process all pending items}"
CHECK_TYPE="${2:-needs_action}"
DONE_SIGNAL="${3:-}"
MAX_ITER="${MAX_ITERATIONS:-10}"
SESSION_FILE="/tmp/ralph_wiggum"
VAULT_PATH="/home/asad/piaic/projects/personal_ai_employee/ai_employee_vault"

python3 -c "
import json
d = {
    'task': '$TASK',
    'check_type': '$CHECK_TYPE',
    'done_signal': '$DONE_SIGNAL',
    'max_iter': $MAX_ITER,
    'iter': 0,
    'vault_path': '$VAULT_PATH'
}
with open('$SESSION_FILE', 'w') as f:
    json.dump(d, f, indent=2)
print(f'[Ralph Wiggum] Session started: {d}')
"

echo ""
echo "Ralph Wiggum session active. Now run:"
echo "  claude \"$TASK\""
echo ""
echo "Claude will loop until completion or $MAX_ITER iterations."
echo "To cancel: rm $SESSION_FILE"
