"""Local offline review using the existing beam/frame configuration.

Selector loop avoids the observed Windows proactor accept failures in local
browser review. No persistent provider configuration or credentials are edited.
"""
import sys
import asyncio
import serve_beam_frame_local  # existing process-local offline/budget settings
from app.core.config import settings
settings.ASSISTANT_INFERENCE_APPROVED = False
settings.ASSISTANT_BUDGET_USD = 0

if __name__ == "__main__":
    import uvicorn
    server = uvicorn.Server(uvicorn.Config("app.main:app", host="127.0.0.1", port=8001, proxy_headers=False))
    # Uvicorn 0.36+ supplies its own Proactor factory on Windows, ignoring policy.
    asyncio.run(server.serve(), loop_factory=asyncio.SelectorEventLoop if sys.platform == "win32" else None)
