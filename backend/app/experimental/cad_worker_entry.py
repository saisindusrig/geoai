"""Internal fixed executable. Reads bounded data before loading native libraries."""
import hashlib
import json
import sys
from pathlib import Path


def main():
    # Parent supplies private scratch directory, never an authored recipe field.
    root = Path(sys.argv[1])
    payload = sys.stdin.buffer.read(2_000_001)
    if len(payload) > 2_000_000:
        raise ValueError("INPUT_LIMIT")
    from app.experimental.cad_contract import Geometry, Result, Artifact, digest, encode
    request = Geometry.model_validate_json(payload)
    from importlib.metadata import version
    if any(version(name) != pinned for name, pinned in (("cadquery-ocp", "8.0.1.1.0"), ("cadquery-ocp-proxy", "8.0.1.1.0"), ("vtk", "9.6.2"))):
        raise ValueError("KERNEL_VERSION_MISMATCH")
    from app.experimental import cad_geometry as cad
    from OCP.BRepTools import BRepTools
    results = []
    vertices = triangles = total_bytes = 0
    for d in request.definitions:
        r, p = d.recipe, dict(d.recipe.parameters)
        if r.operation == "PROFILE_EXTRUSION":
            length = p.pop("length")
            points = cad.rectangle(**p) if r.profile == "RECTANGLE" else cad.i_profile(**p)
            shape = cad.extrude(points, length)
        elif r.operation == "CIRCULAR_COLUMN":
            shape = cad.circular_column(p["radius"], p["length"])
        elif r.operation in ("RECTANGULAR_OPENING", "CIRCULAR_HOLE"):
            shape = cad.box_with_opening(**p)
        else:
            shape = cad.tapered_rectangle(**p)
        shape = cad.transform(shape, (0, 0, 0), horizontal=r.orientation == "HORIZONTAL")
        shape = cad.transform(shape, d.placement.origin, d.placement.heading_deg)
        shape = cad.transform(shape, d.assembly_placement.origin, d.assembly_placement.heading_deg)
        metrics = cad.solid_metrics(shape)
        # B-rep saved before meshing: disposable tessellation is not authoritative.
        scratch = root / "solid.brep"
        if not BRepTools.Write_s(shape, str(scratch)):
            raise ValueError("BREP_WRITE_FAILED")
        brep = scratch.read_bytes()
        mesh = cad.tessellate(shape)
        vertices += len(mesh["positions"])
        triangles += len(mesh["triangles"])
        if vertices > 250000 or triangles > 500000:
            raise ValueError("BATCH_MESH_LIMIT")
        mesh_bytes = encode(mesh)
        artifacts = []
        for kind, data in (("BREP", brep), ("MESH", mesh_bytes)):
            total_bytes += len(data)
            if total_bytes > 32_000_000:
                raise ValueError("BATCH_BYTE_LIMIT")
            sha = hashlib.sha256(data).hexdigest()
            (root / sha).write_bytes(data)
            artifacts.append(Artifact(sha256=sha, byte_length=len(data), kind=kind))
        b = metrics["boundsM"]
        results.append(Result(component_id=d.component_id, definition_hash=digest(d), brep=artifacts[0], mesh=artifacts[1],
            dimensions_m=[b[i+3]-b[i] for i in range(3)], bounds_m=b, volume_m3=metrics["volumeM3"]))
    scratch.unlink(missing_ok=True)
    sys.stdout.buffer.write(encode([r.model_dump(mode="json", by_alias=True) for r in results]))


if __name__ == "__main__":
    main()
