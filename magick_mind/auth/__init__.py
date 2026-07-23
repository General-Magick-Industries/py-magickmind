"""Authentication module for Magick Mind SDK."""

from magick_mind.auth.base import AuthProvider
from magick_mind.auth.email_password import EmailPasswordAuth
from magick_mind.auth.static_token import StaticTokenAuth

__all__ = [
    "AuthProvider",
    "EmailPasswordAuth",
    "StaticTokenAuth",
]
