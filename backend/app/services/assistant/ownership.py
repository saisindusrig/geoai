"""Foundation authorization for nested domain references. No persistence APIs."""
import sqlalchemy as sa
from fastapi import HTTPException
from pydantic import BaseModel
from app.db.models import Project, Base

REFERENCE_TABLES = {
    "selection_id": "site_selections", "selection_version_id": "site_selection_versions",
    "profile_version_id": "site_profile_versions", "site_profile_version_id": "site_profile_versions",
    "evidence_ids": "site_evidence", "resolution_evidence_ids": "site_evidence",
    "input_evidence_ids": "site_evidence", "transformation_evidence_id": "site_evidence",
    "asset_id": "asset_instances", "model_revision_id": "model_revisions",
    "source_model_revision_id": "model_revisions", "expected_model_revision_id": "model_revisions",
    "source_scenario_id": "design_scenarios", "proposal_version_id": "design_proposal_versions",
    "parent_version_id": "design_proposal_versions", "alternative_id": "proposal_alternatives",
    "alternative_ids": "proposal_alternatives", "dependency_manifest_id": "dependency_manifests",
    "asset_specification_version_ids": "asset_specification_versions",
    "input_memory_version_ids": "project_memory_versions", "assumption_version_ids": "project_memory_versions",
    "acknowledged_assumption_version_ids": "project_memory_versions", "message_id": "conversation_messages",
    "survey_dataset_id": "survey_datasets", "source_file_id": "terrain_source_files",
    "validation_run_id": "survey_validation_runs", "assumption_id": "project_memory_items",
}


def validate_project_references(db, project_id: int, actor_id: int, contract: BaseModel):
    if not db.query(Project.id).filter_by(id=project_id, user_id=actor_id).first():
        raise HTTPException(404, "Project not found")

    def visit(value):
        if isinstance(value, list):
            for item in value:
                visit(item)
        elif isinstance(value, dict):
            if "project_id" in value and str(value["project_id"]) != str(project_id):
                raise HTTPException(404, "Referenced resource not found")
            for key, item in value.items():
                if key in REFERENCE_TABLES and item is not None:
                    table = Base.metadata.tables[REFERENCE_TABLES[key]]
                    for identity in item if isinstance(item, list) else [item]:
                        if not db.execute(sa.select(table.c.id).where(table.c.id == identity, table.c.project_id == project_id)).first():
                            raise HTTPException(404, "Referenced resource not found")
                visit(item)
            if "object_id" in value and "model_revision_id" in value:
                table = Base.metadata.tables["model_revisions"]
                document = db.execute(sa.select(table.c.document_json).where(table.c.id == value["model_revision_id"], table.c.project_id == project_id)).scalar_one()
                if not any(c.get("id") == value["object_id"] for c in document.get("components", [])):
                    raise HTTPException(404, "Referenced object not found in revision")

    visit(contract.model_dump())
