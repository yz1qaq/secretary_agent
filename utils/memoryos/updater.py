from collections import Counter

from .long_term import LongTermMemory
from .mid_term import MidTermMemory
from .short_term import ShortTermMemory
from .utils import dedupe_preserve_order, excerpt, now_iso, tokenize_text


class Updater:
    def __init__(
        self,
        *,
        short_term_memory: ShortTermMemory,
        mid_term_memory: MidTermMemory,
        long_term_memory: LongTermMemory,
        assistant_long_term_memory: LongTermMemory,
        heat_threshold: float = 3.0,
    ) -> None:
        self.short_term_memory = short_term_memory
        self.mid_term_memory = mid_term_memory
        self.long_term_memory = long_term_memory
        self.assistant_long_term_memory = assistant_long_term_memory
        self.heat_threshold = heat_threshold

    def _extract_keywords(self, text: str, limit: int = 8) -> list[str]:
        tokens = [
            token
            for token in tokenize_text(text)
            if len(token) >= 2 and token not in {"用户", "助手", "今天", "现在"}
        ]
        return [token for token, _ in Counter(tokens).most_common(limit)]

    def process_short_term_to_mid_term(self) -> dict[str, object] | None:
        qa_pairs = self.short_term_memory.consume_all()
        if not qa_pairs:
            return None

        combined_lines: list[str] = []
        thread_ids: list[str] = []
        for item in qa_pairs:
            user_input = str(item.get("user_input") or "").strip()
            agent_response = str(item.get("agent_response") or "").strip()
            if user_input:
                combined_lines.append(f"用户：{user_input}")
            if agent_response:
                combined_lines.append(f"助手：{agent_response}")
            if item.get("thread_id"):
                thread_ids.append(str(item["thread_id"]))

        summary_text = "\n".join(combined_lines).strip()
        if not summary_text:
            return None

        title_seed = str(qa_pairs[0].get("user_input") or "对话片段").strip() or "对话片段"
        segment = {
            "title": excerpt(title_seed, 24),
            "summary": excerpt(summary_text, 500),
            "keywords": self._extract_keywords(summary_text),
            "details": qa_pairs,
            "thread_ids": dedupe_preserve_order(thread_ids),
            "created_at": now_iso(),
            "updated_at": now_iso(),
            "last_accessed_at": now_iso(),
            "retrieval_count": 0,
            "heat": 1.0,
            "analyzed": False,
        }
        return self.mid_term_memory.add_segment(segment)

    def get_hot_unanalyzed_segments(self) -> list[dict[str, object]]:
        return self.mid_term_memory.get_hot_unanalyzed_segments(self.heat_threshold)

    def analyze_segment(self, segment: dict[str, object]) -> None:
        details = segment.get("details") or []
        if not isinstance(details, list):
            details = []

        user_knowledge_candidates: list[str] = []
        assistant_knowledge_candidates: list[str] = []

        for item in details:
            if not isinstance(item, dict):
                continue
            user_input = str(item.get("user_input") or "").strip()
            agent_response = str(item.get("agent_response") or "").strip()
            if len(user_input) >= 4:
                user_knowledge_candidates.append(user_input)
            if 12 <= len(agent_response) <= 220:
                assistant_knowledge_candidates.append(agent_response)

        user_knowledge = dedupe_preserve_order(user_knowledge_candidates)[-8:]
        assistant_knowledge = dedupe_preserve_order(assistant_knowledge_candidates)[-6:]

        segment_id = str(segment.get("id") or "")
        meta_data = {"thread_ids": segment.get("thread_ids") or []}

        for knowledge in user_knowledge:
            self.long_term_memory.add_knowledge(
                knowledge,
                source_segment_id=segment_id,
                meta_data=meta_data,
            )

        for knowledge in assistant_knowledge:
            self.assistant_long_term_memory.add_knowledge(
                knowledge,
                source_segment_id=segment_id,
                meta_data=meta_data,
            )

        self.long_term_memory.rebuild_profile_from_knowledge(
            title="当前已知的用户偏好与事实"
        )
        self.mid_term_memory.mark_analyzed([segment_id])
