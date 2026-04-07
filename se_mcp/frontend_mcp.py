import re
import subprocess
from pathlib import Path
from typing import Annotated
import sys

from mcp.server.fastmcp import FastMCP
from pydantic import Field

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from utils.frontend_regions import (
    PROJECT_ROOT,
    FRONTEND_REGION_REGISTRY,
    get_frontend_region,
    serialize_frontend_region,
)


mcp = FastMCP()
FRONTEND_ROOT = PROJECT_ROOT / "frontend"


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _write_text(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def _ensure_allowed_exports(region: dict, source: str) -> None:
    """局部改前端时强制保留关键导出，避免 agent 一次修改把区域接口改丢。"""
    for export_name in region["allowed_exports"]:
        export_pattern = re.compile(
            rf"export\s+(const|function)\s+{re.escape(export_name)}\b"
        )
        if not export_pattern.search(source):
            raise ValueError(
                f"区域 {region['region_id']} 缺少必需导出: {export_name}"
            )


def _run_frontend_build() -> tuple[bool, str]:
    """所有源码修改最终都以真实构建结果为准，而不是只看语法替换是否成功。"""
    result = subprocess.run(
        ["npm", "run", "build"],
        cwd=FRONTEND_ROOT,
        capture_output=True,
        text=True,
    )
    output = (result.stdout or "") + (result.stderr or "")
    return result.returncode == 0, output.strip()


@mcp.tool(name="list_frontend_regions", description="列出允许编辑的前端白名单区域")
def list_frontend_regions() -> dict:
    return {
        "regions": [
            serialize_frontend_region(region) for region in FRONTEND_REGION_REGISTRY
        ]
    }


@mcp.tool(name="read_frontend_region", description="读取指定前端区域源码与约束")
def read_frontend_region(
    region_id: Annotated[str, Field(description="前端区域 ID")]
) -> dict:
    region = get_frontend_region(region_id)
    source = _read_text(region["file_path"])
    return {
        **serialize_frontend_region(region),
        "source": source,
        "constraints": [
            "只能修改当前白名单区域文件。",
            "必须保留 allowed_exports 中列出的导出。",
            "保存后默认需要通过 frontend/npm run build 校验。",
        ],
    }


@mcp.tool(
    name="validate_frontend_region_change",
    description="校验当前前端区域所在项目是否能正常构建",
)
def validate_frontend_region_change(
    region_id: Annotated[str, Field(description="前端区域 ID")]
) -> dict:
    region = get_frontend_region(region_id)
    build_passed, output = _run_frontend_build()
    message = "frontend build 通过" if build_passed else output or "frontend build 失败"
    return {
        "success": build_passed,
        "region_id": region["region_id"],
        "file_path": str(region["file_path"]),
        "build_passed": build_passed,
        "message": message,
    }


@mcp.tool(
    name="update_frontend_region",
    description="更新指定前端白名单区域源码，并在需要时执行构建校验，失败自动回滚",
)
def update_frontend_region(
    region_id: Annotated[str, Field(description="前端区域 ID")],
    new_source: Annotated[str, Field(description="新的完整区域源码")],
    validate: Annotated[bool, Field(description="是否执行构建校验")] = True,
) -> dict:
    """前端白名单区域更新入口：先替换文件，再构建校验，失败时自动回滚。"""
    region = get_frontend_region(region_id)
    file_path = region["file_path"]
    original_source = _read_text(file_path)

    _ensure_allowed_exports(region, new_source)
    _write_text(file_path, new_source)

    if not validate:
        return {
            "success": True,
            "region_id": region["region_id"],
            "file_path": str(file_path),
            "build_passed": False,
            "message": "区域源码已更新，未执行构建校验。",
        }

    build_passed, output = _run_frontend_build()
    if build_passed:
        return {
            "success": True,
            "region_id": region["region_id"],
            "file_path": str(file_path),
            "build_passed": True,
            "message": "区域源码已更新，frontend build 通过。",
        }

    _write_text(file_path, original_source)
    return {
        "success": False,
        "region_id": region["region_id"],
        "file_path": str(file_path),
        "build_passed": False,
        "message": output or "frontend build 失败，已自动回滚。",
    }


if __name__ == "__main__":
    mcp.run(transport="stdio")
