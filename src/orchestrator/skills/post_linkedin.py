#!/usr/bin/env python3
"""
Agent Skill: Post to LinkedIn
Posts content to LinkedIn using the official LinkedIn API v2 with Human-in-the-Loop approval support

This skill uses the LinkedIn OAuth 2.0 API for posting content:
- Text shares
- Posts with links
- Posts with images

Requires:
- LINKEDIN_CLIENT_ID
- LINKEDIN_CLIENT_SECRET
- LINKEDIN_REDIRECT_URI
- Authenticated token (run setup_linkedin_auth.py first)
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
try:
    from .base_skill import BaseSkill, run_skill
    from .linkedin_api_client import LinkedInAPIClient
except ImportError:
    from base_skill import BaseSkill, run_skill
    from linkedin_api_client import LinkedInAPIClient


class PostLinkedInSkill(BaseSkill):
    """Skill to post content to LinkedIn using official API"""

    def _execute_impl(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute LinkedIn posting based on parameters"""
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

    def _get_linkedin_client(self) -> LinkedInAPIClient:
        """Get configured LinkedIn API client"""
        import os

        client_id = os.getenv('LINKEDIN_CLIENT_ID')
        client_secret = os.getenv('LINKEDIN_CLIENT_SECRET')
        redirect_uri = os.getenv('LINKEDIN_REDIRECT_URI', 'http://localhost:8000/callback')
        token_path = os.getenv('LINKEDIN_TOKEN_PATH', './credentials/linkedin_api_token.json')

        if not client_id or not client_secret:
            raise ValueError(
                "LinkedIn API credentials not configured. "
                "Set LINKEDIN_CLIENT_ID and LINKEDIN_CLIENT_SECRET environment variables."
            )

        client = LinkedInAPIClient(client_id, client_secret, redirect_uri, token_path)

        if not client.is_authenticated():
            raise RuntimeError(
                "LinkedIn not authenticated. "
                f"Run: python src/orchestrator/skills/linkedin_api_client.py {client_id} {client_secret} {redirect_uri}"
            )

        return client

    def _create_post(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new LinkedIn post"""
        content = params.get('content')
        image_path = params.get('image_path')
        scheduled_for = params.get('scheduled_for')

        if not content:
            raise ValueError("Post content is required")

        # Validate content
        if len(content) > 3000:
            raise ValueError("LinkedIn post content exceeds 3000 character limit")

        # Check if approval is required (always required for LinkedIn posts)
        requires_approval = params.get('requires_approval', True)

        if requires_approval:
            return self._create_approval_request(content, image_path, scheduled_for)

        # Post directly (if configured to skip approval)
        return self._post_to_linkedin(content, image_path)

    def _schedule_post(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Schedule a post for future publishing"""
        content = params.get('content')
        scheduled_time = params.get('scheduled_time')

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
            'type': 'linkedin_post',
            'content': content,
            'image_path': params.get('image_path'),
            'scheduled_for': scheduled_time,
            'created_at': datetime.now().isoformat(),
            'status': 'scheduled'
        }

        # Save to content calendar
        calendar_path = self.vault_path / 'Content_Calendar'
        calendar_path.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        post_file = calendar_path / f"POST_{timestamp}.json"
        post_file.write_text(json.dumps(post_data, indent=2))

        self.logger.info(f"Scheduled LinkedIn post for {scheduled_time}")

        return {
            "success": True,
            "scheduled_for": scheduled_time,
            "calendar_file": str(post_file),
            "message": f"Post scheduled for {scheduled_time}"
        }

    def _check_content_calendar(self) -> Dict[str, Any]:
        """Check content calendar for posts that need to be published"""
        calendar_path = self.vault_path / 'Content_Calendar'
        if not calendar_path.exists():
            return {"posts_due": [], "message": "No content calendar found"}

        now = datetime.now()
        posts_due = []

        for post_file in calendar_path.glob('POST_*.json'):
            try:
                data = json.loads(post_file.read_text())
                scheduled_time = datetime.fromisoformat(data['scheduled_for'])

                # Check if post is due (within next hour and not already processed)
                if now >= scheduled_time and data.get('status') == 'scheduled':
                    posts_due.append({
                        'file': str(post_file),
                        'content': data['content'],
                        'image_path': data.get('image_path'),
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
                    post.get('image_path'),
                    post['scheduled_for']
                )
                created_count += 1

                # Mark as pending_approval in calendar
                data = json.loads(Path(post['file']).read_text())
                data['status'] = 'pending_approval'
                Path(post['file']).write_text(json.dumps(data, indent=2))
            except Exception as e:
                self.logger.error(f"Error creating approval for post: {e}")

        return {
            "posts_due": len(posts_due),
            "approval_requests_created": created_count,
            "message": f"Found {len(posts_due)} posts due, created {created_count} approval requests"
        }

    def _get_content_from_calendar(self) -> Optional[Dict[str, Any]]:
        """Get next scheduled post from content calendar"""
        calendar_path = self.vault_path / 'Content_Calendar'
        if not calendar_path.exists():
            return None

        now = datetime.now()
        due_posts = []

        for post_file in calendar_path.glob('POST_*.json'):
            try:
                data = json.loads(post_file.read_text())
                if data.get('status') == 'scheduled':
                    scheduled_time = datetime.fromisoformat(data['scheduled_for'])
                    if now >= scheduled_time:
                        due_posts.append((scheduled_time, data))
            except:
                continue

        if due_posts:
            # Return the oldest scheduled post
            due_posts.sort(key=lambda x: x[0])
            return due_posts[0][1]

        return None

    def _create_approval_request(self, content: str, image_path: Optional[str],
                                  scheduled_for: Optional[str]) -> Dict[str, Any]:
        """Create approval request file for LinkedIn post"""
        import os

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        approval_filename = f"LINKEDIN_POST_{timestamp}.md"
        approval_path = self.vault_path / 'Pending_Approval' / approval_filename

        # Store post data
        post_data = {
            'action': 'linkedin_post',
            'content': content,
            'image_path': image_path,
            'scheduled_for': scheduled_for,
            'created_at': datetime.now().isoformat()
        }

        # Determine post type
        post_type = "Scheduled Post" if scheduled_for else "Immediate Post"

        # Determine if using API
        using_api = os.getenv('LINKEDIN_CLIENT_ID') is not None
        api_status = "✓ Official LinkedIn API" if using_api else "⚠ Browser automation"

        approval_content = f"""---
type: approval_request
action: linkedin_post
post_type: {post_type}
status: pending
priority: normal
created: {datetime.now().isoformat()}
expires: {(datetime.now() + timedelta(hours=48)).isoformat()}
---

# Approval Request: LinkedIn Post

## Post Type
**{post_type}**

## API Status
**{api_status}**

## Post Content
```
{content}
```

## Content Analysis
- **Character Count**: {len(content)}
- **Estimated Read Time**: {len(content) // 200 + 1} minutes
- **Hashtags Detected**: {', '.join([word for word in content.split() if word.startswith('#')]) or 'None'}

## Image Attachment
{'**Yes**: ' + str(image_path) if image_path else '**None**'}

## Scheduling
{'Scheduled for: ' + scheduled_for if scheduled_for else 'Immediate posting upon approval'}

## Purpose
This post is part of your automated content strategy to:
- Generate business leads
- Increase brand visibility
- Engage with your professional network
- Drive traffic to your business

## Actions Required
1. **Review** the content above for accuracy and tone
2. **Edit** if needed by modifying the content section above
3. **Approve** by moving this file to **/Approved/** folder
4. **Reject** by moving this file to **/Rejected/** folder

## Best Practices Checklist
- [ ] Content is professional and on-brand
- [ ] No sensitive information included
- [ ] Links are working (if any)
- [ ] Appropriate for your network
- [ ] No spelling or grammar errors

## After Approval
Once approved, the post will be published to LinkedIn automatically and:
- Logged to the activity log
- Moved to /Done/
- Dashboard will be updated

---
**Created**: {datetime.now().strftime('%Y-%m-%d %H:%M')}
**Platform**: LinkedIn (Official API v2)
**Skill**: PostLinkedIn
"""

        approval_path.write_text(approval_content, encoding='utf-8')

        # Save post data for execution
        data_path = approval_path.with_suffix('.json')
        data_path.write_text(json.dumps(post_data, indent=2))

        self.logger.info(f"Created LinkedIn post approval request: {approval_path.name}")

        # Update Dashboard
        self._update_dashboard(f"LinkedIn post pending approval: {approval_path.name}")

        return {
            "requires_approval": True,
            "approval_file": str(approval_path),
            "content": content,
            "message": f"LinkedIn post requires approval. Review {approval_path.name} and move to /Approved/ to publish."
        }

    def _execute_approved_post(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute posting to LinkedIn (called after approval)"""
        content = params.get('content')
        image_path = params.get('image_path')

        if not content:
            raise ValueError("Content is required to post to LinkedIn")

        return self._post_to_linkedin(content, image_path)

    def _post_to_linkedin(self, content: str, image_path: Optional[str]) -> Dict[str, Any]:
        """Actually post content to LinkedIn using the official API"""
        import os

        # Check dry run mode
        dry_run = os.getenv('DRY_RUN', 'false').lower() == 'true'
        if dry_run:
            self.logger.info("[DRY RUN] Would post to LinkedIn")
            return {
                "dry_run": True,
                "content": content[:100] + "...",
                "message": "Post would be published (dry run mode)"
            }

        try:
            # Get LinkedIn API client
            client = self._get_linkedin_client()

            # Post with image if provided
            if image_path and Path(image_path).exists():
                result = client.create_post_with_image(content, str(image_path))
            else:
                result = client.create_text_share(content)

            if result.get('success'):
                self.logger.info(f"LinkedIn post published successfully: {result.get('post_id')}")

                # Log activity
                self._log_post(content, result.get('post_id'))

                return {
                    "success": True,
                    "content": content[:100] + "...",
                    "posted_at": datetime.now().isoformat(),
                    "post_id": result.get('post_id'),
                    "post_url": result.get('url'),
                    "message": "LinkedIn post published successfully via API"
                }
            else:
                error_msg = result.get('message', 'Unknown error')
                self.logger.error(f"LinkedIn API error: {error_msg}")
                raise RuntimeError(f"LinkedIn API error: {error_msg}")

        except ValueError as e:
            self.logger.error(f"LinkedIn configuration error: {e}")
            raise
        except RuntimeError as e:
            self.logger.error(f"LinkedIn authentication error: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Failed to post to LinkedIn: {e}", exc_info=True)
            raise RuntimeError(f"LinkedIn posting failed: {e}")

    def _log_post(self, content: str, post_id: Optional[str] = None):
        """Log the posted content"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": "linkedin_post",
            "content_preview": content[:100] + "..." if len(content) > 100 else content,
            "platform": "LinkedIn",
            "api_version": "v2",
            "post_id": post_id
        }

        log_path = self.vault_path / 'Logs' / f'linkedin_activity_{datetime.now().strftime("%Y-%m-%d")}.json'
        log_path.parent.mkdir(parents=True, exist_ok=True)

        logs = []
        if log_path.exists():
            try:
                logs = json.loads(log_path.read_text())
            except:
                logs = []

        logs.append(log_entry)
        log_path.write_text(json.dumps(logs, indent=2))

    def _update_dashboard(self, activity: str):
        """Update dashboard with posting activity"""
        dashboard_path = self.vault_path / 'Dashboard.md'
        if dashboard_path.exists():
            content = self.read_file(dashboard_path)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            activity_line = f"\n- [{timestamp}] {activity}"

            if "## Recent Activity" in content:
                content = content.replace(
                    "## Recent Activity",
                    f"## Recent Activity{activity_line}"
                )
            else:
                content += f"\n## Recent Activity{activity_line}\n"

            self.write_file(dashboard_path, content)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python post_linkedin.py '<json_params>'")
        print("\nExamples:")
        print('  Create post: python post_linkedin.py \'{"action": "create_post", "content": "Hello LinkedIn!"}\'')
        print('  Schedule post: python post_linkedin.py \'{"action": "schedule_post", "content": "...", "scheduled_time": "2026-04-01T09:00:00"}\'')
        print('  Check calendar: python post_linkedin.py \'{"action": "check_calendar"}\'')
        sys.exit(1)

    run_skill(PostLinkedInSkill, sys.argv[1])
