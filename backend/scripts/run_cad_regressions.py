"""Offline regression runner: no real Nebius HTTP or configured S3 clients.

Tests retain settings for source/redaction assertions. Explicit mock transports
and mocked storage clients remain available to fixtures; live clients do not.
"""
from pathlib import Path
import sys
import tempfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import httpx
import pytest
from app.services import storage

sync_send = httpx.Client.send
async_send = httpx.AsyncClient.send


def blocked(request,client):
    return "nebius" in request.url.host.lower() and isinstance(client._transport,(httpx.HTTPTransport,httpx.AsyncHTTPTransport))


def guarded_sync(self,request,*args,**kwargs):
    if blocked(request,self):
        raise AssertionError("LIVE_NEBIUS_FORBIDDEN")
    return sync_send(self,request,*args,**kwargs)


async def guarded_async(self,request,*args,**kwargs):
    if blocked(request,self):
        raise AssertionError("LIVE_NEBIUS_FORBIDDEN")
    return await async_send(self,request,*args,**kwargs)


if __name__ == "__main__":
    httpx.Client.send = guarded_sync
    httpx.AsyncClient.send = guarded_async
    storage._get_s3 = lambda: None
    with tempfile.TemporaryDirectory(prefix="cad-regression-storage-") as isolated_storage:
        storage.settings.LOCAL_STORAGE_DIR = isolated_storage
        raise SystemExit(pytest.main(sys.argv[1:] or ["tests","-q"]))
