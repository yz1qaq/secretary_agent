import sys
from pathlib import Path
from typing import Annotated

from mcp.server.fastmcp import FastMCP
from pydantic import Field

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from utils.logger import get_project_logger
from utils.time_utils import DEFAULT_TIMEZONE, get_current_datetime_payload, resolve_timezone


mcp = FastMCP()
logger = get_project_logger("time_mcp", "time_mcp.log")


@mcp.tool(name="get_current_datetime", description="获取当前日期、时间、星期和时区信息")
def get_current_datetime(
    timezone: Annotated[
        str,
        Field(description="IANA 时区名称，默认 Asia/Shanghai"),
    ] = DEFAULT_TIMEZONE,
) -> dict[str, str]:
    resolved_timezone = resolve_timezone(timezone)
    payload = get_current_datetime_payload(resolved_timezone)
    logger.info(
        "get_current_datetime called: requested_timezone=%s resolved_timezone=%s result=%s",
        timezone,
        resolved_timezone,
        payload["display_text"],
    )
    return payload


if __name__ == "__main__":
    mcp.run(transport="stdio")

