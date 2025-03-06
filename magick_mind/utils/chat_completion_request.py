from litellm import completion
import os
from magick_mind.brainoids import AvailableBrainoids


def chat_completion_request(
    prompt: str,
    model: AvailableBrainoids,
):
    messages = [{"role": "user", "content": prompt}]

    # Create chat completions using LiteLLM's completion function
    chat_response = completion(
        model=model.value,
        messages=messages,
        temperature=0.6,
        max_tokens=1500,
        api_key=os.environ.get("LITELLM_API_KEY"),
        base_url=os.environ.get("LITELLM_BASE_URL"),
    )

    # Extract the completion text from the response
    if chat_response.choices:
        completion_text = chat_response.choices[0].message.content
    else:
        completion_text = None
    return completion_text
