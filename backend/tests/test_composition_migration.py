"""Exercise the actual legacy relationship constraint with retention triggers present."""
import pytest
import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations
from tests.test_stage1_storage import migrate
from app.db.models import Base,STAGE1_TABLES
from app.db.stage1_schema_v1 import install_guards


@pytest.mark.parametrize("representative",[False,True])
def test_existing_010_relationship_upgrade_preserves_records_and_guards(tmp_path,representative):
    url=f"sqlite:///{(tmp_path/'existing010.db').as_posix()}"
    migrate(url,"010")
    engine=sa.create_engine(url)
    with engine.begin() as c:
        # 001 imports current metadata. Restore the released 010 constraint to
        # ensure 011 really runs its SQLite batch path instead of skipping it.
        removed=c.exec_driver_sql("SELECT name,sql FROM sqlite_master WHERE type='trigger' AND sql LIKE '%asset_relationships%'").all()
        for name,_ in removed:c.exec_driver_sql(f'DROP TRIGGER "{name}"')
        ops=Operations(MigrationContext.configure(c))
        with ops.batch_alter_table("asset_relationships") as batch:
            batch.drop_constraint("ck_asset_relationships_1",type_="check")
            batch.create_check_constraint("ck_asset_relationships_1","kind IN ('CONNECTS_TO','CROSSES','SUPPORTED_BY','DRAINS_TO','SERVES','ADJACENT_TO','INTERSECTS','DEPENDS_ON')")
        for _,sql in removed:c.exec_driver_sql(sql)
        install_guards(c,STAGE1_TABLES)
        c.execute(Base.metadata.tables["users"].insert().values(id=1,name="Owner",email="upgrade@test"))
        c.execute(Base.metadata.tables["projects"].insert().values(id=1,user_id=1,name="Keep project",project_type="bridge"))
        for aid,kind in (("a","BRIDGE"),("b","ROAD")):
            c.exec_driver_sql("INSERT INTO asset_instances(id,project_id,asset_type,name) VALUES (?,?,?,?)",(aid,1,kind,aid))
        c.exec_driver_sql("INSERT INTO asset_relationships(id,project_id,relationship_id,version,from_asset_id,to_asset_id,kind,payload) VALUES ('edge',1,'stable-edge',1,'a','b','CONNECTS_TO','{\"keep\":true}')")
        c.exec_driver_sql("CREATE TRIGGER custom_relationship_guard BEFORE INSERT ON asset_relationships WHEN NEW.kind='PART_OF' BEGIN SELECT RAISE(ABORT,'custom guard retained'); END")
        if representative:
            c.exec_driver_sql("INSERT INTO project_conversations(id,project_id,title,created_by) VALUES ('c',1,'Keep conversation',1)")
            c.exec_driver_sql("INSERT INTO conversation_messages(id,project_id,conversation_id,sequence,role,parts,context) VALUES ('m',1,'c',1,'USER','[]','{}')")
            c.exec_driver_sql("INSERT INTO site_selections(id,project_id,kind) VALUES ('s',1,'POINT')")
            c.exec_driver_sql("INSERT INTO site_profiles(id,project_id,selection_id) VALUES ('p',1,'s')")
        before=c.exec_driver_sql("SELECT * FROM asset_relationships").all()
    migrate(url)
    with engine.begin() as c:
        assert c.exec_driver_sql("SELECT version_num FROM alembic_version").scalar()=="011"
        assert c.exec_driver_sql("SELECT * FROM asset_relationships").all()==before
        assert not c.exec_driver_sql("PRAGMA foreign_key_check").all()
        if representative:
            assert c.exec_driver_sql("SELECT parts FROM conversation_messages WHERE id='m'").scalar()=="[]"
            assert c.exec_driver_sql("SELECT selection_id FROM site_profiles WHERE id='p'").scalar()=="s"
        c.exec_driver_sql("INSERT INTO asset_relationships(id,project_id,relationship_id,version,from_asset_id,to_asset_id,kind,payload) VALUES ('host',1,'host',1,'a','b','HOSTED_BY','{}')")
    for sql,message in (("UPDATE asset_relationships SET payload='{}' WHERE id='edge'","immutable"),
        ("DELETE FROM asset_relationships WHERE id='edge'","immutable"),
        ("DELETE FROM asset_instances WHERE id='a'","retained"),
        ("INSERT INTO asset_relationships(id,project_id,relationship_id,version,from_asset_id,to_asset_id,kind,payload) VALUES ('bad',1,'bad',1,'a','missing','CONNECTS_TO','{}')","reference"),
        ("INSERT INTO asset_relationships(id,project_id,relationship_id,version,from_asset_id,to_asset_id,kind,payload) VALUES ('custom',1,'custom',1,'a','b','PART_OF','{}')","custom guard retained")):
        with engine.begin() as c:
            with pytest.raises(sa.exc.IntegrityError,match=message):c.exec_driver_sql(sql)
    engine.dispose()
