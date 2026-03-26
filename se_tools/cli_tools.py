import sys

from utils.mcp import create_mcp_stdio_client


async def get_stdio_cli_tools():
    params = {
        "command": sys.executable,
        "args":[
            "/Users/yz1/Learn/secretary_agent/se_mcp/cli_mcp.py"
        ]
    }

    client,tools = await create_mcp_stdio_client("cli_tools",params)

    return tools

if __name__== "__main__":
    print("tools.cli_tools.py!")
