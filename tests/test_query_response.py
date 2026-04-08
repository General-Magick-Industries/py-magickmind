"""Smoke tests for structured query response models."""

from __future__ import annotations

from magick_mind.models.v1.corpus import (
    Entity,
    QueryCorpusResponse,
    QueryMetadata,
)


def test_query_response_with_all_fields():
    """Full structured response deserializes correctly."""
    data = {
        "result": '{"status": "success"}',
        "entities": [
            {
                "name": "AI",
                "type": "concept",
                "description": "Artificial Intelligence",
                "score": 0.95,
            }
        ],
        "relationships": [
            {
                "source": "AI",
                "target": "ML",
                "relationship": "includes",
                "description": "AI includes ML",
                "score": 0.8,
            }
        ],
        "chunks": [
            {"content": "AI is transformative", "source_id": "doc-1", "score": 0.9}
        ],
        "references": [{"source_id": "doc-1", "content": "Full document text"}],
        "metadata": {
            "query_mode": "hybrid",
            "high_level_keywords": ["artificial intelligence"],
            "low_level_keywords": ["neural networks"],
        },
        "llm_response": "AI is a broad field of study.",
    }
    resp = QueryCorpusResponse(**data)

    assert resp.result == '{"status": "success"}'
    assert len(resp.entities) == 1
    assert resp.entities[0].name == "AI"
    assert resp.entities[0].score == 0.95
    assert len(resp.relationships) == 1
    assert resp.relationships[0].source == "AI"
    assert len(resp.chunks) == 1
    assert resp.chunks[0].content == "AI is transformative"
    assert len(resp.references) == 1
    assert resp.metadata is not None
    assert resp.metadata.query_mode == "hybrid"
    assert resp.metadata.high_level_keywords == ["artificial intelligence"]
    assert resp.llm_response == "AI is a broad field of study."


def test_query_response_backward_compat_result_only():
    """Old server response with only result field still works."""
    resp = QueryCorpusResponse.model_validate(
        {"result": '{"status": "success", "data": {}}'}
    )

    assert resp.result == '{"status": "success", "data": {}}'
    assert resp.entities == []
    assert resp.relationships == []
    assert resp.chunks == []
    assert resp.references == []
    assert resp.metadata is None
    assert resp.llm_response == ""


def test_query_response_empty_structured_fields():
    """Response with empty structured fields deserializes correctly."""
    data = {
        "result": "",
        "entities": [],
        "relationships": [],
        "chunks": [],
        "references": [],
        "metadata": {
            "query_mode": "hybrid",
            "high_level_keywords": [],
            "low_level_keywords": [],
        },
        "llm_response": "",
    }
    resp = QueryCorpusResponse(**data)
    assert resp.entities == []
    assert resp.metadata is not None
    assert resp.metadata.query_mode == "hybrid"


def test_entity_model():
    """Entity model validates correctly."""
    entity = Entity(name="Test Entity", type="concept", description="A test", score=0.5)
    assert entity.name == "Test Entity"
    assert entity.score == 0.5


def test_query_metadata_defaults():
    """QueryMetadata has sensible defaults."""
    meta = QueryMetadata()
    assert meta.query_mode == ""
    assert meta.high_level_keywords == []
    assert meta.low_level_keywords == []
