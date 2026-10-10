"""Seed one unapproved platform proposal. Uses a scripted provider; never inference.

Run only against a dedicated migrated local SQLite database (see companion guide).
"""
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tests"))

from app.core.config import settings
from app.db.models import User, Project, DesignScenario
from app.db.session import SessionLocal
from app.domain.site_workspace import SelectionInput, ConversationInput, MessageInput
from app.services.site_profiles.selection import save_selection
from app.services.site_profiles.service import SiteProfileService
from app.services.assistant.conversations import ConversationService
from app.services.assistant.ai3d_validation import site_summary
from app.services.assistant.runtime import queue_run, process
from app.services.assistant.policy import evaluate
from app.services.assistant.storage import owned_row, rows
from industrial_platform_design import platform_design
from test_assistant_runtime import FixtureProvider
from test_site_workspace import AREA, WGS84


def main():
    if not settings.DATABASE_URL.startswith("sqlite:///") or settings.AI_PROVIDER != "mock":
        raise RuntimeError("Use a dedicated local SQLite database and AI_PROVIDER=mock.")
    # Local fixture preparation must never inherit cloud object-storage credentials.
    settings.S3_ACCESS_KEY = settings.S3_SECRET_KEY = ""
    with SessionLocal() as db:
        user = db.query(User).filter_by(id=1).first()
        if not user:
            db.add(User(id=1, name="Platform fixture", email="platform@example.test"))
            db.commit()
        project = Project(user_id=1, name="Industrial maintenance platform - offline concept",
                          project_type="building", center_lng=77.001, center_lat=12.0005, boundary_geojson=AREA)
        db.add(project); db.flush()
        scenario = DesignScenario(project_id=project.id, name="5 m x 3 m conceptual platform", status="draft")
        db.add(scenario); db.commit()
        selected = save_selection(db, project.id, 1, SelectionInput(selection={"kind": "AREA", "geometry": AREA}, original_crs=WGS84))
        profiles = SiteProfileService()
        prepared, _ = profiles.prepare(db, project.id, 1, selected["id"])
        profiles.build(db, project.id, prepared["id"], prepared["jobId"])
        profile = profiles.read(db, project.id, prepared["id"])["version"]
        conversations = ConversationService()
        convo = conversations.create(db, project.id, 1, ConversationInput(client_request_id="platform"))
        posted = conversations.submit(db, project.id, 1, convo["id"], MessageInput(client_request_id="platform",
            parts=[{"kind": "TEXT", "text": "Create a 5 m x 3 m industrial maintenance platform concept with columns, beams and slab."}],
            context={"scenarioId": str(scenario.id), "siteSelectionVersionId": selected["id"], "siteProfileVersionId": profile["id"]}))
        message = owned_row(db, "conversation_messages", project.id, posted["messageId"])
        design = platform_design(site_summary(db, project.id, message["context"])["selectionReference"])
        arguments = {"title": "5 m x 3 m industrial maintenance platform", "rationale": "One conceptual platform with four columns, four beams and a slab; deck top at local visual Z approximately 3 m.",
            "warnings": ["Loads, foundations, clearances, structural adequacy and code compliance are unverified."],
            "assets": [{"assetType": "AI3D_DESIGN", "name": "Maintenance platform", "ai3dDesign": design}]}
        queue_run(db, project.id, 1, posted["runId"])
        asyncio.run(process(db, project.id, posted["runId"], FixtureProvider([evaluate(message)["intent"],
            {"toolCalls": [{"name": "create_proposal", "arguments": json.dumps(arguments)}]},
            {"text": "Review the platform dimensions and preview assumptions. Use the application approval control before generating."}])))
        run = owned_row(db, "assistant_runs", project.id, posted["runId"])
        if run["status"] != "COMPLETE":
            raise RuntimeError(run["error_code"])
        proposal = next(part["proposalVersionId"] for msg in rows(db, "conversation_messages", project.id)
                        for part in msg["parts"] if part["kind"] == "PROPOSAL")
        print(json.dumps({"projectId": project.id, "scenarioId": scenario.id, "proposalVersionId": proposal,
                          "componentCount": 9, "approved": False}))


if __name__ == "__main__":
    main()
