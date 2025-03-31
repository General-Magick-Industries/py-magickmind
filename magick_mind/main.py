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

        episodic_memory_data = (
            episodic_memory.recall(stimulus) if episodic_memory else None
        )

        episodic_memory_string = (
            "Today's Conversation: "
            + episodic_memory_data.today_conversation
            + "\nPrevious Day's Conversation: "
            + episodic_memory_data.previous_day_conversation
            + "\nPrevious Week's Conversation: "
            + episodic_memory_data.previous_week_conversation
            + "\nPrevious Month's Conversation: "
            + episodic_memory_data.previous_month_conversation
            + "\nPrevious Year's Conversation: "
            + episodic_memory_data.previous_year_conversation
            + "\nSimilar Conversations: "
            + episodic_memory_data.similar_conversations
        )

        answer = await self.reasoning_model.process(
            stimulus=stimulus,
            iterations=iterations,
            role=role,
            semantic_memory=semantic_memory,
            episodic_memory=episodic_memory_string,
        )

        if episodic_memory:
            prior_conversation = episodic_memory.get_prior_conversation()
            last_message = MessageDTO(
                role=MessageRole.ASSISTANT.value, content=answer.__str__()
            )
            prior_conversation.messages.append(last_message)
            episodic_memory.update_prior_conversation(prior_conversation)

        return answer
