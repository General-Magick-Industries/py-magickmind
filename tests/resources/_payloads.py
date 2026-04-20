"""Shared payload fixtures for network-level resource tests."""

from __future__ import annotations

BASE_URL = "https://api.test"

MINDSPACE_PAYLOAD = {
    "id": "ms-123",
    "name": "Test Space",
    "type": "PRIVATE",
    "description": "test",
    "project_id": "proj-1",
    "created_by": "user-1",
    "updated_by": "user-1",
    "corpus_ids": [],
    "participant_ids": [],
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z",
}

PROJECT_PAYLOAD = {
    "id": "proj-123",
    "name": "Test Project",
    "description": "test",
    "corpus_ids": [],
    "created_by": "user-1",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z",
}

END_USER_PAYLOAD = {
    "id": "eu-123",
    "name": "John Doe",
    "external_id": "ext-123",
    "tenant_id": "t-1",
    "created_by": None,
    "updated_by": None,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z",
}

HISTORY_PAYLOAD = {
    "data": [
        {
            "id": "msg-1",
            "mindspace_id": "ms-1",
            "content": "Hello",
            "sent_by_user_id": "user-1",
            "create_at": "2024-01-01T00:00:00Z",
            "update_at": "2024-01-01T00:00:00Z",
        }
    ],
    "paging": {
        "cursors": {"after": None, "before": None},
        "has_more": False,
        "has_previous": False,
    },
}

PAGING_EMPTY = {
    "cursors": {"after": None, "before": None},
    "has_more": False,
    "has_previous": False,
}

TRAIT_PAYLOAD = {
    "id": "tr-123",
    "name": "openness",
    "namespace": "SYSTEM",
    "owner_id": None,
    "category": "personality",
    "display_name": "Openness",
    "description": "Openness to experience",
    "type": "NUMERIC",
    "numeric_config": {"min": 0.0, "max": 1.0, "default": 0.5},
    "categorical_config": None,
    "multilabel_config": None,
    "default_lock": None,
    "default_learning_rate": 0.1,
    "supports_dyadic": False,
    "visibility": "PUBLIC",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z",
}

ERROR_ENVELOPE = {
    "error": {
        "type": "https://example.com/not-found",
        "title": "Not Found",
        "status": 404,
        "detail": "Resource not found",
        "request_id": "req-abc123",
    }
}

ERROR_500_ENVELOPE = {
    "error": {
        "type": "https://example.com/internal-error",
        "title": "Internal Server Error",
        "status": 500,
        "detail": "Something went wrong",
        "request_id": "req-def456",
    }
}
