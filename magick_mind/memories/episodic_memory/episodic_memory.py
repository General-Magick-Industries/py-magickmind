import json
import os
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from dataclasses import dataclass, field
from litellm import completion, embedding
from pymongo import MongoClient
from pymongo.operations import SearchIndexModel
from redis import Redis
from redis.commands.json.path import Path
from magick_mind.memories.episodic_memory.topic_track import track_topic_change
from magick_mind.memories.episodic_memory.dto.episodic_memory_dto import (
    EpisodicMemoryResponseDTO,
    PriorConversation,
    MessageDTO,
)
from magick_mind.utils.providers.inference.constants import MessageRole


@dataclass
class EpisodicMemory:
    workspace_id: str
    mongo_uri: Optional[str] = field(
        default_factory=lambda: os.environ.get("MONGODB_URI")
    )
    db_name: Optional[str] = field(default_factory=lambda: "agentic_memory")
    collection_name: Optional[str] = field(default_factory=lambda: "episodic_memory")
    redis_host: str = field(default_factory=lambda: os.environ.get("REDIS_HOST"))
    redis_port: int = field(default_factory=lambda: int(os.environ.get("REDIS_PORT")))
    redis_db: int = field(default_factory=lambda: int(os.environ.get("REDIS_DB")))
    topic_change: bool = field(default_factory=lambda: False)

    def __post_init__(self):
        """Initialize MongoDB connection and collection"""
        mongo_client = MongoClient(self.mongo_uri)
        if self.db_name not in mongo_client.list_database_names():
            db = mongo_client.get_database(self.db_name)
        else:
            db = mongo_client[self.db_name]

        if self.collection_name in db.list_collection_names():
            self.collection = db[self.collection_name]
        else:
            self.collection = db.create_collection(self.collection_name)

        # Check if index exists
        existing_indexes = self.collection.list_search_indexes()
        index_exists = any(
            index.get("name") == "vector_index" for index in existing_indexes
        )
        if not index_exists:
            search_index_model = SearchIndexModel(
                definition={
                    "fields": [
                        {
                            "type": "vector",
                            "numDimensions": 3072,
                            "path": "embedding",
                            "similarity": "cosine",
                        }
                    ]
                },
                name="vector_index",
                type="vectorSearch",
            )
            self.collection.create_search_index(model=search_index_model)

        self.key = f"episodic_memory:{self.workspace_id}"
        self.redis = Redis(host=self.redis_host, port=self.redis_port, db=self.redis_db)
        # Only initialize if the key doesn't exist yet
        if not self.redis.exists(self.key):
            self.redis.json().set(
                self.key,
                Path.root_path(),
                PriorConversation(messages=[]).model_dump(),
            )

    def get_embedding(self, query: str) -> List[float]:
        """Get embedding for a query using LiteLLM's embedding function"""
        response = embedding(model="text-embedding-3-large", input=[query])
        return response.data[0]["embedding"]

    def reflect(self, conversation: str) -> dict:
        """Generate reflection on conversation"""
        reflection_prompt = f"""
        You are analyzing conversations about research papers to create memories that will help guide future interactions. Your task is to extract key elements that would be most helpful when encountering similar academic discussions in the future.

        Review the conversation and create a memory reflection following these rules:

        1. For any field where you don't have enough information or the field isn't relevant, use "N/A"
        2. Be extremely concise - each string should be one clear, actionable sentence
        3. Focus only on information that would be useful for handling similar future conversations
        4. Context_tags should be specific enough to match similar situations but general enough to be reusable

        Output valid JSON in exactly this format:
        {{
        "context_tags": [              // 2-4 keywords that would help identify similar future conversations
            string,                    // Use field-specific terms like "deep_learning", "methodology_question", "results_interpretation"
            ...
        ],
        "conversation_summary": string, // One sentence describing what the conversation accomplished
        "what_worked": string,         // Most effective approach or strategy used in this conversation
        "what_to_avoid": string        // Most important pitfall or ineffective approach to avoid
        }}

        Examples:
        - Good context_tags: ["transformer_architecture", "attention_mechanism", "methodology_comparison"]
        - Bad context_tags: ["machine_learning", "paper_discussion", "questions"]

        - Good conversation_summary: "Explained how the attention mechanism in the BERT paper differs from traditional transformer architectures"
        - Bad conversation_summary: "Discussed a machine learning paper"

        - Good what_worked: "Using analogies from matrix multiplication to explain attention score calculations"
        - Bad what_worked: "Explained the technical concepts well"

        - Good what_to_avoid: "Diving into mathematical formulas before establishing user's familiarity with linear algebra fundamentals"
        - Bad what_to_avoid: "Used complicated language"

        Additional examples for different research scenarios:

        Context tags examples:
        - ["experimental_design", "control_groups", "methodology_critique"]
        - ["statistical_significance", "p_value_interpretation", "sample_size"]
        - ["research_limitations", "future_work", "methodology_gaps"]

        Conversation summary examples:
        - "Clarified why the paper's cross-validation approach was more robust than traditional hold-out methods"
        - "Helped identify potential confounding variables in the study's experimental design"

        What worked examples:
        - "Breaking down complex statistical concepts using visual analogies and real-world examples"
        - "Connecting the paper's methodology to similar approaches in related seminal papers"

        What to avoid examples:
        - "Assuming familiarity with domain-specific jargon without first checking understanding"
        - "Over-focusing on mathematical proofs when the user needed intuitive understanding"

        Do not include any text outside the JSON object in your response.

        Here is the prior conversation:

        {conversation}
        """

        response_format = {
            "type": "json_schema",
            "json_schema": {
                "name": "reflection",
                "schema": {
                    "type": "object",
                    "properties": {
                        "context_tags": {"type": "array", "items": {"type": "string"}},
                        "conversation_summary": {"type": "string"},
                        "what_worked": {"type": "string"},
                        "what_to_avoid": {"type": "string"},
                    },
                    "required": [
                        "context_tags",
                        "conversation_summary",
                        "what_worked",
                        "what_to_avoid",
                    ],
                    "additionalProperties": False,
                },
                "strict": True,
            },
        }

        response = completion(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": reflection_prompt}],
            response_format=response_format,
        )

        return json.loads(response.choices[0].message.content)

    def store_memory(self, reflection: dict, conversation: str) -> None:
        """Store memory in MongoDB"""
        text_to_embed = (
            f"{conversation} "
            f"{', '.join(reflection['context_tags'])} "
            f"{reflection['conversation_summary']} "
            f"{reflection['what_worked']} "
            f"{reflection['what_to_avoid']}"
        )

        memory_doc = {
            "workspace_id": self.workspace_id,
            "conversation": conversation,
            "context_tags": reflection["context_tags"],
            "conversation_summary": reflection["conversation_summary"],
            "what_worked": reflection["what_worked"],
            "what_to_avoid": reflection["what_to_avoid"],
            "timestamp": datetime.now(timezone.utc),
            "embedding": self.get_embedding(text_to_embed),
        }

        self.collection.insert_one(memory_doc)

    def similar(self, query: str) -> Optional[str]:
        """Retrieve most relevant memory based on query"""
        query_embedding = self.get_embedding(query)
        pipeline = [
            {
                "$match": {
                    "workspace_id": self.workspace_id,
                }
            },
            {
                "$vectorSearch": {
                    "index": "vector_index",
                    "path": "embedding",
                    "queryVector": query_embedding,
                    "numCandidates": 3,
                    "limit": 3,
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "conversation": 1,
                    "context_tags": 1,
                    "conversation_summary": 1,
                    "what_worked": 1,
                    "what_to_avoid": 1,
                    "timestamp": 1,
                    "score": {"$meta": "vectorSearchScore"},
                }
            },
        ]

        try:
            result = list(self.collection.aggregate(pipeline))
            return "".join(
                [
                    f"[{conv['timestamp'].strftime('%H:%M:%S')}] {conv['conversation_summary']}\n"
                    for conv in result
                ]
            )
        except Exception:
            # Fallback to most recent document if vector search fails
            recent = self.collection.find_one(sort=[("timestamp", -1)])
            return (
                f"[{recent['timestamp'].strftime('%H:%M:%S')}] {recent['conversation_summary']}"
                if recent
                else None
            )

    def _get_today_conversation(self, selected_date: datetime) -> str:
        """Get conversation summaries for a specific day"""
        start_date = selected_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(days=1)

        conversations = self.collection.find(
            {
                "timestamp": {"$gte": start_date, "$lt": end_date},
                "workspace_id": self.workspace_id,
            },
            {"conversation_summary": 1, "timestamp": 1, "_id": 0},
        ).sort("timestamp", 1)

        summaries = [
            f"[{conv['timestamp'].strftime('%H:%M:%S')}] {conv['conversation_summary']}"
            for conv in conversations
        ]

        if not summaries:
            return f"No conversations found for the date {selected_date.strftime('%Y-%m-%d')}"

        summary = f"""Summary of conversations from {selected_date.strftime("%Y-%m-%d")}:
        {chr(10).join(summaries)}"""

        return summary

    def _get_previous_day_conversation(self, selected_date: datetime) -> str:
        """Get conversation summaries for a specific day"""
        start_date = selected_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date - timedelta(days=1)

        conversations = self.collection.find(
            {
                "timestamp": {"$gte": start_date, "$lt": end_date},
                "workspace_id": self.workspace_id,
            },
            {"conversation_summary": 1, "timestamp": 1, "_id": 0},
        ).sort("timestamp", 1)

        summaries = [
            f"[{conv['timestamp'].strftime('%H:%M:%S')}] {conv['conversation_summary']}"
            for conv in conversations
        ]

        if not summaries:
            return f"No conversations found for the date {selected_date.strftime('%Y-%m-%d')}"

        summary = f"""Summary of conversations from {selected_date.strftime("%Y-%m-%d")}:
        {chr(10).join(summaries)}"""

        print(summary)

        return summary

    def _get_previous_week_conversation(self, selected_date: datetime) -> str:
        """Get conversation summaries for a specific week"""
        start_date = selected_date - timedelta(days=selected_date.weekday())
        end_date = start_date + timedelta(days=7)

        conversations = self.collection.find(
            {
                "timestamp": {"$gte": start_date, "$lt": end_date},
                "workspace_id": self.workspace_id,
            },
            {"conversation_summary": 1, "timestamp": 1, "_id": 0},
        ).sort("timestamp", 1)

        summaries = [
            f"[{conv['timestamp'].strftime('%H:%M:%S')}] {conv['conversation_summary']}"
            for conv in conversations
        ]

        if not summaries:
            return f"No conversations found for the week starting {start_date.strftime('%Y-%m-%d')}"

        return f"""Summary of conversations from the week starting {start_date.strftime("%Y-%m-%d")}:
        {chr(10).join(summaries)}"""

    def _get_previous_month_conversation(self, selected_date: datetime) -> str:
        """Get conversation summaries for a specific month"""
        start_date = selected_date.replace(day=1)
        end_date = (selected_date.replace(day=1) + timedelta(days=30)).replace(day=1)

        conversations = self.collection.find(
            {
                "timestamp": {"$gte": start_date, "$lt": end_date},
                "workspace_id": self.workspace_id,
            },
            {"conversation_summary": 1, "timestamp": 1, "_id": 0},
        ).sort("timestamp", 1)

        summaries = [
            f"[{conv['timestamp'].strftime('%H:%M:%S')}] {conv['conversation_summary']}"
            for conv in conversations
        ]

        if not summaries:
            return "No conversations found for this month"

        return f"""Summary of conversations from {selected_date.strftime("%Y-%m")}:
        {chr(10).join(summaries)}"""

    def _get_previous_year_conversation(self, selected_date: datetime) -> str:
        """Get conversation summaries for a specific year"""
        start_date = selected_date.replace(day=1, month=1)
        end_date = (
            selected_date.replace(day=1, month=1) + timedelta(days=365)
        ).replace(day=1, month=1)

        conversations = self.collection.find(
            {
                "timestamp": {"$gte": start_date, "$lt": end_date},
                "workspace_id": self.workspace_id,
            },
            {"conversation_summary": 1, "timestamp": 1, "_id": 0},
        ).sort("timestamp", 1)

        summaries = [
            f"[{conv['timestamp'].strftime('%H:%M:%S')}] {conv['conversation_summary']}"
            for conv in conversations
        ]

        if not summaries:
            return "No conversations found for this year"

        return f"""Summary of conversations from {selected_date.strftime("%Y")}:
        {chr(10).join(summaries)}"""

    def get_prior_conversation(self) -> PriorConversation:
        """Get the prior conversation from Redis"""
        conversation_data = self.redis.json().get(self.key, Path.root_path())
        conversation = PriorConversation.model_validate(conversation_data)
        return conversation

    def update_prior_conversation(
        self, conversation_history: PriorConversation
    ) -> None:
        """Update the prior conversation in Redis"""
        self.redis.json().set(
            self.key, Path.root_path(), conversation_history.model_dump()
        )

    def recall(self, query: str) -> EpisodicMemoryResponseDTO:
        # TOPIC TRACK
        # IF TOPIC CHANGES, Prior Conversation converts to reflect
        # Then call store memory with output from the reflect

        # IF TOPIC NOT CHANGES, update the chat history in Redis

        """Get comprehensive episodic memory including temporal and similarity-based recalls"""
        now = datetime.now(timezone.utc)

        previous_conversation = self.get_prior_conversation()

        # Convert PriorConversation object to string format
        conversation_string = "\n".join(
            [
                f"{message.role}: {message.content}"
                for message in previous_conversation.messages
            ]
        )

        self.topic_change = track_topic_change(query, conversation_string)

        if self.topic_change:
            reflection = self.reflect(conversation_string)
            self.store_memory(reflection, conversation_string)
            self.update_prior_conversation(
                PriorConversation(
                    messages=[MessageDTO(role=MessageRole.USER.value, content=query)]
                )
            )
        else:
            previous_conversation.messages.append(
                MessageDTO(role=MessageRole.USER.value, content=query)
            )
            self.update_prior_conversation(previous_conversation)

        today_conversation = self._get_today_conversation(now)
        previous_day = self._get_previous_day_conversation(now)
        previous_week = self._get_previous_week_conversation(now)
        previous_month = self._get_previous_month_conversation(now)
        previous_year = self._get_previous_year_conversation(now)
        similar_conversations = self.similar(query)

        return EpisodicMemoryResponseDTO(
            today_conversation=today_conversation,
            previous_day_conversation=previous_day,
            previous_week_conversation=previous_week,
            previous_month_conversation=previous_month,
            previous_year_conversation=previous_year,
            similar_conversations=similar_conversations,
        )
