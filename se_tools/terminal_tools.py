from pathlib import Path
import sys

from utils.mcp import create_mcp_stdio_client

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TERMINAL_MCP_PATH = PROJECT_ROOT / "se_mcp" / "terminal_mcp.py"


async def get_stdio_terminal_tools():
    params = {
        "command": sys.executable,
        "args": [str(TERMINAL_MCP_PATH)],
        "cwd": str(PROJECT_ROOT),
    }

    client, tools = await create_mcp_stdio_client("terminal", params)

    return tools

if __name__== "__main__":
    print("tools.terminal_tools.py!")
