import {expect,it} from 'vitest';
import {readFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {createRequire} from 'node:module';
const require=createRequire(import.meta.url);
const semver=require('semver') as {gte:(version:string,minimum:string)=>boolean;satisfies:(version:string,range:string)=>boolean};
const read=(path:string)=>JSON.parse(readFileSync(resolve(process.cwd(),path),'utf8'));
it('declared locked and installed Next packages agree and exclude reviewed vulnerable releases',()=>{
 const source=read('package.json'),lock=read('package-lock.json');
 for(const name of ['next','eslint-config-next','@next/bundle-analyzer']){
  const installed=read(`node_modules/${name}/package.json`).version as string;
  expect(source.dependencies?.[name]??source.devDependencies?.[name]).toBe(installed);
  expect(lock.packages[`node_modules/${name}`].version).toBe(installed);
  expect(semver.gte(installed,'16.4.1')).toBe(true);
 }
});
it('patched native image dependency and existing React satisfy framework requirements',()=>{
 const framework=read('node_modules/next/package.json');
 expect(semver.gte(read('node_modules/sharp/package.json').version,'0.35.5')).toBe(true);
 for(const name of ['react','react-dom'])expect(semver.satisfies(read(`node_modules/${name}/package.json`).version,framework.peerDependencies[name])).toBe(true);
});
