"""
Main entry point for running the LinkedIn Watcher
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

    # Get configuration from environment or command line
    vault_path = os.getenv('VAULT_PATH', './ai_employee_vault')
    username = os.getenv('LINKEDIN_USERNAME')
    password = os.getenv('LINKEDIN_PASSWORD')
    session_path = os.getenv('LINKEDIN_SESSION_PATH', './credentials/linkedin_session')
    check_interval = int(os.getenv('LINKEDIN_CHECK_INTERVAL', '300'))

    # Allow command line overrides
    if len(sys.argv) > 1:
        vault_path = sys.argv[1]
    if len(sys.argv) > 2:
        username = sys.argv[2]
    if len(sys.argv) > 3:
        password = sys.argv[3]
    if len(sys.argv) > 4:
        check_interval = int(sys.argv[4])

    # Validate
    if not username or not password:
        print('Error: LinkedIn credentials not configured')
        print('\nSet via environment variables:')
        print('  LINKEDIN_USERNAME=your_email@example.com')
        print('  LINKEDIN_PASSWORD=your_password')
        print('\nOr pass as arguments:')
        print('  python run_linkedin_watcher.py <vault_path> <username> <password>')
        sys.exit(1)

    vault_path = Path(vault_path)
    if not vault_path.exists():
        print(f'Error: Vault path does not exist: {vault_path}')
        sys.exit(1)

    print(f'Starting LinkedIn Watcher...')
    print(f'Vault: {vault_path}')
    print(f'Session path: {session_path}')
    print(f'Check interval: {check_interval}s')
    print()
    print('First run will require login and may trigger security check.')
    print('Watch for prompts and complete any CAPTCHA if shown.\n')

    try:
        watcher = LinkedInWatcher(
            str(vault_path),
            username,
            password,
            session_path,
            check_interval
        )
        watcher.run()
    except KeyboardInterrupt:
        print('\nLinkedIn Watcher stopped by user')
    except Exception as e:
        print(f'\nLinkedIn Watcher error: {e}')
        raise


if __name__ == '__main__':
    main()
