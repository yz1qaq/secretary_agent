from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent


FRONTEND_REGION_REGISTRY = [
    {
        "region_id": "sidebar-nav",
        "label": "左侧导航栏",
        "file_path": PROJECT_ROOT
        / "frontend"
        / "src"
        / "dashboard"
        / "regions"
        / "SidebarNav.tsx",
        "description": "控制左侧导航栏标题和导航项。",
        "allowed_exports": ["sidebarNavItems", "SidebarNav"],
    },
    {
        "region_id": "today-plan-panel",
        "label": "今日计划区域",
        "file_path": PROJECT_ROOT
        / "frontend"
        / "src"
        / "dashboard"
        / "regions"
        / "TodayPlanPanel.tsx",
        "description": "控制今日计划页面的汇总卡片、执行清单和建议内容。",
        "allowed_exports": ["todayPlanWorkspaceCopy", "TodayPlanPanel"],
    },
    {
        "region_id": "study-panel",
        "label": "学习区域",
        "file_path": PROJECT_ROOT
        / "frontend"
        / "src"
        / "dashboard"
        / "regions"
        / "StudyPanel.tsx",
        "description": "控制学习区域的卡片、时间线和学习任务。",
        "allowed_exports": [
            "studyWorkspaceCopy",
            "studyStatCards",
            "studyTimelineEntries",
            "studyTasks",
            "StudyPanel",
        ],
    },
    {
        "region_id": "life-panel",
        "label": "生活区域",
        "file_path": PROJECT_ROOT
        / "frontend"
        / "src"
        / "dashboard"
        / "regions"
        / "LifePanel.tsx",
        "description": "控制生活区域的卡片、健身计划和生活提醒。",
        "allowed_exports": [
            "lifeWorkspaceCopy",
            "lifeStatCards",
            "lifeTimelineEntries",
            "lifeTasks",
            "LifePanel",
        ],
    },
]


FRONTEND_REGIONS_BY_ID = {
    region["region_id"]: region for region in FRONTEND_REGION_REGISTRY
}


def serialize_frontend_region(region: dict) -> dict:
    return {
        "region_id": region["region_id"],
        "label": region["label"],
        "file_path": str(region["file_path"]),
        "description": region["description"],
        "allowed_exports": list(region["allowed_exports"]),
    }


def get_frontend_region(region_id: str) -> dict:
    region = FRONTEND_REGIONS_BY_ID.get(region_id)
    if region is None:
        raise ValueError(f"未知的前端区域: {region_id}")
    return region

