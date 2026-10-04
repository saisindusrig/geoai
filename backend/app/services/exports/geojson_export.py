"""GeoJSON export of project geometry + analysis layers."""

import json


def build_geojson(project, analysis) -> bytes:
    features = []
    if project.boundary_geojson:
        features.append({"type": "Feature", "geometry": project.boundary_geojson,
                         "properties": {"layer": "project_boundary", "name": project.name}})
    if project.alignment_geojson:
        features.append({"type": "Feature", "geometry": project.alignment_geojson,
                         "properties": {"layer": "alignment", "name": project.name}})
    if analysis is not None and analysis.raw_geojson:
        features.extend(analysis.raw_geojson.get("features", []))
    return json.dumps({"type": "FeatureCollection", "features": features}, indent=2).encode()
