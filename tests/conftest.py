"""Pytest configuration and fixtures."""

import pytest


@pytest.fixture
def base_url():
    """Base URL for testing."""
    return "https://test-bifrost.example.com"


@pytest.fixture
def test_credentials():
    """Test credentials."""
    return {
        "email": "test@example.com",
        "password": "testpass123"
    }
