"""Disposable JWT-only acceptance server. Never imports a user's database."""
import os
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
root = Path(__file__).resolve().parents[2] / 'docs/release'
root.mkdir(exist_ok=True, parents=True)
run = str(int(time.time()))
database = root / f'isolated-{run}.sqlite'
os.environ.update(DATABASE_URL=f'sqlite:///{database.as_posix()}', AUTH_REQUIRE_JWT='true', AI_PROVIDER='mock', REDIS_URL='redis://127.0.0.1:1/15', LOCAL_STORAGE_DIR=str(root / f'storage-{run}'), NEXT_PUBLIC_APP_URL='http://localhost:3002')
from app.core.config import settings
assert settings.DATABASE_URL == f'sqlite:///{database.as_posix()}'
settings.APP_SECRET = 'isolated-release-fixture-secret-not-a-production-credential'
settings.AUTH_REQUIRE_JWT = True
settings.PUBLIC_API_URL = 'http://127.0.0.1:8022'
settings.AI_PROVIDER = 'mock'
settings.ENGINEERING_AI_MODE = 'mock'
settings.USE_ARQ_WORKER = False
settings.S3_ACCESS_KEY = settings.S3_SECRET_KEY = settings.S3_BUCKET = ''
settings.NEBIUS_API_KEY = settings.OPENAI_API_KEY = settings.ANTHROPIC_API_KEY = settings.GEMINI_API_KEY = ''
settings.CORS_ALLOWED_ORIGINS = 'http://localhost:3002,http://127.0.0.1:3002'
settings.USAGE_LIMITS_ENABLED = False  # Fixture accounts have no commercial usage policy.
settings.RATE_LIMITING_ENABLED = False

from app.main import app
from app.db.init_db import init_db
from app.db.models import Base, User
from app.db.session import SessionLocal, engine
from app.core.passwords import hash_password
init_db()
# init_db intentionally excludes Stage 1 tables; disposable fixtures need the
# complete registered schema, including lineage and its immutability guards.
Base.metadata.create_all(engine)
with SessionLocal() as db:
    for uid in [1001, 1002]:
        db.add(User(id=uid, name=f'Release fixture {uid}', email=f'release{uid}@example.invalid', password_hash=hash_password('Disposable-fixture-2026'), role='admin', plan='admin'))
    db.commit()

# Deterministic external-data adapters, marked assumed/unknown in actual results.
from app.api.routes import site_analysis
from app.services.geospatial import terrain
from app.services.ai import design_planner
async def offline_osm(_bbox):
    return {'type': 'FeatureCollection', 'features': [], 'mock': True}
async def offline_terrain(points):
    return {'elevations_m': [None] * len(points), 'provider': 'NONE', 'assumed': True}
site_analysis.fetch_osm_features = offline_osm
terrain.sample_elevations = offline_terrain

# Fail closed on outbound network, even if a provider path is accidentally used.
import socket
original_connect = socket.socket.connect
def local_connect(sock, address):
    if isinstance(address, tuple) and address[0] not in ('127.0.0.1', 'localhost', '::1'):
        raise RuntimeError('External network disabled in isolated acceptance server')
    return original_connect(sock, address)
socket.socket.connect = local_connect
(root / 'isolated-server.json').write_text(__import__('json').dumps({'database': str(database), 'storage': settings.LOCAL_STORAGE_DIR, 'jwt_required': True, 'provider': settings.AI_PROVIDER, 'external_network': 'blocked', 'port': 8022}), encoding='utf-8')

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='127.0.0.1', port=8022, access_log=False)
