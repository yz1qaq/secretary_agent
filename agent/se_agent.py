import asyncio
import json
import os
import sys
import traceback
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncIterator

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from langchain.agents import create_agent
from pydantic import BaseModel, Field

from se_tools.frontend_tools import get_stdio_frontend_tools
from se_tools.cli_tools import get_stdio_cli_tools
from se_tools.rag_tools import get_stdio_rag_tools
from se_tools.terminal_tools import get_stdio_terminal_tools
from se_tools.time_tools import get_stdio_time_tools
from se_model.llm import creat_llm
from se_model.llm_config import creat_config
from se_prompts.system_prompts import creat_system_prompt
from utils.logger import get_project_logger
from utils.memoryos import MemoryOSService
from utils.time_utils import DEFAULT_TIMEZONE, build_time_context_text
from utils.thread_store import DEFAULT_THREAD_PREVIEW, DEFAULT_THREAD_TITLE, thread_store


API_KEY = os.getenv("DASHSCOPE_API_KEY")
BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
MODEL_NAME = "qwen3.5-plus"
DEFAULT_THREAD_ID = 1
HOST =  "127.0.0.1"
PORT = 9826
MEMORY_BACKEND_NAME = "memoryos"
DEFAULT_MEMORY_USER_ID = "default_user"
SYSTEM_REFRESH_THREAD_IDS = {
    "study": "system-refresh-study",
    "life": "system-refresh-life",
}
PANEL_REFRESH_PROMPTS = {
    "study": (
        "查询今日与近期学习信息，并且使用前端工具更新前端界面中的 study-panel 区域。"
        "你必须先读取当前前端区域，再修改学习界面中的今日学习计划、明日学习计划、长期学习计划三层结构，以及学习概览卡片。"
        "保持 today 导出内容可供 today-plan-panel 聚合使用，并执行前端构建校验。"
        "不要修改其他区域。"
    ),
    "life": (
        "查询今日与近期生活信息，并且使用前端工具更新前端界面中的 life-panel 区域。"
        "你必须先读取当前前端区域，再修改生活界面中的今日生活计划、明日生活计划、长期生活计划三层结构，以及生活概览卡片。"
        "保持 today 导出内容可供 today-plan-panel 聚合使用，并执行前端构建校验。"
        "不要修改其他区域。"
    ),
}

logger = get_project_logger("secretary_agent", "secretary_agent.log")


class ChatRequest(BaseModel):
    message: str = Field(default="", description="用户发送给 AI 秘书的消息")
    thread_id: str = Field(default=DEFAULT_THREAD_ID, description="会话线程 ID")
    attachments: list["ChatAttachmentPayload"] = Field(
        default_factory=list,
        description="用户上传的图片附件",
    )


class ChatAttachmentPayload(BaseModel):
    name: str = Field(..., description="附件文件名")
    type: str = Field(..., description="附件 MIME 类型")
    size: int = Field(default=0, description="附件大小")
    content: str = Field(..., description="附件内容，通常为 data URL")


class ChatResponse(BaseModel):
    status: str
    reply: str
    thread_id: str
    checkpointer: str
    memory_backend: str | None = None


class ThreadCreateRequest(BaseModel):
    thread_id: str | None = None
    title: str = Field(default=DEFAULT_THREAD_TITLE)
    preview: str = Field(default=DEFAULT_THREAD_PREVIEW)
    is_draft: bool = Field(default=True)


class ThreadUpdateRequest(BaseModel):
    title: str | None = None
    preview: str | None = None
    is_draft: bool | None = None


class PanelRefreshRequest(BaseModel):
    panel: str = Field(..., description="需要静默刷新的面板，支持 study 或 life")


class PanelRefreshResponse(BaseModel):
    status: str
    panel: str
    message: str
    thread_id: str


def creat_se_agent(llm, tools, debug: bool, system_prompt: str, checkpointer=None):
    agent_kwargs = dict(
        model=llm,
        tools=tools,
        debug=debug,
        system_prompt=system_prompt,
    )
    if checkpointer is not None:
        agent_kwargs["checkpointer"] = checkpointer
    agent = create_agent(**agent_kwargs)
    return agent


def extract_message_text(content: Any) -> str:
    if isinstance(content, str):
        return content

    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
                continue

            if isinstance(item, dict):
                text = item.get("text")
                if isinstance(text, str):
                    parts.append(text)

        return "\n".join(part for part in parts if part).strip()

    return str(content)


def split_text_for_stream(reply: str, chunk_size: int = 2) -> list[str]:
    text = reply.strip()
    if not text:
        return []

    return [text[index : index + chunk_size] for index in range(0, len(text), chunk_size)]


def build_user_content(message: str, attachments: list[ChatAttachmentPayload]) -> str | list[dict[str, Any]]:
    if len(attachments) > 3:
        raise ValueError("最多只能同时上传 3 张图片")

    content_blocks: list[dict[str, Any]] = []
    text = message.strip()
    if text:
        content_blocks.append({"type": "text", "text": text})

    for attachment in attachments:
        if not attachment.type.startswith("image/"):
            raise ValueError(f"暂不支持的附件类型: {attachment.type}")
        if not attachment.content.startswith("data:"):
            raise ValueError(f"图片附件 {attachment.name} 缺少有效的 data URL 内容")

        content_blocks.append(
            {
                "type": "image_url",
                "image_url": {
                    "url": attachment.content,
                },
            }
        )

    if not content_blocks:
        raise ValueError("message 和 attachments 不能同时为空")

    if len(content_blocks) == 1 and content_blocks[0]["type"] == "text":
        return text

    return content_blocks


def summarize_message(message: str, max_length: int = 120) -> str:
    text = " ".join(message.strip().split())
    if len(text) <= max_length:
        return text
    return f"{text[:max_length]}..."


def summarize_attachments(attachments: list[ChatAttachmentPayload]) -> list[dict[str, Any]]:
    return [
        {
            "name": attachment.name,
            "type": attachment.type,
            "size": attachment.size,
        }
        for attachment in attachments
    ]


def build_memory_record_input(
    message: str,
    attachments: list[ChatAttachmentPayload],
) -> str:
    text = message.strip()
    if not attachments:
        return text

    attachment_names = ", ".join(attachment.name for attachment in attachments[:3])
    attachment_note = f"用户上传了{len(attachments)}张图片附件：{attachment_names}"
    if text:
        return f"{text}\n[{attachment_note}]"
    return attachment_note


def summarize_memory_results(results: dict[str, object]) -> str:
    summary_parts: list[str] = []
    for key in (
        "short_term_memory",
        "retrieved_pages",
        "retrieved_user_knowledge",
        "retrieved_assistant_knowledge",
    ):
        value = results.get(key)
        count = len(value) if isinstance(value, list) else 0
        summary_parts.append(f"{key}={count}")
    return ", ".join(summary_parts)


class SecretaryAgentService:
    def __init__(self) -> None:
        self.agent = None
        self.llm = None
        self.tools = []
        self.agent_name = "moss"
        self.memory_service: MemoryOSService | None = None
        self.memory_backend_name = MEMORY_BACKEND_NAME
        self.checkpointer_name = MEMORY_BACKEND_NAME
        self._startup_lock = asyncio.Lock()

    async def startup(self) -> None:
        async with self._startup_lock:
            if self.agent is not None:
                return

            cli_tools = await get_stdio_cli_tools()
            terminal_tools = await get_stdio_terminal_tools()
            frontend_tools = await get_stdio_frontend_tools()
            time_tools = await get_stdio_time_tools()
            try:
                rag_tools = await get_stdio_rag_tools()
            except FileNotFoundError:
                rag_tools = []
            system_prompt = creat_system_prompt(agent_name=self.agent_name)
            config = creat_config(
                api_key=API_KEY,
                base_url=BASE_URL,
                model_name=MODEL_NAME,
            )
            llm = creat_llm(config)

            self.llm = llm
            self.tools = cli_tools + terminal_tools + rag_tools + frontend_tools + time_tools
            self.memory_service = MemoryOSService(
                user_id=DEFAULT_MEMORY_USER_ID,
                assistant_id=self.agent_name,
                data_storage_path=ROOT_DIR / "data" / "memoryos",
            )

            self.agent = creat_se_agent(
                llm=self.llm,
                tools=self.tools,
                debug=False,
                system_prompt=system_prompt,
            )
            logger.info(
                "agent startup complete: memory_backend=%s cli=%d terminal=%d rag=%d frontend=%d time=%d",
                self.memory_backend_name,
                len(cli_tools),
                len(terminal_tools),
                len(rag_tools),
                len(frontend_tools),
                len(time_tools),
            )

    async def shutdown(self) -> None:
        self.agent = None
        self.llm = None
        self.tools = []
        self.memory_service = None
        self.checkpointer_name = MEMORY_BACKEND_NAME
        logger.info("agent shutdown complete")

    def create_runtime_agent(self, time_context: str, memory_context: str):
        if self.llm is None:
            raise RuntimeError("agent 运行时依赖未初始化")

        runtime_system_prompt = creat_system_prompt(
            agent_name=self.agent_name,
            current_time_context=time_context,
            current_memory_context=memory_context,
        )
        return creat_se_agent(
            llm=self.llm,
            tools=self.tools,
            debug=False,
            system_prompt=runtime_system_prompt,
        )

    async def ask(
        self,
        message: str,
        thread_id: str,
        attachments: list[ChatAttachmentPayload] | None = None,
        *,
        store_in_memory: bool = True,
    ) -> str:
        attachments = attachments or []
        user_content = build_user_content(message, attachments)
        memory_record_input = build_memory_record_input(message, attachments)
        time_context = build_time_context_text(DEFAULT_TIMEZONE)

        logger.info(
            "chat request received: thread_id=%s attachments=%d message=%s attachment_meta=%s time_context=%s",
            thread_id,
            len(attachments),
            summarize_message(message),
            json.dumps(summarize_attachments(attachments), ensure_ascii=False),
            summarize_message(time_context, 200),
        )

        await self.startup()

        if self.agent is None or self.memory_service is None:
            raise RuntimeError("agent 初始化失败")

        memory_context, memory_results = await self.memory_service.build_prompt_context(
            thread_id=thread_id,
            query=memory_record_input,
        )
        runtime_agent = self.create_runtime_agent(time_context, memory_context)
        input_messages = [{"role": "user", "content": user_content}]

        logger.info(
            "chat prompt context prepared: thread_id=%s ui_history_in_prompt=%s memory=%s",
            thread_id,
            False,
            summarize_memory_results(memory_results),
        )

        try:
            result = await runtime_agent.ainvoke(
                input={"messages": input_messages},
            )
        except Exception as exc:
            logger.error(
                "chat request failed: thread_id=%s error=%s\n%s",
                thread_id,
                str(exc),
                traceback.format_exc(),
            )
            raise

        reply = extract_message_text(result["messages"][-1].content).strip()
        if not reply:
            logger.error("chat request returned empty reply: thread_id=%s", thread_id)
            raise RuntimeError("agent 未返回有效回复")

        await thread_store.append_turn(
            thread_id=thread_id,
            user_content=message.strip(),
            assistant_content=reply,
            user_attachments=[attachment.model_dump() for attachment in attachments],
        )
        if store_in_memory:
            await self.memory_service.add_memory(
                user_input=memory_record_input,
                agent_response=reply,
                thread_id=thread_id,
                meta_data={
                    "attachments": summarize_attachments(attachments),
                },
            )

        logger.info(
            "chat request succeeded: thread_id=%s reply=%s memory_backend=%s store_in_memory=%s",
            thread_id,
            summarize_message(reply),
            self.memory_backend_name,
            store_in_memory,
        )

        return reply

    async def ask_stream(
        self,
        message: str,
        thread_id: str,
        attachments: list[ChatAttachmentPayload] | None = None,
        *,
        store_in_memory: bool = True,
    ) -> AsyncIterator[dict[str, str]]:
        attachments = attachments or []
        user_content = build_user_content(message, attachments)
        memory_record_input = build_memory_record_input(message, attachments)
        time_context = build_time_context_text(DEFAULT_TIMEZONE)

        logger.info(
            "stream request received: thread_id=%s attachments=%d message=%s attachment_meta=%s time_context=%s",
            thread_id,
            len(attachments),
            summarize_message(message),
            json.dumps(summarize_attachments(attachments), ensure_ascii=False),
            summarize_message(time_context, 200),
        )

        await self.startup()

        if self.agent is None or self.memory_service is None:
            raise RuntimeError("agent 初始化失败")

        memory_context, memory_results = await self.memory_service.build_prompt_context(
            thread_id=thread_id,
            query=memory_record_input,
        )
        runtime_agent = self.create_runtime_agent(time_context, memory_context)
        input_messages = [{"role": "user", "content": user_content}]

        logger.info(
            "stream prompt context prepared: thread_id=%s ui_history_in_prompt=%s memory=%s",
            thread_id,
            False,
            summarize_memory_results(memory_results),
        )

        final_state = None
        try:
            async for state in runtime_agent.astream(
                input={"messages": input_messages},
                stream_mode="values",
            ):
                final_state = state
        except Exception as exc:
            logger.error(
                "stream request failed: thread_id=%s error=%s\n%s",
                thread_id,
                str(exc),
                traceback.format_exc(),
            )
            raise

        if not isinstance(final_state, dict) or "messages" not in final_state:
            logger.error("stream request returned invalid final_state: thread_id=%s", thread_id)
            raise RuntimeError("agent 未返回有效流式状态")

        reply = extract_message_text(final_state["messages"][-1].content).strip()
        if not reply:
            logger.error("stream request returned empty reply: thread_id=%s", thread_id)
            raise RuntimeError("agent 未返回有效回复")

        stored_thread = await thread_store.append_turn(
            thread_id=thread_id,
            user_content=message.strip(),
            assistant_content=reply,
            user_attachments=[attachment.model_dump() for attachment in attachments],
        )
        if store_in_memory:
            await self.memory_service.add_memory(
                user_input=memory_record_input,
                agent_response=reply,
                thread_id=thread_id,
                meta_data={
                    "attachments": summarize_attachments(attachments),
                },
            )

        logger.info(
            "stream request succeeded: thread_id=%s reply=%s memory_backend=%s store_in_memory=%s",
            thread_id,
            summarize_message(reply),
            self.memory_backend_name,
            store_in_memory,
        )

        for delta in split_text_for_stream(reply):
            yield {
                "delta": delta,
                "thread_id": str(thread_id),
            }
            await asyncio.sleep(0.08)

        yield {
            "reply": reply,
            "thread_id": str(thread_id),
            "title": str(stored_thread.get("title") or DEFAULT_THREAD_TITLE),
            "preview": str(stored_thread.get("preview") or DEFAULT_THREAD_PREVIEW),
            "done": "true",
        }


agent_service = SecretaryAgentService()


@asynccontextmanager
async def lifespan(_: FastAPI):
    await agent_service.startup()
    yield
    await agent_service.shutdown()


app = FastAPI(title="secretary-agent", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def health_check():
    return {
        "status": "running",
        "message": "秘书服务正常运行",
        "checkpointer": agent_service.checkpointer_name,
        "memory_backend": agent_service.memory_backend_name,
    }


@app.get("/api/chat/threads")
async def get_chat_threads():
    return {
        "threads": await thread_store.list_threads(),
    }


@app.post("/api/chat/threads")
async def create_chat_thread(payload: ThreadCreateRequest):
    thread = await thread_store.create_thread(
        requested_thread_id=payload.thread_id,
        title=payload.title,
        preview=payload.preview,
        is_draft=payload.is_draft,
    )
    return {
        "thread_id": thread["thread_id"],
        "title": thread["title"],
        "preview": thread["preview"],
        "updated_at": thread["updated_at"],
        "is_draft": thread["is_draft"],
    }


@app.get("/api/chat/history")
async def get_chat_history(thread_id: str):
    thread = await thread_store.get_thread(thread_id)
    if thread is None:
        raise HTTPException(status_code=404, detail="thread not found")

    return {
        "thread_id": thread["thread_id"],
        "title": thread["title"],
        "preview": thread["preview"],
        "messages": thread.get("messages", []),
    }


@app.patch("/api/chat/threads/{thread_id}")
async def update_chat_thread(thread_id: str, payload: ThreadUpdateRequest):
    thread = await thread_store.update_thread(
        thread_id,
        title=payload.title,
        preview=payload.preview,
        is_draft=payload.is_draft,
    )
    if thread is None:
        raise HTTPException(status_code=404, detail="thread not found")

    return {
        "thread_id": thread["thread_id"],
        "title": thread["title"],
        "preview": thread["preview"],
        "updated_at": thread["updated_at"],
        "is_draft": thread["is_draft"],
    }


@app.delete("/api/chat/threads/{thread_id}")
async def delete_chat_thread(thread_id: str):
    deleted = await thread_store.delete_thread(thread_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="thread not found")

    return {
        "status": "success",
        "thread_id": thread_id,
    }


@app.post("/api/panel-refresh", response_model=PanelRefreshResponse)
async def panel_refresh(payload: PanelRefreshRequest):
    panel = payload.panel.strip().lower()
    if panel not in PANEL_REFRESH_PROMPTS:
        raise HTTPException(status_code=400, detail="panel 仅支持 study 或 life")

    system_thread_id = SYSTEM_REFRESH_THREAD_IDS[panel]
    system_thread_title = f"{panel} 静默刷新"
    system_thread_preview = f"{panel} 面板后台刷新记录"

    await thread_store.ensure_thread(
        system_thread_id,
        title=system_thread_title,
        preview=system_thread_preview,
        is_draft=False,
        is_hidden=True,
    )

    try:
        reply = await agent_service.ask(
            message=PANEL_REFRESH_PROMPTS[panel],
            thread_id=system_thread_id,
            attachments=[],
            store_in_memory=False,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return PanelRefreshResponse(
        status="success",
        panel=panel,
        message=reply,
        thread_id=system_thread_id,
    )


@app.post("/", response_model=ChatResponse)
async def chat(payload: ChatRequest):
    try:
        reply = await agent_service.ask(
            message=payload.message,
            thread_id=str(payload.thread_id),
            attachments=payload.attachments,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return ChatResponse(
        status="success",
        reply=reply,
        thread_id=str(payload.thread_id),
        checkpointer=agent_service.checkpointer_name,
        memory_backend=agent_service.memory_backend_name,
    )


@app.post("/api/chat")
async def chat_v2(payload: ChatRequest):
    try:
        reply = await agent_service.ask(
            message=payload.message,
            thread_id=str(payload.thread_id),
            attachments=payload.attachments,
        )
        thread = await thread_store.get_thread(str(payload.thread_id))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return {
        "thread_id": str(payload.thread_id),
        "title": thread["title"] if thread else DEFAULT_THREAD_TITLE,
        "preview": thread["preview"] if thread else DEFAULT_THREAD_PREVIEW,
        "reply": reply,
        "message": {
            "id": "",
            "role": "assistant",
            "content": reply,
            "created_at": "",
            "attachments": [],
        },
    }


@app.post("/stream")
async def chat_stream(payload: ChatRequest):
    async def event_generator():
        try:
            async for chunk in agent_service.ask_stream(
                message=payload.message,
                thread_id=str(payload.thread_id),
                attachments=payload.attachments,
            ):
                yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
        except ValueError as exc:
            yield (
                f"data: {json.dumps({'error': str(exc)}, ensure_ascii=False)}\n\n"
            )
        except Exception as exc:
            yield (
                f"data: {json.dumps({'error': str(exc)}, ensure_ascii=False)}\n\n"
            )

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.post("/api/chat/stream")
async def chat_stream_v2(payload: ChatRequest):
    return await chat_stream(payload)


if __name__ == "__main__":
    uvicorn.run(app, host=HOST, port=PORT)
