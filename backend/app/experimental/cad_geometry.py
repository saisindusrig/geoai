"""Isolated OCCT solids in metres. No scripts, persistence, or AI execution.

Install requirements-cad-proof.txt separately. Native shapes never enter a model
document. Meshes are derived caches, not the authoritative CAD/BIM definition.
"""
import math
from OCP.BRep import BRep_Tool
from OCP.BRepAlgoAPI import BRepAlgoAPI_Cut
from OCP.BRepBndLib import BRepBndLib
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakePolygon, BRepBuilderAPI_MakeFace, BRepBuilderAPI_Transform
from OCP.BRepCheck import BRepCheck_Analyzer
from OCP.BRepGProp import BRepGProp
from OCP.BRepMesh import BRepMesh_IncrementalMesh
from OCP.BRepOffsetAPI import BRepOffsetAPI_ThruSections
from OCP.BRepPrimAPI import BRepPrimAPI_MakeBox, BRepPrimAPI_MakeCylinder, BRepPrimAPI_MakePrism
from OCP.Bnd import Bnd_Box
from OCP.GProp import GProp_GProps
from OCP.TopAbs import TopAbs_SOLID, TopAbs_FACE, TopAbs_REVERSED
from OCP.TopExp import TopExp_Explorer
from OCP.TopLoc import TopLoc_Location
from OCP.TopoDS import TopoDS
from OCP.gp import gp_Pnt, gp_Vec, gp_Trsf, gp_Ax1, gp_Dir
from shapely.geometry import Polygon

TOLERANCE_M = 1e-7
MESH_DEFLECTION_M = .002
MESH_ANGLE_RAD = .2


def positive(*values):
    if any(not math.isfinite(v) or v < .0001 or v > 500 for v in values):
        raise ValueError("INVALID_CAD_DIMENSION")


def profile_wire(points):
    if not 3 <= len(points) <= 50 or any(not math.isfinite(v) or abs(v) > 500 for p in points for v in p):
        raise ValueError("INVALID_PROFILE")
    polygon = Polygon(points)
    if not polygon.is_valid or polygon.area <= TOLERANCE_M ** 2:
        raise ValueError("INVALID_PROFILE")
    builder = BRepBuilderAPI_MakePolygon()
    for x, y in points:
        builder.Add(gp_Pnt(x, y, 0))
    builder.Close()
    if not builder.IsDone():
        raise ValueError("PROFILE_CONSTRUCTION_FAILED")
    return builder.Wire()


def extrude(points, length):
    positive(length)
    face = BRepBuilderAPI_MakeFace(profile_wire(points)).Face()
    return validate_solid(BRepPrimAPI_MakePrism(face, gp_Vec(0, 0, length)).Shape())


def rectangle(width, depth):
    positive(width, depth)
    return [(-width/2, -depth/2), (width/2, -depth/2), (width/2, depth/2), (-width/2, depth/2)]


def i_profile(width, depth, web, flange):
    positive(width, depth, web, flange)
    if web >= width or flange * 2 >= depth:
        raise ValueError("INVALID_I_SECTION")
    w, d, t = width/2, depth/2, web/2
    return [(-w,-d),(w,-d),(w,-d+flange),(t,-d+flange),(t,d-flange),
            (w,d-flange),(w,d),(-w,d),(-w,d-flange),(-t,d-flange),(-t,-d+flange),(-w,-d+flange)]


def circular_column(radius, height):
    positive(radius, height)
    return validate_solid(BRepPrimAPI_MakeCylinder(radius, height).Shape())


def box_with_opening(width, depth, thickness, *, hole_width=None, hole_depth=None, hole_radius=None):
    positive(width, depth, thickness)
    base = BRepPrimAPI_MakeBox(gp_Pnt(-width/2, -depth/2, 0), width, depth, thickness).Shape()
    if hole_radius is not None:
        positive(hole_radius)
        if 2*hole_radius >= min(width, depth):
            raise ValueError("OPENING_OUTSIDE_MEMBER")
        cutter = BRepPrimAPI_MakeCylinder(gp_Ax2_z(-1), hole_radius, thickness+2).Shape()
    else:
        positive(hole_width, hole_depth)
        if hole_width >= width or hole_depth >= depth:
            raise ValueError("OPENING_OUTSIDE_MEMBER")
        cutter = BRepPrimAPI_MakeBox(gp_Pnt(-hole_width/2,-hole_depth/2,-1), hole_width, hole_depth, thickness+2).Shape()
    cut = BRepAlgoAPI_Cut(base, cutter)
    cut.SetRunParallel(False)
    cut.Build()
    if not cut.IsDone():
        raise ValueError("BOOLEAN_FAILED")
    return validate_solid(cut.Shape())


def gp_Ax2_z(z):
    from OCP.gp import gp_Ax2
    return gp_Ax2(gp_Pnt(0, 0, z), gp_Dir(0, 0, 1))


def tapered_rectangle(width, depth, end_width, end_depth, length):
    positive(length)
    first = profile_wire(rectangle(width, depth))
    last = profile_wire(rectangle(end_width, end_depth))
    translation = gp_Trsf()
    translation.SetTranslation(gp_Vec(0, 0, length))
    last = TopoDS.Wire(BRepBuilderAPI_Transform(last, translation, True).Shape())
    loft = BRepOffsetAPI_ThruSections(True, True, TOLERANCE_M)
    loft.AddWire(first)
    loft.AddWire(last)
    loft.Build()
    if not loft.IsDone():
        raise ValueError("LOFT_FAILED")
    return validate_solid(loft.Shape())


def validate_solid(shape):
    if shape.IsNull() or not BRepCheck_Analyzer(shape).IsValid():
        raise ValueError("INVALID_CAD_TOPOLOGY")
    explorer = TopExp_Explorer(shape, TopAbs_SOLID)
    count = 0
    while explorer.More():
        count += 1
        explorer.Next()
    properties = GProp_GProps()
    BRepGProp.VolumeProperties_s(shape, properties)
    if count != 1 or not math.isfinite(properties.Mass()) or properties.Mass() <= TOLERANCE_M**3:
        raise ValueError("SINGLE_POSITIVE_SOLID_REQUIRED")
    return shape


def solid_metrics(shape):
    validate_solid(shape)
    properties = GProp_GProps()
    BRepGProp.VolumeProperties_s(shape, properties)
    bounds = Bnd_Box()
    # Exact geometry bounds, independent of tessellation; ignore bounding-box gap.
    BRepBndLib.AddOptimal_s(shape, bounds, False, False)
    # OCP 8's Bnd_Box.Get returns an unregistered C++ Limits type. Corners are
    # bound gp_Pnt values and retain exact bounds without relying on that wrapper.
    low, high = bounds.CornerMin(), bounds.CornerMax()
    return {"volumeM3": properties.Mass(), "boundsM": [low.X(),low.Y(),low.Z(),high.X(),high.Y(),high.Z()], "solidCount": 1, "valid": True, "units": "m"}


def transform(shape, origin, heading_deg=0, horizontal=False):
    if horizontal:
        turn = gp_Trsf()
        # Profile x(width)->local y, profile y(depth)->local z,
        # extrusion z(length)->local x; preserve the section's vertical depth.
        turn.SetRotation(gp_Ax1(gp_Pnt(0,0,0),gp_Dir(1,1,1)), 2*math.pi/3)
        shape = BRepBuilderAPI_Transform(shape, turn, True).Shape()
    turn = gp_Trsf()
    turn.SetRotation(gp_Ax1(gp_Pnt(0,0,0),gp_Dir(0,0,1)), math.radians(heading_deg))
    shape = BRepBuilderAPI_Transform(shape, turn, True).Shape()
    translation = gp_Trsf()
    translation.SetTranslation(gp_Vec(*origin))
    return validate_solid(BRepBuilderAPI_Transform(shape, translation, True).Shape())


def tessellate(shape):
    validate_solid(shape)
    mesher = BRepMesh_IncrementalMesh(shape, MESH_DEFLECTION_M, False, MESH_ANGLE_RAD, False)
    if not mesher.IsDone():
        raise ValueError("TESSELLATION_FAILED")
    positions, triangles = [], []
    explorer = TopExp_Explorer(shape, TopAbs_FACE)
    while explorer.More():
        face = TopoDS.Face(explorer.Current())
        location = TopLoc_Location()
        triangulation = BRep_Tool.Triangulation_s(face, location)
        if triangulation is None:
            raise ValueError("MISSING_FACE_TRIANGULATION")
        offset = len(positions)
        for index in range(1, triangulation.NbNodes()+1):
            point = triangulation.Node(index).Transformed(location.Transformation())
            positions.append([point.X(), point.Y(), point.Z()])
        for index in range(1, triangulation.NbTriangles()+1):
            a, b, c = triangulation.Triangle(index).Get()
            if face.Orientation() == TopAbs_REVERSED:
                b, c = c, b
            triangles.append([offset+a-1, offset+b-1, offset+c-1])
        explorer.Next()
        if len(positions) > 100000 or len(triangles) > 200000:
            raise ValueError("MESH_LIMIT_EXCEEDED")
    if not triangles or any(not math.isfinite(v) for p in positions for v in p):
        raise ValueError("INVALID_RENDER_MESH")
    return {"positions": positions, "triangles": triangles, "units": "m", "deflectionM": MESH_DEFLECTION_M, "angleRad": MESH_ANGLE_RAD}
