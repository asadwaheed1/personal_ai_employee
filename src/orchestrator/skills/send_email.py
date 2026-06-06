#!/usr/bin/env python3
"""
Agent Skill: Send Email
Sends emails using Gmail MCP Server with Human-in-the-Loop approval support
Silver Tier Requirement: Uses MCP server for external action
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any
from base_skill import BaseSkill, run_skill
from gmail_retry_handler import with_gmail_retry


class SendEmailSkill(BaseSkill):
    """Skill to send emails via Gmail MCP Server"""

    def _execute_impl(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Send email based on parameters"""
        to = params.get('to')
        subject = params.get('subject')
        body = params.get('body')
        cc = params.get('cc', [])
        bcc = params.get('bcc', [])
        attachments = params.get('attachments', [])

        # Enhanced validation
        if not to:
            raise ValueError("Recipient email ('to') is required")
        if not subject:
            raise ValueError("Email subject is required")
        if not body or not body.strip():
            raise ValueError("Email body is required and cannot be empty")

        # Validate email format
        if not self._validate_email(to):
            raise ValueError(f"Invalid email address: {to}")

        # Validate CC/BCC if provided
        if cc:
            cc = [cc] if isinstance(cc, str) else cc
            for email in cc:
                if not self._validate_email(email):
                    raise ValueError(f"Invalid CC email address: {email}")

        if bcc:
            bcc = [bcc] if isinstance(bcc, str) else bcc
            for email in bcc:
                if not self._validate_email(email):
                    raise ValueError(f"Invalid BCC email address: {email}")

        # Validate attachments exist
        if attachments:
            attachments = [attachments] if isinstance(attachments, str) else attachments
            for attachment in attachments:
                attachment_path = Path(attachment)
                if not attachment_path.exists():
                    self.logger.warning(f"Attachment not found: {attachment}")
                    # Remove non-existent attachments
                    attachments = [a for a in attachments if Path(a).exists()]

        # Check for dry run mode
        dry_run = os.getenv('DRY_RUN', 'false').lower() == 'true'
        if dry_run:
            self.logger.info(f"[DRY RUN] Would send email to {to}")
            return {
                "dry_run": True,
                "to": to,
                "subject": subject,
                "message": "Email would be sent (dry run mode)"
            }

        # Check if approval is required
        if self._requires_approval(to, subject, body):
            return self._create_approval_request(to, subject, body, cc, bcc, attachments)

        # For Silver Tier: Use MCP Server instead of direct API
        # Create an MCP action file for the orchestrator to process
        result = self._create_mcp_email_action(to, subject, body, cc, bcc, attachments)

        return result

    def _validate_email(self, email: str) -> bool:
        """Validate email address format"""
        import re
        if not email or not isinstance(email, str):
            return False
        # Basic email validation regex
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email.strip()) is not None

    def _requires_approval(self, to: str, subject: str, body: str) -> bool:
        """Check if email requires approval based on Company Handbook rules"""
        # Load Company Handbook
        handbook_path = self.vault_path / 'Company_Handbook.md'
        if not handbook_path.exists():
            # Default behavior: require approval for external domains
            return self._is_external_email(to)

        # Check for approval rules in handbook
        content = self.read_file(handbook_path)
        content_lower = content.lower()

        # Check for sensitive keywords
        sensitive_keywords = ['payment', 'invoice', 'contract', 'legal', 'confidential']
        for keyword in sensitive_keywords:
            if keyword in subject.lower() or keyword in body.lower():
                return True

        # Check if external email
        if self._is_external_email(to):
            # Look for external email policy
            if 'external emails require approval' in content_lower:
                return True

        # Check for high-value recipient rules
        high_value_keywords = ['client', 'customer', 'vendor', 'partner', 'ceo', 'director']
        for keyword in high_value_keywords:
            if keyword in to.lower():
                return True

        return False

    def _is_external_email(self, email: str) -> bool:
        """Check if email is to external domain"""
        # Get allowed domains from Company Handbook or default
        allowed_domains = ['yourcompany.com', 'yourorg.com']  # Default placeholders

        domain = email.split('@')[-1].lower() if '@' in email else ''
        return domain not in allowed_domains

    def _create_approval_request(self, to: str, subject: str, body: str,
                                  cc: list, bcc: list, attachments: list) -> Dict[str, Any]:
        """Create an approval request file for the email"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        sanitized_subject = self._sanitize_filename(subject)[:30]

        approval_filename = f"EMAIL_{timestamp}_{sanitized_subject}.md"
        approval_path = self.vault_path / 'Pending_Approval' / approval_filename

        # Store email data for later execution
        email_data = {
            'action': 'send_email',
            'to': to,
            'cc': cc,
            'bcc': bcc,
            'subject': subject,
            'body': body,
            'attachments': attachments,
            'created_at': datetime.now().isoformat()
        }

        content = f"""---
type: approval_request
action: send_email
status: pending
priority: high
created: {datetime.now().isoformat()}
expires: {(datetime.now().replace(hour=datetime.now().hour + 24)).isoformat()}
---

# Approval Request: Send Email

## Email Details
- **To**: {to}
- **CC**: {', '.join(cc) if cc else 'None'}
- **BCC**: {', '.join(bcc) if bcc else 'None'}
- **Subject**: {subject}

## Email Body
```
{body}
```

## Reason for Approval
This email has been flagged as requiring approval based on:
- External recipient
- Sensitive content detected
- High-value recipient

## Actions Required
1. Review the email content above
2. Move this file to **/Approved/** to authorize sending
3. Move this file to **/Rejected/** to cancel

## Technical Details
- Created: {datetime.now().strftime('%Y-%m-%d %H:%M')}
- Skill: SendEmail
- External Action: Gmail MCP Server
- Silver Tier Compliance: Uses MCP for external actions

---
**Note**: After approval, the email will be sent via the Gmail MCP Server and this file will be moved to /Done/
"""

        approval_path.write_text(content, encoding='utf-8')
        self.logger.info(f"Created approval request: {approval_path.name}")

        # Also save the email data as JSON for the orchestrator to use
        data_path = approval_path.with_suffix('.json')
        data_path.write_text(json.dumps(email_data, indent=2), encoding='utf-8')

        return {
            "requires_approval": True,
            "approval_file": str(approval_path),
            "message": f"Email requires approval. Review {approval_path.name} and move to /Approved/ to send via MCP server."
        }

    def _create_mcp_email_action(self, to: str, subject: str, body: str,
                                  cc: list, bcc: list, attachments: list) -> Dict[str, Any]:
        """
        Silver Tier: Create MCP action file for Gmail MCP Server
        The orchestrator will process this via the MCP server
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        action_filename = f"MCP_EMAIL_{timestamp}.json"
        action_path = self.vault_path / 'Needs_Action' / action_filename

        # MCP action payload for Gmail server
        mcp_action = {
            "mcp_server": "gmail",
            "tool": "send_email",
            "timestamp": datetime.now().isoformat(),
            "status": "pending",
            "params": {
                "to": to,
                "subject": subject,
                "body": body,
                "cc": cc if cc else None,
                "bcc": bcc if bcc else None
            },
            "result": None,
            "executed_at": None
        }

        action_path.write_text(json.dumps(mcp_action, indent=2), encoding='utf-8')
        self.logger.info(f"Created MCP email action: {action_path.name}")
        
        # Gold Tier: Structured Audit Logging
        self._log_audit('email_mcp_queued', to, 'success', platform='gmail', details={'subject': subject})

        return {
            "mcp_action_created": True,
            "action_file": str(action_path),
            "mcp_server": "gmail",
            "tool": "send_email",
            "message": f"Email action queued for MCP execution via Gmail MCP Server. Action file: {action_path.name}"
        }

    def _send_email_via_gmail(self, to: str, subject: str, body: str,
                               cc: list, bcc: list, attachments: list) -> Dict[str, Any]:
        """Send email using Gmail API with retry logic"""
        return self._send_email_via_gmail_with_retry(to, subject, body, cc, bcc, attachments)

    @with_gmail_retry
    def _send_email_via_gmail_with_retry(self, to: str, subject: str, body: str,
                                          cc: list, bcc: list, attachments: list) -> Dict[str, Any]:
        """Send email using Gmail API (wrapped with retry logic)"""
        try:
            from google.auth.transport.requests import Request
            from google.oauth2.credentials import Credentials
            from googleapiclient.discovery import build
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            from email.mime.base import MIMEBase
            import base64

            # Load credentials
            token_path = Path(os.getenv('GMAIL_TOKEN_PATH', './credentials/gmail_token.json'))
            if not token_path.exists():
                raise FileNotFoundError(f"Gmail token not found at {token_path}. Run Gmail watcher first.")

            creds = Credentials.from_authorized_user_file(str(token_path), [
                'https://www.googleapis.com/auth/gmail.send'
            ])

            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                    # Save refreshed token
                    token_path.write_text(creds.to_json())
                else:
                    raise RuntimeError("Gmail credentials expired. Please re-authenticate.")

            service = build('gmail', 'v1', credentials=creds)

            # Create message
            msg = MIMEMultipart()
            msg['to'] = to
            msg['subject'] = subject

            if cc:
                msg['cc'] = ', '.join(cc)
            if bcc:
                msg['bcc'] = ', '.join(bcc)

            # Attach body
            msg.attach(MIMEText(body, 'plain'))

            # Attach files if any
            for attachment_path in attachments:
                attachment = Path(attachment_path)
                if attachment.exists():
                    # Check file size (Gmail limit: 25MB)
                    file_size = attachment.stat().st_size
                    if file_size > 25 * 1024 * 1024:
                        self.logger.warning(f"Attachment {attachment.name} exceeds 25MB limit, skipping")
                        continue

                    with open(attachment, 'rb') as f:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(f.read())
                        from email import encoders
                        encoders.encode_base64(part)
                        part.add_header(
                            'Content-Disposition',
                            f'attachment; filename="{attachment.name}"'
                        )
                        msg.attach(part)

            # Encode and send
            raw_message = base64.urlsafe_b64encode(msg.as_bytes()).decode('utf-8')
            result = service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()

            self.logger.info(f"Email sent successfully: {result['id']}")

            return {
                "success": True,
                "message_id": result['id'],
                "to": to,
                "subject": subject,
                "sent_at": datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Failed to send email: {e}", exc_info=True)
            raise RuntimeError(f"Failed to send email: {e}")

    def _log_email_sent(self, to: str, subject: str, result: Dict):
        """Log the sent email to activity log"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": "email_sent",
            "to": to,
            "subject": subject,
            "message_id": result.get('message_id'),
            "success": result.get('success', False)
        }

        # Write to log file
        log_path = self.vault_path / 'Logs' / f'email_activity_{datetime.now().strftime("%Y-%m-%d")}.json'
        log_path.parent.mkdir(parents=True, exist_ok=True)

        logs = []
        if log_path.exists():
            try:
                logs = json.loads(log_path.read_text())
            except:
                logs = []

        logs.append(log_entry)
        log_path.write_text(json.dumps(logs, indent=2))

    def _sanitize_filename(self, name: str) -> str:
        """Sanitize filename"""
        import re
        sanitized = re.sub(r'[^\w\-. ]', '_', name)
        sanitized = sanitized[:100].strip('. ')
        return sanitized or 'unnamed'


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python send_email.py '<json_params>'")
        print("Example: python send_email.py '{\"to\": \"user@example.com\", \"subject\": \"Hello\", \"body\": \"Message\"}'")
        sys.exit(1)

    run_skill(SendEmailSkill, sys.argv[1])
