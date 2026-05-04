#!/usr/bin/env python3
"""
Agent Skill: Process Approved Actions
Executes approved actions from the Approved folder
"""

import json
import re
import subprocess
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

try:
    from .base_skill import BaseSkill, run_skill
except ImportError:
    from base_skill import BaseSkill, run_skill


class ProcessApprovedActionsSkill(BaseSkill):
    """Skill to process and execute approved actions"""

    def _execute_impl(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Process and execute approved actions"""
        files = params.get('files', [])

        # If no specific files provided, process all .md files in Approved
        if not files:
            approved_dir = self.vault_path / 'Approved'
            if approved_dir.exists():
                files = [str(f) for f in approved_dir.glob('*.md') if not f.name.startswith('.')]

        if not files:
            self.logger.info("No approved actions to process")
            return {"processed_count": 0, "message": "No approved actions"}

        # Process each approved action
        processed_count = 0
        execution_results = []

        for file_path in files:
            file_path = Path(file_path)
            if not file_path.exists():
                self.logger.warning(f"File not found: {file_path}")
                continue

            try:
                # Read approval file
                content = self.read_file(file_path)
                self.logger.info(f"Processing approved action: {file_path.name}")

                # Extract approval details
                approval_data = self._parse_approval_file(content, file_path.name)

                # Execute the approved action
                result = self._execute_approved_action(approval_data, content)

                action_label = approval_data.get('type') or approval_data.get('action', 'unknown')
                execution_results.append({
                    "file": file_path.name,
                    "action": action_label,
                    "result": result
                })

                # Determine if the skill actually succeeded
                is_failed = (
                    result.get('status') == 'failed'
                    or result.get('success') is False
                    or ('error' in result and result.get('status') not in ('completed', 'mcp_queued', 'logged'))
                )

                if is_failed:
                    error_msg = result.get('error', 'skill returned failed status')
                    self.logger.error(f"Skill returned failure for {file_path.name}: {error_msg}")
                    execution_results[-1]['error'] = error_msg
                    # Move to Pending_Approval so user can fix and re-approve
                    pending_dir = self.vault_path / 'Pending_Approval'
                    pending_dir.mkdir(exist_ok=True)
                    failed_note = f"\n\n---\n## Action Required\n**Failed at**: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n**Error**: {error_msg}\n\nFix the issue above, then move this file to **/Approved/** to retry.\n"
                    file_path.write_text(content + failed_note)
                    dest = pending_dir / file_path.name
                    file_path.rename(dest)
                    self.logger.info(f"Moved failed action to Pending_Approval: {file_path.name}")
                else:
                    # mcp_queued: process_email_actions.py already archived the file to Done
                    # For all other cases archive here
                    if result.get('status') != 'mcp_queued':
                        self._archive_approval_file(file_path, approval_data, result)
                    elif file_path.exists():
                        self._archive_approval_file(file_path, approval_data, result)
                    processed_count += 1
                    self.logger.info(f"Successfully executed approved action: {file_path.name}")

            except Exception as e:
                self.logger.error(f"Failed to execute approved action {file_path}: {e}")
                execution_results.append({
                    "file": file_path.name,
                    "error": str(e)
                })
                continue

        # Update dashboard
        self._update_dashboard(processed_count, execution_results)

        # Log to audit trail
        self._log_audit_trail(execution_results)

        return {
            "processed_count": processed_count,
            "execution_results": execution_results
        }

    def _parse_approval_file(self, content: str, filename: str) -> Dict[str, Any]:
        """Parse approval file to extract action details"""
        approval_data = {"id": filename.replace('.md', '')}

        # Extract frontmatter (manual parse to avoid yaml dep)
        if content.startswith('---'):
            try:
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    for line in parts[1].strip().split('\n'):
                        if ':' in line:
                            key, value = line.split(':', 1)
                            approval_data[key.strip()] = value.strip()
            except Exception as e:
                self.logger.warning(f"Failed to parse approval metadata: {e}")

        # Extract action type from content (approval request files)
        action_match = re.search(r'Action Type:\s*(.+?)\n', content)
        if action_match:
            approval_data['action'] = action_match.group(1).strip()

        return approval_data

    def _execute_approved_action(self, approval_data: Dict[str, Any], content: str) -> Dict[str, Any]:
        """Execute the approved action based on type"""
        file_type = approval_data.get('type', '').lower()

        # Gmail watcher email files (type: email) — queue via MCP
        if file_type == 'email':
            return self._execute_approved_email_via_mcp(approval_data, content)

        # Scheduled post files carry type: *_scheduled_post in frontmatter but no action: field
        _PLATFORM_FROM_TYPE = {
            'twitter_scheduled_post': 'twitter',
            'facebook_scheduled_post': 'facebook',
            'instagram_scheduled_post': 'instagram',
            'linkedin_scheduled_post': 'linkedin',
        }
        if file_type in _PLATFORM_FROM_TYPE:
            return self._execute_social_post(_PLATFORM_FROM_TYPE[file_type], approval_data, content)

        action_type = approval_data.get('action', '').lower()

        # Social Media Posting Actions — parse content from approval MD, call skill directly
        if 'twitter_post' in action_type:
            return self._execute_social_post('twitter', approval_data, content)
        elif 'facebook_post' in action_type:
            return self._execute_social_post('facebook', approval_data, content)
        elif 'instagram_post' in action_type:
            return self._execute_social_post('instagram', approval_data, content)
        elif 'linkedin_post' in action_type or 'linkedin_scheduled_post' in action_type:
            return self._execute_social_post('linkedin', approval_data, content)

        if 'payment' in action_type:
            return self._execute_payment_action(approval_data, content)
        elif 'email' in action_type or action_type == 'send_email':
            return self._execute_email_action(approval_data, content)
        elif 'file' in action_type or 'delete' in action_type:
            return self._execute_file_action(approval_data, content)
        elif 'system' in action_type:
            return self._execute_system_action(approval_data, content)
        else:
            return self._execute_generic_action(approval_data, content)

    def _execute_social_post(self, platform: str, approval_data: Dict[str, Any], content: str) -> Dict[str, Any]:
        """Parse approval MD and call the appropriate social posting skill directly."""
        try:
            if platform == 'facebook':
                post_content = self._parse_md_code_block(content, '## Post Content')
                if not post_content:
                    post_content = self._parse_md_code_block(content, '## Content')
                link = self._parse_md_bold_field(content, 'Link')
                from .post_facebook import PostFacebookSkill
                skill = PostFacebookSkill(str(self.vault_path))
                return skill.execute({'content': post_content, 'link': link, 'require_approval': False})

            elif platform == 'instagram':
                caption = self._parse_md_code_block(content, '## Caption')
                if not caption:
                    caption = self._parse_md_code_block(content, '## Content')
                image_url = self._parse_md_bold_field(content, 'Image URL')
                from .post_instagram import PostInstagramSkill
                skill = PostInstagramSkill(str(self.vault_path))
                return skill.execute({'content': caption, 'image_url': image_url, 'require_approval': False})

            elif platform == 'linkedin':
                post_content = self._parse_md_code_block(content, '## Post Content')
                if not post_content:
                    post_content = self._parse_md_code_block(content, '## Content')
                from .post_linkedin import PostLinkedInSkill
                skill = PostLinkedInSkill(str(self.vault_path))
                return skill.execute({'content': post_content, 'require_approval': False})

            elif platform == 'twitter':
                tweet = self._parse_md_code_block(content, '## Tweet')
                if not tweet:
                    tweet = self._parse_md_code_block(content, '## Post Content')
                if not tweet:
                    tweet = self._parse_md_code_block(content, '## Content')
                from .post_twitter import PostTwitterSkill
                skill = PostTwitterSkill(str(self.vault_path))
                return skill.execute({'content': tweet, 'require_approval': False})

            return {'status': 'failed', 'error': f'Unknown platform: {platform}'}

        except Exception as e:
            self.logger.error(f"Social post execution failed for {platform}: {e}", exc_info=True)
            return {'status': 'failed', 'error': str(e)}

    def _parse_md_code_block(self, content: str, header: str) -> str:
        """Extract text inside first code block after a markdown header."""
        import re
        pattern = rf'{re.escape(header)}\s*\n```[^\n]*\n(.*?)```'
        match = re.search(pattern, content, re.DOTALL)
        return match.group(1).strip() if match else ''

    def _parse_md_bold_field(self, content: str, field_name: str) -> Optional[str]:
        """Extract value from pattern '## Field\n**value**'. Returns None if value is None/empty."""
        import re
        pattern = rf'## {re.escape(field_name)}\s*\n\*\*(.+?)\*\*'
        match = re.search(pattern, content)
        if match:
            val = match.group(1).strip()
            if val.lower() not in ('none', ''):
                return val
        return None

    def _execute_skill(self, skill_name: str, approval_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a specific skill with approved parameters"""
        skill_path = Path(__file__).parent / skill_name
        if not skill_path.exists():
            return {'status': 'failed', 'error': f'Skill not found: {skill_name}'}

        # Try to load the companion JSON data file
        # Reconstruct path from id
        approved_dir = self.vault_path / 'Approved'
        data_path = approved_dir / f"{approval_data['id']}.json"
        
        if data_path.exists():
            try:
                params = json.loads(data_path.read_text())
                params['action'] = 'execute_approved'
            except:
                params = {'action': 'execute_approved'}
        else:
            params = {'action': 'execute_approved'}

        try:
            result = subprocess.run(
                [sys.executable, str(skill_path), json.dumps(params)],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=str(self.vault_path.parent)
            )

            if result.returncode == 0:
                try:
                    payload = json.loads(result.stdout)
                    return payload.get('result', payload)
                except:
                    return {'status': 'completed', 'message': 'Skill executed successfully'}
            else:
                return {'status': 'failed', 'error': result.stderr[:300]}
        except Exception as e:
            return {'status': 'failed', 'error': str(e)}

    def _execute_approved_email_via_mcp(self, email_data: Dict[str, Any], content: str) -> Dict[str, Any]:
        """
        Route approved email file through process_email_actions skill.
        That skill creates MCP JSON files; the MCP processor executes them
        via Gmail MCP server in the next orchestrator cycle.
        """
        email_file = email_data.get('id', '')
        # Reconstruct full path: email_data['id'] is filename without .md
        approved_dir = self.vault_path / 'Approved'
        email_path = approved_dir / f"{email_file}.md"

        if not email_path.exists():
            # Try to find by id in Approved folder
            matches = list(approved_dir.glob(f"{email_file}*"))
            if matches:
                email_path = matches[0]
            else:
                return {'status': 'failed', 'error': f'Email file not found: {email_file}'}

        skill_path = Path(__file__).parent / 'process_email_actions.py'
        if not skill_path.exists():
            return {'status': 'failed', 'error': f'process_email_actions.py not found at {skill_path}'}

        params = {
            'email_file': str(email_path),
            'vault_path': str(self.vault_path)
        }

        self.logger.info(f"Routing approved email to MCP queue: {email_path.name}")

        try:
            result = subprocess.run(
                [sys.executable, str(skill_path), json.dumps(params)],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=str(self.vault_path.parent)
            )

            if result.returncode == 0:
                try:
                    payload = json.loads(result.stdout)
                    skill_result = payload.get('result', payload)
                    queued = skill_result.get('actions_queued', 0)
                    self.logger.info(f"Email MCP actions queued: {queued}")
                    return {
                        'status': 'mcp_queued',
                        'message': f'Email actions queued for MCP execution ({queued} actions)',
                        'actions_queued': queued
                    }
                except Exception:
                    return {'status': 'mcp_queued', 'message': 'Email actions queued for MCP execution'}
            else:
                self.logger.error(f"process_email_actions failed: {result.stderr[:300]}")
                return {'status': 'failed', 'error': result.stderr[:300]}

        except subprocess.TimeoutExpired:
            self.logger.error("process_email_actions timed out (60s)")
            return {'status': 'failed', 'error': 'Skill timeout after 60s'}
        except Exception as e:
            self.logger.error(f"Failed to route email to MCP: {e}", exc_info=True)
            return {'status': 'failed', 'error': str(e)}

    def _execute_payment_action(self, approval_data: Dict[str, Any], content: str) -> Dict[str, Any]:
        return {
            "status": "logged",
            "message": "Payment action approved and logged",
            "action": "payment",
            "details": approval_data
        }

    def _execute_email_action(self, approval_data: Dict[str, Any], content: str) -> Dict[str, Any]:
        return {
            "status": "logged",
            "message": "Email send action approved and logged",
            "action": "email",
            "details": approval_data
        }

    def _execute_file_action(self, approval_data: Dict[str, Any], content: str) -> Dict[str, Any]:
        action = approval_data.get('action', '')
        return {
            "status": "logged",
            "message": "File action approved and logged",
            "action": action or "file",
            "details": approval_data
        }

    def _execute_system_action(self, approval_data: Dict[str, Any], content: str) -> Dict[str, Any]:
        return {
            "status": "logged",
            "message": "System change approved and logged",
            "action": "system_change",
            "details": approval_data
        }

    def _execute_generic_action(self, approval_data: Dict[str, Any], content: str) -> Dict[str, Any]:
        return {
            "status": "completed",
            "message": "Generic action approved and processed",
            "action": "generic",
            "details": approval_data
        }

    def _archive_approval_file(self, file_path: Path, approval_data: Dict[str, Any], result: Dict[str, Any]):
        """Move approval file to Done with execution summary"""
        content = self.read_file(file_path)

        # Add execution summary
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')

        # Convert result to JSON-serializable format
        def json_serializable(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError(f"Type {type(obj)} not serializable")

        try:
            result_json = json.dumps(result, indent=2, default=json_serializable)
        except Exception as e:
            result_json = json.dumps({"error": f"Could not serialize result: {str(e)}"})

        summary = f"""

---
## Execution Summary
**Executed**: {timestamp}
**Status**: {result.get('status', 'unknown')}
**Result**: {result.get('message', 'No message')}

### Execution Details
```json
{result_json}
```
"""

        # Append summary
        content += summary

        # Write to Done folder
        done_path = self.vault_path / 'Done' / f"EXECUTED_{file_path.name}"
        self.write_file(done_path, content)

        # Remove from Approved folder
        file_path.unlink()

        self.logger.info(f"Archived approval file to: {done_path.name}")

    def _update_dashboard(self, processed_count: int, execution_results: list):
        """Update dashboard with execution results"""
        dashboard_path = self.vault_path / 'Dashboard.md'

        # Read current dashboard
        if dashboard_path.exists():
            content = self.read_file(dashboard_path)
        else:
            content = "# AI Employee Dashboard\n\n## Status\nOperational\n"

        # Add new activity
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        successful = sum(1 for r in execution_results if 'error' not in r)
        activity = f"Executed {processed_count} approved actions ({successful} successful)"

        activity_line = f"- [{timestamp}] {activity}"

        # Find or create Recent Activity section
        if "## Recent Activity" in content:
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if line.startswith("## Recent Activity"):
                    # Insert after header
                    lines.insert(i + 1, activity_line)
                    break
            content = '\n'.join(lines)
        else:
            content += f"\n\n## Recent Activity\n{activity_line}"

        self.write_file(dashboard_path, content)
        self.logger.info(f"Updated dashboard with execution results")

    def _log_audit_trail(self, execution_results: list):
        """Log execution to audit trail"""
        audit_dir = self.vault_path / 'Logs'
        audit_dir.mkdir(exist_ok=True)

        audit_file = audit_dir / f'audit_{datetime.now().strftime("%Y-%m-%d")}.json'

        # Read existing audit or create new
        if audit_file.exists():
            try:
                with open(audit_file, 'r') as f:
                    audit_log = json.load(f)
            except:
                audit_log = []
        else:
            audit_log = []

        # Add new entries
        for result in execution_results:
            audit_entry = {
                "timestamp": datetime.now().isoformat(),
                "type": "approved_action_execution",
                "result": result
            }
            audit_log.append(audit_entry)

        # Write audit log
        with open(audit_file, 'w') as f:
            json.dump(audit_log, f, indent=2)

        self.logger.info(f"Updated audit trail: {audit_file.name}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python process_approved_actions.py '<json_params>'")
        sys.exit(1)

    run_skill(ProcessApprovedActionsSkill, sys.argv[1])