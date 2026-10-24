const path=require('node:path'),fs=require('node:fs'),assert=require('node:assert/strict');
const front=path.resolve(__dirname,'../../frontend');const sharp=require(path.join(front,'node_modules/sharp'));
const {imageOptimizerTransform}=require(path.join(front,'node_modules/next/dist/server/image-optimizer/transform'));
const defaults=require(path.join(front,'node_modules/next/dist/shared/lib/image-config')).imageConfigDefault;
(async()=>{
 const base={create:{width:16,height:16,channels:3,background:{r:60,g:120,b:180}}};
 const png=await sharp(base).png().toBuffer(),avif=await sharp(base).avif().toBuffer();
 const cfg={images:{...defaults,formats:['image/avif','image/webp']},experimental:{}};
 async function optimize(buffer,mimeType){return imageOptimizerTransform({buffer,etag:'benign-generated-fixture',cacheControl:'max-age=60'},{href:'/synthetic-fixture',quality:75,width:16,mimeType},cfg);}
 const webp=await optimize(avif,'image/webp');assert.equal(webp.contentType,'image/webp');assert.equal((await sharp(webp.buffer).metadata()).format,'webp');
 const encoded=await optimize(png,'image/avif');assert.equal(encoded.contentType,'image/avif');
 let svgRejected=false;try{await optimize(Buffer.from('<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16"><rect width="16" height="16"/></svg>'),'image/webp');}catch(error){svgRejected=error.statusCode===400;}
 assert.equal(svgRejected,true);
 const result={next:require(path.join(front,'node_modules/next/package.json')).version,sharp:require(path.join(front,'node_modules/sharp/package.json')).version,libvips:sharp.versions.vips,heif:sharp.versions.heif,avif_input_to_webp:true,png_to_avif:true,svg_optimizer_rejected_by_default:svgRejected,malicious_payloads_executed:false};
 fs.writeFileSync(path.join(__dirname,'image-codec-probe.json'),JSON.stringify(result,null,2));console.log(result);
})().catch(error=>{console.error(error.message);process.exitCode=1;});
