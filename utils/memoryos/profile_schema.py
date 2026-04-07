import re
from typing import Any, Literal

from .utils import dedupe_preserve_order, excerpt


ProfileKind = Literal["user", "assistant"]

USER_PROFILE_FIELDS = {
    "name": "姓名",
    "alias": "称呼偏好",
    "role": "身份角色",
    "school": "学校",
    "major": "专业方向",
    "grade_or_stage": "年级阶段",
    "advisor": "导师",
    "goals": "目标",
    "preferences": "偏好",
    "constraints": "约束",
    "notes": "备注",
}

ASSISTANT_PROFILE_FIELDS = {
    "name": "名称",
    "role": "角色",
    "tone": "语气风格",
    "core_responsibilities": "核心职责",
    "response_style": "回复风格",
    "tool_usage_style": "工具使用方式",
    "boundaries": "边界原则",
    "notes": "备注",
}

DEFAULT_ASSISTANT_INFERRED_PROFILE = {
    "name": "Moss",
    "role": "AI 秘书",
    "tone": "温和、可靠、执行导向",
    "core_responsibilities": "帮助用户统筹学习、生活、前端界面与工具执行任务。",
    "response_style": "先判断任务目标，再调用合适工具，最后给出清晰结论和下一步建议。",
    "tool_usage_style": "遇到真实状态问题优先调用工具，不凭空猜测，不把 RAG 当实时事实。",
    "boundaries": "不跳过验证，不把未执行的操作说成已经完成，需要校验的结果要先确认。",
    "notes": "",
}


def get_profile_fields(kind: ProfileKind) -> dict[str, str]:
    return USER_PROFILE_FIELDS if kind == "user" else ASSISTANT_PROFILE_FIELDS


def blank_profile(kind: ProfileKind) -> dict[str, str]:
    return {field: "" for field in get_profile_fields(kind)}


def normalize_profile(kind: ProfileKind, raw_profile: Any) -> dict[str, str]:
    normalized = blank_profile(kind)
    if not isinstance(raw_profile, dict):
        return normalized

    for field in normalized:
        value = raw_profile.get(field, "")
        normalized[field] = str(value).strip() if value is not None else ""
    return normalized


def profile_has_values(profile: dict[str, str]) -> bool:
    return any(str(value or "").strip() for value in profile.values())


def merge_profiles(
    kind: ProfileKind,
    manual_profile: dict[str, str],
    inferred_profile: dict[str, str],
) -> dict[str, str]:
    manual = normalize_profile(kind, manual_profile)
    inferred = normalize_profile(kind, inferred_profile)
    merged = blank_profile(kind)

    for field in merged:
        merged[field] = manual[field] or inferred[field]
    return merged


def render_profile_text(kind: ProfileKind, profile: dict[str, str]) -> str:
    normalized = normalize_profile(kind, profile)
    labels = get_profile_fields(kind)
    lines = [
        f"- {labels[field]}：{value}"
        for field, value in normalized.items()
        if value
    ]
    if not lines:
        return ""

    title = "用户长期画像" if kind == "user" else "AI 秘书长期画像"
    return f"{title}：\n" + "\n".join(lines)


def legacy_profile_to_inferred(kind: ProfileKind, profile_text: str) -> dict[str, str]:
    normalized = blank_profile(kind)
    clean = str(profile_text or "").strip()
    if not clean:
        if kind == "assistant":
            return normalize_profile("assistant", DEFAULT_ASSISTANT_INFERRED_PROFILE)
        return normalized

    normalized["notes"] = clean
    if kind == "assistant":
        for field, value in DEFAULT_ASSISTANT_INFERRED_PROFILE.items():
            if field in normalized and not normalized[field]:
                normalized[field] = value
    return normalized


def _collect_lines_by_keywords(lines: list[str], keywords: tuple[str, ...], limit: int = 4) -> str:
    matched = [line for line in lines if any(keyword in line for keyword in keywords)]
    if not matched:
        return ""
    return "；".join(dedupe_preserve_order(matched)[:limit])


def infer_user_profile_from_knowledge(knowledge_items: list[dict[str, Any]]) -> dict[str, str]:
    profile = blank_profile("user")
    lines = [
        str(item.get("knowledge") or "").strip()
        for item in knowledge_items
        if isinstance(item, dict) and str(item.get("knowledge") or "").strip()
    ]
    if not lines:
        return profile

    joined = "\n".join(lines)

    name_match = re.search(r"(?:我叫|我是|名字是)([A-Za-z\u4e00-\u9fff·]{2,20})", joined)
    alias_match = re.search(r"(?:你可以叫我|叫我)([A-Za-z\u4e00-\u9fff·]{1,20})", joined)
    school_match = re.search(r"([A-Za-z\u4e00-\u9fff]{2,24}(?:大学|学院|学校))", joined)
    major_match = re.search(r"(?:专业|研究方向|方向)[:：]?\s*([A-Za-z\u4e00-\u9fff]{2,30})", joined)
    advisor_match = re.search(r"(?:导师|指导老师)[:：]?\s*([A-Za-z\u4e00-\u9fff]{2,20})", joined)
    stage_match = re.search(r"(大一|大二|大三|大四|研一|研二|研三|博一|博二|博三)", joined)

    if name_match:
        profile["name"] = name_match.group(1)
    if alias_match:
        profile["alias"] = alias_match.group(1)
    if school_match:
        profile["school"] = school_match.group(1)
    if major_match:
        profile["major"] = major_match.group(1)
    if advisor_match:
        profile["advisor"] = advisor_match.group(1)
    if stage_match:
        profile["grade_or_stage"] = stage_match.group(1)

    if "研究生" in joined:
        profile["role"] = "研究生"
    elif "学生" in joined:
        profile["role"] = "学生"
    elif "老师" in joined:
        profile["role"] = "教师"

    profile["goals"] = _collect_lines_by_keywords(
        lines, ("目标", "计划", "希望", "准备", "打算", "要做", "推进")
    )
    profile["preferences"] = _collect_lines_by_keywords(
        lines, ("喜欢", "偏好", "习惯", "倾向", "更想", "通常会")
    )
    profile["constraints"] = _collect_lines_by_keywords(
        lines, ("不要", "不能", "避免", "受限", "截止", "DDL", "ddl", "来不及")
    )

    if not profile["notes"]:
        profile["notes"] = "\n".join(dedupe_preserve_order(lines)[-4:])

    return profile


def infer_assistant_profile_from_knowledge(knowledge_items: list[dict[str, Any]]) -> dict[str, str]:
    profile = normalize_profile("assistant", DEFAULT_ASSISTANT_INFERRED_PROFILE)
    lines = [
        str(item.get("knowledge") or "").strip()
        for item in knowledge_items
        if isinstance(item, dict) and str(item.get("knowledge") or "").strip()
    ]
    if lines:
        profile["notes"] = "\n".join(dedupe_preserve_order(lines)[-4:])

        response_style = _collect_lines_by_keywords(
            lines, ("建议", "可以", "应该", "先", "然后", "最后"), limit=3
        )
        if response_style:
            profile["response_style"] = excerpt(response_style, 200)

    return profile

