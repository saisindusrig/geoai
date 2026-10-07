import { beforeEach, describe, expect, it, vi } from "vitest";
const apiMock = vi.hoisted(() => ({ get: vi.fn(), apiUrl: vi.fn() }));
vi.mock("@/lib/api", () => ({ api: { get: apiMock.get }, apiUrl: apiMock.apiUrl }));
beforeEach(() => { vi.resetModules(); vi.clearAllMocks(); });
function cesium() {
  return { IonImageryProvider: { fromAssetId: vi.fn() }, TileMapServiceImageryProvider: { fromUrl: vi.fn().mockResolvedValue({ reference: true }) }, buildModuleUrl: vi.fn((path: string) => `/cesium/${path}`) };
}
describe("Cesium-only imagery", () => {
  it("uses bundled Cesium imagery without contacting Esri or tile providers", async () => {
    const C = cesium(); const { loadCesiumBasemapProvider } = await import("./map-imagery");
    await loadCesiumBasemapProvider(C, "satellite", null);
    expect(C.TileMapServiceImageryProvider.fromUrl).toHaveBeenCalledWith("/cesium/Assets/Textures/NaturalEarthII");
    expect(apiMock.get).not.toHaveBeenCalled();
  });
  it("uses Ion when configured", async () => {
    const C = cesium(); C.IonImageryProvider.fromAssetId.mockResolvedValue({ ion: true });
    const { loadCesiumBasemapProvider } = await import("./map-imagery");
    expect(await loadCesiumBasemapProvider(C, "satellite", "configured")).toEqual({ ion: true });
    expect(C.TileMapServiceImageryProvider.fromUrl).not.toHaveBeenCalled();
  });
  it("uses Cesium reference imagery if Ion fails", async () => {
    const C = cesium(); C.IonImageryProvider.fromAssetId.mockRejectedValue(new Error("Unauthorized"));
    const { loadCesiumBasemapProvider } = await import("./map-imagery");
    expect(await loadCesiumBasemapProvider(C, "satellite", "expired")).toEqual({ reference: true });
    expect(apiMock.get).not.toHaveBeenCalled();
  });
});
