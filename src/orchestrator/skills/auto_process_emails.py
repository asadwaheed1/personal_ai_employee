#!/usr/bin/env python3
"""
Agent Skill: Auto Process Emails
Automatically processes non-important emails (newsletters, promotions) by marking as read and archiving.
Important emails requiring action are left in Needs_Action for human review.
"""

import json
import sys
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

from base_skill import BaseSkill, run_skill


class AutoProcessEmailsSkill(BaseSkill):
    """Skill to automatically process low-priority emails"""

    def _execute_impl(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Auto-process emails in Needs_Action folder"""

        needs_action = self.vault_path / 'Needs_Action'
        email_files = sorted(needs_action.glob('EMAIL_*.md'))

        if not email_files:
            return {
                "success": True,
                "message": "No emails to process",
                "processed": 0,
                "kept": 0
            }

        processed_count = 0
        kept_for_review_count = 0
        moved_to_pending_approval_count = 0
        results = []

        for email_file in email_files:
            try:
                classification = self._classify_email(email_file)

                if classification['should_auto_process']:
                    # Auto-process: mark read + archive
                    self._auto_process_email(email_file, classification)
                    processed_count += 1
                    results.append({
                        'file': email_file.name,
                        'action': 'auto_processed',
                        'reason': classification['reason']
                    })
                elif classification.get('requires_approval', False):
                    # Move approval-required emails out of Needs_Action
                    self._move_to_pending_approval(email_file, classification)
                    moved_to_pending_approval_count += 1
                    results.append({
                        'file': email_file.name,
                        'action': 'moved_to_pending_approval',
                        'reason': classification['reason']
                    })
                else:
                    # Keep non-approval review items in Needs_Action
                    kept_for_review_count += 1
                    results.append({
                        'file': email_file.name,
                        'action': 'kept_for_review',
                        'reason': classification['reason']
                    })

            except Exception as e:
                self.logger.error(f"Failed to process {email_file.name}: {e}")
                results.append({
                    'file': email_file.name,
                    'action': 'error',
                    'error': str(e)
                })

        # Update dashboard
        self._update_dashboard_summary(
            processed_count,
            kept_for_review_count,
            moved_to_pending_approval_count
        )

        return {
            "success": True,
            "processed": processed_count,
            "kept_for_review": kept_for_review_count,
            "moved_to_pending_approval": moved_to_pending_approval_count,
            "results": results
        }

    def _classify_email(self, email_file: Path) -> Dict[str, Any]:
        """Classify email as auto-processable or needs human review"""
        content = self.read_file(email_file)

        # Parse frontmatter
        metadata = self._parse_frontmatter(content)

        # Extract key fields
        from_addr = metadata.get('from', '').lower()
        subject = metadata.get('subject', '').lower()
        priority = metadata.get('priority', 'normal')
        requires_approval = metadata.get('requires_approval', 'false') == 'true'

        # Newsletter/promotional indicators
        newsletter_patterns = [
            'newsletter', 'unsubscribe', 'promotional', 'marketing',
            'altfins', 'crypto', 'trading', 'cashback', 'offer',
            'instagram', 'notification', 'update', 'picks',
            'noreply', 'no-reply', 'donotreply', 'automated'
        ]

        # Important indicators
        important_patterns = [
            'urgent', 'asap', 'action required', 'reply needed',
            'meeting', 'interview', 'payment', 'invoice',
            'contract', 'agreement', 'deadline'
        ]

        # Check if newsletter/promotional
        is_newsletter = any(pattern in from_addr or pattern in subject
                           for pattern in newsletter_patterns)

        # Check if important
        is_important = any(pattern in subject for pattern in important_patterns)

        # Check if high priority or requires approval
        is_high_priority = priority == 'high' or requires_approval

        # Decision logic
        if is_high_priority or is_important:
            return {
                'should_auto_process': False,
                'requires_approval': requires_approval,
                'reason': 'High priority or requires human review'
            }

        if is_newsletter:
            return {
                'should_auto_process': True,
                'reason': 'Newsletter/promotional email'
            }

        # Default: keep for review if uncertain
        return {
            'should_auto_process': False,
            'reason': 'Uncertain classification, keeping for review'
        }

    def _parse_frontmatter(self, content: str) -> Dict[str, str]:
        """Parse YAML frontmatter from markdown"""
        metadata = {}

        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                frontmatter = parts[1].strip()
                for line in frontmatter.split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        metadata[key.strip()] = value.strip()

        return metadata

    def _auto_process_email(self, email_file: Path, classification: Dict):
        """Auto-process email: create MCP actions for mark read + archive"""
        content = self.read_file(email_file)
        metadata = self._parse_frontmatter(content)
        message_id = metadata.get('message_id')

        if not message_id:
            raise ValueError(f"Missing message_id in {email_file.name}")

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Create MCP action for mark as read
        self._create_mcp_mark_read(message_id, timestamp)

        # Create MCP action for archive
        self._create_mcp_archive(message_id, timestamp)

        # Move email file to Done
        done_path = self.vault_path / 'Done' / f'AUTO_PROCESSED_{email_file.name}'

        # Add processing note to content
        summary = f"""

---
## Auto-Processing Summary
**Processed**: {datetime.now().strftime('%Y-%m-%d %H:%M')}
**Classification**: {classification['reason']}
**Actions**: Mark as read, Archive
**Status**: Queued for MCP execution
"""

        content += summary
        self.write_file(done_path, content)

        # Remove from Needs_Action
        email_file.unlink()

        self.logger.info(f"Auto-processed: {email_file.name}")

    def _move_to_pending_approval(self, email_file: Path, classification: Dict[str, Any]):
        """Move approval-required email from Needs_Action to Pending_Approval"""
        content = self.read_file(email_file)
        pending_path = self.vault_path / 'Pending_Approval' / f'PENDING_{email_file.name}'

        summary = f"""

---
## Approval Routing
**Moved**: {datetime.now().strftime('%Y-%m-%d %H:%M')}
**Reason**: {classification['reason']}
**Status**: Awaiting human approval
"""

        self.write_file(pending_path, content + summary)

        if email_file.exists():
            email_file.unlink()

        self.logger.info(f"Moved to Pending_Approval: {email_file.name}")

    def _create_mcp_mark_read(self, message_id: str, timestamp: str):
        """Create MCP action to mark email as read"""
        action_filename = f"MCP_EMAIL_mark_as_read_{timestamp}_{message_id[:8]}.json"
        action_path = self.vault_path / 'Needs_Action' / action_filename

        mcp_action = {
            "mcp_server": "gmail",
            "tool": "modify_email",
            "timestamp": datetime.now().isoformat(),
            "status": "pending",
            "params": {
                "messageId": message_id,
                "removeLabelIds": ["UNREAD"]
            },
            "result": None,
            "executed_at": None
        }

        action_path.write_text(json.dumps(mcp_action, indent=2))
        self.logger.info(f"Created MCP mark_read action: {action_filename}")

    def _create_mcp_archive(self, message_id: str, timestamp: str):
        """Create MCP action to archive email"""
        action_filename = f"MCP_EMAIL_archive_{timestamp}_{message_id[:8]}.json"
        action_path = self.vault_path / 'Needs_Action' / action_filename

        mcp_action = {
            "mcp_server": "gmail",
            "tool": "modify_email",
            "timestamp": datetime.now().isoformat(),
            "status": "pending",
            "params": {
                "messageId": message_id,
                "removeLabelIds": ["INBOX"]
            },
            "result": None,
            "executed_at": None
        }

        action_path.write_text(json.dumps(mcp_action, indent=2))
        self.logger.info(f"Created MCP archive action: {action_filename}")

    def _update_dashboard_summary(self, processed: int, kept_for_review: int, moved_to_pending_approval: int):
        """Update dashboard with auto-processing summary"""
        from update_dashboard import UpdateDashboardSkill

        try:
            dashboard_skill = UpdateDashboardSkill(str(self.vault_path))
            dashboard_skill.execute({
                'summary': (
                    f"Auto-processed {processed} emails; "
                    f"kept {kept_for_review} for review; "
                    f"moved {moved_to_pending_approval} to Pending_Approval"
                )
            })
        except Exception as e:
            self.logger.warning(f"Failed to update dashboard: {e}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Auto Process Emails Skill")
        print("=" * 50)
        print("Automatically processes non-important emails (newsletters, promotions)")
        print("by marking as read and archiving. Important emails are kept for review.")
        print("\nUsage: python auto_process_emails.py '{}'")
        print("\nClassification Rules:")
        print("  Auto-process: Newsletters, promotions, notifications")
        print("  Keep for review: High priority, requires approval, important keywords")
        sys.exit(1)

    run_skill(AutoProcessEmailsSkill, sys.argv[1])
