import copy
import pytest
from fastapi import HTTPException
from pydantic import ValidationError
from app.api.routes.site_assistant import Context
from app.db.models import ModelRevision
from app.services.assistant.workspace_tools import execute,WorkspaceRejected
from test_site_workspace import site_db
from test_site_assistant import assistant

ARGS=dict(project_id=1,revision_id=1,primitive='column',name='Proposed column',units='mm',dimensions=[400.,500.,3000.],position=[5000.,0.,1500.],position_reference='local_enu_center',rotation_deg=[0.,0.,15.],parent_id=None,provenance='user_dimensions_conceptual')
def setup(db):
 rev=db.get(ModelRevision,1)
 rev.document_json=dict(schema_version=1,project_id=1,scenario_id=1,project_type='bridge',units='metric',origin=dict(lng=77,lat=12,elevation_m=0,heading_deg=0),generator_parameters={},metadata={'source':'synthetic','frame':'local_enu_meters'},components=[dict(id='existing',name='Existing box',category='column',parent_id=None,visible=True,locked=False,geometry={'kind':'box','size':[.4,.4,3]},transform={'position':[0,0,1.5],'rotation_deg':[0,0,0],'scale':[1,1,1]},material={'name':'Appearance','color':'#60A5FA'})])
 db.commit();return rev
def run(db,args=None,**context):return execute('prepare_primitive_preview',ARGS if args is None else args,db,1,Context(project_id=1,revision_id=1,**context))
def test_pure_proposal_units_orientation_and_existing_validators(site_db):
 rev=setup(site_db);before=copy.deepcopy(rev.document_json)
 receipt=run(site_db);c=receipt['candidate']
 assert c['geometry']=={'kind':'box','size':[.4,.5,3.]}
 assert c['transform']=={'position':[5.,0.,1.5],'rotation_deg':[0.,0.,15.],'scale':[1,1,1]}
 assert c['parent_id'] is None and c['quantity']['included'] is False
 assert c['metadata']['engineering']=='UNVERIFIED_GEOMETRY_ONLY'
 assert receipt['saved'] is False and receipt['requiresApproval'] is True and receipt['executed'] is False
 assert run(site_db)['actionId']==receipt['actionId']
 assert rev.document_json==before and site_db.query(ModelRevision).count()==1
@pytest.mark.parametrize('unit,dimensions,position',[('m',[.4,.5,3.],[3.,0.,1.5]),('cm',[40.,50.,300.],[300.,0.,150.]),('mm',[400.,500.,3000.],[3000.,0.,1500.])])
def test_explicit_unit_conversion(site_db,unit,dimensions,position):
 setup(site_db);c=run(site_db,{**ARGS,'units':unit,'dimensions':dimensions,'position':position})['candidate']
 assert c['geometry']['size']==pytest.approx([.4,.5,3.])
 assert c['transform']['position']==pytest.approx([3.,0.,1.5])
@pytest.mark.parametrize('changes',[{'dimensions':[0.,.4,3.]},{'dimensions':[float('nan'),.4,3.]},{'dimensions':[.001,.4,3.],'units':'m'},{'position':[1e20,0.,0.]},{'rotation_deg':[10.,0.,0.]},{'rotation_deg':[0.,0.,float('inf')]},{'revision_id':2}])
def test_invalid_geometry_and_stale_args(site_db,changes):
 setup(site_db)
 with pytest.raises((WorkspaceRejected,ValidationError)):run(site_db,{**ARGS,**changes})
@pytest.mark.parametrize('changes',[{'primitive':'beam'},{'parent_id':'existing'},{'strength':30},{'units':'ft'},{'dimensions':[True,400.,3000.]}])
def test_allowlist_rejects_unsupported_or_engineering_fields(site_db,changes):
 setup(site_db)
 with pytest.raises(ValidationError):run(site_db,{**ARGS,**changes})
@pytest.mark.parametrize('field,value',[('locked',True),('geometry',{'kind':'cad_mesh'}),('metadata',{'parametric_platform':True}),('parent_id','source')])
def test_protected_source_not_bypassed(site_db,field,value):
 rev=setup(site_db);doc=copy.deepcopy(rev.document_json);doc['components'][0][field]=value;rev.document_json=doc;site_db.commit()
 with pytest.raises(WorkspaceRejected):run(site_db)
def test_missing_inputs_ownership_dirty_and_latest_revision(site_db):
 rev=setup(site_db)
 for field in ('dimensions','position','rotation_deg','parent_id','units','provenance'):
  args=dict(ARGS);args.pop(field)
  with pytest.raises(ValidationError):run(site_db,args)
 with pytest.raises(HTTPException):run(site_db,{**ARGS,'project_id':2})
 with pytest.raises(WorkspaceRejected):run(site_db,dirty=True)
 site_db.add(ModelRevision(id=3,project_id=1,design_scenario_id=1,revision_number=2,document_json=copy.deepcopy(rev.document_json)));site_db.commit()
 with pytest.raises(WorkspaceRejected):run(site_db)
def test_exact_proposal_validates_read_only_and_rejects_changed_arguments(site_db):
 setup(site_db);receipt=run(site_db)
 assert run(site_db,{**ARGS,'position':[6000.,0.,1500.]})['actionId']!=receipt['actionId']
 assert execute('cancel_primitive_preview',{'project_id':1},site_db,1,Context(project_id=1,revision_id=1,dirty=True))['executed'] is False
def test_http_validation_rechecks_exact_hash_and_never_applies(assistant):
 client,db,_,_=assistant
 rev=setup(db);receipt=run(db)
 body=dict(page='/projects/1/workspace',project_id=1,revision_id=1,selected_ids=[],dirty=False,name='prepare_primitive_preview',arguments=ARGS,action_id=receipt['actionId'])
 response=client.post('/api/assistant/workspace/validate',json=body)
 assert response.status_code==200 and response.json()['candidate']==receipt['candidate']
 assert client.post('/api/assistant/workspace/validate',json={**body,'arguments':{**ARGS,'dimensions':[500.,500.,3000.]}}).status_code==409
 doc=copy.deepcopy(rev.document_json);doc['components'][0]['name']='Source changed';rev.document_json=doc;db.commit()
 assert client.post('/api/assistant/workspace/validate',json=body).status_code==409
 assert db.query(ModelRevision).count()==1 and len(rev.document_json['components'])==1
