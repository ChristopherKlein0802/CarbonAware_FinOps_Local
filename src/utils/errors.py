"""Lightweight error helper definitions for the dashboard."""

from typing import Optional


class ErrorMessages:
    """Centralised error strings reused across the app."""

    # AWS SSO messages reused by tracker and AWS client modules
    AWS_SSO_EXPIRED = "AWS SSO token expired - run 'aws sso login' to re-authenticate"
    AWS_SSO_FIX = "💡 Fix: aws sso login --profile carbon-finops-sandbox"


class AWSAuthenticationError(RuntimeError):
    """Raised when AWS authentication fails and user action is required."""

    def __init__(self, message: Optional[str] = None):
        super().__init__(message or ErrorMessages.AWS_SSO_EXPIRED)
