"""
LinkedIn Watcher (API Version) - Content Calendar and Post Monitoring

This watcher monitors for:
1. Content calendar triggers for scheduled posting
2. Approval files that need to be processed

Note: Message monitoring has been removed as it requires LinkedIn Partner Program access.
For messaging, consider using LinkedIn's native notifications or webhook integrations.

Uses the official LinkedIn API v2 for all operations.
"""

import time
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
from base_watcher import BaseWatcher


class LinkedInWatcher(BaseWatcher):
    """Watcher for LinkedIn content calendar and scheduled posts"""

    def __init__(self, vault_path: str, check_interval: int = 3600):
        """
        Initialize LinkedIn watcher

        Args:
            vault_path: Path to the Obsidian vault
            check_interval: How often to check (default: 3600s = 1 hour)
        """
        super().__init__(vault_path, check_interval)

        self.logger.info('LinkedIn watcher initialized (API version)')
        self.logger.info(f'Check interval: {check_interval}s')
        self.logger.info('Note: Message monitoring requires LinkedIn Partner Program access')

    def check_for_updates(self) -> List[Dict[str, Any]]:
        """Check for content calendar posts that are due"""
        items = []

        try:
            # Check content calendar for due posts
            calendar_items = self._check_content_calendar()
            items.extend(calendar_items)

            # Log results
            if items:
                self.logger.info(f'Found {len(items)} LinkedIn items requiring action')
            else:
                self.logger.debug('No LinkedIn items found')

        except Exception as e:
            self.logger.error(f'Error checking LinkedIn: {e}', exc_info=True)

        return items

    def _check_content_calendar(self) -> List[Dict[str, Any]]:
        """Check content calendar for posts that are due"""
        items = []

        calendar_path = self.vault_path / 'Content_Calendar'
        if not calendar_path.exists():
            return items

        now = datetime.now()

        try:
            for post_file in calendar_path.glob('POST_*.json'):
                try:
                    data = json.loads(post_file.read_text())

                    # Skip already processed posts
                    if data.get('status') in ['pending_approval', 'posted', 'cancelled']:
                        continue

                    scheduled_time_str = data.get('scheduled_for')
                    if not scheduled_time_str:
                        continue

                    scheduled_time = datetime.fromisoformat(scheduled_time_str)

                    # Check if post is due
                    if now >= scheduled_time:
                        items.append({
                            'type': 'linkedin_scheduled_post',
                            'content': data.get('content', ''),
                            'image_path': data.get('image_path'),
                            'scheduled_for': scheduled_time_str,
                            'calendar_file': str(post_file),
                            'detected_at': datetime.now().isoformat(),
                            'priority': 'normal'
                        })

                except Exception as e:
                    self.logger.warning(f'Error reading calendar file {post_file}: {e}')
                    continue

        except Exception as e:
            self.logger.error(f'Error checking content calendar: {e}')

        return items

    def create_action_file(self, item: Dict[str, Any]) -> Path:
        """Create action file for scheduled LinkedIn post"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        action_filename = f"LINKEDIN_SCHEDULED_{timestamp}.md"
        action_filepath = self.needs_action / action_filename

        content = f"""---
type: linkedin_scheduled_post
scheduled_for: {item['scheduled_for']}
detected_at: {item['detected_at']}
priority: {item['priority']}
status: pending
calendar_file: {item['calendar_file']}
requires_approval: true
---

# Scheduled LinkedIn Post

## Content
```
{item['content']}
```

## Details
- **Scheduled for**: {item['scheduled_for']}
- **Detected at**: {item['detected_at']}
- **Image**: {'Yes - ' + item['image_path'] if item.get('image_path') else 'No'}

## Actions Required
1. Review the content above
2. Create approval request if you want to proceed
3. Or use: Move to Approved/ to trigger posting

## Processing Notes
This is a scheduled post from your content calendar. The post was scheduled for
{item['scheduled_for']} and is now ready to be published.

---
*Detected at: {item['detected_at']}*
*Scheduled for: {item['scheduled_for']}*
"""

        action_filepath.write_text(content, encoding='utf-8')
        self.logger.info(f'Created LinkedIn scheduled post action file: {action_filepath.name}')

        return action_filepath


def main():
    """Main entry point"""
    import sys
    from dotenv import load_dotenv

    # Load environment variables
    env_path = Path(__file__).parent.parent.parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)

    import os

    # Get configuration
    vault_path = os.getenv('VAULT_PATH', './ai_employee_vault')
    check_interval = int(os.getenv('LINKEDIN_CHECK_INTERVAL', '3600'))

    # Allow command line override
    if len(sys.argv) > 1:
        vault_path = sys.argv[1]
    if len(sys.argv) > 2:
        check_interval = int(sys.argv[2])

    vault_path = Path(vault_path)
    if not vault_path.exists():
        print(f'Error: Vault path does not exist: {vault_path}')
        sys.exit(1)

    print('=' * 70)
    print('LinkedIn Watcher (API Version)')
    print('=' * 70)
    print(f'Vault: {vault_path}')
    print(f'Check interval: {check_interval}s ({check_interval//60} minutes)')
    print('\nNote: This version uses the official LinkedIn API v2.')
    print('Message monitoring requires LinkedIn Partner Program access.')
    print('Focusing on content calendar and scheduled posts.\n')

    try:
        watcher = LinkedInWatcher(str(vault_path), check_interval)
        watcher.run()
    except KeyboardInterrupt:
        print('\n\nLinkedIn Watcher stopped by user')
    except Exception as e:
        print(f'\n\nLinkedIn Watcher error: {e}')
        raise


if __name__ == '__main__':
    main()
