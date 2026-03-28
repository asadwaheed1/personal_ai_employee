#!/usr/bin/env python3
"""
Agent Skill: Create Approval Request
Generates approval request files for sensitive actions
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any

from base_skill import BaseSkill, run_skill


class CreateApprovalRequestSkill(BaseSkill):
    """Skill to create approval request files"""

    def _execute_impl(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create an approval request file"""
        action_type = params.get('action_type')
        action_details = params.get('action_details', {})
        reason = params.get('reason', '')
        expires_in_hours = params.get('expires_in_hours', 24)

        # Generate approval ID
        approval_id = f"APPROVAL_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Calculate expiration
        expires_at = datetime.now() + timedelta(hours=expires_in_hours)

        # Create approval content based on action type
        approval_content = self._generate_approval_content(
            approval_id,
            action_type,
            action_details,
            reason,
            expires_at
        )

        # Write approval file
        approval_path = self.vault_path / 'Pending_Approval' / f"{approval_id}.md"
        self.write_file(approval_path, approval_content)

        self.logger.info(f"Created approval request: {approval_path.name}")

        return {
            "approval_id": approval_id,
            "approval_path": str(approval_path),
            "action_type": action_type,
            "expires_at": expires_at.isoformat()
        }

    def _generate_approval_content(self, approval_id: str, action_type: str,
                                 action_details: Dict[str, Any], reason: str,
                                 expires_at: datetime) -> str:
        """Generate approval content based on action type"""

        # Get action-specific details
        details_section = self._get_action_details(action_type, action_details)

        # Generate content
        content = f"""---
id: {approval_id}
type: approval_request
action: {action_type}
created: {datetime.now().isoformat()}
expires: {expires_at.isoformat()}
status: pending
---

# Approval Required

## Summary
**Action Type**: {action_type.replace('_', ' ').title()}
**Created**: {datetime.now().strftime('%Y-%m-%d %H:%M')}
**Expires**: {expires_at.strftime('%Y-%m-%d %H:%M')}

## Reason for Approval
{reason}

## Action Details
{details_section}

## Approval Instructions

### To Approve:
1. Review the details above
2. If approved, move this file to the `/Approved/` folder
3. The system will automatically execute the action

### To Reject:
1. Add your rejection reason below
2. Move this file to the `/Rejected/` folder
3. The system will log the rejection and take no action

## Human Review Notes
[Add your review notes here]

## Decision
- [ ] **Approved** - Action authorized for execution
- [ ] **Rejected** - Action denied

**Reviewer**: ________________
**Date**: ________________
**Reason**: ________________

---

## Risk Assessment
"""

        # Add risk assessment based on action type
        content += self._get_risk_assessment(action_type, action_details)

        content += f"""

## System Notes
This approval request was automatically generated based on Company Handbook rules.
Please review carefully before approving.

*Approval ID: {approval_id}*
"""

        return content

    def _get_action_details(self, action_type: str, details: Dict[str, Any]) -> str:
        """Get formatted action details based on type"""

        if action_type == 'payment':
            return f"""
- **Amount**: ${details.get('amount', 'Unknown')}
- **Recipient**: {details.get('recipient', 'Unknown')}
- **Account**: {details.get('account', 'Not specified')}
- **Reference**: {details.get('reference', 'None')}
- **Purpose**: {details.get('purpose', 'Not specified')}
"""

        elif action_type == 'email':
            return f"""
- **To**: {details.get('to', 'Unknown')}
- **Subject**: {details.get('subject', 'No subject')}
- **Type**: {details.get('email_type', 'Regular')}
- **Attachments**: {len(details.get('attachments', []))} file(s)
- **Content Preview**: {details.get('preview', 'Not available')}
"""

        elif action_type == 'file_delete':
            return f"""
- **Files to Delete**: {', '.join(details.get('files', []))}
- **Reason**: {details.get('reason', 'Not specified')}
- **Backup Required**: {'Yes' if details.get('backup', True) else 'No'}
- **Permanent**: {'Yes' if details.get('permanent', False) else 'No (can be recovered)'}
"""

        elif action_type == 'system_change':
            return f"""
- **Change Type**: {details.get('change_type', 'Unknown')}
- **Component**: {details.get('component', 'Not specified')}
- **Description**: {details.get('description', 'No description')}
- **Rollback Plan**: {details.get('rollback', 'Not specified')}
- **Testing Required**: {'Yes' if details.get('testing', True) else 'No'}
"""

        else:
            # Generic format for unknown types
            if details:
                details_str = "\n".join(f"- **{k.title()}**: {v}" for k, v in details.items())
                return f"\n{details_str}\n"
            else:
                return "\n- No additional details provided\n"

    def _get_risk_assessment(self, action_type: str, details: Dict[str, Any]) -> str:
        """Get risk assessment for the action"""

        risk_levels = {
            'payment': self._assess_payment_risk(details),
            'email': self._assess_email_risk(details),
            'file_delete': self._assess_delete_risk(details),
            'system_change': self._assess_system_risk(details)
        }

        risk_info = risk_levels.get(action_type, {
            'level': 'Medium',
            'reason': 'Unknown action type',
            'mitigation': 'Review carefully'
        })

        return f"""
**Risk Level**: {risk_info['level']}

**Reason**: {risk_info['reason']}

**Mitigation**: {risk_info['mitigation']}
"""

    def _assess_payment_risk(self, details: Dict[str, Any]) -> Dict[str, Any]:
        """Assess risk for payment actions"""
        amount = details.get('amount', 0)

        if isinstance(amount, (int, float)) and amount > 1000:
            return {
                'level': 'High',
                'reason': f'Large payment amount (${amount})',
                'mitigation': 'Verify recipient and purpose carefully'
            }
        elif isinstance(amount, (int, float)) and amount > 100:
            return {
                'level': 'Medium',
                'reason': f'Moderate payment amount (${amount})',
                'mitigation': 'Confirm payment details are correct'
            }
        else:
            return {
                'level': 'Low',
                'reason': 'Small payment amount',
                'mitigation': 'Standard verification'
            }

    def _assess_email_risk(self, details: Dict[str, Any]) -> Dict[str, Any]:
        """Assess risk for email actions"""
        to_address = details.get('to', '')

        if '@' in to_address:
            domain = to_address.split('@')[1].lower()
            if domain not in ['gmail.com', 'yahoo.com', 'outlook.com']:
                return {
                    'level': 'Medium',
                    'reason': 'External domain email',
                    'mitigation': 'Verify recipient is authorized'
                }

        return {
            'level': 'Low',
            'reason': 'Standard email',
            'mitigation': 'Review content before approving'
        }

    def _assess_delete_risk(self, details: Dict[str, Any]) -> Dict[str, Any]:
        """Assess risk for file delete actions"""
        files = details.get('files', [])
        permanent = details.get('permanent', False)

        if len(files) > 10:
            risk_level = 'High'
            reason = f'Bulk delete ({len(files)} files)'
        elif permanent:
            risk_level = 'High'
            reason = 'Permanent deletion (no recovery)'
        else:
            risk_level = 'Medium'
            reason = 'Standard file deletion'

        return {
            'level': risk_level,
            'reason': reason,
            'mitigation': 'Verify files are safe to delete'
        }

    def _assess_system_risk(self, details: Dict[str, Any]) -> Dict[str, Any]:
        """Assess risk for system changes"""
        change_type = details.get('change_type', '').lower()

        high_risk_changes = ['configuration', 'security', 'network', 'database']

        if any(risk in change_type for risk in high_risk_changes):
            return {
                'level': 'High',
                'reason': f'Critical system change: {change_type}',
                'mitigation': 'Ensure rollback plan is tested'
            }

        return {
            'level': 'Medium',
            'reason': f'System change: {change_type}',
            'mitigation': 'Review change impact'
        }


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python create_approval_request.py '<json_params>'")
        sys.exit(1)

    run_skill(CreateApprovalRequestSkill, sys.argv[1])