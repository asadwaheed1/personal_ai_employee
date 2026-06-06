"""
Twitter API Client - Integration for Twitter/X via Tweepy
Used for Gold Tier 2.1: Twitter/X Integration
"""

import os
import tweepy
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List

class TwitterAPIClient:
    """Client for Twitter/X API v2 with OAuth 1.0a and Bearer Token"""

    def __init__(self, api_key: str, api_secret: str, access_token: str, access_token_secret: str, bearer_token: str = None):
        """
        Initialize Twitter API client

        Args:
            api_key: Consumer Key
            api_secret: Consumer Secret
            access_token: Access Token
            access_token_secret: Access Token Secret
            bearer_token: Bearer Token (optional, for some v2 endpoints)
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.access_token = access_token
        self.access_token_secret = access_token_secret
        self.bearer_token = bearer_token

        # Initialize API v2 Client (preferred for posting)
        self.client_v2 = tweepy.Client(
            bearer_token=self.bearer_token,
            consumer_key=self.api_key,
            consumer_secret=self.api_secret,
            access_token=self.access_token,
            access_token_secret=self.access_token_secret,
            wait_on_rate_limit=True
        )

        # Initialize API v1.1 Client (for media upload and some older endpoints)
        auth = tweepy.OAuth1UserHandler(
            self.api_key, self.api_secret, self.access_token, self.access_token_secret
        )
        self.api_v1 = tweepy.API(auth, wait_on_rate_limit=True)

    def post_tweet(self, text: str, media_ids: List[str] = None) -> Dict[str, Any]:
        """
        Post a tweet

        Args:
            text: Tweet content (max 280 chars)
            media_ids: Optional list of media IDs from upload_media()

        Returns:
            Dictionary with result
        """
        try:
            response = self.client_v2.create_tweet(text=text, media_ids=media_ids)
            data = response.data
            return {
                'success': True,
                'tweet_id': data.get('id'),
                'text': data.get('text'),
                'url': f"https://twitter.com/user/status/{data.get('id')}"
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def upload_media(self, filename: str) -> Optional[str]:
        """
        Upload media (image/video) to Twitter

        Args:
            filename: Path to media file

        Returns:
            Media ID string if successful
        """
        try:
            media = self.api_v1.media_upload(filename=filename)
            return media.media_id_string
        except Exception as e:
            print(f"Failed to upload media: {e}")
            return None

    def get_mentions(self, since_id: str = None, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Get mentions for the authenticated user

        Args:
            since_id: Returns results with an ID greater than this
            max_results: Max number of mentions to return

        Returns:
            List of mention objects
        """
        try:
            # First get own user ID if not known
            me = self.client_v2.get_me()
            user_id = me.data.id

            response = self.client_v2.get_users_mentions(
                id=user_id,
                since_id=since_id,
                max_results=max_results,
                tweet_fields=['created_at', 'author_id', 'public_metrics']
            )

            if not response.data:
                return []

            mentions = []
            for tweet in response.data:
                mentions.append({
                    'id': tweet.id,
                    'text': tweet.text,
                    'author_id': tweet.author_id,
                    'created_at': tweet.created_at.isoformat() if tweet.created_at else None,
                    'metrics': tweet.public_metrics
                })
            return mentions
        except Exception as e:
            print(f"Failed to get mentions: {e}")
            return []

    def get_engagement_stats(self) -> Dict[str, Any]:
        """
        Get basic engagement stats for the user

        Returns:
            Dictionary with stats
        """
        try:
            me = self.client_v2.get_me(user_fields=['public_metrics'])
            data = me.data
            return {
                'success': True,
                'username': data.username,
                'followers_count': data.public_metrics.get('followers_count'),
                'following_count': data.public_metrics.get('following_count'),
                'tweet_count': data.public_metrics.get('tweet_count'),
                'listed_count': data.public_metrics.get('listed_count')
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

def setup_twitter_client_from_env() -> Optional[TwitterAPIClient]:
    """Helper to initialize client from environment variables"""
    api_key = os.getenv('TWITTER_API_KEY')
    api_secret = os.getenv('TWITTER_API_SECRET')
    access_token = os.getenv('TWITTER_ACCESS_TOKEN')
    access_token_secret = os.getenv('TWITTER_ACCESS_SECRET')
    bearer_token = os.getenv('TWITTER_BEARER_TOKEN')

    if not all([api_key, api_secret, access_token, access_token_secret]):
        return None

    return TwitterAPIClient(api_key, api_secret, access_token, access_token_secret, bearer_token)
