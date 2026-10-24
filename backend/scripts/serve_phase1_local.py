"""Run the existing local app without paid AI credentials or telemetry.
Settings overrides are process-local; existing .env, storage and projects stay intact.
"""
import sys
import os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.core.config import settings
settings.AI_PROVIDER = "mock"
settings.GEOAI_OFFLINE_PLATFORM_DEMO = True
settings.NEXT_PUBLIC_APP_URL = "http://localhost:3001"
settings.CORS_ALLOWED_ORIGINS = ",".join(filter(None, [settings.CORS_ALLOWED_ORIGINS, "http://localhost:3001", "http://127.0.0.1:3001"]))
settings.PUBLIC_API_URL = f"http://127.0.0.1:{os.environ.get('GEOAI_LOCAL_PORT', '8001')}"
settings.S3_ACCESS_KEY = ""
settings.S3_SECRET_KEY = ""
for name in ("NEBIUS_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GEMINI_API_KEY", "SENTRY_DSN"):
    setattr(settings, name, "")
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=int(os.environ.get("GEOAI_LOCAL_PORT", "8001")))
