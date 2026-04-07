import asyncio
import uuid
from pathlib import Path
from typing import Any

from .long_term import LongTermMemory
from .mid_term import MidTermMemory
from .retriever import Retriever
from .short_term import ShortTermMemory
from .updater import Updater
from .utils import excerpt, now_iso


class MemoryOSService:
    def __init__(
        self,
        *,
        user_id: str,
        assistant_id: str,
        data_storage_path: Path,
        short_term_capacity: int = 6,
        mid_term_capacity: int = 200,
        long_term_knowledge_capacity: int = 120,
        retrieval_queue_capacity: int = 4,
        mid_term_heat_threshold: float = 3.0,
    ) -> None:
        self.user_id = user_id
        self.assistant_id = assistant_id
        self.data_storage_path = data_storage_path

        user_dir = self.data_storage_path / "users" / self.user_id
        assistant_dir = self.data_storage_path / "assistants" / self.assistant_id

        self.short_term_memory = ShortTermMemory(
            user_dir / "short_term.json",
            max_capacity=short_term_capacity,
        )
        self.mid_term_memory = MidTermMemory(
            user_dir / "mid_term.json",
            max_capacity=mid_term_capacity,
        )
        self.user_long_term_memory = LongTermMemory(
            user_dir / "long_term_user.json",
            knowledge_capacity=long_term_knowledge_capacity,
            profile_key="user_profile",
            profile_kind="user",
        )
        self.assistant_long_term_memory = LongTermMemory(
            assistant_dir / "long_term_assistant.json",
            knowledge_capacity=long_term_knowledge_capacity,
            profile_key="assistant_profile",
            profile_kind="assistant",
        )

        self.retriever = Retriever(
            short_term_memory=self.short_term_memory,
            mid_term_memory=self.mid_term_memory,
            long_term_memory=self.user_long_term_memory,
            assistant_long_term_memory=self.assistant_long_term_memory,
            queue_capacity=retrieval_queue_capacity,
        )
        self.updater = Updater(
            short_term_memory=self.short_term_memory,
            mid_term_memory=self.mid_term_memory,
            long_term_memory=self.user_long_term_memory,
            assistant_long_term_memory=self.assistant_long_term_memory,
            heat_threshold=mid_term_heat_threshold,
        )
        self._lock = asyncio.Lock()

    async def add_memory(
        self,
        *,
        user_input: str,
        agent_response: str,
        thread_id: str,
        timestamp: str | None = None,
        meta_data: dict[str, Any] | None = None,
    ) -> None:
        qa_pair = {
            "id": str(uuid.uuid4()),
            "thread_id": thread_id,
            "user_input": user_input.strip(),
            "agent_response": agent_response.strip(),
            "timestamp": timestamp or now_iso(),
            "meta_data": meta_data or {},
        }

        async with self._lock:
            self.short_term_memory.add_qa_pair(qa_pair)
            if self.short_term_memory.is_full():
                self.updater.process_short_term_to_mid_term()

            hot_segments = self.updater.get_hot_unanalyzed_segments()
            for segment in hot_segments:
                self.updater.analyze_segment(segment)

    async def retrieve_memory(
        self,
        *,
        query: str,
        thread_id: str | None = None,
    ) -> dict[str, object]:
        async with self._lock:
            result = self.retriever.retrieve_context(
                user_query=query,
                user_id=self.user_id,
                thread_id=thread_id,
            )
            hot_segments = self.updater.get_hot_unanalyzed_segments()
            if hot_segments:
                for segment in hot_segments:
                    self.updater.analyze_segment(segment)
                result = self.retriever.retrieve_context(
                    user_query=query,
                    user_id=self.user_id,
                    thread_id=thread_id,
                )
            return result

    async def get_user_profile(self) -> dict[str, object]:
        async with self._lock:
            return {
                "user_id": self.user_id,
                "assistant_id": self.assistant_id,
                "user_profile": self.user_long_term_memory.get_snapshot(),
                "assistant_profile": self.assistant_long_term_memory.get_snapshot(),
                "user_knowledge": self.user_long_term_memory.get_knowledge(),
                "assistant_knowledge": self.assistant_long_term_memory.get_knowledge(),
            }

    async def get_short_term_memory(self) -> list[dict[str, Any]]:
        async with self._lock:
            return self.short_term_memory.get_all()

    async def get_mid_term_memory(self) -> list[dict[str, Any]]:
        async with self._lock:
            return self.mid_term_memory.get_all()

    async def get_long_term_memory(self) -> dict[str, Any]:
        async with self._lock:
            return {
                "user": self.user_long_term_memory.get_snapshot(),
                "assistant": self.assistant_long_term_memory.get_snapshot(),
            }

    async def update_manual_profiles(
        self,
        *,
        user_manual_profile: dict[str, Any] | None = None,
        assistant_manual_profile: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        async with self._lock:
            if user_manual_profile is not None:
                self.user_long_term_memory.update_manual_profile(user_manual_profile)
            if assistant_manual_profile is not None:
                self.assistant_long_term_memory.update_manual_profile(assistant_manual_profile)

            return {
                "user": self.user_long_term_memory.get_snapshot(),
                "assistant": self.assistant_long_term_memory.get_snapshot(),
            }

    async def get_memory_center_snapshot(self) -> dict[str, Any]:
        async with self._lock:
            return {
                "short_term": self.short_term_memory.get_all(),
                "mid_term": self.mid_term_memory.get_all(),
                "long_term": {
                    "user": self.user_long_term_memory.get_snapshot(),
                    "assistant": self.assistant_long_term_memory.get_snapshot(),
                },
            }

    async def build_prompt_context(
        self,
        *,
        thread_id: str,
        query: str,
    ) -> tuple[str, dict[str, object]]:
        retrieved = await self.retrieve_memory(query=query, thread_id=thread_id)

        parts: list[str] = []
        user_profile = self.user_long_term_memory.get_profile()
        if user_profile:
            parts.append(f"用户画像摘要：\n{user_profile}")

        assistant_profile = self.assistant_long_term_memory.get_profile()
        if assistant_profile:
            parts.append(f"AI秘书画像摘要：\n{assistant_profile}")

        user_knowledge = retrieved.get("retrieved_user_knowledge") or []
        if isinstance(user_knowledge, list) and user_knowledge:
            lines = [
                f"- {excerpt(str(item.get('knowledge') or ''), 180)}"
                for item in user_knowledge
                if isinstance(item, dict) and str(item.get("knowledge") or "").strip()
            ]
            if lines:
                parts.append("相关用户长期记忆：\n" + "\n".join(lines))

        assistant_knowledge = retrieved.get("retrieved_assistant_knowledge") or []
        if isinstance(assistant_knowledge, list) and assistant_knowledge:
            lines = [
                f"- {excerpt(str(item.get('knowledge') or ''), 180)}"
                for item in assistant_knowledge
                if isinstance(item, dict) and str(item.get("knowledge") or "").strip()
            ]
            if lines:
                parts.append("相关助手长期知识：\n" + "\n".join(lines))

        retrieved_pages = retrieved.get("retrieved_pages") or []
        if isinstance(retrieved_pages, list) and retrieved_pages:
            lines = [
                f"- {excerpt(str(item.get('summary') or ''), 220)}"
                for item in retrieved_pages
                if isinstance(item, dict) and str(item.get("summary") or "").strip()
            ]
            if lines:
                parts.append("相关中期记忆片段：\n" + "\n".join(lines))

        short_term_memory = retrieved.get("short_term_memory") or []
        if isinstance(short_term_memory, list) and short_term_memory:
            lines = []
            for item in short_term_memory:
                if not isinstance(item, dict):
                    continue
                user_input = excerpt(str(item.get("user_input") or ""), 120)
                agent_response = excerpt(str(item.get("agent_response") or ""), 120)
                if not user_input and not agent_response:
                    continue
                lines.append(f"- 用户：{user_input}；助手：{agent_response}")
            if lines:
                parts.append("相关短期记忆：\n" + "\n".join(lines))

        return "\n\n".join(parts).strip(), retrieved
