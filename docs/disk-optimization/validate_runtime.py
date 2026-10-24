"""Temporary attested offline backend; refuses the original database."""
from pathlib import Path
import asyncio
import json
import os
import sys

ROOT = Path(__file__).resolve().parents[2]
paths = json.loads((ROOT / "docs/disk-optimization/runtime-path.json").read_text())
os.environ["DATABASE_URL"] = "sqlite:///" + Path(paths["database"]).as_posix()
os.environ["LOCAL_STORAGE_DIR"] = paths["storage"]
sys.path[:0] = [str(ROOT / "backend"), str(ROOT / "backend/scripts")]
import serve_beam_frame_local
from app.core.config import settings
from app.db.session import engine

assert Path(engine.url.database).resolve() == Path(paths["database"]).resolve()
assert Path(engine.url.database).resolve() == (ROOT / "docs/disk-optimization/.validation/validation.db").resolve()
settings.PUBLIC_API_URL = "http://127.0.0.1:18001"
settings.CORS_ALLOWED_ORIGINS = "http://localhost:13001,http://127.0.0.1:13001"
from app.main import app

@app.get("/__disk_validation")
def attestation():
    return {"mode": "isolated-disk-optimization-20261015", "paid_inference": False}

import uvicorn
server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=18001))
asyncio.run(server.serve(), loop_factory=asyncio.SelectorEventLoop if sys.platform == "win32" else None)
