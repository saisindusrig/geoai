"""Deterministic conceptual building adapter. No engineering solver, foundation or BOQ."""
import math
import hashlib
from pydantic import ValidationError
from shapely.geometry import Polygon, LineString, box as polygon_box, Point
from app.domain.building_specialist import BuildingSpec
from app.domain.specialist_metadata import AdapterMetadata
from app.services.design.geometry_utils import box


class BuildingSpecValidator:
    def validate(self, raw):
        try:spec=BuildingSpec.model_validate(raw)
        except ValidationError as exc:
            return {"status":"INVALID_SPEC","issues":[{"code":"SCHEMA_VALIDATION_FAILED","path":".".join(map(str,e["loc"])),"message":e["msg"]} for e in exc.errors(include_input=False)]}
        issues=[]
        def issue(code,path):issues.append({"code":code,"path":path,"message":code.replace("_"," ")})
        footprint=Polygon(spec.footprint)
        if not footprint.is_valid or footprint.area<=0 or spec.footprint[0]!=spec.footprint[-1]:issue("INVALID_FOOTPRINT","footprint")
        elif not footprint.equals(polygon_box(*footprint.bounds)):issue("UNSUPPORTED_FOOTPRINT","footprint")
        all_ids=[x.id for group in (spec.spaces,spec.walls,spec.openings,spec.columns,spec.beams) for x in group]
        if len(set(all_ids))!=len(all_ids):issue("DUPLICATE_COMPONENT_ID","components")
        generated_ids=[f"slab-{floor}" for floor in range(spec.floors+1)]+[s.id for s in spec.spaces]+[o.id for o in spec.openings]
        generated_ids += [f"{member.id}-{floor}" for member in [*spec.columns,*spec.beams] for floor in range(spec.floors)]
        for wall in spec.walls:
            generated_ids.append(f"{wall.id}-end")
            for opening in spec.openings:
                if opening.wall_id==wall.id:generated_ids.extend(f"{wall.id}-{part}-{opening.id}" for part in ("before","sill","lintel"))
        if len(set(generated_ids))!=len(generated_ids):issue("DUPLICATE_GENERATED_ID","components")
        walls={w.id:w for w in spec.walls}
        if footprint.is_valid and footprint.area>0:
            for i,space in enumerate(spec.spaces):
                if space.floor>=spec.floors or not footprint.covers(polygon_box(space.x,space.y,space.x+space.width,space.y+space.depth)):issue("SPACE_OUTSIDE_FOOTPRINT",f"spaces.{i}")
                for other in spec.spaces[:i]:
                    if space.floor==other.floor and polygon_box(space.x,space.y,space.x+space.width,space.y+space.depth).intersection(polygon_box(other.x,other.y,other.x+other.width,other.y+other.depth)).area>.001:issue("OVERLAPPING_SPACES",f"spaces.{i}")
            if {s.floor for s in spec.spaces}!=set(range(spec.floors)):issue("MISSING_FLOOR_SPACE","spaces")
            for i,wall in enumerate(spec.walls):
                if wall.floor>=spec.floors or math.dist(wall.start,wall.end)<.2 or not footprint.covers(LineString([wall.start,wall.end])):issue("INVALID_WALL",f"walls.{i}")
            from shapely.ops import unary_union
            for floor in range(spec.floors):
                shell=unary_union([LineString([w.start,w.end]) for w in spec.walls if w.floor==floor])
                if not shell.buffer(.00001).covers(footprint.boundary):issue("INCOMPLETE_EXTERNAL_WALLS",f"walls.floor.{floor}")
            for i,column in enumerate(spec.columns):
                if not footprint.covers(Point(column.x,column.y)):issue("COLUMN_OUTSIDE_FOOTPRINT",f"columns.{i}")
            for i,beam in enumerate(spec.beams):
                if math.dist(beam.start,beam.end)<.2 or not footprint.covers(LineString([beam.start,beam.end])):issue("INVALID_BEAM",f"beams.{i}")
        for i,opening in enumerate(spec.openings):
            wall=walls.get(opening.wall_id)
            if not wall or opening.offset+opening.width>math.dist(wall.start,wall.end) or opening.sill+opening.height>spec.floor_height-spec.slab_thickness:issue("OPENING_OUTSIDE_WALL",f"openings.{i}")
            for other in spec.openings[:i]:
                if other.wall_id==opening.wall_id and min(other.offset+other.width,opening.offset+opening.width)>max(other.offset,opening.offset):issue("OVERLAPPING_OPENINGS",f"openings.{i}")
        if spec.input_source=="PREVIEW_ASSUMPTION" and not spec.assumptions:issue("PREVIEW_ASSUMPTION_REQUIRED","assumptions")
        return {"status":"INVALID_SPEC" if issues else "SPEC_VALID","geometryStatus":"GEOMETRY_INVALID" if issues else "GEOMETRY_VALID","issues":issues,
                "engineeringStatus":"UNVALIDATED","limitations":["No structural, foundation, code, MEP, reinforcement or quantity validation."]}


class BuildingAdapter:
    metadata=AdapterMetadata("building-concept","1","BUILDING",frozenset({"BUILDING","OFFICE_BUILDING","WAREHOUSE"}),
        frozenset({"DISCUSS","PLAN","PROPOSE","GENERATE","VALIDATE_GEOMETRY"}),"building-concept/1",
        frozenset({"MOVE_COMPONENT","ROTATE_COMPONENT","RESIZE_OPENING","MOVE_OPENING","ADD_OPENING","REMOVE_OPENING"}))
    specification_schema=BuildingSpec
    def can_handle(self,asset_type):return asset_type.upper() in self.metadata.supported_asset_types
    def requirements_to_specification(self,requirements,context):return BuildingSpec.model_validate(requirements)
    def validate_specification(self,specification):return BuildingSpecValidator().validate(specification)
    def validate_geometry(self,geometry,specification):
        validation=self.validate_specification(specification)
        objects=geometry.get("objects",[]) if isinstance(geometry,dict) else []
        identifiers=[o.get("semantic",{}).get("id") for o in objects]
        if not objects or None in identifiers or len(set(identifiers))!=len(identifiers) or any(
            o.get("kind","box")!="box" or len(o.get("size",[]))!=3 or any(not math.isfinite(v) or v<=0 for v in o["size"])
            or len(o.get("center",[]))!=3 or any(not math.isfinite(v) for v in o["center"]) for o in objects):
            return {**validation,"status":"INVALID_SPEC","geometryStatus":"GEOMETRY_INVALID","issues":[*validation["issues"],{"code":"INVALID_GENERATED_GEOMETRY","path":"objects","message":"Generated geometry violates the model contract."}]}
        return validation
    def generate_preview(self,specification):return self.generate(specification)
    def apply_patch(self,model,patch):
        from app.services.assistant.building_patch import BuildingPatchValidator, SavedBuildingPatchContext
        if not isinstance(model,SavedBuildingPatchContext):raise ValueError("SAVED_PATCH_CONTEXT_REQUIRED")
        return BuildingPatchValidator().preview(model.db,model.project_id,patch)
    def generate(self,specification):
        spec=BuildingSpec.model_validate(specification)
        validation=self.validate_specification(spec)
        if validation["issues"]:raise ValueError("INVALID_BUILDING_SPEC")
        objects=[];angle=math.radians(spec.orientation)
        def solid(identifier,kind,floor,center,size,rotation=0):
            if min(size)<=.00001:return
            x,y,z=center
            raw=box(identifier,kind.lower(),(x*math.cos(angle)-y*math.sin(angle),x*math.sin(angle)+y*math.cos(angle),z),size,rotation+spec.orientation)
            semantic_id=f"{spec.building_id}:{identifier}"
            if len(semantic_id)>128:semantic_id=f"{spec.building_id[:40]}:{identifier[:50]}:{hashlib.sha256(semantic_id.encode()).hexdigest()[:24]}"
            component_kind="SLAB" if kind=="ROOF" else "OPENING" if kind in {"DOOR","WINDOW"} else kind
            raw["semantic"]={"id":semantic_id,"assetFamily":"BUILDING","componentKind":component_kind,"componentRole":kind,
                "sourceComponentId":identifier,"buildingId":spec.building_id,"floor":floor,"adapterVersion":"1"}
            objects.append(raw)
        def along(identifier,kind,wall,offset,length,z,height):
            total=math.dist(wall.start,wall.end);ux=(wall.end[0]-wall.start[0])/total;uy=(wall.end[1]-wall.start[1])/total
            solid(identifier,kind,wall.floor,(wall.start[0]+ux*(offset+length/2),wall.start[1]+uy*(offset+length/2),z+height/2),(length,wall.thickness,height),math.degrees(math.atan2(uy,ux)))
        x,y,x2,y2=Polygon(spec.footprint).bounds
        for floor in range(spec.floors+1):solid(f"slab-{floor}","ROOF" if floor==spec.floors else "SLAB",floor,((x+x2)/2,(y+y2)/2,floor*spec.floor_height-spec.slab_thickness/2),(x2-x,y2-y,spec.slab_thickness))
        for room in spec.spaces:solid(room.id,"ROOM",room.floor,(room.x+room.width/2,room.y+room.depth/2,room.floor*spec.floor_height+.01),(room.width,room.depth,.02))
        for column in spec.columns:
            for floor in range(spec.floors):solid(f"{column.id}-{floor}","COLUMN",floor,(column.x,column.y,(floor+.5)*spec.floor_height),(column.size,column.size,spec.floor_height))
        for beam in spec.beams:
            for floor in range(spec.floors):
                solid(f"{beam.id}-{floor}","BEAM",floor,((beam.start[0]+beam.end[0])/2,(beam.start[1]+beam.end[1])/2,(floor+1)*spec.floor_height-spec.slab_thickness-beam.depth/2),(math.dist(beam.start,beam.end),beam.width,beam.depth),math.degrees(math.atan2(beam.end[1]-beam.start[1],beam.end[0]-beam.start[0])))
        for wall in spec.walls:
            base=wall.floor*spec.floor_height;height=spec.floor_height-spec.slab_thickness;cursor=0
            for opening in sorted((o for o in spec.openings if o.wall_id==wall.id),key=lambda o:o.offset):
                along(f"{wall.id}-before-{opening.id}","WALL",wall,cursor,opening.offset-cursor,base,height)
                along(f"{wall.id}-sill-{opening.id}","WALL",wall,opening.offset,opening.width,base,opening.sill)
                along(f"{wall.id}-lintel-{opening.id}","WALL",wall,opening.offset,opening.width,base+opening.sill+opening.height,height-opening.sill-opening.height)
                along(opening.id,opening.kind.upper(),wall,opening.offset,opening.width,base+opening.sill,opening.height)
                cursor=opening.offset+opening.width
            along(f"{wall.id}-end","WALL",wall,cursor,math.dist(wall.start,wall.end)-cursor,base,height)
        return {"objects":objects,"frame":"local_meters","validation":validation,"referencePlane":"LOCAL_VISUAL_REFERENCE"}
