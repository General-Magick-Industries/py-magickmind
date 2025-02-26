import re
from magick_mind.utils.providers.abstraction import InferenceProvider


async def get_critique(question, draft_answer, episodic_memory, semantic_memory, inference_provider: InferenceProvider):
    prompt = (
        f"Episodic Memory: {episodic_memory}\n"
        f"Semantic Memory: {semantic_memory}\n"
        "You can use the episodic memory and semantic memory to improve the answer if the user question is related to the episodic memory or semantic memory."
        f"Question: {question}\n"
        f"Draft Answer: {draft_answer}\n"
        "Please critique the draft answer. "
        "Do a careful assessment of whether the answer is correct or not, and why."
        "Consider multiple ways of verifying the correctness of the answer."
        "Do point out every flaw and hold the draft answer to a high standard. "
        "Do provide specific recommendations to improve the answer. "
        "Do think step by step. "
        "Do not provide a revised answer."
    )

    # Create the request to the LLM
    return inference_provider.infer(prompt)


async def improve_answer(question, draft_answer, critique, episodic_memory, semantic_memory, inference_provider: InferenceProvider):
    prompt = (
        f"Episodic Memory: {episodic_memory}\n"
        f"Semantic Memory: {semantic_memory}\n"
        "You can use the episodic memory and semantic memory to improve the answer if the user question is related to the episodic memory or semantic memory."
        f"Question: {question}\n"
        f"Draft Answer: {draft_answer}\n"
        f"Critique: {critique}\n\n"
        "Please improve the draft answer based on the critique. Follow this format:\n"
        "Reasoning Process: <step-by-step reasoning process>\n"
        "Verification: <verification of the facts>\n"
        "Final Answer: <the improved and verified answer>\n"
    )

    # Create the request to the LLM
    return inference_provider.infer(prompt)


def rate_answer(question, answer, episodic_memory, semantic_memory, inference_provider: InferenceProvider):
    prompt = (
        f"Episodic Memory: {episodic_memory}\n"
        f"Semantic Memory: {semantic_memory}\n"
        "You can use the episodic memory and semantic memory to improve the answer if the user question is related to the episodic memory or semantic memory."
        f"Question: {question}\n"
        f"Answer: {answer}\n\n"
        "As an expert on this topic, please provide a detailed critique of the answer, pointing out every flaw. "
        "Provide only a critique, not a suggested answer. "
        "Then, rate the answer on a scale of 0 to 100. "
        "The response should be in the following format:\n"
        "Critique: <detailed critique>\n"
        "Rating: <rating>"
    )

    # Create the request to the LLM
    rating_response = inference_provider.infer(prompt)

    # Extract the rating
    try:
        match = re.search(r'Rating:\s*(\d+)', rating_response)
        if match:
            rating = int(match.group(1))
            if rating > 95:
                rating = 95
            rating = float(rating) / 100
        else:
            raise ValueError("Rating not found in the response")
    except Exception as e:
        print(f"Error extracting rating: {e}")
        rating = 0.0

    return rating
