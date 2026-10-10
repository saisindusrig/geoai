import json
from app.core.config import Settings, settings
from app.services.ai.nebius_config import safe_loading_diagnostics


def test_development_file_credential_overrides_parent(tmp_path,monkeypatch):
    path=tmp_path/'local.env';path.write_text('NEBIUS_API_KEY=file-test-key\n',encoding='utf-8')
    monkeypatch.setenv('NEBIUS_API_KEY','parent-test-key')
    monkeypatch.setenv('ENVIRONMENT','development')
    monkeypatch.setenv('NEBIUS_PRIMARY_MODEL','unchanged-primary')
    config=Settings(_env_file=path)
    assert config.NEBIUS_API_KEY=='file-test-key'
    assert config.NEBIUS_PRIMARY_MODEL=='unchanged-primary'


def test_production_keeps_process_credential(tmp_path,monkeypatch):
    path=tmp_path/'local.env';path.write_text('NEBIUS_API_KEY=file-test-key\n',encoding='utf-8')
    monkeypatch.setenv('NEBIUS_API_KEY','parent-test-key')
    assert Settings(_env_file=path,ENVIRONMENT='production').NEBIUS_API_KEY=='parent-test-key'


def test_explicit_constructor_and_missing_file_fallback(tmp_path,monkeypatch):
    path=tmp_path/'local.env';path.write_text('NEBIUS_API_KEY=file-test-key\n',encoding='utf-8')
    monkeypatch.setenv('NEBIUS_API_KEY','parent-test-key')
    assert Settings(_env_file=path,NEBIUS_API_KEY='explicit-test-key').NEBIUS_API_KEY=='explicit-test-key'
    assert Settings(_env_file=tmp_path/'missing.env').NEBIUS_API_KEY=='parent-test-key'


def test_sanitized_source_diagnostics(monkeypatch):
    monkeypatch.setattr(settings,'NEBIUS_API_KEY','private-fixture-key')
    text=json.dumps(safe_loading_diagnostics())
    assert 'private-fixture-key' not in text
    assert 'Authorization' not in text
    assert json.loads(text)['keyConfigured'] is True


def test_explicit_file_source_is_identified(tmp_path,monkeypatch):
    from app.services.ai import nebius_config
    monkeypatch.setattr(nebius_config,'_explicit_env_sources',{})
    monkeypatch.setattr(settings,'NEBIUS_API_KEY','old-fixture')
    path=tmp_path/'diagnostic.env'
    path.write_text('NEBIUS_API_KEY=explicit-private-fixture\n',encoding='utf-8')
    nebius_config.use_env_file(path)
    diagnostics=safe_loading_diagnostics()
    assert diagnostics['keySource']=='explicit env file: '+str(path.resolve())
    assert 'explicit-private-fixture' not in json.dumps(diagnostics)
