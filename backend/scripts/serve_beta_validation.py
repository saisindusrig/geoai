"""Offline acceptance server. All writes stay in an isolated database and storage.

Legacy regressions use a read-only SQLite backup. No data is copied back.
Fresh-journey projects are created through normal application APIs.
"""
import os
import sys
import sqlite3
import asyncio
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
print('Preparing isolated website data', flush=True)
RUN = ROOT/'.cache/production-beta/website'
RUN.mkdir(parents=True, exist_ok=True)
database = RUN/'validation.db'
if not database.exists():
    with sqlite3.connect(f'file:{(ROOT/"backend/dev.db").as_posix()}?mode=ro', uri=True) as source:
        with sqlite3.connect(database) as target:
            source.backup(target)
os.environ.update(DATABASE_URL=f'sqlite:///{database.as_posix()}',
    LOCAL_STORAGE_DIR=str(RUN/'storage'), GEOAI_ENGINEERING_ARTIFACT_ROOT=str(RUN/'solver'),
    GEOAI_LOCAL_PORT='8011')
sys.path.insert(0, str(ROOT/'backend'))
print('Loading offline application', flush=True)
import serve_beam_frame_local
from app.core.config import settings
settings.CORS_ALLOWED_ORIGINS = 'http://localhost:3001,http://127.0.0.1:3001,http://localhost:3011,http://127.0.0.1:3011'
import shutil
drawings = ROOT/'backend/storage/drawing-references'
if drawings.is_dir():
    shutil.copytree(drawings, RUN/'storage/drawing-references', dirs_exist_ok=True)

if __name__ == '__main__':
    print('Starting loopback API on 8011', flush=True)
    import uvicorn
    server = uvicorn.Server(uvicorn.Config('app.main:app', host='127.0.0.1', port=8011))
    asyncio.run(server.serve(), loop_factory=asyncio.SelectorEventLoop if sys.platform == 'win32' else None)
