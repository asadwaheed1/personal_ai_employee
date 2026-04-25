"""
Content Calendar Watcher - Monitors all social media platforms for scheduled posts
Used for Gold Tier 2.3: Cross-Platform Content Calendar
"""

import time
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

try:
    from .base_watcher import BaseWatcher
except ImportError:
    from base_watcher import BaseWatcher

class ContentCalendarWatcher(BaseWatcher):
    """Watcher for all social media platforms' content calendars"""

    def __init__(self, vault_path: str, check_interval: int = 3600):
        super().__init__(vault_path, check_interval)
        self.platforms = ['LINKEDIN', 'TWITTER', 'FACEBOOK', 'INSTAGRAM']
        self.logger.info(f'Content Calendar watcher initialized for platforms: {self.platforms}')

    def check_for_updates(self) -> List[Dict[str, Any]]:
        """Check for content calendar posts that are due across all platforms"""
        items = []
        calendar_path = self.vault_path / 'Content_Calendar'
        if not calendar_path.exists():
            return items

        now = datetime.now()
        
        # Check for all platform-specific post files
        for platform in self.platforms:
            pattern = f"{platform}_POST_*.json"
            for post_file in calendar_path.glob(pattern):
                try:
                    data = json.loads(post_file.read_text())
                    
                    if data.get('status') in ['pending_approval', 'posted', 'cancelled']:
                        continue
                        
                    scheduled_time_str = data.get('scheduled_for')
                    if not scheduled_time_str:
                        continue
                        
                    scheduled_time = datetime.fromisoformat(scheduled_time_str)
                    
                    if now >= scheduled_time:
                        items.append({
                            'platform': platform.lower(),
                            'type': f"{platform.lower()}_scheduled_post",
                            'content': data.get('content', ''),
                            'media_path': data.get('media_path') or data.get('image_url'),
                            'scheduled_for': scheduled_time_str,
                            'calendar_file': str(post_file),
                            'detected_at': datetime.now().isoformat()
                        })
                except Exception as e:
                    self.logger.warning(f'Error reading {platform} calendar file {post_file}: {e}')

        # Also support legacy pattern if any
        for post_file in calendar_path.glob('POST_*.json'):
            if any(p in post_file.name for p in self.platforms):
                continue
            try:
                data = json.loads(post_file.read_text())
                if data.get('status') in ['pending_approval', 'posted', 'cancelled']:
                    continue
                scheduled_time_str = data.get('scheduled_for')
                if scheduled_time_str and now >= datetime.fromisoformat(scheduled_time_str):
                    items.append({
                        'platform': 'linkedin', # Legacy default
                        'type': 'linkedin_scheduled_post',
                        'content': data.get('content', ''),
                        'scheduled_for': scheduled_time_str,
                        'calendar_file': str(post_file),
                        'detected_at': datetime.now().isoformat()
                    })
            except:
                pass

        return items

    def create_action_file(self, item: Dict[str, Any]) -> Path:
        """Create action file for a scheduled post"""
        platform = item['platform']
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        action_filename = f"SCHEDULED_{platform.upper()}_{timestamp}.md"
        action_filepath = self.needs_action / action_filename

        content = f"""---
type: {item['type']}
platform: {platform}
scheduled_for: {item['scheduled_for']}
detected_at: {item['detected_at']}
status: pending
calendar_file: {item['calendar_file']}
requires_approval: true
---

# Scheduled {platform.capitalize()} Post

## Content
```
{item['content']}
```

## Details
- **Platform**: {platform.capitalize()}
- **Scheduled for**: {item['scheduled_for']}
- **Media**: {'Yes' if item.get('media_path') else 'No'}

## Actions Required
1. Review the content above
2. Move this file to **/Approved/** to trigger publishing via the `{platform}` skill.

---
*Detected at: {item['detected_at']}*
"""
        action_filepath.write_text(content, encoding='utf-8')
        
        # Mark the calendar file as pending_approval to avoid duplicate actions
        try:
            cal_file = Path(item['calendar_file'])
            data = json.loads(cal_file.read_text())
            data['status'] = 'pending_approval'
            cal_file.write_text(json.dumps(data, indent=2))
        except:
            pass

        self.logger.info(f'Created action file for {platform}: {action_filepath.name}')
        return action_filepath

if __name__ == "__main__":
    import sys
    from dotenv import load_dotenv
    load_dotenv()
    vault_path = sys.argv[1] if len(sys.argv) > 1 else './ai_employee_vault'
    watcher = ContentCalendarWatcher(vault_path)
    watcher.run()
