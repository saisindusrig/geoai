from copy import deepcopy
import json
from pathlib import Path
import pytest
from app.services.design.floor_transfer import evidence
from app.api.routes import spatial_frames as route
from app.db.models import EngineeringAnalysis,ModelRevision
from test_physical_column import seed
from fastapi import HTTPException

DATA=json.loads((Path(__file__).resolve().parents[2]/'docs/spatial-frame/demo.json').read_text())
@pytest.mark.parametrize('review',DATA)
def test_all_saved_case_joint_equilibrium_and_exact_tributaries(review):
 for case in review['analysis']['result']['cases']:
  source=deepcopy(case);r=evidence(case);assert r['status']=='VERIFIED';assert case==source
  assert max(r['comparisons'].values())<1e-6
  for s in r['slabs']:
   assert s['area_m2']==pytest.approx(16);assert s['allocation_residual_n']==pytest.approx(0)
   assert sum(t['downward_force_n'] for t in s['strips'])==pytest.approx(s['applied_downward_n'])
   for t in s['strips']:assert t['area_m2']==pytest.approx(8);assert t['line_load_n_m']==pytest.approx(s['pressure_pa']*2)
  assert not r['capabilities']['diaphragm'];assert not r['capabilities']['slab_structural_analysis'];assert not r['capabilities']['per_load_force_attribution']

@pytest.mark.parametrize('corrupt',['joint_force','uniform','unsupported','axis','nan_reaction','nan_pressure','length'])
def test_does_not_infer_or_repair_broken_saved_evidence(corrupt):
 c=deepcopy(DATA[1]['analysis']['result']['cases'][0])
 if corrupt=='joint_force':c['members'][0]['end_forces'][0]+=100
 if corrupt=='uniform':c['members'][0]['uniform_global_n_m'][2]-=100
 if corrupt=='unsupported':c['status']='STALE'
 if corrupt=='axis':c['members'][0]['axes'][0][0]=999
 if corrupt=='nan_reaction':c['nodes'][0]['reaction'][0]=float('nan')
 if corrupt=='nan_pressure':c['slabs'][0]['pressure_pa']=float('nan')
 if corrupt=='length':next(m for m in c['members'] if m['id']==c['slabs'][0]['beams'][0])['length_m']+=1
 if corrupt in ('unsupported','axis','nan_reaction','nan_pressure','length'):
  with pytest.raises(ValueError):evidence(c)
 else:assert evidence(c)['status']=='VERIFICATION_FAILED'

def test_read_only_owned_revision_bound_endpoint(db_session):
 seed(db_session);saved=deepcopy(DATA[1]['analysis']['result']);rev=db_session.get(ModelRevision,1)
 from app.services.design.opensees_benchmark import digest
 saved.update(model_document_sha256=digest(rev.document_json),proposal_id=11)
 p=EngineeringAnalysis(id=11,project_id=1,model_revision_id=1,analysis_type=route.PROPOSAL,algorithm_version='test',status='SOLVER_COMPLETED',result_json={'model_document_sha256':saved['model_document_sha256']},actor_user_id=1)
 a=EngineeringAnalysis(id=12,project_id=1,model_revision_id=1,analysis_type=route.RUN,algorithm_version='test',status='VERIFIED',result_json=saved,actor_user_id=1);db_session.add_all([p,a]);db_session.commit();before=db_session.query(EngineeringAnalysis).count()
 result=route.floor_evidence(1,12,db_session,1);assert len(result['cases'])==3;assert db_session.query(EngineeringAnalysis).count()==before;assert a.result_json==saved
 with pytest.raises(HTTPException):route.floor_evidence(1,12,db_session,99)
 a.status='STALE';db_session.commit()
 with pytest.raises(HTTPException):route.floor_evidence(1,12,db_session,1)
