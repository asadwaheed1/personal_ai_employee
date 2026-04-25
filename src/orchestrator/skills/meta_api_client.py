"""
Meta API Client - Integration for Facebook and Instagram via Graph API
Used for Gold Tier 2.2: Facebook + Instagram Integration
"""

import os
import requests
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

class MetaAPIClient:
    """Client for Meta Graph API (Facebook Pages & Instagram Business)"""

    BASE_URL = "https://graph.facebook.com/v21.0"

    def __init__(self, app_id: str, app_secret: str, access_token: Optional[str] = None, token_path: str = './credentials/meta_api_token.json'):
        self.app_id = app_id
        self.app_secret = app_secret
        self.access_token = access_token
        self.token_path = Path(token_path)
        
        if not self.access_token:
            self._load_token()

    def _load_token(self):
        """Load saved token from disk"""
        if self.token_path.exists():
            import json
            try:
                data = json.loads(self.token_path.read_text())
                self.access_token = data.get('access_token')
            except Exception as e:
                logging.error(f"Failed to load Meta token: {e}")

    def _save_token(self, token_data: Dict[str, Any]):
        """Save token to disk"""
        import json
        self.token_path.parent.mkdir(parents=True, exist_ok=True)
        self.token_path.write_text(json.dumps(token_data, indent=2))
        self.access_token = token_data.get('access_token')

    def get_long_lived_token(self, short_lived_token: str) -> Dict[str, Any]:
        """Exchange short-lived token for a long-lived (60 day) user token"""
        url = f"{self.BASE_URL}/oauth/access_token"
        params = {
            'grant_type': 'fb_exchange_token',
            'client_id': self.app_id,
            'client_secret': self.app_secret,
            'fb_exchange_token': short_lived_token
        }
        
        response = requests.get(url, params=params)
        data = response.json()
        
        if 'access_token' in data:
            self._save_token(data)
            return {'success': True, 'data': data}
        return {'success': False, 'error': data.get('error', 'Unknown error')}

    def get_pages(self) -> List[Dict[str, Any]]:
        """Get list of Facebook Pages managed by the user"""
        url = f"{self.BASE_URL}/me/accounts"
        params = {'access_token': self.access_token}
        
        response = requests.get(url, params=params)
        data = response.json()
        
        if 'data' in data:
            return data['data']
        return []

    def post_to_facebook_page(self, page_id: str, page_access_token: str, message: str, link: Optional[str] = None) -> Dict[str, Any]:
        """Post a status update to a Facebook Page"""
        url = f"{self.BASE_URL}/{page_id}/feed"
        params = {
            'message': message,
            'access_token': page_access_token
        }
        if link:
            params['link'] = link
            
        response = requests.post(url, params=params)
        data = response.json()
        
        if 'id' in data:
            return {'success': True, 'post_id': data['id']}
        return {'success': False, 'error': data.get('error', 'Unknown error')}

    def get_instagram_business_account(self, page_id: str, page_access_token: str) -> Optional[str]:
        """Get the Instagram Business Account ID linked to a Facebook Page"""
        url = f"{self.BASE_URL}/{page_id}"
        params = {
            'fields': 'instagram_business_account',
            'access_token': page_access_token
        }
        
        response = requests.get(url, params=params)
        data = response.json()
        
        if 'instagram_business_account' in data:
            return data['instagram_business_account']['id']
        return None

    def post_to_instagram(self, ig_user_id: str, access_token: str, caption: str, image_url: str) -> Dict[str, Any]:
        """Post a photo to Instagram Business account (requires public URL for image)"""
        # 1. Create Media Container
        container_url = f"{self.BASE_URL}/{ig_user_id}/media"
        container_params = {
            'image_url': image_url,
            'caption': caption,
            'access_token': access_token
        }
        
        response = requests.post(container_url, params=container_params)
        container_data = response.json()
        
        if 'id' not in container_data:
            return {'success': False, 'error': container_data.get('error', 'Container creation failed')}
            
        creation_id = container_data['id']
        
        # 2. Publish Media
        publish_url = f"{self.BASE_URL}/{ig_user_id}/media_publish"
        publish_params = {
            'creation_id': creation_id,
            'access_token': access_token
        }
        
        response = requests.post(publish_url, params=publish_params)
        publish_data = response.json()
        
        if 'id' in publish_data:
            return {'success': True, 'ig_post_id': publish_data['id']}
        return {'success': False, 'error': publish_data.get('error', 'Publishing failed')}

    def get_page_insights(self, page_id: str, page_access_token: str) -> Dict[str, Any]:
        """Get engagement metrics for a Facebook Page"""
        url = f"{self.BASE_URL}/{page_id}/insights"
        params = {
            'metric': 'page_posts_impressions,page_post_engagements',
            'period': 'day',
            'access_token': page_access_token
        }
        
        response = requests.get(url, params=params)
        return response.json()

def setup_meta_client_from_env() -> Optional[MetaAPIClient]:
    """Helper to initialize client from environment variables"""
    app_id = os.getenv('META_APP_ID')
    app_secret = os.getenv('META_APP_SECRET')
    
    if not all([app_id, app_secret]):
        return None
        
    return MetaAPIClient(app_id, app_secret)

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python meta_api_client.py <short_lived_token>")
        sys.exit(1)
        
    from dotenv import load_dotenv
    load_dotenv()
    
    client = setup_meta_client_from_env()
    if client:
        result = client.get_long_lived_token(sys.argv[1])
        print(f"Token Exchange Result: {result}")
    else:
        print("Meta credentials not found in .env")
