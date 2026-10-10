"""Fresh seeded SQLite regression setup; use the existing offline HTTP guard."""
import os
from pathlib import Path
import runpy
import sys
from uuid import uuid4

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
out=ROOT/".cad-proof-output"/("4ch-regression-"+uuid4().hex)
out.mkdir()
os.environ["DATABASE_URL"]="sqlite:///"+(out/"regression.db").as_posix()
from app.core.config import settings
settings.LOCAL_STORAGE_DIR=str(out/"seed-storage")
from app.services import storage
original_configured=storage._s3_configured
storage._s3_configured=lambda:False
from app.db.models import Base
from app.db.session import engine
Base.metadata.create_all(engine)
from app.db.init_db import init_db
original_auth=settings.AUTH_REQUIRE_JWT
settings.AUTH_REQUIRE_JWT=False
try:init_db()
finally:
    settings.AUTH_REQUIRE_JWT=original_auth
    storage._s3_configured=original_configured
print("Offline regression database: "+str(out/"regression.db"),flush=True)
runpy.run_path(str(ROOT/"scripts"/"run_cad_regressions.py"),run_name="__main__")
