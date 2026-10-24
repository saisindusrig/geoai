// @vitest-environment jsdom
import {afterEach,expect,it,vi} from 'vitest';
import {apiUrl,fetchBinary,setAuthToken} from './api';
afterEach(()=>{localStorage.clear();vi.unstubAllGlobals();});
it('never sends bearer credentials to an external or script download destination',async()=>{
 const fetch=vi.fn();vi.stubGlobal('fetch',fetch);setAuthToken('synthetic-test-token');
 for(const path of ['https://outside.invalid/api/evidence','//outside.invalid/files/a','javascript:alert(1)','data:text/plain,hello'])await expect(fetchBinary(path)).rejects.toThrow('outside the configured API');
 expect(fetch).not.toHaveBeenCalled();
});
it('uses the owned API destination with redirect refusal and no replay',async()=>{
 const fetch=vi.fn().mockResolvedValue(new Response('synthetic evidence'));vi.stubGlobal('fetch',fetch);setAuthToken('synthetic-test-token');
 const response=await fetchBinary('/api/projects/1/evidence');expect(await response.text()).toBe('synthetic evidence');
 expect(fetch).toHaveBeenCalledTimes(1);expect(fetch.mock.calls[0][0]).toBe(new URL(apiUrl('/api/projects/1/evidence'),window.location.origin).href);
 expect(fetch.mock.calls[0][1]).toMatchObject({redirect:'error',cache:'no-store',credentials:'omit'});
 expect(new Headers(fetch.mock.calls[0][1].headers).get('Authorization')).toBe('Bearer synthetic-test-token');
});
it('keeps denied downloads denied and never retries them',async()=>{
 const fetch=vi.fn().mockResolvedValue(new Response(JSON.stringify({detail:{message:'File access denied'}}),{status:403}));vi.stubGlobal('fetch',fetch);
 await expect(fetchBinary('/files/projects/2/proof.txt')).rejects.toThrow('File access denied');expect(fetch).toHaveBeenCalledTimes(1);
});
