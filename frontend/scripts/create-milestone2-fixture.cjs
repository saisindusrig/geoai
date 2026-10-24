// Local fixture preparation uses only installed TypeScript and the actual generators.
const fs = require('node:fs');
const path = require('node:path');
const ts = require('typescript');
const root = path.resolve(__dirname, '../..');
const output = path.join(root, '.cache/milestone2/compiled');
fs.mkdirSync(output, {recursive:true});
for (const name of ['parametric-platform','platform-attachments']) {
  const source = fs.readFileSync(path.join(root, `frontend/lib/${name}.ts`), 'utf8');
  fs.writeFileSync(path.join(output, `${name}.js`), ts.transpileModule(source, {compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022}}).outputText);
}
const {previewPlatform,readPlatform} = require(path.join(output,'parametric-platform.js'));
const {previewAttachment,ATTACHMENT_DEFAULTS} = require(path.join(output,'platform-attachments.js'));
const base = JSON.parse(fs.readFileSync(path.join(root,'frontend/lib/__fixtures__/maintenance-platform.json'),'utf8'));
let doc = previewPlatform(base,{...readPlatform(base),length:5,width:3,height:3});
const prefix='industrial-platform-5x3:';
for(const corner of ['sw','se','nw','ne']) for(const kind of ['foundation','base_plate','connection']) {
  doc=previewAttachment(doc,{id:`${kind}-${corner}`,kind,refs:kind==='connection'?[prefix+`column-${corner}`,prefix+(corner.startsWith('s')?'beam-south':'beam-north')]:[prefix+`column-${corner}`],parameters:{...ATTACHMENT_DEFAULTS[kind]}});
}
for(const side of ['w','e']) doc=previewAttachment(doc,{id:`brace-${side}`,kind:'brace',refs:[prefix+`column-s${side}`,prefix+`column-n${side}`],parameters:{...ATTACHMENT_DEFAULTS.brace}});
doc=previewAttachment(doc,{id:'stairs-south',kind:'stairs',refs:[prefix+'platform-deck'],parameters:{...ATTACHMENT_DEFAULTS.stairs}});
fs.writeFileSync(path.join(root,'.cache/milestone2/generated-platform.json'),JSON.stringify(doc,null,2));
console.log(`Generated ${doc.components.length} actual components in .cache/milestone2/generated-platform.json; no network or AI.`);
