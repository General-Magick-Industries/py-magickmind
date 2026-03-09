"""Basic smoke tests for SDK structure."""

import pytest
from magick_mind import MagickMind


def test_client_requires_credentials():
    """Test that client requires email and password."""
    with pytest.raises(ValueError, match="Email and password are required"):
        MagickMind(base_url="https://test.com", email="", password="")


def test_client_initialization():
    """Test that client initializes with valid credentials."""
    client = MagickMind(
        base_url="https://test.com", email="test@example.com", password="password123"
    )

    assert client.config.base_url == "https://test.com"
    assert client.config.normalized_base_url() == "https://test.com"


def test_client_repr():
    """Test string representation of client."""
    client = MagickMind(
        base_url="https://test.com", email="test@example.com", password="password123"
    )

    repr_str = repr(client)
    assert "MagickMind" in repr_str
    assert "EmailPassword" in repr_str


def test_client_context_manager():
    """Test client can be used as context manager."""
    with MagickMind(
        base_url="https://test.com", email="test@example.com", password="password123"
    ) as client:
        assert client is not None
