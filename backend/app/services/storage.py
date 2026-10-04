"""File storage: S3/MinIO/AWS when configured, else local filesystem.

Local files are served by the backend at /files/{path}.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from urllib.parse import urlparse

from app.core.config import settings

logger = logging.getLogger(__name__)

_s3_client = None
_s3_checked = False

LOCALHOST_MARKERS = ("localhost", "127.0.0.1")


def reset_storage_cache() -> None:
    """Clear cached S3 client (tests)."""
    global _s3_client, _s3_checked
    _s3_client = None
    _s3_checked = False


def _s3_configured() -> bool:
    return bool(settings.S3_ACCESS_KEY and settings.S3_SECRET_KEY and settings.S3_BUCKET)


def public_api_base() -> str:
    """Public base URL for API-served files (no trailing slash)."""
    if settings.PUBLIC_API_URL:
        return settings.PUBLIC_API_URL.rstrip("/")
    render_url = os.environ.get("RENDER_EXTERNAL_URL", "").strip()
    if render_url:
        return render_url.rstrip("/")
    return "http://localhost:8000"


def local_file_url(key: str) -> str:
    return f"{public_api_base()}/files/{key.lstrip('/')}"


def normalize_file_url(url: str | None) -> str | None:
    """Rewrite dev localhost URLs to the configured public API base."""
    if not url:
        return url
    if url.startswith("/files/"):
        return f"{public_api_base()}{url}"
    parsed = urlparse(url)
    if parsed.path.startswith("/files/") and any(h in (parsed.hostname or "") for h in LOCALHOST_MARKERS):
        return f"{public_api_base()}{parsed.path}"
    return url


def _ensure_bucket(client, bucket: str) -> None:
    from botocore.exceptions import ClientError

    try:
        client.head_bucket(Bucket=bucket)
        return
    except ClientError as exc:
        code = str(exc.response.get("Error", {}).get("Code", ""))
        if code in ("403", "301", "302"):
            return
        if code not in ("404", "NoSuchBucket"):
            raise
    if not settings.S3_ENDPOINT:
        raise RuntimeError(f"S3 bucket {bucket!r} not found — create it in your cloud provider")
    client.create_bucket(Bucket=bucket)


def _get_s3():
    global _s3_client, _s3_checked
    if _s3_checked:
        return _s3_client
    _s3_checked = True
    if not _s3_configured():
        return None
    try:
        import boto3
        from botocore.config import Config

        kwargs: dict = {
            "aws_access_key_id": settings.S3_ACCESS_KEY,
            "aws_secret_access_key": settings.S3_SECRET_KEY,
            "config": Config(signature_version="s3v4"),
        }
        if settings.S3_ENDPOINT:
            kwargs["endpoint_url"] = settings.S3_ENDPOINT
        if settings.S3_REGION:
            kwargs["region_name"] = settings.S3_REGION
        client = boto3.client("s3", **kwargs)
        # Align client region with bucket location (fixes 403 on presigned URLs).
        if not settings.S3_ENDPOINT:
            try:
                loc = client.get_bucket_location(Bucket=settings.S3_BUCKET)
                bucket_region = loc.get("LocationConstraint") or "us-east-1"
                if bucket_region != kwargs.get("region_name"):
                    kwargs["region_name"] = bucket_region
                    client = boto3.client("s3", **kwargs)
            except Exception:
                logger.debug("Could not resolve bucket region; using configured S3_REGION", exc_info=True)
        _ensure_bucket(client, settings.S3_BUCKET)
        _s3_client = client
        target = settings.S3_ENDPOINT or f"aws:s3:{settings.S3_REGION or 'default'}"
        logger.info("Using S3 storage (%s, bucket=%s)", target, settings.S3_BUCKET)
    except Exception:
        logger.warning("S3 unreachable; using local filesystem storage", exc_info=True)
        _s3_client = None
    return _s3_client


def save_file(key: str, data: bytes, content_type: str) -> str:
    """Returns a URL the frontend can download from."""
    s3 = _get_s3()
    if s3 is not None:
        s3.put_object(Bucket=settings.S3_BUCKET, Key=key, Body=data, ContentType=content_type)
        return s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": settings.S3_BUCKET, "Key": key},
            ExpiresIn=7 * 24 * 3600,
        )
    path = Path(settings.LOCAL_STORAGE_DIR) / key
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return local_file_url(key)


def storage_mode() -> str:
    return "s3" if _get_s3() is not None else "local"
