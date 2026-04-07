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
        "description": "控制今日计划页面的聚合视图。这里只展示今天的学习计划和生活计划，不维护明日或长期内容。",
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
        "description": "控制学习区域。该区域包含今日学习计划、明日学习计划、长期学习计划三个抽屉，以及学习概览卡片和页面文案。",
        "allowed_exports": [
            "studyWorkspaceCopy",
            "studyOverviewStats",
            "studyTodayPlan",
            "studyTomorrowPlan",
            "studyLongTermPlan",
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
        "description": "控制生活区域。该区域包含今日生活计划、明日生活计划、长期生活计划三个抽屉，以及生活概览卡片和页面文案。",
        "allowed_exports": [
            "lifeWorkspaceCopy",
            "lifeOverviewStats",
            "lifeTodayPlan",
            "lifeTomorrowPlan",
            "lifeLongTermPlan",
            "LifePanel",
        ],
    },
    {
        "region_id": "settings-panel",
        "label": "设置区域",
        "file_path": PROJECT_ROOT
        / "frontend"
        / "src"
        / "dashboard"
        / "regions"
        / "SettingsPanel.tsx",
        "description": "控制设置页。该区域展示模型配置、短期记忆、中期记忆，以及长期记忆中的用户画像和 Agent 画像表单。",
        "allowed_exports": [
            "settingsWorkspaceCopy",
            "SettingsPanel",
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
