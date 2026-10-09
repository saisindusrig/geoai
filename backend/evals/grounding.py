"""Semantic fact matching against frozen evidence, never model-authored arguments."""
import re


def canonical(key):
    key = re.sub(r"[^a-z0-9]", "", key.lower())
    return {"siteselectionid":"siteselection", "selectedsiteid":"siteselection",
            "savedsiteid":"siteselection", "proposalid":"proposalversionid",
            "proposalversion":"proposalversionid"}.get(key, key)


def equivalent(actual, known):
    # The evaluation contract permits strings/numbers, but not booleans.
    if isinstance(known, bool):
        return actual == int(known) or (isinstance(actual, str) and actual.lower() == str(known).lower())
    return actual == known


def evidence(case, tools):
    items = []
    def walk(value, path, source):
        if isinstance(value, dict):
            for key, child in value.items():
                walk(child, path + [key], source)
        elif isinstance(value, list):
            for index, child in enumerate(value):
                walk(child, path + [str(index)], source)
        else:
            key = path[-1]
            names = {canonical(key), canonical("_".join(path))}
            if path[-2:] == ["site", "selection"]:
                names.add("siteselection")
            if "capabilities" in path:
                names.add(canonical(key + "_capability"))
            if source.startswith("tool:") and source.split(":")[1] in {"create_proposal", "revise_proposal", "validate_proposal"}:
                if path == ["data", "status"]:
                    names.add("proposalstatus")
            if source == "tool:get_site_readiness" and path == ["data", "status"]:
                names.add("sitereadiness")
            items.append((names, value, source + ":" + ".".join(path)))
    walk(case.context, [], "context")
    # Explicit facts in deterministic fixtures are case evidence. Other result
    # fields become evidence only after that tool has actually returned.
    for name, fixture in case.fixtures.items():
        data = fixture.get("data")
        if isinstance(data, dict):
            walk(data.get("facts", {}), [], "fixture:" + name)
    for entry in getattr(tools, "results", []):
        if entry["result"].get("status") == "OK":
            walk(entry["result"], [], "tool:" + entry["name"])
            if entry['name']=='get_selected_objects':
                objects=entry['result'].get('data')
                if isinstance(objects,list) and all(isinstance(obj,dict) and isinstance(obj.get('objectId'),str) for obj in objects):
                    ids=[obj['objectId'] for obj in objects]
                    if len(ids)==len(set(ids)) and set(ids).issubset(case.context.get('selected_objects',[])):
                        items.append(({'selectedobjectcount'},len(ids),'derivation:get_selected_objects.unique_ids.count'))
                        items.append(({'selectedobjectids'},','.join(ids),'derivation:get_selected_objects.ordered_ids.join'))
    # Only an unambiguous explicit translation request, not arbitrary arithmetic.
    request=re.fullmatch(r'\s*move these\s+(\d+(?:\.\d+)?)\s*(mm|m)\s+(east|west|north|south)\s*[.!]?\s*',case.userMessage,re.I)
    axis=case.context.get('axis_convention')
    if request and axis=='LOCAL x east, y north, z up; metre units':
        distance=float(request[1]); metres=distance/1000 if request[2].lower()=='mm' else distance
        items.extend([({'translationdistancem'},metres,'derivation:explicit_move_request.metres'),
            ({'translationdistancemm'},metres*1000,'derivation:explicit_move_request.millimetres'),
            ({'translationdirection'},request[3].lower(),'derivation:explicit_move_request.direction'),
            ({'coordinatesystem'},'LOCAL','derivation:frozen.axis_convention.LOCAL')])
    # Expected multiplicities explicitly encode the case's user-request counts;
    # they authorize count arithmetic, never physical/engineering quantities.
    counts = case.expected.asset_counts
    if counts:
        items.append(({"assetcount"}, sum(counts.values()), "derivation:expected.asset_counts.sum"))
        for family, count in counts.items():
            items.append(({canonical(family + "_count")}, count, "derivation:expected.asset_counts." + family))
        match = re.search(r"\b(two|three|four|\d+) warehouses\b", case.userMessage.lower())
        if match:
            count = {"two":2, "three":3, "four":4}.get(match[1])
            count = count if count is not None else int(match[1])
            items.append(({"warehousecount"}, count, "derivation:user_requested_warehouse_count"))
    for key, value in case.context.get("allowed_derivations", {}).items():
        items.append(({canonical(key)}, value, "derivation:case." + key))
    return items


def grounded(key, value, items):
    return [source for names, known, source in items if canonical(key) in names and equivalent(value, known)]


RISKY = re.compile(r"standard\s+\w+\s+dimensions\s+apply|utility connections?\s+(?:are\s+)?available", re.I)
UNKNOWN = re.compile(r"not yet|unknown|to be (?:confirmed|determined)|not defined|remain.*confirm|if required", re.I)


def assumption_warnings(case, tools, text):
    warnings = []
    context_text = str(case.context).lower() + " " + case.userMessage.lower()
    for call in tools.calls:
        if call["name"] not in {"create_proposal", "revise_proposal"}:
            continue
        import json
        try:
            arguments = json.loads(call["arguments"])
        except (ValueError, TypeError):
            continue
        for assumption in arguments.get("assumptions", []):
            if isinstance(assumption, str) and RISKY.search(assumption) and not UNKNOWN.search(assumption) and assumption.lower() not in context_text:
                warnings.append({"code":"UNSUPPORTED_DESIGN_ASSUMPTION", "kind":"PROPOSED_ASSUMPTION",
                    "text":assumption, "recommendation":"Keep this unknown until confirmed by the user or evidence."})
    for match in RISKY.finditer(text):
        if not UNKNOWN.search(text) and match[0].lower() not in context_text:
            warnings.append({"code":"UNSUPPORTED_DESIGN_ASSUMPTION", "kind":"ASSERTED_FACT", "text":match[0],
                "recommendation":"This assertion needs evidence."})
    return warnings
