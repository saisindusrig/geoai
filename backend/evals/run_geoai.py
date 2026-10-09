"""python -m evals.run_geoai --dry-run --all (offline, zero paid calls)."""
import argparse
import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path
from app.services.ai.provider import NebiusProvider
from .contracts import Case, ModelConfig
from .fixtures import FixtureTools
from .runner import evaluate_case
from .reporting import write_reports

ROOT=Path(__file__).parent


def load(config_path=ROOT/"geoai_models.json", cases_path=ROOT/"geoai_cases.json"):
    config=ModelConfig.model_validate(json.loads(Path(config_path).read_text(encoding="utf-8")))
    cases=[Case.model_validate(c) for c in json.loads(Path(cases_path).read_text(encoding="utf-8"))]
    if len({c.id for c in cases})!=len(cases):
        raise ValueError("Duplicate case IDs")
    from app.services.assistant.tool_contracts import SCHEMAS
    for case in cases:
        if any(name not in SCHEMAS for name in case.fixtures):
            raise ValueError("Unknown fixture tool")
        if not set(case.expected.required_tools).issubset(case.expected.allowed_tools) or not set(case.expected.allowed_tools).issubset(case.fixtures):
            raise ValueError("Expected tools must be available")
        for result in case.fixtures.values():
            if not {"status","data","errorCode","limitations","evidenceIds","dependencyRefs"}.issubset(result):
                raise ValueError("Fixture must use production tool envelope")
    return config,cases


async def run(args, provider_factory=None):
    config,cases=load(args.config,args.dataset)
    if getattr(args, 'env_file', None):
        from app.services.ai.nebius_config import use_env_file
        use_env_file(args.env_file)
    if args.all and (args.model or args.models) or args.model and args.models:
        raise ValueError("Use one model selector: --model, --models, or --all")
    keys=(args.models or args.model or "").split(",")
    candidates=config.candidates if args.all else [c for c in config.candidates if c.key in keys]
    if not candidates:
        raise ValueError("Select --model, --models, or --all")
    if not args.all and set(keys)-{c.key for c in config.candidates}:
        raise ValueError("Unknown candidate key")
    cases=[c for c in cases if (not args.case or c.id==args.case) and (not args.category or c.category==args.category)]
    if getattr(args,'pilot',False):
        if args.case or args.category:
            raise ValueError("--pilot cannot be combined with --case or --category")
        pilot=json.loads((ROOT/'geoai_pilot.json').read_text())
        case_ids=pilot['case_ids']
        if len(case_ids)!=5 or len(set(case_ids))!=5:
            raise ValueError("Pilot must contain exactly five distinct cases")
        by_id={c.id:c for c in cases}
        if any(key not in by_id for key in case_ids):raise ValueError("Pilot case missing from dataset")
        cases=[by_id[key] for key in case_ids]
    if not cases:
        raise ValueError("No matching cases")
    if args.dry_run:
        return {"mode":"DRY_RUN","cases":len(cases),"categories":sorted({c.category for c in cases}),
            "models":[c.model_dump() for c in candidates],"paid_requests":0,
            "request_upper_bound":len(cases)*len(candidates)*config.max_rounds*(config.repairs+1)}
    if any(not c.model_id or not c.verified or c.availability == "UNAVAILABLE" for c in candidates):
        raise ValueError("Unresolved/unverified model IDs: verify the provider catalogue first")
    from .reporting import redact
    import os
    output=Path(args.output) if args.output else ROOT/"results"/datetime.now(timezone.utc).strftime("run_%Y%m%d_%H%M%S_%f")
    # Fail before any paid request if this destination already exists.
    output.mkdir(parents=True,exist_ok=False)
    def save_json(path,value):
        temporary=path.with_suffix(path.suffix+'.tmp')
        with temporary.open('w',encoding='utf-8') as handle:
            json.dump(redact(value),handle,indent=2);handle.flush();os.fsync(handle.fileno())
        temporary.replace(path)
    save_json(output/'run_state.json',{'status':'RUNNING','model_aliases':[c.key for c in candidates],
        'case_ids':[c.id for c in cases],'configuration':config.model_dump(),'completed_evaluations':0})
    save_json(output/'run_manifest.json',{'configuration':config.model_dump(),
        'cases':[c.model_dump() for c in cases],'model_aliases':[c.key for c in candidates]})
    completed=0
    results={}
    for candidate in candidates:
        records=[]
        for case in cases:
            usage={}
            provider=provider_factory(candidate) if provider_factory else NebiusProvider(usage_sink=usage)
            def event(entry):
                entry={**entry,'model_alias':candidate.key,'case_id':case.id,'time':datetime.now(timezone.utc).isoformat()}
                with (output/'request_ledger.jsonl').open('a',encoding='utf-8') as handle:
                    handle.write(json.dumps(entry)+'\n');handle.flush();os.fsync(handle.fileno())
            row=await evaluate_case(case,candidate,config,provider,on_event=event)
            # Transport accumulates usage per request, including repair/tool rounds.
            row["input_tokens"]=usage.get("prompt_tokens")
            row["output_tokens"]=usage.get("completion_tokens")
            if candidate.input_per_million is not None and candidate.output_per_million is not None and all(row[k] is not None for k in ("input_tokens","output_tokens")):
                row["estimated_cost"]=(row["input_tokens"]*candidate.input_per_million+row["output_tokens"]*candidate.output_per_million)/1_000_000
            records.append(row)
            checkpoint=output/'checkpoints'/candidate.key
            checkpoint.mkdir(parents=True,exist_ok=True)
            save_json(checkpoint/(case.id+'.json'),row)
            completed+=1
            save_json(output/'run_state.json',{'status':'RUNNING','completed_evaluations':completed,
                'total_evaluations':len(cases)*len(candidates),'last_model':candidate.key,'last_case':case.id})
            print(f"Completed {completed}/{len(cases)*len(candidates)}: {candidate.key}/{case.id}; requests={row['requests']}",flush=True)
        results[candidate.key]=records
    summary=write_reports(output,config,cases,results,existing_run=True)
    save_json(output/'run_state.json',{'status':'COMPLETE','completed_evaluations':completed,
        'total_evaluations':completed,'completion_requests':sum(r['requests'] for rows in results.values() for r in rows)})
    return summary


def parser():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--model");p.add_argument("--models");p.add_argument("--case");p.add_argument("--category")
    p.add_argument("--all",action="store_true");p.add_argument("--dry-run",action="store_true")
    p.add_argument("--output");p.add_argument("--config",type=Path,default=ROOT/"geoai_models.json")
    p.add_argument("--env-file",type=Path,help="Explicit backend env-file override for inherited stale process settings")
    p.add_argument("--pilot",action="store_true",help="Select the documented five-case pilot; execution still requires an explicit invocation")
    p.add_argument("--dataset",type=Path,default=ROOT/"geoai_cases.json")
    return p


def main():
    args=parser().parse_args()
    try:
        print(json.dumps(asyncio.run(run(args)),indent=2))
    except (ValueError,OSError) as exc:
        from .reporting import redact
        parser().exit(2,redact(str(exc))+"\n")


if __name__=="__main__":
    main()
