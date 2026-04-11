"""
LinkedIn API Client - Official API integration for LinkedIn

Uses LinkedIn OAuth 2.0 and API v2 for:
- Authentication via OpenID Connect
- Posting to LinkedIn (Share API)
- User profile information

Note: LinkedIn Messaging API requires special partnership access.
For message monitoring, consider using webhooks or keep the Play watcher as fallback.

Documentation:
- https://learn.microsoft.com/en-us/linkedin/shared/authentication/authorization-code-flow
- https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/posts-api
"""

import json
import base64
import hashlib
import secrets
import requests
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from urllib.parse import urlencode, parse_qs, urlparse


class LinkedInAPIClient:
    """Client for LinkedIn API v2 with OAuth 2.0 authentication"""

    # OAuth endpoints
    AUTHORIZATION_URL = "https://www.linkedin.com/oauth/v2/authorization"
    TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"

    # API endpoints
    API_BASE_URL = "https://api.linkedin.com/v2"
    POSTS_ENDPOINT = f"{API_BASE_URL}/posts"
    UGC_POSTS_ENDPOINT = f"{API_BASE_URL}/ugcPosts"
    ME_ENDPOINT = f"{API_BASE_URL}/me"
    USERINFO_ENDPOINT = "https://api.linkedin.com/v2/userinfo"

    # Scopes needed
    SCOPES = [
        "openid",
        "profile",
        "w_member_social"  # Required for posting
    ]

    def __init__(self, client_id: str, client_secret: str, redirect_uri: str,
                 token_path: str = "./credentials/linkedin_api_token.json"):
        """
        Initialize LinkedIn API client

        Args:
            client_id: LinkedIn App Client ID
            client_secret: LinkedIn App Client Secret
            redirect_uri: OAuth redirect URI (must match LinkedIn app settings)
            token_path: Path to store/retrieve access tokens
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.token_path = Path(token_path)

        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.token_expires_at: Optional[datetime] = None
        self.user_info: Optional[Dict[str, Any]] = None

        # Try to load existing token
        self._load_token()

    def _load_token(self) -> bool:
        """Load token from file if it exists"""
        if not self.token_path.exists():
            return False

        try:
            data = json.loads(self.token_path.read_text())
            self.access_token = data.get('access_token')
            self.refresh_token = data.get('refresh_token')

            expires_at = data.get('expires_at')
            if expires_at:
                self.token_expires_at = datetime.fromisoformat(expires_at)

            user_info = data.get('user_info')
            if user_info:
                self.user_info = user_info

            # Check if token is still valid (with 5 minute buffer)
            if self.token_expires_at and datetime.now() < self.token_expires_at - timedelta(minutes=5):
                return True
            elif self.refresh_token:
                # Try to refresh
                return self._refresh_access_token()

            return False
        except Exception as e:
            print(f"Error loading token: {e}")
            return False

    def _save_token(self):
        """Save token to file"""
        self.token_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            'access_token': self.access_token,
            'refresh_token': self.refresh_token,
            'expires_at': self.token_expires_at.isoformat() if self.token_expires_at else None,
            'user_info': self.user_info,
            'saved_at': datetime.now().isoformat()
        }

        self.token_path.write_text(json.dumps(data, indent=2))

    def get_authorization_url(self, state: Optional[str] = None) -> tuple[str, str]:
        """
        Generate OAuth authorization URL and PKCE verifier

        Returns:
            Tuple of (authorization_url, code_verifier) - save code_verifier for token exchange
        """
        # Generate PKCE parameters
        code_verifier = secrets.token_urlsafe(64)
        code_challenge = base64.urlsafe_b64encode(
            hashlib.sha256(code_verifier.encode()).digest()
        ).decode().rstrip('=')

        if not state:
            state = secrets.token_urlsafe(32)

        params = {
            'response_type': 'code',
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'scope': ' '.join(self.SCOPES),
            'state': state,
            'code_challenge': code_challenge,
            'code_challenge_method': 'S256'
        }

        auth_url = f"{self.AUTHORIZATION_URL}?{urlencode(params)}"

        return auth_url, code_verifier

    def exchange_code_for_token(self, authorization_code: str, code_verifier: Optional[str] = None) -> bool:
        """
        Exchange authorization code for access token

        Args:
            authorization_code: Code from OAuth callback
            code_verifier: Optional PKCE verifier from get_authorization_url()

        Returns:
            True if successful, False otherwise
        """
        base_data = {
            'grant_type': 'authorization_code',
            'code': authorization_code,
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'redirect_uri': self.redirect_uri,
        }

        data = dict(base_data)
        if code_verifier:
            data['code_verifier'] = code_verifier

        try:
            response = requests.post(self.TOKEN_URL, data=data, timeout=30)

            if response.status_code >= 400 and code_verifier:
                retry_data = dict(base_data)
                retry_response = requests.post(self.TOKEN_URL, data=retry_data, timeout=30)
                retry_response.raise_for_status()
                response = retry_response
            else:
                response.raise_for_status()

            token_data = response.json()

            self.access_token = token_data.get('access_token')
            self.refresh_token = token_data.get('refresh_token')

            expires_in = token_data.get('expires_in', 3600)
            self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)

            # Get user info
            self._fetch_user_info()

            # Save token
            self._save_token()

            return True

        except Exception as e:
            print(f"Token exchange failed: {e}")
            return False

    def _refresh_access_token(self) -> bool:
        """Refresh access token using refresh token"""
        if not self.refresh_token:
            return False

        data = {
            'grant_type': 'refresh_token',
            'refresh_token': self.refresh_token,
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }

        try:
            response = requests.post(self.TOKEN_URL, data=data, timeout=30)
            response.raise_for_status()

            token_data = response.json()

            self.access_token = token_data.get('access_token')
            if 'refresh_token' in token_data:
                self.refresh_token = token_data['refresh_token']

            expires_in = token_data.get('expires_in', 3600)
            self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)

            self._save_token()
            return True

        except Exception as e:
            print(f"Token refresh failed: {e}")
            return False

    def _fetch_user_info(self) -> Optional[Dict[str, Any]]:
        """Fetch user info from LinkedIn"""
        if not self.access_token:
            return None

        try:
            headers = {'Authorization': f'Bearer {self.access_token}'}
            response = requests.get(self.USERINFO_ENDPOINT, headers=headers, timeout=30)
            response.raise_for_status()

            self.user_info = response.json()
            return self.user_info

        except Exception as e:
            print(f"Failed to fetch user info: {e}")
            return None

    def is_authenticated(self) -> bool:
        """Check if client has valid authentication"""
        if not self.access_token:
            self._load_token()

        if not self.access_token:
            return False

        # Check expiration
        if self.token_expires_at and datetime.now() >= self.token_expires_at:
            # Try refresh
            return self._refresh_access_token()

        return True

    def get_user_id(self) -> Optional[str]:
        """Get LinkedIn user ID (sub claim from userinfo)"""
        if not self.user_info:
            self._fetch_user_info()

        return self.user_info.get('sub') if self.user_info else None

    def create_text_share(self, text: str, visibility: str = "PUBLIC") -> Dict[str, Any]:
        """
        Create a text-only share (post) on LinkedIn

        Args:
            text: Post content (max 3000 characters for shares)
            visibility: PUBLIC or CONNECTIONS

        Returns:
            API response with post details
        """
        if not self.is_authenticated():
            raise RuntimeError("Not authenticated. Call authenticate() first.")

        user_id = self.get_user_id()
        if not user_id:
            raise RuntimeError("Could not get user ID")

        # LinkedIn Share API v2 payload
        payload = {
            "author": f"urn:li:person:{user_id}",
            "lifecycleState": "PUBLISHED",
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": visibility
            },
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {
                        "text": text
                    },
                    "shareMediaCategory": "NONE"
                }
            }
        }

        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json',
            'X-Restli-Protocol-Version': '2.0.0'
        }

        try:
            response = requests.post(
                self.UGC_POSTS_ENDPOINT,
                headers=headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()

            result = response.json()
            return {
                'success': True,
                'post_id': result.get('id'),
                'message': 'Post created successfully',
                'url': f"https://www.linkedin.com/feed/update/{result.get('id', '').replace('urn:li:share:', '')}"
            }

        except requests.exceptions.HTTPError as e:
            error_detail = ""
            try:
                error_detail = response.json()
            except:
                pass

            return {
                'success': False,
                'error': str(e),
                'details': error_detail,
                'message': f'Failed to create post: {e}'
            }

    def create_post_with_url(self, text: str, url: str, title: str = None,
                             description: str = None, visibility: str = "PUBLIC") -> Dict[str, Any]:
        """
        Create a share with a URL (article link)

        Args:
            text: Post commentary text
            url: URL to share
            title: Optional title for the link
            description: Optional description for the link
            visibility: PUBLIC or CONNECTIONS

        Returns:
            API response with post details
        """
        if not self.is_authenticated():
            raise RuntimeError("Not authenticated")

        user_id = self.get_user_id()
        if not user_id:
            raise RuntimeError("Could not get user ID")

        # Build media content for URL sharing
        media_content = {
            "status": "READY",
            "originalUrl": url,
            "title": {"text": title or url}
        }

        if description:
            media_content["description"] = {"text": description}

        payload = {
            "author": f"urn:li:person:{user_id}",
            "lifecycleState": "PUBLISHED",
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": visibility
            },
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {
                        "text": text
                    },
                    "shareMediaCategory": "ARTICLE",
                    "media": [media_content]
                }
            }
        }

        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json',
            'X-Restli-Protocol-Version': '2.0.0'
        }

        try:
            response = requests.post(
                self.UGC_POSTS_ENDPOINT,
                headers=headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()

            result = response.json()
            return {
                'success': True,
                'post_id': result.get('id'),
                'message': 'Post with URL created successfully',
                'url': f"https://www.linkedin.com/feed/update/{result.get('id', '').replace('urn:li:share:', '')}"
            }

        except requests.exceptions.HTTPError as e:
            return {
                'success': False,
                'error': str(e),
                'message': f'Failed to create post: {e}'
            }

    def get_post(self, post_id: str) -> Dict[str, Any]:
        """
        Get details of a specific post

        Args:
            post_id: LinkedIn post URN or ID

        Returns:
            Post details
        """
        if not self.is_authenticated():
            raise RuntimeError("Not authenticated")

        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-Restli-Protocol-Version': '2.0.0'
        }

        try:
            response = requests.get(
                f"{self.UGC_POSTS_ENDPOINT}/{post_id}",
                headers=headers,
                timeout=30
            )
            response.raise_for_status()
            return response.json()

        except Exception as e:
            return {'error': str(e)}

    def delete_post(self, post_id: str) -> bool:
        """
        Delete a post

        Args:
            post_id: LinkedIn post URN or ID

        Returns:
            True if deleted successfully
        """
        if not self.is_authenticated():
            raise RuntimeError("Not authenticated")

        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-Restli-Protocol-Version': '2.0.0'
        }

        try:
            response = requests.delete(
                f"{self.UGC_POSTS_ENDPOINT}/{post_id}",
                headers=headers,
                timeout=30
            )
            response.raise_for_status()
            return True

        except Exception as e:
            print(f"Failed to delete post: {e}")
            return False

    def _register_image_asset(self, image_path: str) -> Optional[str]:
        """
        Register an image asset with LinkedIn for posting

        Args:
            image_path: Path to image file

        Returns:
            Image URN if successful, None otherwise
        """
        if not self.is_authenticated():
            raise RuntimeError("Not authenticated")

        user_id = self.get_user_id()
        if not user_id:
            raise RuntimeError("Could not get user ID")

        # Get image file info
        image_path_obj = Path(image_path)
        if not image_path_obj.exists():
            raise ValueError(f"Image file not found: {image_path}")

        file_size = image_path_obj.stat().st_size
        file_name = image_path_obj.name
        file_extension = image_path_obj.suffix.lower()

        # Validate image
        valid_extensions = ['.png', '.jpg', '.jpeg', '.gif']
        if file_extension not in valid_extensions:
            raise ValueError(f"Invalid image format. Supported: {', '.join(valid_extensions)}")

        # Max 8MB for LinkedIn images
        if file_size > 8 * 1024 * 1024:
            raise ValueError("Image file too large. Maximum size is 8MB")

        # Map extensions to LinkedIn media types
        media_type_map = {
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif'
        }
        media_type = media_type_map.get(file_extension, 'image/jpeg')

        # Step 1: Initialize image upload (register the asset)
        register_endpoint = f"{self.API_BASE_URL}/assets?action=registerUpload"

        payload = {
            "registerUploadRequest": {
                "owner": f"urn:li:person:{user_id}",
                "recipes": [
                    "urn:li:digitalmediaRecipe:feedshare-image"
                ],
                "serviceRelationships": [
                    {
                        "identifier": "urn:li:userGeneratedContent",
                        "relationshipType": "OWNER"
                    }
                ],
                "supportedUploadMechanism": [
                    "SINGLE_REQUEST"
                ]
            }
        }

        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json',
            'X-Restli-Protocol-Version': '2.0.0'
        }

        try:
            # Register the upload
            response = requests.post(
                register_endpoint,
                headers=headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()

            register_data = response.json()
            upload_url = register_data['value']['uploadUrl']
            asset_urn = register_data['value']['asset']

            # Step 2: Upload the image file
            with open(image_path, 'rb') as image_file:
                image_data = image_file.read()

            upload_headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': media_type,
                'media-type-family': 'STILLIMAGE'
            }

            upload_response = requests.put(
                upload_url,
                headers=upload_headers,
                data=image_data,
                timeout=60
            )
            upload_response.raise_for_status()

            return asset_urn

        except Exception as e:
            print(f"Failed to register image asset: {e}")
            return None

    def create_post_with_image(self, text: str, image_path: str,
                                 visibility: str = "PUBLIC") -> Dict[str, Any]:
        """
        Create a post with an image on LinkedIn

        Args:
            text: Post content text
            image_path: Path to image file to attach
            visibility: PUBLIC or CONNECTIONS

        Returns:
            API response with post details
        """
        if not self.is_authenticated():
            raise RuntimeError("Not authenticated. Call authenticate() first.")

        user_id = self.get_user_id()
        if not user_id:
            raise RuntimeError("Could not get user ID")

        # Register the image asset first
        image_urn = self._register_image_asset(image_path)
        if not image_urn:
            return {
                'success': False,
                'error': 'image_upload_failed',
                'message': 'Failed to upload image to LinkedIn'
            }

        # Build the post payload with image
        payload = {
            "author": f"urn:li:person:{user_id}",
            "lifecycleState": "PUBLISHED",
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": visibility
            },
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {
                        "text": text
                    },
                    "shareMediaCategory": "IMAGE",
                    "media": [
                        {
                            "status": "READY",
                            "media": image_urn
                        }
                    ]
                }
            }
        }

        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json',
            'X-Restli-Protocol-Version': '2.0.0'
        }

        try:
            response = requests.post(
                self.UGC_POSTS_ENDPOINT,
                headers=headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()

            result = response.json()
            return {
                'success': True,
                'post_id': result.get('id'),
                'message': 'Post with image created successfully',
                'url': f"https://www.linkedin.com/feed/update/{result.get('id', '').replace('urn:li:share:', '')}"
            }

        except requests.exceptions.HTTPError as e:
            error_detail = ""
            try:
                error_detail = response.json()
            except:
                pass

            return {
                'success': False,
                'error': str(e),
                'details': error_detail,
                'message': f'Failed to create post with image: {e}'
            }


def setup_linkedin_auth(client_id: str, client_secret: str, redirect_uri: str) -> bool:
    """
    Interactive setup for LinkedIn OAuth authentication

    This function will:
    1. Generate an authorization URL
    2. Instruct user to visit URL and authorize
    3. Wait for authorization code
    4. Exchange code for tokens
    5. Save tokens for future use

    Args:
        client_id: LinkedIn App Client ID
        client_secret: LinkedIn App Client Secret
        redirect_uri: OAuth redirect URI (must be HTTPS and match app settings)

    Returns:
        True if authentication successful
    """
    client = LinkedInAPIClient(client_id, client_secret, redirect_uri)

    auth_url, code_verifier = client.get_authorization_url()

    print("=" * 60)
    print("LinkedIn OAuth Setup")
    print("=" * 60)
    print("\n1. Visit this URL in your browser:\n")
    print(auth_url)
    print("\n2. Log in to LinkedIn and authorize the app")
    print("3. After authorization, you'll be redirected to your redirect_uri")
    print("4. Copy the 'code' parameter from the redirect URL")
    print("=" * 60)

    auth_code = input("\nEnter the authorization code: ").strip()

    if not auth_code:
        print("No code provided. Setup cancelled.")
        return False

    print("\nExchanging code for token...")

    if client.exchange_code_for_token(auth_code, code_verifier):
        print("✓ Authentication successful!")
        print(f"User: {client.user_info.get('name', 'Unknown')}")
        print(f"Token saved to: {client.token_path}")
        return True
    else:
        print("✗ Authentication failed")
        return False


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 4:
        print("Usage: python linkedin_api_client.py <client_id> <client_secret> <redirect_uri>")
        print("\nExample:")
        print("  python linkedin_api_client.py 78xxxxxxx1234 https://localhost/callback")
        sys.exit(1)

    setup_linkedin_auth(sys.argv[1], sys.argv[2], sys.argv[3])
