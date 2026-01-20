from typing import List, Optional
from pydantic import BaseModel, Field


class Model(BaseModel):
    """Model information"""

    id: Optional[str] = Field(None, description="The model identifier, e.g. 'gpt-4o'")
    object: str = Field("model", description="The object type, always 'model'")
    created: Optional[int] = Field(
        None, description="The unix timestamp when the model was created"
    )
    owned_by: Optional[str] = Field(
        None, description="The organization that owns the model"
    )
    provider: Optional[str] = Field(None, description="The provider of the model")


class ModelsListResponse(BaseModel):
    """Response containing a list of models"""

    object: str = Field("list", description="The object type, always 'list'")
    data: List[Model] = Field(
        default_factory=list, description="The list of available models"
    )
