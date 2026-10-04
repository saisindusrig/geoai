"""Subscription plan definitions and limit keys."""

from __future__ import annotations

PLAN_FREE = "free"
PLAN_PRO = "pro"
PLAN_ADMIN = "admin"

LIMIT_MAX_PROJECTS = "max_projects"
LIMIT_MAX_SCENARIOS_PER_PROJECT = "max_scenarios_per_project"
LIMIT_MAX_GENERATIONS_PER_DAY = "max_generations_per_day"
LIMIT_MAX_LLM_PLANS_PER_DAY = "max_llm_plans_per_day"
LIMIT_MAX_EXPORTS_PER_DAY = "max_exports_per_day"
LIMIT_MAX_FILE_DOWNLOADS_PER_DAY = "max_file_downloads_per_day"
LIMIT_MAX_SITE_ANALYSES_PER_DAY = "max_site_analyses_per_day"

# None value = unlimited for that limit
PLAN_LIMITS: dict[str, dict[str, int | None]] = {
    PLAN_FREE: {
        LIMIT_MAX_PROJECTS: 3,
        LIMIT_MAX_SCENARIOS_PER_PROJECT: 10,
        LIMIT_MAX_GENERATIONS_PER_DAY: 10,
        LIMIT_MAX_LLM_PLANS_PER_DAY: 5,
        LIMIT_MAX_EXPORTS_PER_DAY: 10,
        LIMIT_MAX_FILE_DOWNLOADS_PER_DAY: 50,
        LIMIT_MAX_SITE_ANALYSES_PER_DAY: 10,
    },
    PLAN_PRO: {
        LIMIT_MAX_PROJECTS: 25,
        LIMIT_MAX_SCENARIOS_PER_PROJECT: 50,
        LIMIT_MAX_GENERATIONS_PER_DAY: 100,
        LIMIT_MAX_LLM_PLANS_PER_DAY: 50,
        LIMIT_MAX_EXPORTS_PER_DAY: 100,
        LIMIT_MAX_FILE_DOWNLOADS_PER_DAY: 500,
        LIMIT_MAX_SITE_ANALYSES_PER_DAY: 200,
    },
    PLAN_ADMIN: {
        LIMIT_MAX_PROJECTS: None,
        LIMIT_MAX_SCENARIOS_PER_PROJECT: None,
        LIMIT_MAX_GENERATIONS_PER_DAY: None,
        LIMIT_MAX_LLM_PLANS_PER_DAY: None,
        LIMIT_MAX_EXPORTS_PER_DAY: None,
        LIMIT_MAX_FILE_DOWNLOADS_PER_DAY: None,
        LIMIT_MAX_SITE_ANALYSES_PER_DAY: None,
    },
}

DAILY_EVENT_TYPES = frozenset(
    {
        "generation.started",
        "llm.plan",
        "export.pdf",
        "export.csv",
        "export.dxf",
        "export.json",
        "file.download",
        "site_analysis.run",
    }
)

EVENT_TO_LIMIT: dict[str, str] = {
    "project.create": LIMIT_MAX_PROJECTS,
    "scenario.created": LIMIT_MAX_SCENARIOS_PER_PROJECT,
    "generation.started": LIMIT_MAX_GENERATIONS_PER_DAY,
    "llm.plan": LIMIT_MAX_LLM_PLANS_PER_DAY,
    "export.pdf": LIMIT_MAX_EXPORTS_PER_DAY,
    "export.csv": LIMIT_MAX_EXPORTS_PER_DAY,
    "export.dxf": LIMIT_MAX_EXPORTS_PER_DAY,
    "export.json": LIMIT_MAX_EXPORTS_PER_DAY,
    "file.download": LIMIT_MAX_FILE_DOWNLOADS_PER_DAY,
    "site_analysis.run": LIMIT_MAX_SITE_ANALYSES_PER_DAY,
}
