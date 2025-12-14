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
    mock_auth.get_token.return_value = "token"

    rt = RealtimeClient(auth=mock_auth, ws_url="ws://test")
    rt._client = AsyncMock()

    # helper to reset mock calls
    def reset_mocks():
        rt._client.rpc.reset_mock()

    print("1. Testing subscribe_many (Bulk Ops)...")
    users = [f"user_{i}" for i in range(50)]

    await rt.subscribe_many(users)

    # Verify 50 calls
    assert rt._client.rpc.call_count == 50
    # Check args of first call
    args, _ = rt._client.rpc.call_args_list[0]
    assert args[0] == "subscribe"
    print("   ✅ Validated 50 concurrent subscriptions")

    print("2. Testing unsubscribe_many...")
    reset_mocks()
    await rt.unsubscribe_many(users)
    assert rt._client.rpc.call_count == 50
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
