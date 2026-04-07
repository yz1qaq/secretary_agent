import asyncio
import json
import sys
import time
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
from utils.llm_audit_store import llm_audit_store
from utils.logger import get_project_logger
from utils.memoryos import MemoryOSService
from utils.model_config_store import ModelConfigStore
from utils.time_utils import DEFAULT_TIMEZONE, build_time_context_text
from utils.thread_store import DEFAULT_THREAD_PREVIEW, DEFAULT_THREAD_TITLE, thread_store


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


class ModelSettingsUpdateRequest(BaseModel):
    base_url: str = Field(..., description="模型服务的 base_url")
    api_key: str = Field(default="", description="模型服务的 api_key，留空时保持当前值")
    model_name: str = Field(..., description="模型名称")


class LongTermProfileUpdateRequest(BaseModel):
    user_manual_profile: dict[str, str] = Field(default_factory=dict)
    assistant_manual_profile: dict[str, str] = Field(default_factory=dict)


def creat_se_agent(llm, tools, debug: bool, system_prompt: str, checkpointer=None):
    """统一封装 agent 创建逻辑，避免启动期和请求期各自散落一份配置。"""
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
    """兼容 LangChain 返回的多种 message content 结构，尽量提取出可读文本。"""
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
    """把前端传来的文本和图片附件整理成模型可消费的单模态/多模态 content。"""
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


def build_model_input_messages(
    *,
    time_context: str,
    user_content: str | list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """在真正发给模型的消息体里嵌入时间上下文，给时间工具失败时再加一层兜底。"""
    if isinstance(user_content, str):
        content = (
            f"【当前时间上下文】\n{time_context}\n\n"
            f"【用户消息】\n{user_content.strip()}"
        ).strip()
        return [{"role": "user", "content": content}]

    time_block = {
        "type": "text",
        "text": f"【当前时间上下文】\n{time_context}",
    }
    content_blocks = [time_block, *user_content]
    return [{"role": "user", "content": content_blocks}]


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
    """把一次问答压成记忆侧可读文本，避免短中期记忆丢掉“用户上传过图片”这类关键信号。"""
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
        self._model_update_lock = asyncio.Lock()
        self.model_config_store = ModelConfigStore(ROOT_DIR / "data" / "model_config.json")
        self.current_model_config = None

    def _build_llm(self, *, base_url: str, api_key: str, model_name: str):
        """把配置校验和 llm 实例化收口到一起，便于启动和热更新共用一套入口。"""
        config = creat_config(
            api_key=api_key.strip(),
            base_url=base_url.strip(),
            model_name=model_name.strip(),
        )
        config.validate()
        llm = creat_llm(config)
        return llm, config

    def _build_base_agent(self):
        """构造不带运行时上下文的基础 agent，主要用于服务启动后的默认可用状态。"""
        if self.llm is None:
            raise RuntimeError("llm 未初始化")
        system_prompt = creat_system_prompt(agent_name=self.agent_name)
        return creat_se_agent(
            llm=self.llm,
            tools=self.tools,
            debug=False,
            system_prompt=system_prompt,
        )

    def get_model_settings_payload(self) -> dict[str, object]:
        """把模型配置转成适合前端展示的结构，并统一处理 api_key 掩码。"""
        config = self.current_model_config or self.model_config_store.load_or_initialize()
        return {
            "base_url": config.base_url,
            "api_key_masked": self.model_config_store.mask_api_key(config.api_key),
            "api_key_configured": bool(config.api_key.strip()),
            "model_name": config.model_name,
        }

    async def startup(self) -> None:
        """启动时只做一次重资源初始化：工具、llm、MemoryOS 和基础 agent。"""
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
            llm, config = self._build_llm(
                **self.model_config_store.load_or_initialize().to_dict(),
            )

            self.llm = llm
            self.current_model_config = config
            self.tools = cli_tools + terminal_tools + rag_tools + frontend_tools + time_tools
            self.memory_service = MemoryOSService(
                user_id=DEFAULT_MEMORY_USER_ID,
                assistant_id=self.agent_name,
                data_storage_path=ROOT_DIR / "data" / "memoryos",
            )

            self.agent = self._build_base_agent()
            logger.info(
                "agent startup complete: memory_backend=%s model=%s base_url=%s cli=%d terminal=%d rag=%d frontend=%d time=%d",
                self.memory_backend_name,
                config.model_name,
                config.base_url,
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
        self.current_model_config = None
        self.checkpointer_name = MEMORY_BACKEND_NAME
        logger.info("agent shutdown complete")

    async def update_model_config(
        self,
        *,
        base_url: str,
        api_key: str,
        model_name: str,
    ) -> dict[str, object]:
        """热切换模型配置时原子替换 llm，保证旧请求不被打断，新请求立刻生效。"""
        await self.startup()

        current_config = self.current_model_config or self.model_config_store.load_or_initialize()
        next_api_key = api_key.strip() or current_config.api_key

        async with self._model_update_lock:
            llm, config = self._build_llm(
                base_url=base_url,
                api_key=next_api_key,
                model_name=model_name,
            )
            self.model_config_store.save(config)
            self.llm = llm
            self.current_model_config = config
            self.agent = self._build_base_agent()

        logger.info(
            "model config hot updated: model=%s base_url=%s api_key_configured=%s",
            config.model_name,
            config.base_url,
            bool(config.api_key.strip()),
        )

        return {
            "status": "success",
            "reload_applied": True,
            **self.get_model_settings_payload(),
        }

    async def get_settings_snapshot(self) -> dict[str, object]:
        """聚合设置页需要的模型配置和 MemoryOS 快照，避免前端拆成多次请求。"""
        await self.startup()
        if self.memory_service is None:
            raise RuntimeError("memory service 未初始化")

        memory_snapshot = await self.memory_service.get_memory_center_snapshot()
        return {
            "model": self.get_model_settings_payload(),
            "memory": {
                "short_term": memory_snapshot["short_term"],
                "mid_term": memory_snapshot["mid_term"],
                "long_term": memory_snapshot["long_term"],
            },
        }

    async def update_long_term_profiles(
        self,
        *,
        user_manual_profile: dict[str, str],
        assistant_manual_profile: dict[str, str],
    ) -> dict[str, object]:
        """统一更新长期记忆里的手动画像，用户画像和秘书画像走同一条保存链路。"""
        await self.startup()
        if self.memory_service is None:
            raise RuntimeError("memory service 未初始化")

        snapshot = await self.memory_service.update_manual_profiles(
            user_manual_profile=user_manual_profile,
            assistant_manual_profile=assistant_manual_profile,
        )
        logger.info("long term profiles updated")
        return {
            "status": "success",
            "long_term": snapshot,
        }

    def build_runtime_system_prompt(self, time_context: str, memory_context: str) -> str:
        """单独产出运行时 system prompt，便于实际调用和审计记录共用同一份内容。"""
        return creat_system_prompt(
            agent_name=self.agent_name,
            current_time_context=time_context,
            current_memory_context=memory_context,
        )

    def _schedule_audit_record(
        self,
        *,
        thread_id: str,
        request_kind: str,
        runtime_system_prompt: str,
        input_messages: list[dict[str, Any]],
        reply: str,
        duration_ms: int,
    ) -> None:
        """在成功得到模型回复后异步记录本次真实上下文与 token 开销，避免阻塞主响应。"""
        if self.current_model_config is None:
            return

        async def _record() -> None:
            try:
                await llm_audit_store.record_interaction(
                    timestamp=None,
                    thread_id=thread_id,
                    request_kind=request_kind,
                    model_name=self.current_model_config.model_name,
                    base_url=self.current_model_config.base_url,
                    system_prompt=runtime_system_prompt,
                    input_messages=input_messages,
                    tools=self.tools,
                    reply=reply,
                    duration_ms=duration_ms,
                )
            except Exception:
                logger.error(
                    "failed to record llm interaction: thread_id=%s\n%s",
                    thread_id,
                    traceback.format_exc(),
                )

        asyncio.create_task(_record())

    def create_runtime_agent(self, time_context: str, memory_context: str):
        """每次请求都重新拼运行时 prompt，把当前时间和记忆上下文动态注入进去。"""
        if self.llm is None:
            raise RuntimeError("agent 运行时依赖未初始化")

        runtime_system_prompt = self.build_runtime_system_prompt(time_context, memory_context)
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
        """非流式对话主链路：准备时间/记忆/多模态输入，调用 agent，再分别落线程记录和 MemoryOS。"""
        attachments = attachments or []
        user_content = build_user_content(message, attachments)
        memory_record_input = build_memory_record_input(message, attachments)
        time_context = build_time_context_text(DEFAULT_TIMEZONE)
        started_at = time.perf_counter()

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
        # 线程历史只保留给前端恢复；真正喂给模型的是 MemoryOS 检索结果和当前这轮输入。
        runtime_system_prompt = self.build_runtime_system_prompt(time_context, memory_context)
        runtime_agent = self.create_runtime_agent(time_context, memory_context)
        input_messages = build_model_input_messages(
            time_context=time_context,
            user_content=user_content,
        )

        logger.info(
            "chat prompt context prepared: thread_id=%s ui_history_in_prompt=%s embedded_time_context=%s memory=%s",
            thread_id,
            False,
            True,
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
        duration_ms = int((time.perf_counter() - started_at) * 1000)

        await thread_store.append_turn(
            thread_id=thread_id,
            user_content=message.strip(),
            assistant_content=reply,
            user_attachments=[attachment.model_dump() for attachment in attachments],
        )
        # 静默刷新等系统任务可以只写线程记录，不进入长期记忆，避免污染用户画像。
        if store_in_memory:
            await self.memory_service.add_memory(
                user_input=memory_record_input,
                agent_response=reply,
                thread_id=thread_id,
                meta_data={
                    "attachments": summarize_attachments(attachments),
                },
            )

        self._schedule_audit_record(
            thread_id=thread_id,
            request_kind="chat",
            runtime_system_prompt=runtime_system_prompt,
            input_messages=input_messages,
            reply=reply,
            duration_ms=duration_ms,
        )

        logger.info(
            "chat request succeeded: thread_id=%s reply=%s memory_backend=%s store_in_memory=%s duration_ms=%s",
            thread_id,
            summarize_message(reply),
            self.memory_backend_name,
            store_in_memory,
            duration_ms,
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
        """流式对话链路和 ask 基本一致，只是在最终回复拿到后再模拟分块输出给前端。"""
        attachments = attachments or []
        user_content = build_user_content(message, attachments)
        memory_record_input = build_memory_record_input(message, attachments)
        time_context = build_time_context_text(DEFAULT_TIMEZONE)
        started_at = time.perf_counter()

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
        # 当前 provider 不直接产出 token 级流，所以这里先完整拿到结果，再切片成前端可消费的流。
        runtime_system_prompt = self.build_runtime_system_prompt(time_context, memory_context)
        runtime_agent = self.create_runtime_agent(time_context, memory_context)
        input_messages = build_model_input_messages(
            time_context=time_context,
            user_content=user_content,
        )

        logger.info(
            "stream prompt context prepared: thread_id=%s ui_history_in_prompt=%s embedded_time_context=%s memory=%s",
            thread_id,
            False,
            True,
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
        duration_ms = int((time.perf_counter() - started_at) * 1000)

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

        self._schedule_audit_record(
            thread_id=thread_id,
            request_kind="stream",
            runtime_system_prompt=runtime_system_prompt,
            input_messages=input_messages,
            reply=reply,
            duration_ms=duration_ms,
        )

        logger.info(
            "stream request succeeded: thread_id=%s reply=%s memory_backend=%s store_in_memory=%s duration_ms=%s",
            thread_id,
            summarize_message(reply),
            self.memory_backend_name,
            store_in_memory,
            duration_ms,
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
        "model": agent_service.get_model_settings_payload(),
    }


@app.get("/api/settings")
async def get_settings():
    try:
        return await agent_service.get_settings_snapshot()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.put("/api/settings/model")
async def update_model_settings(payload: ModelSettingsUpdateRequest):
    try:
        return await agent_service.update_model_config(
            base_url=payload.base_url,
            api_key=payload.api_key,
            model_name=payload.model_name,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.put("/api/settings/long-term-profile")
async def update_long_term_profile(payload: LongTermProfileUpdateRequest):
    try:
        return await agent_service.update_long_term_profiles(
            user_manual_profile=payload.user_manual_profile,
            assistant_manual_profile=payload.assistant_manual_profile,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


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
