/** Whether the heavy Cesium viewer should mount (3D mode only). */
export function shouldMountCesiumView(view: "2d" | "3d"): boolean {
  return view === "3d";
}
