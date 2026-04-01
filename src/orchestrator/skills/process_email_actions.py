#!/usr/bin/env python3
"""
Agent Skill: Process Email Actions
Executes Gmail actions (mark as read, archive, reply) based on task files
"""

import json
import sys
import os
import base64
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from base_skill import BaseSkill, run_skill


class ProcessEmailActionsSkill(BaseSkill):
    """Skill to process email actions via Gmail API"""

    def _execute_impl(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Process email actions from task file or email file directly"""
        task_file = params.get('task_file')
        email_file = params.get('email_file')
        actions = params.get('actions', [])
        reply_body = params.get('reply_body', '')
        reply_subject = params.get('reply_subject', '')

        # If task file provided, parse it
        if task_file:
            task_data = self._parse_task_file(Path(task_file))
            email_file = task_data.get('email_file')
            actions = task_data.get('actions', [])
            reply_body = task_data.get('reply_body', '')
            reply_subject = task_data.get('reply_subject', '')

        if not email_file:
            raise ValueError("Email file path is required")

        email_path = Path(email_file)
        if not email_path.exists():
            raise FileNotFoundError(f"Email file not found: {email_path}")

        # If no actions provided yet, try parsing from email file itself
        if not actions:
            email_actions = self._parse_email_file_actions(email_path)
            actions = email_actions.get('actions', [])
            reply_body = email_actions.get('reply_body', reply_body)
            reply_subject = email_actions.get('reply_subject', reply_subject)

        # Read email metadata
        email_data = self._parse_email_file(email_path)
        message_id = email_data.get('message_id')
        thread_id = email_data.get('thread_id')

        if not message_id:
            raise ValueError("Email message_id not found in email file")

        # Initialize Gmail service
        service = self._initialize_gmail_service()

        results = []

        # Execute actions
        for action in actions:
            action = action.lower().strip()
            try:
                if action == 'mark_as_read':
                    result = self._mark_as_read(service, message_id)
                    results.append({'action': 'mark_as_read', 'status': 'success', 'result': result})

                elif action == 'archive':
                    result = self._archive_email(service, message_id)
                    results.append({'action': 'archive', 'status': 'success', 'result': result})

                elif action == 'reply':
                    if not reply_body:
                        raise ValueError("Reply body is required for reply action")
                    result = self._send_reply(
                        service, message_id, thread_id, email_data,
                        reply_body, reply_subject
                    )
                    results.append({'action': 'reply', 'status': 'success', 'result': result})

                elif action == 'delete':
                    result = self._delete_email(service, message_id)
                    results.append({'action': 'delete', 'status': 'success', 'result': result})

                else:
                    results.append({'action': action, 'status': 'unknown', 'error': 'Unknown action'})

            except Exception as e:
                results.append({'action': action, 'status': 'failed', 'error': str(e)})
                self.logger.error(f"Failed to execute action {action}: {e}")

        # Move email file to Done with execution summary
        self._archive_email_file(email_path, email_data, actions, results)

        # If task file was provided, also move it to Done
        if task_file:
            self._archive_task_file(Path(task_file), results)

        # Update dashboard
        self._update_dashboard(email_data, actions, results)

        return {
            "success": True,
            "message_id": message_id,
            "actions_executed": len([r for r in results if r['status'] == 'success']),
            "actions_failed": len([r for r in results if r['status'] == 'failed']),
            "results": results
        }

    def _parse_task_file(self, task_path: Path) -> Dict[str, Any]:
        """Parse task file to extract email actions"""
        content = self.read_file(task_path)

        task_data = {
            'email_file': None,
            'actions': [],
            'reply_body': '',
            'reply_subject': ''
        }

        # Extract email file reference
        import re

        # Look for email file reference
        email_file_match = re.search(r'\*\*File\*\*:\s*(.+?)\n', content)
        if email_file_match:
            task_data['email_file'] = email_file_match.group(1).strip()

        # Look for message ID as fallback
        message_id_match = re.search(r'\*\*Message ID\*\*:\s*(.+?)\n', content)
        if message_id_match and not task_data['email_file']:
            message_id = message_id_match.group(1).strip()
            # Find email file by message ID
            needs_action = self.vault_path / 'Needs_Action'
            for email_file in needs_action.glob('EMAIL_*.md'):
                email_content = self.read_file(email_file)
                if f'message_id: {message_id}' in email_content:
                    task_data['email_file'] = str(email_file)
                    break

        # Parse actions from markdown checkboxes
        action_patterns = [
            (r'- \[x\]\s*Mark as read', 'mark_as_read'),
            (r'- \[x\]\s*Archive', 'archive'),
            (r'- \[x\]\s*Reply', 'reply'),
            (r'- \[x\]\s*Delete', 'delete'),
        ]

        for pattern, action_name in action_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                task_data['actions'].append(action_name)

        # Look for "Actions Required" section
        if '## Actions Required' in content:
            actions_section = content.split('## Actions Required')[1].split('##')[0]
            if 'mark as read' in actions_section.lower():
                task_data['actions'].append('mark_as_read')
            if 'archive' in actions_section.lower():
                task_data['actions'].append('archive')
            if 'reply' in actions_section.lower():
                task_data['actions'].append('reply')
            if 'delete' in actions_section.lower():
                task_data['actions'].append('delete')

        # Remove duplicates while preserving order
        seen = set()
        task_data['actions'] = [x for x in task_data['actions'] if not (x in seen or seen.add(x))]

        # Extract reply body if present
        if '## Reply Content' in content:
            reply_section = content.split('## Reply Content')[1].split('##')[0]
            task_data['reply_body'] = reply_section.strip()

        # Extract reply subject if present
        reply_subject_match = re.search(r'\*\*Reply Subject\*\*:\s*(.+?)\n', content)
        if reply_subject_match:
            task_data['reply_subject'] = reply_subject_match.group(1).strip()

        return task_data

    def _parse_email_file(self, email_path: Path) -> Dict[str, Any]:
        """Parse email markdown file to extract metadata"""
        content = self.read_file(email_path)

        email_data = {}

        # Extract frontmatter
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                frontmatter = parts[1].strip()
                for line in frontmatter.split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        email_data[key.strip()] = value.strip()

        # Extract sender info
        import re
        from_match = re.search(r'\*\*From\*\*:\s*(.+?)\n', content)
        if from_match:
            email_data['from'] = from_match.group(1).strip()

        to_match = re.search(r'\*\*To\*\*:\s*(.+?)\n', content)
        if to_match:
            email_data['to'] = to_match.group(1).strip()

        subject_match = re.search(r'\*\*Subject\*\*:\s*(.+?)\n', content)
        if subject_match:
            email_data['subject'] = subject_match.group(1).strip()

        return email_data

    def _parse_email_file_actions(self, email_path: Path) -> Dict[str, Any]:
        """Parse email file to extract checked actions and human notes"""
        content = self.read_file(email_path)

        actions_data = {
            'actions': [],
            'reply_body': '',
            'reply_subject': ''
        }

        import re

        # Parse Suggested Actions section for checked boxes
        if '## Suggested Actions' in content:
            actions_section = content.split('## Suggested Actions')[1]
            # Get content until next ## or end
            next_section = re.search(r'\n##[^#]', actions_section)
            if next_section:
                actions_section = actions_section[:next_section.start()]

            # Map checkbox text to action names
            action_mappings = [
                (r'- \[x\].*reply', 'reply'),
                (r'- \[x\].*mark as read', 'mark_as_read'),
                (r'- \[x\].*archive', 'archive'),
                (r'- \[x\].*delete', 'delete'),
                (r'- \[x\].*forward', 'forward'),
            ]

            for pattern, action_name in action_mappings:
                if re.search(pattern, actions_section, re.IGNORECASE):
                    actions_data['actions'].append(action_name)

        # Parse Human Notes section for reply content
        if '## Human Notes' in content or '## Human notes' in content:
            # Try both capitalizations
            notes_section = None
            if '## Human Notes' in content:
                notes_section = content.split('## Human Notes')[1]
            elif '## Human notes' in content:
                notes_section = content.split('## Human notes')[1]

            if notes_section:
                # Get content until next ## or end
                next_section = re.search(r'\n##[^#]', notes_section)
                if next_section:
                    notes_section = notes_section[:next_section.start()]

                # Extract the reply content
                notes_text = notes_section.strip()

                # If there's content, use it as reply body
                if notes_text:
                    actions_data['reply_body'] = notes_text

        # Remove duplicates while preserving order
        seen = set()
        actions_data['actions'] = [x for x in actions_data['actions'] if not (x in seen or seen.add(x))]

        return actions_data

    def _initialize_gmail_service(self):
        """Initialize Gmail API service"""
        try:
            from google.auth.transport.requests import Request
            from google.oauth2.credentials import Credentials
            from googleapiclient.discovery import build

            token_path = Path(os.getenv('GMAIL_TOKEN_PATH', './credentials/gmail_token.json'))
            if not token_path.exists():
                raise FileNotFoundError(f"Gmail token not found at {token_path}")

            creds = Credentials.from_authorized_user_file(str(token_path), [
                'https://www.googleapis.com/auth/gmail.modify',
                'https://www.googleapis.com/auth/gmail.send'
            ])

            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    raise RuntimeError("Gmail credentials expired")

            return build('gmail', 'v1', credentials=creds, cache_discovery=False)

        except ImportError:
            raise ImportError("Gmail API dependencies not installed. Run: pip install google-auth google-auth-oauthlib google-api-python-client")

    def _mark_as_read(self, service, message_id: str) -> Dict[str, Any]:
        """Mark email as read by removing UNREAD label"""
        service.users().messages().modify(
            userId='me',
            id=message_id,
            body={'removeLabelIds': ['UNREAD']}
        ).execute()

        return {'message_id': message_id, 'action': 'marked_as_read'}

    def _archive_email(self, service, message_id: str) -> Dict[str, Any]:
        """Archive email by removing INBOX label"""
        service.users().messages().modify(
            userId='me',
            id=message_id,
            body={'removeLabelIds': ['INBOX']}
        ).execute()

        return {'message_id': message_id, 'action': 'archived'}

    def _delete_email(self, service, message_id: str) -> Dict[str, Any]:
        """Move email to trash"""
        service.users().messages().trash(
            userId='me',
            id=message_id
        ).execute()

        return {'message_id': message_id, 'action': 'trashed'}

    def _send_reply(self, service, message_id: str, thread_id: str,
                    email_data: Dict[str, Any], reply_body: str,
                    reply_subject: str = '') -> Dict[str, Any]:
        """Send a reply to the email"""
        # Extract original sender to reply to
        from_header = email_data.get('from', '')
        import re
        email_match = re.search(r'<([^>]+)>', from_header)
        if email_match:
            reply_to = email_match.group(1)
        else:
            reply_to = from_header

        # Get original subject
        original_subject = email_data.get('subject', '')
        if not original_subject.lower().startswith('re:'):
            reply_subject = f"Re: {original_subject}" if not reply_subject else reply_subject
        else:
            reply_subject = original_subject if not reply_subject else reply_subject

        # Create reply message
        msg = MIMEMultipart()
        msg['to'] = reply_to
        msg['subject'] = reply_subject
        msg['In-Reply-To'] = message_id
        msg['References'] = message_id

        # Add reply body
        msg.attach(MIMEText(reply_body, 'plain'))

        # Encode message
        raw_message = base64.urlsafe_b64encode(msg.as_bytes()).decode('utf-8')

        # Send reply
        result = service.users().messages().send(
            userId='me',
            body={
                'raw': raw_message,
                'threadId': thread_id
            }
        ).execute()

        return {
            'message_id': result['id'],
            'thread_id': thread_id,
            'to': reply_to,
            'subject': reply_subject,
            'action': 'reply_sent'
        }

    def _archive_email_file(self, email_path: Path, email_data: Dict[str, Any],
                           actions: list, results: list):
        """Move email file to Done with execution summary"""
        content = self.read_file(email_path)

        # Add execution summary
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
        action_summary = ', '.join(actions) if actions else 'No actions'

        success_count = len([r for r in results if r['status'] == 'success'])
        failed_count = len([r for r in results if r['status'] == 'failed'])

        summary = f"""

---
## Execution Summary
**Executed**: {timestamp}
**Actions Requested**: {action_summary}
**Successful**: {success_count}
**Failed**: {failed_count}

### Action Results
```json
{json.dumps(results, indent=2)}
```
"""

        content += summary

        # Write to Done
        done_path = self.vault_path / 'Done' / f"PROCESSED_{email_path.name}"
        self.write_file(done_path, content)

        # Remove from Needs_Action
        if email_path.exists():
            email_path.unlink()

        self.logger.info(f"Archived email file to: {done_path.name}")

    def _archive_task_file(self, task_path: Path, results: list):
        """Move task file to Done"""
        if not task_path.exists():
            return

        content = self.read_file(task_path)

        # Add summary
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
        success_count = len([r for r in results if r['status'] == 'success'])

        summary = f"""

---
## Completion Summary
**Completed**: {timestamp}
**Actions Successful**: {success_count}
**Status**: Done
"""

        content += summary

        # Write to Done
        done_path = self.vault_path / 'Done' / f"COMPLETED_{task_path.name}"
        self.write_file(done_path, content)

        # Remove from Inbox
        task_path.unlink()

        self.logger.info(f"Archived task file to: {done_path.name}")

    def _update_dashboard(self, email_data: Dict[str, Any], actions: list, results: list):
        """Update dashboard with email processing activity"""
        from update_dashboard import UpdateDashboardSkill

        try:
            subject = email_data.get('subject', 'Unknown')[:40]
            action_names = ', '.join(actions)
            successful = len([r for r in results if r['status'] == 'success'])

            dashboard_skill = UpdateDashboardSkill(str(self.vault_path))
            dashboard_skill.execute({
                'summary': f"Processed email '{subject}': {action_names} ({successful}/{len(actions)} successful)"
            })
        except Exception as e:
            self.logger.warning(f"Failed to update dashboard: {e}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python process_email_actions.py '<json_params>'")
        print("\nExamples:")
        print('  # Using task file:')
        print('  python process_email_actions.py \'{"task_file": "Inbox/process_email_task.md"}\'')
        print()
        print('  # Direct execution:')
        print('  python process_email_actions.py \'{"email_file": "Needs_Action/EMAIL_xxx.md", "actions": ["mark_as_read", "archive"]}\'')
        print()
        print('  # With reply:')
        print('  python process_email_actions.py \'{"email_file": "Needs_Action/EMAIL_xxx.md", "actions": ["reply"], "reply_body": "Thanks for the update!", "reply_subject": "Re: Original Subject"}\'')
        sys.exit(1)

    run_skill(ProcessEmailActionsSkill, sys.argv[1])
