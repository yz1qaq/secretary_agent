import os
from pathlib import Path
import sys

from utils.mcp import create_mcp_stdio_client


PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAG_MCP_PATH = PROJECT_ROOT / "se_mcp" / "rag_mcp.py"


async def get_stdio_rag_tools():
    if not RAG_MCP_PATH.exists():
        raise FileNotFoundError(
            f"未找到项目内的 RAG MCP 脚本: {RAG_MCP_PATH}"
        )

    params = {
        "command": sys.executable,
        "args": [str(RAG_MCP_PATH)],
        "cwd": str(PROJECT_ROOT),
        "env": {
            **os.environ,
        },
    }

    client,tools = await create_mcp_stdio_client("rag_tools",params)

    return tools



if __name__== "__main__":
    print("tools.rag_tools.py!")
