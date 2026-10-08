"""One bounded, content-free structured connectivity check. Never prints credentials."""
import asyncio
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.services.ai.nebius import assistant_configuration, assistant_json, AssistantProviderError


async def main():
    state=assistant_configuration()
    if state!="CONFIGURED":
        print(state)
        return
    try:
        result=await assistant_json('Return exactly the JSON object {"ok":true}. This is a connectivity test.',{"connectivityCheck":True})
        print("STRUCTURED_CONNECTIVITY_OK" if result=={"ok":True} else "INVALID_RESPONSE")
    except AssistantProviderError as exc:
        print(exc.code)


if __name__=="__main__":
    asyncio.run(main())
