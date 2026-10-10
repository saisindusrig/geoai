"""Offline Phase 4A demonstrations. No provider, database, approval or publication.

Run with --native-proof for the existing bounded worker. Only synthetic fixture
metrics are written; native artifact bytes are discarded after verification.
"""
import argparse
from pathlib import Path
import json
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.experimental.bim_authoring import FrozenAuthoringContext, prepare_candidate, capabilities, compile_offline_proof, proposal_summary, review_offline
from app.experimental.bim_authoring_fixtures import authoring_case
from app.domain.bim_authoring import AuthoringBundle
from app.experimental.cad_contract import Source


def verify(native=False):
    context=FrozenAuthoringContext(Source(project_id=1,revision_id=1,revision_document_hash="0"*64,
        design_id="offline-synthetic-source",design_version=1,source_model_revision_id="1"),"synthetic-area-selection","AREA",enabled=True)
    output=dict(schemaVersion="bim-authoring-demonstration/1",syntheticSource=True,productionCadBuild=False,capabilities=capabilities(),cases=[])
    for name in ("bridge","platform","mixed","unregistered"):
        candidate=prepare_candidate(authoring_case(name),context)
        results,blobs=compile_offline_proof(candidate) if native else (None,{})
        review=proposal_summary(candidate,results)
        output["cases"].append(dict(case=name,componentCount=len(candidate.geometry.definitions),assetCount=len(candidate.model.assets),
            assemblyCount=len(candidate.model.assemblies),geometryStatus=review["geometryStatus"],
            nativeArtifactCount=len(blobs),componentResults=[dict(id=r.component_id,volumeM3=r.volume_m3,boundsM=r.bounds_m,
                dimensionsM=r.dimensions_m,solidCount=r.solid_count,geometryValid=r.geometry_valid) for r in (results or [])],
            unresolvedConnectionCount=len(review["unresolvedConnections"]),finalizationBlocked=review["finalizationBlocked"],engineeringStatus="UNVERIFIED"))
    unsupported=review_offline(authoring_case("unsupported"),context)
    assert unsupported["geometryStatus"] == "REJECTED"
    output["cases"].append(dict(case="unsupported",review=unsupported))
    for kind in ("dimensions","references","dependencies","omitted-support"):
        data=authoring_case("platform").model_dump(mode="json")
        first=data["expansions"][0]["components"][0]
        if kind == "dimensions":first["parameters"][0]["value"]=-1
        if kind == "references":first["material_id"]="unknown-material"
        if kind == "dependencies":
            edge=data["relationships"]["dependencies"][0]
            data["relationships"]["dependencies"].append({**edge,"id":"reverse","source_component_id":edge["target_component_id"],"target_component_id":edge["source_component_id"]})
        if kind == "omitted-support":data["relationships"]["connections"]=[]
        rejected=review_offline(data,context)
        assert rejected["geometryStatus"] == "REJECTED"
        output["cases"].append(dict(case="invalid-"+kind,review=rejected))
    return output


if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--native-proof",action="store_true")
    parser.add_argument("--export-schema",action="store_true")
    args=parser.parse_args()
    root=Path(__file__).resolve().parents[2]
    if args.export_schema:
        (root/"docs/contracts/bim-authoring.schema.json").write_text(json.dumps(AuthoringBundle.model_json_schema(by_alias=True),indent=2)+"\n",encoding="utf-8")
    results=verify(args.native_proof)
    path=root/"backend/.cad-proof-output/4a-authoring-demonstrations.json"
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(results,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(dict(output=str(path),nativeProof=args.native_proof,cases=[{k:v for k,v in c.items() if k in {"case","componentCount","geometryStatus"}} for c in results["cases"]])))
