"""Phase A clean-data boundary; no original database or seeder invocation."""
from unittest.mock import Mock
import pytest
from fastapi import HTTPException
from app.core.config import settings
from app.api.routes import projects
from app.db import demo_seed

@pytest.mark.parametrize('environment',['production','prod','PRODUCTION'])
def test_production_demo_cannot_seed_or_commit(monkeypatch,environment):
    monkeypatch.setattr(settings,'ENVIRONMENT',environment)
    seed=Mock(side_effect=AssertionError('Production must never seed demo data'))
    monkeypatch.setattr(demo_seed,'ensure_demo_project_for_user',seed)
    db=Mock()
    with pytest.raises(HTTPException) as error:projects.get_demo_project(db)
    assert error.value.status_code==404
    seed.assert_not_called()
    assert not db.method_calls

def test_local_demo_keeps_existing_workflow(monkeypatch):
    monkeypatch.setattr(settings,'ENVIRONMENT','development')
    project=object();seed=Mock(return_value=project)
    monkeypatch.setattr(demo_seed,'ensure_demo_project_for_user',seed)
    db=Mock()
    assert projects.get_demo_project(db) is project
    seed.assert_called_once_with(db,projects.DEV_USER_ID)
    db.commit.assert_called_once();db.refresh.assert_called_once_with(project)
