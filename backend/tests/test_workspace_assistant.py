import copy
import pytest
from fastapi import HTTPException
from app.api.routes.site_assistant import Context
from app.services.assistant.workspace_tools import execute,WorkspaceRejected
from app.db.models import ModelRevision,EngineeringAnalysis
from app.services.design.opensees_benchmark import digest
from test_site_workspace import site_db
from test_engineering_guidance import prepare

def request(**changes):return Context(project_id=1,revision_id=1,selected_ids=['beam'],**changes)
def test_component_reads_selection_and_no_mutation(site_db):
 prepare(site_db);before=copy.deepcopy(site_db.get(ModelRevision,1).document_json)
 listing=execute('list_components',{'project_id':1},site_db,1,request())
 assert listing['components'][0]['id']=='beam' and listing['total']==1
 props=execute('read_component_properties',{'project_id':1,'component_ids':['beam']},site_db,1,request())
 assert props['components'][0]['geometry']['size']==[6,.2,.3]
 receipt=execute('select_components',{'project_id':1,'component_ids':['beam']},site_db,1,request())
 assert receipt['executed'] is False and len(receipt['actionId'])==64 and receipt['documentHash']==digest(before)
 assert site_db.get(ModelRevision,1).document_json==before
@pytest.mark.parametrize('name,args',[('open_project',{'project_id':2}),('list_components',{'project_id':2}),('select_components',{'project_id':2,'component_ids':['beam']}),('list_saved_results',{'project_id':2})])
def test_cross_project_access(site_db,name,args):
 prepare(site_db)
 with pytest.raises(HTTPException):execute(name,args,site_db,1,request())
def test_missing_hidden_dirty_and_stale_source(site_db):
 prepare(site_db)
 with pytest.raises(WorkspaceRejected):execute('select_components',{'project_id':1,'component_ids':['invented']},site_db,1,request())
 with pytest.raises(WorkspaceRejected):execute('open_project',{'project_id':1},site_db,1,request(dirty=True))
 d=copy.deepcopy(site_db.get(ModelRevision,1).document_json);d['components'][0]['visible']=False;site_db.get(ModelRevision,1).document_json=d;site_db.commit()
 with pytest.raises(WorkspaceRejected):execute('focus_components',{'project_id':1,'component_ids':['beam']},site_db,1,request())
 site_db.add(ModelRevision(id=3,project_id=1,design_scenario_id=1,revision_number=2,document_json=d));site_db.commit()
 with pytest.raises(WorkspaceRejected):execute('switch_workspace_view',{'project_id':1,'view':'model'},site_db,1,request())
def test_exact_saved_result_and_load_case_binding(site_db,monkeypatch):
 prepare(site_db)
 from app.api.routes import analysis_capabilities as cap
 doc=site_db.get(ModelRevision,1).document_json
 identity=dict(id=1,project_id=1,model_revision_id=1,method='frame',status='VERIFIED',load_cases=['Gravity'],model_document_sha256=digest(doc))
 def capabilities(*args,**kwargs):
  assert kwargs['saved_only'] is True
  return {'methods':{'frame':{'current_results':[identity],'status':'SUPPORTED','reason':'test'}}}
 monkeypatch.setattr(cap,'capabilities',capabilities)
 args=dict(project_id=1,revision_id=1,result_id=1,method='frame',load_case='Gravity',mode='forces')
 receipt=execute('show_saved_result',args,site_db,1,request())
 assert receipt['resultIdentity']==identity and receipt['loadCase']=='Gravity' and receipt['executed'] is False
 for changes in ({'result_id':9},{'revision_id':2},{'load_case':'Unknown'},{'mode':'slab'}):
  with pytest.raises(WorkspaceRejected):execute('show_saved_result',{**args,**changes},site_db,1,request())
 identity['model_document_sha256']='changed'
 with pytest.raises(WorkspaceRejected):execute('show_saved_result',args,site_db,1,request())
def test_action_validation_does_not_accept_changed_receipt(assistant):
 client,db,m,app=assistant
 result=execute('select_components',{'project_id':1,'component_ids':['beam']},db,1,request())
 body={**request().model_dump(),'name':'select_components','arguments':{'project_id':1,'component_ids':['beam']},'action_id':result['actionId']}
 assert client.post('/api/assistant/workspace/validate',json=body).status_code==200
 assert client.post('/api/assistant/workspace/validate',json={**body,'action_id':'0'*64}).status_code==409
 assert client.post('/api/assistant/workspace/outcome',json={'task_id':'0'*36,'action_id':result['actionId'],'ok':True,'message':'Forged'}).status_code==404
from test_site_assistant import assistant
def test_saved_only_foundation_capability_never_recalculates(site_db,monkeypatch):
 prepare(site_db)
 from types import SimpleNamespace
 from app.api.routes import analysis_capabilities as cap
 rev=site_db.get(ModelRevision,1);doc=copy.deepcopy(rev.document_json);doc['metadata']={'foundation_system':{'bound':True}};rev.document_json=doc
 row=EngineeringAnalysis(id=9,project_id=1,model_revision_id=1,analysis_type='FOUNDATION_SYSTEM_RESULT',algorithm_version='test',status='REVIEWED_SYNTHETIC_CALCULATION',actor_user_id=1,result_json={'computed':{'saved':True},'inputs':{}});site_db.add(row);site_db.commit()
 monkeypatch.setattr(cap,'context',lambda *a,**k:(rev,None))
 def forbidden(*a,**k):raise AssertionError('Numerical recalculation forbidden during saved-result inspection')
 fake=SimpleNamespace(history=lambda *a,**k:{'records':[dict(id=9,model_revision_id=1,status=row.status,result=row.result_json)]},prepare=forbidden,Preview=lambda **k:k)
 monkeypatch.setattr(cap,'METHODS',{'foundation':(fake,'FOUNDATION_SYSTEM_RESULT')})
 result=cap.capabilities(1,1,'',site_db,1,saved_only=True)
 assert result['methods']['foundation']['current_results'][0]['load_cases']==['Saved foundation actions']

def test_frontend_outcomes_append_without_rewriting_accounting(assistant):
 import json,time
 from uuid import uuid4
 from app.services.assistant import site_store
 client,db,m,app=assistant
 receipt=execute('select_components',{'project_id':1,'component_ids':['beam']},db,1,request())
 task_id=str(uuid4());task={'id':task_id,'request':request().model_dump(),'status':'SUCCEEDED','events':[{'type':'tool_result','ok':True,'result':receipt}]}
 with site_store.connection() as c:c.execute('INSERT INTO tasks VALUES (?,?,?,?,?,?,?,?,?)',(task_id,1,1,time.time(),'SUCCEEDED','zai-org/GLM-5.3-Flash',.001,10,json.dumps(task)))
 before=site_store.snapshot(1)
 body={'task_id':task_id,'action_id':receipt['actionId'],'ok':True,'message':'Selected Beam A.'}
 assert client.post('/api/assistant/workspace/outcome',json=body).status_code==200
 assert client.post('/api/assistant/workspace/outcome',json=body).status_code==200
 assert len(client.get('/api/assistant/workspace/history').json()['outcomes'])==1
 assert site_store.snapshot(1)==before
