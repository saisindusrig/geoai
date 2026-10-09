"""Authoritative normalized Nebius settings. Credentials never appear in repr."""
from dataclasses import dataclass, field
from urllib.parse import urlsplit
from dotenv import dotenv_values
from app.core.config import settings, REPO_DIR, BACKEND_DIR

DEFAULT_BASE_URL = "https://api.tokenfactory.nebius.com/v1"


def normalize_key(value):
    value = str(value or "").strip()
    if len(value)>1 and value[0]==value[-1] and value[0] in "\"'":
        value=value[1:-1].strip()
    if value.lower().startswith("bearer "):
        value=value[7:].strip()
    if any(c.isspace() for c in value):
        raise ValueError("API key contains internal whitespace; correct the source")
    return value


def normalize_base(value):
    value=str(value or DEFAULT_BASE_URL).strip().rstrip("/")
    base=urlsplit(value)
    if base.scheme!='https' or not base.hostname or base.username or base.password or base.query or base.fragment:
        raise ValueError("Nebius base must be an HTTPS URL without credentials, query, or fragment")
    if base.path not in ('','/v1'):
        raise ValueError("Nebius base path must be empty or /v1; duplicate /v1 paths are invalid")
    return value if base.path else value+'/v1'


@dataclass(frozen=True)
class NebiusConfig:
    base_url: str
    model: str
    api_key: str = field(repr=False)
    timeout: float = 25

    def url(self, endpoint):
        if endpoint not in {'models','chat/completions'}:
            raise ValueError("Unsupported Nebius endpoint")
        return self.base_url+'/'+endpoint

    def headers(self):
        return {'Authorization':'Bearer '+self.api_key}


def resolve(*, model=None, timeout=None):
    resolved_timeout=settings.NEBIUS_TIMEOUT_SECONDS if timeout is None else float(timeout)
    if not 0<resolved_timeout<=120:
        raise ValueError("Nebius timeout must be between zero and 120 seconds")
    return NebiusConfig(normalize_base(settings.NEBIUS_BASE_URL.strip() or settings.NEBIUS_TOKEN_FACTORY_BASE_URL),
        str(settings.NEBIUS_CHAT_MODEL if model is None else model).strip(),normalize_key(settings.NEBIUS_API_KEY),resolved_timeout)


def use_env_file(path):
    """Explicit diagnostic override; normal app env precedence remains intact."""
    from pathlib import Path
    path=Path(path)
    if not path.is_file():raise ValueError("Env file does not exist")
    values=dotenv_values(path,interpolate=False)
    # Do not retain unrelated environment content or change production routing tiers.
    for name in ('NEBIUS_API_KEY','NEBIUS_BASE_URL','NEBIUS_TOKEN_FACTORY_BASE_URL','NEBIUS_CHAT_MODEL','NEBIUS_TIMEOUT_SECONDS'):
        if name in values:
            setattr(settings,name,float(values[name]) if name=='NEBIUS_TIMEOUT_SECONDS' else values[name] or '')


def safe_loading_diagnostics():
    import os
    root=dotenv_values(REPO_DIR/'.env',interpolate=False) if (REPO_DIR/'.env').exists() else {}
    effective=settings.NEBIUS_API_KEY
    root_key=root.get('NEBIUS_API_KEY') or ''
    try:
        config=resolve()
        base=urlsplit(config.base_url)
        normalized=True
    except ValueError:
        base=urlsplit('');normalized=False
    return {'keyConfigured':bool(effective),'keyLength':len(effective),'processKeyPresent':bool(os.environ.get('NEBIUS_API_KEY')),
        'repoEnvExists':(REPO_DIR/'.env').exists(),'backendEnvExists':(BACKEND_DIR/'.env').exists(),
        'repoKeyMatchesEffective':bool(root_key) and root_key==effective,'normalizationValid':normalized,
        'baseHost':base.hostname,'basePath':base.path,
        'precedence':'explicit diagnostic env-file > process env > backend/.env > repository .env > defaults'}
