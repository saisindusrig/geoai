import copy,io
import numpy as np
import pytest
import trimesh
from fastapi import HTTPException
from pydantic import ValidationError
from trimesh.transformations import euler_matrix
from app.api.routes.site_assistant import Context
from app.db.models import ModelRevision
from app.services.assistant.workspace_tools import execute,WorkspaceRejected
from app.services.assistant.beam_proposal import beam_box
from app.services.design.editable_model import document_to_geometry_spec
from app.services.exports.gltf_export import generate_glb,_Z_UP_TO_Y_UP
from test_supervised_primitive import setup,site_db

ARGS=dict(project_id=1,revision_id=1,primitive='beam',name='Beam proposal',units='mm',endpoints=[[0.,0.,3000.],[4000.,2000.,4000.]],width=300.,depth=450.,position_reference='local_enu',point_source='user_explicit_enu',parent_id=None,provenance='user_dimensions_conceptual')
def run(db,args=None,**changes):return execute('prepare_beam_preview',ARGS if args is None else args,db,1,Context(project_id=1,revision_id=1,**changes))
@pytest.mark.parametrize('endpoints',[[[0,0,0],[5,0,0]],[[2,3,1],[-3,1,4]],[[0,0,0],[0,5,0]],[[0,0,0],[0,0,5]],[[0,0,5],[0,0,0]],[[1,1,1],[-2,-3,-4]],[[0,0,0],[.000001,0,5]]])
def test_xyz_box_transform_matches_explicit_endpoints_and_reverse(endpoints):
 a=beam_box(endpoints,.3,.45,'m');b=beam_box(endpoints[::-1],.3,.45,'m')
 for q,ends in [(a,endpoints),(b,endpoints[::-1])]:
  matrix=euler_matrix(*np.radians(q['rotation_deg']),axes='rxyz');matrix[:3,3]=q['position']
  observed=trimesh.transform_points([[-q['length_m']/2,0,0],[q['length_m']/2,0,0]],matrix)
  assert np.allclose(observed,ends,atol=1e-8)
  assert q['length_m']==pytest.approx(np.linalg.norm(np.subtract(ends[1],ends[0])))
 # Endpoint reversal preserves the same rectangular solid and depth direction.
 ra=euler_matrix(*np.radians(a['rotation_deg']),axes='rxyz');rb=euler_matrix(*np.radians(b['rotation_deg']),axes='rxyz')
 assert np.allclose(ra[:3,2],rb[:3,2],atol=1e-8)
@pytest.mark.parametrize('unit,factor',[('m',1.),('cm',100.),('mm',1000.)])
def test_units_saved_glb_and_editor_document_agree(site_db,unit,factor):
 rev=setup(site_db);before=copy.deepcopy(rev.document_json)
 args={**ARGS,'units':unit,'width':.3*factor,'depth':.45*factor,'endpoints':[[v*factor for v in p] for p in [[0.,0.,3.],[4.,2.,4.]]]}
 receipt=run(site_db,args);c=receipt['candidate'];q=c['metadata']['beam']
 assert q['length_m']==pytest.approx(np.sqrt(21)) and c['geometry']['size'][1:]==pytest.approx([.3,.45])
 assert receipt['executed'] is False and receipt['saved'] is False and c['quantity']['included'] is False
 assert rev.document_json==before and site_db.query(ModelRevision).count()==1
 spec=document_to_geometry_spec({**before,'components':[c]});assert 'rotation_deg' in spec['objects'][0]
 scene=trimesh.load(io.BytesIO(generate_glb(spec)),file_type='glb',force='scene')
 vertices=scene.to_geometry().vertices
 enu=trimesh.transform_points(vertices,np.linalg.inv(_Z_UP_TO_Y_UP))
 rotation=euler_matrix(*np.radians(c['transform']['rotation_deg']),axes='rxyz')[:3,:3]
 local=(enu-np.asarray(c['transform']['position']))@rotation
 assert np.ptp(local,axis=0)==pytest.approx(c['geometry']['size'],abs=1e-5)
 assert local.mean(axis=0)==pytest.approx([0,0,0],abs=1e-5)
@pytest.mark.parametrize('change',[{'endpoints':[[0.,0.,0.],[0.,0.,0.]]},{'endpoints':[[0.,0.,0.],[.001,0.,0.]]},{'endpoints':[[0.,0.,0.],[float('nan'),0.,0.]]},{'endpoints':[[0.,0.,0.],[1e9,0.,0.]]},{'width':0.},{'depth':float('inf')},{'point_source':'selected_columns'},{'endpoint_ids':['one','other']},{'strength':30},{'parent_id':'column-a'},{'primitive':'curved_beam'},{'units':'feet'},{'endpoints':[[True,0.,0.],[5.,0.,0.]]}])
def test_invalid_or_ambiguous_requests(site_db,change):
 setup(site_db)
 with pytest.raises((ValueError,ValidationError)):run(site_db,{**ARGS,**change})
def test_missing_inputs_freshness_ownership_and_protected_sources(site_db):
 rev=setup(site_db)
 for field in ('endpoints','width','depth','units','point_source'):
  args=dict(ARGS);args.pop(field)
  with pytest.raises(ValidationError):run(site_db,args)
 with pytest.raises(HTTPException):run(site_db,{**ARGS,'project_id':2})
 with pytest.raises(WorkspaceRejected):run(site_db,dirty=True)
 original=copy.deepcopy(rev.document_json)
 for key,value in [('locked',True),('geometry',{'kind':'cad_mesh'}),('metadata',{'parametric_platform':True})]:
  doc=copy.deepcopy(original);doc['components'][0][key]=value;rev.document_json=doc;site_db.commit()
  with pytest.raises(WorkspaceRejected):run(site_db)
 rev.document_json=original;site_db.commit();receipt=run(site_db)
 assert receipt['actionId']==run(site_db)['actionId']
 assert receipt['actionId']!=run(site_db,{**ARGS,'endpoints':ARGS['endpoints'][::-1]})['actionId']
 site_db.add(ModelRevision(id=3,project_id=1,design_scenario_id=1,revision_number=2,document_json=original));site_db.commit()
 with pytest.raises(WorkspaceRejected):run(site_db)
def test_yaw_only_export_shape_remains_compatible():
 doc={'components':[dict(id='original',category='beam',geometry={'kind':'box','size':[5,.3,.45]},transform={'position':[2,0,3],'rotation_deg':[0,0,30],'scale':[1,1,1]})]}
 spec=document_to_geometry_spec(doc)['objects'][0]
 assert spec==dict(name='original',layer='beam',kind='box',size=[5.,.3,.45],center=[2.,0.,3.],rotation_z_deg=30.)
