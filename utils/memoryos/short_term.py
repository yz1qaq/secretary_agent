from copy import deepcopy
from pathlib import Path
from typing import Any

from .utils import excerpt, load_json_file, save_json_file, score_text


class ShortTermMemory:
    def __init__(self, file_path: Path, max_capacity: int = 8) -> None:
        self.file_path = file_path
        self.max_capacity = max_capacity

    def _default_payload(self) -> dict[str, list[dict[str, Any]]]:
        return {"qa_pairs": []}

    def _read(self) -> dict[str, list[dict[str, Any]]]:
        payload = load_json_file(self.file_path, self._default_payload())
        qa_pairs = payload.get("qa_pairs")
        if not isinstance(qa_pairs, list):
            return self._default_payload()
        return {"qa_pairs": qa_pairs}

    def _write(self, payload: dict[str, list[dict[str, Any]]]) -> None:
        save_json_file(self.file_path, payload)

    def get_all(self) -> list[dict[str, Any]]:
        return deepcopy(self._read()["qa_pairs"])

    def add_qa_pair(self, qa_pair: dict[str, Any]) -> None:
        payload = self._read()
        payload["qa_pairs"].append(qa_pair)
        self._write(payload)

    def is_full(self) -> bool:
        return len(self._read()["qa_pairs"]) >= self.max_capacity

    def consume_all(self) -> list[dict[str, Any]]:
        payload = self._read()
        qa_pairs = deepcopy(payload["qa_pairs"])
        payload["qa_pairs"] = []
        self._write(payload)
        return qa_pairs

    def retrieve(self, query: str, limit: int = 4) -> list[dict[str, Any]]:
        scored: list[tuple[float, dict[str, Any]]] = []
        for item in self._read()["qa_pairs"]:
            candidate = f"{item.get('user_input', '')}\n{item.get('agent_response', '')}"
            score = score_text(query, candidate)
            if score > 0:
                enriched = deepcopy(item)
                enriched["score"] = round(score, 4)
                scored.append((score, enriched))

        scored.sort(key=lambda pair: pair[0], reverse=True)
        if scored:
            return [item for _, item in scored[:limit]]

        recent = self._read()["qa_pairs"][-limit:]
        fallback: list[dict[str, Any]] = []
        for item in recent:
            enriched = deepcopy(item)
            enriched["score"] = 0.0
            enriched["preview"] = excerpt(
                f"{item.get('user_input', '')} {item.get('agent_response', '')}"
            )
            fallback.append(enriched)
        return fallback
