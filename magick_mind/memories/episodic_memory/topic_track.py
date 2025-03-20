import json
from magick_mind.brainoids.available_brainoids import AvailableBrainoids
from magick_mind.utils.providers.inference_provider import LiteLLMInferenceProvider
from magick_mind.utils.providers.inference.constants import MessageRole
from magick_mind.utils.providers.inference.dto import MessageDTO


def track_topic_change(current_message: str, prior_conversation: str = None) -> bool:
    prompt = f"""
    You are a helpful assistant that tracks the topic of a conversation.
    Your task is to determine if there is a significant change in topic between the prior conversation and the current message.
    You should not consider introductory messages, random messages, or messages that are asking about previous conversations.

    Prior conversation:
    {prior_conversation}

    Current message:
    {current_message}

    Compare the prior conversation with the current message.
    Return True if there is a significant change in the topic or conversation direction.
    Return False if the current message continues the same topic or is closely related to the prior conversation.
    """
    response_format = {
        "type": "json_schema",
        "json_schema": {
            "name": "topic_change",
            "schema": {
                "type": "object",
                "properties": {
                    "topic_change": {
                        "type": "boolean",
                        "description": "True if there is a change in the topic, otherwise False",
                    },
                },
                "required": ["topic_change"],
                "additionalProperties": False,
            },
            "strict": True,
        },
    }

    inference_provider = LiteLLMInferenceProvider(
        model=AvailableBrainoids.GPT_4o,
    )

    messages = [
        MessageDTO(role=MessageRole.USER.value, content=prompt),
    ]

    response = inference_provider.infer(
        messages=messages,
        response_format=response_format,
    )

    return json.loads(response)["topic_change"]
