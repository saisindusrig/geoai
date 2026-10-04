/** Shared map / 3D drawing colors — keep in sync with CSS vars in globals.css */
export const MAP_COLORS = {
  road: "#F59E0B",
  valid: "#B2BBAB",
  primary: "#B2BBAB",
  structure: "#4B5C58",
  /** Subtle OSM / fallback building extrusions in 3D workspace */
  contextBuilding: "rgba(75, 92, 88, 0.25)",
  contextBuildingOutline: "rgba(75, 92, 88, 0.45)",
  water: "#8EA0A3",
  warning: "#F59E0B",
  danger: "#EF4444",
  vertexStroke: "#EAEDE9",
} as const;
