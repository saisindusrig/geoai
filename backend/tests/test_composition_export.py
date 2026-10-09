import json
from scripts.export_stage1_contracts import outputs


def test_composition_export_is_deterministic_and_current():
    first=outputs()
    assert first==outputs()
    for path,content in first.items():
        assert path.read_text(encoding="utf-8")==content, f"Generated contract drift: {path}"
    schema=json.loads(next(v for k,v in first.items() if k.suffix==".json"))
    assert "composition" in schema["properties"]
    assert {"AssetProposal","PatchProposal","RelationshipInput","ObjectLineage"} <= schema["$defs"].keys()
