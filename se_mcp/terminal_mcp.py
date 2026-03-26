import subprocess

from mcp.server.fastmcp import FastMCP

import time
import re
from typing import List

mcp = FastMCP()


def run_applescript(script):
    p = subprocess.Popen(
        ["osascript", "-e", script], stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    output, err = p.communicate()
    return output.decode("utf-8").strip(), err.decode("utf-8").strip()


# def close_terminal_if_open():
#     run_applescript("""
#     tell application "Terminal"
#         if it is running then
#             close front window
#         end if
#     end tell
#     """)


@mcp.tool(name="close_terminal_if_open", description="如果终端打开就关闭掉")
def close_terminal_if_open(args: str = "") -> bool:
    terminal_content, error = run_applescript("""
tell application "System Events"
    if exists process "Terminal" then
        tell application "Terminal" to quit
    end if
end tell
""")
    if error:
        return False
    else:
        return True


@mcp.tool(name="open_new_terminal", description="打开一个新的终端窗口，返回窗口ID")
def open_new_terminal(args: str = "") -> str:
    terminal_content, error = run_applescript("""
tell application "Terminal"
    if (count of windows) > 0 then
        activate
    else
        activate
    end if
end tell
""")
    time.sleep(5)  # 等待5秒钟，Terminal打开需要一段时间
    if error:
        return error
    else:
        if terminal_content.strip() == "":
            return get_all_terminal_window_ids()[0]
        else:
            return terminal_content


def get_all_terminal_window_ids(args=None):
    script = """
tell application "Terminal"
    set outputList to {}
    repeat with aWindow in windows
        set windowID to id of aWindow
        set tabCount to number of tabs of aWindow
        repeat with tabIndex from 1 to tabCount
            set end of outputList to {tab tabIndex of window id windowID}
        end repeat
    end repeat
end tell
return outputList
"""
    terminal_content, error = run_applescript(script)
    if error:
        return error
    else:
        # 检查字符串中是否包含逗号
        if "," in terminal_content:
            # 将字符串按逗号分割成列表
            list_data = terminal_content.split(",")
            list_data = [item.strip() for item in list_data]
        else:
            # 如果不包含逗号，将整个字符串作为一个元素放入列表
            list_data = [terminal_content.strip()]
        return list_data


@mcp.tool(name="get_terminal_full_text", description="获取当前终端窗口的所有文本内容")
def get_terminal_full_text(args: str = "") -> str:
    terminal_content, error = run_applescript("""
tell application "Terminal"
    set fullText to history of selected tab of front window
end tell
""")
    if error:
        return error
    else:
        return terminal_content


@mcp.tool(
    name="run_script_in_exist_terminal", description="在已存在的终端窗口中运行脚本"
)
def run_script_in_exist_terminal(command: str) -> str:
    command = clean_bash_tags(command)  # 清除markdown字符串
    print("\nrun_script_in_exist_terminal command:")
    print(command)
    print("-" * 50)
    terminal_content, error = run_applescript(f'''
tell application "Terminal"
    activate
    if (count of windows) > 0 then
        do script "{command}" in window 1
    else
        do script "{command}"
    end if
end tell
''')
    if error:
        return error
    else:
        return terminal_content


def clean_bash_tags(s):
    # 同时匹配开头和结尾的标记及周围可能的空白（包括换行符）
    s = re.sub(r"^\s*```bash\s*", "", s, flags=re.DOTALL)  # 去开头
    s = re.sub(r"^\s*```shell\s*", "", s, flags=re.DOTALL)  # 去开头
    s = re.sub(r"\s*```\s*$", "", s, flags=re.DOTALL)  # 去结尾
    return s.strip()


def parse_key_code(button):
    button = button.lower()

    keycode_map = {
        "return": "return",
        "space": "space",
        "up": 126,
        "down": 125,
        "left": 123,
        "right": 124,
        "a": 0,
        "b": 11,
        "c": 8,
        "d": 2,
        "e": 14,
        "f": 3,
        "g": 5,
        "h": 4,
        "i": 34,
        "j": 38,
        "k": 40,
        "l": 37,
        "m": 46,
        "n": 45,
        "o": 31,
        "p": 35,
        "q": 12,
        "r": 15,
        "s": 1,
        "t": 17,
        "u": 32,
        "v": 9,
        "w": 13,
        "x": 7,
        "y": 16,
        "z": 6,
        ".": 47,
        "dot": 47,
        "0": 29,
        "1": 18,
        "2": 19,
        "3": 20,
        "4": 21,
        "5": 23,
        "6": 22,
        "7": 26,
        "8": 28,
        "9": 25,
        "-": 27,
    }

    return keycode_map[button]


def concat_key_codes(key_codes):
    script = ""
    for key in key_codes:
        key_code = parse_key_code(key)
        script += f"keystroke {key_code}\n"
        script += "delay 0.5\n"
    return script.strip()


@mcp.tool(
    name="send_terminal_keyboard_key", description="向已存在的终端窗口发送键盘按键"
)
def send_terminal_keyboard_key(key_codes: List[str]) -> bool:
    print("\nsend_terminal_keyboard_key keycode:", key_codes)
    print("-" * 50)
    script = f"""
    tell application "Terminal"
        activate
        tell application "System Events"
            {concat_key_codes(key_codes)}
        end tell
    end tell
    """
    print(script)
    _, error = run_applescript(script)
    if error:
        return False
    else:
        return True


if __name__ == "__main__":
    # open_new_terminal()
    # close_terminal_if_open()
    # window_ids = get_all_terminal_window_ids()
    # print(window_ids)
    mcp.run(transport="stdio")
