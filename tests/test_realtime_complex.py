import asyncio
import sys
from unittest.mock import MagicMock, AsyncMock

import pytest


@pytest.mark.asyncio
async def test_complex_realtime_scenarios():
    print("🧪 Testing Realtime Scalability & Resilience...")

    # Mock dependencies
    sys.modules["centrifuge"] = MagicMock()
    sys.modules["centrifuge.exceptions"] = MagicMock()

    # Import locally
    from magick_mind.realtime.client import RealtimeClient

    # Setup Mocks
    mock_auth = MagicMock()
    # Fake JWT with sub field
    fake_token = f"header.{'eyJzdWIiOiAic2VydmljZS0xMjMifQ'}.signature"
    mock_auth.get_token_async = AsyncMock(return_value=fake_token)

    rt = RealtimeClient(auth=mock_auth, ws_url="ws://test")
    rt._events = MagicMock()
    rt._client = MagicMock()
    rt._client.get_subscription.return_value = None
    mock_sub = AsyncMock()
    rt._client.new_subscription.return_value = mock_sub

    print("1. Testing subscribe_many (Bulk Ops)...")
    users = [f"user_{i}" for i in range(50)]

    await rt.subscribe_many(users)

    # Verify 50 calls
    assert rt._client.new_subscription.call_count == 50
    # Check args of first call
    args, _ = rt._client.new_subscription.call_args_list[0]
    assert args[0].startswith("personal:user_")
    print("   ✅ Validated 50 concurrent subscriptions")

    print("2. Testing unsubscribe_many...")
    rt._client.get_subscription.reset_mock()
    rt._client.get_subscription.return_value = AsyncMock()
    await rt.unsubscribe_many(users)
    assert rt._client.get_subscription.call_count == 50
    print("   ✅ Validated 50 concurrent unsubscriptions")

    print("\n🎉 All Complex Realtime Tests Passed!")


if __name__ == "__main__":
    try:
        asyncio.run(test_complex_realtime_scenarios())
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
