from magick_mind.memories.episodic_memory.episodic_memory import EpisodicMemory
from magick_mind.memories.semantic_memory.semantic_memory import SemanticMemory
from magick_mind.utils.providers.inference.constants import MessageRole
from magick_mind.memories.episodic_memory.dto.episodic_memory_dto import MessageDTO
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
        if not stimulus:
            raise ValueError("Stimulus cannot be empty")

        if semantic_memory:
            semantic_memory = await semantic_memory.recall(stimulus)

        if episodic_memory:
            # topic track
            episodic_memory = episodic_memory.recall(stimulus)

        answer = await self.reasoning_model.process(
            stimulus=stimulus,
            iterations=iterations,
            role=role,
            semantic_memory=semantic_memory,
            episodic_memory=episodic_memory,
        )

        if episodic_memory:
            last_message = MessageDTO(role=MessageRole.ASSISTANT.value, content=answer)
            episodic_memory.update_prior_conversation(last_message)

        return answer
