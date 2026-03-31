"""
Gmail Watcher - Monitors Gmail for new emails

This watcher monitors a Gmail account for unread emails and creates
action items in the vault when new emails are detected.
"""

import time
import os
import base64
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

from base_watcher import BaseWatcher


class GmailWatcher(BaseWatcher):
    """Watcher for monitoring Gmail inbox"""

    def __init__(self, vault_path: str, credentials_path: str, token_path: str,
                 query: str = "is:unread is:inbox", check_interval: int = 120):
        super().__init__(vault_path, check_interval)

        self.credentials_path = Path(credentials_path)
        self.token_path = Path(token_path)
        self.query = query

        # Initialize Gmail API
        self.service = self._initialize_gmail_service()

        self.logger.info(f'Gmail watcher initialized')
        self.logger.info(f'Query: {self.query}')
        self.logger.info(f'Check interval: {check_interval}s')

    def _initialize_gmail_service(self):
        """Initialize and return Gmail API service"""
        try:
            from google.auth.transport.requests import Request
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from googleapiclient.discovery import build

            # Gmail API scopes
            SCOPES = [
                'https://www.googleapis.com/auth/gmail.readonly',
                'https://www.googleapis.com/auth/gmail.modify',
                'https://www.googleapis.com/auth/gmail.send'
            ]

            creds = None

            # Load existing token if it exists
            if self.token_path.exists():
                self.logger.info('Loading existing Gmail token')
                creds = Credentials.from_authorized_user_file(
                    str(self.token_path), SCOPES)

            # If no valid credentials, run OAuth flow
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    self.logger.info('Refreshing expired Gmail token')
                    creds.refresh(Request())
                else:
                    if not self.credentials_path.exists():
                        raise FileNotFoundError(
                            f"Gmail credentials not found at {self.credentials_path}. "
                            "Please download credentials from Google Cloud Console."
                        )

                    self.logger.info('Running Gmail OAuth flow')
                    flow = InstalledAppFlow.from_client_secrets_file(
                        str(self.credentials_path), SCOPES)
                    creds = flow.run_local_server(port=0)

                # Save token for future runs
                self.token_path.parent.mkdir(parents=True, exist_ok=True)
                with open(self.token_path, 'w') as token:
                    token.write(creds.to_json())
                self.logger.info(f'Gmail token saved to {self.token_path}')

            return build('gmail', 'v1', credentials=creds, cache_discovery=False)

        except ImportError:
            self.logger.error(
                "Gmail API dependencies not installed. "
                "Run: pip install google-auth google-auth-oauthlib "
                "google-auth-httplib2 google-api-python-client"
            )
            raise

    def check_for_updates(self) -> List[Dict[str, Any]]:
        """Check Gmail for new emails matching the query"""
        try:
            # Execute the query
            results = self.service.users().messages().list(
                userId='me',
                q=self.query,
                maxResults=50  # Limit to prevent overwhelming
            ).execute()

            messages = results.get('messages', [])

            if not messages:
                self.logger.debug('No new emails found')
                return []

            self.logger.info(f'Found {len(messages)} new emails')

            # Process each message
            items = []
            for msg_meta in messages:
                message_id = msg_meta['id']

                # Skip if already processed
                if message_id in self.processed_ids:
                    continue

                # Fetch full message details
                msg = self.service.users().messages().get(
                    userId='me',
                    id=message_id,
                    format='full'
                ).execute()

                # Extract email data
                email_data = self._parse_email(msg)

                if email_data:
                    items.append(email_data)
                    self.processed_ids.add(message_id)

            return items

        except Exception as e:
            self.logger.error(f'Error checking Gmail: {e}', exc_info=True)
            return []

    def _parse_email(self, msg: Dict) -> Optional[Dict[str, Any]]:
        """Parse Gmail message into structured data"""
        try:
            payload = msg.get('payload', {})
            headers = payload.get('headers', [])

            # Extract headers
            header_map = {}
            for header in headers:
                header_map[header['name'].lower()] = header['value']

            # Get message body
            body_text = self._extract_body(payload)

            # Get labels
            labels = msg.get('labelIds', [])

            # Determine priority
            priority = 'high' if 'IMPORTANT' in labels else 'normal'

            return {
                'id': msg['id'],
                'thread_id': msg.get('threadId', ''),
                'from': header_map.get('from', 'Unknown'),
                'to': header_map.get('to', ''),
                'subject': header_map.get('subject', 'No Subject'),
                'date': header_map.get('date', ''),
                'snippet': msg.get('snippet', ''),
                'body': body_text,
                'priority': priority,
                'labels': labels,
                'internal_date': msg.get('internalDate', ''),
                'size_estimate': msg.get('sizeEstimate', 0),
                'detected_at': datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f'Error parsing email: {e}')
            return None

    def _extract_body(self, payload: Dict) -> str:
        """Extract text body from email payload"""
        try:
            # Handle multipart messages
            if 'parts' in payload:
                for part in payload['parts']:
                    mime_type = part.get('mimeType', '')

                    if mime_type == 'text/plain':
                        data = part.get('body', {}).get('data', '')
                        if data:
                            return base64.urlsafe_b64decode(data).decode('utf-8')

                    elif mime_type == 'text/html':
                        # For HTML, try to get plain text version
                        data = part.get('body', {}).get('data', '')
                        if data:
                            html = base64.urlsafe_b64decode(data).decode('utf-8')
                            # Simple HTML to text conversion
                            import re
                            text = re.sub('<[^<]+?>', '', html)
                            return text

                    # Recursively check nested parts
                    if 'parts' in part:
                        nested = self._extract_body(part)
                        if nested:
                            return nested

            # Handle single part messages
            body = payload.get('body', {})
            data = body.get('data', '')

            if data:
                return base64.urlsafe_b64decode(data).decode('utf-8')

            return ''

        except Exception as e:
            self.logger.warning(f'Error extracting body: {e}')
            return ''

    def create_action_file(self, item: Dict[str, Any]) -> Path:
        """Create action file for email"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Sanitize subject for filename
        subject_part = self._sanitize_filename(item['subject'])[:50]
        action_filename = f"EMAIL_{timestamp}_{subject_part}.md"

        action_filepath = self.needs_action / action_filename

        # Determine if this is a sensitive email
        is_sensitive = self._is_sensitive_email(item)

        # Create content
        content = f"""---
type: email
message_id: {item['id']}
thread_id: {item['thread_id']}
from: {item['from']}
to: {item['to']}
subject: {item['subject']}
date: {item['date']}
received: {item['detected_at']}
priority: {item['priority']}
labels: {', '.join(item['labels'])}
size_estimate: {item['size_estimate']}
status: pending
requires_approval: {str(is_sensitive).lower()}
---

# Email: {item['subject']}

## Sender Information
- **From**: {item['from']}
- **To**: {item['to']}
- **Date**: {item['date']}
- **Priority**: {item['priority']}

## Snippet
{item['snippet']}

## Email Content
```
{item['body'][:1000]}{'...' if len(item['body']) > 1000 else ''}
```

## Suggested Actions
- [ ] Review email content
- [ ] Draft a reply if needed
- [ ] Forward to relevant party if needed
- [ ] Mark as read in Gmail
- [ ] Archive after processing

## Processing Notes
{'**Note**: This email has been flagged as potentially sensitive and may require approval before any action is taken.' if is_sensitive else ''}

---
*Gmail ID: {item['id']}*
*Thread ID: {item['thread_id']}*
"""

        # Write file
        action_filepath.write_text(content, encoding='utf-8')
        self.logger.info(f'Created action file: {action_filepath.name}')

        return action_filepath

    def _is_sensitive_email(self, item: Dict[str, Any]) -> bool:
        """Determine if email is potentially sensitive"""
        sensitive_keywords = [
            'payment', 'invoice', 'bank', 'account', 'password',
            'login', 'security', 'transaction', 'financial',
            'confidential', 'private', 'urgent', 'asap'
        ]

        subject_lower = item['subject'].lower()
        body_lower = item['body'][:500].lower()

        for keyword in sensitive_keywords:
            if keyword in subject_lower or keyword in body_lower:
                return True

        # Check for high priority
        if item['priority'] == 'high':
            return True

        return False

    def mark_as_read(self, message_id: str):
        """Mark a Gmail message as read (remove UNREAD label)"""
        try:
            self.service.users().messages().modify(
                userId='me',
                id=message_id,
                body={'removeLabelIds': ['UNREAD']}
            ).execute()
            self.logger.info(f'Marked message {message_id} as read')
        except Exception as e:
            self.logger.error(f'Failed to mark message as read: {e}')


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 4:
        print('Usage: python gmail_watcher.py <vault_path> <credentials_path> <token_path> [query] [check_interval]')
        print('Example: python gmail_watcher.py ./ai_employee_vault ./credentials/gmail_credentials.json ./credentials/gmail_token.json')
        sys.exit(1)

    vault_path = sys.argv[1]
    credentials_path = sys.argv[2]
    token_path = sys.argv[3]
    query = sys.argv[4] if len(sys.argv) > 4 else "is:unread is:inbox"
    check_interval = int(sys.argv[5]) if len(sys.argv) > 5 else 120

    print(f'Starting Gmail Watcher...')
    print(f'Vault: {vault_path}')
    print(f'Query: {query}')
    print(f'Check interval: {check_interval}s')

    watcher = GmailWatcher(vault_path, credentials_path, token_path, query, check_interval)
    watcher.run()
