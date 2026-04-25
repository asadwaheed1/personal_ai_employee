#!/usr/bin/env python3
"""
Agent Skill: Audit Logger
Consolidates and manages structured audit logging for all external actions
Used for Gold Tier 4.2: Comprehensive Audit Logging
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

try:
    from .base_skill import BaseSkill, run_skill
except ImportError:
    from base_skill import BaseSkill, run_skill

class AuditLoggerSkill(BaseSkill):
    """Skill to log structured audit data"""

    def _execute_impl(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Log an audit entry"""
        action_type = params.get('action_type', 'unknown')
        actor = params.get('actor', 'ai_employee')
        platform = params.get('platform', 'system')
        target = params.get('target', 'unknown')
        result = params.get('result', 'success')
        details = params.get('details', {})
        
        audit_entry = {
            "timestamp": datetime.now().isoformat(),
            "action_type": action_type,
            "actor": actor,
            "platform": platform,
            "target": target,
            "approval_status": params.get('approval_status', 'auto'),
            "approved_by": params.get('approved_by', 'system'),
            "result": result,
            "error": params.get('error'),
            "details": details
        }
        
        audit_dir = self.vault_path / 'Logs'
        audit_dir.mkdir(exist_ok=True)
        
        audit_file = audit_dir / f"audit_{datetime.now().strftime('%Y-%m-%d')}.json"
        
        # Read existing or create new list
        logs = []
        if audit_file.exists():
            try:
                logs = json.loads(audit_file.read_text())
            except:
                logs = []
        
        logs.append(audit_entry)
        audit_file.write_text(json.dumps(logs, indent=2))
        
        # Also maintain a master consolidated log with limited retention
        master_log = audit_dir / "audit_master.json"
        master_logs = []
        if master_log.exists():
            try:
                master_logs = json.loads(master_log.read_text())
            except:
                master_logs = []
        
        master_logs.append(audit_entry)
        # Keep last 1000 entries
        if len(master_logs) > 1000:
            master_logs = master_logs[-1000:]
        master_log.write_text(json.dumps(master_logs, indent=2))

        return {
            "success": True,
            "audit_file": str(audit_file),
            "entry": audit_entry
        }

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python audit_logger.py '<json_params>'")
        sys.exit(1)
    run_skill(AuditLoggerSkill, sys.argv[1])
