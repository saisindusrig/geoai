"""Offline replay of saved validated turns; this module never calls a provider."""
import argparse
import hashlib
import json
from copy import deepcopy
from pathlib import Path
from .contracts import Case, EvaluationResponse
from .fixtures import FixtureTools
from .scoring import score
from .reporting import redact


def rescore_record(case, original):
    row = deepcopy(original)
    row["original_scoring"] = deepcopy(original["scoring"])
    row["prior_score_audits"] = deepcopy(original.get("prior_score_audits", []))
    if "original_scoring" in original:
        row["prior_score_audits"].append(deepcopy(original["original_scoring"]))
    row["rescore_paid_requests"] = 0
    if not original.get("structured_output_valid") or not original.get("response"):
        if not original.get('attempt_metadata'):
            row["legacy_failure_diagnostics"] = {"classification":"UNKNOWN", "finish_reason":None,
            "reason":"No raw structured response or per-attempt finish metadata was retained. Aggregate 7000 tokens alone cannot establish the cause."}
        row["score_delta"] = 0
        row["rescore_reasons"] = ["Invalid output remains invalid; no valid structured response to rescore."]
        return row
    tools = FixtureTools(case)
    saved_results = iter(original.get("tool_results", []))
    turn_scores = []
    turns = original.get("visible_turns") or [original["response"]]
    for raw in turns:
        result = EvaluationResponse.model_validate(raw)
        turn_score = score(case, result, tools)
        turn_scores.append(turn_score)
        tools.semantic_failures.extend(turn_score["hard_failures"])
        tools.effect_mismatches=turn_score['effect_mismatches']
        for call in result.response.tool_calls:
            saved = next(saved_results)
            if saved["name"] != call.name or saved["arguments"] != call.arguments:
                raise ValueError("Saved tool sequence does not match visible turns")
            # Validate arguments deterministically, then use the actual saved result.
            tools.execute(call.name, call.arguments)
            if saved["result"].get("status") == "OK":
                tools.results[-1] = {"name":call.name,"result":deepcopy(saved["result"])}
            else:
                tools.failures.append(saved["result"].get("errorCode") or "TOOL_ERROR")
    if next(saved_results, None) is not None:
        raise ValueError("Unmatched saved tool result")
    # Preserve failures not reproducible from validated visible turns, e.g. a
    # forbidden tool in an invalid repair attempt. Only the grounding bug is removed.
    tools.semantic_failures.extend(code for code in original["scoring"]["hard_failures"] if code not in {"INVENTED_SITE_VALUE","FORBIDDEN_MUTATION"})
    if 'UNSUPPORTED_TOOL' in original['scoring']['hard_failures'] and 'FORBIDDEN_MUTATION' in original['scoring']['hard_failures']:
        tools.semantic_failures.append('FORBIDDEN_MUTATION')
    row["scoring"] = score(case, EvaluationResponse.model_validate(original["response"]), tools)
    row["turn_scoring"] = turn_scores
    row["score_delta"] = row["scoring"]["score"] - original["scoring"]["score"]
    row["category_deltas"] = {key: value - original["scoring"]["categories"][key] for key,value in row["scoring"]["categories"].items()}
    row["rescore_reasons"] = [
        "Grounded runtime facts now match context, returned tool fields and narrow explicit-request derivations (see turn_scoring.grounding). Effect mismatches are separated from actual mutation evidence.",
        "Semantic failures no longer incorrectly zero valid tool-argument points.",
        "Proposal relationship scoring is unchanged: canonical expected relationships still must match.",
        "Unsupported proposed design assumptions warn and deduct one proposal-quality point each, limited by available proposal-quality points."]
    return row


def rescore_directory(source, destination):
    source, destination = Path(source), Path(destination)
    # Verify against the smoke's frozen case context; do not silently use changed cases.
    manifest = json.loads((source / "run_manifest.json").read_text(encoding="utf-8"))
    cases = {case.id:case for case in (Case.model_validate(raw) for raw in manifest["cases"])}
    destination.mkdir(parents=True, exist_ok=False)
    audit = {"mode":"OFFLINE_RESCORE", "new_provider_requests":0, "original_file_hashes":{}, "results":[]}
    for alias in manifest["model_aliases"]:
        path = source / (alias + ".json")
        before = path.read_bytes()
        digest = hashlib.sha256(before).hexdigest()
        rows = [rescore_record(cases[row["case_id"]],row) for row in json.loads(before)]
        target = destination / path.name
        target.write_text(json.dumps(redact(rows),indent=2),encoding="utf-8")
        assert json.loads(target.read_text(encoding="utf-8"))
        assert hashlib.sha256(path.read_bytes()).hexdigest() == digest
        audit["original_file_hashes"][str(path.resolve())] = digest
        for row in rows:
            audit["results"].append({"model":alias,"original_score":row["original_scoring"]["score"],
                "corrected_score":row["scoring"]["score"],"delta":row["score_delta"],
                "original_hard_failures":row["original_scoring"]["hard_failures"],
                "corrected_hard_failures":row["scoring"]["hard_failures"],
                "warnings":row["scoring"].get("warnings",[]),"saved_path":str(target.resolve()),
                "legacy_failure_diagnostics":row.get("legacy_failure_diagnostics")})
    (destination / "audit.json").write_text(json.dumps(redact(audit),indent=2),encoding="utf-8")
    return audit


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source",type=Path)
    parser.add_argument("destination",type=Path)
    args = parser.parse_args()
    print(json.dumps(rescore_directory(args.source,args.destination),indent=2))
