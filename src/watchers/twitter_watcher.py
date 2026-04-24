"""
Twitter Watcher - Monitors Twitter/X for mentions
Used for Gold Tier 2.1: Twitter/X Integration
"""

import time
import os
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List

try:
    from .base_watcher import BaseWatcher
    from ..orchestrator.skills.twitter_api_client import setup_twitter_client_from_env
except ImportError:
    from base_watcher import BaseWatcher
    # If running directly or via different path
    import sys
    sys.path.append(str(Path(__file__).parent.parent))
    from orchestrator.skills.twitter_api_client import setup_twitter_client_from_env

class TwitterWatcher(BaseWatcher):
    """Monitors Twitter/X for mentions and creates action items"""

    def __init__(self, vault_path: str, check_interval: int = 900):
        """
        Initialize Twitter watcher

        Args:
            vault_path: Path to the vault
            check_interval: Check interval in seconds (default 15 min for rate limits)
        """
        super().__init__(vault_path, check_interval)
        self.state_file = Path(vault_path) / '.state' / 'twitter_watcher_state.json'
        self.client = None

    def _load_state(self) -> Dict[str, Any]:
        """Load last processed mention ID"""
        if self.state_file.exists():
            try:
                return json.loads(self.state_file.read_text())
            except:
                pass
        return {'last_mention_id': None}

    def _save_state(self, state: Dict[str, Any]):
        """Save last processed mention ID"""
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.state_file.write_text(json.dumps(state, indent=2))

    def run(self):
        """Main watcher loop"""
        print(f"Twitter Watcher started (interval: {self.check_interval}s)")
        
        while True:
            try:
                self._check_mentions()
            except Exception as e:
                print(f"Error in Twitter Watcher: {e}")
            
            time.sleep(self.check_interval)

    def _check_mentions(self):
        """Check for new mentions and create action files"""
        if not self.client:
            self.client = setup_twitter_client_from_env()
            if not self.client:
                print("Twitter credentials not configured. Skipping mention check.")
                return

        state = self._load_state()
        last_id = state.get('last_mention_id')

        print(f"Checking for Twitter mentions since ID: {last_id}")
        mentions = self.client.get_mentions(since_id=last_id)

        if not mentions:
            print("No new Twitter mentions found.")
            return

        print(f"Found {len(mentions)} new Twitter mention(s).")

        new_last_id = last_id
        for mention in mentions:
            self._create_action_file(mention)
            # mentions are usually returned newest first or oldest first depending on API,
            # but we want to track the maximum ID seen.
            if not new_last_id or int(mention['id']) > int(new_last_id):
                new_last_id = str(mention['id'])

        state['last_mention_id'] = new_last_id
        state['last_check'] = datetime.now().isoformat()
        self._save_state(state)
        
        # Notify dashboard
        self._notify_dashboard(f"Detected {len(mentions)} new Twitter mention(s)")

    def _create_action_file(self, mention: Dict[str, Any]):
        """Create a Needs_Action file for a Twitter mention"""
        mention_id = mention['id']
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"TWITTER_MENTION_{mention_id}_{timestamp}.md"
        file_path = Path(self.vault_path) / 'Needs_Action' / filename

        content = f"""---
type: twitter_mention
mention_id: {mention_id}
author_id: {mention.get('author_id')}
created_at: {mention.get('created_at')}
status: needs_action
---

# Twitter Mention

**From User ID**: {mention.get('author_id')}
**At**: {mention.get('created_at')}

## Content
```
{mention.get('text')}
```

## Metrics
- Retweets: {mention.get('metrics', {}).get('retweet_count', 0)}
- Replies: {mention.get('metrics', {}).get('reply_count', 0)}
- Likes: {mention.get('metrics', {}).get('like_count', 0)}

## Actions Required
Please process this Twitter mention according to the Company Handbook.
- Determine if a reply is needed
- Create a reply if appropriate
- Flag if it's a customer support issue or a lead
"""
        file_path.write_text(content, encoding='utf-8')
        print(f"Created action file: {filename}")


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python twitter_watcher.py <vault_path> [check_interval]")
        sys.exit(1)

    vault_path = sys.argv[1]
    interval = int(sys.argv[2]) if len(sys.argv) > 2 else 900
    
    watcher = TwitterWatcher(vault_path, interval)
    watcher.run()
