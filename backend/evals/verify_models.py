"""Read-only, non-completion model discovery. Never guesses candidate mappings."""
import asyncio
import json
from app.services.ai.nebius import available_assistant_models
from app.services.ai.provider import AssistantProviderError
from .run_geoai import load


async def verify(env_file=None):
    if env_file:
        from app.services.ai.nebius_config import use_env_file
        use_env_file(env_file)
    config,_=load()
    try:
        ids=await available_assistant_models()
    except AssistantProviderError as exc:
        return {"status":exc.code,"httpStatus":exc.diagnostics.get("httpStatus"),"paid_requests":0}
    return {"status":"CATALOGUE_AVAILABLE","available_ids":[i for i in ids if any(s in i.lower() for s in ('qwen','glm','nemotron','kimi'))],"paid_requests":0,
        "candidates":[{"key":c.key,"configured_id":c.model_id,"available":c.model_id in ids} for c in config.candidates],
        "note":"Set exact matching model_id and verified=true in geoai_models.json after review. No automatic mapping or production change."}


if __name__=="__main__":
    import argparse
    from pathlib import Path
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--env-file',type=Path)
    print(json.dumps(asyncio.run(verify(parser.parse_args().env_file)),indent=2))
