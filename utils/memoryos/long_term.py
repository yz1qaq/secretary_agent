import uuid
from copy import deepcopy
from pathlib import Path
from typing import Any

from .utils import dedupe_preserve_order, load_json_file, now_iso, normalize_text, save_json_file, score_text


class LongTermMemory:
    def __init__(
        self,
        file_path: Path,
        knowledge_capacity: int = 120,
        profile_key: str = "profile",
    ) -> None:
        self.file_path = file_path
        self.knowledge_capacity = knowledge_capacity
        self.profile_key = profile_key

    def _default_payload(self) -> dict[str, Any]:
        return {self.profile_key: "", "knowledge": []}

    def _read(self) -> dict[str, Any]:
        payload = load_json_file(self.file_path, self._default_payload())
        if not isinstance(payload.get("knowledge"), list):
            payload["knowledge"] = []
        if not isinstance(payload.get(self.profile_key), str):
            payload[self.profile_key] = ""
        return payload

    def _write(self, payload: dict[str, Any]) -> None:
        save_json_file(self.file_path, payload)

    def get_profile(self) -> str:
        return str(self._read().get(self.profile_key) or "").strip()

    def update_profile(self, profile_text: str) -> None:
        payload = self._read()
        payload[self.profile_key] = profile_text.strip()
        self._write(payload)

    def get_knowledge(self) -> list[dict[str, Any]]:
        return deepcopy(self._read()["knowledge"])

    def add_knowledge(
        self,
        knowledge_text: str,
        *,
        source_segment_id: str | None = None,
        meta_data: dict[str, Any] | None = None,
    ) -> None:
        normalized = normalize_text(knowledge_text)
        if not normalized:
            return

        payload = self._read()
        existing = {
            normalize_text(str(item.get("knowledge") or ""))
            for item in payload["knowledge"]
        }
        if normalized in existing:
            return

        payload["knowledge"].append(
            {
                "id": str(uuid.uuid4()),
                "knowledge": knowledge_text.strip(),
                "timestamp": now_iso(),
                "source_segment_id": source_segment_id or "",
                "meta_data": meta_data or {},
            }
        )
        payload["knowledge"] = payload["knowledge"][-self.knowledge_capacity :]
        self._write(payload)

    def rebuild_profile_from_knowledge(
        self,
        *,
        max_items: int = 8,
        title: str = "已知用户信息",
    ) -> str:
        knowledge_items = [
            str(item.get("knowledge") or "").strip()
            for item in self.get_knowledge()[-max_items:]
            if str(item.get("knowledge") or "").strip()
        ]
        lines = dedupe_preserve_order(knowledge_items)
        if not lines:
            profile = ""
        else:
            bullet_lines = "\n".join(f"- {line}" for line in lines[-max_items:])
            profile = f"{title}：\n{bullet_lines}"
        self.update_profile(profile)
        return profile

    def retrieve(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        scored: list[tuple[float, dict[str, Any]]] = []
        for item in self.get_knowledge():
            knowledge = str(item.get("knowledge") or "")
            score = score_text(query, knowledge)
            if score <= 0:
                continue
            enriched = deepcopy(item)
            enriched["score"] = round(score, 4)
            scored.append((score, enriched))

        scored.sort(key=lambda pair: pair[0], reverse=True)
        return [item for _, item in scored[:limit]]
