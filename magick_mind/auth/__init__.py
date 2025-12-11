"""Authentication module for Magick Mind SDK."""

from magick_mind.auth.base import AuthProvider
from magick_mind.auth.email_password import EmailPasswordAuth

__all__ = [
    "AuthProvider",
    "EmailPasswordAuth",
]
