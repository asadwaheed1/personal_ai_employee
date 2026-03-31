"""
LinkedIn Watcher - Monitors LinkedIn for new messages and content opportunities

This watcher monitors LinkedIn for:
1. New messages with keywords indicating business opportunities
2. Content calendar triggers for automated posting

Uses Playwright for browser automation.
"""

import time
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
from base_watcher import BaseWatcher


class LinkedInWatcher(BaseWatcher):
    """Watcher for monitoring LinkedIn activity"""

    def __init__(self, vault_path: str, username: str = None, password: str = None,
                 session_path: str = None, check_interval: int = 300,
                 keywords: List[str] = None):
        super().__init__(vault_path, check_interval)

        self.username = username or self._get_env('LINKEDIN_USERNAME')
        self.password = password or self._get_env('LINKEDIN_PASSWORD')
        self.session_path = Path(session_path) if session_path else Path(self._get_env('LINKEDIN_SESSION_PATH', './credentials/linkedin_session'))
        self.keywords = keywords or self._parse_keywords(self._get_env('LINKEDIN_KEYWORDS', 'urgent,opportunity,partnership,meeting'))

        self.logger.info(f'LinkedIn watcher initialized')
        self.logger.info(f'Session path: {self.session_path}')
        self.logger.info(f'Check interval: {check_interval}s')
        self.logger.info(f'Monitoring keywords: {self.keywords}')

    def _get_env(self, key: str, default: str = None) -> str:
        """Get environment variable"""
        import os
        return os.getenv(key, default)

    def _parse_keywords(self, keywords_str: str) -> List[str]:
        """Parse comma-separated keywords"""
        return [k.strip().lower() for k in keywords_str.split(',')]

    def check_for_updates(self) -> List[Dict[str, Any]]:
        """Check LinkedIn for new messages"""
        try:
            from playwright.sync_api import sync_playwright

            items = []

            with sync_playwright() as p:
                # Launch browser
                browser = p.chromium.launch_persistent_context(
                    str(self.session_path),
                    headless=True,
                    args=['--disable-blink-features=AutomationControlled']
                )

                page = browser.new_page()

                # Navigate to LinkedIn
                page.goto('https://www.linkedin.com/messaging/')

                # Check if already logged in
                if 'login' in page.url:
                    self.logger.info('LinkedIn login required')
                    if not self._login(page):
                        self.logger.error('Failed to login to LinkedIn')
                        browser.close()
                        return []

                # Wait for messaging interface
                page.wait_for_selector('[data-testid="conversations-list"]', timeout=10000)

                # Find conversations with unread messages
                conversations = self._get_unread_conversations(page)

                for conv in conversations:
                    # Check if message contains keywords
                    if self._contains_keywords(conv['preview']):
                        items.append({
                            'type': 'linkedin_message',
                            'sender': conv['sender'],
                            'preview': conv['preview'],
                            'timestamp': conv['timestamp'],
                            'detected_at': datetime.now().isoformat(),
                            'keywords_matched': self._get_matched_keywords(conv['preview']),
                            'priority': 'high'
                        })

                browser.close()

            self.logger.info(f'Found {len(items)} LinkedIn messages matching keywords')
            return items

        except ImportError:
            self.logger.error(
                "Playwright not installed. "
                "Run: pip install playwright && playwright install"
            )
            return []
        except Exception as e:
            self.logger.error(f'Error checking LinkedIn: {e}', exc_info=True)
            return []

    def _login(self, page) -> bool:
        """Login to LinkedIn"""
        try:
            page.goto('https://www.linkedin.com/login')

            # Fill credentials
            page.fill('#username', self.username)
            page.fill('#password', self.password)

            # Click login button
            page.click('button[type="submit"]')

            # Wait for navigation
            page.wait_for_load_state('networkidle')

            # Check if login successful
            if '/feed' in page.url or '/messaging' in page.url:
                self.logger.info('LinkedIn login successful')
                return True

            # Check for security challenge
            if 'checkpoint' in page.url or 'captcha' in page.content().lower():
                self.logger.error('LinkedIn security challenge detected. Manual login required.')
                return False

            return False

        except Exception as e:
            self.logger.error(f'LinkedIn login failed: {e}')
            return False

    def _get_unread_conversations(self, page) -> List[Dict[str, str]]:
        """Get list of conversations with unread messages"""
        conversations = []

        try:
            # Wait for conversation list
            page.wait_for_selector('.msg-conversation-listitem', timeout=5000)

            # Get all conversation items
            items = page.query_selector_all('.msg-conversation-listitem')

            for item in items:
                try:
                    # Check for unread indicator
                    unread = item.query_selector('.msg-conversation-listitem__unread-count')

                    if unread:
                        # Extract sender name
                        sender_elem = item.query_selector('.msg-conversation-listitem__participant-names')
                        sender = sender_elem.inner_text() if sender_elem else 'Unknown'

                        # Extract message preview
                        preview_elem = item.query_selector('.msg-conversation-listitem__message-snippet')
                        preview = preview_elem.inner_text() if preview_elem else ''

                        # Extract timestamp
                        time_elem = item.query_selector('.msg-conversation-listitem__time')
                        timestamp = time_elem.inner_text() if time_elem else ''

                        conversations.append({
                            'sender': sender.strip(),
                            'preview': preview.strip(),
                            'timestamp': timestamp.strip()
                        })
                except Exception as e:
                    self.logger.warning(f'Error parsing conversation: {e}')
                    continue

        except Exception as e:
            self.logger.warning(f'Error getting conversations: {e}')

        return conversations

    def _contains_keywords(self, text: str) -> bool:
        """Check if text contains any monitored keywords"""
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in self.keywords)

    def _get_matched_keywords(self, text: str) -> List[str]:
        """Get list of keywords matched in text"""
        text_lower = text.lower()
        return [kw for kw in self.keywords if kw in text_lower]

    def create_action_file(self, item: Dict[str, Any]) -> Path:
        """Create action file for LinkedIn message"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        sender_part = self._sanitize_filename(item['sender'])[:30]

        action_filename = f"LINKEDIN_{timestamp}_{sender_part}.md"
        action_filepath = self.needs_action / action_filename

        content = f"""---
type: linkedin_message
sender: {item['sender']}
detected_at: {item['detected_at']}
timestamp: {item['timestamp']}
priority: {item['priority']}
keywords_matched: {', '.join(item['keywords_matched'])}
status: pending
requires_approval: true
---

# LinkedIn Message from {item['sender']}

## Message Preview
> {item['preview']}

## Detected Keywords
{chr(10).join(f'- **{kw}**' for kw in item['keywords_matched'])}

## Suggested Actions
- [ ] Review full conversation on LinkedIn
- [ ] Draft a response if needed
- [ ] Check sender's profile for context
- [ ] Mark as priority if business opportunity
- [ ] Create task in project management if needed

## Business Context
This message was flagged because it contains keywords indicating potential business value:
{chr(10).join(f'- {kw}' for kw in item['keywords_matched'])}

## Processing Notes
- Open LinkedIn to view full conversation
- Consider connection strength and previous interactions
- May require follow-up or meeting scheduling

---
*Detected at: {item['detected_at']}*
*Original timestamp: {item['timestamp']}*
"""

        action_filepath.write_text(content, encoding='utf-8')
        self.logger.info(f'Created LinkedIn action file: {action_filepath.name}')

        return action_filepath

    def post_content(self, content: str, image_path: Path = None) -> Dict[str, Any]:
        """Post content to LinkedIn (requires manual execution)"""
        # This creates an approval request for posting
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        post_data = {
            'type': 'linkedin_post',
            'content': content,
            'image_path': str(image_path) if image_path else None,
            'created_at': datetime.now().isoformat(),
            'scheduled_for': None
        }

        # Create approval request
        approval_filename = f"LINKEDIN_POST_{timestamp}.md"
        approval_path = self.vault_path / 'Pending_Approval' / approval_filename

        approval_content = f"""---
type: approval_request
action: linkedin_post
status: pending
created: {datetime.now().isoformat()}
---

# Approval Request: LinkedIn Post

## Post Content
```
{content}
```

## Image Attachment
{'Yes: ' + str(image_path) if image_path else 'None'}

## Purpose
This post is part of the automated content strategy to generate business leads.

## Actions Required
1. Review the content above
2. Move this file to **/Approved/** to schedule posting
3. Move this file to **/Rejected/** to cancel

## Technical Details
- Created: {datetime.now().strftime('%Y-%m-%d %H:%M')}
- Platform: LinkedIn
- Post type: Organic content

---
**Note**: After approval, the post will be published automatically.
"""

        approval_path.write_text(approval_content, encoding='utf-8')

        # Save post data
        data_path = approval_path.with_suffix('.json')
        data_path.write_text(json.dumps(post_data, indent=2))

        self.logger.info(f'Created LinkedIn post approval request: {approval_path.name}')

        return {
            'requires_approval': True,
            'approval_file': str(approval_path),
            'message': 'LinkedIn post requires approval. Review and move to /Approved/ to publish.'
        }


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print('Usage: python linkedin_watcher.py <vault_path> [username] [password] [check_interval]')
        print('Example: python linkedin_watcher.py ./ai_employee_vault user@email.com password 300')
        print('\nEnvironment variables can also be used:')
        print('  LINKEDIN_USERNAME, LINKEDIN_PASSWORD, LINKEDIN_SESSION_PATH')
        sys.exit(1)

    vault_path = sys.argv[1]
    username = sys.argv[2] if len(sys.argv) > 2 else None
    password = sys.argv[3] if len(sys.argv) > 3 else None
    check_interval = int(sys.argv[4]) if len(sys.argv) > 4 else 300

    print(f'Starting LinkedIn Watcher...')
    print(f'Vault: {vault_path}')
    print(f'Check interval: {check_interval}s')

    watcher = LinkedInWatcher(vault_path, username, password, check_interval=check_interval)
    watcher.run()
