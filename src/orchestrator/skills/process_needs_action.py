#!/usr/bin/env python3
"""
Agent Skill: Process Needs Action
Processes files in the Needs_Action directory and updates dashboard
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

from datetime import timedelta
from datetime import timedelta
from base_skill import BaseSkill, run_skill


class ProcessNeedsActionSkill(BaseSkill):
    """Skill to process files in Needs_Action directory"""

    def _execute_impl(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Process all files in Needs_Action"""
        files = params.get('files', [])

        # If no specific files provided, process all .md files in Needs_Action
        if not files:
            needs_action_dir = self.vault_path / 'Needs_Action'
            if needs_action_dir.exists():
                files = [str(f) for f in needs_action_dir.glob('*.md') if not f.name.startswith('.')]

        if not files:
            self.logger.info("No files to process in Needs_Action")
            return {"processed_count": 0, "message": "No files to process"}

        # Process each file
        processed_count = 0
        for file_path in files:
            file_path = Path(file_path)
            if not file_path.exists():
                self.logger.warning(f"File not found: {file_path}")
                continue

            try:
                # Read and process the file
                content = self.read_file(file_path)
                self.logger.info(f"Processing file: {file_path.name}")

                # Extract metadata from frontmatter if present
                metadata = self._extract_metadata(content)

                # Create a plan if needed
                if metadata.get('type') == 'task' or 'plan' in metadata:
                    self._create_plan_for_file(file_path, content, metadata)

                # Check if approval is needed
                if self._requires_approval(metadata):
                    self._create_approval_request(file_path, content, metadata)

                # Move file to Done
                done_path = self.vault_path / 'Done' / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file_path.name}"
                self.move_file(file_path, done_path)

                processed_count += 1
                self.logger.info(f"Successfully processed: {file_path.name}")

            except Exception as e:
                self.logger.error(f"Failed to process {file_path}: {e}")
                continue

        # Update dashboard
        self._update_dashboard(processed_count)

        return {
            "processed_count": processed_count,
            "files_processed": files[:processed_count]  # Return only successfully processed
        }

    def _extract_metadata(self, content: str) -> Dict[str, Any]:
        """Extract YAML frontmatter metadata"""
        metadata = {}
        if content.startswith('---'):
            try:
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    import yaml
                    metadata = yaml.safe_load(parts[1]) or {}
            except Exception as e:
                self.logger.warning(f"Failed to parse metadata: {e}")
        return metadata

    def _create_plan_for_file(self, file_path: Path, content: str, metadata: Dict[str, Any]):
        """Create a plan file for complex tasks"""
        plan_content = f"""---
created: {datetime.now().isoformat()}
source_file: {file_path.name}
status: pending
type: plan
---

# Action Plan for {file_path.name}

## Task Description
{metadata.get('description', 'Process file ' + file_path.name)}

## Steps
- [ ] Review file content
- [ ] Determine required actions
- [ ] Execute actions
- [ ] Update dashboard
- [ ] Mark complete

## Metadata
```json
{json.dumps(metadata, indent=2)}
```

## File Content Summary
{content[:500]}{'...' if len(content) > 500 else ''}
"""

        plan_path = self.vault_path / 'Plans' / f"PLAN_{file_path.stem}.md"
        self.write_file(plan_path, plan_content)
        self.logger.info(f"Created plan: {plan_path.name}")

    def _requires_approval(self, metadata: Dict[str, Any]) -> bool:
        """Check if action requires approval based on metadata"""
        # Check Company Handbook for approval rules
        handbook_path = self.vault_path / 'Company_Handbook.md'
        if handbook_path.exists():
            handbook_content = self.read_file(handbook_path)
            # Simple heuristic - can be made more sophisticated
            if 'payment' in str(metadata).lower() or 'financial' in str(metadata).lower():
                return True
        return metadata.get('requires_approval', False)

    def _create_approval_request(self, file_path: Path, content: str, metadata: Dict[str, Any]):
        """Create an approval request file"""
        approval_content = f"""---
type: approval_request
action: process_file
file: {file_path.name}
created: {datetime.now().isoformat()}
status: pending
expires: {(datetime.now() + timedelta(hours=24)).isoformat()}
---

# Approval Request

## File to Process
**Name**: {file_path.name}
**Type**: {metadata.get('type', 'unknown')}
**Priority**: {metadata.get('priority', 'normal')}

## Content Summary
{content[:300]}{'...' if len(content) > 300 else ''}

## Reason for Approval
This file contains content that may require human review before processing.

## Actions to Take
- Review the file content above
- Determine if processing should proceed
- Move this file to /Approved/ to approve
- Move this file to /Rejected/ to reject
"""

        approval_path = self.vault_path / 'Pending_Approval' / f"APPROVAL_{file_path.name}"
        self.write_file(approval_path, approval_content)
        self.logger.info(f"Created approval request: {approval_path.name}")

    def _update_dashboard(self, processed_count: int):
        """Update dashboard with processing results"""
        dashboard_path = self.vault_path / 'Dashboard.md'

        # Read current dashboard
        if dashboard_path.exists():
            content = self.read_file(dashboard_path)
        else:
            content = "# AI Employee Dashboard\n\n## Status\nOperational\n"

        # Add new activity
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        new_activity = f"- [{timestamp}] Processed {processed_count} files from Needs_Action"

        # Find Activities section or create it
        if "## Recent Activity" in content:
            parts = content.split("## Recent Activity")
            if len(parts) == 2:
                before = parts[0]
                after = parts[1]
                # Add new activity at the top of the list
                lines = after.split('\n')
                insert_pos = 0
                for i, line in enumerate(lines):
                    if line.strip() and not line.startswith('-') and not line.startswith(' '):
                        insert_pos = i
                        break
                lines.insert(insert_pos, new_activity)
                content = before + "## Recent Activity\n" + '\n'.join(lines)
        else:
            content += f"\n## Recent Activity\n{new_activity}\n"

        # Update last updated timestamp
        if "## Last Updated" in content:
            content = content.replace(
                "## Last Updated",
                f"## Last Updated\n{datetime.now().strftime('%Y-%m-%d %H:%M')}"
            )
        else:
            content = content.replace(
                "# AI Employee Dashboard",
                f"# AI Employee Dashboard\n\n## Last Updated\n{datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
            )

        self.write_file(dashboard_path, content)
        self.logger.info(f"Updated dashboard with {processed_count} processed files")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python process_needs_action.py '<json_params>'")
        sys.exit(1)

    run_skill(ProcessNeedsActionSkill, sys.argv[1])