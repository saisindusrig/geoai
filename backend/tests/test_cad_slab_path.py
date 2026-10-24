import json
from pathlib import Path
from copy import deepcopy
import pytest
from app.services.design import slab_transfer as slab

ROOT=Path(__file__).resolve().parents[2]/'docs/cad-slab-path'
def document():return json.loads((ROOT/'verification-geometry.json').read_text(encoding='utf-8'))
def inputs():return json.loads((ROOT/'verification-inputs.json').read_text(encoding='utf-8'))

def test_original_missing_north_geometry_is_blocked():
 d=document();q=inputs();north=set(q['frames'][1]['component_ids']);d['components']=[c for c in d['components'] if c['id'] not in north]
 with pytest.raises(ValueError):slab.graphs(d,q)

def test_actual_cad_sources_widths_and_load_conservation():
 d=document();q=inputs();before=deepcopy(d);t,frames=slab.graphs(d,q)
 assert t['slab_source']['source_entity_id'].endswith(':95');assert t['size_m']==[6,4,.2];assert t['area_m2']==24;assert t['applied_kn']==120
 assert [s['width_m'] for s in t['strips']]==[2,2];assert [s['line_load_kn_m'] for s in t['strips']]==[10,10];assert t['conservation_error_kn']==0
 assert len(t['excluded_context_component_ids'])==45
 for f in frames:
  assert f['graph']['column_heights_m']==[3.26,3.2];assert f['graph']['beam_offsets_m'][0]==pytest.approx([-.15,-.01]);assert f['graph']['beam_offsets_m'][1]==pytest.approx([.15,.05]);assert all(m['cad_source']['source_entity_id'].startswith('dxf:') for m in f['graph']['members'])
 assert d==before

def test_actual_opensees_unequal_slabs_mesh_units_scaling_and_hand_reference():
 d=document();before=deepcopy(d);base=None
 for n,units,scale in [(1,'SI',1),(2,'SI',1),(4,'SI',1),(2,'N-mm',1),(2,'SI',.5)]:
  q=inputs();q['intensity_kn_m2']*=scale
  for f in q['frames']:f.update(elements_per_member=n,units=units)
  r=slab.run(d,q);assert r['status']=='VERIFIED';assert r['load_path_equilibrium']['passed'];assert r['reaction_total_kn']==pytest.approx(120*scale,abs=1e-7);assert not r['self_weight_included']
  heads=lambda r:[[v for node in [2,3] for v in next(x for x in f['result']['nodes'] if x['id']==node)['displacement_m']] for f in r['frames']]
  if base:
   for a,b in zip(heads(r),heads(base)):assert a==pytest.approx([v*scale for v in b],abs=1e-10)
  else:base=r
  for f in r['frames']:
   assert f['result']['solver_version']=='3.8.0';assert f['result']['unequal_frame_independent_verification']['passed'];assert max(map(abs,f['result']['equilibrium_residual_si']))<1e-5
  for b in r['beam_references']:
   assert b['hand']['reaction_y_n']==pytest.approx(30000*scale);assert b['hand']['left_end_moment_nm']==pytest.approx(30000*scale);assert b['hand']['midspan_displacement_m']==pytest.approx(-.000375*scale)
 assert d==before

@pytest.mark.parametrize('bad',['scope','context_approval','context_source','incomplete_context','hide_cad_support','width','width_source','pressure','direction','slab_source','column_source','connection','support','unknown_north','two_way','self_weight','shared','gap','opening','source_change'])
def test_rejected_inputs_and_unverified_geometry(bad):
 d=document();q=inputs();by={c['id']:c for c in d['components']}
 if bad=='scope':d['metadata'].pop('cad_slab_path_review')
 if bad=='context_approval':q['context_exclusion_approved']=False
 if bad=='context_source':q['context_exclusion_source']=None
 if bad=='incomplete_context':q['excluded_context_component_ids'].pop()
 if bad=='hide_cad_support':q['excluded_context_component_ids'].append(q['beam_ids'][0])
 if bad=='width':q['tributary_widths_m'][0]=1.9
 if bad=='width_source':q['tributary_width_source']=None
 if bad=='pressure':q['intensity_kn_m2']=0
 if bad=='direction':q['direction']='unknown'
 if bad=='slab_source':by[q['slab_id']]['metadata']['drawing_cad']['component_sha256']='bad'
 if bad=='column_source':by[q['frames'][0]['component_ids'][0]]['metadata']['drawing_cad']['source_entity_id']='absent'
 if bad=='connection':q['frames'][0]['connections'][0]['idealization_approved']=False
 if bad=='support':q['frames'][0]['supports']='soil'
 if bad=='unknown_north':q['beam_ids'][1]='unknown'
 if bad=='two_way':q['method']='two_way'
 if bad=='self_weight':q['density_kg_m3']=7850
 if bad=='shared':q['frames'][1]=deepcopy(q['frames'][0])
 if bad=='gap':by[q['beam_ids'][0]]['transform']['position'][2]-=.1
 if bad=='opening':by[q['slab_id']]['geometry']['openings']=[{}]
 if bad=='source_change':by[q['slab_id']]['geometry']['size'][0]=7
 with pytest.raises((ValueError,KeyError)):slab.graphs(d,q)

def test_cad_slab_source_review_authorization_and_artifacts(db_session,tmp_path,monkeypatch):
 from test_physical_column import seed
 from test_drawing_strength import source,correction,FILE
 from app.api.routes import engineering_study as study,slab_transfers as api
 from app.db.models import ModelRevision,EngineeringAnalysis
 from fastapi import HTTPException
 db=db_session;seed(db);rev=db.get(ModelRevision,1);d=document();d.update(project_id=1,scenario_id=1);rev.document_json=d;db.commit()
 monkeypatch.setattr(study,'ROOT',tmp_path);directory=tmp_path/'1';directory.mkdir();s=source();file=directory/(s['source_sha256']+'.dxf');file.write_bytes(FILE.read_bytes());src=study.record(1,rev,study.SOURCE,'REFERENCE_IMPORTED_NOT_ANALYTICAL_MODEL',s,db,1);study.record(1,rev,study.REVIEW,'REVIEWED_REFERENCE_ANALYSIS_BLOCKED',dict(inputs=correction(),source_reference_id=src.id),db,1)
 saved=api.save(1,api.Save(**inputs(),model_revision_id=1),db,1);assert len(saved['result']['cad_source_provenance']['component_sources'])==7
 with pytest.raises(HTTPException):api.run(1,api.Authorize(input_id=saved['id'],input_sha256='0'*64,authorize_solver=True),db,1)
 result=api.run(1,api.Authorize(input_id=saved['id'],input_sha256=saved['result']['input_sha256'],authorize_solver=True),db,1);assert result['status']=='VERIFIED';assert result['result']['load_path_equilibrium']['passed']
 beam=inputs()['beam_ids'][0];manifest=json.loads(api.artifact(1,beam,result['id'],'manifest.json',db=db,user_id=1)['contents']);assert manifest['model_revision_id']==1;assert manifest['slab_load_transfer']['slab_source']['source_entity_id'].endswith(':95')
 file.write_bytes(file.read_bytes()+b'\n');assert api.output(db.get(EngineeringAnalysis,result['id']),db,1)['status']=='STALE'
 file.write_bytes(FILE.read_bytes());assert api.output(db.get(EngineeringAnalysis,result['id']),db,1)['status']=='VERIFIED'
 study.record(1,rev,study.REVIEW,'REVIEWED_REFERENCE_ANALYSIS_BLOCKED',dict(inputs=correction(),source_reference_id=src.id),db,1);assert api.output(db.get(EngineeringAnalysis,result['id']),db,1)['status']=='STALE'
 with pytest.raises(HTTPException):api.run(1,api.Authorize(input_id=saved['id'],input_sha256=saved['result']['input_sha256'],authorize_solver=True),db,1)
