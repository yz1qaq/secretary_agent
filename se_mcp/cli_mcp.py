# 把命令行工具封装为mcp
import subprocess
import shlex
from mcp.server.fastmcp import FastMCP
from typing import Annotated
from pydantic import Field

mcp = FastMCP()


@mcp.tool(name="run_cli", description="运行命令行工具")
def run_cli_command(
    command: Annotated[
        str,
        Field(
            description="""要运行的命令行工具。""",
            examples=["ls -al", "mv file1 file2"],
        ),
    ],
) -> str:
    try:
        args = shlex.split(command)
        if args[0] == "rm":
            raise Exception("不允许使用rm")
        res = subprocess.run(command, shell=True, capture_output=True, text=True)
        if res.returncode != 0:
            return f"{res.returncode}: {res.stderr}"
        return res.stdout
    except Exception as e:
        return str(e)


# def run_cli_command_popen(command:str) -> str:
#     p = subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,shell=True)
#     stdout,stderr = p.communicate()
#     if stdout:
#         return stdout
#     return stderr


if __name__ == "__main__":
    # print("clo_tools.py 测试：")
    # command = "rm -rf"
    # ret = run_cli_command(command=command)
    # print(ret)
    # com = input("开始测试输入：")
    # ret = run_cli_command(command=com)
    # print(ret)
    mcp.run(transport="stdio")
