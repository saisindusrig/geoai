"""Pure deterministic dependency-aware compilation to editable primitives."""
from copy import deepcopy
import hashlib
import math
from shapely import affinity
from shapely.geometry import Polygon, LineString, Point, box as rectangle
from app.domain.ai3d import AI3DDesign
from app.services.design.geometry_utils import box
from app.core.asset_families import asset_definition

EXECUTOR_VERSION = "1"


def stable_id(design, object_id, suffix=""):
    value = f"{design}:{object_id}{suffix}"
    return value if len(value) <= 128 else f"{design[:40]}:{hashlib.sha256(value.encode()).hexdigest()}"


def dependencies(obj):
    params = obj.parameters
    return [ref for ref in [obj.parent_id, getattr(params, "path_ref", None), getattr(params, "polygon_ref", None), getattr(params, "template_ref", None)] if ref]


def topological_order(spec):
    objects = {obj.object_id: obj for obj in spec.objects}
    if len(objects) != len(spec.objects): raise ValueError("DUPLICATE_OBJECT_ID")
    pending = set(objects); ordered = []
    while pending:
        ready = sorted(key for key in pending if all(ref in ordered for ref in dependencies(objects[key])))
        if not ready:
            if any(ref not in objects for key in pending for ref in dependencies(objects[key])): raise ValueError("UNRESOLVED_REFERENCE")
            raise ValueError("CIRCULAR_DEPENDENCY")
        ordered.extend(ready); pending.difference_update(ready)
    return [objects[key] for key in ordered]


def footprint(raw):
    if raw["kind"] == "box":
        x,y,_ = raw["center"]; length,width,_ = raw["size"]
        return affinity.rotate(rectangle(x-length/2,y-width/2,x+length/2,y+width/2),raw["rotation_z_deg"],origin=(x,y))
    start,end = raw["start"],raw["end"]
    return LineString([start[:2],end[:2]]).buffer(raw["radius_m"]) if start[:2] != end[:2] else Point(start[:2]).buffer(raw["radius_m"])


def compile_geometry(design):
    spec = AI3DDesign.model_validate(design)
    resolved = {}; output = []; systems = {s.id:s for s in spec.systems}
    if len(systems) != len(spec.systems): raise ValueError("DUPLICATE_SYSTEM_ID")
    if set(systems) & {o.object_id for o in spec.objects}: raise ValueError("ID_NAMESPACE_CONFLICT")
    for obj in topological_order(spec):
        if obj.system_id not in systems: raise ValueError("UNRESOLVED_SYSTEM")
        params=obj.parameters; kind=params.primitive_type; solids=[]; reference=None
        def path(ref):
            found=resolved[ref]
            if found["kind"] not in {"PATH","OFFSET"}: raise ValueError("PATH_REFERENCE_REQUIRED")
            return found["reference"]
        def add_box(center,size,heading=0):
            solids.append(box(obj.object_id,obj.semantic_type.lower(),center,size,heading))
        if kind=="POINT": reference=list(params.position)
        elif kind in {"PATH","POLYGON"}:
            reference=[list(p) for p in params.points]
            if kind=="PATH":
                if any(math.dist(a,b)<.001 for a,b in zip(reference,reference[1:])): raise ValueError("ZERO_LENGTH_PATH")
                if not LineString([p[:2] for p in reference]).is_simple: raise ValueError("SELF_INTERSECTING_PATH")
            else:
                polygon=Polygon([p[:2] for p in reference])
                if reference[0]!=reference[-1] or not polygon.is_valid or polygon.area<=0: raise ValueError("INVALID_POLYGON")
                if len({p[2] for p in reference})!=1: raise ValueError("NONPLANAR_POLYGON")
        elif kind=="BOX": add_box(params.center,params.size,params.heading_deg)
        elif kind=="CYLINDER":
            if math.dist(params.start,params.end)<.001: raise ValueError("ZERO_LENGTH_CYLINDER")
            solids.append({"kind":"cylinder","name":obj.object_id,"layer":obj.semantic_type.lower(),"start":list(params.start),"end":list(params.end),"radius_m":params.radius_m})
        elif kind in {"EXTRUDE","SURFACE"}:
            source=resolved[params.polygon_ref]
            if source["kind"]!="POLYGON": raise ValueError("POLYGON_REFERENCE_REQUIRED")
            polygon=Polygon([p[:2] for p in source["reference"]]); x,y,x2,y2=polygon.bounds
            if not polygon.equals(rectangle(x,y,x2,y2)): raise ValueError("RECTANGULAR_EXTRUSION_ONLY")
            add_box(((x+x2)/2,(y+y2)/2,source["reference"][0][2]+params.height_m/2),(x2-x,y2-y,params.height_m))
        elif kind=="OFFSET":
            points=path(params.path_ref)
            if len(points)!=2 or points[0][2]!=points[1][2]: raise ValueError("STRAIGHT_PLANAR_OFFSET_ONLY")
            dx,dy=points[1][0]-points[0][0],points[1][1]-points[0][1]; length=math.hypot(dx,dy)
            if length<.001: raise ValueError("ZERO_LENGTH_PATH")
            reference=[[p[0]-dy/length*params.distance_m,p[1]+dx/length*params.distance_m,p[2]] for p in points]
        elif kind in {"SWEEP","PIPE","CHANNEL"}:
            points=path(params.path_ref)
            if kind=="CHANNEL" and (params.thickness_m*2>=params.width_m or params.thickness_m>=params.depth_m): raise ValueError("INVALID_CHANNEL_SECTION")
            for a,b in zip(points,points[1:]):
                if kind=="PIPE":
                    solids.append({"kind":"cylinder","name":obj.object_id,"layer":obj.semantic_type.lower(),"start":list(a),"end":list(b),"radius_m":params.radius_m})
                    continue
                if a[2]!=b[2]: raise ValueError("PLANAR_SWEEP_ONLY")
                dx,dy=b[0]-a[0],b[1]-a[1]; length=math.hypot(dx,dy)
                if length<.001: raise ValueError("ZERO_LENGTH_PATH")
                heading=math.degrees(math.atan2(dy,dx)); center=[(a[i]+b[i])/2 for i in range(3)]
                if kind=="SWEEP": add_box(center,(length,params.width_m,params.thickness_m),heading)
                else:
                    add_box((center[0],center[1],center[2]-params.depth_m/2),(length,params.width_m,params.thickness_m),heading)
                    for sign in (-1,1):
                        offset=sign*(params.width_m-params.thickness_m)/2
                        add_box((center[0]-dy/length*offset,center[1]+dx/length*offset,center[2]),(length,params.thickness_m,params.depth_m),heading)
        elif kind in {"ARRAY_ALONG_PATH","ARRAY_ON_GRID"}:
            template=resolved[params.template_ref]
            if template["kind"] not in {"BOX","CYLINDER"} or not template["templateOnly"]: raise ValueError("SIMPLE_TEMPLATE_REQUIRED")
            locations=[]
            if kind=="ARRAY_ON_GRID":
                locations=[[params.origin[0]+col*params.spacing_x_m,params.origin[1]+row*params.spacing_y_m,params.origin[2]] for row in range(params.rows) for col in range(params.columns)]
            else:
                points=path(params.path_ref); lengths=[math.dist(a,b) for a,b in zip(points,points[1:])]
                for index in range(params.count):
                    distance=params.start_chainage_m+index*params.spacing_m
                    if distance>sum(lengths)+1e-8: raise ValueError("ARRAY_EXCEEDS_PATH")
                    for a,b,length in zip(points,points[1:],lengths):
                        if distance<=length+1e-8:
                            locations.append([a[i]+(b[i]-a[i])*distance/length for i in range(3)]);break
                        distance-=length
            for location in locations:
                for original in template["solids"]:
                    raw=deepcopy(original)
                    for field in (["center"] if raw["kind"]=="box" else ["start","end"]):raw[field]=[raw[field][i]+location[i] for i in range(3)]
                    raw["name"]=obj.object_id;raw["layer"]=obj.semantic_type.lower();solids.append(raw)
        resolved[obj.object_id]={"kind":kind,"reference":reference,"solids":solids,"templateOnly":obj.template_only,"systemId":obj.system_id}
        if not obj.template_only:
            for index,raw in enumerate(solids):
                suffix=f":{index:03d}" if len(solids)>1 else ""
                raw["semantic"]={"id":stable_id(spec.design_id,obj.object_id,suffix),"ai3dDesignId":spec.design_id,"systemId":obj.system_id,
                    "assetFamily":asset_definition(systems[obj.system_id].asset_type)["family"],"systemAssetType":systems[obj.system_id].asset_type,
                    "sourceParentId":obj.parent_id,
                    "sourceObjectId":obj.object_id,"primitiveType":kind,"componentKind":obj.semantic_type,"componentRole":obj.role,
                    "executorVersion":EXECUTOR_VERSION,"referencePlane":"LOCAL_VISUAL_REFERENCE"}
                output.append(raw)
        if len(output)>1000: raise ValueError("OUTPUT_COMPONENT_LIMIT")
    if not output: raise ValueError("NO_SOLID_OUTPUT")
    for raw in output:
        dimensions=raw["size"] if raw["kind"]=="box" else [math.dist(raw["start"],raw["end"]),2*raw["radius_m"]]
        if any(not math.isfinite(v) or v<=0 or v>500 for v in dimensions):raise ValueError("OUTPUT_DIMENSION_LIMIT")
        coords=[raw["center"]] if raw["kind"]=="box" else [raw["start"],raw["end"]]
        if any(not math.isfinite(v) or abs(v)>2000 for p in coords for v in p):raise ValueError("OUTPUT_COORDINATE_LIMIT")
        if any(abs(v)>2500 for v in footprint(raw).bounds):raise ValueError("OUTPUT_EXTENT_LIMIT")
    return {"objects":output,"frame":"local_meters","referencePlane":"LOCAL_VISUAL_REFERENCE"},resolved
