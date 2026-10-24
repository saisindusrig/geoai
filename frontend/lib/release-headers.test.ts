import { expect,it } from 'vitest';
import config from '../next.config';
it('sets compatible baseline browser security headers without weakening the local API proxy',async()=>{
 const rules=await config.headers!();const values=Object.fromEntries(rules[0].headers.map(item=>[item.key,item.value]));
 expect(rules[0].source).toBe('/:path*');
 expect(values['X-Content-Type-Options']).toBe('nosniff');
 expect(values['X-Frame-Options']).toBe('DENY');
 expect(values['Referrer-Policy']).toBe('strict-origin-when-cross-origin');
 expect(values['Content-Security-Policy']).toContain("frame-ancestors 'none'");
 expect(values['Content-Security-Policy']).not.toContain('unsafe-eval');
 expect(config.poweredByHeader).toBe(false);
});
