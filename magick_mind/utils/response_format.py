from typing import Type
from pydantic import BaseModel


class AnswerResponse(BaseModel):
    reasoning_process: str
    verification: str
    final_answer: str | BaseModel


class SuperGammaRateAnswerResponse(BaseModel):
    critique: str
    rating: float


class SuperMasterRateAnswerResponse(BaseModel):
    critique: str
    rating: float
    confidence_score: float


def get_answer_response_format(
    response_format: Type[BaseModel] | None = None,
) -> Type[BaseModel]:
    """
    Dynamically generate a new model with the updated `final_answer` type.
    """
    if response_format:

        class DynamicAnswerResponse(AnswerResponse):
            final_answer: response_format  # Update the type of `final_answer`

        return DynamicAnswerResponse

    return AnswerResponse
