import asyncio
import json
import uuid
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
THREADS_FILE = DATA_DIR / "chat_threads.json"
DEFAULT_THREAD_TITLE = "草稿会话"
DEFAULT_THREAD_PREVIEW = "当前为草稿会话，发送首条消息后会自动保存。"


def _now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _now_clock() -> str:
    return datetime.now().strftime("%H:%M")


def _default_store() -> dict[str, list[dict[str, Any]]]:
    return {"threads": []}


class ThreadStore:
    def __init__(self, file_path: Path = THREADS_FILE) -> None:
        self.file_path = file_path
        self._lock = asyncio.Lock()

    def _read_store_unlocked(self) -> dict[str, list[dict[str, Any]]]:
        if not self.file_path.exists():
            return _default_store()

        content = self.file_path.read_text(encoding="utf-8").strip()
        if not content:
            return _default_store()

        payload = json.loads(content)
        if not isinstance(payload, dict) or not isinstance(payload.get("threads"), list):
            return _default_store()

        return payload

    def _write_store_unlocked(self, payload: dict[str, list[dict[str, Any]]]) -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.file_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _normalize_attachments(
        self,
        attachments: list[dict[str, Any]] | None,
    ) -> list[dict[str, Any]]:
        normalized: list[dict[str, Any]] = []
        for attachment in attachments or []:
            content = str(attachment.get("content") or "")
            normalized.append(
                {
                    "name": str(attachment.get("name") or "未命名附件"),
                    "type": str(attachment.get("type") or "application/octet-stream"),
                    "size": int(attachment.get("size") or 0),
                    "content": content,
                    "url": content if content.startswith("data:") else "",
                }
            )
        return normalized

    def _create_thread_record(
        self,
        thread_id: str,
        *,
        title: str | None = None,
        preview: str | None = None,
        is_draft: bool = True,
        is_hidden: bool = False,
    ) -> dict[str, Any]:
        timestamp = _now_iso()
        return {
            "thread_id": thread_id,
            "title": title or DEFAULT_THREAD_TITLE,
            "preview": preview or DEFAULT_THREAD_PREVIEW,
            "is_draft": is_draft,
            "is_hidden": is_hidden,
            "created_at": timestamp,
            "updated_at": timestamp,
            "messages": [],
        }

    def _choose_unique_thread_id(
        self,
        existing_threads: list[dict[str, Any]],
        requested_thread_id: str | None = None,
    ) -> str:
        existing_ids = {
            str(thread.get("thread_id"))
            for thread in existing_threads
            if thread.get("thread_id")
        }

        if requested_thread_id and requested_thread_id not in existing_ids:
            return requested_thread_id

        generated = str(uuid.uuid4())
        while generated in existing_ids:
            generated = str(uuid.uuid4())
        return generated

    async def list_threads(self) -> list[dict[str, Any]]:
        async with self._lock:
            payload = self._read_store_unlocked()
            threads = sorted(
                [
                    thread
                    for thread in payload["threads"]
                    if not bool(thread.get("is_hidden", False))
                ],
                key=lambda item: str(item.get("updated_at") or ""),
                reverse=True,
            )

            return [
                {
                    "thread_id": str(thread.get("thread_id") or ""),
                    "title": str(thread.get("title") or DEFAULT_THREAD_TITLE),
                    "preview": str(thread.get("preview") or DEFAULT_THREAD_PREVIEW),
                    "updated_at": str(thread.get("updated_at") or ""),
                    "is_draft": bool(thread.get("is_draft", False)),
                }
                for thread in threads
            ]

    async def create_thread(
        self,
        requested_thread_id: str | None = None,
        *,
        title: str | None = None,
        preview: str | None = None,
        is_draft: bool = True,
        is_hidden: bool = False,
    ) -> dict[str, Any]:
        async with self._lock:
            payload = self._read_store_unlocked()
            thread_id = self._choose_unique_thread_id(
                payload["threads"],
                requested_thread_id=requested_thread_id,
            )
            thread = self._create_thread_record(
                thread_id,
                title=title,
                preview=preview,
                is_draft=is_draft,
                is_hidden=is_hidden,
            )
            payload["threads"].append(thread)
            self._write_store_unlocked(payload)
            return deepcopy(thread)

    async def ensure_thread(
        self,
        thread_id: str,
        *,
        title: str | None = None,
        preview: str | None = None,
        is_draft: bool = True,
        is_hidden: bool = False,
    ) -> dict[str, Any]:
        async with self._lock:
            payload = self._read_store_unlocked()
            for thread in payload["threads"]:
                if str(thread.get("thread_id")) != thread_id:
                    continue

                if title is not None:
                    thread["title"] = title
                if preview is not None:
                    thread["preview"] = preview
                thread["is_draft"] = is_draft
                thread["is_hidden"] = is_hidden
                thread["updated_at"] = _now_iso()
                self._write_store_unlocked(payload)
                return deepcopy(thread)

            thread = self._create_thread_record(
                thread_id,
                title=title,
                preview=preview,
                is_draft=is_draft,
                is_hidden=is_hidden,
            )
            payload["threads"].append(thread)
            self._write_store_unlocked(payload)
            return deepcopy(thread)

    async def get_thread(self, thread_id: str) -> dict[str, Any] | None:
        async with self._lock:
            payload = self._read_store_unlocked()
            for thread in payload["threads"]:
                if str(thread.get("thread_id")) == thread_id:
                    return deepcopy(thread)
        return None

    async def get_recent_messages(
        self,
        thread_id: str,
        *,
        limit: int = 6,
    ) -> list[dict[str, Any]]:
        async with self._lock:
            payload = self._read_store_unlocked()
            for thread in payload["threads"]:
                if str(thread.get("thread_id")) != thread_id:
                    continue
                messages = thread.get("messages", [])
                if not isinstance(messages, list):
                    return []
                return deepcopy(messages[-limit:])
        return []

    async def update_thread(
        self,
        thread_id: str,
        *,
        title: str | None = None,
        preview: str | None = None,
        is_draft: bool | None = None,
    ) -> dict[str, Any] | None:
        async with self._lock:
            payload = self._read_store_unlocked()
            for thread in payload["threads"]:
                if str(thread.get("thread_id")) != thread_id:
                    continue

                if title is not None:
                    thread["title"] = title
                if preview is not None:
                    thread["preview"] = preview
                if is_draft is not None:
                    thread["is_draft"] = is_draft
                thread["updated_at"] = _now_iso()
                self._write_store_unlocked(payload)
                return deepcopy(thread)

        return None

    async def delete_thread(self, thread_id: str) -> bool:
        async with self._lock:
            payload = self._read_store_unlocked()
            original_length = len(payload["threads"])
            payload["threads"] = [
                thread
                for thread in payload["threads"]
                if str(thread.get("thread_id")) != thread_id
            ]
            if len(payload["threads"]) == original_length:
                return False

            self._write_store_unlocked(payload)
            return True

    async def append_turn(
        self,
        thread_id: str,
        *,
        user_content: str,
        assistant_content: str,
        user_attachments: list[dict[str, Any]] | None = None,
        assistant_attachments: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        async with self._lock:
            payload = self._read_store_unlocked()
            thread = next(
                (
                    item
                    for item in payload["threads"]
                    if str(item.get("thread_id")) == thread_id
                ),
                None,
            )
            if thread is None:
                thread = self._create_thread_record(thread_id)
                payload["threads"].append(thread)

            preview_text = user_content.strip() or f"发送了 {len(user_attachments or [])} 张图片"
            if thread.get("title") == DEFAULT_THREAD_TITLE and preview_text:
                thread["title"] = preview_text[:14] or DEFAULT_THREAD_TITLE

            thread["preview"] = assistant_content[:28] or preview_text[:28] or DEFAULT_THREAD_PREVIEW
            thread["is_draft"] = False
            thread["updated_at"] = _now_iso()
            thread.setdefault("messages", [])
            thread["messages"].append(
                {
                    "id": str(uuid.uuid4()),
                    "role": "user",
                    "content": user_content,
                    "created_at": _now_clock(),
                    "attachments": self._normalize_attachments(user_attachments),
                }
            )
            thread["messages"].append(
                {
                    "id": str(uuid.uuid4()),
                    "role": "assistant",
                    "content": assistant_content,
                    "created_at": _now_clock(),
                    "attachments": self._normalize_attachments(assistant_attachments),
                }
            )

            self._write_store_unlocked(payload)
            return deepcopy(thread)


thread_store = ThreadStore()
