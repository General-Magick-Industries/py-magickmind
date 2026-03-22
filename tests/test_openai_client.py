"""Tests for MagickMind.openai_client() helper."""

from __future__ import annotations

import sys
from unittest.mock import patch

import pytest
from magick_mind import MagickMind


def test_openai_client_returns_configured_client() -> None:
    """openai_client() returns a pre-configured AsyncOpenAI pointed at the MagickMind API."""
    pytest.importorskip("openai")
    from openai import AsyncOpenAI

    client = MagickMind(
        email="test@test.com",
        password="pass",
        base_url="https://dev-api.magickmind.ai",
    )
    oc = client.openai_client(api_key="test-key-123")
    assert isinstance(oc, AsyncOpenAI)
    assert "dev-api.magickmind.ai" in str(oc.base_url)
    assert oc.api_key == "test-key-123"


def test_openai_client_raises_without_openai() -> None:
    """openai_client() raises ImportError with install hint when openai is missing."""
    client = MagickMind(
        email="test@test.com",
        password="pass",
        base_url="https://dev-api.magickmind.ai",
    )
    with patch.dict("sys.modules", {"openai": None}):
        with pytest.raises(ImportError, match="pip install magick-mind"):
            client.openai_client(api_key="test-key")


def test_openai_client_base_url_includes_v1() -> None:
    """openai_client() appends /v1 to the base_url for OpenAI SDK compatibility."""
    pytest.importorskip("openai")

    client = MagickMind(
        email="test@test.com",
        password="pass",
        base_url="https://dev-api.magickmind.ai",
    )
    oc = client.openai_client(api_key="test-key-123")
    assert "/v1" in str(oc.base_url)


def test_openai_client_default_compute_power_header() -> None:
    """openai_client() sets X-Compute-Power header to '1' by default."""
    pytest.importorskip("openai")

    client = MagickMind(
        email="test@test.com",
        password="pass",
        base_url="https://dev-api.magickmind.ai",
    )
    oc = client.openai_client(api_key="test-key-123")
    assert oc.default_headers.get("X-Compute-Power") == "1"


def test_openai_client_custom_compute_power() -> None:
    """openai_client() passes custom compute_power as X-Compute-Power header."""
    pytest.importorskip("openai")

    client = MagickMind(
        email="test@test.com",
        password="pass",
        base_url="https://dev-api.magickmind.ai",
    )
    oc = client.openai_client(api_key="test-key-123", compute_power=3)
    assert oc.default_headers.get("X-Compute-Power") == "3"
