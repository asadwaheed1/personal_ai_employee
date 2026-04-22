"""
Main entry point for running the LinkedIn Watcher (API Version)
"""

import sys
from pathlib import Path

# Add parent directory to path to import base_watcher
sys.path.insert(0, str(Path(__file__).parent))

from linkedin_watcher import LinkedInWatcher


def main():
    """Main entry point with environment variable support"""
    import os
    from dotenv import load_dotenv

    # Load environment variables from .env file
    env_path = Path(__file__).parent.parent.parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)

    # Get configuration from environment
    vault_path = os.getenv('VAULT_PATH', './ai_employee_vault')
    check_interval = int(os.getenv('LINKEDIN_CHECK_INTERVAL', '3600'))

    # Allow command line overrides
    if len(sys.argv) > 1:
        vault_path = sys.argv[1]
    if len(sys.argv) > 2:
        check_interval = int(sys.argv[2])

    vault_path = Path(vault_path)
    if not vault_path.exists():
        print(f'Error: Vault path does not exist: {vault_path}')
        sys.exit(1)

    print('=' * 70)
    print('LinkedIn Watcher (API Version)')
    print('=' * 70)
    print(f'Vault: {vault_path}')
    print(f'Check interval: {check_interval}s ({check_interval//60} minutes)')
    print('\nThis version uses the official LinkedIn API v2.')
    print('Make sure you have authenticated using:')
    print('  python scripts/setup_linkedin_api.py')
    print('=' * 70 + '\n')

    try:
        watcher = LinkedInWatcher(
            str(vault_path),
            check_interval
        )
        watcher.run()
    except KeyboardInterrupt:
        print('\n\nLinkedIn Watcher stopped by user')
    except Exception as e:
        print(f'\n\nLinkedIn Watcher error: {e}')
        raise


if __name__ == '__main__':
    main()
