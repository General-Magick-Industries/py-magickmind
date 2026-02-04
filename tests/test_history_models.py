"""Tests for history models."""

from magick_mind.models.v1.history import ChatHistoryMessage, HistoryResponse
from magick_mind.models.common import Cursors, PageInfo


class TestChatHistoryMessage:
    """Tests for ChatHistoryMessage model."""

    def test_valid_message(self):
        """Test creating a valid chat history message."""
        message = ChatHistoryMessage(
            id="msg-123",
            mindspace_id="mind-456",
            sent_by_user_id="user-789",
            content="Hello, world!",
            reply_to_message_id="msg-100",
            status="sent",
            create_at="2024-01-01T10:00:00Z",
            update_at="2024-01-01T10:00:00Z",
        )

        assert message.id == "msg-123"
        assert message.mindspace_id == "mind-456"
        assert message.sent_by_user_id == "user-789"
        assert message.content == "Hello, world!"
        assert message.reply_to_message_id == "msg-100"
        assert message.status == "sent"
        assert message.created_at == "2024-01-01T10:00:00Z"
        assert message.updated_at == "2024-01-01T10:00:00Z"

    def test_message_without_reply_to(self):
        """Test message without reply_to_message_id."""
        message = ChatHistoryMessage(
            id="msg-123",
            mindspace_id="mind-456",
            sent_by_user_id="user-789",
            content="Hello!",
            status="sent",
            create_at="2024-01-01T10:00:00Z",
            update_at="2024-01-01T10:00:00Z",
        )

        assert message.reply_to_message_id is None

    def test_field_aliases(self):
        """Test that both create_at/created_at and update_at/updated_at work."""
        # Using aliased names
        message1 = ChatHistoryMessage(
            id="msg-1",
            mindspace_id="mind-1",
            sent_by_user_id="user-1",
            content="Test",
            status="sent",
            create_at="2024-01-01T10:00:00Z",
            update_at="2024-01-01T10:00:00Z",
        )

        # Using field names
        message2 = ChatHistoryMessage(
            id="msg-2",
            mindspace_id="mind-2",
            sent_by_user_id="user-2",
            content="Test",
            status="sent",
            created_at="2024-01-01T10:00:00Z",
            updated_at="2024-01-01T10:00:00Z",
        )

        assert message1.created_at == message2.created_at
        assert message1.updated_at == message2.updated_at

    def test_missing_required_fields(self):
        """Test that ChatHistoryMessage accepts relaxed optional fields."""
        # With relaxed spec, all fields are Optional
        message = ChatHistoryMessage(id="msg-123")
        assert message.id == "msg-123"
        assert message.mindspace_id is None
        assert message.content is None


class TestHistoryResponse:
    """Tests for HistoryResponse model with standardized {data, paging} structure."""

    def test_empty_response(self):
        """Test creating an empty history response."""
        response = HistoryResponse()

        # Test new structure
        assert response.data == []
        assert response.paging.has_more is False
        assert response.paging.has_previous is False
        assert response.paging.cursors.after is None
        assert response.paging.cursors.before is None

        # Test backward compatibility properties
        assert response.chat_histories == []
        assert response.has_more is False
        assert response.has_older is False
        assert response.next_after_id is None
        assert response.next_before_id is None

    def test_latest_mode_response(self):
        """Test response for latest mode."""
        msg = ChatHistoryMessage(
            id="msg-1",
            mindspace_id="mind-1",
            sent_by_user_id="user-1",
            content="Hello",
            status="sent",
            create_at="2024-01-01T10:00:00Z",
            update_at="2024-01-01T10:00:00Z",
        )
        response = HistoryResponse(
            data=[msg],
            paging=PageInfo(
                cursors=Cursors(after=None, before=None),
                has_more=False,
                has_previous=False,
            ),
        )

        assert len(response.data) == 1
        assert response.paging.has_more is False

        # Backward compat
        assert len(response.chat_histories) == 1
        assert response.next_after_id is None
        assert response.next_before_id is None

    def test_forward_pagination_response(self):
        """Test response for forward pagination with has_more and after cursor."""
        msg = ChatHistoryMessage(
            id="msg-2",
            mindspace_id="mind-1",
            sent_by_user_id="user-1",
            content="World",
            status="sent",
            create_at="2024-01-01T10:01:00Z",
            update_at="2024-01-01T10:01:00Z",
        )
        response = HistoryResponse(
            data=[msg],
            paging=PageInfo(
                cursors=Cursors(after="msg-2", before=None),
                has_more=True,
                has_previous=False,
            ),
        )

        assert len(response.data) == 1
        assert response.paging.cursors.after == "msg-2"
        assert response.paging.has_more is True

        # Backward compat
        assert len(response.chat_histories) == 1
        assert response.next_after_id == "msg-2"
        assert response.has_more is True

    def test_backward_pagination_response(self):
        """Test response for backward pagination with has_previous and before cursor."""
        msg = ChatHistoryMessage(
            id="msg-0",
            mindspace_id="mind-1",
            sent_by_user_id="user-1",
            content="First",
            status="sent",
            create_at="2024-01-01T09:59:00Z",
            update_at="2024-01-01T09:59:00Z",
        )
        response = HistoryResponse(
            data=[msg],
            paging=PageInfo(
                cursors=Cursors(after=None, before="msg-0"),
                has_more=False,
                has_previous=True,
            ),
        )

        assert len(response.data) == 1
        assert response.paging.cursors.before == "msg-0"
        assert response.paging.has_previous is True

        # Backward compat
        assert len(response.chat_histories) == 1
        assert response.next_before_id == "msg-0"
        assert response.has_older is True

    def test_multiple_messages(self):
        """Test response with multiple messages."""
        messages = [
            ChatHistoryMessage(
                id=f"msg-{i}",
                mindspace_id="mind-1",
                sent_by_user_id="user-1",
                content=f"Message {i}",
                status="sent",
                create_at=f"2024-01-01T10:0{i}:00Z",
                update_at=f"2024-01-01T10:0{i}:00Z",
            )
            for i in range(3)
        ]

        response = HistoryResponse(
            data=messages,
            paging=PageInfo(
                cursors=Cursors(after="msg-2", before=None),
                has_more=True,
                has_previous=False,
            ),
        )

        assert len(response.data) == 3
        assert response.data[0].id == "msg-0"
        assert response.data[2].id == "msg-2"

        # Backward compat
        assert len(response.chat_histories) == 3
        assert response.chat_histories[0].id == "msg-0"
        assert response.chat_histories[2].id == "msg-2"
