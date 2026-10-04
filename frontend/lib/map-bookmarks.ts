export interface MapBookmark {
  id: string;
  name: string;
  center: [number, number];
  zoom: number;
  bearing: number;
  pitch: number;
  createdAt: number;
}

function storageKey(projectId: number) {
  return `geoai-map-bookmarks-${projectId}`;
}

export function loadMapBookmarks(projectId: number): MapBookmark[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = localStorage.getItem(storageKey(projectId));
    return raw ? (JSON.parse(raw) as MapBookmark[]) : [];
  } catch {
    return [];
  }
}

export function saveMapBookmarks(projectId: number, bookmarks: MapBookmark[]) {
  localStorage.setItem(storageKey(projectId), JSON.stringify(bookmarks.slice(0, 8)));
}

export function addMapBookmark(projectId: number, bookmark: Omit<MapBookmark, "id" | "createdAt">) {
  const list = loadMapBookmarks(projectId);
  const entry: MapBookmark = {
    ...bookmark,
    id: crypto.randomUUID(),
    createdAt: Date.now(),
  };
  saveMapBookmarks(projectId, [entry, ...list]);
  return entry;
}
