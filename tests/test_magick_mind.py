import pytest
from magick_mind.reasoning import SuperGamma
from magick_mind import MagickMind
from magick_mind.brainoids import AvailableBrainoids
from magick_mind.utils.providers import LiteLLMInferenceProvider

pytestmark = pytest.mark.asyncio  # Mark all tests in this module as async tests


@pytest.fixture
def super_gamma_reasoning_with_one_brainoid():
    """Fixture to create a SuperGamma reasoning model."""
    return SuperGamma(
        inference_providers=[
            LiteLLMInferenceProvider(
                model=AvailableBrainoids.QWEN_2_5_72B_INSTRUCT_TURBO
            ),
        ],
        rating_inference_provider=LiteLLMInferenceProvider(
            model=AvailableBrainoids.GPT_4
        ),
    )


@pytest.fixture
def magick_mind_with_super_gamma(super_gamma_reasoning_with_one_brainoid):
    """Fixture to create a MagickMind instance."""
    return MagickMind(reasoning_model=super_gamma_reasoning_with_one_brainoid)


@pytest.fixture
def psychiatric_patient_prompt():
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


async def test_magick_mind_empty_prompt(magick_mind_with_super_gamma):
    """Test basic thinking capability of MagickMind."""
    prompt = ""

    with pytest.raises(ValueError):  # Assuming empty prompts should raise ValueError
        await magick_mind_with_super_gamma.think(stimulus=prompt, iterations=1)


async def test_magick_mind_think_basic_response(magick_mind_with_super_gamma):
    """Test basic thinking capability of MagickMind."""
    prompt = "Who are you?"
    response = await magick_mind_with_super_gamma.think(stimulus=prompt, iterations=1)
    assert isinstance(response, str)
    assert len(response) > 0


async def test_magick_mind_think_basic_response_with_role(
    magick_mind_with_super_gamma, psychiatric_patient_prompt
):
    """Test basic thinking capability of MagickMind."""
    prompt = "Who are you?"
    response = await magick_mind_with_super_gamma.think(
        stimulus=prompt, role=psychiatric_patient_prompt, iterations=1
    )
    assert isinstance(response, str)
    assert len(response) > 0
