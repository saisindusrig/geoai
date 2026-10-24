// @vitest-environment jsdom
import {afterEach,expect,it,vi} from 'vitest';
afterEach(()=>{localStorage.clear();vi.unstubAllGlobals();vi.unstubAllEnvs();vi.resetModules();});
it('clears a rejected bearer and navigates only to the same-origin login with encoded project context',async()=>{
 vi.stubEnv('NEXT_PUBLIC_AUTH_REQUIRE_JWT','true');vi.resetModules();const assign=vi.fn();
 vi.stubGlobal('window',{location:{pathname:'/projects/793/workspace',origin:'http://localhost:3001',assign}});
 vi.stubGlobal('fetch',vi.fn().mockResolvedValue(new Response(JSON.stringify({detail:{message:'Authorization required'}}),{status:401})));
 const {api,setAuthToken,getAuthToken}=await import('./api');setAuthToken('synthetic-invalid-token');
 await expect(api.get('/api/projects/793')).rejects.toThrow('Authorization required');
 expect(getAuthToken()).toBeNull();expect(assign).toHaveBeenCalledWith('http://localhost:3001/login?next=%2Fprojects%2F793%2Fworkspace');
});
