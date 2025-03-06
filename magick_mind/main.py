from magick_mind.memories.episodic_memory.episodic_memory import EpisodicMemory
from magick_mind.memories.semantic_memory.semantic_memory import SemanticMemory
from magick_mind.reasoning.interfaces import ReasoningModel


class MagickMind:
    def __init__(
        self,
        reasoning_model: ReasoningModel,
    ):
        self.reasoning_model = reasoning_model

    async def think(
        self,
        stimulus: str,
        role: str | None = None,
        semantic_memory: SemanticMemory | None = None,
        episodic_memory: EpisodicMemory | None = None,
        iterations: int = 3,
    ) -> str:
        if semantic_memory:
            semantic_memory = await semantic_memory.recall(stimulus)
            print(f"Semantic Memory: {semantic_memory}")

        if episodic_memory:
            episodic_memory = episodic_memory.get_episodic_memory(stimulus)
            print(f"Episodic Memory: {episodic_memory}")

        answer = await self.reasoning_model.process(
            stimulus=stimulus,
            iterations=iterations,
            role=role,
            semantic_memory=semantic_memory,
            episodic_memory=episodic_memory,
        )

        return answer
