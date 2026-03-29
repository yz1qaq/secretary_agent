from pathlib import Path
import sys

from utils.mcp import create_mcp_stdio_client


PROJECT_ROOT = Path(__file__).resolve().parent.parent
FRONTEND_MCP_PATH = PROJECT_ROOT / "se_mcp" / "frontend_mcp.py"


async def get_stdio_frontend_tools():
    params = {
        "command": sys.executable,
        "args": [str(FRONTEND_MCP_PATH)],
        "cwd": str(PROJECT_ROOT),
    }

    client, tools = await create_mcp_stdio_client("frontend_tools", params)

    return tools


if __name__ == "__main__":
    print("tools.frontend_tools.py!")
