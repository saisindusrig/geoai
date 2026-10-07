/** Display-only ground preview. Never write this elevation into a model or survey record. */
export function modelDisplayElevation(
  originElevation: number,
  accepted: { elevation: number | null; offset: number; legacy_display_elevation?: number | null } | null,
  contextHeight: number | null,
): number {
  if (accepted) {
    if (accepted.elevation !== null && Number.isFinite(accepted.elevation)) return accepted.elevation + accepted.offset;
    // Preserve an audited legacy render transform without treating it as a measurement.
    if (accepted.legacy_display_elevation != null) return accepted.legacy_display_elevation + accepted.offset;
    return originElevation;
  }
  // Existing display origins stay fixed; their accuracy is established separately.
  if (originElevation !== 0) return originElevation;
  return contextHeight !== null && Number.isFinite(contextHeight) ? contextHeight : 0;
}

export function globalBuildingsVisible(requested: boolean, terrainEnabled: boolean, terrainReady: boolean, vendorDisabled: boolean) {
  return requested && terrainEnabled && terrainReady && !vendorDisabled;
}
