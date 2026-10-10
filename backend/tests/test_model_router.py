import asyncio
import pytest
from pydantic import ValidationError
from app.core.config import settings
from app.services.ai.provider import RoutingMetadata, ModelRouter, FixtureProvider


@pytest.mark.parametrize("metadata,tier", [
    ({"intent":"QUESTION"},"FAST"), ({"intent":"EXPLANATION_REQUEST"},"FAST"),
    ({"intent":"DESIGN_REQUEST","asset_count":3},"PRIMARY"),
    ({"intent":"CHANGE_REQUEST","requested_effect":"PROPOSAL_ONLY"},"PRIMARY"),
    ({"intent":"SITE_QUERY","tool_requirement":True},"PRIMARY"),
    ({"intent":"QUESTION","complexity":"COMPLEX"},"PRIMARY"),
    ({"intent":"QUESTION","retry_state":True},"PRIMARY"),
])
def test_routing_metadata(metadata,tier,monkeypatch):
    monkeypatch.setattr(settings,"NEBIUS_FAST_MODEL","fixture-fast")
    monkeypatch.setattr(settings,"NEBIUS_PRIMARY_MODEL","fixture-primary")
    route=ModelRouter().route(RoutingMetadata(**metadata))
    assert route.tier==tier and route.provider=="nebius"
    assert route.model==('fixture-fast' if tier=='FAST' else 'fixture-primary')
    assert route.tool_calling_allowed==metadata.get("tool_requirement",False)
    assert route.timeout==(settings.NEBIUS_PRIMARY_COMPLETION_TIMEOUT_SECONDS if tier=='PRIMARY' else settings.NEBIUS_TIMEOUT_SECONDS) and route.max_output_tokens<=3500


@pytest.mark.parametrize("effect",["GENERATE","CALCULATE"])
def test_deterministic_work_never_routes(effect):
    with pytest.raises(ValueError,match="DETERMINISTIC"):ModelRouter().route(RoutingMetadata(intent="DESIGN_REQUEST",requested_effect=effect))


def test_router_rejects_payloads_and_unbounded_metadata():
    with pytest.raises(ValidationError):RoutingMetadata(intent="QUESTION",chat="sensitive context")
    with pytest.raises(ValidationError):RoutingMetadata(intent="QUESTION",asset_count=101)
    with pytest.raises(ValidationError):RoutingMetadata(intent="QUESTION",context_size=100001)


def test_fixture_provider_preserved():
    async def callback(system,payload):return {"text":"Recorded fixture"}
    route=ModelRouter().route(RoutingMetadata(intent="QUESTION"))
    assert asyncio.run(FixtureProvider(callback).complete("system",{},route))=={"text":"Recorded fixture"}
