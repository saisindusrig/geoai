"""Gate 2C: a reserved ADC mode must never discover or use credentials.

All verifier outputs/identities are synthetic. No keyless/live qualification.
"""
import pytest
from fastapi import HTTPException

from app.core import firebase_auth
from app.core.config import settings
from test_firebase_auth import bearer, firebase_client, sdk  # noqa: F401
from test_private_beta_security import secured  # noqa: F401


def forbidden(*args, **kwargs):
    raise AssertionError('Credential discovery or verification must not occur')


@pytest.mark.parametrize('project,code', [
    ('struvocivil-918c9', 'ADC_IDENTITY_NOT_QUALIFIED'),
    ('synthetic-auth-project', 'ADC_PROJECT_NOT_APPROVED'),
])
def test_adc_rejects_before_credential_path_or_sdk_access(sdk, monkeypatch, project, code):
    monkeypatch.setattr(settings, 'FIREBASE_AUTH_CREDENTIAL_MODE', 'adc')
    monkeypatch.setattr(settings, 'FIREBASE_PROJECT_ID', project)
    monkeypatch.setenv('GOOGLE_APPLICATION_CREDENTIALS', 'synthetic-do-not-open.json')
    monkeypatch.setenv('CLOUDSDK_CONFIG', 'synthetic-do-not-inspect')
    monkeypatch.setattr(firebase_auth, 'Path', forbidden)
    sdk.module.credentials.ApplicationDefault = forbidden
    sdk.module.credentials.Certificate = forbidden
    sdk.module.get_app = forbidden
    sdk.module.initialize_app = forbidden
    sdk.module.auth.verify_id_token = forbidden
    assert firebase_auth.readiness()['code'] == code
    for verify in (firebase_auth.verify_identity, firebase_auth._sdk_verify):
        with pytest.raises(HTTPException) as failure:
            verify('synthetic-token')
        assert failure.value.status_code == 503
    assert sdk.calls == []


@pytest.mark.parametrize('mode', ['ADC', '', 'auto', 'application-default', 'unknown'])
def test_unknown_modes_fail_closed_without_certificate_fallback(sdk, monkeypatch, mode):
    monkeypatch.setattr(settings, 'FIREBASE_AUTH_CREDENTIAL_MODE', mode)
    assert firebase_auth.readiness()['code'] == 'CREDENTIAL_MODE_UNSUPPORTED'
    with pytest.raises(HTTPException) as failure:
        firebase_auth._sdk_verify('valid')
    assert failure.value.status_code == 503
    assert sdk.calls == []


def test_disabled_mode_does_not_inspect_credentials_or_sdk(sdk, monkeypatch):
    monkeypatch.setattr(settings, 'FIREBASE_AUTH_ENABLED', False)
    monkeypatch.setattr(settings, 'FIREBASE_AUTH_CREDENTIAL_MODE', 'adc')
    monkeypatch.setattr(firebase_auth, 'Path', forbidden)
    monkeypatch.setattr(firebase_auth.importlib.util, 'find_spec', forbidden)
    assert firebase_auth.readiness()['code'] == 'DISABLED'
    assert sdk.calls == []


def test_adc_cannot_reuse_certificate_app_or_fall_back_to_local_identity(firebase_client, monkeypatch):
    client, _, _, sdk = firebase_client
    assert client.get('/api/auth/me', headers=bearer()).status_code == 200
    prior_calls = len(sdk.calls)
    monkeypatch.setattr(settings, 'FIREBASE_AUTH_CREDENTIAL_MODE', 'adc')
    monkeypatch.setattr(settings, 'FIREBASE_PROJECT_ID', 'struvocivil-918c9')
    for token in ('valid', 'forged', 'expired', 'revoked', 'outage', 'unknown'):
        response = client.get('/api/projects/1', headers=bearer(token, **{'X-Mock-User-Id': '1'}))
        assert response.status_code == 503
    assert len(sdk.calls) == prior_calls
    configuration = client.get('/api/auth/config').json()
    assert configuration['mode'] == 'firebase'
    assert configuration['password_login_allowed'] is False
    assert configuration['firebase']['ready'] is False
