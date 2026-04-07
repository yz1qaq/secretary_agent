import uuid
from copy import deepcopy
from pathlib import Path
from typing import Any

from .profile_schema import (
    ProfileKind,
    blank_profile,
    infer_assistant_profile_from_knowledge,
    infer_user_profile_from_knowledge,
    legacy_profile_to_inferred,
    merge_profiles,
    normalize_profile,
    render_profile_text,
)
from .utils import dedupe_preserve_order, load_json_file, now_iso, normalize_text, save_json_file, score_text


class LongTermMemory:
    def __init__(
        self,
        file_path: Path,
        knowledge_capacity: int = 120,
        profile_key: str = "profile",
        profile_kind: ProfileKind = "user",
    ) -> None:
        self.file_path = file_path
        self.knowledge_capacity = knowledge_capacity
        self.profile_key = profile_key
        self.profile_kind = profile_kind

    def _default_payload(self) -> dict[str, Any]:
        return {
            "manual_profile": blank_profile(self.profile_kind),
            "inferred_profile": blank_profile(self.profile_kind),
            "merged_profile_text": "",
            "knowledge": [],
        }

    def _build_merged_profile_text(
        self,
        manual_profile: dict[str, str],
        inferred_profile: dict[str, str],
    ) -> str:
        merged_profile = merge_profiles(self.profile_kind, manual_profile, inferred_profile)
        return render_profile_text(self.profile_kind, merged_profile)

    def _normalize_payload(self, raw_payload: dict[str, Any]) -> dict[str, Any]:
        payload = dict(raw_payload)
        knowledge = payload.get("knowledge")
        if not isinstance(knowledge, list):
            knowledge = []

        manual_profile = normalize_profile(
            self.profile_kind,
            payload.get("manual_profile"),
        )
        inferred_profile = normalize_profile(
            self.profile_kind,
            payload.get("inferred_profile"),
        )

        legacy_profile_text = str(payload.get(self.profile_key) or "").strip()
        if legacy_profile_text and not any(inferred_profile.values()):
            inferred_profile = legacy_profile_to_inferred(
                self.profile_kind,
                legacy_profile_text,
            )
        elif self.profile_kind == "assistant" and not any(inferred_profile.values()):
            inferred_profile = legacy_profile_to_inferred(self.profile_kind, "")

        merged_profile_text = self._build_merged_profile_text(
            manual_profile,
            inferred_profile,
        )
        if not merged_profile_text:
            merged_profile_text = str(payload.get("merged_profile_text") or "").strip()

        return {
            "manual_profile": manual_profile,
            "inferred_profile": inferred_profile,
            "merged_profile_text": merged_profile_text,
            "knowledge": knowledge,
        }

    def _read(self) -> dict[str, Any]:
        raw_payload = load_json_file(self.file_path, self._default_payload())
        payload = self._normalize_payload(raw_payload)

        if payload != raw_payload:
            self._write(payload)

        return payload

    def _write(self, payload: dict[str, Any]) -> None:
        save_json_file(self.file_path, self._normalize_payload(payload))

    def get_profile(self) -> str:
        return str(self._read().get("merged_profile_text") or "").strip()

    def update_profile(self, profile_text: str) -> None:
        self.update_manual_profile({"notes": profile_text.strip()})

    def get_manual_profile(self) -> dict[str, str]:
        return deepcopy(self._read()["manual_profile"])

    def get_inferred_profile(self) -> dict[str, str]:
        return deepcopy(self._read()["inferred_profile"])

    def get_merged_profile(self) -> dict[str, str]:
        payload = self._read()
        return merge_profiles(
            self.profile_kind,
            payload["manual_profile"],
            payload["inferred_profile"],
        )

    def get_snapshot(self) -> dict[str, Any]:
        payload = self._read()
        return {
            "manual_profile": deepcopy(payload["manual_profile"]),
            "inferred_profile": deepcopy(payload["inferred_profile"]),
            "merged_profile_text": str(payload.get("merged_profile_text") or "").strip(),
            "knowledge": deepcopy(payload["knowledge"]),
        }

    def refresh_merged_profile_text(self) -> str:
        payload = self._read()
        payload["merged_profile_text"] = self._build_merged_profile_text(
            payload["manual_profile"],
            payload["inferred_profile"],
        )
        self._write(payload)
        return str(payload["merged_profile_text"]).strip()

    def update_manual_profile(self, profile_patch: dict[str, Any]) -> dict[str, str]:
        payload = self._read()
        current = payload["manual_profile"]
        normalized_patch = normalize_profile(self.profile_kind, profile_patch)
        for field in current:
            if isinstance(profile_patch, dict) and field in profile_patch:
                current[field] = normalized_patch[field]
        payload["manual_profile"] = current
        payload["merged_profile_text"] = self._build_merged_profile_text(
            payload["manual_profile"],
            payload["inferred_profile"],
        )
        self._write(payload)
        return deepcopy(payload["manual_profile"])

    def update_inferred_profile(self, profile_data: dict[str, Any]) -> dict[str, str]:
        payload = self._read()
        payload["inferred_profile"] = normalize_profile(self.profile_kind, profile_data)
        payload["merged_profile_text"] = self._build_merged_profile_text(
            payload["manual_profile"],
            payload["inferred_profile"],
        )
        self._write(payload)
        return deepcopy(payload["inferred_profile"])

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
        knowledge = self.get_knowledge()[-max_items:]
        if self.profile_kind == "assistant":
            inferred_profile = infer_assistant_profile_from_knowledge(knowledge)
        else:
            inferred_profile = infer_user_profile_from_knowledge(knowledge)

        notes = [
            str(item.get("knowledge") or "").strip()
            for item in knowledge
            if str(item.get("knowledge") or "").strip()
        ]
        deduped_notes = dedupe_preserve_order(notes)
        if deduped_notes and not inferred_profile.get("notes"):
            inferred_profile["notes"] = f"{title}：\n" + "\n".join(
                f"- {line}" for line in deduped_notes[-max_items:]
            )

        self.update_inferred_profile(inferred_profile)
        return self.get_profile()

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
