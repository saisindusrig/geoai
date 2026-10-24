import { expect, it } from 'vitest';
// Shared CommonJS boundary is used by the standalone Chrome evidence harness.
// eslint-disable-next-line @typescript-eslint/no-require-imports
const { classifyRequest } = require('../e2e/support/isolated-routing.cjs');
const classify=(url:string,method='GET')=>classifyRequest(url,method,'http://127.0.0.1:3001','http://127.0.0.1:8003');
it('routes API and file assets exclusively to isolated storage, including absolute legacy URLs',()=>{
 expect(classify('http://127.0.0.1:3001/local-api/files/projects/991600/excavation.glb')).toEqual({kind:'isolated',url:'http://127.0.0.1:8003/files/projects/991600/excavation.glb'});
 expect(classify('http://127.0.0.1:3001/files/projects/991600/model.glb').kind).toBe('isolated');
 expect(classify('http://127.0.0.1:3001/local-api/api/projects/1').kind).toBe('isolated');
 expect(classify('http://localhost:8001/files/projects/991600/model.glb').kind).toBe('block');
 expect(classify('http://127.0.0.1:8001/api/projects').kind).toBe('block');
});
it('blocks writes, exports, unknown proxy paths and outside requests',()=>{
 for(const method of ['POST','PUT','PATCH','DELETE'])expect(classify('http://127.0.0.1:3001/local-api/api/projects',method).kind).toBe('block');
 for(const url of ['/unknown-download','/local-api/unknown','/local-api%2ffiles/x'])expect(classify('http://127.0.0.1:3001'+url).kind).toBe('block');
 expect(classify('http://127.0.0.1:3001/api/projects/991600/exports/files').kind).toBe('isolated');
 expect(classify('http://127.0.0.1:3001/api/projects/991600/exports/report').kind).toBe('block');
 expect(classify('http://127.0.0.1:3001/api/projects/demo').kind).toBe('block');
 expect(classify('http://127.0.0.1:3001/files/projects/5/excavation.glb').kind).toBe('block');
 expect(classify('https://example.com/api').kind).toBe('block');
 expect(classify('http://127.0.0.1:3001/_next/static/chunk.js').kind).toBe('frontend');
 expect(()=>classifyRequest('http://127.0.0.1:3001/','GET','http://127.0.0.1:3001','http://127.0.0.1:8001')).toThrow();
});

