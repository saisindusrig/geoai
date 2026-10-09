"""Exercise actual 009 -> 010 ALTERs, not just current metadata create_all."""
import sqlalchemy as sa
from tests.test_stage1_storage import migrate
from app.db.models import User, Project


def test_009_upgrade_preserves_foundation_payloads(tmp_path):
    url=f"sqlite:///{(tmp_path/'existing009.db').as_posix()}"
    migrate(url,"009")
    engine=sa.create_engine(url)
    with engine.begin() as c:
        for (name,) in c.exec_driver_sql("SELECT name FROM sqlite_master WHERE type='trigger'").all():
            if "site_sample_sets" in name:
                c.exec_driver_sql(f'DROP TRIGGER "{name}"')
        c.exec_driver_sql("DROP TABLE IF EXISTS site_sample_sets")
        for name in ("latest_version_id","refresh_context","refresh_job_id","refresh_error"):
            if name in {col["name"] for col in sa.inspect(c).get_columns("site_profiles")}:
                c.exec_driver_sql(f'ALTER TABLE site_profiles DROP COLUMN "{name}"')
        c.execute(User.__table__.insert().values(id=1,name="One",email="upgrade@test"))
        c.execute(Project.__table__.insert().values(id=1,user_id=1,name="Keep site",project_type="bridge"))
        c.exec_driver_sql("INSERT INTO site_selections(id,project_id,kind) VALUES ('s',1,'POINT')")
        c.exec_driver_sql("INSERT INTO site_profiles(id,project_id,selection_id) VALUES ('p',1,'s')")
        c.exec_driver_sql("INSERT INTO project_conversations(id,project_id,title,created_by) VALUES ('c',1,'Keep discussion',1)")
        c.exec_driver_sql("INSERT INTO conversation_messages(id,project_id,conversation_id,sequence,role,parts,context,client_request_id) VALUES ('m',1,'c',1,'USER','[{\"kind\":\"TEXT\",\"text\":\"Keep this\"}]','{}','old')")
    migrate(url)
    with engine.begin() as c:
        assert c.exec_driver_sql("SELECT version_num FROM alembic_version").scalar()=="011"
        assert c.exec_driver_sql("SELECT parts FROM conversation_messages WHERE id='m'").scalar()=='[{"kind":"TEXT","text":"Keep this"}]'
        assert c.exec_driver_sql("SELECT latest_version_id FROM site_profiles WHERE id='p'").scalar() is None
        c.exec_driver_sql("INSERT INTO site_sample_sets(id,project_id,profile_id,payload,content_hash) VALUES ('samples',1,'p','{}','hash')")
        assert not c.exec_driver_sql("PRAGMA foreign_key_check").all()
    with engine.begin() as c:
        import pytest
        with pytest.raises(sa.exc.IntegrityError,match="immutable"):
            c.exec_driver_sql("UPDATE site_sample_sets SET payload='{}'")
    engine.dispose()
