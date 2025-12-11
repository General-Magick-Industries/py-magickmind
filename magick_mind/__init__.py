"""
Magick Mind SDK - Python client for Bifrost Magick Mind AI platform.

Simple, powerful SDK for authentication and interaction with the Magick Mind API.
"""

from magick_mind.client import MagickMind
from magick_mind.exceptions import (
    MagickMindError,
    AuthenticationError,
    APIError,
    TokenExpiredError,
)

__version__ = "0.0.1"
__all__ = [
    "MagickMind",
    "MagickMindError",
    "AuthenticationError",
    "APIError",
    "TokenExpiredError",
]
