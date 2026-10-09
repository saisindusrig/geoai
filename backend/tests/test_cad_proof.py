"""Opt-in native CAD tests; standard backend installs skip this experiment."""
from copy import deepcopy
import math
import pytest

pytest.importorskip("OCP", reason="Install requirements-cad-proof.txt in an isolated environment")
from app.experimental import cad_geometry as cad
from app.experimental.bim_cad import build_candidate, regenerate, TrustedSource
from app.experimental.cad_fixtures import support_frame, TRUSTED


@pytest.mark.parametrize("shape,volume,dimensions", [
    (lambda: cad.extrude(cad.rectangle(.3,.5),5), .75, (.3,.5,5)),
    (lambda: cad.extrude(cad.i_profile(.3,.5,.02,.03),5), (.3*.03*2+.02*.44)*5, (.3,.5,5)),
    (lambda: cad.circular_column(.2,3), math.pi*.2**2*3, (.4,.4,3)),
    (lambda: cad.box_with_opening(5,3,.2,hole_width=.8,hole_depth=.6), (15-.48)*.2, (5,3,.2)),
    (lambda: cad.box_with_opening(.4,.4,.02,hole_radius=.04), (.16-math.pi*.04**2)*.02, (.4,.4,.02)),
    (lambda: cad.tapered_rectangle(.4,.4,.2,.2,5), 5*(.16+.04+math.sqrt(.16*.04))/3, (.4,.4,5)),
])
def test_true_solids_dimensions_volume_topology_mesh(shape,volume,dimensions):
    solid = shape()
    result = cad.solid_metrics(solid)
    assert result["valid"] and result["solidCount"] == 1 and result["units"] == "m"
    assert result["volumeM3"] == pytest.approx(volume, rel=1e-7)
    bounds = result["boundsM"]
    assert [bounds[i+3]-bounds[i] for i in range(3)] == pytest.approx(dimensions, abs=1e-6)
    mesh = cad.tessellate(solid)
    assert mesh["positions"] and mesh["triangles"]
    assert all(0 <= i < len(mesh["positions"]) for t in mesh["triangles"] for i in t)
    assert mesh == cad.tessellate(shape())
    import trimesh
    render = trimesh.Trimesh(vertices=mesh["positions"],faces=mesh["triangles"],process=True)
    assert render.is_watertight and render.is_winding_consistent
    assert render.volume == pytest.approx(volume,rel=.005)


def test_boolean_openings_are_empty_space():
    from OCP.BRepClass3d import BRepClass3d_SolidClassifier
    from OCP.TopAbs import TopAbs_OUT, TopAbs_IN
    from OCP.gp import gp_Pnt
    for solid in [cad.box_with_opening(5,3,.2,hole_width=.8,hole_depth=.6), cad.box_with_opening(5,3,.2,hole_radius=.2)]:
        assert BRepClass3d_SolidClassifier(solid,gp_Pnt(0,0,.1),cad.TOLERANCE_M).State() == TopAbs_OUT
        assert BRepClass3d_SolidClassifier(solid,gp_Pnt(1,1,.1),cad.TOLERANCE_M).State() == TopAbs_IN


def test_arbitrary_profile_extrusion():
    solid = cad.extrude([(0,0),(2,0),(2,1),(1,1),(1,2),(0,2)],3)
    assert cad.solid_metrics(solid)["volumeM3"] == pytest.approx(9)


@pytest.mark.parametrize("build", [
    lambda: cad.extrude([(0,0),(1,1),(0,1),(1,0)],3),
    lambda: cad.i_profile(.3,.5,.4,.03),
    lambda: cad.i_profile(.3,.5,.02,.3),
    lambda: cad.circular_column(float("nan"),3),
    lambda: cad.extrude(cad.rectangle(.3,.5),0),
    lambda: cad.box_with_opening(5,3,.2,hole_width=6,hole_depth=1),
    lambda: cad.box_with_opening(5,3,.2,hole_radius=2),
])
def test_invalid_geometry_rejected(build):
    with pytest.raises(ValueError):
        build()


def test_non_solid_topology_rejected():
    from OCP.TopoDS import TopoDS_Shape
    with pytest.raises(ValueError,match="INVALID_CAD_TOPOLOGY"):
        cad.validate_solid(TopoDS_Shape())
    with pytest.raises(ValueError,match="SINGLE_POSITIVE_SOLID_REQUIRED"):
        cad.validate_solid(cad.profile_wire(cad.rectangle(1,1)))


def test_cross_asset_reuse_and_determinism():
    bridge = build_candidate(*support_frame("BRIDGE"), trusted=TRUSTED)
    industry = build_candidate(*support_frame("INDUSTRIAL_PLATFORM"), trusted=TRUSTED)
    assert len(bridge.outputs) == 10
    assert bridge.outputs == industry.outputs
    assert bridge.outputs == build_candidate(*support_frame("BRIDGE"),trusted=TRUSTED).outputs
    for component in bridge.model.components:
        output = bridge.outputs[component.id]
        assert output["id"] == component.id and output["materialId"] == component.material_id
        assert output["assemblyId"] == component.assembly_id
        assert output["provenance"] == component.provenance.model_dump(mode="json",by_alias=True)


def test_length_regeneration_and_atomicity():
    original = build_candidate(*support_frame(),trusted=TRUSTED)
    before = deepcopy(original.outputs)
    updated, dirty = regenerate(original,{("primary-0","length"):6},trusted=TRUSTED)
    assert dirty == ["primary-0","primary-1"]
    assert updated.epoch == 2
    for id in dirty:
        bounds = updated.outputs[id]["metrics"]["boundsM"]
        assert bounds[3]-bounds[0] == pytest.approx(6,abs=1e-6)
        assert [bounds[4]-bounds[1],bounds[5]-bounds[2]] == pytest.approx([.3,.5],abs=1e-6)
        assert updated.outputs[id]["metrics"]["volumeM3"] == pytest.approx(original.outputs[id]["metrics"]["volumeM3"]*6/5)
        assert updated.outputs[id]["id"] == original.outputs[id]["id"]
    for id in set(before)-set(dirty):
        assert updated.outputs[id] == before[id]
    assert original.outputs == before
    assert original.model.components[4].parameters[0].value == 5
    assert original.model.components[4].geometry.primitive.size[0] == pytest.approx(5)
    assert updated.model.components[4].geometry.primitive.size[0] == pytest.approx(6)
    with pytest.raises(ValueError):
        regenerate(original,{("primary-0","length"):0},trusted=TRUSTED)
    assert original.outputs == before


def test_unit_unsupported_recipe_and_source_rejection():
    model, mapping = support_frame()
    with pytest.raises(ValueError,match="UNTRUSTED_CAD_SOURCE"):
        build_candidate(model,mapping,trusted=TrustedSource("forged",1,None))
    raw = model.model_dump()
    raw["components"][0]["parameters"][0]["unit"] = "deg"
    with pytest.raises(ValueError,match="CAD_METRE_PARAMETERS_REQUIRED"):
        build_candidate(raw,mapping,trusted=TRUSTED)
    raw = mapping.model_dump()
    raw["recipes"][0]["operation"] = "ARBITRARY_SCRIPT"
    with pytest.raises(ValueError):
        build_candidate(model,raw,trusted=TRUSTED)


def test_assembly_and_component_transform():
    model, mapping = support_frame()
    raw = model.model_dump()
    raw["assemblies"][0]["placement"] = dict(origin=[10,20,0],heading_deg=90)
    transformed = build_candidate(raw,mapping,trusted=TRUSTED)
    bounds = transformed.outputs["primary-0"]["metrics"]["boundsM"]
    assert bounds[4]-bounds[1] == pytest.approx(5,abs=1e-6)
    assert bounds[0] > 9 and bounds[1] == pytest.approx(20,abs=1e-6)


def test_brep_round_trip(tmp_path):
    from OCP.BRepTools import BRepTools
    from OCP.BRep import BRep_Builder
    from OCP.TopoDS import TopoDS_Shape
    shape = cad.box_with_opening(5,3,.2,hole_width=.8,hole_depth=.6)
    path = str(tmp_path/'slab.brep')
    assert BRepTools.Write_s(shape,path)
    restored = TopoDS_Shape()
    assert BRepTools.Read_s(restored,path,BRep_Builder())
    assert cad.solid_metrics(restored) == cad.solid_metrics(shape)


def test_gltf_export_preserves_component_nodes_and_axes():
    from scripts.run_cad_proof import gltf
    model = build_candidate(*support_frame(),trusted=TRUSTED)
    result = gltf(model.outputs)
    assert len(result['nodes']) == 10
    assert {n['name'] for n in result['nodes']} == set(model.outputs)
    assert all(n['extras']['id']==n['name'] for n in result['nodes'])
    assert result['extras']['axisConversion'] == 'x,y,z -> x,z,-y'
    assert all(m['primitives'][0]['attributes']['NORMAL']>=0 for m in result['meshes'])


def test_failure_after_first_solid_is_atomic(monkeypatch):
    import app.experimental.bim_cad as service
    original = build_candidate(*support_frame(),trusted=TRUSTED)
    before = deepcopy(original.outputs)
    compile_ = service.compile_component
    def fail_second(model,component,recipe):
        if component.id == 'primary-1':
            raise ValueError('NATIVE_BUILD_FAILED')
        return compile_(model,component,recipe)
    monkeypatch.setattr(service,'compile_component',fail_second)
    with pytest.raises(ValueError,match='NATIVE_BUILD_FAILED'):
        regenerate(original,{('primary-0','length'):6},trusted=TRUSTED)
    assert original.outputs == before
    assert original.model.components[4].parameters[0].value == 5
