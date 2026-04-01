#!/usr/bin/env python3
"""Daily dashboard update script for cron jobs."""

import sys
import os

# Add the skills directory to the path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(script_dir)
sys.path.insert(0, os.path.join(project_dir, 'src', 'orchestrator', 'skills'))

from update_dashboard import UpdateDashboardSkill

if __name__ == "__main__":
    vault_path = os.path.join(project_dir, 'ai_employee_vault')
    skill = UpdateDashboardSkill(vault_path)
    skill.execute({'summary': 'Morning dashboard update'})
