#!/usr/bin/env python3
"""
Agent Skill: Process Inbox
Processes files dropped in the Inbox folder
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

from base_skill import BaseSkill, run_skill


class ProcessInboxSkill(BaseSkill):
    """Skill to process files in Inbox directory"""

    def _execute_impl(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Process all files in Inbox"""
        files = params.get('files', [])

        # If no specific files provided, process all .md files in Inbox
        if not files:
            inbox_dir = self.vault_path / 'Inbox'
            if inbox_dir.exists():
                files = [str(f) for f in inbox_dir.glob('*.md') if not f.name.startswith('.')]

        if not files:
            self.logger.info("No files to process in Inbox")
            return {"processed_count": 0, "message": "No files to process"}

        # Process each file
        processed_count = 0
        needs_action_count = 0

        for file_path in files:
            file_path = Path(file_path)
            if not file_path.exists():
                self.logger.warning(f"File not found: {file_path}")
                continue

            try:
                # Read file content
                content = self.read_file(file_path)
                self.logger.info(f"Processing inbox file: {file_path.name}")

                # Extract metadata
                metadata = self._extract_metadata(content)

                # Determine where to move the file
                if self._requires_needs_action(metadata, content):
                    # Move to Needs_Action for further processing
                    target_dir = self.vault_path / 'Needs_Action'
                    needs_action_count += 1
                else:
                    # Move directly to Done
                    target_dir = self.vault_path / 'Done'

                # Generate unique filename
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                target_path = target_dir / f"{timestamp}_{file_path.name}"

                # Move file
                self.move_file(file_path, target_path)

                # Create metadata file if going to Needs_Action
                if target_dir.name == 'Needs_Action':
                    self._create_metadata_file(target_path, metadata, content)

                processed_count += 1
                self.logger.info(f"Moved {file_path.name} to {target_dir.name}")

            except Exception as e:
                self.logger.error(f"Failed to process {file_path}: {e}")
                continue

        # Update dashboard
        self._update_dashboard(processed_count, needs_action_count)

        return {
            "processed_count": processed_count,
            "moved_to_needs_action": needs_action_count,
            "moved_to_done": processed_count - needs_action_count,
            "files_processed": files[:processed_count]
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

    def _requires_needs_action(self, metadata: Dict[str, Any], content: str) -> bool:
        """Determine if file needs further processing"""
        # Check metadata flags
        if metadata.get('requires_processing', False):
            return True

        if metadata.get('priority') in ['high', 'urgent']:
            return True

        # Check content for keywords
        content_lower = content.lower()
        processing_keywords = [
            'task:', 'action:', 'process:', 'approve', 'payment',
            'urgent', 'important', 'deadline', 'schedule'
        ]

        if any(keyword in content_lower for keyword in processing_keywords):
            return True

        # Check if it's a simple note
        if len(content.split('\n')) <= 3 and not metadata:
            return False

        return True

    def _create_metadata_file(self, original_path: Path, metadata: Dict[str, Any], content: str):
        """Create a metadata file for files moved to Needs_Action"""
        meta_content = f"""---
source_file: {original_path.name}
source_type: inbox_drop
created: {datetime.now().isoformat()}
status: pending
priority: {metadata.get('priority', 'normal')}
---

# Inbox File Processing

## Original File
**Name**: {original_path.name}
**Dropped**: {datetime.now().strftime('%Y-%m-%d %H:%M')}

## Content Summary
{content[:300]}{'...' if len(content) > 300 else ''}

## Processing Required
This file was moved from Inbox to Needs_Action for further processing.
Please review and take appropriate action.

## Suggested Actions
- [ ] Review file content
- [ ] Determine processing requirements
- [ ] Execute necessary actions
- [ ] Move to Done when complete
"""

        # Create metadata file with same name but add _META
        meta_path = original_path.parent / f"{original_path.stem}_META.md"
        self.write_file(meta_path, meta_content)
        self.logger.info(f"Created metadata file: {meta_path.name}")

    def _update_dashboard(self, processed_count: int, needs_action_count: int):
        """Update dashboard with processing results"""
        dashboard_path = self.vault_path / 'Dashboard.md'

        # Read current dashboard
        if dashboard_path.exists():
            content = self.read_file(dashboard_path)
        else:
            content = "# AI Employee Dashboard\n\n## Status\nOperational\n"

        # Add new activity
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        if needs_action_count > 0:
            activity = f"Processed {processed_count} inbox files ({needs_action_count} moved to Needs_Action)"
        else:
            activity = f"Processed {processed_count} inbox files (all moved to Done)"

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
        self.logger.info(f"Updated dashboard with inbox processing results")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python process_inbox.py '<json_params>'")
        sys.exit(1)

    run_skill(ProcessInboxSkill, sys.argv[1])