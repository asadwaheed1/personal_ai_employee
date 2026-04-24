#!/usr/bin/env python3
"""
Health Check - Checks connectivity and authentication for external services
Used for Gold Tier 1.4: Error Recovery & Graceful Degradation Hardening
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime
import subprocess

def check_gmail_mcp(vault_path):
    """Check Gmail MCP connectivity via orchestrator's mcp_processor"""
    sys.path.append(str(Path(__file__).parent.parent))
    from src.orchestrator.mcp_processor import MCPProcessor
    
    processor = MCPProcessor(str(vault_path))
    result = processor.validate_gmail_mcp_auth()
    
    return {
        'status': 'healthy' if result.get('success') else 'unhealthy',
        'details': result.get('output', result.get('error', 'Unknown error')) if not result.get('success') else 'Authenticated'
    }

def check_linkedin_api(vault_path):
    """Check LinkedIn API connectivity"""
    sys.path.append(str(Path(__file__).parent.parent))
    from src.orchestrator.skills.linkedin_api_client import LinkedInAPIClient
    
    client_id = os.getenv('LINKEDIN_CLIENT_ID')
    client_secret = os.getenv('LINKEDIN_CLIENT_SECRET')
    token_path = os.getenv('LINKEDIN_TOKEN_PATH', './credentials/linkedin_api_token.json')
    
    if not client_id or not client_secret:
        return {'status': 'unconfigured', 'details': 'Missing credentials'}
        
    try:
        client = LinkedInAPIClient(client_id, client_secret, '', token_path)
        if client.is_authenticated():
            user_id = client.get_user_id()
            if user_id:
                return {'status': 'healthy', 'details': f'Authenticated as {user_id}'}
        return {'status': 'unhealthy', 'details': 'Authentication failed'}
    except Exception as e:
        return {'status': 'unhealthy', 'details': str(e)}

def update_dashboard_health(vault_path, health_results):
    """Update Dashboard.md with health status"""
    dashboard_path = Path(vault_path) / 'Dashboard.md'
    if not dashboard_path.exists():
        return
        
    content = dashboard_path.read_text()
    
    health_section = "\n## System Health\n\n"
    health_section += f"**Last Checked**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    health_section += "| Service | Status | Details |\n"
    health_section += "|---------|--------|---------|\n"
    
    for service, result in health_results.items():
        icon = "🟢" if result['status'] == 'healthy' else "🔴" if result['status'] == 'unhealthy' else "⚪"
        health_section += f"| {service} | {icon} {result['status']} | {result['details']} |\n"
    
    if "## System Health" in content:
        import re
        content = re.sub(
            r'## System Health.*?(?=## |$)',
            health_section,
            content,
            flags=re.DOTALL
        )
    else:
        # Find a good spot to insert - maybe after status or before recent activity
        if "## Recent Activity" in content:
            content = content.replace("## Recent Activity", health_section + "\n## Recent Activity")
        else:
            content += health_section
            
    dashboard_path.write_text(content)

def main():
    if len(sys.argv) < 2:
        print("Usage: python health_check.py <vault_path>")
        sys.exit(1)
        
    vault_path = Path(sys.argv[1])
    
    # Load env for LinkedIn creds
    from dotenv import load_dotenv
    load_dotenv(vault_path.parent / '.env')
    
    print(f"Running health check for vault: {vault_path}")
    
    results = {}
    results['Gmail MCP'] = check_gmail_mcp(vault_path)
    results['LinkedIn API'] = check_linkedin_api(vault_path)
    
    # Log results
    log_dir = vault_path / 'Logs'
    log_dir.mkdir(exist_ok=True)
    health_log = log_dir / 'health_check.json'
    
    log_data = {
        'timestamp': datetime.now().isoformat(),
        'results': results
    }
    
    with open(health_log, 'w') as f:
        json.dump(log_data, f, indent=2)
        
    # Update dashboard
    update_dashboard_health(vault_path, results)
    
    print("Health check complete. Dashboard updated.")
    
    # Exit with non-zero if any unhealthy
    if any(r['status'] == 'unhealthy' for r in results.values()):
        sys.exit(2)
    sys.exit(0)

if __name__ == '__main__':
    main()
