"""Read existing project sources. Failed retrieval never becomes an empty success."""
import math
import json
from datetime import datetime, timezone
import sqlalchemy as sa
from app.db.models import (Project, ModelRevision, ModelPlacement, ActiveTerrainConfiguration,
    TerrainDatasetVersion, TerrainSourceFile, SurveyValidationRun, SurveyDataset, ConstraintDataset, SiteAnalysis)
from app.services.assistant.storage import digest
from app.services.site_profiles.evidence import known, unknown, vertical_reference, UNKNOWN_VERTICAL
from app.services.survey.ground_resolver import resolve_ground


def record(row):
    return json.loads(json.dumps({c.name:getattr(row,c.name) for c in row.__table__.columns if c.name not in {"created_at","updated_at","activated_at","ready_at"}}, default=str)) if row else None


def capture(db, project_id, selection_id):
    db.expire_all()
    project = db.get(Project, project_id)
    model = db.query(ModelRevision).filter_by(project_id=project_id).order_by(ModelRevision.id.desc()).first()
    placement = db.query(ModelPlacement).filter_by(project_id=project_id,model_revision_id=model.id).first() if model else None
    active = db.get(ActiveTerrainConfiguration, project_id)
    version = db.query(TerrainDatasetVersion).filter_by(project_id=project_id,id=active.terrain_version_id).first() if active else None
    from app.services.assistant.storage import table
    t=table("site_selection_versions")
    latest=db.execute(sa.select(t.c.id).where(t.c.project_id==project_id,t.c.selection_id==selection_id).order_by(t.c.version.desc())).scalar()
    context=db.query(SiteAnalysis).filter_by(project_id=project_id).order_by(SiteAnalysis.id.desc()).first()
    return {"project":{"id":project.id,"boundary":project.boundary_geojson,"alignment":project.alignment_geojson,
                "locationName":project.location_name,"engineeringCrs":project.engineering_crs_epsg},
            "selection":latest,"model":record(model),"placement":record(placement),"active":record(active),"terrain":record(version),
            "sources":[record(r) for r in db.query(TerrainSourceFile).filter_by(project_id=project_id).order_by(TerrainSourceFile.id).limit(100)],
            "validation":[record(r) for r in db.query(SurveyValidationRun).filter_by(project_id=project_id).order_by(SurveyValidationRun.id.desc()).limit(100)],
            "surveys":[record(r) for r in db.query(SurveyDataset).filter_by(project_id=project_id).order_by(SurveyDataset.id).limit(100)],
            "constraints":[record(r) for r in db.query(ConstraintDataset).filter_by(project_id=project_id).order_by(ConstraintDataset.id).limit(100)],
            "context":None if not context else {"id":context.id,"capturedAt":context.created_at.isoformat(),"geojson":context.raw_geojson}}


class SiteRetrievalService:
    def sample(self, db, project_id, positions, snapshot, evidence):
        version = snapshot["terrain"]
        vertical = vertical_reference(version)
        samples = []
        for position in positions:
            p=position["position"]
            try:
                with db.begin_nested():
                    result = resolve_ground(db,project_id,p["longitude"],p["latitude"])
            except Exception:
                result={"elevation":None,"status":"FAILED","failure_reason":"RETRIEVAL_FAILED"}
            valid = (version and result.get("status")=="VALID" and result.get("terrain_version_id")==version["id"]
                and result.get("vertical_reference")==version["vertical_reference_json"]
                and vertical["status"]=="RESOLVED" and isinstance(result.get("elevation"),(int,float))
                and math.isfinite(result["elevation"]))
            if valid:
                # Reuse existing GroundSample observations for identical immutable-version inputs.
                from app.db.models import GroundSample
                row = db.query(GroundSample).filter_by(project_id=project_id, terrain_version_id=version["id"],
                    longitude=p["longitude"],latitude=p["latitude"],elevation=result["elevation"],status="VALID").first()
                if not row:
                    row=GroundSample(project_id=project_id,longitude=p["longitude"],latitude=p["latitude"],elevation=result["elevation"],
                        status="VALID",source=result["source"],terrain_dataset_id=version["terrain_dataset_id"],terrain_version_id=version["id"],
                        vertical_reference_json=result["vertical_reference"],sampled_at=datetime.now(timezone.utc))
                    db.add(row); db.flush()
                eid=evidence.add({"kind":"MEASURED","measurementId":str(row.id)},
                    {"position":p,"elevation":row.elevation,"resolver":"ground-resolver/1"},vertical=vertical,
                    dataset_id=str(version["terrain_dataset_id"]),version_id=str(version["id"]))
                fact=known("elevation",{"value":row.elevation,"unit":"m"},[eid],"MEASURED")
                sample_id=str(row.id)
            else:
                reason = "OUTSIDE_COVERAGE" if result.get("status")=="OUTSIDE_COVERAGE" else "RETRIEVAL_FAILED" if result.get("failure_reason")=="RETRIEVAL_FAILED" else "UNAVAILABLE"
                eid=evidence.add({"kind":"UNKNOWN","reason":reason}, {"position":p,"failure":result.get("failure_reason","Terrain unavailable")})
                fact=unknown("elevation",reason,[eid])
                sample_id=None
            samples.append({**position,"elevation":fact,"verticalReference":vertical if valid else UNKNOWN_VERTICAL,"groundSampleId":sample_id})
        return samples

    def context(self, snapshot, extent, evidence):
        nearby={name:{"retrieval":"NOT_REQUESTED","features":[],"evidenceIds":[],"queryExtent":extent,"truncated":False}
                for name in ("roads","waterways","buildings","utilities")}
        retained=snapshot["context"]
        if retained:
            raw=retained["geojson"] or {}
            if raw.get("mock") or not isinstance(raw.get("features"),list):
                eid=evidence.add({"kind":"UNKNOWN","reason":"RETRIEVAL_FAILED"},{"analysisId":retained["id"],"reason":"Legacy mock/unavailable context is not evidence"})
                for name in ("roads","waterways","buildings"):
                    nearby[name].update(retrieval="FAILED",evidenceIds=[eid])
            else:
                from shapely.geometry import shape, mapping
                from shapely.ops import transform
                from pyproj import Transformer
                projected=Transformer.from_crs("EPSG:4326",snapshot["calculationCrs"]["definition"],always_xy=True)
                inverse=Transformer.from_crs(snapshot["calculationCrs"]["definition"],"EPSG:4326",always_xy=True)
                query=transform(projected.transform,shape(snapshot["queryGeometry"])).buffer(500)
                query_geometry=mapping(transform(inverse.transform,query))
                features=[]
                for feature in raw["features"][:1000]:
                    try:
                        geometry=shape(feature["geometry"])
                        if geometry.is_valid and transform(projected.transform,geometry).intersects(query):
                            features.append(feature)
                    except (KeyError,TypeError,ValueError):
                        continue
                eid=evidence.add({"kind":"PUBLIC_MAP","provider":"OpenStreetMap","sourceUrl":"https://www.openstreetmap.org/copyright",
                    "license":"ODbL-1.0","queryExtentHash":digest(query_geometry)},
                    {"analysisId":retained["id"],"capturedAt":retained["capturedAt"],"features":features[:100],"retainedContextQuery":query_geometry,
                     "originalQueryExtent":"UNKNOWN","retainedResponseDigest":digest(raw)})
                for name in ("roads","waterways","buildings"):
                    nearby[name].update(retrieval="PARTIAL",evidenceIds=[eid],truncated=len(features)>100 or len(raw["features"])>1000)
                # Retain observations without asserting that an old query covered this selection.
                for f in features[:100]:
                    props=f.get("properties",{}); category=props.get("category")
                    name={"road":"roads","waterway":"waterways","building":"buildings"}.get(category)
                    if name and f.get("geometry"):
                        fid=str(props.get("osm_id") or digest(f))
                        attribute_fields={"road":["classification","width","access"],"waterway":["waterwayType","flowDirection"],"building":["height","storeys","use"]}[category]
                        attributes={"kind":category.upper(),**{key:unknown(key) for key in attribute_fields}}
                        mapped={"road":("classification","highway"),"waterway":("waterwayType","waterway"),"building":("use","building")}[category]
                        if props.get(mapped[1]):
                            attributes[mapped[0]]=known(mapped[0],props[mapped[1]],[eid],"PUBLIC_MAP","CONTEXT_ONLY")
                        nearby[name]["features"].append({"id":fid,"kind":category.upper(),
                            "attributes":attributes,
                            "geometry":known("geometry",{"id":fid,"hash":digest(f["geometry"]),"horizontalCrs":extent["horizontalCrs"]},[eid],"PUBLIC_MAP","CONTEXT_ONLY"),
                            "name":known("name",props["name"],[eid],"PUBLIC_MAP","CONTEXT_ONLY") if props.get("name") else unknown("name")})
        return nearby
