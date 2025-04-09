# Magick Mind

A package for the Magick Mind project by General Magicko Industries

## Installation

```bash
pip install git+https://{GITHUB_TOKEN}@github.com/General-Magick-Industries/AGD_Magick_Mind.git
```

## Usage

```python
from magick_mind import MagickMind
from magick_mind.reasoning import SuperGamma
from magick_mind.utils.providers.inference_provider import LiteLLMInferenceProvider
from magick_mind.brainoids.available_brainoids import AvailableBrainoids

mm = MagickMind(
    reasoning_model=SuperGamma(
        inference_providers=[
            LiteLLMInferenceProvider(model=AvailableBrainoids.GPT_4o),
            LiteLLMInferenceProvider(model=AvailableBrainoids.Claude_3_5_Sonnet),
        ],
    ),
)

stimulus = "What is the capital of France?"

answer = await mm.think(
    stimulus=stimulus,
    role="You are a helpful assistant.",
    iterations=2,
)

print(answer)
```

## Memory

```python
from magick_mind.memories.episodic_memory import EpisodicMemory
from magick_mind.memories.semantic_memory import SemanticMemory

episodic_memory = EpisodicMemory(workspace_id="")
semantic_memory = SemanticMemory(workspace_id="")

mm = MagickMind(
    reasoning_model=SuperGamma(
        inference_providers=[
            LiteLLMInferenceProvider(model=AvailableBrainoids.GPT_4o),
            LiteLLMInferenceProvider(model=AvailableBrainoids.Claude_3_5_Sonnet),
        ],
    ),
)

answer = await mm.think(
    stimulus=stimulus,
    role="You are a helpful assistant.",
    iterations=2,
    episodic_memory=episodic_memory,
    semantic_memory=semantic_memory,
)

```
