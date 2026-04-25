"""
Meta Watcher - Monitors Facebook and Instagram for comments and mentions
Used for Gold Tier 2.2: Facebook + Instagram Integration
"""

import time
import os
import json
import requests
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List

try:
    from .base_watcher import BaseWatcher
    from ..orchestrator.skills.meta_api_client import setup_meta_client_from_env
except ImportError:
    from base_watcher import BaseWatcher
    import sys
    sys.path.append(str(Path(__file__).parent.parent))
    from orchestrator.skills.meta_api_client import setup_meta_client_from_env

class MetaWatcher(BaseWatcher):
    """Monitors Facebook and Instagram for new activity"""

    def __init__(self, vault_path: str, check_interval: int = 900):
        super().__init__(vault_path, check_interval)
        self.state_file = Path(vault_path) / '.state' / 'meta_watcher_state.json'
        self.client = None

    def _load_state(self) -> Dict[str, Any]:
        if self.state_file.exists():
            try:
                return json.loads(self.state_file.read_text())
            except:
                pass
        return {'last_fb_comment_time': None, 'last_ig_comment_time': None}

    def _save_state(self, state: Dict[str, Any]):
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.state_file.write_text(json.dumps(state, indent=2))

    def run(self):
        print(f"Meta Watcher started (interval: {self.check_interval}s)")
        while True:
            try:
                self._check_activity()
            except Exception as e:
                print(f"Error in Meta Watcher: {e}")
            time.sleep(self.check_interval)

    def _check_activity(self):
        if not self.client:
            self.client = setup_meta_client_from_env()
            if not self.client or not self.client.access_token:
                print("Meta credentials or token not configured. Skipping check.")
                return

        state = self._load_state()
        page_id = os.getenv('META_PAGE_ID')
        ig_id = os.getenv('INSTAGRAM_BUSINESS_ACCOUNT_ID')

        if page_id:
            self._check_facebook_comments(page_id, state)
        if ig_id:
            self._check_instagram_comments(ig_id, state)

        self._save_state(state)

    def _check_facebook_comments(self, page_id: str, state: Dict[str, Any]):
        """Check for new comments on the Page's posts"""
        # 1. Get Page Access Token
        pages = self.client.get_pages()
        page_token = None
        for page in pages:
            if page['id'] == page_id:
                page_token = page['access_token']
                break
        
        if not page_token:
            return

        # 2. Get recent posts and their comments
        url = f"{self.client.BASE_URL}/{page_id}/feed"
        params = {
            'fields': 'comments{from,message,created_time,id},message',
            'access_token': page_token,
            'limit': 5
        }
        
        response = requests.get(url, params=params)
        data = response.json()
        
        if 'data' not in data:
            return

        last_time = state.get('last_fb_comment_time')
        new_last_time = last_time
        count = 0

        for post in data['data']:
            if 'comments' in post:
                for comment in post['comments']['data']:
                    comment_time = comment['created_time']
                    if not last_time or comment_time > last_time:
                        self._create_action_file('facebook', post, comment)
                        count += 1
                        if not new_last_time or comment_time > new_last_time:
                            new_last_time = comment_time

        state['last_fb_comment_time'] = new_last_time
        if count > 0:
            self._notify_dashboard(f"Detected {count} new Facebook comment(s)")

    def _check_instagram_comments(self, ig_id: str, state: Dict[str, Any]):
        """Check for new comments on Instagram media"""
        # Use user token or page token (if shared permissions)
        url = f"{self.client.BASE_URL}/{ig_id}/media"
        params = {
            'fields': 'comments{from,text,timestamp,id},caption',
            'access_token': self.client.access_token,
            'limit': 5
        }
        
        response = requests.get(url, params=params)
        data = response.json()
        
        if 'data' not in data:
            return

        last_time = state.get('last_ig_comment_time')
        new_last_time = last_time
        count = 0

        for media in data['data']:
            if 'comments' in media:
                for comment in media['comments']['data']:
                    comment_time = comment['timestamp']
                    if not last_time or comment_time > last_time:
                        self._create_action_file('instagram', media, comment)
                        count += 1
                        if not new_last_time or comment_time > new_last_time:
                            new_last_time = comment_time

        state['last_ig_comment_time'] = new_last_time
        if count > 0:
            self._notify_dashboard(f"Detected {count} new Instagram comment(s)")

    def _create_action_file(self, platform: str, parent: Dict, comment: Dict):
        """Create Needs_Action file for a new comment"""
        comment_id = comment['id']
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"META_COMMENT_{platform.upper()}_{comment_id}_{timestamp}.md"
        file_path = Path(self.vault_path) / 'Needs_Action' / filename

        author = comment.get('from', {}).get('name', 'Unknown')
        text = comment.get('message') or comment.get('text')
        created = comment.get('created_time') or comment.get('timestamp')
        parent_preview = parent.get('message') or parent.get('caption', 'Media')

        content = f"""---
type: meta_comment
platform: {platform}
comment_id: {comment_id}
author: {author}
created_at: {created}
status: needs_action
---

# New {platform.capitalize()} Comment

**From**: {author}
**At**: {created}

## Post Context
> {parent_preview[:100]}...

## Comment
```
{text}
```

## Actions Required
Please process this {platform} comment.
- Decide if a reply is needed
- Flag as priority if it's a customer inquiry
"""
        file_path.write_text(content, encoding='utf-8')
        print(f"Created action file: {filename}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python meta_watcher.py <vault_path> [check_interval]")
        sys.exit(1)
    vault_path = sys.argv[1]
    interval = int(sys.argv[2]) if len(sys.argv) > 2 else 900
    watcher = MetaWatcher(vault_path, interval)
    watcher.run()
