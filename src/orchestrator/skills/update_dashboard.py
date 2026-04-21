#!/usr/bin/env python3
"""
Agent Skill: Update Dashboard
Updates the Dashboard.md file with current status and activity
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

try:
    from .base_skill import BaseSkill, run_skill
except ImportError:
    from base_skill import BaseSkill, run_skill


class UpdateDashboardSkill(BaseSkill):
    """Skill to update the main dashboard"""

    def _execute_impl(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Update dashboard with provided information"""
        dashboard_path = self.vault_path / 'Dashboard.md'

        # Get parameters
        activity_log = params.get('activity_log', '')
        summary = params.get('summary', '')
        status = params.get('status', 'operational')

        # Read existing dashboard or create new one
        if dashboard_path.exists():
            content = self.read_file(dashboard_path)
        else:
            content = self._create_default_dashboard()

        # Update sections
        content = self._update_status(content, status)
        content = self._update_timestamp(content)

        if activity_log:
            content = self._add_activity(content, activity_log)

        if summary:
            content = self._update_summary(content, summary)

        # Add pending actions count
        content = self._update_pending_actions(content)

        # Write updated dashboard
        self.write_file(dashboard_path, content)

        self.logger.info(f"Dashboard updated with status: {status}")

        return {
            "dashboard_path": str(dashboard_path),
            "status": status,
            "activity_added": bool(activity_log),
            "summary_updated": bool(summary)
        }

    def _create_default_dashboard(self) -> str:
        """Create a default dashboard structure"""
        return """# AI Employee Dashboard

## System Status
Operational

## Last Updated
""" + datetime.now().strftime('%Y-%m-%d %H:%M') + """

## Pending Actions
No pending actions

## Recent Activity
No recent activity

## Summary
System is operational and ready to process tasks.
"""

    def _update_status(self, content: str, status: str) -> str:
        """Update the system status section"""
        status_map = {
            'operational': '✅ Operational',
            'processing': '⏳ Processing',
            'error': '❌ Error',
            'idle': '💤 Idle'
        }

        status_text = status_map.get(status, '⚪ Unknown')

        if "## System Status" in content:
            # Replace existing status
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if line.startswith("## System Status"):
                    # Find the next non-empty line
                    for j in range(i+1, len(lines)):
                        if lines[j].strip() and not lines[j].startswith('#'):
                            lines[j] = status_text
                            break
                    break
            content = '\n'.join(lines)
        else:
            # Add status section after title
            content = content.replace(
                "# AI Employee Dashboard",
                f"# AI Employee Dashboard\n\n## System Status\n{status_text}"
            )

        return content

    def _update_timestamp(self, content: str) -> str:
        """Update the last updated timestamp"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')

        if "## Last Updated" in content:
            # Replace existing timestamp
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if line.startswith("## Last Updated"):
                    # Find the next non-empty line
                    for j in range(i+1, len(lines)):
                        if lines[j].strip() and not lines[j].startswith('#'):
                            lines[j] = timestamp
                            break
                    break
            content = '\n'.join(lines)
        else:
            # Add timestamp after status
            content = content.replace(
                "## System Status",
                f"## System Status\n\n## Last Updated\n{timestamp}"
            )

        return content

    def _add_activity(self, content: str, activity: str) -> str:
        """Add activity to the recent activity section"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
        activity_line = f"- [{timestamp}] {activity}"

        if "## Recent Activity" in content:
            # Add to existing section
            lines = content.split('\n')
            insert_pos = None

            for i, line in enumerate(lines):
                if line.startswith("## Recent Activity"):
                    # Find where to insert (after header, before next section)
                    for j in range(i+1, len(lines)):
                        if lines[j].startswith('#'):
                            insert_pos = j
                            break
                        elif lines[j].strip() == "" and j > i+1:
                            insert_pos = j
                            break

                    if insert_pos is None:
                        insert_pos = len(lines)

                    lines.insert(insert_pos, activity_line)
                    break

            content = '\n'.join(lines)
        else:
            # Add new section
            content += f"\n\n## Recent Activity\n{activity_line}"

        return content

    def _update_summary(self, content: str, summary: str) -> str:
        """Update the summary section"""
        if "## Summary" in content:
            # Replace existing summary
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if line.startswith("## Summary"):
                    # Find the next section or end
                    end_pos = len(lines)
                    for j in range(i+1, len(lines)):
                        if lines[j].startswith('#'):
                            end_pos = j
                            break

                    # Replace summary content
                    lines[i+1:end_pos] = [f"\n{summary}\n"]
                    break

            content = '\n'.join(lines)
        else:
            # Add new summary section
            content += f"\n\n## Summary\n\n{summary}"

        return content

    def _update_pending_actions(self, content: str) -> str:
        """Update pending actions count"""
        needs_action_dir = self.vault_path / 'Needs_Action'
        pending_approval_dir = self.vault_path / 'Pending_Approval'

        needs_action_count = 0
        pending_approval_count = 0

        if needs_action_dir.exists():
            needs_action_count = len([f for f in needs_action_dir.glob('*.md') if not f.name.startswith('.')])

        if pending_approval_dir.exists():
            pending_approval_count = len([f for f in pending_approval_dir.glob('*.md') if not f.name.startswith('.')])

        total_pending = needs_action_count + pending_approval_count

        if total_pending == 0:
            pending_text = "No pending actions"
        else:
            pending_text = f"{total_pending} pending actions"
            if needs_action_count > 0:
                pending_text += f" ({needs_action_count} in Needs_Action"
            if pending_approval_count > 0:
                if needs_action_count > 0:
                    pending_text += f", {pending_approval_count} awaiting approval"
                else:
                    pending_text += f" ({pending_approval_count} awaiting approval"
                pending_text += ")"
            elif needs_action_count > 0:
                pending_text += ")"

        if "## Pending Actions" in content:
            # Replace existing
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if line.startswith("## Pending Actions"):
                    # Find the next section or empty line
                    for j in range(i+1, len(lines)):
                        if lines[j].strip() and not lines[j].startswith('#'):
                            lines[j] = pending_text
                            break
                    break
            content = '\n'.join(lines)
        else:
            # Add after last updated
            content = content.replace(
                "## Last Updated",
                f"## Last Updated\n\n## Pending Actions\n{pending_text}"
            )

        return content


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python update_dashboard.py '<json_params>'")
        sys.exit(1)

    run_skill(UpdateDashboardSkill, sys.argv[1])