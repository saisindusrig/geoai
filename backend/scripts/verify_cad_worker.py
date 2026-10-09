"""Offline headless smoke/metric comparison. No DB, provider or cloud calls."""
import argparse
import json
import math
from pathlib import Path
import platform
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.experimental.cad_contract import Source, from_bim, digest
from app.experimental.cad_worker import compile_batch


def run():
    from importlib.metadata import version
    from OCP.TopAbs import TopAbs_FACE
    from OCP.TopExp import TopExp_Explorer
    from app.experimental import cad_geometry as cad
    from app.experimental.cad_fixtures import support_frame
    from app.services.assistant.bim_foundation import propagate_parameters
    from vtkmodules.vtkCommonCore import vtkVersion
    assert vtkVersion.GetVTKVersion() == "9.6.2"
    examples = {"concrete-beam":cad.extrude(cad.rectangle(.3,.5),5),
        "steel-I-beam":cad.extrude(cad.i_profile(.3,.5,.02,.03),5),
        "circular-column":cad.circular_column(.2,3),
        "slab-opening":cad.box_with_opening(5,3,.2,hole_width=.8,hole_depth=.6),
        "plate-hole":cad.box_with_opening(.4,.4,.02,hole_radius=.04),
        "tapered-member":cad.tapered_rectangle(.4,.4,.2,.2,5)}
    solids = {}
    for name,shape in examples.items():
        metrics = cad.solid_metrics(shape)
        explorer = TopExp_Explorer(shape,TopAbs_FACE)
        faces = 0
        while explorer.More():
            faces += 1
            explorer.Next()
        solids[name] = {**metrics,"faceCount":faces}
    model,mapping = support_frame()
    source = Source(project_id=1,revision_id=1,revision_document_hash=digest({}),design_id="cad-proof",design_version=1,source_model_revision_id=None)
    before = from_bim(model,mapping,source=source)
    old,_ = compile_batch(before)
    changed,dirty = propagate_parameters(model,{("primary-0","length"):6},expected_design_version=1)
    new,_ = compile_batch(from_bim(changed,mapping,source=source))
    old_by_id = {r.component_id:r for r in old}
    assert dirty == ["primary-0","primary-1"]
    for r in new:
        if r.component_id not in dirty:
            assert r == old_by_id[r.component_id]
    # Compare geometric invariants across OS, not byte-level native serialization.
    def metric(r):
        return {"boundsM":r.bounds_m,"volumeM3":r.volume_m3,"solidCount":r.solid_count,"valid":r.geometry_valid}
    return {"schemaVersion":"cad-platform-proof/1","platform":platform.platform(),"python":platform.python_version(),"libc":platform.libc_ver(),
            "packages":{n:version(n) for n in ("cadquery-ocp","cadquery-ocp-proxy","vtk")},
            "solids":solids,"before":{r.component_id:metric(r) for r in old},"after":{r.component_id:metric(r) for r in new},"dirty":dirty}


def compare(actual,expected):
    assert actual["packages"] == expected["packages"]
    assert actual["dirty"] == expected["dirty"]
    for group in ("solids","before","after"):
        assert set(actual[group]) == set(expected[group])
        for key,value in actual[group].items():
            target = expected[group][key]
            assert value["valid"] and value["solidCount"] == target["solidCount"] == 1
            assert math.isclose(value["volumeM3"],target["volumeM3"],rel_tol=1e-7,abs_tol=1e-9),(group,key,"volume")
            assert all(math.isclose(a,b,rel_tol=0,abs_tol=1e-6) for a,b in zip(value["boundsM"],target["boundsM"],strict=True)),(group,key,"bounds")
            if group == "solids":
                assert value["faceCount"] == target["faceCount"],(key,"analytic topology")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output",type=Path)
    parser.add_argument("--compare",type=Path)
    args = parser.parse_args()
    result = run()
    if args.compare:
        compare(result,json.loads(args.compare.read_text()))
    data = json.dumps(result,indent=2)+"\n"
    if args.output:
        args.output.write_text(data,encoding="utf-8")
    else:
        print(data)
