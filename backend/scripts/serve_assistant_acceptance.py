"""Manually activated acceptance server. Never invokes a model on startup.

Do not run with approval flags until the human has approved a spending cap.
The ordinary review launcher remains disabled. No environment file is edited.
"""
import argparse,asyncio,math,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--human-approved-spending',action='store_true')
    parser.add_argument('--budget-usd',type=float)
    parser.add_argument('--daily-tokens',type=int,default=200000)
    args=parser.parse_args()
    if not args.human_approved_spending or args.budget_usd is None or not math.isfinite(args.budget_usd) or not 0<args.budget_usd<=.10:
        parser.error('Explicit human approval and a positive cap at or below USD 0.10 are required. No inference enabled.')
    if not 10000<=args.daily_tokens<=200000:
        parser.error('Controlled acceptance daily token allowance must be between 10,000 and 200,000.')
    from app.core.config import settings
    from app.services.ai.nebius_config import resolve
    config=resolve(model='zai-org/GLM-5.3-Flash')
    if not config.api_key or config.base_url!='https://api.tokenfactory.nebius.com/v1':
        parser.error('Configure backend credentials and official Nebius endpoint first. No inference enabled.')
    # This acceptance approval is Flash-only, regardless of the browser selection.
    # request_body rejects any model absent from this process-local allowlist.
    from app.services.assistant import site_provider
    site_provider.MODELS = {'zai-org/GLM-5.3-Flash': site_provider.MODELS['zai-org/GLM-5.3-Flash']}
    # Disable all legacy inference routes; the new assistant uses its own ledger.
    settings.NEBIUS_ENFORCE_AGENT_BUDGET=True
    settings.AI_PROVIDER='nebius'  # Legacy helpers fail on their budget gate, with no provider chain.
    settings.GEOAI_OFFLINE_PLATFORM_DEMO=False
    settings.ENGINEERING_AI_BUDGET_APPROVED=False
    settings.ENGINEERING_AI_BUDGET_USD=0
    settings.ENGINEERING_AI_MODE='disabled'
    settings.ASSISTANT_INFERENCE_APPROVED=True
    settings.ASSISTANT_BUDGET_USD=args.budget_usd
    settings.ASSISTANT_DAILY_REQUESTS=3
    settings.ASSISTANT_DAILY_TOKENS=args.daily_tokens
    settings.CORS_ALLOWED_ORIGINS=','.join(filter(None,[settings.CORS_ALLOWED_ORIGINS,'http://localhost:3001','http://127.0.0.1:3001']))
    settings.S3_ACCESS_KEY=''
    settings.S3_SECRET_KEY=''
    for name in ('OPENAI_API_KEY','ANTHROPIC_API_KEY','GEMINI_API_KEY','SENTRY_DSN'):
        setattr(settings,name,'')
    import uvicorn
    server=uvicorn.Server(uvicorn.Config('app.main:app',host='127.0.0.1',port=8001,proxy_headers=False))
    print('Controlled acceptance: loopback only, three accepted turns/user/24h, shared budget cap, no startup inference, no retries. Charges remain unknown.')
    asyncio.run(server.serve(),loop_factory=asyncio.SelectorEventLoop if sys.platform=='win32' else None)


if __name__=='__main__':main()
