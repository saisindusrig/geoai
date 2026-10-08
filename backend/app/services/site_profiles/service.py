"""Capture → retrieve → derive → verify dependencies → commit immutable profile."""
import uuid
from datetime import datetime, timezone
import sqlalchemy as sa
from sqlalchemy.orm import Session
from app.db.models import EngineeringAnalysis
from app.domain.site_workspace import SiteProfileVersion, ElevationSample
from app.domain.stage1 import MissingSiteInformation, DependencyManifest
from app.services.assistant.storage import digest, identity, insert, lock_project, now, owned_row, rows, table, update, error
from app.services.site_profiles.evidence import EvidenceCollector, WGS84, UNKNOWN_VERTICAL, known, unknown, vertical_reference
from app.services.site_profiles.derivation import SiteDerivationService
from app.services.site_profiles.retrieval import SiteRetrievalService, capture
from app.services.survey.engineering_evidence import readiness
from app.services import jobs


def missing_information(profile_id, elevation_known, accuracy_known):
    definitions = [
        ("SOIL_BEARING_CAPACITY","Foundation sizing requires a geotechnical bearing-capacity assessment.",["FOUNDATION_ANALYSIS"],["GEOTECH_REPORT"]),
        ("GROUNDWATER","Foundation and excavation analysis needs groundwater evidence.",["FOUNDATION_ANALYSIS"],["GEOTECH_REPORT"]),
        ("UTILITIES","An empty public map is not a utility clearance.",["CONSTRUCTION_DOCUMENTATION"],["UTILITY_SURVEY"]),
        ("DESIGN_FLOOD_LEVEL","Hydraulic analysis requires an authoritative design flood level.",["HYDRAULIC_ANALYSIS"],["AUTHORITY_SOURCE"]),
        ("OWNERSHIP","Property rights have not been verified.",["CONSTRUCTION_DOCUMENTATION"],["AUTHORITY_SOURCE"]),
        ("LOCAL_CODE","Applicable local requirements have not been verified.",["CONSTRUCTION_DOCUMENTATION"],["AUTHORITY_SOURCE"])]
    if not accuracy_known:
        definitions.append(("SURVEY_ACCURACY","Independent survey accuracy has not been established.",["GEOMETRY_CHECK","CONSTRUCTION_DOCUMENTATION"],["SURVEY_UPLOAD","VALIDATED_CALCULATION"]))
    if not elevation_known:
        definitions.append(("ELEVATION","Compatible terrain elevation is unavailable or only partially sampled.",["GEOMETRY_CHECK","FOUNDATION_ANALYSIS","HYDRAULIC_ANALYSIS"],["SURVEY_UPLOAD"]))
    return [MissingSiteInformation.model_validate({"id":identity(profile_id,kind),"profileVersionId":profile_id,"type":kind,
        "severity":"WARNING","whyNeeded":why,"requiredFor":operations,"blockingLevel":"GEOMETRY" if "GEOMETRY_CHECK" in operations else "ENGINEERING",
        "resolutionMethod":methods,"status":"OPEN"}).model_dump(mode="json",by_alias=True) for kind,why,operations,methods in definitions]


def dependency_capture(snapshot,selection):
    entries=[]
    for kind,key in (("BOUNDARY","project"),("MODEL","model"),("PLACEMENT","placement"),("TERRAIN","active"),
                     ("TERRAIN","terrain"),("SURVEY_EVIDENCE","sources"),("SURVEY_EVIDENCE","validation"),
                     ("SURVEY_EVIDENCE","surveys"),("CONSTRAINT","constraints"),("SURVEY_EVIDENCE","context")):
        data=snapshot[key]
        hashed=digest(data)
        entries.append({"kind":kind,"id":f"project:{snapshot['project']['id']}:{key}","version":hashed,
            "contentHash":hashed,"policy":"MUST_MATCH_CURRENT","scope":"PROJECT"})
    entries.append({"kind":"SELECTION","id":selection["selectionId"],"version":str(selection["version"]),
        "contentHash":selection["contentHash"],"policy":"MUST_MATCH_CURRENT","scope":"PROJECT"})
    manifest=DependencyManifest.model_validate({"schemaVersion":"dependencies/1","entries":entries,"hash":digest(entries)})
    return {"manifest":manifest.model_dump(mode="json",by_alias=True),"snapshot":snapshot,
            "selectionVersionId":selection["id"],"algorithm":"site-profile/1"}


class SiteProfileService:
    def __init__(self, retrieval=None, derivation=None):
        self.retrieval=retrieval or SiteRetrievalService()
        self.derivation=derivation or SiteDerivationService()

    def prepare(self, db, project_id, actor_id, selection_version_id, profile_id=None):
        lock_project(db, project_id)
        selection=owned_row(db,"site_selection_versions",project_id,selection_version_id)
        pid=profile_id or identity("profile",project_id,selection["selection_id"])
        if profile_id:
            profile=owned_row(db,"site_profiles",project_id,pid)
            if profile["selection_id"]!=selection["selection_id"]:
                error(422,"SELECTION_MISMATCH","Profile belongs to another selection")
        t=table("site_profiles")
        profile=db.execute(sa.select(t).where(t.c.id==pid,t.c.project_id==project_id)).mappings().first()
        queued_at=(profile["refresh_context"] or {}).get("queuedAt") if profile else None
        lease_active=bool(queued_at and (datetime.now(timezone.utc)-datetime.fromisoformat(queued_at)).total_seconds()<120)
        if profile and profile["refresh_state"] in {"QUEUED","RUNNING"} and lease_active:
            db.commit()
            return {"id":pid,"jobId":profile["refresh_job_id"],"refreshState":profile["refresh_state"]},False
        if not profile:
            insert(db,"site_profiles",id=pid,project_id=project_id,selection_id=selection["selection_id"],refresh_state="IDLE")
        snapshot=capture(db,project_id,selection["selection_id"])
        manifest=dependency_capture(snapshot,selection["selection_payload"])
        mid=identity("manifest",project_id,digest(manifest))
        if not db.execute(sa.select(table("dependency_manifests").c.id).where(table("dependency_manifests").c.id==mid)).first():
            insert(db,"dependency_manifests",id=mid,project_id=project_id,payload=manifest,content_hash=digest(manifest))
        job_id=uuid.uuid4().hex
        update(db,"site_profiles",project_id,pid,refresh_state="QUEUED",refresh_job_id=job_id,refresh_error=None,
               refresh_context={"manifestId":mid,"selectionVersionId":selection_version_id,"actorId":actor_id,"queuedAt":now()})
        db.commit()
        jobs.update_job(job_id,stage="queued",message="Creating site profile",user_id=actor_id,project_id=project_id)
        return {"id":pid,"jobId":job_id,"refreshState":"QUEUED"},True

    def build(self, db, project_id, profile_id, job_id):
        profile=owned_row(db,"site_profiles",project_id,profile_id)
        if profile["refresh_job_id"]!=job_id:
            return
        ctx=profile["refresh_context"]
        manifest=owned_row(db,"dependency_manifests",project_id,ctx["manifestId"])["payload"]
        snapshot=manifest["snapshot"]
        selection=owned_row(db,"site_selection_versions",project_id,ctx["selectionVersionId"])["selection_payload"]
        update(db,"site_profiles",project_id,profile_id,refresh_state="RUNNING")
        db.commit()
        collector=EvidenceCollector(project_id)
        metrics=self.derivation.derive(selection,collector)
        version=snapshot["terrain"]
        vertical=vertical_reference(version)
        extent={"id":selection["id"],"hash":selection["contentHash"],"horizontalCrs":WGS84}
        terrain_eid=collector.add({"kind":"USER_PROVIDED","sourceRecordId":f"active-terrain:{project_id}","actorId":str(ctx["actorId"])},
            {"active":snapshot["active"],"version":version}) if version else collector.add({"kind":"UNKNOWN","reason":"NOT_COLLECTED"},{"terrain":"No explicit active configuration"})
        try:
            with db.begin_nested():
                coverage_status,fraction=self.derivation.coverage(db,selection["canonicalGeometry"],version["coverage_geojson"] if version else None,metrics["calculationCrs"])
        except Exception:
            coverage_status,fraction="UNKNOWN",None
        coverage_eid=collector.derived([selection["transformationEvidenceId"],terrain_eid],
            {"terrainVersionId":version["id"] if version else None,"coverage":version["coverage_geojson"] if version else None,"status":coverage_status,"fraction":fraction}, "coverage/1")
        samples=[ElevationSample.model_validate(s).model_dump(mode="json",by_alias=True) for s in self.retrieval.sample(db,project_id,metrics["samples"],snapshot,collector)]
        valid=sum(s["elevation"]["sourceKind"]!="UNKNOWN" for s in samples)
        try:
            nearby=self.retrieval.context({**snapshot,"queryGeometry":selection["canonicalGeometry"],"calculationCrs":metrics["calculationCrs"]},extent,collector)
        except Exception:
            eid=collector.add({"kind":"UNKNOWN","reason":"RETRIEVAL_FAILED"},{"operation":"retained-project-context"})
            nearby={name:{"retrieval":"FAILED","features":[],"evidenceIds":[eid],"queryExtent":extent,"truncated":False}
                    for name in ("roads","waterways","buildings","utilities")}
        relief=self.derivation.relief(samples,collector,selection["selection"]["kind"])
        boundary=snapshot["project"]["boundary"]
        if boundary:
            bid=collector.add({"kind":"USER_PROVIDED","sourceRecordId":f"project:{project_id}:boundary:{digest(boundary)[:16]}","actorId":str(ctx["actorId"])},boundary)
            boundary_fact=known("boundary",{"id":str(project_id),"hash":digest(boundary),"horizontalCrs":WGS84},[bid],"USER_PROVIDED")
        else:
            boundary_fact=unknown("boundary")
        survey_refs=[]
        for survey in snapshot["surveys"]:
            # Legacy datasets often have no immutable source-file linkage. Preserve
            # their snapshot, but do not fabricate a SURVEY validation reference.
            eid=collector.add({"kind":"USER_PROVIDED","sourceRecordId":f"survey-dataset:{survey['id']}","actorId":str(ctx["actorId"])},survey)
            survey_refs.append({"id":str(survey["id"]),"version":None,"contentHash":digest(survey)})
        validation=next((r for r in snapshot["validation"] if version and r["terrain_version_id"]==version["id"]),None)
        source=next((r for r in snapshot["sources"] if version and r["terrain_version_id"]==version["id"]),None)
        if source:
            collector.add({"kind":"SURVEY","terrainDatasetId":str(version["terrain_dataset_id"]),"sourceFileId":str(source["id"]),
                "validationRunId":str(validation["id"]) if validation else None},{"fileDigest":source["sha256"],"validation":validation},vertical=vertical,
                status="VERIFIED" if validation and validation["status"]=="VALID" else "UNVERIFIED",dataset_id=str(version["terrain_dataset_id"]),version_id=str(version["id"]))
        constraints=[]
        for constraint in snapshot["constraints"]:
            eid=collector.add({"kind":"USER_PROVIDED","sourceRecordId":f"constraint:{constraint['id']}","actorId":str(ctx["actorId"])},constraint)
            constraints.append({"id":str(constraint["id"]),"kind":constraint["kind"],"contentHash":digest(constraint),"evidenceIds":[eid]})
        stats=(validation or {}).get("result_json",{})
        if "checkpoint_statistics" in stats:
            stats=stats["checkpoint_statistics"]
        state=readiness({"terrain_available":valid>0,"horizontal_crs_resolved":True,"vertical_reference_resolved":vertical["status"]=="RESOLVED",
            "units_resolved":bool(version and version["source_unit"]=="METRE"),"coverage_verified":coverage_status=="FULL" and valid==len(samples),
            "survey_authoritative":db.get_bind().dialect.name=="postgresql" and bool(source),
            "validation_status":(validation or {}).get("status"),"checkpoint_statistics":stats})
        provisional_missing=missing_information("pending",valid==len(samples) and valid>0 and coverage_status=="FULL",state in {"SURVEY_READY","ENGINEERING_READY"})
        assessment={"siteDataState":state,"ruleSetVersion":"site-readiness/1","databaseMode":"POSTGIS" if db.get_bind().dialect.name=="postgresql" else "DEMO",
            "operations":[{"operation":op,"eligible":op=="CONCEPT_LAYOUT" or (op=="GEOMETRY_CHECK" and not any(op in m["requiredFor"] for m in provisional_missing)),
                "reasons":[m["type"] for m in provisional_missing if op in m["requiredFor"]]}
                for op in ("CONCEPT_LAYOUT","GEOMETRY_CHECK","FOUNDATION_ANALYSIS","HYDRAULIC_ANALYSIS","CONSTRUCTION_DOCUMENTATION")]}
        # Hash substantive inputs/results, excluding row IDs/timestamps and job state.
        result_hash=digest({"manifest":manifest,"metrics":metrics,"samples":samples,"nearby":nearby,"readiness":assessment})
        vid=identity(profile_id,result_hash)
        lock_project(db,project_id)
        current=capture(db,project_id,profile["selection_id"])
        is_current=digest(current)==digest(snapshot) and current["selection"]==selection["id"]
        profile=owned_row(db,"site_profiles",project_id,profile_id)
        if profile["refresh_job_id"]!=job_id:
            db.rollback(); return
        versions=table("site_profile_versions")
        existing=db.execute(sa.select(versions).where(versions.c.profile_id==profile_id,versions.c.content_hash==result_hash)).mappings().first()
        if existing:
            update(db,"site_profiles",project_id,profile_id,refresh_state="IDLE",latest_version_id=existing["id"] if is_current else profile["latest_version_id"],refresh_error=None if is_current else "STALE_DEPENDENCIES")
            db.commit()
            return {"profileId":profile_id,"versionId":existing["id"],"current":is_current,"deduplicated":True}
        number=(db.execute(sa.select(sa.func.max(versions.c.version)).where(versions.c.profile_id==profile_id)).scalar() or 0)+1
        sample_id=identity("samples",profile_id,digest(samples))
        if not db.execute(sa.select(table("site_sample_sets").c.id).where(table("site_sample_sets").c.id==sample_id)).first():
            insert(db,"site_sample_sets",id=sample_id,project_id=project_id,profile_id=profile_id,content_hash=digest(samples),
                payload={"samples":samples,"selectionVersionId":selection["id"],"method":"bounded-sampling/1","nodataPolicy":"NO_INTERPOLATION","maximumSamples":26})
        if selection["selection"]["kind"] in {"ROUTE","CROSSING"}:
            relief["profileIds"]=[sample_id]
        analysis=EngineeringAnalysis(project_id=project_id,analysis_type="SITE_PROFILE_READINESS",algorithm_version="site-readiness/1",
            terrain_version_id=version["id"] if version else None,model_revision_id=snapshot["model"]["id"] if snapshot["model"] else None,
            result_json=assessment,status="VALID" if is_current else "STALE",actor_user_id=ctx["actorId"])
        db.add(analysis);db.flush()
        missing=missing_information(vid,valid==len(samples) and valid>0 and coverage_status=="FULL",state in {"SURVEY_READY","ENGINEERING_READY"})
        elevation_missing=next((m["id"] for m in missing if m["type"]=="ELEVATION"),None)
        if elevation_missing:
            for name in ("minElevation","maxElevation","meanSlope","maxSlope"):
                if relief[name]["sourceKind"]=="UNKNOWN":
                    relief[name]["missingInformationIds"]=[elevation_missing]
        active=snapshot["active"]
        data={"id":vid,"siteProfileId":profile_id,"projectId":str(project_id),"version":number,"contentHash":result_hash,"createdAt":now(),
            "selectionVersion":{"id":selection["id"],"version":selection["version"],"contentHash":selection["contentHash"]},
            "boundarySnapshot":boundary_fact,"location":metrics["location"],"coordinateSystem":WGS84,"calculationCrs":metrics["calculationCrs"],"verticalReference":vertical,
            "dimensions":metrics["dimensions"],"orientation":metrics["orientation"],"terrain":{"activeConfigurationRevision":active["revision"] if active else None,
                "datasetId":str(active["terrain_dataset_id"]) if active else None,"versionId":str(active["terrain_version_id"]) if active else None,
                "coverage":{"status":coverage_status,"coveredFraction":fraction,"checkedGeometryHash":selection["contentHash"],"methodVersion":"coverage/1","evidenceIds":[coverage_eid]},
                "sampleSetId":sample_id,"sampleSummary":{"requested":len(samples),"valid":valid,"failed":len(samples)-valid}},
            "relief":relief,"nearby":nearby,"surveyDatasetRefs":survey_refs,"constraints":constraints,"environmentalFacts":[],"planningFacts":[],"onSiteObjects":[],
            "evidenceIds":[selection["transformationEvidenceId"],*collector.records],"missingInformationIds":[m["id"] for m in missing],
            "readinessAssessmentId":str(analysis.id),"dependencyManifestId":ctx["manifestId"],
            "limitations":["Bounded samples do not establish continuous terrain or subsurface conditions.","Stored map context has unverified extent and age; absence is not clearance."] +
                (["SQLite demo: authoritative survey sampling and production spatial queries require PostGIS."] if db.get_bind().dialect.name!="postgresql" else [])}
        if selection["selection"]["kind"] not in {"ROUTE","CROSSING"}:
            data["limitations"].append("Slope is not derived for this selection type; no intermediate route is inferred from endpoints.")
        if snapshot["model"]:
            from app.services.assistant.conversations import resolve_objects
            object_ids=[str(c["id"]) for c in snapshot["model"]["document_json"].get("components",[])][:1000]
            data["onSiteObjects"],_=resolve_objects(db,project_id,str(snapshot["model"]["id"]),object_ids)
            data["limitations"].append("Object references snapshot the saved project model; their spatial intersection with this selection has not been validated.")
        payload=SiteProfileVersion.model_validate(data).model_dump(mode="json",by_alias=True)
        collector.persist(db)
        insert(db,"site_profile_versions",id=vid,project_id=project_id,profile_id=profile_id,version=number,selection_version_id=selection["id"],
            dependency_manifest_id=ctx["manifestId"],payload=payload,content_hash=result_hash)
        for eid in payload["evidenceIds"]:
            insert(db,"site_profile_evidence",id=identity(vid,eid),project_id=project_id,profile_version_id=vid,evidence_id=eid)
        for item in missing:
            insert(db,"site_missing_information",id=item["id"],project_id=project_id,profile_version_id=vid,payload=item)
        update(db,"site_profiles",project_id,profile_id,refresh_state="IDLE",latest_version_id=vid if is_current else profile["latest_version_id"],refresh_error=None if is_current else "STALE_DEPENDENCIES")
        db.commit()
        return {"profileId":profile_id,"versionId":vid,"current":is_current,"deduplicated":False}

    def read(self,db,project_id,profile_id,version=None):
        profile=owned_row(db,"site_profiles",project_id,profile_id)
        queued_at=(profile["refresh_context"] or {}).get("queuedAt")
        if profile["refresh_state"] in {"QUEUED","RUNNING"} and queued_at and (datetime.now(timezone.utc)-datetime.fromisoformat(queued_at)).total_seconds()>=120:
            profile["refresh_state"]="FAILED"
            profile["refresh_error"]="REFRESH_INTERRUPTED"
        t=table("site_profile_versions")
        q=sa.select(t).where(t.c.profile_id==profile_id,t.c.project_id==project_id)
        if version is not None:
            q=q.where(t.c.version==version)
        row=db.execute(q.order_by(t.c.version.desc())).mappings().first()
        if version is not None and not row:
            error(404,"NOT_FOUND","Profile version not found")
        payload=row["payload"] if row else None
        current=False
        if row:
            manifest=owned_row(db,"dependency_manifests",project_id,row["dependency_manifest_id"])["payload"]
            current=(profile["latest_version_id"]==row["id"] and digest(capture(db,project_id,profile["selection_id"]))==digest(manifest["snapshot"]))
        return {"id":profile_id,"selectionId":profile["selection_id"],"refreshState":profile["refresh_state"],"jobId":profile["refresh_job_id"],
                "errorCode":profile["refresh_error"],"current":current,"version":payload}


def run_profile_job(bind, project_id, profile_id, job_id):
    with Session(bind=bind) as db:
        try:
            jobs.update_job(job_id,stage="analyzing",message="Deriving site profile")
            result=SiteProfileService().build(db,project_id,profile_id,job_id)
            jobs.update_job(job_id,stage="completed",progress=100,message="Site profile saved",result=result)
        except Exception as exc:
            db.rollback()
            code="UNSUPPORTED_EXTENT" if str(exc)=="UNSUPPORTED_EXTENT" else "PROFILE_RETRIEVAL_FAILED"
            p=owned_row(db,"site_profiles",project_id,profile_id)
            if p["refresh_job_id"]==job_id:
                update(db,"site_profiles",project_id,profile_id,refresh_state="FAILED",refresh_error=code)
                db.commit()
            jobs.update_job(job_id,stage="failed",error=code,message="Site profile could not be completed; retry after checking site data")
