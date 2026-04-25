#!/usr/bin/env python3
"""
Agent Skill: Post to Facebook
Posts content to a Facebook Page using the official Meta Graph API
Used for Gold Tier 2.2: Facebook + Instagram Integration
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

try:
    from .base_skill import BaseSkill, run_skill
    from .meta_api_client import setup_meta_client_from_env
except ImportError:
    from base_skill import BaseSkill, run_skill
    from meta_api_client import setup_meta_client_from_env


class PostFacebookSkill(BaseSkill):
    """Skill to post content to Facebook Pages"""

    def _execute_impl(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute Facebook posting based on parameters"""
        action = params.get('action', 'create_post')

        if action == 'create_post':
            return self._create_post(params)
        elif action == 'schedule_post':
            return self._schedule_post(params)
        elif action == 'check_calendar':
            return self._check_content_calendar()
        elif action == 'execute_approved':
            return self._execute_approved_post(params)
        else:
            raise ValueError(f"Unknown action: {action}")

    def _get_meta_client(self):
        """Get configured Meta API client"""
        client = setup_meta_client_from_env()
        if not client:
            raise ValueError("Meta credentials not configured. Set META_APP_ID and META_APP_SECRET in .env")
        if not client.access_token:
            raise ValueError("Meta access token not found. Run 'python scripts/setup_meta_api.py' first.")
        return client

    def _create_post(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new Facebook post (usually goes through approval)"""
        content = params.get('content')
        link = params.get('link')
        scheduled_for = params.get('scheduled_for')

        if not content:
            raise ValueError("Post content is required")

        # Check if approval is required
        requires_approval = params.get('requires_approval', True)

        if requires_approval:
            return self._create_approval_request(content, link, scheduled_for)

        # Post directly if configured
        return self._post_to_facebook(content, link)

    def _schedule_post(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Schedule a post for future publishing"""
        content = params.get('content')
        scheduled_time = params.get('scheduled_time')
        link = params.get('link')

        if not content:
            raise ValueError("Post content is required")
        if not scheduled_time:
            raise ValueError("Scheduled time is required")

        # Parse scheduled time
        try:
            schedule_dt = datetime.fromisoformat(scheduled_time)
        except:
            raise ValueError("Invalid scheduled_time format. Use ISO format: YYYY-MM-DDTHH:MM:SS")

        # Create scheduled post entry
        post_data = {
            'type': 'facebook_post',
            'content': content,
            'link': link,
            'scheduled_for': scheduled_time,
            'created_at': datetime.now().isoformat(),
            'status': 'scheduled'
        }

        # Save to content calendar
        calendar_path = self.vault_path / 'Content_Calendar'
        calendar_path.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        post_file = calendar_path / f"FACEBOOK_POST_{timestamp}.json"
        post_file.write_text(json.dumps(post_data, indent=2))

        self.logger.info(f"Scheduled Facebook post for {scheduled_time}")

        return {
            "success": True,
            "scheduled_for": scheduled_time,
            "calendar_file": str(post_file),
            "message": f"Facebook post scheduled for {scheduled_time}"
        }

    def _check_content_calendar(self) -> Dict[str, Any]:
        """Check content calendar for posts that need to be published"""
        calendar_path = self.vault_path / 'Content_Calendar'
        if not calendar_path.exists():
            return {"posts_due": [], "message": "No content calendar found"}

        now = datetime.now()
        posts_due = []

        for post_file in calendar_path.glob('FACEBOOK_POST_*.json'):
            try:
                data = json.loads(post_file.read_text())
                scheduled_time = datetime.fromisoformat(data['scheduled_for'])

                # Check if post is due
                if now >= scheduled_time and data.get('status') == 'scheduled':
                    posts_due.append({
                        'file': str(post_file),
                        'content': data['content'],
                        'link': data.get('link'),
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
                    post.get('link'),
                    post['scheduled_for']
                )
                created_count += 1

                # Mark as pending_approval in calendar
                data = json.loads(Path(post['file']).read_text())
                data['status'] = 'pending_approval'
                Path(post['file']).write_text(json.dumps(data, indent=2))
            except Exception as e:
                self.logger.error(f"Error creating approval for Facebook post: {e}")

        return {
            "posts_due": len(posts_due),
            "approval_requests_created": created_count,
            "message": f"Found {len(posts_due)} Facebook posts due, created {created_count} approval requests"
        }

    def _create_approval_request(self, content: str, link: Optional[str],
                                  scheduled_for: Optional[str]) -> Dict[str, Any]:
        """Create approval request file for Facebook post"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        approval_filename = f"FACEBOOK_POST_{timestamp}.md"
        approval_path = self.vault_path / 'Pending_Approval' / approval_filename

        # Store post data
        post_data = {
            'action': 'facebook_post',
            'content': content,
            'link': link,
            'scheduled_for': scheduled_for,
            'created_at': datetime.now().isoformat()
        }

        approval_content = f"""---
type: approval_request
action: facebook_post
status: pending
priority: normal
created: {datetime.now().isoformat()}
---

# Approval Request: Facebook Post

## Post Content
```
{content}
```

## Link
{'**Yes**: ' + str(link) if link else '**None**'}

## Scheduling
{'Scheduled for: ' + scheduled_for if scheduled_for else 'Immediate posting upon approval'}

## Actions Required
1. **Review** content for tone and accuracy
2. **Approve** by moving to **/Approved/** folder
3. **Reject** by moving to **/Rejected/** folder

---
**Skill**: PostFacebook
"""
        approval_path.write_text(approval_content, encoding='utf-8')

        # Save data for execution
        data_path = approval_path.with_suffix('.json')
        data_path.write_text(json.dumps(post_data, indent=2))

        self.logger.info(f"Created Facebook post approval request: {approval_path.name}")
        return {
            "requires_approval": True,
            "approval_file": str(approval_path),
            "message": f"Facebook post requires approval: {approval_path.name}"
        }

    def _execute_approved_post(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute approved Facebook post"""
        content = params.get('content')
        link = params.get('link')
        return self._post_to_facebook(content, link)

    def _post_to_facebook(self, content: str, link: Optional[str]) -> Dict[str, Any]:
        """Actually post to Facebook using the API"""
        try:
            client = self._get_meta_client()
            page_id = os.getenv('META_PAGE_ID')
            
            if not page_id:
                raise ValueError("META_PAGE_ID not configured in .env")

            # Get Page Access Token from the user token
            # In a real app, you'd fetch the specific page token from get_pages()
            pages = client.get_pages()
            page_token = None
            for page in pages:
                if page['id'] == page_id:
                    page_token = page['access_token']
                    break
            
            if not page_token:
                raise ValueError(f"Could not find access token for Page ID {page_id}. Grant 'pages_manage_posts' permission.")

            result = client.post_to_facebook_page(page_id, page_token, content, link)
            
            if result.get('success'):
                self.logger.info(f"Facebook post published: {result.get('post_id')}")
                
                # Gold Tier: Structured Audit Logging
                self._log_audit('facebook_post', result.get('post_id'), 'success', platform='facebook')
                
                return {
                    "success": True,
                    "post_id": result.get('post_id'),
                    "message": "Facebook post published successfully"
                }
            else:
                error_msg = result.get('error', 'Unknown error')
                # Check for transient errors
                if any(ind in str(error_msg).lower() for ind in ['timeout', 'connection', 'network', 'busy']):
                    return {
                        "success": False,
                        "status": "retry",
                        "error": error_msg,
                        "message": f"Transient Facebook error: {error_msg}. Post will be retried."
                    }
                raise RuntimeError(f"Facebook API error: {error_msg}")

        except Exception as e:
            self.logger.error(f"Failed to post to Facebook: {e}", exc_info=True)
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
        print("Usage: python post_facebook.py '<json_params>'")
        sys.exit(1)

    run_skill(PostFacebookSkill, sys.argv[1])
