"""
Main entry point for running the Gmail Watcher
"""

import sys
from pathlib import Path

# Add parent directory to path to import base_watcher
sys.path.insert(0, str(Path(__file__).parent))

from gmail_watcher import GmailWatcher


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
    credentials_path = os.getenv('GMAIL_CREDENTIALS_PATH', './credentials/gmail_credentials.json')
    token_path = os.getenv('GMAIL_TOKEN_PATH', './credentials/gmail_token.json')
    query = os.getenv('GMAIL_QUERY', 'is:unread is:inbox')
    check_interval = int(os.getenv('GMAIL_CHECK_INTERVAL', '120'))

    # Allow command line overrides
    if len(sys.argv) > 1:
        vault_path = sys.argv[1]
    if len(sys.argv) > 2:
        credentials_path = sys.argv[2]
    if len(sys.argv) > 3:
        token_path = sys.argv[3]
    if len(sys.argv) > 4:
        query = sys.argv[4]
    if len(sys.argv) > 5:
        check_interval = int(sys.argv[5])

    # Validate paths
    vault_path = Path(vault_path)
    if not vault_path.exists():
        print(f'Error: Vault path does not exist: {vault_path}')
        sys.exit(1)

    credentials_path = Path(credentials_path)
    if not credentials_path.exists():
        print(f'Error: Gmail credentials not found at: {credentials_path}')
        print('\nTo set up Gmail API:')
        print('1. Go to https://console.cloud.google.com/apis/credentials')
        print('2. Create a new project or select existing one')
        print('3. Enable Gmail API')
        print('4. Create OAuth 2.0 credentials')
        print('5. Download credentials JSON and save to the specified path')
        sys.exit(1)

    print(f'Starting Gmail Watcher...')
    print(f'Vault: {vault_path}')
    print(f'Credentials: {credentials_path}')
    print(f'Token path: {token_path}')
    print(f'Query: {query}')
    print(f'Check interval: {check_interval}s')
    print()
    print('First run will require OAuth authorization.')
    print('A browser window will open for authentication.\n')

    try:
        watcher = GmailWatcher(
            str(vault_path),
            str(credentials_path),
            str(token_path),
            query,
            check_interval
        )
        watcher.run()
    except KeyboardInterrupt:
        print('\nGmail Watcher stopped by user')
    except Exception as e:
        print(f'\nGmail Watcher error: {e}')
        raise


if __name__ == '__main__':
    main()
