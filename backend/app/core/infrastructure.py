"""Read-only dependency probes. Configuration is distinct from verified availability."""
from pathlib import Path
import os
import sqlalchemy as sa
from alembic.config import Config
from alembic.script import ScriptDirectory
from app.core.config import BACKEND_DIR, settings
from app.db.session import engine, IS_POSTGRES


def database_status():
    result = {"backend":"postgresql" if IS_POSTGRES else "sqlite", "status":"UNAVAILABLE", "postgis":False, "schema":"UNKNOWN"}
    try:
        config = Config(); config.set_main_option("script_location",str(BACKEND_DIR / "alembic"))
        heads = set(ScriptDirectory.from_config(config).get_heads())
        with engine.connect() as connection:
            if IS_POSTGRES: connection.execute(sa.text("SET LOCAL statement_timeout = 2000"))
            connection.execute(sa.text("SELECT 1"))
            result["status"] = "AVAILABLE"
            if IS_POSTGRES:
                result["postgis"] = bool(connection.execute(sa.text("SELECT EXISTS (SELECT 1 FROM pg_extension WHERE extname='postgis')")).scalar())
            if sa.inspect(connection).has_table("alembic_version"):
                versions = set(connection.execute(sa.text("SELECT version_num FROM alembic_version")).scalars())
                result["schema"] = "CURRENT" if versions == heads else "OUTDATED"
            else: result["schema"] = "MISSING"
    except Exception:
        result["status"] = "UNAVAILABLE"
    return result


def dependency_status():
    from app.services import jobs, storage
    from app.services.ai import nebius
    redis = jobs._get_redis()
    redis_ok = False
    worker_ok = False
    try:
        if redis:
            redis_ok = bool(redis.ping())
            worker_ok = redis_ok and settings.USE_ARQ_WORKER and bool(redis.exists("geoai:worker:health"))
    except Exception: pass
    s3 = storage._get_s3()
    storage_status = "LOCAL_ONLY"
    if s3:
        try:
            s3.head_bucket(Bucket=settings.S3_BUCKET)
            storage_status = "AVAILABLE"
        except Exception: storage_status = "UNAVAILABLE"
    elif storage._s3_configured(): storage_status = "UNAVAILABLE"
    local_path = Path(settings.LOCAL_STORAGE_DIR)
    ai_status = nebius.assistant_configuration()
    if ai_status == "CONFIGURED":
        last = nebius.LAST_ASSISTANT_RESULT
        current = nebius.assistant_diagnostics()
        ai_status = last["status"] if last and all(last["diagnostics"].get(k)==current[k] for k in ("configuredModel","baseHost","basePath")) else "UNVERIFIED"
    return {"database":database_status(), "redis":{"status":"AVAILABLE" if redis_ok else "UNAVAILABLE"},
        "worker":{"status":"AVAILABLE" if worker_ok else "UNAVAILABLE" if settings.USE_ARQ_WORKER else "INLINE_ONLY","configured":settings.USE_ARQ_WORKER},
        "storage":{"status":storage_status,"mode":"s3" if s3 else "local","localWritable":local_path.is_dir() and os.access(local_path,os.W_OK)},
        "ai":{"provider":"nebius","status":ai_status,"configured":nebius.assistant_configuration()=="CONFIGURED"},
        "cesium":{"status":"CONFIGURED" if settings.CESIUM_ION_READ_TOKEN else "MISSING_CONFIGURATION"}}
