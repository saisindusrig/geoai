"""Isolated migration tests. Never use the user's demo database."""
import os
import subprocess
import sys
from pathlib import Path

import pytest
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateTable, CreateIndex
from alembic.migration import MigrationContext
from alembic.operations import Operations
from fastapi import HTTPException

from app.db.models import Base, STAGE1_TABLES, Project, User, ModelRevision, DesignScenario
from app.domain.stage1 import ObjectRef
from app.services.assistant.ownership import validate_project_references

ROOT = Path(__file__).resolve().parents[1]


def migrate(url, revision="head"):
    subprocess.run([sys.executable, "-m", "alembic", "upgrade", revision], cwd=ROOT,
                   env=os.environ | {"DATABASE_URL": url}, check=True, capture_output=True, text=True)


def test_existing_007_upgrade_preserves_data_and_elevation(tmp_path):
    url = f"sqlite:///{(tmp_path/'legacy.db').as_posix()}"
    migrate(url, "007")
    engine = sa.create_engine(url)
    # 001/006 historically import live metadata. Explicitly restore the actual
    # pre-foundation table shape to exercise 008/009, not merely create_all.
    with engine.begin() as c:
        for (name,) in c.exec_driver_sql("SELECT name FROM sqlite_master WHERE type='trigger'").all():
            if name.startswith(("scope_", "retain_", "immutable_")):
                c.exec_driver_sql(f'DROP TRIGGER "{name}"')
        for table in reversed(Base.metadata.sorted_tables):
            if table.info.get("stage1"):
                table.drop(c)
        ops = Operations(MigrationContext.configure(c))
        with ops.batch_alter_table("model_placements") as batch:
            batch.drop_column("elevation_resolution")
            batch.drop_column("elevation_provenance_json")
            batch.alter_column("anchor_elevation", existing_type=sa.Float(), nullable=False, server_default="0")
        c.execute(Base.metadata.tables['users'].insert().values(id=1,name='Test',email='stage1@example.test'))
        c.execute(Base.metadata.tables['projects'].insert().values(id=1,user_id=1,name='Keep me',project_type='building'))
        c.execute(Base.metadata.tables['design_scenarios'].insert().values(id=1,project_id=1,name='Keep scenario'))
        meta = sa.MetaData()
        rev = sa.Table("model_revisions",meta,autoload_with=c)
        p = sa.Table("model_placements",meta,autoload_with=c)
        sample = sa.Table("ground_samples",meta,autoload_with=c)
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        for i,value in enumerate([0,0,621.482,0,45],1):
            c.execute(rev.insert().values(id=i,project_id=1,design_scenario_id=1,revision_number=i,
                document_json={"metadata":{"elevation_known":False}} if i == 1 else {"keep":True}, source="manual_edit",created_at=now))
            c.execute(p.insert().values(id=i,project_id=1,model_revision_id=i,anchor_longitude=77,anchor_latitude=12,
                anchor_elevation=value,placement_mode="GROUND_RELATIVE",height_reference="TERRAIN",placement_state="UNPLACED",
                anchor_heading_deg=17,elevation_offset=3,anchor_locked=True,local_transform_json={"matrix":[1,2,3]},
                legacy_placement=i==1,created_at=now,updated_at=now,
                anchor_vertical_reference_json={"type":"ELLIPSOIDAL"} if i in (2,3) else None,
                accepted_ground_sample_id=i if i in (2,3) else None))
            if i in (2,3):
                c.execute(sample.insert().values(id=i,project_id=1,placement_id=i,longitude=77,latitude=12,elevation=value,
                    source="SURVEY",status="VALID",vertical_reference_json={"type":"ELLIPSOIDAL"},created_at=now))
    migrate(url)
    with engine.begin() as c:
        c.exec_driver_sql("PRAGMA foreign_keys=ON")
        assert c.exec_driver_sql("SELECT name FROM projects").scalar() == "Keep me"
        assert c.exec_driver_sql("SELECT count(*) FROM model_revisions").scalar() == 5
        assert c.exec_driver_sql("SELECT count(*) FROM ground_samples").scalar() == 2
        rows = c.exec_driver_sql("SELECT anchor_elevation,elevation_resolution FROM model_placements ORDER BY id").all()
        assert rows == [(None,"UNKNOWN"),(0,"RESOLVED"),(621.482,"RESOLVED"),(0,"LEGACY_UNRESOLVED"),(45,"LEGACY_UNRESOLVED")]
        assert c.exec_driver_sql("SELECT count(*) FROM model_placements WHERE anchor_heading_deg=17 AND elevation_offset=3").scalar() == 5
        assert '1, 2, 3' in c.exec_driver_sql("SELECT local_transform_json FROM model_placements WHERE id=1").scalar()
        assert c.exec_driver_sql("SELECT count(*) FROM audit_logs WHERE action='placement.elevation_migrated'").scalar() == 5
        assert not c.exec_driver_sql("PRAGMA foreign_key_check").all()
        assert set(STAGE1_TABLES) <= set(sa.inspect(c).get_table_names())
        columns={v['name']:v for v in sa.inspect(c).get_columns('model_placements')}
        assert columns['anchor_elevation']['nullable'] and columns['anchor_elevation']['default'] is None
    engine.dispose()


def test_null_elevation_backfill(tmp_path):
    from app.db.stage1_elevation_v1 import backfill
    engine=sa.create_engine('sqlite://')
    Base.metadata.create_all(engine)
    with engine.begin() as c:
        c.execute(Base.metadata.tables['users'].insert().values(id=1,name='test',email='null@test'))
        c.execute(Base.metadata.tables['projects'].insert().values(id=1,user_id=1,name='test',project_type='building'))
        c.execute(Base.metadata.tables['design_scenarios'].insert().values(id=1,project_id=1,name='test'))
        c.execute(Base.metadata.tables['model_revisions'].insert().values(id=1,project_id=1,design_scenario_id=1,revision_number=1,document_json={}))
        c.execute(Base.metadata.tables['model_placements'].insert().values(id=1,project_id=1,model_revision_id=1,anchor_longitude=77,anchor_latitude=12))
        backfill(c)
        row=c.execute(sa.select(Base.metadata.tables['model_placements'])).mappings().one()
        assert row['anchor_elevation'] is None and row['elevation_resolution']=='UNKNOWN'


def test_sqlite_scope_and_immutable_constraints():
    engine=sa.create_engine('sqlite://')
    Base.metadata.create_all(engine)
    with engine.connect() as c:
        c.exec_driver_sql('PRAGMA foreign_keys=ON')
        c.execute(Base.metadata.tables['users'].insert().values(id=1,name='a',email='a@test'))
        for i in (1,2):
            c.execute(Base.metadata.tables['projects'].insert().values(id=i,user_id=1,name='p',project_type='building'))
        c.execute(STAGE1_TABLES['site_selections'].insert().values(id='s1',project_id=1,kind='POINT'))
        c.commit()
        with pytest.raises(sa.exc.IntegrityError):
            c.execute(STAGE1_TABLES['site_profiles'].insert().values(id='p2',project_id=2,selection_id='s1'))
        c.rollback()
        c.execute(STAGE1_TABLES['dependency_manifests'].insert().values(id='m',project_id=1,payload={},content_hash='a'*64))
        c.commit()
        for statement in (sa.update(STAGE1_TABLES['dependency_manifests']).values(payload={'changed':True}),sa.delete(STAGE1_TABLES['dependency_manifests'])):
            with pytest.raises(sa.exc.IntegrityError,match='immutable'):
                c.execute(statement)
            c.rollback()
        assert len([n for n in sa.inspect(c).get_table_names() if n in STAGE1_TABLES])==28


def test_foreign_project_nested_reference(db_session):
    db_session.add(User(id=901,name='a',email='nested@test'))
    db_session.add_all([Project(id=i,user_id=901,name='p',project_type='building') for i in (901,902)])
    db_session.flush()
    db_session.execute(STAGE1_TABLES['asset_instances'].insert().values(id='foreign',project_id=902,asset_type='COFFERDAM',name='Cofferdam'))
    with pytest.raises(HTTPException) as exc:
        validate_project_references(db_session,901,901,ObjectRef(asset_id='foreign',object_id='o',model_revision_id='1',component_id='c',geometry_hash='a'*64))
    assert exc.value.status_code == 404


def test_postgresql_ddl_contract():
    # Compilation is NOT an actual PostgreSQL migration test.
    table=STAGE1_TABLES['site_selection_versions']
    ddl=str(CreateTable(table).compile(dialect=postgresql.dialect()))
    assert 'geometry(Geometry,4326)' in ddl and 'JSONB' in ddl
    index=next(i for i in table.indexes if i.name=='ix_site_selection_versions_geometry')
    assert 'USING gist' in str(CreateIndex(index).compile(dialect=postgresql.dialect()))


@pytest.mark.skipif(not os.environ.get('STAGE1_TEST_POSTGRES_URL'),reason='Dedicated PostgreSQL/PostGIS test database not configured')
def test_postgresql_upgrade():
    # Must point to an EMPTY disposable database; never use DATABASE_URL here.
    url=os.environ['STAGE1_TEST_POSTGRES_URL']
    engine=sa.create_engine(url)
    assert not sa.inspect(engine).get_table_names(), 'Postgres test database must be empty'
    migrate(url)
    with engine.connect() as c:
        assert c.exec_driver_sql("SELECT type,srid FROM geometry_columns WHERE f_table_name='site_selection_versions'").one()==('GEOMETRY',4326)
        assert 'gist' in c.exec_driver_sql("SELECT indexdef FROM pg_indexes WHERE indexname='ix_site_selection_versions_geometry'").scalar()


def test_downgrade_refuses_history_loss(tmp_path):
    url=f"sqlite:///{(tmp_path/'downgrade.db').as_posix()}"
    migrate(url)
    result=subprocess.run([sys.executable,'-m','alembic','downgrade','007'],cwd=ROOT,
        env=os.environ|{'DATABASE_URL':url},capture_output=True,text=True)
    assert result.returncode != 0 and 'Restore a verified' in result.stderr
