/** Display-only ground preview. Never write this elevation into a model or survey record. */
export function modelDisplayElevation(
  originElevation: number,
  accepted: { elevation: number; offset: number } | null,
  contextHeight: number | null,
): number {
  if (accepted) return accepted.elevation + accepted.offset;
  // An explicit nonzero origin remains an absolute engineering elevation.
  if (originElevation !== 0) return originElevation;
  return contextHeight !== null && Number.isFinite(contextHeight) ? contextHeight : 0;
}

export function globalBuildingsVisible(requested: boolean, terrainEnabled: boolean, terrainReady: boolean, vendorDisabled: boolean) {
  return requested && terrainEnabled && terrainReady && !vendorDisabled;
}
