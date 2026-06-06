#!/usr/bin/env python3
"""
Meta API Setup Script

Interactive setup for Facebook and Instagram Graph API authentication.
This script will guide you through getting a long-lived access token.

Prerequisites:
1. Create a Meta app at https://developers.facebook.com/
2. Select "Other" -> "Business" or "Social Media Management" use cases.
3. Add "Facebook Login for Business" and "Instagram Graph API" products.
4. Get your App ID and App Secret.

Usage:
    python scripts/setup_meta_api.py
"""

import sys
import os
import json
from pathlib import Path

# Add src to path so we can import skills
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.orchestrator.skills.meta_api_client import setup_meta_client_from_env

def main():
    """Main setup function"""
    print("=" * 70)
    print("Meta (Facebook + Instagram) API Setup")
    print("=" * 70)
    
    # Load env vars
    from dotenv import load_dotenv
    load_dotenv()
    
    client = setup_meta_client_from_env()
    if not client:
        print("\n✗ Error: META_APP_ID or META_APP_SECRET not found in .env")
        print("Please update your .env file with the credentials from your Meta Developer Portal.")
        sys.exit(1)
        
    print(f"✓ Found App ID: {client.app_id}")
    
    print("\nSTEP 1: Get a Short-Lived User Token")
    print("-" * 70)
    print("1. Go to the Graph API Explorer: https://developers.facebook.com/tools/explorer/")
    print(f"2. Select your App: {client.app_id}")
    print("3. Add the following permissions:")
    print("   - pages_manage_posts")
    print("   - pages_read_engagement")
    print("   - instagram_basic")
    print("   - instagram_content_publish")
    print("   - pages_show_list")
    print("4. Click 'Generate Access Token'")
    print("5. Copy the 'User Access Token' shown in the input field.")
    
    short_token = input("\nEnter your Short-Lived User Access Token: ").strip()
    if not short_token:
        print("✗ Error: Token is required.")
        sys.exit(1)
        
    print("\nSTEP 2: Exchange for Long-Lived Token")
    print("-" * 70)
    result = client.get_long_lived_token(short_token)
    
    if not result.get('success'):
        print(f"✗ Token exchange failed: {result.get('error')}")
        sys.exit(1)
        
    print("✓ Success! Long-lived token (60 days) saved to credentials/meta_api_token.json")
    
    print("\nSTEP 3: Discover Pages and Instagram Accounts")
    print("-" * 70)
    pages = client.get_pages()
    
    if not pages:
        print("✗ No Facebook Pages found for this user.")
        print("Make sure you have granted 'pages_show_list' and 'pages_manage_posts' permissions.")
    else:
        print(f"Found {len(pages)} Facebook Page(s):")
        print("\n| Page Name | Page ID | Instagram Business Account ID |")
        print("|-----------|---------|-----------------------------|")
        
        for page in pages:
            page_id = page['id']
            page_name = page['name']
            page_token = page['access_token']
            
            # Find linked Instagram account
            ig_id = client.get_instagram_business_account(page_id, page_token)
            ig_display = ig_id if ig_id else "None linked"
            
            print(f"| {page_name[:20]} | {page_id} | {ig_display} |")
            
        print("\nACTION REQUIRED:")
        print("Update your .env file with the IDs above to enable posting:")
        print("META_PAGE_ID=<Your Preferred Page ID>")
        print("INSTAGRAM_BUSINESS_ACCOUNT_ID=<Your Instagram ID>")
        
    print("\n" + "=" * 70)
    print("Setup Complete!")
    print("=" * 70)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
