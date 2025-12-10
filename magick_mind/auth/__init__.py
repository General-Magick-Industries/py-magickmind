"""Authentication module for Magick Mind SDK."""

from .base import AuthProvider
from .email_password import EmailPasswordAuth

__all__ = [
    "AuthProvider",
    "EmailPasswordAuth",
]

