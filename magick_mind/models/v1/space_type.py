"""Magickspace type vocabulary and the proto-enum normalizer shared by every
model that carries a space type."""

from __future__ import annotations

from typing import Literal

MindSpaceType = Literal["PRIVATE", "GROUP"]

# The API returns proto enum .String() values prefixed with the owning enum's
# name -- MINDSPACE_TYPE_GROUP, and MAGICKSPACE_TYPE_GROUP after the rename.
# We normalize to the short form for SDK consumers.
_TYPE_MARKER = "_TYPE_"

_TYPE_NORMALIZE: dict[str, MindSpaceType] = {
    "PRIVATE": "PRIVATE",
    "GROUP": "GROUP",
}


def normalize_space_type(v: object) -> object:
    """Normalize a proto enum type name to its short form.

    Accepts the short form as-is and any ``<ENUM>_TYPE_<SHORT>`` spelling whose
    suffix is a valid short form. Matching the suffix rather than a fixed list
    of prefixes means the next rename of the enum keeps parsing instead of
    failing validation on every row, as the mindspace -> magickspace rename did.

    An unrecognized value is returned unchanged so it fails validation loudly
    rather than being masked.
    """
    if not isinstance(v, str):
        return v
    if v in _TYPE_NORMALIZE:
        return _TYPE_NORMALIZE[v]
    marker = v.rfind(_TYPE_MARKER)
    if marker != -1:
        return _TYPE_NORMALIZE.get(v[marker + len(_TYPE_MARKER) :], v)
    return v


def space_type_or_none(v: object) -> object:
    """Normalize an optional space type; empty means absent."""
    return normalize_space_type(v) if v else None
