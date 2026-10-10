/** Load the installed package's official browser build and existing assets.
 * Keeps embedded ZIP/WASM strings out of Next's JavaScript minifier.
 */
type Runtime = typeof import("cesium");
let pending: Promise<Runtime> | null = null;

export function loadCesiumRuntime(): Promise<Runtime> {
  const global = window as Window & {Cesium?: Runtime};
  if (global.Cesium?.Viewer) return Promise.resolve(global.Cesium);
  if (pending) return pending;
  pending = new Promise<Runtime>((resolve, reject) => {
    const script = document.createElement("script");
    script.src = "/cesium/Cesium.js";
    script.async = true;
    const timer = window.setTimeout(() => failed(new Error("Cesium browser runtime loading timed out.")), 30000);
    const failed = (error: Error) => {window.clearTimeout(timer); script.remove(); pending = null; reject(error);};
    script.onerror = () => failed(new Error("Cesium browser runtime is unavailable."));
    script.onload = () => {
      window.clearTimeout(timer);
      if (!global.Cesium?.Viewer) {failed(new Error("Invalid Cesium browser runtime.")); return;}
      resolve(global.Cesium);
    };
    document.head.appendChild(script);
  });
  return pending;
}
