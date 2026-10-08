"""Bounded projected/geodesic calculations, never angular metres."""
import math
from pyproj import Geod, Transformer
from shapely.geometry import Point, shape
from shapely.ops import transform
from app.services.site_profiles.evidence import WGS84, known, unknown

GEOD = Geod(ellps="WGS84")
ALGORITHM = "site-metrics/1"


class SiteDerivationService:
    def derive(self, selection, evidence):
        geom = shape(selection["canonicalGeometry"])
        xmin, ymin, xmax, ymax = geom.bounds
        if xmax - xmin > 2 or ymax - ymin > 2 or ymin < -80 or ymax > 84 or GEOD.inv(xmin,ymin,xmax,ymax)[2] > 100000:
            raise ValueError("UNSUPPORTED_EXTENT")
        center = geom.centroid
        epsg = (32600 if center.y >= 0 else 32700) + min(60, int((center.x+180)//6)+1)
        crs = {"status":"RESOLVED", "definition":f"EPSG:{epsg}", "axisOrder":"XY", "unit":"METRE", "transformId":"pyproj-always-xy/1"}
        forward = Transformer.from_crs("EPSG:4326",epsg,always_xy=True)
        reverse = Transformer.from_crs(epsg,"EPSG:4326",always_xy=True)
        local = transform(forward.transform,geom)
        kind = selection["selection"]["kind"]
        values = {}
        bearing = None
        method = "UNDEFINED"
        if kind == "AREA":
            area, perimeter = GEOD.geometry_area_perimeter(geom)
            # Orient rings so holes subtract even for a clockwise user-drawn boundary.
            from shapely.geometry.polygon import orient
            polygons = list(geom.geoms) if geom.geom_type == "MultiPolygon" else [geom]
            area = sum(abs(GEOD.geometry_area_perimeter(orient(p, sign=1))[0]) for p in polygons)
            perimeter = sum(GEOD.line_length(*zip(*ring.coords)) for p in polygons for ring in [p.exterior,*p.interiors])
            values.update(area=(area,"m2"), perimeter=(perimeter,"m"))
            rect = list(local.minimum_rotated_rectangle.exterior.coords)
            edges = [(math.dist(rect[i], rect[i+1]), rect[i], rect[i+1]) for i in range(4)]
            width, a, b = max(edges)
            depth = min(e[0] for e in edges)
            values.update(boundingWidth=(width,"m"),boundingDepth=(depth,"m"))
            if width / depth > 1.05:
                bearing = GEOD.inv(*reverse.transform(*a), *reverse.transform(*b))[0] % 180
                method = "PRINCIPAL_AXIS"
        elif kind == "ROUTE":
            values["routeLength"] = (GEOD.geometry_length(geom),"m")
        elif kind in {"CROSSING", "ENDPOINTS"}:
            a = selection["selection"]["endpointA"]["coordinates"]
            b = selection["selection"]["endpointB"]["coordinates"]
            azimuth, _, distance = GEOD.inv(*a,*b)
            values["crossingSpan" if kind == "CROSSING" else "endpointDistance"] = (distance,"m")
            bearing, method = azimuth % 360, "ENDPOINT_BEARING"
        eid = evidence.derived([selection["transformationEvidenceId"]], {"values":values,"azimuth":bearing}, ALGORITHM, {"calculationCrs":crs})
        dimensions = {}
        for name in ("area","perimeter","routeLength","crossingSpan","boundingWidth","boundingDepth","endpointDistance"):
            dimensions[name] = ({"applicability":"APPLICABLE", "fact":known(name,{"value":values[name][0],"unit":values[name][1]},[eid])}
                if name in values else {"applicability":"NOT_APPLICABLE","reason":f"Not a {kind} measurement"})
        orientation = {"method":method, "azimuth":known("azimuth",{"value":bearing,"unit":"deg"},[eid]) if bearing is not None else unknown("azimuth","UNAVAILABLE")}
        samples = []
        if kind in {"ROUTE", "CROSSING"}:
            for i in range(25):
                p = local.interpolate(i/24, normalized=True)
                lng, lat = reverse.transform(p.x,p.y)
                samples.append({"position":{"longitude":lng,"latitude":lat}, "chainageM":local.length*i/24})
        elif kind == "AREA":
            x1,y1,x2,y2 = local.bounds
            points = [local.representative_point()]
            for i in range(5):
                for j in range(5):
                    p = Point(x1+(x2-x1)*i/4,y1+(y2-y1)*j/4)
                    if local.covers(p):
                        points.append(p)
            for p in points:
                lng,lat = reverse.transform(p.x,p.y)
                samples.append({"position":{"longitude":lng,"latitude":lat},"chainageM":None})
        else:
            points = list(geom.geoms) if kind == "ENDPOINTS" else [geom]
            samples = [{"position":{"longitude":p.x,"latitude":p.y},"chainageM":None} for p in points]
        return {"dimensions":dimensions,"orientation":orientation,"calculationCrs":crs,"samples":samples,
                "location":known("location",{"longitude":center.x,"latitude":center.y},[eid]), "evidenceId":eid}

    def coverage(self, db, geometry, coverage, crs):
        if not coverage:
            return "UNKNOWN", None
        g, c = shape(geometry), shape(coverage)
        if db.get_bind().dialect.name == "postgresql":
            import sqlalchemy as sa
            import json
            full = db.execute(sa.text("SELECT ST_Covers(ST_SetSRID(ST_GeomFromGeoJSON(:c),4326), ST_SetSRID(ST_GeomFromGeoJSON(:g),4326))"),
                              {"c":json.dumps(coverage),"g":json.dumps(geometry)}).scalar()
        else:
            full = c.covers(g)
        if full:
            return "FULL",1.0
        projection = Transformer.from_crs("EPSG:4326",crs["definition"],always_xy=True)
        g,c = transform(projection.transform,g),transform(projection.transform,c)
        if not g.intersects(c):
            return "NONE",0.0
        intersection = g.intersection(c)
        if g.area:
            fraction = intersection.area/g.area
        elif g.length:
            fraction = intersection.length/g.length
        elif g.geom_type == "MultiPoint":
            fraction = sum(c.covers(p) for p in g.geoms)/len(g.geoms)
        else:
            fraction = 1.0
        return "PARTIAL",max(0.0,min(1.0,fraction))

    def relief(self, samples, evidence, kind):
        valid = [s for s in samples if s["elevation"]["sourceKind"] != "UNKNOWN"]
        values = [s["elevation"]["value"]["value"] for s in valid]
        inputs = list(dict.fromkeys(e for s in samples for e in s["elevation"]["evidenceIds"]))
        slopes = []
        if kind in {"ROUTE","CROSSING"}:
            for a,b in zip(samples,samples[1:]):
                if a in valid and b in valid and a["verticalReference"] == b["verticalReference"]:
                    distance = b["chainageM"]-a["chainageM"]
                    if distance > 0:
                        slopes.append(100*abs(b["elevation"]["value"]["value"]-a["elevation"]["value"]["value"])/distance)
        eid = evidence.derived(inputs, {"min":min(values,default=None),"max":max(values,default=None),"slopes":slopes}, "adjacent-valid-samples/1") if inputs else None
        quantity = lambda name,value,unit: known(name,{"value":value,"unit":unit},[eid]) if value is not None else unknown(name,"UNAVAILABLE",inputs)
        return {"minElevation":quantity("minElevation",min(values,default=None),"m"),
                "maxElevation":quantity("maxElevation",max(values,default=None),"m"),
                "meanSlope":quantity("meanSlope",sum(slopes)/len(slopes) if slopes else None,"percent"),
                "maxSlope":quantity("maxSlope",max(slopes,default=None),"percent"),
                "slopeMethodVersion":"adjacent-valid-samples/1" if slopes else None,"profileIds":[]}
