"""Path parameters are percent-encoded before they reach a URL."""

from __future__ import annotations

import pytest

from magick_mind.routes import Routes


@pytest.mark.parametrize("segment", [".", ".."])
def test_dot_segments_are_refused(segment: str):
    with pytest.raises(ValueError, match="path segment"):
        Routes.persona_version("p-1", segment)


def test_ids_cannot_splice_query_fragment_or_path():
    hostile = "ms 1?admin=true#frag/../../v1/keys"

    path = Routes.end_user_magickspace_messages(hostile)

    assert path.startswith("/v1/end-user/magickspaces/")
    assert path.endswith("/messages")
    assert "?" not in path and "#" not in path
    assert path.count("/") == 5


def test_plain_ids_are_unchanged():
    assert Routes.magickspace("ms-123") == "/v1/magickspaces/ms-123"
    assert Routes.end_user_artifact("art-1") == "/v1/end-user/artifacts/art-1"
    assert Routes.persona_version("p-1", "v2") == "/v1/persona/p-1/version/v2"
