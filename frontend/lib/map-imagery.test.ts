import { beforeEach, describe, expect, it, vi } from "vitest";
const apiMock = vi.hoisted(() => ({ get: vi.fn(), apiUrl: vi.fn((url: string) => `http://localhost:8000${url}`) }));
vi.mock("@/lib/api", () => ({ api: { get: apiMock.get }, apiUrl: apiMock.apiUrl }));

beforeEach(() => { vi.resetModules(); vi.clearAllMocks(); });

const providers = {
  satellite_config: { provider: "esri", max_zoom: 19, tile_size: 256, url_template: "https://server.arcgisonline.com/tile/{z}/{y}/{x}", attribution: "Esri World Imagery" },
};
function cesium() {
  const urlProvider = vi.fn();
  const ionProvider = vi.fn();
  return { IonImageryProvider: { fromAssetId: ionProvider }, UrlTemplateImageryProvider: class { constructor(config: unknown) { urlProvider(config); } }, urlProvider, ionProvider };
}

describe("Cesium basemap loading", () => {
  it("loads configured satellite tiles without an Ion token", async () => {
    apiMock.get.mockResolvedValue(providers);
    const C = cesium();
    const { loadCesiumBasemapProvider } = await import("./map-imagery");
    await loadCesiumBasemapProvider(C, "satellite", null);
    expect(C.ionProvider).not.toHaveBeenCalled();
    expect(C.urlProvider).toHaveBeenCalledWith(expect.objectContaining({ url: providers.satellite_config.url_template, credit: "Esri World Imagery" }));
  });
  it("prefers working Ion imagery", async () => {
    const C = cesium(); C.ionProvider.mockResolvedValue({ ion: true });
    const { loadCesiumBasemapProvider } = await import("./map-imagery");
    expect(await loadCesiumBasemapProvider(C, "satellite", "configured")).toEqual({ ion: true });
    expect(apiMock.get).not.toHaveBeenCalled();
  });
  it("falls back when Ion authorization fails", async () => {
    apiMock.get.mockResolvedValue(providers);
    const C = cesium(); C.ionProvider.mockRejectedValue(new Error("Unauthorized"));
    const { loadCesiumBasemapProvider } = await import("./map-imagery");
    await loadCesiumBasemapProvider(C, "satellite", "expired");
    expect(C.urlProvider).toHaveBeenCalledOnce();
  });
  it("honors street selection even with an Ion token", async () => {
    apiMock.get.mockResolvedValue(providers);
    const C = cesium();
    const { loadCesiumBasemapProvider } = await import("./map-imagery");
    await loadCesiumBasemapProvider(C, "street", "configured");
    expect(C.ionProvider).not.toHaveBeenCalled();
    expect(C.urlProvider).toHaveBeenCalledWith(expect.objectContaining({ url: "https://tile.openstreetmap.org/{z}/{x}/{y}.png" }));
  });
});
