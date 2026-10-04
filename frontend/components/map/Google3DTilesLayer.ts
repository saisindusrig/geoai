import { Tile3DLayer } from "@deck.gl/geo-layers";
import { Tiles3DLoader } from "@loaders.gl/3d-tiles";
import { googleMapsApiKey } from "@/lib/map/providers";

export function google3DTilesLayer(visible: boolean) {
  const key = googleMapsApiKey();
  if (!visible || !key) return null;

  return new Tile3DLayer({
    id: "google-3d-tiles",
    data: "https://tile.googleapis.com/v1/3dtiles/root.json",
    loaders: [Tiles3DLoader],
    loadOptions: {
      fetch: {
        headers: {
          "X-GOOG-API-KEY": key,
        },
      },
    },
    visible,
    pickable: true,
    onTileError: (error) => {
      console.warn("[sitegeoai] Google Photorealistic 3D Tiles failed to load", error);
    },
  });
}
