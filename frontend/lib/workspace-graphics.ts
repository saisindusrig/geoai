/** Presentation-only settings. Never stored in a model or sent to an API. */
export type GraphicsQuality = "auto" | "high" | "balanced" | "performance";
export type GraphicsContextState = "ready" | "lost" | "recovering";
export function graphicsSettings(quality: GraphicsQuality, width: number, height: number) {
  const area = Math.max(1, width) * Math.max(1, height);
  const scale = quality === "high" ? 1.25 : quality === "performance" ? 0.65
    : quality === "balanced" ? 1 : Math.max(0.65, Math.min(1, Math.sqrt(1_400_000 / area)));
  return { scale, shadows: quality === "high", fxaa: quality === "high" };
}
type GraphicsViewer = {
  canvas: HTMLCanvasElement; resolutionScale: number; useBrowserRecommendedResolution: boolean;
  shadows: boolean; useDefaultRenderLoop: boolean; resize(): void; isDestroyed(): boolean;
  scene: { requestRenderMode: boolean; maximumRenderTimeChange: number; requestRender(): void;
    postProcessStages?: { fxaa?: { enabled: boolean } } };
};
export function bindWorkspaceGraphics(viewer: GraphicsViewer, quality: () => GraphicsQuality,
  context: (state: GraphicsContextState) => void, restored: () => void) {
  let disposed = false, lost = false;
  const canvas = viewer.canvas;
  const update = () => {
    if (disposed || lost || viewer.isDestroyed()) return;
    const mode = quality(), settings = graphicsSettings(mode, canvas.clientWidth, canvas.clientHeight);
    // Bound actual drawing-buffer resolution independently of devicePixelRatio.
    viewer.useBrowserRecommendedResolution = true;
    viewer.resolutionScale = settings.scale;
    viewer.shadows = settings.shadows;
    if (viewer.scene.postProcessStages?.fxaa) viewer.scene.postProcessStages.fxaa.enabled = settings.fxaa;
    viewer.resize(); viewer.scene.requestRender();
    canvas.dataset.graphicsQuality = mode;
    canvas.dataset.graphicsScale = settings.scale.toFixed(3);
  };
  const onLost = (event: Event) => {
    event.preventDefault(); lost = true; viewer.useDefaultRenderLoop = false;
    canvas.dataset.graphicsContext = "lost"; context("lost");
  };
  const onRestored = () => {
    if (disposed) return;
    canvas.dataset.graphicsContext = "recovering"; context("recovering");
    // Recreate through the existing viewer lifecycle; do not reuse invalid GPU resources.
    restored();
  };
  viewer.scene.requestRenderMode = true; viewer.scene.maximumRenderTimeChange = Infinity;
  canvas.addEventListener("webglcontextlost", onLost);
  canvas.addEventListener("webglcontextrestored", onRestored);
  window.addEventListener("resize", update); window.addEventListener("orientationchange", update);
  const observer = typeof ResizeObserver === "undefined" ? null : new ResizeObserver(update);
  observer?.observe(canvas.parentElement ?? canvas);
  canvas.dataset.graphicsContext = "ready"; context("ready"); update();
  return { update, dispose() {
    disposed = true; observer?.disconnect();
    canvas.removeEventListener("webglcontextlost", onLost); canvas.removeEventListener("webglcontextrestored", onRestored);
    window.removeEventListener("resize", update); window.removeEventListener("orientationchange", update);
  } };
}
