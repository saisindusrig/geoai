"""One deterministic conceptual composition, using the existing AI3D contract."""


def platform_design(selection, source_revision=None, center=(0, 0)):
    x, y = center

    def box(name, role, position, size):
        return {"objectId": name, "systemId": "platform", "semanticType": role,
                "role": role, "parameters": {"primitiveType": "BOX", "center": position, "size": size}}

    objects = [box("platform-deck", "SLAB", [x, y, 2.9], [5, 3, .2])]
    for side, dy in (("south", -1.35), ("north", 1.35)):
        objects.append(box(f"beam-{side}", "BEAM", [x, y + dy, 2.7], [5, .3, .2]))
    for side, dx in (("west", -2.35), ("east", 2.35)):
        objects.append(box(f"beam-{side}", "BEAM", [x + dx, y, 2.7], [.3, 2.4, .2]))
    for side, dx, dy in (("sw", -2.35, -1.35), ("se", 2.35, -1.35),
                         ("nw", -2.35, 1.35), ("ne", 2.35, 1.35)):
        objects.append(box(f"column-{side}", "COLUMN", [x + dx, y + dy, 1.3], [.3, .3, 2.6]))
    return {
        "designId": "industrial-platform-5x3", "sourceModelRevisionId": source_revision,
        "siteSelection": selection,
        "systems": [{"id": "platform", "assetType": "UNREGISTERED_CIVIL_ASSET",
                     "semanticType": "STRUCTURE", "role": "INDUSTRIAL_MAINTENANCE_PLATFORM"}],
        "objects": objects, "inputSource": "PREVIEW_ASSUMPTION",
        "constraints": [{"id": "platform-within-site", "kind": "WITHIN_AREA", "targetId": "platform"}],
        "assumptions": [
            {"field": "platform footprint", "value": "5 m length x 3 m width", "reason": "Requested conceptual dimensions."},
            {"field": "deck top local Z", "value": "approximately 3 m above the local visual reference plane",
             "reason": "Preview assumption, not surveyed ground or engineered absolute elevation."},
            {"field": "member sizes", "value": "0.2 m slab, 0.3 x 0.2 m beams, 0.3 x 0.3 m columns",
             "reason": "Visual placeholders only; no engineering sizing has been performed."}],
        "unknowns": ["groundElevation", "designLoads", "foundations", "clearances", "structuralAdequacy", "codeCompliance"],
    }
