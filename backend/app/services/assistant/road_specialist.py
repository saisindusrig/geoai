"""Deterministic local planar road concepts with backend-derived chainage."""
import hashlib
import math
from pydantic import ValidationError
from shapely.geometry import LineString
from app.domain.road_specialist import RoadSpec
from app.domain.specialist_metadata import AdapterMetadata
from app.services.design.geometry_utils import box


def section_width(section):
    return section.carriageway_width_m + section.median_width_m + section.shoulder_left_m + section.shoulder_right_m + section.verge_left_m + section.verge_right_m


def chainage(spec):
    distances = [0.0]
    for first, second in zip(spec.alignment, spec.alignment[1:]):
        distances.append(distances[-1] + math.dist(first.position, second.position))
    return distances


def display_chainage(distance):
    return f"{int(distance // 1000)}+{distance % 1000:07.3f}"


class RoadSpecValidator:
    def validate(self, raw):
        try:
            spec = RoadSpec.model_validate(raw)
        except ValidationError as exc:
            return {"status": "INVALID_SPEC", "geometryStatus": "GEOMETRY_INVALID", "generationStatus": "GENERATION_UNSUPPORTED",
                    "issues": [{"code": "SCHEMA_VALIDATION_FAILED", "path": ".".join(map(str, e["loc"])), "message": e["msg"]} for e in exc.errors(include_input=False)]}
        issues = []
        def issue(code, path):
            issues.append({"code": code, "path": path, "message": code.replace("_", " ")})
        points = [p.position for p in spec.alignment]
        lengths = chainage(spec)
        if len({p.id for p in spec.alignment}) != len(points): issue("DUPLICATE_POINT_ID", "alignment")
        if any(math.dist(a, b) < .01 for a, b in zip(points, points[1:])): issue("ZERO_LENGTH_SEGMENT", "alignment")
        if not LineString(points).is_simple: issue("SELF_INTERSECTING_ALIGNMENT", "alignment")
        if lengths[-1] > 2000 or any(math.hypot(*p) > 2000 for p in points): issue("LOCAL_FRAME_LIMIT", "alignment")
        section = spec.cross_section
        if (section.lane_count is None) != (section.lane_width_m is None): issue("LANE_DIMENSIONS_REQUIRED", "crossSection")
        if section.lane_count and not math.isclose(section.lane_count * section.lane_width_m, section.carriageway_width_m, abs_tol=1e-6): issue("INCONSISTENT_LANE_WIDTH", "crossSection")
        if section.median_width_m and (not section.lane_count or section.lane_count % 2): issue("MEDIAN_REQUIRES_EVEN_LANES", "crossSection")
        if section_width(section) > 70: issue("TOTAL_WIDTH_LIMIT", "crossSection")
        if spec.input_source == "PREVIEW_ASSUMPTION" and not spec.assumptions: issue("PREVIEW_ASSUMPTION_REQUIRED", "assumptions")
        if spec.terrain_required: issue("TERRAIN_ROUTING_UNAVAILABLE", "terrainRequired")
        return {"status": "INVALID_SPEC" if issues else "SPEC_VALID", "geometryStatus": "GEOMETRY_INVALID" if issues else "GEOMETRY_VALID",
                "generationStatus": "GENERATION_UNSUPPORTED" if issues else "GENERATION_SUPPORTED", "engineeringStatus": "UNVALIDATED",
                "issues": issues, "chainageM": lengths, "totalWidthM": section_width(section),
                "limitations": ["Planar conceptual straight segments only; joints may overlap. No slope routing, pavement, traffic, hydraulic, geotechnical or code validation."]}


class RoadAdapter:
    metadata = AdapterMetadata("road-concept", "1", "ROAD", frozenset({"ROAD", "ACCESS_ROAD"}),
        frozenset({"DISCUSS", "PLAN", "PROPOSE", "VALIDATE_GEOMETRY"}), "road-concept/1", frozenset())
    specification_schema = RoadSpec
    def can_handle(self, asset_type): return asset_type.upper() in self.metadata.supported_asset_types
    def requirements_to_specification(self, requirements, context): return RoadSpec.model_validate(requirements)
    def validate_specification(self, specification): return RoadSpecValidator().validate(specification)
    def generate_preview(self, specification): return self.generate(specification)
    def apply_patch(self, model, patch): raise ValueError("ROAD_PATCH_UNAVAILABLE")
    def validate_geometry(self, geometry, specification):
        result = self.validate_specification(specification)
        objects = geometry.get("objects", [])
        ids = [o.get("semantic", {}).get("id") for o in objects]
        if not objects or None in ids or len(set(ids)) != len(ids) or any(
                o.get("kind") != "box" or len(o.get("size", [])) != 3 or any(not math.isfinite(v) or v <= 0 for v in o["size"])
                or len(o.get("center", [])) != 3 or any(not math.isfinite(v) for v in o["center"]) for o in objects):
            return {**result, "geometryStatus": "GEOMETRY_INVALID", "issues": [*result["issues"], {"code": "INVALID_GENERATED_GEOMETRY", "path": "objects", "message": "Invalid road component geometry"}]}
        return result
    def generate(self, specification):
        spec = RoadSpec.model_validate(specification)
        validation = self.validate_specification(spec)
        if validation["issues"]: raise ValueError("INVALID_ROAD_SPEC")
        distances = chainage(spec); section = spec.cross_section; objects = []
        for index, (a, b) in enumerate(zip(spec.alignment, spec.alignment[1:])):
            dx, dy = b.position[0] - a.position[0], b.position[1] - a.position[1]
            length = math.hypot(dx, dy); normal = (-dy / length, dx / length)
            heading = math.degrees(math.atan2(dy, dx)); segment = f"segment-{index}"
            def solid(role, width, offset, thickness, z, side=None, lane=None):
                if width <= 0: return
                key = f"{segment}-{role.lower()}" + (f"-{side}" if side else "") + (f"-{lane}" if lane is not None else "")
                identifier = f"{spec.road_id}:{key}"
                if len(identifier) > 128: identifier = f"{spec.road_id[:40]}:{hashlib.sha256(identifier.encode()).hexdigest()[:32]}"
                raw = box(key, role.lower(), ((a.position[0] + b.position[0]) / 2 + normal[0] * offset,
                    (a.position[1] + b.position[1]) / 2 + normal[1] * offset, z), (length, width, thickness), heading)
                raw["semantic"] = {"id": identifier, "assetFamily": "ROAD", "componentKind": role, "componentRole": role,
                    "sourceComponentId": key, "roadId": spec.road_id, "segmentId": segment, "startPointId": a.id, "endPointId": b.id,
                    "chainageStartM": distances[index], "chainageEndM": distances[index + 1],
                    "chainageStart": display_chainage(distances[index]), "chainageEnd": display_chainage(distances[index + 1]),
                    "side": side, "laneNumber": lane, "adapterVersion": "1", "referencePlane": "LOCAL_VISUAL_REFERENCE", "elevationResolution": "UNKNOWN"}
                objects.append(raw)
            # Z=0 is a local visual plane, never a survey elevation.
            solid("ALIGNMENT", .05, 0, .01, .03)
            half = section.carriageway_width_m / 2; median = section.median_width_m
            if median:
                for side, sign in (("left", 1), ("right", -1)):
                    solid("CARRIAGEWAY", half, sign * (median / 2 + half / 2), section.surface_thickness_m, -section.surface_thickness_m / 2, side)
                solid("MEDIAN", median, 0, section.surface_thickness_m, -section.surface_thickness_m / 2)
            else: solid("CARRIAGEWAY", section.carriageway_width_m, 0, section.surface_thickness_m, -section.surface_thickness_m / 2)
            if section.lane_count:
                for lane in range(section.lane_count):
                    offset = -half + section.lane_width_m * (lane + .5)
                    if median: offset += (-1 if lane < section.lane_count / 2 else 1) * median / 2
                    solid("LANE", section.lane_width_m, offset, .01, .005, lane=lane + 1)
            for side, sign, shoulder, verge in (("left", 1, section.shoulder_left_m, section.verge_left_m), ("right", -1, section.shoulder_right_m, section.verge_right_m)):
                edge = half + median / 2
                solid("SHOULDER", shoulder, sign * (edge + shoulder / 2), section.surface_thickness_m, -section.surface_thickness_m / 2, side)
                solid("VERGE", verge, sign * (edge + shoulder + verge / 2), .02, -.01, side)
        return {"objects": objects, "frame": "local_meters", "validation": validation, "referencePlane": "LOCAL_VISUAL_REFERENCE"}
