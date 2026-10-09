import time
from unittest.mock import Mock
import pytest
from fastapi import HTTPException
from jose import jwt
from app.core.config import Settings, settings
from app.core.security import create_access_token, decode_token
from app.core.cors import build_cors_origin_regex
from app.core.production import production_readiness


def test_jwt_expiration_is_required_and_expired_rejected():
    token=create_access_token(3)
    claims=jwt.get_unverified_claims(token)
    assert claims["exp"]>claims["iat"] and decode_token(token)==3
    for claims in ({"sub":"3"},{"sub":"3","exp":int(time.time())-5}):
        with pytest.raises(HTTPException):decode_token(jwt.encode(claims,settings.APP_SECRET,algorithm="HS256"))


def test_netlify_default_is_opt_in(monkeypatch):
    assert Settings.model_fields["CORS_ALLOW_NETLIFY"].default is False
    monkeypatch.setattr(settings,"CORS_ALLOW_NETLIFY",False)
    assert build_cors_origin_regex() is None


def test_production_postgres_failure_does_not_fallback(monkeypatch):
    from app.db import session
    monkeypatch.setattr(settings,"ENVIRONMENT","production")
    monkeypatch.setattr(settings,"DATABASE_URL","postgresql://hidden:secret@unavailable/db")
    factory=Mock(side_effect=RuntimeError("secret"));monkeypatch.setattr(session,"create_engine",factory)
    with pytest.raises(RuntimeError,match="startup stopped") as exc:session._resolve_engine()
    assert "secret" not in str(exc.value)
    assert factory.call_count==1
    monkeypatch.setattr(settings,"DATABASE_URL","sqlite://")
    with pytest.raises(RuntimeError,match="local/demo"):session._resolve_engine()


def test_development_fallback_remains_explicitly_limited(monkeypatch):
    from app.db import session
    monkeypatch.setattr(settings,"ENVIRONMENT","development")
    monkeypatch.setattr(settings,"DATABASE_URL","postgresql://unavailable/db")
    result=object();factory=Mock(side_effect=[RuntimeError(),result]);monkeypatch.setattr(session,"create_engine",factory)
    assert session._resolve_engine()==(result,False)
    assert factory.call_args.args[0]==session.SQLITE_URL


def test_production_init_never_repairs_schema(monkeypatch):
    from app.db import init_db
    monkeypatch.setattr(settings,"ENVIRONMENT","production")
    ddl=Mock(side_effect=AssertionError("DDL forbidden"));monkeypatch.setattr(init_db.Base.metadata,"create_all",ddl)
    monkeypatch.setattr("app.core.infrastructure.database_status",lambda:{"status":"AVAILABLE","schema":"CURRENT","postgis":True})
    init_db.init_db();ddl.assert_not_called()
    monkeypatch.setattr("app.core.infrastructure.database_status",lambda:{"status":"AVAILABLE","schema":"OUTDATED","postgis":True})
    with pytest.raises(RuntimeError,match="Alembic"):init_db.init_db()


def healthy():
    return {"database":{"backend":"postgresql","status":"AVAILABLE","schema":"CURRENT","postgis":True},
        "redis":{"status":"AVAILABLE"},"worker":{"status":"AVAILABLE"},"storage":{"status":"AVAILABLE","mode":"s3"},
        "ai":{"status":"AVAILABLE"},"cesium":{"status":"CONFIGURED"}}


@pytest.mark.parametrize("dependency",["database","postgis","redis","worker","storage","ai","cesium"])
def test_failed_required_dependency_blocks_production(monkeypatch,dependency):
    monkeypatch.setattr(settings,"ENVIRONMENT","production")
    monkeypatch.setattr(settings,"AUTH_REQUIRE_JWT",True)
    monkeypatch.setattr(settings,"APP_SECRET","safe-production-secret-with-32-characters")
    monkeypatch.setattr("app.core.production.collect_production_warnings",lambda:[])
    deps=healthy()
    assert production_readiness(deps)["production_ready"]
    if dependency=="postgis":deps["database"]["postgis"]=False
    else:deps[dependency]["status"]="UNAVAILABLE"
    result=production_readiness(deps)
    assert not result["production_ready"] and not result["deployment_ready"]
    assert result["critical_count"]==1


def test_cesium_checks_read_token_and_status_excludes_write_token(monkeypatch):
    from app.core.production import collect_production_warnings
    monkeypatch.setattr(settings,"CESIUM_ION_TOKEN","legacy")
    monkeypatch.setattr(settings,"CESIUM_ION_WRITE_TOKEN","write-secret")
    monkeypatch.setattr(settings,"CESIUM_ION_READ_TOKEN","")
    assert any(w["code"]=="cesium_ion_missing" for w in collect_production_warnings())
    monkeypatch.setattr(settings,"CESIUM_ION_READ_TOKEN","read")
    assert not any(w["code"]=="cesium_ion_missing" for w in collect_production_warnings())
    assert "write-secret" not in str(production_readiness(healthy()))


def test_dependency_probe_observes_failed_redis_worker_and_storage(monkeypatch):
    from app.core.infrastructure import dependency_status
    from app.services.ai import nebius
    redis=Mock();redis.ping.side_effect=RuntimeError("unavailable")
    s3=Mock();s3.head_bucket.side_effect=RuntimeError("unavailable")
    monkeypatch.setattr("app.services.jobs._get_redis",lambda:redis)
    monkeypatch.setattr("app.services.storage._get_s3",lambda:s3)
    monkeypatch.setattr("app.core.infrastructure.database_status",lambda:healthy()["database"])
    monkeypatch.setattr(settings,"USE_ARQ_WORKER",True)
    monkeypatch.setattr(nebius,"LAST_ASSISTANT_RESULT",None)
    result=dependency_status()
    assert result["redis"]["status"]==result["worker"]["status"]==result["storage"]["status"]=="UNAVAILABLE"
    assert result["ai"]["status"] in {"UNVERIFIED","MISSING_CONFIGURATION"}
