"""Frozen Stage 1 storage schema shared by metadata and migration 008.

Do not evolve this module after release: subsequent schema changes belong in
new revisions. Payload versions are immutable; mutable state has separate rows.
"""
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.types import UserDefinedType


class CanonicalGeometry(UserDefinedType):
    cache_ok = True

    def get_col_spec(self, **kw):
        return "geometry(Geometry,4326)"


@compiles(CanonicalGeometry, "sqlite")
def sqlite_geometry(type_, compiler, **kw):
    return "JSON"


JSON = sa.JSON().with_variant(JSONB(), "postgresql")
IMMUTABLE = set()


def register(metadata):
    tables = {}

    def col(name, type_=sa.String(128), nullable=False, **kw):
        return sa.Column(name, type_, nullable=nullable, **kw)

    def payload(name="payload"):
        return col(name, JSON)

    def ref(name, target, nullable=False, integer=False):
        return (col(name, sa.Integer if integer else sa.String(128), nullable=nullable), sa.ForeignKeyConstraint(
            ["project_id", name], [f"{target}.project_id", f"{target}.id"],
            name=f"fk_{name}_{target}"))

    def table(name, *fields, immutable=False, unique=(), checks=()):
        parts = [col("id", primary_key=True),
                 sa.Column("project_id", sa.Integer, sa.ForeignKey("projects.id"), nullable=False),
                 sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.current_timestamp()),
                 sa.UniqueConstraint("project_id", "id", name=f"uq_{name}_project_id")]
        for field in fields:
            parts.extend(field if isinstance(field, tuple) else [field])
        parts.extend(sa.UniqueConstraint(*keys, name=f"uq_{name}_{i}") for i, keys in enumerate(unique))
        parts.extend(sa.CheckConstraint(expr, name=f"ck_{name}_{i}") for i, expr in enumerate(checks))
        t = sa.Table(name, metadata, *parts, info={"stage1": True, "immutable": immutable})
        sa.Index(f"ix_{name}_project", t.c.project_id)
        tables[name] = t
        if immutable:
            IMMUTABLE.add(name)
        return t

    def version():
        return col("version", sa.Integer), sa.CheckConstraint("version >= 1")

    def digest():
        return col("content_hash", sa.String(64))

    table("site_selections", col("kind", sa.String(24)),
          checks=("kind IN ('AREA','ROUTE','CROSSING','POINT','ENDPOINTS')",))
    t = table("site_selection_versions", ref("selection_id", "site_selections"), version(),
              col("kind", sa.String(24)), payload("original_geometry"), payload("original_crs"),
              col("canonical_geometry", CanonicalGeometry().with_variant(sa.JSON(), "sqlite")),
              col("canonical_crs", sa.String(32), server_default="EPSG:4326"),
              payload("transformation_provenance"), payload("selection_payload"), digest(),
              immutable=True, unique=(("selection_id", "version"),),
              checks=("canonical_crs = 'EPSG:4326'", "kind IN ('AREA','ROUTE','CROSSING','POINT','ENDPOINTS')"))
    sa.Index("ix_site_selection_versions_geometry", t.c.canonical_geometry,
             postgresql_using="gist").ddl_if(dialect="postgresql")
    table("site_profiles", ref("selection_id", "site_selections"), col("refresh_state", sa.String(24), server_default="IDLE"))
    table("dependency_manifests", payload(), digest(), immutable=True)
    table("site_profile_versions", ref("profile_id", "site_profiles"), version(),
          ref("selection_version_id", "site_selection_versions"), ref("dependency_manifest_id", "dependency_manifests"),
          payload(), digest(), immutable=True, unique=(("profile_id", "version"), ("profile_id", "content_hash")))
    table("site_evidence", col("source_type", sa.String(24)), payload(), digest(),
          ref("supersedes_id", "site_evidence", True), immutable=True,
          checks=("source_type IN ('MEASURED','SURVEY','PUBLIC_MAP','USER_PROVIDED','DERIVED','AI_ASSUMPTION','UNKNOWN')",))
    table("site_profile_evidence", ref("profile_version_id", "site_profile_versions"), ref("evidence_id", "site_evidence"),
          immutable=True, unique=(("profile_version_id", "evidence_id"),))
    table("site_missing_information", ref("profile_version_id", "site_profile_versions"), payload(), immutable=True)

    table("project_conversations", col("title", sa.String(255)),
          sa.Column("created_by", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
          col("archived_at", sa.DateTime(timezone=True), True),
          col("next_sequence", sa.Integer, server_default="1"), checks=("next_sequence >= 1",))
    table("conversation_messages", ref("conversation_id", "project_conversations"), col("sequence", sa.Integer),
          col("role", sa.String(24)), payload("parts"), payload("context"), col("client_request_id", nullable=True),
          immutable=True, unique=(("conversation_id", "sequence"), ("conversation_id", "client_request_id")),
          checks=("sequence >= 1", "role IN ('USER','ASSISTANT','SYSTEM_EVENT')"))
    table("assistant_runs", ref("conversation_id", "project_conversations"), ref("message_id", "conversation_messages"),
          col("status", sa.String(32), server_default="QUEUED"), payload("context_snapshot"),
          col("error_code", nullable=True), ref("retry_of_id", "assistant_runs", True))
    table("assistant_tool_executions", ref("run_id", "assistant_runs"), col("tool_name"), col("tool_version"),
          payload("arguments"), col("status", sa.String(24)), col("result", JSON, True), col("error_code", nullable=True))
    table("assistant_run_events", ref("run_id", "assistant_runs"), col("sequence", sa.Integer), payload(),
          immutable=True, unique=(("run_id", "sequence"),), checks=("sequence >= 1",))
    table("asset_instances", col("asset_type"), col("name", sa.String(255)), ref("site_profile_id", "site_profiles", True),
          col("lifecycle", sa.String(24), server_default="PROPOSED"))
    table("project_memory_items", col("kind", sa.String(24)), ref("asset_id", "asset_instances", True),
          checks=("kind IN ('REQUIREMENT','PREFERENCE','DECISION','ASSUMPTION')",))
    table("project_memory_versions", ref("item_id", "project_memory_items"), version(), payload(), digest(),
          ref("supersedes_id", "project_memory_versions", True), immutable=True, unique=(("item_id", "version"),))
    table("project_memory_states", ref("memory_version_id", "project_memory_versions"), col("status", sa.String(24)),
          sa.Column("actor_id", sa.Integer, sa.ForeignKey("users.id")),
          unique=(("memory_version_id",),), checks=("status IN ('PROPOSED','ACCEPTED','REJECTED','SUPERSEDED')",))
    table("design_proposals", col("name", sa.String(255)))
    table("design_proposal_versions", ref("proposal_id", "design_proposals"), version(),
          ref("site_profile_version_id", "site_profile_versions"), ref("dependency_manifest_id", "dependency_manifests"),
          ref("parent_version_id", "design_proposal_versions", True),
          ref("source_model_revision_id", "model_revisions", True, integer=True),
          payload(), digest(), immutable=True, unique=(("proposal_id", "version"),))
    table("proposal_version_states", ref("proposal_version_id", "design_proposal_versions"), col("status", sa.String(32)),
          unique=(("proposal_version_id",),),
          checks=("status IN ('DRAFT','GENERATING','READY_FOR_REVIEW','HAS_ISSUES','APPROVED','STALE','REJECTED','BUILT')",))
    table("asset_specification_versions", ref("asset_id", "asset_instances"), version(), col("schema_id"),
          col("schema_version"), payload(), digest(), immutable=True, unique=(("asset_id", "version"),))
    table("proposal_asset_specifications", ref("proposal_version_id", "design_proposal_versions"),
          ref("specification_version_id", "asset_specification_versions"), immutable=True,
          unique=(("proposal_version_id", "specification_version_id"),))
    table("proposal_alternatives", ref("proposal_version_id", "design_proposal_versions"), col("name", sa.String(255)),
          payload(), digest(), immutable=True)
    table("proposal_approvals", ref("proposal_version_id", "design_proposal_versions"),
          ref("alternative_id", "proposal_alternatives", True), col("proposal_hash", sa.String(64)),
          col("dependency_hash", sa.String(64)), col("validation_hash", sa.String(64)),
          sa.Column("approved_by", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
          payload("acknowledged_assumptions"), immutable=True, unique=(("proposal_version_id",),))
    table("asset_relationships", col("relationship_id"), version(), ref("from_asset_id", "asset_instances"),
          ref("to_asset_id", "asset_instances"), col("kind", sa.String(32)), payload(), immutable=True,
          unique=(("relationship_id", "version"),),
          checks=("from_asset_id <> to_asset_id", "kind IN ('CONNECTS_TO','CROSSES','SUPPORTED_BY','DRAINS_TO','SERVES','ADJACENT_TO','INTERSECTS','DEPENDS_ON')"))
    table("model_object_lineage", ref("asset_id", "asset_instances"), ref("proposal_version_id", "design_proposal_versions"),
          ref("specification_version_id", "asset_specification_versions"),
          ref("model_revision_id", "model_revisions", integer=True),
          col("object_id"), col("component_id"), col("generator_id"), col("generator_version"), payload(),
          immutable=True, unique=(("model_revision_id", "object_id"),))
    table("generation_requests", ref("approval_id", "proposal_approvals"), col("manifest_hash", sa.String(64)),
          col("job_id", unique=True), col("status", sa.String(24), server_default="QUEUED"),
          unique=(("approval_id", "manifest_hash"),))
    table("job_outbox", ref("generation_request_id", "generation_requests"), payload(),
          col("status", sa.String(24), server_default="PENDING"), col("attempts", sa.Integer, server_default="0"),
          unique=(("generation_request_id",),))
    return tables


def install_guards(connection, tables):
    """Database-level protection also covers bulk SQL and non-ORM writers."""
    postgres = connection.dialect.name == "postgresql"
    if postgres:
        connection.exec_driver_sql("""CREATE OR REPLACE FUNCTION geoai_stage1_immutable() RETURNS trigger
        LANGUAGE plpgsql AS $$ BEGIN RAISE EXCEPTION 'Stage 1 version history is immutable'; END $$""")
    for name, table in tables.items():
        if not postgres:
            # SQLite's legacy connections may have foreign_keys disabled. These
            # scoped reference guards keep new foundation rows protected too.
            for index, fk in enumerate(sorted(table.foreign_key_constraints, key=lambda f: tuple(e.parent.name for e in f.elements))):
                target = fk.elements[0].column.table.name
                present = " AND ".join(f'NEW."{e.parent.name}" IS NOT NULL' for e in fk.elements)
                match = " AND ".join(f'"{e.column.name}"=NEW."{e.parent.name}"' for e in fk.elements)
                for operation in ("INSERT", "UPDATE"):
                    connection.exec_driver_sql(f'DROP TRIGGER IF EXISTS "scope_{name}_{index}_{operation.lower()}"')
                    connection.exec_driver_sql(f'''CREATE TRIGGER IF NOT EXISTS "scope_{name}_{index}_{operation.lower()}"
                    BEFORE {operation} ON "{name}" WHEN {present} AND NOT EXISTS
                    (SELECT 1 FROM "{target}" WHERE {match})
                    BEGIN SELECT RAISE(ABORT, 'Foreign-project or missing reference'); END''')
                child_match = " AND ".join(f'"{e.parent.name}"=OLD."{e.column.name}"' for e in fk.elements)
                for operation in ("DELETE", "UPDATE"):
                    changed = "" if operation == "DELETE" else " AND (" + " OR ".join(
                        f'NEW."{e.column.name}" IS NOT OLD."{e.column.name}"' for e in fk.elements) + ")"
                    connection.exec_driver_sql(f'DROP TRIGGER IF EXISTS "retain_{name}_{index}_{operation.lower()}"')
                    connection.exec_driver_sql(f'''CREATE TRIGGER IF NOT EXISTS "retain_{name}_{index}_{operation.lower()}"
                    BEFORE {operation} ON "{target}" WHEN EXISTS (SELECT 1 FROM "{name}" WHERE {child_match}){changed}
                    BEGIN SELECT RAISE(ABORT, 'Referenced Stage 1 history must be retained'); END''')
        if not table.info.get("immutable"):
            continue
        if postgres:
            connection.exec_driver_sql(f'DROP TRIGGER IF EXISTS stage1_immutable ON "{name}"')
            connection.exec_driver_sql(f'CREATE TRIGGER stage1_immutable BEFORE UPDATE OR DELETE ON "{name}" FOR EACH ROW EXECUTE FUNCTION geoai_stage1_immutable()')
        else:
            for operation in ("UPDATE", "DELETE"):
                connection.exec_driver_sql(f'''CREATE TRIGGER IF NOT EXISTS "immutable_{name}_{operation.lower()}"
                BEFORE {operation} ON "{name}" BEGIN SELECT RAISE(ABORT, 'Stage 1 version history is immutable'); END''')
    if postgres:
        # Typed PostGIS storage, dimensional/range/type constraints and GiST are
        # production requirements; SQLite only carries validated JSON snapshots.
        exists = connection.execute(sa.text("SELECT 1 FROM pg_constraint WHERE conname='ck_selection_spatial_v1'")).scalar()
        if not exists:
            connection.exec_driver_sql("""ALTER TABLE site_selection_versions ADD CONSTRAINT ck_selection_spatial_v1 CHECK (
                ST_SRID(canonical_geometry)=4326 AND ST_NDims(canonical_geometry)=2
                AND NOT ST_IsEmpty(canonical_geometry) AND ST_IsValid(canonical_geometry)
                AND ST_CoveredBy(canonical_geometry, ST_MakeEnvelope(-180,-90,180,90,4326))
                AND ((kind='AREA' AND GeometryType(canonical_geometry) IN ('POLYGON','MULTIPOLYGON'))
                  OR (kind IN ('ROUTE','CROSSING') AND GeometryType(canonical_geometry)='LINESTRING')
                  OR (kind='POINT' AND GeometryType(canonical_geometry)='POINT')
                  OR (kind='ENDPOINTS' AND GeometryType(canonical_geometry)='MULTIPOINT' AND ST_NumGeometries(canonical_geometry)=2)))""")
