"""Explicit experimental provider injection; does not change production routing.

Caller must supply a budgeted, durable at-most-once provider. This adapter alone
is not authority to dispatch and is not registered in application routes.
"""
from dataclasses import replace

MODEL='nvidia/nemotron-3-super-120b-a12b'


class PlatformDemoProvider:
    def __init__(self, guarded_provider):
        self.guarded_provider=guarded_provider

    @property
    def metadata_sink(self):
        return getattr(self.guarded_provider,'metadata_sink',[])

    async def complete(self,system,payload,route):
        if route.tier!='PRIMARY' or route.tool_calling_allowed or route.max_output_tokens!=3500 or route.timeout!=45:
            raise ValueError('DEMO_ROUTE_LIMIT_MISMATCH')
        if payload.get('stage') not in {'UNDERSTAND','PLAN','EXPAND','RELATE'}:
            raise ValueError('DEMO_STAGE_INVALID')
        return await self.guarded_provider.complete(system,payload,replace(route,model=MODEL))
