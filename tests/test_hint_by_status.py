"""Hints attach once, keep the exception type, and skip credential errors."""

from __future__ import annotations

import pytest

from magick_mind.exceptions import (
    AuthenticationError,
    MagickMindError,
    ProblemDetailsException,
    hint_by_status,
    reraise_with_hint,
)
from magick_mind.models.errors import ProblemDetails


def _problem(status: int) -> ProblemDetailsException:
    return ProblemDetailsException(
        ProblemDetails(type="about:blank", title="Nope", status=status, detail="nope")
    )


class TestReraiseWithHint:
    def test_plain_error_carries_the_hint_once(self):
        with pytest.raises(MagickMindError) as exc:
            reraise_with_hint(MagickMindError("boom", status_code=403), "hint: A")

        assert str(exc.value) == "boom (hint: A)"
        assert exc.value.message == "boom"
        assert exc.value.args == ("boom (hint: A)",)

    def test_second_application_replaces(self):
        error = MagickMindError("boom")
        with pytest.raises(MagickMindError):
            reraise_with_hint(error, "hint: A")
        with pytest.raises(MagickMindError) as exc:
            reraise_with_hint(error, "hint: B")

        assert str(exc.value) == "boom (hint: B)"

    def test_problem_details_keeps_its_fields(self):
        with pytest.raises(ProblemDetailsException) as exc:
            reraise_with_hint(_problem(404), "hint: look elsewhere")

        assert exc.value.status == 404
        assert str(exc.value).count("hint:") == 1


class TestHintByStatus:
    def test_hints_matching_status(self):
        with pytest.raises(ProblemDetailsException) as exc:
            hint_by_status(_problem(401), {401: "hint: use the other route"})
        assert exc.value.hint == "hint: use the other route"

    def test_reraises_unmatched_status_untouched(self):
        with pytest.raises(ProblemDetailsException) as exc:
            hint_by_status(_problem(500), {401: "hint: x"})
        assert exc.value.hint is None

    def test_credential_errors_pass_through(self):
        """A 401 from token rotation is about the credential, not the route."""
        with pytest.raises(AuthenticationError) as exc:
            hint_by_status(
                AuthenticationError("token rejected", status_code=401),
                {401: "hint: use process_own()"},
            )
        assert exc.value.hint is None
