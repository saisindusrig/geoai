"""Tests for file storage URL generation and normalization."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.services import storage


@pytest.fixture(autouse=True)
def reset_storage():
    storage.reset_storage_cache()
    yield
    storage.reset_storage_cache()


def test_local_file_url_uses_public_api_base(monkeypatch):
    monkeypatch.setattr(storage.settings, "PUBLIC_API_URL", "https://api.example.com")
    assert storage.local_file_url("projects/1/model.glb") == (
        "https://api.example.com/files/projects/1/model.glb"
    )


def test_normalize_file_url_rewrites_localhost():
    with patch.object(storage.settings, "PUBLIC_API_URL", "https://geoai-api-91oc.onrender.com"):
        assert storage.normalize_file_url("http://localhost:8000/files/projects/5/model.glb") == (
            "https://geoai-api-91oc.onrender.com/files/projects/5/model.glb"
        )


def test_normalize_file_url_relative_path():
    with patch.object(storage.settings, "PUBLIC_API_URL", "https://api.example.com"):
        assert storage.normalize_file_url("/files/a.glb") == "https://api.example.com/files/a.glb"


def test_save_file_local_uses_public_base(tmp_path, monkeypatch):
    monkeypatch.setattr(storage.settings, "LOCAL_STORAGE_DIR", str(tmp_path))
    monkeypatch.setattr(storage.settings, "PUBLIC_API_URL", "https://api.example.com")
    storage.reset_storage_cache()
    url = storage.save_file("test/demo.glb", b"glb-bytes", "model/gltf-binary")
    assert url == "https://api.example.com/files/test/demo.glb"
    assert (tmp_path / "test" / "demo.glb").read_bytes() == b"glb-bytes"


def test_save_file_s3_presigned(monkeypatch):
    mock_client = MagicMock()
    mock_client.generate_presigned_url.return_value = "https://s3.example.com/signed"
    monkeypatch.setattr(storage.settings, "S3_ACCESS_KEY", "key")
    monkeypatch.setattr(storage.settings, "S3_SECRET_KEY", "secret")
    monkeypatch.setattr(storage.settings, "S3_BUCKET", "bucket")
    monkeypatch.setattr(storage, "_get_s3", lambda: mock_client)
    url = storage.save_file("projects/1/model.glb", b"x", "model/gltf-binary")
    assert url == "https://s3.example.com/signed"
    mock_client.put_object.assert_called_once()
