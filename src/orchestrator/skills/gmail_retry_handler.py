#!/usr/bin/env python3
"""
Gmail Retry Handler - Handles rate limiting and network errors for Gmail API calls

This module provides retry logic with exponential backoff for Gmail API operations,
handling rate limits, network failures, and token refresh errors.
"""

import time
import logging
from typing import Callable, Any, Optional
from functools import wraps
from datetime import datetime, timedelta


class GmailRetryHandler:
    """
    Handles retries for Gmail API calls with exponential backoff
    """

    def __init__(self, max_retries: int = 3, base_delay: float = 1.0, max_delay: float = 60.0):
        """
        Initialize retry handler

        Args:
            max_retries: Maximum number of retry attempts
            base_delay: Base delay in seconds for exponential backoff
            max_delay: Maximum delay between retries
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.logger = logging.getLogger('GmailRetryHandler')

        # Rate limit tracking
        self.rate_limit_reset_time: Optional[datetime] = None
        self.consecutive_rate_limits = 0

    def with_retry(self, func: Callable) -> Callable:
        """
        Decorator to add retry logic to Gmail API calls

        Usage:
            @retry_handler.with_retry
            def send_email(...):
                # Gmail API call
        """
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(self.max_retries + 1):
                try:
                    # Check if we're in rate limit cooldown
                    if self.rate_limit_reset_time and datetime.now() < self.rate_limit_reset_time:
                        wait_time = (self.rate_limit_reset_time - datetime.now()).total_seconds()
                        self.logger.warning(f"Rate limit active, waiting {wait_time:.1f}s before retry")
                        time.sleep(wait_time)

                    # Execute the function
                    result = func(*args, **kwargs)

                    # Success - reset rate limit tracking
                    self.consecutive_rate_limits = 0
                    self.rate_limit_reset_time = None

                    return result

                except Exception as e:
                    last_exception = e
                    error_str = str(e).lower()

                    # Check if it's a rate limit error
                    if self._is_rate_limit_error(e, error_str):
                        self._handle_rate_limit(attempt)

                    # Check if it's a network error
                    elif self._is_network_error(e, error_str):
                        self._handle_network_error(attempt)

                    # Check if it's a token refresh error
                    elif self._is_token_error(e, error_str):
                        self._handle_token_error(attempt)

                    # Unknown error - don't retry
                    else:
                        self.logger.error(f"Non-retryable error: {e}")
                        raise

                    # If we've exhausted retries, raise the last exception
                    if attempt >= self.max_retries:
                        self.logger.error(f"Max retries ({self.max_retries}) exceeded")
                        raise last_exception

                    # Calculate exponential backoff delay
                    delay = min(self.base_delay * (2 ** attempt), self.max_delay)
                    self.logger.info(f"Retry attempt {attempt + 1}/{self.max_retries} after {delay:.1f}s")
                    time.sleep(delay)

            # Should never reach here, but just in case
            raise last_exception

        return wrapper

    def _is_rate_limit_error(self, exception: Exception, error_str: str) -> bool:
        """Check if error is a rate limit error"""
        rate_limit_indicators = [
            'rate limit',
            'quota exceeded',
            'too many requests',
            'user rate limit exceeded',
            '429',
            'rateLimitExceeded'
        ]
        return any(indicator in error_str for indicator in rate_limit_indicators)

    def _is_network_error(self, exception: Exception, error_str: str) -> bool:
        """Check if error is a network error"""
        network_indicators = [
            'connection',
            'timeout',
            'network',
            'unreachable',
            'socket',
            'dns',
            'ssl',
            'certificate'
        ]
        return any(indicator in error_str for indicator in network_indicators)

    def _is_token_error(self, exception: Exception, error_str: str) -> bool:
        """Check if error is a token/auth error"""
        token_indicators = [
            'token',
            'unauthorized',
            'authentication',
            'credentials',
            'invalid_grant',
            '401',
            'expired'
        ]
        return any(indicator in error_str for indicator in token_indicators)

    def _handle_rate_limit(self, attempt: int):
        """Handle rate limit errors"""
        self.consecutive_rate_limits += 1

        # Exponential backoff for rate limits
        if self.consecutive_rate_limits > 3:
            # If we're hitting rate limits repeatedly, wait longer
            cooldown = min(300, 60 * (2 ** (self.consecutive_rate_limits - 3)))  # Max 5 minutes
            self.rate_limit_reset_time = datetime.now() + timedelta(seconds=cooldown)
            self.logger.warning(f"Consecutive rate limits: {self.consecutive_rate_limits}, "
                              f"setting cooldown until {self.rate_limit_reset_time}")
        else:
            self.logger.warning(f"Rate limit hit (attempt {attempt + 1})")

    def _handle_network_error(self, attempt: int):
        """Handle network errors"""
        self.logger.warning(f"Network error (attempt {attempt + 1}), will retry")

    def _handle_token_error(self, attempt: int):
        """Handle token/auth errors"""
        self.logger.error(f"Token/auth error (attempt {attempt + 1})")

        # Token errors usually require manual intervention
        if attempt >= 1:
            # After first retry, don't keep trying
            raise RuntimeError(
                "Gmail token expired or invalid. Please re-authenticate by running the Gmail watcher. "
                "Token errors typically require manual intervention."
            )


# Global retry handler instance
gmail_retry_handler = GmailRetryHandler(max_retries=3, base_delay=2.0, max_delay=60.0)


def with_gmail_retry(func: Callable) -> Callable:
    """
    Convenience decorator for Gmail API retry logic

    Usage:
        @with_gmail_retry
        def my_gmail_function():
            # Gmail API call
    """
    return gmail_retry_handler.with_retry(func)


# Example usage in skills:
"""
from gmail_retry_handler import with_gmail_retry

class SendEmailSkill(BaseSkill):
    @with_gmail_retry
    def _send_email_via_gmail(self, ...):
        # Gmail API call here
        service.users().messages().send(...).execute()
"""
