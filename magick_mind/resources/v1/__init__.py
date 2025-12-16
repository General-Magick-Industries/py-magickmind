"""V1 API resources."""

from magick_mind.resources.v1.artifact import ArtifactResourceV1
from magick_mind.resources.v1.corpus import CorpusResourceV1
from magick_mind.resources.v1.chat import ChatResourceV1
from magick_mind.resources.v1.end_user import EndUserResourceV1
from magick_mind.resources.v1.mindspace import MindspaceResourceV1
from magick_mind.resources.v1.project import ProjectResourceV1

__all__ = [
    "ArtifactResourceV1",
    "CorpusResourceV1",
    "ChatResourceV1",
    "EndUserResourceV1",
    "MindspaceResourceV1",
    "ProjectResourceV1",
]
