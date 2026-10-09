"""One bounded, content-free structured connectivity check. Never prints credentials."""
import asyncio
import json
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.services.ai.nebius import assistant_json, assistant_diagnostics, AssistantProviderError


async def main(env_file=None):
    if env_file:
        from app.services.ai.nebius_config import use_env_file
        use_env_file(env_file)
    try:
        result=await assistant_json('Return exactly the JSON object {"ok":true}. This is a connectivity test.',{"connectivityCheck":True})
        print(json.dumps({"status":"STRUCTURED_CONNECTIVITY_OK" if result=={"ok":True} else "INVALID_RESPONSE","diagnostics":assistant_diagnostics()},sort_keys=True))
    except AssistantProviderError as exc:
        print(json.dumps({"status":exc.code,"diagnostics":exc.diagnostics},sort_keys=True))


if __name__=="__main__":
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--env-file',type=Path)
    asyncio.run(main(parser.parse_args().env_file))
