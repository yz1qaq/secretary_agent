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
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from langchain.agents import create_agent
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.mongodb import MongoDBSaver
from pydantic import BaseModel, Field

from se_tools.terminal_tools import get_stdio_terminal_tools
from se_tools.rag_tools import get_stdio_rag_tools
from se_tools.frontend_tools import get_stdio_frontend_tools
from se_tools.time_tools import get_stdio_time_tools

from se_model.llm import creat_llm
from se_model.llm_config import creat_config
from se_prompts.system_prompts import creat_system_prompt
from se_tools.cli_tools import get_stdio_cli_tools
from utils.logger import get_project_logger
from utils.time_utils import DEFAULT_TIMEZONE, build_time_context_text
from utils.thread_store import DEFAULT_THREAD_PREVIEW, DEFAULT_THREAD_TITLE, thread_store


API_KEY = os.getenv("DASHSCOPE_API_KEY")
BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
MODEL_NAME = "qwen3.5-plus"
DEFAULT_THREAD_ID = 1
MONGO_URI = "mongodb://localhost:27017"
MONGO_DB_NAME =  "docker"
HOST =  "127.0.0.1"
PORT = 9826

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


class ThreadCreateRequest(BaseModel):
    thread_id: str | None = None
    title: str = Field(default=DEFAULT_THREAD_TITLE)
    preview: str = Field(default=DEFAULT_THREAD_PREVIEW)
    is_draft: bool = Field(default=True)


class ThreadUpdateRequest(BaseModel):
    title: str | None = None
    preview: str | None = None
    is_draft: bool | None = None


def creat_se_agent(llm, tools, checkpointer, debug: bool, system_prompt: str):
    agent = create_agent(
        model=llm,
        tools=tools,
        checkpointer=checkpointer,
        debug=debug,
        system_prompt=system_prompt,
    )
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


class SecretaryAgentService:
    def __init__(self) -> None:
        self.agent = None
        self.llm = None
        self.tools = []
        self.agent_name = "moss"
        self.checkpointer = None
        self.checkpointer_name = "unknown"
        self._mongo_context = None
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

            #默认使用mongo连接，如果有问题就使用内存存储
            try:
                self._mongo_context = MongoDBSaver.from_conn_string(
                    conn_string=MONGO_URI,
                    db_name=MONGO_DB_NAME,
                )
                self.checkpointer = self._mongo_context.__enter__()
                self.checkpointer_name = "mongodb"
            except Exception:
                self._mongo_context = None
                self.checkpointer = InMemorySaver()
                self.checkpointer_name = "memory"

            self.llm = llm
            self.tools = cli_tools + terminal_tools + rag_tools + frontend_tools + time_tools

            self.agent = creat_se_agent(
                llm=self.llm,
                tools=self.tools,
                checkpointer=self.checkpointer,
                debug=False,
                system_prompt=system_prompt,
            )
            logger.info(
                "agent startup complete: checkpointer=%s cli=%d terminal=%d rag=%d frontend=%d time=%d",
                self.checkpointer_name,
                len(cli_tools),
                len(terminal_tools),
                len(rag_tools),
                len(frontend_tools),
                len(time_tools),
            )

    async def shutdown(self) -> None:
        if self._mongo_context is not None:
            self._mongo_context.__exit__(None, None, None)
            self._mongo_context = None

        self.agent = None
        self.llm = None
        self.tools = []
        self.checkpointer = None
        self.checkpointer_name = "unknown"
        logger.info("agent shutdown complete")

    def create_runtime_agent(self, time_context: str):
        if self.llm is None or self.checkpointer is None:
            raise RuntimeError("agent 运行时依赖未初始化")

        runtime_system_prompt = creat_system_prompt(
            agent_name=self.agent_name,
            current_time_context=time_context,
        )
        return creat_se_agent(
            llm=self.llm,
            tools=self.tools,
            checkpointer=self.checkpointer,
            debug=False,
            system_prompt=runtime_system_prompt,
        )

    async def ask(
        self,
        message: str,
        thread_id: str,
        attachments: list[ChatAttachmentPayload] | None = None,
    ) -> str:
        attachments = attachments or []
        user_content = build_user_content(message, attachments)
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

        if self.agent is None:
            raise RuntimeError("agent 初始化失败")

        runtime_agent = self.create_runtime_agent(time_context)

        try:
            result = await runtime_agent.ainvoke(
                input={"messages": [{"role": "user", "content": user_content}]},
                config=RunnableConfig(configurable={"thread_id": thread_id}),
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

        logger.info(
            "chat request succeeded: thread_id=%s reply=%s",
            thread_id,
            summarize_message(reply),
        )

        return reply

    async def ask_stream(
        self,
        message: str,
        thread_id: str,
        attachments: list[ChatAttachmentPayload] | None = None,
    ) -> AsyncIterator[dict[str, str]]:
        attachments = attachments or []
        user_content = build_user_content(message, attachments)
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

        if self.agent is None:
            raise RuntimeError("agent 初始化失败")

        runtime_agent = self.create_runtime_agent(time_context)

        final_state = None
        try:
            async for state in runtime_agent.astream(
                input={"messages": [{"role": "user", "content": user_content}]},
                config=RunnableConfig(configurable={"thread_id": thread_id}),
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

        logger.info(
            "stream request succeeded: thread_id=%s reply=%s",
            thread_id,
            summarize_message(reply),
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
