from utils.mcp import create_mcp_stdio_client


async def get_stdio_terminal_tools():
    params = {
        "command": "python",
        "args": [
            "/Users/yz1/Learn/secretary_agent/se_mcp/terminal_mcp.py",
        ],
    }

    client, tools = await create_mcp_stdio_client("terminal", params)

    return tools

if __name__== "__main__":
    print("tools.terminal_tools.py!")