from .long_term import LongTermMemory
from .mid_term import MidTermMemory
from .short_term import ShortTermMemory


class Retriever:
    def __init__(
        self,
        *,
        short_term_memory: ShortTermMemory,
        mid_term_memory: MidTermMemory,
        long_term_memory: LongTermMemory,
        assistant_long_term_memory: LongTermMemory,
        queue_capacity: int = 4,
    ) -> None:
        self.short_term_memory = short_term_memory
        self.mid_term_memory = mid_term_memory
        self.long_term_memory = long_term_memory
        self.assistant_long_term_memory = assistant_long_term_memory
        self.queue_capacity = queue_capacity

    def retrieve_context(
        self,
        *,
        user_query: str,
        user_id: str,
        thread_id: str | None = None,
    ) -> dict[str, object]:
        """把短中长期检索统一收口成一份上下文包，便于上层直接拼 prompt。"""
        return {
            "user_id": user_id,
            "thread_id": thread_id or "",
            "short_term_memory": self.short_term_memory.retrieve(
                user_query,
                limit=self.queue_capacity,
            ),
            "retrieved_pages": self.mid_term_memory.retrieve(
                user_query,
                limit=self.queue_capacity,
            ),
            "retrieved_user_knowledge": self.long_term_memory.retrieve(
                user_query,
                limit=self.queue_capacity,
            ),
            "retrieved_assistant_knowledge": self.assistant_long_term_memory.retrieve(
                user_query,
                limit=self.queue_capacity,
            ),
        }
