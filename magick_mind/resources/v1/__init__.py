"""V1 API resources."""

from magick_mind.resources.v1.artifact import ArtifactResourceV1
from magick_mind.resources.v1.api_keys import ApiKeysResourceV1
from magick_mind.resources.v1.blueprint import BlueprintResourceV1
from magick_mind.resources.v1.corpus import CorpusResourceV1
from magick_mind.resources.v1.chat import ChatResourceV1
from magick_mind.resources.v1.end_user import EndUserResourceV1
from magick_mind.resources.v1.mindspace import MindspaceResourceV1
from magick_mind.resources.v1.persona import PersonaResourceV1
from magick_mind.resources.v1.project import ProjectResourceV1
from magick_mind.resources.v1.runtime import RuntimeResourceV1

__all__ = [
    "ArtifactResourceV1",
    "ApiKeysResourceV1",
    "BlueprintResourceV1",
    "CorpusResourceV1",
    "ChatResourceV1",
    "EndUserResourceV1",
    "MindspaceResourceV1",
    "PersonaResourceV1",
    "ProjectResourceV1",
    "RuntimeResourceV1",
]
