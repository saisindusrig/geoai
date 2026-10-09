import json
from collections import defaultdict
from statistics import mean
from app.services.ai.nebius import sanitized


def redact(value):
    """Redact known credentials plus common credential/header patterns, recursively."""
    import re
    from app.core.config import settings
    if isinstance(value,dict):
        return {k:("[REDACTED]" if any(t in k.lower() for t in ("api_key","authorization","secret","access_token")) else redact(v)) for k,v in value.items()}
    if isinstance(value,list):
        return [redact(v) for v in value]
    if isinstance(value,str):
        for key,secret in settings.model_dump().items():
            if any(t in key for t in ("KEY","TOKEN","SECRET","DATABASE_URL","REDIS_URL")) and isinstance(secret,str) and secret:
                value=value.replace(secret,"[REDACTED]")
        value=re.sub(r"(?i)bearer\s+\S+","Bearer [REDACTED]",value)
        value=re.sub(r"(?i)\b(?:api[_ -]?key|password|secret|access[_ -]?token)\s*[:=]\s*[^\s,;]+", "credential=[REDACTED]", value)
        value=re.sub(r"\b(?:sk-[A-Za-z0-9_-]{8,}|v1\.[A-Za-z0-9_.-]{20,})","[REDACTED]",value)
        return value
    return value


def summarize(results):
    summaries=[]
    for key,records in results.items():
        categories=defaultdict(list)
        for row in records:
            categories[row["category"]].append(row["scoring"]["score"])
        summaries.append({"model":key,"cases":len(records),"score":round(mean(r["scoring"]["score"] for r in records),2),
            "hard_failure_cases":sum(bool(r["scoring"]["hard_failures"]) for r in records),
            "provider_failures":sum(bool(r["provider_error"]) for r in records),
            "valid_structured_outputs":sum(r.get("structured_output_valid",r["response"] is not None) for r in records),
            "tool_errors":sum(sum(code in {"UNSUPPORTED_TOOL","MALFORMED_TOOL_ARGUMENTS","TOOL_LIMIT","AUTHORITY_VIOLATION"} for code in r["scoring"]["hard_failures"]) for r in records),
            "hard_failures":dict(__import__('collections').Counter(code for r in records for code in r['scoring']['hard_failures'])),
            "repair_requests":sum(r.get("repair_requests",0) for r in records),
            "latency_seconds":round(mean(r["latency_seconds"] for r in records),3),
            "requests":sum(r["requests"] for r in records),
            "input_tokens":sum(r["input_tokens"] for r in records) if all(r["input_tokens"] is not None for r in records) else None,
            "output_tokens":sum(r["output_tokens"] for r in records) if all(r["output_tokens"] is not None for r in records) else None,
            "estimated_cost":sum(r["estimated_cost"] for r in records) if all(r["estimated_cost"] is not None for r in records) else None,
            "categories":{c:round(mean(values),2) for c,values in categories.items()}})
    # Recommendation remains provisional, requires equal coverage and manual review.
    comparable = (len(results) >= 2 and
        len({tuple(sorted(r["case_id"] for r in rows)) for rows in results.values()}) == 1 and
        all(len(rows) >= 40 and len({r["category"] for r in rows}) == 10 for rows in results.values()))
    eligible=[s for s in summaries if not s["hard_failure_cases"] and not s["provider_failures"]] if comparable else []
    primary=max(eligible,key=lambda s:s["score"])["model"] if eligible else None
    fast_pool=[s for s in eligible if s["score"]>=80 and all(s["categories"].get(c,0)>=80 for c in ("SIMPLE_CONVERSATION","ASSET_UNDERSTANDING"))]
    fast=min(fast_pool,key=lambda s:(s["latency_seconds"],s["estimated_cost"] if s["estimated_cost"] is not None else float("inf")))["model"] if fast_pool else None
    return {"models":summaries,"primary_candidate":primary,"fast_candidate":fast,
        "recommendation_status":"PROVISIONAL_MANUAL_REVIEW_REQUIRED" if eligible else "INSUFFICIENT_SAFE_COMPARABLE_RESULTS",
        "production_configuration_changed":False}


def write_reports(output, config, cases, results, *, existing_run=False, system_instructions=None):
    output.mkdir(parents=True,exist_ok=existing_run)
    summary=summarize(results)
    summary["evaluation_configuration"]=config.model_dump()
    summary["case_ids"]=[c.id for c in cases]
    summary["sampling"]={"temperature":0.1,"seed":None,"note":"Existing Nebius transport; seed not assumed supported."}
    from .runner import SYSTEM
    import hashlib
    summary["system_instructions"]=SYSTEM if system_instructions is None else system_instructions
    summary["dataset_hash"]=hashlib.sha256(json.dumps([c.model_dump() for c in cases],sort_keys=True).encode()).hexdigest()
    (output/"summary.json").write_text(json.dumps(redact(summary),indent=2),encoding="utf-8")
    lines=["# GeoAI evaluation", "", "Visible responses only. Automatic scores are behavioral proxies; review prose, assumptions, and clarification usefulness before choosing a model.", ""]
    for item in summary["models"]:
        lines.append(f"- {item['model']}: score {item['score']}; hard-failure cases {item['hard_failure_cases']}; provider failures {item['provider_failures']}; mean latency {item['latency_seconds']}s; cost {item['estimated_cost']}.")
        lines.append("  Category scores: "+json.dumps(item["categories"],sort_keys=True))
    lines += ["",f"Primary candidate: {summary['primary_candidate']}",f"Fast candidate: {summary['fast_candidate']}",summary["recommendation_status"],""]
    for key,records in results.items():
        (output/f"{key}.json").write_text(json.dumps(redact(records),indent=2),encoding="utf-8")
        for row in records:
            lines += [f"## {key} / {row['case_id']}","", "User request: "+row["user_request"],"", "Expected behavior:","```json",json.dumps(row["expected"],indent=2),"```",
                "Model responses (visible turns):","```json",json.dumps(row["visible_turns"],indent=2),"```",
                "Tools used:","```json",json.dumps(row["tools_used"],indent=2),"```",
                "Tool results used:","```json",json.dumps(row.get("tool_results",[]),indent=2),"```",
                "Automatic score: "+str(row["scoring"]["score"]),"Hard failures: "+json.dumps(row["scoring"]["hard_failures"]),
                "Provider error: "+str(row["provider_error"]),"",
                "Reasoning usefulness (visible rationale only), 1–5: ___",
                "Clarification quality, 1–5: ___","Tool-use quality, 1–5: ___","Proposal usefulness, 1–5: ___","Capability honesty, 1–5: ___","Overall preference, 1–5: ___","Notes: ___",""]
    (output/"report.md").write_text(redact("\n".join(lines)),encoding="utf-8")
    return summary
