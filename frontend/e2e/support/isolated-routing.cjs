/** Fail-closed routing for isolated browser checks. No arbitrary localhost bypass. */
function classifyRequest(raw, method, frontendOrigin, isolatedOrigin) {
  const url = new URL(raw);
  const source = new URL(frontendOrigin);
  const isolated = new URL(isolatedOrigin);
  if (isolated.hostname !== '127.0.0.1' || isolated.port !== '8003') throw new Error('Isolated API must be the dedicated loopback port');
  if (url.origin !== source.origin) return { kind: 'block', reason: 'outside frontend origin' };
  if (url.pathname === '/__nextjs_original-stack-frames') return { kind: 'mock-dev' };
  if (url.pathname.endsWith('/site-suggestions')) return { kind: 'mock-suggestions' };
  if (!['GET', 'HEAD'].includes(method)) return { kind: 'block', reason: 'mutation' };
  if (url.pathname.endsWith('/map-runtime-config')) return { kind: 'mock-map' };
  const path = url.pathname.startsWith('/local-api/') ? url.pathname.slice('/local-api'.length) : url.pathname;
  const exportListing = /^\/api\/projects\/(?:991600|991280)\/exports\/files$/.test(path);
  if (!exportListing && /\/(?:demo|export|exports|download|generate|authorize-run)(?:\/|$)/.test(path)) return { kind: 'block', reason: 'side-effect or download endpoint' };
  if (path.startsWith('/files/') && !/^\/files\/projects\/(?:991600|991280)\//.test(path)) return { kind: 'block', reason: 'not a synthetic project file' };
  if (path.startsWith('/api/') || path.startsWith('/files/')) return { kind: 'isolated', url: isolated.origin + path + url.search };
  // Allow only Next resources, known local public assets and explicit UI routes.
  if (url.pathname.startsWith('/local-api') || /%2f|%5c/i.test(url.pathname)) return { kind: 'block', reason: 'ambiguous proxy path' };
  const publicAsset = /^\/(?:_next\/|__nextjs_font\/|brand\/|images\/|cesium\/|fonts\/|models\/)/.test(path)
    || /^\/(?:icon\.svg|favicon\.ico|manifest\.webmanifest|brand-social\.(?:png|svg))$/.test(path);
  const page = /^\/(?:$|login$|dashboard$|settings$|diagnostics$|projects\/\d+\/(?:workspace|analysis|model|report)$)/.test(path);
  return publicAsset || page ? { kind: 'frontend' } : { kind: 'block', reason: 'unlisted resource' };
}
module.exports = { classifyRequest };
