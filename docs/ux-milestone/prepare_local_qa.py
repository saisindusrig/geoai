"""Create one explicitly named local UI test fixture, preserving original projects."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))
from app.db.models import Project, DesignScenario, ModelRevision
from app.db.session import SessionLocal

with SessionLocal() as db:
    project = db.query(Project).filter_by(name="[Local UX QA] Save and reload validation").first()
    if not project:
        project = Project(user_id=1, name="[Local UX QA] Save and reload validation", project_type="building", center_lat=12.97, center_lng=77.59)
        db.add(project); db.flush()
        scenario = DesignScenario(project_id=project.id, name="Disposable UX fixture", status="draft")
        db.add(scenario); db.flush()
        components = []
        for index, (name, color, material, metalness) in enumerate([
            ("QA steel beam", "#829bb2", "Steel visual reference", .7),
            ("QA concrete block", "#b5b4aa", "Concrete visual reference", 0),
            ("QA soil block", "#aa8057", "Soil visual reference", 0),
            ("QA conceptual block", "#8bacc5", "Conceptual placeholder", 0),
        ]):
            components.append(dict(id=f"ux-qa:{index}", parent_id=None, name=name, category="beam" if index==0 else "zone", visible=True, locked=False,
                geometry=dict(kind="box", size=[3, .4, .6]), transform=dict(position=[0,index*1.5,.5],rotation_deg=[0,0,0],scale=[1,1,1]),
                material=dict(name=material,color=color,roughness=.4 if index==0 else .9,metalness=metalness), quantity=dict(included=False),metadata=dict(engineeringStatus="UNVERIFIED")))
        document = dict(schema_version=1,project_id=project.id,scenario_id=scenario.id,project_type="building",units="metric",
            origin=dict(lng=77.59,lat=12.97,elevation_m=0,heading_deg=0),generator_parameters={},components=components,metadata=dict(source="local_ux_qa",frame="local_enu_meters"))
        db.add(ModelRevision(project_id=project.id,design_scenario_id=scenario.id,revision_number=1,source="manual_edit",user_id=1,document_json=document))
        db.commit()
    print(f"Local QA project: {project.id}")
