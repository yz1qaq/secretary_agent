import uuid
from copy import deepcopy
from pathlib import Path
from typing import Any

from .utils import excerpt, load_json_file, now_iso, save_json_file, score_text


class MidTermMemory:
    def __init__(self, file_path: Path, max_capacity: int = 200) -> None:
        self.file_path = file_path
        self.max_capacity = max_capacity

    def _default_payload(self) -> dict[str, list[dict[str, Any]]]:
        return {"segments": []}

    def _read(self) -> dict[str, list[dict[str, Any]]]:
        payload = load_json_file(self.file_path, self._default_payload())
        segments = payload.get("segments")
        if not isinstance(segments, list):
            return self._default_payload()
        return {"segments": segments}

    def _write(self, payload: dict[str, list[dict[str, Any]]]) -> None:
        save_json_file(self.file_path, payload)

    def add_segment(self, segment: dict[str, Any]) -> dict[str, Any]:
        payload = self._read()
        if not segment.get("id"):
            segment["id"] = str(uuid.uuid4())
        payload["segments"].append(segment)
        payload["segments"] = payload["segments"][-self.max_capacity :]
        self._write(payload)
        return deepcopy(segment)

    def get_all(self) -> list[dict[str, Any]]:
        return deepcopy(self._read()["segments"])

    def retrieve(self, query: str, limit: int = 4) -> list[dict[str, Any]]:
        payload = self._read()
        scored: list[tuple[float, dict[str, Any]]] = []

        for segment in payload["segments"]:
            candidate = "\n".join(
                [
                    str(segment.get("title") or ""),
                    str(segment.get("summary") or ""),
                    " ".join(segment.get("keywords") or []),
                ]
            )
            score = score_text(query, candidate)
            if score <= 0:
                continue

            segment["retrieval_count"] = int(segment.get("retrieval_count") or 0) + 1
            segment["last_accessed_at"] = now_iso()
            segment["heat"] = round(float(segment.get("heat") or 0.0) + 1.0 + score, 4)

            enriched = deepcopy(segment)
            enriched["score"] = round(score, 4)
            enriched["preview"] = excerpt(candidate)
            scored.append((score, enriched))

        if scored:
            self._write(payload)

        scored.sort(key=lambda pair: pair[0], reverse=True)
        return [item for _, item in scored[:limit]]

    def get_hot_unanalyzed_segments(
        self,
        threshold: float,
        limit: int = 3,
    ) -> list[dict[str, Any]]:
        segments = [
            deepcopy(segment)
            for segment in self._read()["segments"]
            if not bool(segment.get("analyzed", False))
            and float(segment.get("heat") or 0.0) >= threshold
        ]
        segments.sort(key=lambda item: float(item.get("heat") or 0.0), reverse=True)
        return segments[:limit]

    def mark_analyzed(self, segment_ids: list[str]) -> None:
        if not segment_ids:
            return

        payload = self._read()
        id_set = set(segment_ids)
        for segment in payload["segments"]:
            if str(segment.get("id")) in id_set:
                segment["analyzed"] = True
                segment["analyzed_at"] = now_iso()
        self._write(payload)
