/** Visual collision floor only; never a surveyed elevation or model placement. */
export function cameraSurfaceFloor(height: number | undefined, exaggeration: number, relativeHeight: number) {
  const surface = Number.isFinite(height) ? height! : 0;
  return (surface - relativeHeight) * exaggeration + relativeHeight + 2;
}
