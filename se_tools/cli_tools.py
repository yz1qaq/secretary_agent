from pathlib import Path
import sys

from utils.mcp import create_mcp_stdio_client

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CLI_MCP_PATH = PROJECT_ROOT / "se_mcp" / "cli_mcp.py"


async def get_stdio_cli_tools():
    params = {
        "command": sys.executable,
        "args": [str(CLI_MCP_PATH)],
        "cwd": str(PROJECT_ROOT),
    }

    client,tools = await create_mcp_stdio_client("cli_tools",params)

    return tools

if __name__== "__main__":
    print("tools.cli_tools.py!")
