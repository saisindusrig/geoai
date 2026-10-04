from app.core.config import settings
from app.services.geospatial.tiles import get_map_runtime_config, get_tile_providers


def test_only_explicit_read_key_reaches_browser(monkeypatch):
    monkeypatch.setattr(settings, "CESIUM_ION_TOKEN", "legacy-possibly-write")
    monkeypatch.setattr(settings, "CESIUM_ION_WRITE_TOKEN", "server-write")
    monkeypatch.setattr(settings, "CESIUM_ION_READ_TOKEN", "")
    assert get_map_runtime_config()["cesium_ion_token"] is None
    assert get_tile_providers()["cesium_ion_available"] is False
    monkeypatch.setattr(settings, "CESIUM_ION_READ_TOKEN", "restricted-read")
    assert get_map_runtime_config()["cesium_ion_token"] == "restricted-read"
    assert "server-write" not in str(get_map_runtime_config())
