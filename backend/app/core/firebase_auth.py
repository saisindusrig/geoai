"""Optional official-SDK verification. No token decoding or offline substitute."""
import importlib.util
import os
import math
import re
import threading
import time
from dataclasses import dataclass
from pathlib import Path

from fastapi import HTTPException
from app.core.config import settings

_lock = threading.Lock()
_APPROVED_ADC_PROJECT = 'struvocivil-918c9'


def _credential_mode_error():
    """Never discover ambient ADC, including cached developer Google logins."""
    mode = settings.FIREBASE_AUTH_CREDENTIAL_MODE
    if mode == 'certificate':
        return None
    if mode == 'adc':
        if settings.FIREBASE_PROJECT_ID != _APPROVED_ADC_PROJECT:
            return ('ADC_PROJECT_NOT_APPROVED', 'ADC requires the approved staging project.')
        return ('ADC_IDENTITY_NOT_QUALIFIED',
                'Keyless authentication is unavailable: an explicitly pinned workload identity source requires separate review. Ambient ADC discovery is forbidden.')
    return ('CREDENTIAL_MODE_UNSUPPORTED', 'Firebase credential mode is unsupported.')


@dataclass(frozen=True)
class FirebaseIdentity:
    project_id: str
    issuer: str
    uid: str


def readiness() -> dict:
    """Sanitized, local-only prerequisite inspection; never initializes the SDK."""
    if not settings.FIREBASE_AUTH_ENABLED:
        return dict(enabled=False, ready=False, code='DISABLED', message='Firebase authentication is disabled.')
    checks = [
        (settings.AUTH_REQUIRE_JWT, 'AUTH_ENFORCEMENT_REQUIRED'),
        (bool(re.fullmatch(r'[a-z][a-z0-9-]{4,28}[a-z0-9]', settings.FIREBASE_PROJECT_ID)), 'PROJECT_REQUIRED'),
        (not os.environ.get('FIREBASE_AUTH_EMULATOR_HOST'), 'EMULATOR_FORBIDDEN'),
        (importlib.util.find_spec('firebase_admin') is not None, 'ADMIN_SDK_MISSING'),
    ]
    for ok, code in checks:
        if not ok:
            return dict(enabled=True, ready=False, code=code, message='Firebase authentication prerequisites are incomplete. Sign-in is unavailable.')
    mode_error = _credential_mode_error()
    if mode_error:
        code, message = mode_error
        return dict(enabled=True, ready=False, code=code, message=message)
    try:
        credential_present = bool(settings.FIREBASE_AUTH_CREDENTIALS_FILE) and Path(settings.FIREBASE_AUTH_CREDENTIALS_FILE).is_file()
    except (OSError, ValueError):
        credential_present = False
    if not credential_present:
        return dict(enabled=True, ready=False, code='CREDENTIALS_MISSING', message='Firebase authentication prerequisites are incomplete. Sign-in is unavailable.')
    return dict(enabled=True, ready=True, code='PREREQUISITES_PRESENT', message='Local prerequisites present; live authentication is not qualified.')


def _sdk_verify(token: str) -> dict:
    # This function is the sole trust boundary. Tests replace it, never the decoder.
    # Check before SDK imports/app reuse: switching mode cannot reuse a certificate
    # app or trigger SDK default-credential discovery. ADC is not implemented yet.
    mode_error = _credential_mode_error()
    if mode_error:
        raise HTTPException(503, mode_error[1])
    from firebase_admin import auth, credentials, get_app, initialize_app
    project = settings.FIREBASE_PROJECT_ID
    name = 'struvocivil-auth-' + project
    with _lock:
        try:
            app = get_app(name)
        except ValueError:
            credential = credentials.Certificate(settings.FIREBASE_AUTH_CREDENTIALS_FILE)
            if credential.project_id != project:
                raise HTTPException(503, 'Firebase credentials do not match the configured project')
            app = initialize_app(credential, {'projectId': project}, name=name)
    # Mandatory remote account/revocation check on every verification; no positive cache.
    return auth.verify_id_token(token, app=app, check_revoked=True, clock_skew_seconds=0)


def verify_identity(token: str) -> FirebaseIdentity:
    state = readiness()
    if not state['enabled'] or not state['ready']:
        raise HTTPException(503, state['message'])
    if not isinstance(token, str) or not token or len(token) > 16384:
        raise HTTPException(401, 'Invalid Firebase identity token')
    try:
        claims = _sdk_verify(token)
    except HTTPException:
        raise
    except Exception as exc:
        # Only official SDK credential failures become 401. Everything else fails
        # unavailable, including certificate fetch, IAM and account-service errors.
        try:
            from firebase_admin import auth
        except ImportError:
            raise HTTPException(503, 'Firebase Admin SDK unavailable; no fallback identity accepted') from None
        if isinstance(exc, (auth.InvalidIdTokenError, auth.ExpiredIdTokenError,
                            auth.RevokedIdTokenError, auth.UserDisabledError)):
            raise HTTPException(401, 'Invalid, expired, revoked or disabled Firebase identity') from None
        raise HTTPException(503, 'Firebase verification unavailable; no fallback identity accepted') from None
    project = settings.FIREBASE_PROJECT_ID
    issuer = f'https://securetoken.google.com/{project}'
    now = time.time()
    try:
        uid = claims['sub']
        valid = (claims['aud'] == project and claims['iss'] == issuer
                 and isinstance(uid, str) and 0 < len(uid) <= 128
                 and claims.get('uid') == uid
                 and all(isinstance(claims[k], (int, float)) and not isinstance(claims[k], bool) and math.isfinite(claims[k])
                         for k in ('exp', 'iat', 'auth_time'))
                 and claims['exp'] > now and 0 <= claims['auth_time'] <= claims['iat'] <= now
                 and not (claims.get('firebase') or {}).get('tenant'))
    except (KeyError, TypeError, AttributeError, OverflowError):
        valid = False
    if not valid:
        raise HTTPException(401, 'Firebase identity does not match the configured project or token lifetime')
    return FirebaseIdentity(project, issuer, uid)
