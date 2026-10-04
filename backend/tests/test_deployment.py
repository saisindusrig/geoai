"""Deployment configuration and production smoke script tests."""

import importlib.util
from pathlib import Path
from unittest.mock import patch

from app.core.production import production_readiness

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = Path(__file__).resolve().parents[1]


def _load_smoke_module():
    import sys

    script = BACKEND_ROOT / "scripts" / "production_smoke.py"
    spec = importlib.util.spec_from_file_location("production_smoke", script)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules["production_smoke"] = module
    spec.loader.exec_module(module)
    return module


def test_production_readiness_has_deployment_fields():
    readiness = production_readiness()
    for key in (
        "deployment_ready",
        "production_ready",
        "database_backend",
        "migrations",
        "use_arq_worker",
        "usage_limits_enabled",
        "rate_limiting_enabled",
    ):
        assert key in readiness


def test_smoke_script_import_and_parse_args():
    smoke = _load_smoke_module()
    args = smoke.parse_args(["--base-url", "https://example.com", "--email-prefix", "ci"])
    assert args.base_url == "https://example.com"
    assert args.email_prefix == "ci"
    assert callable(smoke.run_smoke)



def test_init_db_skips_demo_seed_when_jwt_required(monkeypatch):
    """Production startup must not insert demo project before any user exists."""
    from app.core import config
    from app.db import init_db as init_db_module

    monkeypatch.setattr(config.settings, "AUTH_REQUIRE_JWT", True)

    with patch("app.db.demo_seed.ensure_demo_project") as mock_demo:
        init_db_module.init_db()
        mock_demo.assert_not_called()
