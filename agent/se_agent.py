import asyncio
import json
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncIterator

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



ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from se_model.llm import creat_llm
from se_model.llm_config import creat_config
from se_prompts.system_prompts import creat_system_prompt
from se_tools.cli_tools import get_stdio_cli_tools


API_KEY = os.getenv("DASHSCOPE_API_KEY")
BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
MODEL_NAME = "qwen3.5-plus"
DEFAULT_THREAD_ID = 1
MONGO_URI = "mongodb://localhost:27017"
MONGO_DB_NAME =  "docker"
HOST =  "127.0.0.1"
PORT = 9826


class ChatRequest(BaseModel):
    message: str = Field(..., description="用户发送给 AI 秘书的消息")
    thread_id: str = Field(default=DEFAULT_THREAD_ID, description="会话线程 ID")


class ChatResponse(BaseModel):
    status: str
    reply: str
    thread_id: str
    checkpointer: str


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


class SecretaryAgentService:
    def __init__(self) -> None:
        self.agent = None
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
            system_prompt = creat_system_prompt(agent_name="moss")
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

            self.agent = creat_se_agent(
                llm=llm,
                tools=cli_tools+terminal_tools,
                checkpointer=self.checkpointer,
                debug=False,
                system_prompt=system_prompt,
            )

    async def shutdown(self) -> None:
        if self._mongo_context is not None:
            self._mongo_context.__exit__(None, None, None)
            self._mongo_context = None

        self.agent = None
        self.checkpointer = None
        self.checkpointer_name = "unknown"

    async def ask(self, message: str, thread_id: str) -> str:
        if not message.strip():
            raise ValueError("message 不能为空")

        await self.startup()

        if self.agent is None:
            raise RuntimeError("agent 初始化失败")

        result = await self.agent.ainvoke(
            input={"messages": [{"role": "user", "content": message}]},
            config=RunnableConfig(configurable={"thread_id": thread_id}),
        )

        reply = extract_message_text(result["messages"][-1].content).strip()
        if not reply:
            raise RuntimeError("agent 未返回有效回复")

        return reply

    async def ask_stream(self, message: str, thread_id: str) -> AsyncIterator[dict[str, str]]:
        if not message.strip():
            raise ValueError("message 不能为空")

        await self.startup()

        if self.agent is None:
            raise RuntimeError("agent 初始化失败")

        final_state = None
        async for state in self.agent.astream(
            input={"messages": [{"role": "user", "content": message}]},
            config=RunnableConfig(configurable={"thread_id": thread_id}),
            stream_mode="values",
        ):
            final_state = state

        if not isinstance(final_state, dict) or "messages" not in final_state:
            raise RuntimeError("agent 未返回有效流式状态")

        reply = extract_message_text(final_state["messages"][-1].content).strip()
        if not reply:
            raise RuntimeError("agent 未返回有效回复")

        for delta in split_text_for_stream(reply):
            yield {
                "delta": delta,
                "thread_id": str(thread_id),
            }
            await asyncio.sleep(0.08)

        yield {
            "reply": reply,
            "thread_id": str(thread_id),
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


@app.post("/", response_model=ChatResponse)
async def chat(payload: ChatRequest):
    try:
        reply = await agent_service.ask(
            message=payload.message,
            thread_id=str(payload.thread_id),
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


@app.post("/stream")
async def chat_stream(payload: ChatRequest):
    async def event_generator():
        try:
            async for chunk in agent_service.ask_stream(
                message=payload.message,
                thread_id=str(payload.thread_id),
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


if __name__ == "__main__":
    uvicorn.run(app, host=HOST, port=PORT)
