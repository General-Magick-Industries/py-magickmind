import re
from magick_mind.reasoning.super_master.dto import (
    GetCritiqueDTO,
    ImproveAnswerDTO,
    RateAnswerDTO,
)
from magick_mind.utils.providers.abstraction import InferenceProvider
from magick_mind.utils.providers.inference.constants import MessageRole
from magick_mind.utils.providers.inference.dto import MessageDTO
from magick_mind.utils.response_format import (
    AnswerResponse,
    SuperMasterRateAnswerResponse,
)


# Get Critique
async def get_critique(
    get_critique_dto: GetCritiqueDTO,
    inference_provider: InferenceProvider,
):
    prompt = (
        f"Episodic Memory: {get_critique_dto.episodic_memory}\n"
        f"Semantic Memory: {get_critique_dto.semantic_memory}\n"
        "You can use the episodic memory and semantic memory to improve the answer if the user question is related to the episodic memory or semantic memory."
        f"Question: {get_critique_dto.question}\n"
        f"Draft Answer: {get_critique_dto.draft_answer}\n"
        + (f"Role: {get_critique_dto.role}\n" if get_critique_dto.role else "")
        + "Please critique the draft answer. "
        "Do a careful assessment of whether the answer is correct or not, and why."
        "Consider multiple ways of verifying the correctness of the answer."
        "Do point out every flaw and hold the draft answer to a high standard. "
        "Do provide specific recommendations to improve the answer. "
        "Do think step by step. "
        "Do not provide a revised answer."
    )

    messages = [
        MessageDTO(role=MessageRole.USER.value, content=prompt),
    ]

    return inference_provider.infer(messages=messages)


async def improve_answer(
    improve_answer_dto: ImproveAnswerDTO,
    inference_provider: InferenceProvider,
):
    prompt = (
        f"Episodic Memory: {improve_answer_dto.episodic_memory}\n"
        f"Semantic Memory: {improve_answer_dto.semantic_memory}\n"
        "You can use the episodic memory and semantic memory to improve the answer if the user question is related to the episodic memory or semantic memory."
        f"Question: {improve_answer_dto.question}\n"
        f"Draft Answer: {improve_answer_dto.draft_answer}\n"
        f"Critique: {improve_answer_dto.critique}\n\n"
        + (f"Role: {improve_answer_dto.role}\n" if improve_answer_dto.role else "")
        + "Please improve the draft answer based on the critique. Follow this format:\n"
        """
        {
            "reasoning_process": "<step-by-step reasoning process>",
            "verification": "<verification of the facts>",
            "final_answer": "<the improved and verified answer>"
        }
        """
    )

    messages = [
        MessageDTO(role=MessageRole.USER.value, content=prompt),
    ]

    improved_answer = inference_provider.infer(
        messages=messages, response_format=improve_answer_dto.response_format
    )

    try:
        if improved_answer:
            response_model = improve_answer_dto.response_format.model_validate_json(
                improved_answer
            )
            improved_answer = response_model
    except Exception:
        improved_answer = AnswerResponse(
            reasoning_process="", verification="", final_answer=""
        )

    return improved_answer


async def rate_answer(
    rate_answer_dto: RateAnswerDTO,
    inference_provider: InferenceProvider,
):
    prompt = (
        f"Episodic Memory: {rate_answer_dto.episodic_memory}\n"
        f"Semantic Memory: {rate_answer_dto.semantic_memory}\n"
        "You can use the episodic memory and semantic memory to improve the answer if the user question is related to the episodic memory or semantic memory."
        f"Question: {rate_answer_dto.question}\n"
        f"Answer: {rate_answer_dto.answer}\n\n"
        + (f"Role: {rate_answer_dto.role}\n" if rate_answer_dto.role else "")
        + "As an expert on this topic, please provide a detailed critique of the answer, pointing out every flaw. "
        "Provide only a critique, not a suggested answer. "
        "Then, rate the correctness of the answer on a scale of 0 to 100."
        "Then, provide the confidence score in the correctness rating of the answer on a scale of 0 to 100."
        "The response should be in the following format:\n"
        "Critique: <detailed critique>\n"
        "Rating: <rating>\n"
        "Confidence Score: <confidence score>"
    )

    messages = [
        MessageDTO(role=MessageRole.USER.value, content=prompt),
    ]

    rating_response = inference_provider.infer(
        messages=messages, response_format=SuperMasterRateAnswerResponse
    )

    # Extract the rating
    try:
        if rating_response:
            response_model = SuperMasterRateAnswerResponse.model_validate_json(
                rating_response
            )
            rating = response_model.rating
            confidence = response_model.confidence_score
        else:
            raise ValueError("Rating not found in the response")
    except Exception as e:
        print(f"Error extracting rating: {e}")
        rating = 0.0
        confidence = 0.0
    return rating, confidence
