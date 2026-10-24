"""Geometric validation of the local parametric platform attachments.

No load, soil, connection strength, stair safety or code analysis is performed.
"""
import math
import re


PARAMETERS = {
    "foundation": {"width", "depth", "thickness"},
    "base_plate": {"width", "depth", "thickness"},
    "brace": {"radius"},
    "stairs": {"width", "going", "maxRiser", "treadThickness", "stringerRadius"},
    "connection": {"width", "depth", "thickness"},
}
PREFIX = "industrial-platform-5x3:"


def validate_platform_attachments(document):
    value = (document.get("generator_parameters") or {}).get("platform_attachments")
    components = document.get("components") or []
    managed = [c for c in components if (c.get("metadata") or {}).get("parametric_attachment")]
    if value is None and not managed:
        return []
    try:
        _validate(value, components, managed)
        return []
    except (ValueError, TypeError, KeyError, IndexError, ZeroDivisionError, OverflowError) as exc:
        return [f"Parametric attachment geometry: {exc}"]


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _finite(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def _equal(a, b):
    if _finite(a) and _finite(b):
        return abs(a - b) < 1e-6
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(_equal(x, y) for x, y in zip(a, b))
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(_equal(a[k], b[k]) for k in a)
    return a == b


def _size(c):
    g = c.get("geometry") or {}
    s = g.get("size")
    _require(g.get("kind") == "box" and isinstance(s, list) and len(s) == 3 and all(_finite(v) and v > 0 for v in s), "reference must be a positive finite box")
    return s


def _validate(value, components, managed):
    _require(isinstance(value, dict) and value.get("version") == 1 and isinstance(value.get("items"), list), "unsupported parameter records")
    items = value["items"]
    _require(len(items) <= 64, "at most 64 attached assemblies are supported")
    all_ids = [c.get("id") for c in components]
    _require(len(all_ids) == len(set(all_ids)), "duplicate component identities")
    by_id = {c["id"]: c for c in components}
    if not items and not managed:
        return
    deck = by_id.get(PREFIX + "platform-deck")
    _require(deck is not None, "deck reference is missing")
    for name in ["platform-deck", "beam-north", "beam-south", "beam-east", "beam-west", "column-ne", "column-nw", "column-se", "column-sw"]:
        _require(PREFIX + name in by_id, "attached assemblies require the complete nine-member platform")
        _size(by_id[PREFIX + name])
    ds = _size(deck)
    heading = deck["transform"]["rotation_deg"][2]
    _require(_finite(heading), "invalid reference rotation")
    rad = math.radians(heading)

    def local(c):
        t = c["transform"]
        _require(_equal(t["rotation_deg"], [0, 0, heading]) and _equal(t["scale"], [1, 1, 1]) and len(t["position"]) == 3 and all(_finite(v) for v in t["position"]), "references must have common horizontal rotation and unit scale")
        x, y = t["position"][0] - deck["transform"]["position"][0], t["position"][1] - deck["transform"]["position"][1]
        return [x * math.cos(rad) + y * math.sin(rad), -x * math.sin(rad) + y * math.cos(rad), t["position"][2]]

    def world(p):
        x, y, z = p
        return [deck["transform"]["position"][0] + x * math.cos(rad) - y * math.sin(rad), deck["transform"]["position"][1] + x * math.sin(rad) + y * math.cos(rad), z]

    local(deck)
    ids, slots, expected = set(), set(), {}
    for a in items:
        _require(isinstance(a, dict) and isinstance(a.get("id"), str) and re.fullmatch(r"[a-zA-Z0-9_-]{1,80}", a["id"]) and a["id"] not in ids and a.get("kind") in PARAMETERS, "invalid attachment identity or type")
        ids.add(a["id"])
        p, kind, refs = a.get("parameters"), a["kind"], a.get("refs")
        _require(isinstance(p, dict) and p.keys() == PARAMETERS[kind] and all(_finite(v) and 0 < v <= 500 for v in p.values()), "parameters must be finite positive dimensions within the 500 m editor limit")
        count = 2 if kind in {"brace", "connection"} else 1
        _require(isinstance(refs, list) and len(refs) == count and all(isinstance(v, str) for v in refs) and len(set(refs)) == count, "distinct component references are required")
        _require(all(v in by_id and v.startswith(PREFIX) and not (by_id[v].get("metadata") or {}).get("parametric_attachment") for v in refs), "unknown or unsupported reference")
        slot = (kind, *refs)
        _require(slot not in slots, "duplicate assembly references")
        slots.add(slot)
        first = by_id[refs[0]]
        cs, at = _size(first), local(first)
        base, top = at[2] - cs[2] / 2, at[2] + cs[2] / 2
        _require(first["id"] == deck["id"] if kind == "stairs" else first.get("category") == "column", "wrong reference category")

        def add(part, category, geometry, pos):
            cid = f"platform-addon:{a['id']}:{part}"
            expected[cid] = {"geometry": geometry, "transform": {"position": world(pos), "rotation_deg": [0, 0, heading], "scale": [1, 1, 1]}, "parent_id": first["id"], "category": category, "refs": refs, "attachment": a["id"], "kind": kind}

        def box(part, category, size, pos):
            add(part, category, {"kind": "box", "size": size}, pos)

        if kind in {"foundation", "base_plate"}:
            _require(p["width"] >= cs[0] and p["depth"] >= cs[1], "support footprint must cover column")
            plate = next((v for v in items if v.get("kind") == "base_plate" and v.get("refs", []) == [first["id"]]), None)
            offset = 0
            if kind == "foundation" and plate:
                pp = plate["parameters"]
                _require(p["width"] >= pp["width"] and p["depth"] >= pp["depth"], "foundation footprint must cover base plate")
                offset = pp["thickness"]
            box("body", kind, [p["width"], p["depth"], p["thickness"]], [at[0], at[1], base - offset - p["thickness"] / 2])
        elif kind == "brace":
            second = by_id[refs[1]]
            _require(second.get("category") == "column", "brace end must reference a column")
            end, es = local(second), _size(second)
            end[2] += es[2] / 2
            _require(p["radius"] <= min(cs[0], cs[1], es[0], es[1]) / 2, "brace radius does not fit column")
            _require(math.hypot(end[0] - at[0], end[1] - at[1]) > 1e-6 and end[2] > base, "brace must be a rising diagonal")
            add("diagonal", "bracing", {"kind": "cylinder", "start": [at[0], at[1], base], "end": end, "radius_m": p["radius"]}, [0, 0, 0])
        elif kind == "connection":
            beam = by_id[refs[1]]
            _require(beam.get("category") == "beam", "joint must reference a beam")
            bp, bs = local(beam), _size(beam)
            _require(_equal(top, bp[2] - bs[2] / 2) and abs(at[0] - bp[0]) <= bs[0] / 2 and abs(at[1] - bp[1]) <= bs[1] / 2, "beam must touch the referenced column top")
            box("joint", "connection", [p["width"], p["depth"], p["thickness"]], [at[0], at[1], top])
        else:
            columns = [c for c in components if c["id"].startswith(PREFIX + "column-")]
            _require(len(columns) == 4, "stairs require four platform columns")
            bases = [local(c)[2] - _size(c)[2] / 2 for c in columns]
            ground = bases[0]
            _require(all(_equal(v, ground) for v in bases), "stairs require a common base plane")
            rise = deck["transform"]["position"][2] + ds[2] / 2 - ground
            n = math.ceil(rise / p["maxRiser"])
            _require(rise > 0 and 2 <= n <= 200, "stairs need 2–200 positive risers")
            riser = rise / n
            _require(p["width"] <= ds[0] and p["treadThickness"] < riser and p["stringerRadius"] < min(p["width"] / 4, riser / 2), "stair dimensions do not fit deck/riser geometry")
            for i in range(1, n + 1):
                box(f"tread-{i}", "stairs", [p["width"], p["going"], p["treadThickness"]], [0, -ds[1] / 2 - (n - i + .5) * p["going"], ground + i * riser - p["treadThickness"] / 2])
            for sign in [-1, 1]:
                x = sign * (p["width"] / 2 - 2 * p["stringerRadius"])
                z1 = ground + rise - p["treadThickness"]
                y1 = -ds[1] / 2 - p["going"] / 2
                y0 = y1 - (z1 - ground) / (riser / p["going"])
                add(f"stringer-{sign}", "stairs", {"kind": "cylinder", "start": [x, y0, ground], "end": [x, y1, z1], "radius_m": p["stringerRadius"]}, [0, 0, 0])
    _require(len(managed) == len(expected), "missing or extra generated members")
    _require(all((c.get("metadata") or {}).get("parametric_attachment") in ids for c in managed), "orphan generated member")
    for cid, spec in expected.items():
        c = by_id.get(cid)
        _require(c is not None, "generated member is missing")
        meta = c.get("metadata") or {}
        _require(all(_equal(c.get(k), spec[k]) for k in ["geometry", "transform", "parent_id", "category"]) and meta.get("parametric_attachment") == spec["attachment"] and meta.get("attachment_kind") == spec["kind"] and meta.get("engineering_status") == "conceptual_unverified" and _equal(meta.get("references"), spec["refs"]) and (c.get("quantity") or {}).get("included") is False, "generated member geometry, references or conceptual scope differ from parameters")
