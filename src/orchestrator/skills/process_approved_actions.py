#!/usr/bin/env python3
"""
Agent Skill: Process Approved Actions
Executes approved actions from the Approved folder
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

from base_skill import BaseSkill, run_skill


class ProcessApprovedActionsSkill(BaseSkill):
    """Skill to process and execute approved actions"""

    def _execute_impl(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Process and execute approved actions"""
        files = params.get('files', [])

        # If no specific files provided, process all .md files in Approved
        if not files:
            approved_dir = self.vault_path / 'Approved'
            if approved_dir.exists():
                files = [str(f) for f in approved_dir.glob('*.md') if not f.name.startswith('.')]

        if not files:
            self.logger.info("No approved actions to process")
            return {"processed_count": 0, "message": "No approved actions"}

        # Process each approved action
        processed_count = 0
        execution_results = []

        for file_path in files:
            file_path = Path(file_path)
            if not file_path.exists():
                self.logger.warning(f"File not found: {file_path}")
                continue

            try:
                # Read approval file
                content = self.read_file(file_path)
                self.logger.info(f"Processing approved action: {file_path.name}")

                # Extract approval details
                approval_data = self._parse_approval_file(content, file_path.name)

                # Execute the approved action
                result = self._execute_approved_action(approval_data, content)

                execution_results.append({
                    "file": file_path.name,
                    "action": approval_data.get('action', 'unknown'),
                    "result": result
                })

                # Move original approval file to Done with execution summary
                self._archive_approval_file(file_path, approval_data, result)

                processed_count += 1
                self.logger.info(f"Successfully executed approved action: {file_path.name}")

            except Exception as e:
                self.logger.error(f"Failed to execute approved action {file_path}: {e}")
                execution_results.append({
                    "file": file_path.name,
                    "error": str(e)
                })
                continue

        # Update dashboard
        self._update_dashboard(processed_count, execution_results)

        # Log to audit trail
        self._log_audit_trail(execution_results)

        return {
            "processed_count": processed_count,
            "execution_results": execution_results
        }

    def _parse_approval_file(self, content: str, filename: str) -> Dict[str, Any]:
        """Parse approval file to extract action details"""
        approval_data = {"id": filename.replace('.md', '')}

        # Extract frontmatter
        if content.startswith('---'):
            try:
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    import yaml
                    metadata = yaml.safe_load(parts[1]) or {}
                    approval_data.update(metadata)
            except Exception as e:
                self.logger.warning(f"Failed to parse approval metadata: {e}")

        # Extract action type from content
        import re
        action_match = re.search(r'Action Type:\s*(.+?)\n', content)
        if action_match:
            approval_data['action'] = action_match.group(1).strip()

        # Extract decision
        decision_match = re.search(r'- \[x\] (\*\*Approved\*\*|\*\*Rejected\*\*)', content)
        if decision_match:
            approval_data['decision'] = decision_match.group(1)

        return approval_data

    def _execute_approved_action(self, approval_data: Dict[str, Any], content: str) -> Dict[str, Any]:
        """Execute the approved action based on type"""
        action_type = approval_data.get('action', '').lower()

        if 'payment' in action_type:
            return self._execute_payment_action(approval_data, content)
        elif 'email' in action_type:
            return self._execute_email_action(approval_data, content)
        elif 'file' in action_type or 'delete' in action_type:
            return self._execute_file_action(approval_data, content)
        elif 'system' in action_type:
            return self._execute_system_action(approval_data, content)
        else:
            return self._execute_generic_action(approval_data, content)

    def _execute_payment_action(self, approval_data: Dict[str, Any], content: str) -> Dict[str, Any]:
        """Execute a payment action (Bronze tier - logging only)"""
        # In Bronze tier, we only log the action
        # Actual payment execution requires MCP servers (Silver/Gold tier)

        return {
            "status": "logged",
            "message": "Payment action approved and logged (MCP execution requires Silver tier)",
            "action": "payment",
            "details": approval_data
        }

    def _execute_email_action(self, approval_data: Dict[str, Any], content: str) -> Dict[str, Any]:
        """Execute an email action (Bronze tier - logging only)"""
        # In Bronze tier, we only log the action
        # Actual email sending requires MCP servers (Silver/Gold tier)

        return {
            "status": "logged",
            "message": "Email action approved and logged (MCP execution requires Silver tier)",
            "action": "email",
            "details": approval_data
        }

    def _execute_file_action(self, approval_data: Dict[str, Any], content: str) -> Dict[str, Any]:
        """Execute a file-related action"""
        # For Bronze tier, we can handle basic file operations

        action = approval_data.get('action', '')

        if 'delete' in action:
            # Log deletion for now (actual deletion would be handled by orchestrator)
            return {
                "status": "logged",
                "message": "File deletion approved - logged for execution",
                "action": "file_delete",
                "details": approval_data
            }
        else:
            return {
                "status": "logged",
                "message": "File action approved and logged",
                "action": action,
                "details": approval_data
            }

    def _execute_system_action(self, approval_data: Dict[str, Any], content: str) -> Dict[str, Any]:
        """Execute a system-related action"""
        return {
            "status": "logged",
            "message": "System change approved - logged for execution",
            "action": "system_change",
            "details": approval_data
        }

    def _execute_generic_action(self, approval_data: Dict[str, Any], content: str) -> Dict[str, Any]:
        """Execute a generic approved action"""
        return {
            "status": "completed",
            "message": "Generic action approved and processed",
            "action": "generic",
            "details": approval_data
        }

    def _archive_approval_file(self, file_path: Path, approval_data: Dict[str, Any], result: Dict[str, Any]):
        """Move approval file to Done with execution summary"""
        content = self.read_file(file_path)

        # Add execution summary
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')

        # Convert result to JSON-serializable format
        def json_serializable(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError(f"Type {type(obj)} not serializable")

        try:
            result_json = json.dumps(result, indent=2, default=json_serializable)
        except Exception as e:
            result_json = json.dumps({"error": f"Could not serialize result: {str(e)}"})

        summary = f"""

---
## Execution Summary
**Executed**: {timestamp}
**Status**: {result.get('status', 'unknown')}
**Result**: {result.get('message', 'No message')}

### Execution Details
```json
{result_json}
```
"""

        # Append summary
        content += summary

        # Write to Done folder
        done_path = self.vault_path / 'Done' / f"EXECUTED_{file_path.name}"
        self.write_file(done_path, content)

        # Remove from Approved folder
        file_path.unlink()

        self.logger.info(f"Archived approval file to: {done_path.name}")

    def _update_dashboard(self, processed_count: int, execution_results: list):
        """Update dashboard with execution results"""
        dashboard_path = self.vault_path / 'Dashboard.md'

        # Read current dashboard
        if dashboard_path.exists():
            content = self.read_file(dashboard_path)
        else:
            content = "# AI Employee Dashboard\n\n## Status\nOperational\n"

        # Add new activity
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        successful = sum(1 for r in execution_results if 'error' not in r)
        activity = f"Executed {processed_count} approved actions ({successful} successful)"

        activity_line = f"- [{timestamp}] {activity}"

        # Find or create Recent Activity section
        if "## Recent Activity" in content:
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if line.startswith("## Recent Activity"):
                    # Insert after header
                    lines.insert(i + 1, activity_line)
                    break
            content = '\n'.join(lines)
        else:
            content += f"\n\n## Recent Activity\n{activity_line}"

        self.write_file(dashboard_path, content)
        self.logger.info(f"Updated dashboard with execution results")

    def _log_audit_trail(self, execution_results: list):
        """Log execution to audit trail"""
        audit_dir = self.vault_path / 'Logs'
        audit_dir.mkdir(exist_ok=True)

        audit_file = audit_dir / f'audit_{datetime.now().strftime("%Y-%m-%d")}.json'

        # Read existing audit or create new
        if audit_file.exists():
            try:
                with open(audit_file, 'r') as f:
                    audit_log = json.load(f)
            except:
                audit_log = []
        else:
            audit_log = []

        # Add new entries
        for result in execution_results:
            audit_entry = {
                "timestamp": datetime.now().isoformat(),
                "type": "approved_action_execution",
                "result": result
            }
            audit_log.append(audit_entry)

        # Write audit log
        with open(audit_file, 'w') as f:
            json.dump(audit_log, f, indent=2)

        self.logger.info(f"Updated audit trail: {audit_file.name}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python process_approved_actions.py '<json_params>'")
        sys.exit(1)

    run_skill(ProcessApprovedActionsSkill, sys.argv[1])