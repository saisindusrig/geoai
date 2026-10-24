import json,math
from pathlib import Path
from copy import deepcopy
import pytest
from app.services.design import slab_transfer as s,physical_frame as f
from test_gravity_frame import symmetric_gravity_hand

def document():return json.loads((Path(__file__).resolve().parents[2]/'docs/slab-transfer/source-geometry.json').read_text(encoding='utf-8'))
def fixture(doc):
 by={c['name']:c['id'] for c in doc['components']};frames=[]
 for names in [('column-sw','beam-south','column-se'),('column-nw','beam-north','column-ne')]:
  g=f.geometry(doc,[by[n] for n in names],allow_rigid_offsets=True)
  frames.append(dict(component_ids=g['component_ids'],sections=[dict(component_id=m['component_id'],shape='solid_rectangle',elastic_modulus_pa=200e9,area_m2=m['solid_rectangle_area_m2'],inertia_m4=m['solid_rectangle_inertia_m4'],material_name='Synthetic steel',material_source='Synthetic E=200 GPa verification assumption',section_source='Declared saved solid rectangular verification section') for m in g['members']],connections=[dict(**j,behavior='rigid_offset',offset_m=next(x['offset_m'] for x in g['connection_offsets'] if x['beam_endpoint']==j['beam_endpoint']),idealization_approved=True,source='Synthetic explicitly declared massless rigid arm') for j in g['candidate_joints']],supports='both_column_bases_fixed',support_source='Synthetic four fixed bases, not foundation capacity',elements_per_member=2,units='SI'))
 return dict(slab_id=by['platform-deck'],beam_ids=[by['beam-south'],by['beam-north']],intensity_kn_m2=5,source='Synthetic uniform imposed pressure, excludes slab self-weight',direction='local_enu_negative_up',method='one_way_symmetric_tributary_area',support_assumption='Synthetic one-way span North; only north/south beams participate, equal edge cantilevers included by tributary area; no transverse sharing or slab stiffness/capacity',excluded_beam_ids=[by['beam-east'],by['beam-west']],excluded_attachment_ids=[],no_openings_confirmed=True,symmetric_edge_overhang_approved=True,one_way_idealization_approved=True,purpose='SYNTHETIC_VERIFICATION_ONLY',frames=frames)

def check_hand(r):
 for item in r['frames']:
  a=item['result'];g=a['physical_to_analytical_graph'];h=symmetric_gravity_hand(g,a['applied_loads']);node=next(n for n in a['nodes'] if n['id']==2)
  assert node['displacement_m']==pytest.approx(h['left_head'],abs=1e-10)
  mid=min([p for e in a['elements'] if e['component_id']==item['beam_id'] for p in e['samples']],key=lambda p:abs(p['position_m'][0]-g['length_m']/2))
  assert mid['displacement_m'][1]==pytest.approx(h['midspan_v'],abs=1e-10)
  left=a['reactions'][0];assert [left['fx_n'],left['fy_n'],left['moment_nm']]==pytest.approx(h['left_reaction'],abs=1e-6)
  assert max(map(abs,a['equilibrium_residual_si']))<1e-5
 assert r['reaction_total_kn']==pytest.approx(r['transfer']['applied_kn'],abs=1e-6)

def test_saved_geometry_and_conservation():
 doc=document();q=fixture(doc);t=s.transfer(doc,q)
 assert t['area_m2']==24;assert t['support_spacing_m']==pytest.approx(3.7);assert t['edge_overhangs_m']==pytest.approx([.15,.15]);assert t['applied_kn']==120
 assert [v['line_load_kn_m'] for v in t['strips']]==[10,10];assert t['conservation_error_kn']==0
 assert sum(v['area_m2'] for v in t['strips'])==24

def test_attached_stairs_require_exact_exclusion_and_unknown_children_rejected():
 doc=document();q=fixture(doc);stair=dict(id='attached-stair',parent_id=q['slab_id'],category='stairs',metadata={'attachment_kind':'stairs'},geometry={'kind':'box','size':[1,.3,.04]},transform={'position':[0,-2.2,3.4],'rotation_deg':[0,0,0],'scale':[1,1,1]});doc['components'].append(stair)
 with pytest.raises(ValueError):s.graphs(doc,q)
 q['excluded_attachment_ids']=['attached-stair'];t,_=s.graphs(doc,q);assert t['applied_kn']==120
 stair['category']='slab'
 with pytest.raises(ValueError):s.graphs(doc,q)

def test_inspection_rejects_unknown_coordinate_frame():
 doc=document();doc['metadata']={};q=fixture(document())
 with pytest.raises(ValueError):s.geometry(doc,{k:q[k] for k in ('slab_id','beam_ids')})

def test_actual_solver_mesh_units_scaling():
 doc=document();q=fixture(doc);runs=[]
 for mesh,unit,scale in [(1,'SI',1),(2,'SI',1),(4,'SI',1),(2,'N-mm',1),(2,'SI',.5)]:
  x=deepcopy(q);x['intensity_kn_m2']*=scale
  for f in x['frames']:f.update(elements_per_member=mesh,units=unit)
  r=s.run(doc,x);assert r['status']=='VERIFIED';check_hand(r);runs.append(r)
  for ref in r['beam_references']:
   assert ref['hand']['midspan_displacement_m']==pytest.approx(-.00084375*scale)
   assert ref['hand']['reaction_y_n']==30000*scale
 for r in runs[1:4]:assert r['frames'][0]['result']['nodes'][1]['displacement_m']==pytest.approx(runs[0]['frames'][0]['result']['nodes'][1]['displacement_m'],abs=1e-10)
 assert runs[4]['frames'][0]['result']['nodes'][1]['displacement_m']==pytest.approx([x*.5 for x in runs[0]['frames'][0]['result']['nodes'][1]['displacement_m']],abs=1e-10)

@pytest.mark.parametrize('bad',['pressure','nan','source','direction','method','openings','cutout','rotation','missing_geometry','gap','unequal_supports','third_beam','excluded','approval','section','joint','shared','reference','self_weight'])
def test_rejections(bad):
 doc=document();q=fixture(doc);by={x['name']:x for x in doc['components']}
 if bad=='pressure':q['intensity_kn_m2']=0
 if bad=='nan':q['intensity_kn_m2']=float('nan')
 if bad=='source':q['source']=''
 if bad=='direction':q['direction']='down'
 if bad=='method':q['method']='two_way'
 if bad=='openings':q['no_openings_confirmed']=False
 if bad=='cutout':by['platform-deck']['geometry']['openings']=[{}]
 if bad=='rotation':by['platform-deck']['transform']['rotation_deg'][2]=1
 if bad=='missing_geometry':by['platform-deck']['geometry']['size']=[]
 if bad=='gap':by['beam-south']['transform']['position'][2]-=.1
 if bad=='unequal_supports':by['beam-south']['transform']['position'][1]+=.1
 if bad=='third_beam':b=deepcopy(by['beam-north']);b['id']='third';b['transform']['position'][1]=0;doc['components'].append(b)
 if bad=='excluded':q['excluded_beam_ids']=[]
 if bad=='approval':q['one_way_idealization_approved']=False
 if bad=='section':q['frames'][0]['sections'][0]['area_m2']=.1
 if bad=='joint':q['frames'][0]['connections'][0]['idealization_approved']=False
 if bad=='shared':q['frames'][1]=deepcopy(q['frames'][0])
 if bad=='reference':q['slab_id']='missing'
 if bad=='self_weight':q['density_kg_m3']=7850
 with pytest.raises((ValueError,KeyError,TypeError)):s.graphs(doc,q)

def test_authorization_staleness_and_owned_artifacts(db_session):
 from test_physical_column import seed
 from app.db.models import ModelRevision,EngineeringAnalysis
 from app.api.routes import slab_transfers as api
 from fastapi import HTTPException
 seed(db_session);rev=db_session.get(ModelRevision,1);rev.document_json=document();db_session.commit();q=fixture(rev.document_json)
 row=api.save(1,api.Save(**q,model_revision_id=1),db_session,1)
 with pytest.raises(HTTPException):api.run(1,api.Authorize(input_id=row['id'],input_sha256='0'*64,authorize_solver=True),db_session,1)
 r=api.run(1,api.Authorize(input_id=row['id'],input_sha256=row['result']['input_sha256'],authorize_solver=True),db_session,1);check_hand(r['result']);assert r['status']=='VERIFIED'
 beam=r['result']['frames'][0]['beam_id'];assert 'eleLoad' in api.artifact(1,beam,r['id'],'model.tcl',None,db_session,1)['contents']
 with pytest.raises(HTTPException):api.artifact(1,'unknown',r['id'],'model.tcl',None,db_session,1)
 with pytest.raises(HTTPException):api.artifact(1,beam,r['id'],'../dev.db',None,db_session,1)
 old=db_session.get(EngineeringAnalysis,r['id']).result_json;api.history(1,db_session,1);assert db_session.get(EngineeringAnalysis,r['id']).result_json==old
 q['intensity_kn_m2']=2.5;api.save(1,api.Save(**q,model_revision_id=1,base_input_id=row['id']),db_session,1);assert api.output(db_session.get(EngineeringAnalysis,r['id']),db_session,1)['status']=='STALE'
 with pytest.raises(HTTPException):api.run(1,api.Authorize(input_id=row['id'],input_sha256=row['result']['input_sha256'],authorize_solver=True),db_session,1)
