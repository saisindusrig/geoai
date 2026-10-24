from copy import deepcopy
from fastapi import HTTPException
from app.api.routes import cad_soil as api
from app.db.models import ModelRevision
from test_physical_column import seed
import pytest

def test_exact_review_authorization_identity_and_staleness(db_session,monkeypatch):
 db=db_session;d=seed(db);rev=db.get(ModelRevision,1)
 # Route boundary fixture: no physical connection or actual analysis is manufactured.
 d['components']=[];rev.document_json=d;db.commit()
 current=dict(model_revision_id=1,rows=[dict(column_id=f'c{i}') for i in range(4)],model_sha256='original',source_analysis_sha256='actual_source')
 monkeypatch.setattr(api,'audit_data',lambda *args:deepcopy(current))
 mappings=[dict(column_id=f'c{i}',footing_id=None,source='Explicit missing geometry review; actual analysis remains blocked',reviewed=True) for i in range(4)]
 for bad in ['duplicate','unknown','unreviewed']:
  q=deepcopy(mappings)
  if bad=='duplicate':q[1]['column_id']='c0'
  if bad=='unknown':q[1]['column_id']='unknown'
  if bad=='unreviewed':q[1]['reviewed']=False
  with pytest.raises(HTTPException):api.review(1,api.Review(model_revision_id=1,mappings=q),db,1)
 saved=api.review(1,api.Review(model_revision_id=1,mappings=mappings),db,1)
 for authorized,sha in [(False,saved['result']['review_sha256']),(True,'0'*64)]:
  with pytest.raises(HTTPException):api.run(1,api.Authorize(review_id=saved['id'],review_sha256=sha,authorize_benchmark=authorized),db,1)
 result=api.run(1,api.Authorize(review_id=saved['id'],review_sha256=saved['result']['review_sha256'],authorize_benchmark=True),db,1);assert result['result']['actual_analysis']=='BLOCKED'
 current['model_sha256']='changed';assert all(r['status']=='STALE' for r in api.history(1,1,db,1)['records'])
 with pytest.raises(HTTPException):api.run(1,api.Authorize(review_id=saved['id'],review_sha256=saved['result']['review_sha256'],authorize_benchmark=True),db,1)
 current['model_sha256']='original';second=api.review(1,api.Review(model_revision_id=1,mappings=mappings),db,1);assert second['id']!=saved['id'];assert api.history(1,1,db,1)['records'][1]['status']=='STALE'
 with pytest.raises(HTTPException):api.run(1,api.Authorize(review_id=saved['id'],review_sha256=saved['result']['review_sha256'],authorize_benchmark=True),db,1)
