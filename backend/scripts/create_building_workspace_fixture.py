"""Local deterministic acceptance fixture; never invokes a model provider."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tests"))
from app.db.session import SessionLocal
from app.db.models import User, Project, DesignScenario
from app.domain.site_workspace import SelectionInput, ConversationInput, MessageInput
from app.domain.assistant_runtime import ProposalRequest, ApplicationApproval
from app.services.site_profiles.selection import save_selection
from app.services.site_profiles.service import SiteProfileService
from app.services.assistant.conversations import ConversationService
from app.services.assistant.proposals import ProposalService
from test_building_specialist_v1 import specification
from test_site_workspace import AREA, WGS84

with SessionLocal() as db:
    user = db.query(User).order_by(User.id).first()
    if not user:
        raise RuntimeError("A local workspace user is required")
    project = Project(user_id=user.id, name="Building V1 workspace acceptance", project_type="building",
                      center_lng=77.001, center_lat=12.0005, boundary_geojson=AREA)
    db.add(project); db.flush()
    scenario = DesignScenario(project_id=project.id, name="Deterministic building acceptance", status="draft")
    db.add(scenario); db.commit()
    selection = save_selection(db, project.id, user.id, SelectionInput(selection={"kind":"AREA","geometry":AREA}, original_crs=WGS84))
    profiles = SiteProfileService()
    prepared, _ = profiles.prepare(db, project.id, user.id, selection["id"])
    profiles.build(db, project.id, prepared["id"], prepared["jobId"])
    profile = profiles.read(db, project.id, prepared["id"])["version"]
    conversations = ConversationService()
    conversation = conversations.create(db, project.id, user.id, ConversationInput(client_request_id="acceptance"))
    message = conversations.submit(db, project.id, user.id, conversation["id"], MessageInput(client_request_id="fixture",
        parts=[{"kind":"TEXT","text":"Create a two-floor office concept using the supplied deterministic dimensions."}],
        context={"siteProfileVersionId":profile["id"],"siteSelectionVersionId":profile["selectionVersion"]["id"],"scenarioId":str(scenario.id)}))
    spec = specification()
    spec["spaces"] = [{"id":f"room-{floor}-{side}","name":"Office zone","floor":floor,
        "x":5+6*side,"y":5,"width":6,"depth":10} for floor in range(2) for side in range(2)]
    spec["walls"] += [{"id":f"partition-{floor}","floor":floor,"start":[11,5],"end":[11,15],"thickness":.15} for floor in range(2)]
    proposals = ProposalService()
    view = proposals.create(db, project.id, user.id, ProposalRequest(client_request_id="fixture",message_id=message["messageId"],
        title="Workspace acceptance office",rationale="Deterministic test fixture",assets=[{"assetType":"OFFICE_BUILDING","name":"Office","buildingSpec":spec}]))
    proposals.approve(db, project.id, user.id, ApplicationApproval(client_request_id="fixture",proposal_version_id=view["id"],
        proposal_hash=view["contentHash"],dependency_hash=view["dependencyHash"],validation_hash=view["validationHash"],alternative_id=None,
        acknowledged_assumption_version_ids=view["content"]["contract"]["assumptionVersionIds"],expected_model_revision_id=None))
    result = proposals.build(db, project.id, view["id"])
    print({"projectId":project.id,"scenarioId":scenario.id,"revisionId":result["modelRevisionId"]})
