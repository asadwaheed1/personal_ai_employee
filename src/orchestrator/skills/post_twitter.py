#!/usr/bin/env python3
"""
Agent Skill: Post to Twitter/X
Posts content to Twitter/X using the official Twitter API v2 with Human-in-the-Loop approval support
Used for Gold Tier 2.1: Twitter/X Integration
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

try:
    from .base_skill import BaseSkill, run_skill
    from .twitter_api_client import setup_twitter_client_from_env
except ImportError:
    from base_skill import BaseSkill, run_skill
    from twitter_api_client import setup_twitter_client_from_env


class PostTwitterSkill(BaseSkill):
    """Skill to post content to Twitter/X"""

    def _execute_impl(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute Twitter posting based on parameters"""
        action = params.get('action', 'create_tweet')

        if action == 'create_tweet':
            return self._create_tweet(params)
        elif action == 'schedule_tweet':
            return self._schedule_tweet(params)
        elif action == 'check_calendar':
            return self._check_content_calendar()
        elif action == 'execute_approved':
            return self._execute_approved_tweet(params)
        else:
            raise ValueError(f"Unknown action: {action}")

    def _get_twitter_client(self):
        """Get configured Twitter API client"""
        client = setup_twitter_client_from_env()
        if not client:
            raise ValueError(
                "Twitter API credentials not configured. "
                "Set TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, and TWITTER_ACCESS_SECRET."
            )
        return client

    def _create_tweet(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new tweet (usually goes through approval)"""
        content = params.get('content')
        media_path = params.get('image_path') or params.get('media_path')
        scheduled_for = params.get('scheduled_for')

        if not content:
            raise ValueError("Tweet content is required")

        # Validate content length (280 chars)
        if len(content) > 280:
            raise ValueError(f"Tweet content exceeds 280 character limit ({len(content)} chars)")

        # Check if approval is required (default True for social)
        requires_approval = params.get('requires_approval', True)

        if requires_approval:
            return self._create_approval_request(content, media_path, scheduled_for)

        # Post directly if configured
        return self._post_to_twitter(content, media_path)

    def _schedule_tweet(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Schedule a tweet for future publishing"""
        content = params.get('content')
        scheduled_time = params.get('scheduled_time')

        if not content:
            raise ValueError("Tweet content is required")
        if not scheduled_time:
            raise ValueError("Scheduled time is required")

        # Parse scheduled time
        try:
            schedule_dt = datetime.fromisoformat(scheduled_time)
        except:
            raise ValueError("Invalid scheduled_time format. Use ISO format: YYYY-MM-DDTHH:MM:SS")

        # Create scheduled tweet entry
        post_data = {
            'type': 'twitter_post',
            'content': content,
            'media_path': params.get('image_path') or params.get('media_path'),
            'scheduled_for': scheduled_time,
            'created_at': datetime.now().isoformat(),
            'status': 'scheduled'
        }

        # Save to content calendar
        calendar_path = self.vault_path / 'Content_Calendar'
        calendar_path.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        post_file = calendar_path / f"TWITTER_POST_{timestamp}.json"
        post_file.write_text(json.dumps(post_data, indent=2))

        self.logger.info(f"Scheduled tweet for {scheduled_time}")

        return {
            "success": True,
            "scheduled_for": scheduled_time,
            "calendar_file": str(post_file),
            "message": f"Tweet scheduled for {scheduled_time}"
        }

    def _check_content_calendar(self) -> Dict[str, Any]:
        """Check content calendar for tweets that need to be published"""
        calendar_path = self.vault_path / 'Content_Calendar'
        if not calendar_path.exists():
            return {"posts_due": [], "message": "No content calendar found"}

        now = datetime.now()
        posts_due = []

        for post_file in calendar_path.glob('TWITTER_POST_*.json'):
            try:
                data = json.loads(post_file.read_text())
                scheduled_time = datetime.fromisoformat(data['scheduled_for'])

                # Check if post is due
                if now >= scheduled_time and data.get('status') == 'scheduled':
                    posts_due.append({
                        'file': str(post_file),
                        'content': data['content'],
                        'media_path': data.get('media_path'),
                        'scheduled_for': data['scheduled_for']
                    })
            except Exception as e:
                self.logger.warning(f"Error reading calendar file {post_file}: {e}")
                continue

        # Auto-create approval requests for due posts
        created_count = 0
        for post in posts_due:
            try:
                self._create_approval_request(
                    post['content'],
                    post.get('media_path'),
                    post['scheduled_for']
                )
                created_count += 1

                # Mark as pending_approval in calendar
                data = json.loads(Path(post['file']).read_text())
                data['status'] = 'pending_approval'
                Path(post['file']).write_text(json.dumps(data, indent=2))
            except Exception as e:
                self.logger.error(f"Error creating approval for tweet: {e}")

        return {
            "posts_due": len(posts_due),
            "approval_requests_created": created_count,
            "message": f"Found {len(posts_due)} tweets due, created {created_count} approval requests"
        }

    def _create_approval_request(self, content: str, media_path: Optional[str],
                                  scheduled_for: Optional[str]) -> Dict[str, Any]:
        """Create approval request file for Twitter post"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        approval_filename = f"TWITTER_POST_{timestamp}.md"
        approval_path = self.vault_path / 'Pending_Approval' / approval_filename

        # Store post data
        post_data = {
            'action': 'twitter_post',
            'content': content,
            'media_path': media_path,
            'scheduled_for': scheduled_for,
            'created_at': datetime.now().isoformat()
        }

        approval_content = f"""---
type: approval_request
action: twitter_post
status: pending
priority: normal
created: {datetime.now().isoformat()}
---

# Approval Request: Twitter/X Post

## Tweet Content
```
{content}
```

## Media Attachment
{'**Yes**: ' + str(media_path) if media_path else '**None**'}

## Scheduling
{'Scheduled for: ' + scheduled_for if scheduled_for else 'Immediate posting upon approval'}

## Actions Required
1. **Review** content (280 char limit)
2. **Approve** by moving to **/Approved/** folder
3. **Reject** by moving to **/Rejected/** folder

---
**Skill**: PostTwitter
"""
        approval_path.write_text(approval_content, encoding='utf-8')

        # Save data for execution
        data_path = approval_path.with_suffix('.json')
        data_path.write_text(json.dumps(post_data, indent=2))

        self.logger.info(f"Created tweet approval request: {approval_path.name}")
        return {
            "requires_approval": True,
            "approval_file": str(approval_path),
            "message": f"Tweet requires approval: {approval_path.name}"
        }

    def _execute_approved_tweet(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute approved tweet"""
        content = params.get('content')
        media_path = params.get('media_path')
        return self._post_to_twitter(content, media_path)

    def _post_to_twitter(self, content: str, media_path: Optional[str]) -> Dict[str, Any]:
        """Actually post to Twitter/X"""
        try:
            client = self._get_twitter_client()
            
            media_ids = None
            if media_path and Path(media_path).exists():
                media_id = client.upload_media(str(media_path))
                if media_id:
                    media_ids = [media_id]

            result = client.post_tweet(content, media_ids=media_ids)
            
            if result.get('success'):
                self.logger.info(f"Tweet posted successfully: {result.get('tweet_id')}")
                return {
                    "success": True,
                    "tweet_id": result.get('tweet_id'),
                    "url": result.get('url'),
                    "message": "Tweet published successfully"
                }
            else:
                error_msg = result.get('error', 'Unknown error')
                # Check for transient errors
                transient_indicators = ['timeout', 'connection', 'network', 'busy', 'over capacity']
                if any(ind in error_msg.lower() for ind in transient_indicators):
                    return {
                        "success": False,
                        "status": "retry",
                        "error": error_msg,
                        "message": f"Transient Twitter error: {error_msg}. Post will be retried."
                    }
                raise RuntimeError(f"Twitter API error: {error_msg}")

        except Exception as e:
            self.logger.error(f"Failed to post tweet: {e}", exc_info=True)
            # Check for transient connection errors
            if any(ind in str(e).lower() for ind in ['timeout', 'connection', 'dns']):
                return {
                    "success": False,
                    "status": "retry",
                    "error": str(e),
                    "message": f"Transient connection error: {str(e)}. Post will be retried."
                }
            raise


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python post_twitter.py '<json_params>'")
        sys.exit(1)

    run_skill(PostTwitterSkill, sys.argv[1])
