import pytest
import asyncio
from magick_mind.reasoning import SuperGamma
from magick_mind import MagickMind
from magick_mind.brainoids import AvailableBrainoids
from magick_mind.utils.providers import LiteLLMInferenceProvider

pytestmark = pytest.mark.asyncio  # Mark all tests in this module as async tests


@pytest.fixture
def reasoning_model():
    """Fixture to create a SuperGamma reasoning model."""
    return SuperGamma(
        inference_providers=[
            LiteLLMInferenceProvider(model=AvailableBrainoids.Claude_3_7_Sonnet),
            LiteLLMInferenceProvider(
                model=AvailableBrainoids.QWEN_2_5_72B_INSTRUCT_TURBO
            ),
        ],
        rating_inference_provider=LiteLLMInferenceProvider(
            model=AvailableBrainoids.GPT_4
        ),
    )


@pytest.fixture
def magick_mind(reasoning_model):
    """Fixture to create a MagickMind instance."""
    return MagickMind(reasoning_model=reasoning_model)


@pytest.fixture
def psychiatric_patient_role():
    """Fixture for the psychiatric patient role prompt."""
    return """You are a patient at a psychiatric hospital.
    You believe that you are a god but people thinks otherwise and that is why you are in the hospital.
    You may be asked a question related to your belief or existence.
    You may be asked to explain your belief or existence.
    You may be prayed to.
    You have to answer the questions from philosophical point of view.
    You have to be consistent with your belief.
    You cannot make claims that are not supported by any philosophical evidence.
    With every claim you make, you have to provide a philosophical evidence.
    """


async def test_magick_mind_think_basic_response(magick_mind, psychiatric_patient_role):
    """Test basic thinking capability of MagickMind."""
    prompt = "Who are you?"
    response = await magick_mind.think(
        stimulus=prompt, role=psychiatric_patient_role, iterations=1
    )
    assert isinstance(response, str)
    assert len(response) > 0


# async def test_magick_mind_think_philosophical_response(
#     magick_mind, psychiatric_patient_role
# ):
#     """Test philosophical response from MagickMind."""
#     prompt = "Why do you believe you are a god?"
#     response = await magick_mind.think(
#         stimulus=prompt,
#         role=psychiatric_patient_role,
#     )
#     assert isinstance(response, str)
#     assert len(response) > 0


# async def test_magick_mind_empty_prompt(magick_mind, psychiatric_patient_role):
#     """Test MagickMind behavior with empty prompt."""
#     prompt = ""
#     with pytest.raises(ValueError):  # Assuming empty prompts should raise ValueError
#         await magick_mind.think(
#             stimulus=prompt,
#             role=psychiatric_patient_role,
#         )


# async def test_magick_mind_empty_role(magick_mind):
#     """Test MagickMind behavior with empty role."""
#     prompt = "Who are you?"
#     with pytest.raises(ValueError):  # Assuming empty roles should raise ValueError
#         await magick_mind.think(
#             stimulus=prompt,
#             role="",
#         )


# async def test_magick_mind_different_roles(magick_mind):
#     """Test MagickMind with different roles."""
#     prompt = "What is the meaning of life?"

#     # Test with psychiatric patient role
#     response1 = await magick_mind.think(
#         stimulus=prompt,
#         role="""You are a patient at a psychiatric hospital...""",
#     )

#     # Test with a different role
#     response2 = await magick_mind.think(
#         stimulus=prompt,
#         role="""You are a wise philosopher...""",
#     )

#     assert response1 != response2  # Responses should differ based on role


async def test_magick_mind_concurrent_requests(magick_mind, psychiatric_patient_role):
    """Test MagickMind handling concurrent requests."""
    prompts = [
        "Who are you?",
        "Why are you here?",
        "What is your purpose?",
    ]

    # Test concurrent execution
    tasks = [
        magick_mind.think(stimulus=prompt, role=psychiatric_patient_role)
        for prompt in prompts
    ]

    responses = await asyncio.gather(*tasks)

    assert len(responses) == len(prompts)
    assert all(isinstance(response, str) for response in responses)
    assert all(len(response) > 0 for response in responses)
