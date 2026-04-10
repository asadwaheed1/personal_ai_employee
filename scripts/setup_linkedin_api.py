#!/usr/bin/env python3
"""
LinkedIn API Setup Script

Interactive setup for LinkedIn OAuth authentication.
This script will guide you through the OAuth flow to get your access tokens.

Prerequisites:
1. Create a LinkedIn app at https://www.linkedin.com/developers/apps
2. Enable "Share on LinkedIn" and "Sign In with LinkedIn using OpenID Connect" products
3. Add http://localhost:8000/callback as an authorized redirect URL
4. Get your Client ID and Client Secret

Usage:
    python setup_linkedin_api.py

After setup, your access token will be saved and you can use the LinkedIn posting skill.
"""

import sys
import os
from pathlib import Path

# Add the skills directory to path
sys.path.insert(0, str(Path(__file__).parent))

from linkedin_api_client import setup_linkedin_auth


def main():
    """Main setup function"""
    print("=" * 70)
    print("LinkedIn API Setup")
    print("=" * 70)
    print("\nThis script will help you authenticate with LinkedIn's official API.")
    print("You'll need your LinkedIn app credentials.\n")
    print("Get them from: https://www.linkedin.com/developers/apps\n")

    # Check if credentials are already in environment
    client_id = os.getenv('LINKEDIN_CLIENT_ID')
    client_secret = os.getenv('LINKEDIN_CLIENT_SECRET')
    redirect_uri = os.getenv('LINKEDIN_REDIRECT_URI', 'http://localhost:8000/callback')

    if client_id and client_id != 'your_client_id_here':
        print(f"✓ Found LINKEDIN_CLIENT_ID in environment")
        use_env = input(f"Use environment value? [Y/n]: ").strip().lower()
        if use_env == 'n':
            client_id = None

    if not client_id:
        client_id = input("\nEnter your LinkedIn Client ID: ").strip()

    if client_secret and client_secret != 'your_client_secret_here':
        print(f"✓ Found LINKEDIN_CLIENT_SECRET in environment")
        use_env = input(f"Use environment value? [Y/n]: ").strip().lower()
        if use_env == 'n':
            client_secret = None

    if not client_secret:
        client_secret = input("Enter your LinkedIn Client Secret: ").strip()

    if not client_id or not client_secret:
        print("\n✗ Error: Client ID and Client Secret are required")
        print("\nPlease get these from your LinkedIn Developer Portal:")
        print("https://www.linkedin.com/developers/apps")
        sys.exit(1)

    print(f"\n✓ Using redirect URI: {redirect_uri}")
    print("\nMake sure this redirect URI is configured in your LinkedIn app settings!")
    print("\n" + "=" * 70)

    # Run authentication
    success = setup_linkedin_auth(client_id, client_secret, redirect_uri)

    if success:
        print("\n" + "=" * 70)
        print("Setup Complete!")
        print("=" * 70)
        print("\nYour LinkedIn API token has been saved.")
        print("\nYou can now:")
        print("  1. Run the content calendar to schedule posts")
        print("  2. Create LinkedIn posts through the Pending_Approval workflow")
        print("  3. Test with: python post_linkedin.py '{\"action\": \"check_calendar\"}'")
        print("\nThe token will be automatically refreshed when it expires.")
        print("=" * 70)
    else:
        print("\n✗ Setup failed. Please try again.")
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n✗ Error: {e}")
        sys.exit(1)
