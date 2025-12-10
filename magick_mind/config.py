"""Configuration models for Magick Mind SDK."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class SDKConfig:
    """Configuration for the Magick Mind SDK."""
    
    base_url: str
    """Base URL for the Bifrost API (e.g., https://bifrost.example.com)"""
    
    timeout: float = 30.0
    """Request timeout in seconds"""
    
    max_retries: int = 3
    """Maximum number of retries for failed requests"""
    
    verify_ssl: bool = True
    """Whether to verify SSL certificates"""
    
    def normalized_base_url(self) -> str:
        """Return base URL without trailing slash."""
        return self.base_url.rstrip("/")
