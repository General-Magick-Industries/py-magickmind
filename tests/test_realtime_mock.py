import asyncio
import sys
from unittest.mock import MagicMock, AsyncMock, patch

import pytest

# Mock dependencies before importing the client if they are not installed or to ensure isolation
sys.modules["centrifuge"] = MagicMock()
sys.modules["centrifuge.exceptions"] = MagicMock()


@pytest.mark.asyncio
async def test_realtime_client_logic():
    print("🧪 Testing RealtimeClient logic with mocks...")

    # Import inside function to allow module-level mocks to take effect first
    # and to avoid "import not at top of file" lint errors
    from magick_mind.realtime.client import RealtimeClient

    # Mock Auth Provider
    mock_auth = MagicMock()
    # Fake JWT with sub field
    fake_token = f"header.{'eyJzdWIiOiAic2VydmljZS0xMjMifQ'}.signature"
    mock_auth.get_token_async = AsyncMock(return_value=fake_token)

    # Initialize Client
    ws_url = "wss://api.bifrost.com/connection/websocket"
    rt = RealtimeClient(auth=mock_auth, ws_url=ws_url)

    # Mock the internal centrifuge client
    rt._client = MagicMock()
    rt._client.get_subscription.return_value = None
    mock_sub = AsyncMock()
    rt._client.new_subscription = MagicMock(return_value=mock_sub)

    print("1. Testing Subscribe RPC...")
    target_user = "user-123"
    await rt.subscribe(target_user)

    # Verify call to new_subscription
    rt._client.new_subscription.assert_called()
    args, kwargs = rt._client.new_subscription.call_args
    assert args[0] == f"personal:{target_user}#service-123"
    print("   ✅ new_subscription called with correct channel")

    print("2. Testing Unsubscribe RPC...")
    mock_sub = AsyncMock()
    rt._client.get_subscription.return_value = mock_sub
    await rt.unsubscribe(target_user)

    rt._client.get_subscription.assert_called_with(
        f"personal:{target_user}#service-123"
    )
    mock_sub.unsubscribe.assert_called_once()
    print("   ✅ Unsubscribe called correctly")

    print("3. Testing Connection Logic (Mocked)...")
    # Reset client to test connect
    rt._client = None

    with patch("magick_mind.realtime.client.Client") as MockCentClient:
        mock_cent_instance = AsyncMock()
        MockCentClient.return_value = mock_cent_instance

        await rt.connect()

        MockCentClient.assert_called_once()
        # Verify get_token passed is a callable
        args, kwargs = MockCentClient.call_args
        assert callable(kwargs["get_token"])
        print("   ✅ Centrifuge Client initialized with get_token callback")

        mock_cent_instance.connect.assert_called_once()
        print("   ✅ Client.connect() called")

    print("\n🎉 All RealtimeClient logic tests passed!")


if __name__ == "__main__":
    try:
        asyncio.run(test_realtime_client_logic())
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
