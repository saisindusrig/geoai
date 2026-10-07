from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import declarative_base, relationship

from app.db.session import IS_POSTGRES

Base = declarative_base()


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=True)
    role = Column(String(20), default="user", nullable=False, index=True)
    plan = Column(String(20), default="free", nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)


class ProjectFolder(Base):
    __tablename__ = "project_folders"
    __table_args__ = (UniqueConstraint("user_id", "name", name="uq_project_folders_user_name"),)

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(80), nullable=False)
    color = Column(String(20), default="sage", nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    projects = relationship("Project", back_populates="folder")


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    folder_id = Column(Integer, ForeignKey("project_folders.id", ondelete="SET NULL"), nullable=True, index=True)
    name = Column(String(255), nullable=False)
    project_type = Column(String(50), nullable=False)  # flyover|building|pipeline|road|...
    status = Column(String(50), default="draft", nullable=False)
    units = Column(String(20), default="metric", nullable=False)
    location_name = Column(String(500), default="")
    center_lat = Column(Float, nullable=True)
    center_lng = Column(Float, nullable=True)
    # GeoJSON geometry is the source of truth in the API layer; on PostGIS we
    # additionally maintain a true geometry column for spatial queries.
    boundary_geojson = Column(JSON, nullable=True)   # Polygon
    alignment_geojson = Column(JSON, nullable=True)  # LineString (roads/pipelines/flyovers)
    # Survey workspace — engineering geometry stored in projected CRS (UTM)
    engineering_crs_epsg = Column(Integer, nullable=True)
    accuracy_tier = Column(String(32), default="visual", nullable=False)
    origin_lat = Column(Float, nullable=True)
    origin_lng = Column(Float, nullable=True)
    offset_e_m = Column(Float, nullable=True)
    offset_n_m = Column(Float, nullable=True)
    offset_h_m = Column(Float, nullable=True)
    survey_mode_enabled = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    site_analyses = relationship("SiteAnalysis", back_populates="project", cascade="all, delete-orphan")
    scenarios = relationship("DesignScenario", back_populates="project", cascade="all, delete-orphan")
    files = relationship("GeneratedFile", back_populates="project", cascade="all, delete-orphan")
    survey_datasets = relationship("SurveyDataset", back_populates="project", cascade="all, delete-orphan")
    engineering_layers = relationship("EngineeringLayer", back_populates="project", cascade="all, delete-orphan")
    ground_control_points = relationship("GroundControlPoint", back_populates="project", cascade="all, delete-orphan")
    accuracy_reports = relationship("AccuracyReport", back_populates="project", cascade="all, delete-orphan")
    folder = relationship("ProjectFolder", back_populates="projects")


if IS_POSTGRES:
    from geoalchemy2 import Geometry

    Project.boundary_geom = Column("boundary_geom", Geometry("POLYGON", srid=4326), nullable=True)


class SiteAnalysis(Base):
    __tablename__ = "site_analyses"

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    area_sqm = Column(Float, nullable=True)
    perimeter_m = Column(Float, nullable=True)
    elevation_min_m = Column(Float, nullable=True)
    elevation_max_m = Column(Float, nullable=True)
    slope_percent_estimate = Column(Float, nullable=True)
    nearby_roads_json = Column(JSON, nullable=True)
    existing_buildings_json = Column(JSON, nullable=True)
    risks_json = Column(JSON, nullable=True)
    raw_geojson = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    project = relationship("Project", back_populates="site_analyses")


class DesignScenario(Base):
    __tablename__ = "design_scenarios"

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    input_parameters_json = Column(JSON, nullable=True)
    design_output_json = Column(JSON, nullable=True)
    assumptions_json = Column(JSON, nullable=True)
    status = Column(String(50), default="pending", nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    project = relationship("Project", back_populates="scenarios")
    estimates = relationship("QuantityEstimate", back_populates="scenario", cascade="all, delete-orphan")
    model_revisions = relationship("ModelRevision", back_populates="scenario", cascade="all, delete-orphan")


class ModelRevision(Base):
    """Immutable editable-model snapshot for a design scenario."""

    __tablename__ = "model_revisions"
    __table_args__ = (
        UniqueConstraint("design_scenario_id", "revision_number", name="uq_model_revision_number"),
        UniqueConstraint("project_id", "id", name="uq_model_revision_project_id"),
    )

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    design_scenario_id = Column(Integer, ForeignKey("design_scenarios.id"), nullable=False, index=True)
    revision_number = Column(Integer, nullable=False)
    document_json = Column(JSON, nullable=False)
    source = Column(String(32), default="manual_edit", nullable=False)
    prompt = Column(Text, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, index=True)

    scenario = relationship("DesignScenario", back_populates="model_revisions")


class BuildingPlan(Base):
    """Immutable AI proposal; approval pins a single generation job."""
    __tablename__ = "building_plans"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    parent_id = Column(Integer, ForeignKey("building_plans.id"), nullable=True)
    prompt = Column(Text, nullable=False)
    spec_json = Column(JSON, nullable=False)
    context_json = Column(JSON, nullable=False)
    context_hash = Column(String(64), nullable=False)
    provider_model = Column(String(255), nullable=False)
    scenario_id = Column(Integer, ForeignKey("design_scenarios.id"), nullable=True)
    job_id = Column(String(64), nullable=True, unique=True)
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)


class QuantityEstimate(Base):
    __tablename__ = "quantity_estimates"

    id = Column(Integer, primary_key=True)
    design_scenario_id = Column(Integer, ForeignKey("design_scenarios.id"), nullable=False, index=True)
    model_revision_id = Column(Integer, ForeignKey("model_revisions.id"), nullable=True, index=True)
    concrete_m3 = Column(Float, default=0)
    cement_bags = Column(Float, default=0)
    steel_kg = Column(Float, default=0)
    rebar_kg = Column(Float, default=0)
    excavation_m3 = Column(Float, default=0)
    backfill_m3 = Column(Float, default=0)
    formwork_sqm = Column(Float, default=0)
    asphalt_m3 = Column(Float, default=0)
    pipe_length_m = Column(Float, default=0)
    pipe_diameter_mm = Column(Float, default=0)
    total_cost_estimate = Column(Float, default=0)
    line_items_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    scenario = relationship("DesignScenario", back_populates="estimates")


class GeneratedFile(Base):
    __tablename__ = "generated_files"

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    design_scenario_id = Column(Integer, ForeignKey("design_scenarios.id"), nullable=True)
    model_revision_id = Column(Integer, ForeignKey("model_revisions.id"), nullable=True, index=True)
    file_type = Column(String(50), nullable=False)  # glb|pdf|csv|json|geojson
    file_url = Column(Text, nullable=False)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    project = relationship("Project", back_populates="files")


class RateItem(Base):
    __tablename__ = "rate_items"

    id = Column(Integer, primary_key=True)
    region = Column(String(100), default="default", nullable=False)
    item_code = Column(String(50), nullable=False, index=True)
    item_name = Column(String(255), nullable=False)
    unit = Column(String(20), nullable=False)
    rate = Column(Float, nullable=False)
    currency = Column(String(10), default="INR", nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class ProjectTemplate(Base):
    __tablename__ = "project_templates"

    id = Column(Integer, primary_key=True)
    project_type = Column(String(50), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    default_parameters_json = Column(JSON, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class SurveyDataset(Base):
    __tablename__ = "survey_datasets"

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    kind = Column(String(32), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    storage_key = Column(String(512), nullable=True)
    source = Column(String(255), nullable=True)
    capture_date = Column(DateTime(timezone=True), nullable=True)
    crs_epsg = Column(Integer, nullable=True)
    pixel_size_m = Column(Float, nullable=True)
    rmse_h_m = Column(Float, nullable=True)
    rmse_v_m = Column(Float, nullable=True)
    accuracy_tier = Column(String(32), default="gis_grade", nullable=False)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    project = relationship("Project", back_populates="survey_datasets")
    layers = relationship("EngineeringLayer", back_populates="survey_dataset")


# Versioned terrain is introduced beside SurveyDataset.  The legacy table is
# intentionally retained until an audited backfill and cutover are complete.
class TerrainDataset(Base):
    __tablename__ = "terrain_datasets"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    kind = Column(String(32), nullable=False, default="SURVEY_TERRAIN")
    legacy_provenance = Column(Boolean, nullable=False, default=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    archived_at = Column(DateTime(timezone=True), nullable=True)
    versions = relationship("TerrainDatasetVersion", back_populates="dataset", cascade="all, delete-orphan")


class TerrainDatasetVersion(Base):
    __tablename__ = "terrain_dataset_versions"
    __table_args__ = (UniqueConstraint("terrain_dataset_id", "version", name="uq_terrain_dataset_version"),)
    id = Column(Integer, primary_key=True)
    terrain_dataset_id = Column(Integer, ForeignKey("terrain_datasets.id"), nullable=False, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    version = Column(Integer, nullable=False, default=1)
    processing_state = Column(String(32), nullable=False, default="UPLOADED")
    horizontal_crs_type = Column(String(32), nullable=False, default="UNKNOWN")
    horizontal_crs_code = Column(String(64), nullable=True)
    vertical_reference_json = Column(JSON, nullable=True)
    vertical_resolution_state = Column(String(32), nullable=False, default="NOT_CHECKED")
    source_unit = Column(String(32), nullable=False, default="UNKNOWN")
    coverage_geojson = Column(JSON, nullable=True)
    cesium_ion_asset_id = Column(Integer, nullable=True)
    source_file_name = Column(String(255), nullable=True)
    source_file_hash = Column(String(128), nullable=True)
    validation_state = Column(String(32), nullable=False, default="NOT_RUN")
    ready_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    dataset = relationship("TerrainDataset", back_populates="versions")


class ActiveTerrainConfiguration(Base):
    __tablename__ = "active_terrain_configuration"
    project_id = Column(Integer, ForeignKey("projects.id"), primary_key=True)
    terrain_dataset_id = Column(Integer, ForeignKey("terrain_datasets.id"), nullable=False)
    terrain_version_id = Column(Integer, ForeignKey("terrain_dataset_versions.id"), nullable=False)
    activated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    activated_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    revision = Column(Integer, nullable=False, default=1)

class ModelPlacement(Base):
    __tablename__ = "model_placements"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    model_revision_id = Column(Integer, ForeignKey("model_revisions.id"), nullable=False, unique=True, index=True)
    placement_mode = Column(String(24), nullable=False, default="GROUND_RELATIVE")
    height_reference = Column(String(24), nullable=False, default="TERRAIN")
    placement_state = Column(String(24), nullable=False, default="UNPLACED")
    anchor_longitude = Column(Float, nullable=False)
    anchor_latitude = Column(Float, nullable=False)
    anchor_elevation = Column(Float, nullable=True)
    elevation_resolution = Column(String(24), nullable=False, default="UNKNOWN", server_default="UNKNOWN")
    elevation_provenance_json = Column(JSON, nullable=True)
    anchor_vertical_reference_json = Column(JSON, nullable=True)
    anchor_heading_deg = Column(Float, nullable=False, default=0)
    elevation_offset = Column(Float, nullable=False, default=0)
    anchor_locked = Column(Boolean, nullable=False, default=True)
    terrain_dataset_id = Column(Integer, ForeignKey("terrain_datasets.id"), nullable=True)
    terrain_version_id = Column(Integer, ForeignKey("terrain_dataset_versions.id"), nullable=True)
    local_transform_json = Column(JSON, nullable=False, default=dict)
    accepted_ground_sample_id = Column(Integer, nullable=True)
    legacy_placement = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

class GroundSample(Base):
    __tablename__ = "ground_samples"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    placement_id = Column(Integer, ForeignKey("model_placements.id"), nullable=True, index=True)
    longitude = Column(Float, nullable=False)
    latitude = Column(Float, nullable=False)
    elevation = Column(Float, nullable=True)
    status = Column(String(24), nullable=False, default="NOT_SAMPLED")
    source = Column(String(24), nullable=False, default="NONE")
    terrain_dataset_id = Column(Integer, ForeignKey("terrain_datasets.id"), nullable=True)
    terrain_version_id = Column(Integer, ForeignKey("terrain_dataset_versions.id"), nullable=True)
    vertical_reference_json = Column(JSON, nullable=True)
    failure_reason = Column(Text, nullable=True)
    sampled_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)


class TerrainSourceFile(Base):
    __tablename__ = "terrain_source_files"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    terrain_version_id = Column(Integer, ForeignKey("terrain_dataset_versions.id"), nullable=False)
    storage_key = Column(Text, nullable=False)
    sha256 = Column(String(64), nullable=False)
    metadata_json = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)


class SurveyControlPoint(Base):
    __tablename__ = "survey_control_points"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    role = Column(String(32), nullable=False)
    reference_json = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)


class SurveyValidationRun(Base):
    __tablename__ = "survey_validation_runs"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    terrain_version_id = Column(Integer, ForeignKey("terrain_dataset_versions.id"), nullable=False)
    algorithm_version = Column(String(64), nullable=False)
    actor_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(String(24), nullable=False)
    result_json = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)


class SurveyCheckpointResidual(Base):
    __tablename__ = "survey_checkpoint_residuals"
    id = Column(Integer, primary_key=True)
    validation_run_id = Column(Integer, ForeignKey("survey_validation_runs.id"), nullable=False, index=True)
    checkpoint_id = Column(Integer, ForeignKey("survey_control_points.id"), nullable=False)
    status = Column(String(24), nullable=False)
    result_json = Column(JSON, nullable=False)


class EngineeringAnalysis(Base):
    __tablename__ = "engineering_analyses"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    model_revision_id = Column(Integer, ForeignKey("model_revisions.id"), nullable=True)
    terrain_version_id = Column(Integer, ForeignKey("terrain_dataset_versions.id"), nullable=True)
    analysis_type = Column(String(64), nullable=False)
    algorithm_version = Column(String(64), nullable=False)
    constraint_versions_json = Column(JSON, nullable=False, default=list)
    dependency_ids_json = Column(JSON, nullable=False, default=list)
    status = Column(String(24), nullable=False, default="UNKNOWN")
    result_json = Column(JSON, nullable=False)
    actor_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)


class StructureGroundCheck(Base):
    __tablename__ = "structure_ground_checks"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    analysis_id = Column(Integer, ForeignKey("engineering_analyses.id"), nullable=False)
    component_id = Column(String(255), nullable=False)
    ground_sample_id = Column(Integer, ForeignKey("ground_samples.id"), nullable=True)
    status = Column(String(24), nullable=False)
    result_json = Column(JSON, nullable=False)


class ConstraintDataset(Base):
    __tablename__ = "constraint_datasets"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    version = Column(Integer, nullable=False, default=1)
    kind = Column(String(64), nullable=False)
    metadata_json = Column(JSON, nullable=False)
    geometry_json = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)


class EngineeringAuditEvent(Base):
    __tablename__ = "engineering_audit_events"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    actor_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(String(100), nullable=False)
    terrain_version_id = Column(Integer, ForeignKey("terrain_dataset_versions.id"), nullable=True)
    before_json = Column(JSON, nullable=True)
    after_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)


class SavedCameraView(Base):
    __tablename__ = "saved_camera_views"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    camera_json = Column(JSON, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)


class ProjectMapPreferences(Base):
    __tablename__ = "project_map_preferences"
    project_id = Column(Integer, ForeignKey("projects.id"), primary_key=True)
    preferences_json = Column(JSON, nullable=False, default=dict)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)


class EngineeringLayer(Base):
    __tablename__ = "engineering_layers"

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    survey_dataset_id = Column(Integer, ForeignKey("survey_datasets.id"), nullable=True, index=True)
    layer_type = Column(String(64), nullable=False, index=True)
    name = Column(String(255), default="", nullable=False)
    width_m = Column(Float, nullable=True)
    properties_json = Column(JSON, nullable=True)
    accuracy_tier = Column(String(32), default="gis_grade", nullable=False)
    source = Column(String(255), nullable=True)
    capture_date = Column(DateTime(timezone=True), nullable=True)
    crs_epsg = Column(Integer, nullable=True)
    pixel_size_m = Column(Float, nullable=True)
    rmse_h_m = Column(Float, nullable=True)
    rmse_v_m = Column(Float, nullable=True)
    geom_geojson = Column(JSON, nullable=True)
    geom_wgs84_geojson = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    project = relationship("Project", back_populates="engineering_layers")
    survey_dataset = relationship("SurveyDataset", back_populates="layers")


if IS_POSTGRES:
    EngineeringLayer.geom = Column("geom", Geometry("GEOMETRY", srid=0), nullable=True)


class GroundControlPoint(Base):
    __tablename__ = "ground_control_points"

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    name = Column(String(64), nullable=False)
    source = Column(String(32), default="manual", nullable=False)
    lng = Column(Float, nullable=False)
    lat = Column(Float, nullable=False)
    ellipsoid_h_m = Column(Float, nullable=True)
    easting_m = Column(Float, nullable=True)
    northing_m = Column(Float, nullable=True)
    orthometric_h_m = Column(Float, nullable=True)
    horizontal_accuracy_m = Column(Float, nullable=True)
    vertical_accuracy_m = Column(Float, nullable=True)
    map_derived_e_m = Column(Float, nullable=True)
    map_derived_n_m = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    project = relationship("Project", back_populates="ground_control_points")


class AccuracyReport(Base):
    __tablename__ = "accuracy_reports"

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    tier_result = Column(String(32), nullable=False)
    passed = Column(Boolean, default=False, nullable=False)
    report_json = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    project = relationship("Project", back_populates="accuracy_reports")


class UsageEvent(Base):
    __tablename__ = "usage_events"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True, index=True)
    event_type = Column(String(64), nullable=False, index=True)
    units = Column(Integer, default=1, nullable=False)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, index=True)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    action = Column(String(100), nullable=False, index=True)
    entity_type = Column(String(100), nullable=True, index=True)
    entity_id = Column(String(100), nullable=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True, index=True)
    metadata_json = Column(JSON, nullable=True)
    ip_address = Column(String(64), nullable=True)
    user_agent = Column(String(512), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, index=True)


# Core tables are deliberate: foundation persistence has no behavioral ORM
# services yet. Existing terrain/models remain the sole authority.
from app.db.stage1_schema_v1 import register, install_guards
from sqlalchemy import event

STAGE1_TABLES = register(Base.metadata)


@event.listens_for(Base.metadata, "after_create")
def _stage1_guards(metadata, connection, **kwargs):
    from sqlalchemy import inspect
    if inspect(connection).has_table("site_selection_versions"):
        install_guards(connection, STAGE1_TABLES)
