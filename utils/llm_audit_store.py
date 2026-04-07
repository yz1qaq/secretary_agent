from __future__ import annotations

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Any

import tiktoken

from utils.logger import get_project_logger


ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
AUDIT_LOG_FILE = DATA_DIR / "llm_interactions.jsonl"

audit_logger = get_project_logger("llm_audit", "llm_audit.log")


def _now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _get_encoding(model_name: str):
    try:
        return tiktoken.encoding_for_model(model_name)
    except KeyError:
        return tiktoken.get_encoding("cl100k_base")


def count_text_tokens(text: str, model_name: str) -> int:
    encoding = _get_encoding(model_name)
    return len(encoding.encode(text or ""))


def serialize_tool(tool: Any) -> dict[str, Any]:
    args_schema = getattr(tool, "args_schema", None)
    schema_payload: dict[str, Any] | None = None
    if args_schema is not None:
        if hasattr(args_schema, "model_json_schema"):
            schema_payload = args_schema.model_json_schema()
        elif hasattr(args_schema, "schema"):
            schema_payload = args_schema.schema()

    return {
        "name": str(getattr(tool, "name", tool.__class__.__name__)),
        "description": str(getattr(tool, "description", "")).strip(),
        "args_schema": schema_payload or {},
    }


def serialize_message_content(content: Any) -> Any:
    if isinstance(content, str):
        return content

    if not isinstance(content, list):
        return str(content)

    serialized_blocks: list[dict[str, Any]] = []
    for block in content:
        if not isinstance(block, dict):
            serialized_blocks.append({"type": "text", "text": str(block)})
            continue

        block_type = str(block.get("type") or "")
        if block_type == "image_url":
            image_url = block.get("image_url") or {}
            url = str(image_url.get("url") or "")
            serialized_blocks.append(
                {
                    "type": "image_url",
                    "data_url_preview": url[:120],
                    "data_url_length": len(url),
                }
            )
            continue

        serialized_blocks.append(block)

    return serialized_blocks


def render_message_content_for_count(content: Any) -> str:
    if isinstance(content, str):
        return content

    if not isinstance(content, list):
        return str(content)

    lines: list[str] = []
    for block in content:
        if not isinstance(block, dict):
            lines.append(str(block))
            continue

        block_type = str(block.get("type") or "")
        if block_type == "text":
            lines.append(str(block.get("text") or ""))
        elif block_type == "image_url":
            image_url = block.get("image_url") or {}
            url = str(image_url.get("url") or "")
            lines.append(f"[图片附件，data_url长度={len(url)}]")
        else:
            lines.append(json.dumps(block, ensure_ascii=False))
    return "\n".join(line for line in lines if line).strip()


def build_prompt_snapshot_text(
    *,
    system_prompt: str,
    tools: list[dict[str, Any]],
    input_messages: list[dict[str, Any]],
) -> str:
    tool_lines: list[str] = []
    for tool in tools:
        schema_text = json.dumps(tool.get("args_schema") or {}, ensure_ascii=False)
        tool_lines.append(
            f"- 工具名：{tool.get('name', '')}\n  描述：{tool.get('description', '')}\n  参数：{schema_text}"
        )

    message_lines: list[str] = []
    for message in input_messages:
        role = str(message.get("role") or "")
        content_text = render_message_content_for_count(message.get("content"))
        message_lines.append(f"[{role}]\n{content_text}")

    return "\n\n".join(
        part
        for part in [
            f"[System Prompt]\n{system_prompt.strip()}",
            "[Tools]\n" + ("\n".join(tool_lines) if tool_lines else "无工具"),
            "[Input Messages]\n" + ("\n\n".join(message_lines) if message_lines else "无输入"),
        ]
        if part.strip()
    ).strip()


class LLMAuditStore:
    def __init__(self, file_path: Path = AUDIT_LOG_FILE) -> None:
        self.file_path = file_path
        self._lock = asyncio.Lock()

    async def append_record(self, payload: dict[str, Any]) -> None:
        async with self._lock:
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            with self.file_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(payload, ensure_ascii=False) + "\n")

    async def record_interaction(
        self,
        *,
        timestamp: str | None,
        thread_id: str,
        request_kind: str,
        model_name: str,
        base_url: str,
        system_prompt: str,
        input_messages: list[dict[str, Any]],
        tools: list[Any],
        reply: str,
        duration_ms: int,
    ) -> None:
        serialized_tools = [serialize_tool(tool) for tool in tools]
        serialized_messages = [
            {
                "role": str(message.get("role") or ""),
                "content": serialize_message_content(message.get("content")),
            }
            for message in input_messages
        ]
        prompt_snapshot_text = build_prompt_snapshot_text(
            system_prompt=system_prompt,
            tools=serialized_tools,
            input_messages=input_messages,
        )

        prompt_tokens = count_text_tokens(prompt_snapshot_text, model_name)
        completion_tokens = count_text_tokens(reply, model_name)

        await self.append_record(
            {
                "timestamp": timestamp or _now_iso(),
                "thread_id": thread_id,
                "request_kind": request_kind,
                "model": {
                    "model_name": model_name,
                    "base_url": base_url,
                },
                "duration_ms": duration_ms,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens,
                "system_prompt": system_prompt,
                "tools": serialized_tools,
                "input_messages": serialized_messages,
                "prompt_snapshot_text": prompt_snapshot_text,
                "reply": reply,
            }
        )

        audit_logger.info(
            "interaction recorded: thread_id=%s request_kind=%s prompt_tokens=%s completion_tokens=%s total=%s",
            thread_id,
            request_kind,
            prompt_tokens,
            completion_tokens,
            prompt_tokens + completion_tokens,
        )


llm_audit_store = LLMAuditStore()
