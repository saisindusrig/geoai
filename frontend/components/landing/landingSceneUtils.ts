import * as THREE from "three";

export const LANDING_PALETTE = {
  terrainLow: "#4a7c4e",
  terrainMid: "#3d6b42",
  terrainHigh: "#8b7d5a",
  terrainRock: "#6b6358",
  grass: "#5a9c5e",
  water: "#2a8fa8",
  terrainHighlight: "#b2bbab",
  wire: "#8ea0a3",
  road: "#3a4550",
  roadMarking: "#e8ece8",
  asphalt: "#2c3238",
  globeOcean: "#1a5f7a",
  globeLand: "#3d7a45",
  building: "#b8c0c8",
  buildingGlass: "#6a8fa8",
  buildingDark: "#5a6470",
  concrete: "#9aa3ad",
  excavation: "#6b5344",
  pillar: "#8a9299",
} as const;

/** Multi-octave height for more natural rolling terrain */
export function displaceTerrain(x: number, z: number) {
  let h = 0;
  let amp = 1;
  let freq = 0.38;
  for (let i = 0; i < 6; i++) {
    h +=
      amp *
      (Math.sin(x * freq + 1.2) * Math.cos(z * freq * 0.9) +
        0.5 * Math.sin(x * freq * 2.1 + z * freq * 1.3) +
        0.25 * Math.sin(x * freq * 3.7 - z * freq * 2.4) +
        0.12 * Math.sin(x * freq * 5.2 + z * freq * 4.1));
    amp *= 0.44;
    freq *= 2.1;
  }
  return h * 0.46;
}

export function terrainNormalAt(x: number, z: number, epsilon = 0.08) {
  const y0 = displaceTerrain(x, z);
  const yx = displaceTerrain(x + epsilon, z) - y0;
  const yz = displaceTerrain(x, z + epsilon) - y0;
  return new THREE.Vector3(-yx / epsilon, 1, -yz / epsilon).normalize();
}

export function buildTerrainGeometry(size = 10, segments = 192) {
  const geo = new THREE.PlaneGeometry(size, size, segments, segments);
  geo.rotateX(-Math.PI / 2);

  const pos = geo.attributes.position;
  for (let i = 0; i < pos.count; i++) {
    const x = pos.getX(i);
    const z = pos.getZ(i);
    pos.setY(i, displaceTerrain(x, z));
  }

  geo.computeVertexNormals();
  geo.computeTangents();
  return geo;
}

export function createEarthTexture(size = 1024) {
  const canvas = document.createElement("canvas");
  canvas.width = size;
  canvas.height = size;
  const ctx = canvas.getContext("2d")!;
  ctx.fillStyle = LANDING_PALETTE.globeOcean;
  ctx.fillRect(0, 0, size, size);

  // Ocean depth variation
  for (let i = 0; i < 8000; i++) {
    const x = Math.random() * size;
    const y = Math.random() * size;
    ctx.fillStyle = `rgba(15,70,95,${0.04 + Math.random() * 0.14})`;
    ctx.beginPath();
    ctx.arc(x, y, 1 + Math.random() * 10, 0, Math.PI * 2);
    ctx.fill();
  }

  const land = [
    { x: 0.22, y: 0.35, rx: 0.18, ry: 0.22 },
    { x: 0.55, y: 0.28, rx: 0.2, ry: 0.18 },
    { x: 0.72, y: 0.55, rx: 0.14, ry: 0.2 },
    { x: 0.35, y: 0.62, rx: 0.16, ry: 0.14 },
    { x: 0.48, y: 0.48, rx: 0.1, ry: 0.12 },
  ];

  for (const l of land) {
    ctx.beginPath();
    ctx.ellipse(l.x * size, l.y * size, l.rx * size, l.ry * size, 0.4, 0, Math.PI * 2);
    const g = ctx.createRadialGradient(
      l.x * size,
      l.y * size,
      0,
      l.x * size,
      l.y * size,
      Math.max(l.rx, l.ry) * size,
    );
    g.addColorStop(0, "#4d8a52");
    g.addColorStop(0.55, LANDING_PALETTE.globeLand);
    g.addColorStop(1, "#2d5a35");
    ctx.fillStyle = g;
    ctx.fill();
  }

  const tex = new THREE.CanvasTexture(canvas);
  tex.colorSpace = THREE.SRGBColorSpace;
  return tex;
}

export function sampleRoadPoints(
  count: number,
  fn: (t: number) => { x: number; z: number },
  lift = 0.06,
) {
  return Array.from({ length: count }, (_, i) => {
    const t = i / (count - 1);
    const { x, z } = fn(t);
    return new THREE.Vector3(x, displaceTerrain(x, z) + lift, z);
  });
}

const _tangent = new THREE.Vector3();
const _right = new THREE.Vector3();
const _center = new THREE.Vector3();
const _left = new THREE.Vector3();
const _rightPt = new THREE.Vector3();
const _up = new THREE.Vector3(0, 1, 0);

/** Flat road ribbon draped on terrain — not a cylindrical tube. */
export function buildFlatRoadGeometry(
  points: THREE.Vector3[],
  width: number,
  options?: {
    segments?: number;
    lift?: number;
    drapeTerrain?: boolean;
    uvScale?: number;
  },
) {
  const {
    segments = Math.max(points.length * 12, 96),
    lift = 0.055,
    drapeTerrain = true,
    uvScale = 0.22,
  } = options ?? {};

  const curve = new THREE.CatmullRomCurve3(points);
  const halfW = width / 2;
  const positions: number[] = [];
  const uvs: number[] = [];
  const indices: number[] = [];

  for (let i = 0; i <= segments; i++) {
    const t = i / segments;
    curve.getPoint(t, _center);
    curve.getTangent(t, _tangent);
    if (_tangent.lengthSq() < 1e-8) _tangent.set(1, 0, 0);
    _tangent.normalize();

    if (drapeTerrain) {
      _tangent.y = 0;
      if (_tangent.lengthSq() < 1e-8) _tangent.set(1, 0, 0);
      _tangent.normalize();
    }

    _right.crossVectors(_up, _tangent).normalize();
    if (_right.lengthSq() < 1e-8) _right.set(1, 0, 0);

    _left.copy(_center).addScaledVector(_right, -halfW);
    _rightPt.copy(_center).addScaledVector(_right, halfW);

    if (drapeTerrain) {
      _left.y = displaceTerrain(_left.x, _left.z) + lift;
      _rightPt.y = displaceTerrain(_rightPt.x, _rightPt.z) + lift;
    }

    positions.push(_left.x, _left.y, _left.z, _rightPt.x, _rightPt.y, _rightPt.z);
    const v = t * segments * uvScale;
    uvs.push(0, v, 1, v);
  }

  for (let i = 0; i < segments; i++) {
    const a = i * 2;
    indices.push(a, a + 2, a + 1, a + 1, a + 2, a + 3);
  }

  const geo = new THREE.BufferGeometry();
  geo.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
  geo.setAttribute("uv", new THREE.Float32BufferAttribute(uvs, 2));
  geo.setIndex(indices);
  geo.computeVertexNormals();
  return geo;
}

export type BuildingSpec = {
  x: number;
  z: number;
  w: number;
  d: number;
  h: number;
  floors?: number;
  style?: "glass" | "tech" | "mixed";
  rotation?: number;
};

type XZ = { x: number; z: number };

const BUILDING_STYLES: BuildingSpec["style"][] = ["mixed", "tech", "glass"];

function distToSegment(px: number, pz: number, ax: number, az: number, bx: number, bz: number) {
  const dx = bx - ax;
  const dz = bz - az;
  const lenSq = dx * dx + dz * dz;
  if (lenSq < 1e-8) return Math.hypot(px - ax, pz - az);
  const t = Math.max(0, Math.min(1, ((px - ax) * dx + (pz - az) * dz) / lenSq));
  const cx = ax + t * dx;
  const cz = az + t * dz;
  return Math.hypot(px - cx, pz - cz);
}

export function distanceToPolyline(x: number, z: number, points: XZ[]) {
  let min = Infinity;
  for (let i = 0; i < points.length - 1; i++) {
    const p0 = points[i];
    const p1 = points[i + 1];
    min = Math.min(min, distToSegment(x, z, p0.x, p0.z, p1.x, p1.z));
  }
  return min;
}

export function isClearOfRoads(x: number, z: number, roads: XZ[][], clearance: number) {
  return roads.every((road) => distanceToPolyline(x, z, road) >= clearance);
}

function heroMainRoadPoint(t: number): XZ {
  return {
    x: THREE.MathUtils.lerp(-3.2, 3.4, t),
    z: Math.sin(t * Math.PI * 1.35) * 2.1,
  };
}

function sampleCenterline(count: number, fn: (t: number) => XZ): XZ[] {
  return Array.from({ length: count }, (_, i) => fn(i / (count - 1)));
}

function branchCenterline(start: XZ, end: XZ, count = 12): XZ[] {
  return Array.from({ length: count }, (_, i) => {
    const t = i / (count - 1);
    return {
      x: THREE.MathUtils.lerp(start.x, end.x, t),
      z: THREE.MathUtils.lerp(start.z, end.z, t),
    };
  });
}

function buildingVariant(seed: number): Pick<BuildingSpec, "w" | "d" | "h" | "floors" | "style"> {
  const styles = BUILDING_STYLES;
  const style = styles[seed % styles.length];
  const floors = 2 + (seed % 5);
  const w = 0.2 + (seed % 4) * 0.06;
  const d = 0.18 + ((seed + 2) % 4) * 0.055;
  const h = 0.32 + floors * 0.11 + (seed % 3) * 0.04;
  return { w, d, h, floors, style };
}

export type HeroSiteLayout = {
  mainRoad: THREE.Vector3[];
  branchRoads: THREE.Vector3[][];
  buildings: BuildingSpec[];
};

export function generateHeroSiteLayout(): HeroSiteLayout {
  const mainCenterline = sampleCenterline(28, heroMainRoadPoint);
  const roads: XZ[][] = [mainCenterline];
  const buildings: BuildingSpec[] = [];
  const used = new Set<string>();
  const roadClearance = 0.32;

  const branchDefs = [
    { t: 0.14, offsetAngle: -1.05, length: 2.4, slots: 3 },
    { t: 0.36, offsetAngle: 1.35, length: 2.0, slots: 3 },
    { t: 0.58, offsetAngle: -1.55, length: 2.2, slots: 2 },
    { t: 0.78, offsetAngle: 0.65, length: 1.9, slots: 2 },
  ];

  let seed = 0;

  for (const branch of branchDefs) {
    const start = heroMainRoadPoint(branch.t);
    const prev = heroMainRoadPoint(Math.max(0, branch.t - 0.04));
    const next = heroMainRoadPoint(Math.min(1, branch.t + 0.04));
    const tangent = Math.atan2(next.z - prev.z, next.x - prev.x);
    const angle = tangent + branch.offsetAngle;
    const end = {
      x: start.x + Math.cos(angle) * branch.length,
      z: start.z + Math.sin(angle) * branch.length,
    };
    const branchLine = branchCenterline(start, end, 14);
    roads.push(branchLine);

    const perpX = -Math.sin(angle);
    const perpZ = Math.cos(angle);

    for (let i = 0; i < branch.slots; i++) {
      const along = 0.32 + (i + 1) / (branch.slots + 1) * 0.55;
      const bx = THREE.MathUtils.lerp(start.x, end.x, along);
      const bz = THREE.MathUtils.lerp(start.z, end.z, along);
      const side = i % 2 === 0 ? 1 : -1;
      const setback = 0.34 + (i % 3) * 0.06;
      const x = bx + perpX * side * setback;
      const z = bz + perpZ * side * setback;

      if (!isClearOfRoads(x, z, roads, roadClearance)) continue;
      const key = `${x.toFixed(2)}-${z.toFixed(2)}`;
      if (used.has(key)) continue;
      used.add(key);

      const variant = buildingVariant(seed++);
      buildings.push({
        x,
        z,
        rotation: angle + (side > 0 ? Math.PI / 2 : -Math.PI / 2),
        ...variant,
      });
    }
  }

  const scatterPoints: XZ[] = [
    { x: -2.6, z: -1.7 },
    { x: -1.8, z: -2.1 },
    { x: 2.9, z: 1.6 },
    { x: 3.1, z: -1.3 },
    { x: -2.4, z: 0.4 },
    { x: 0.6, z: 2.35 },
    { x: -0.9, z: -1.6 },
    { x: 1.4, z: 1.9 },
    { x: 2.2, z: -2.0 },
    { x: -3.0, z: 1.8 },
  ];

  for (const pt of scatterPoints) {
    if (Math.hypot(pt.x + 1.6, pt.z - 1.2) < 1.05) continue;
    if (!isClearOfRoads(pt.x, pt.z, roads, roadClearance)) continue;
    const key = `${pt.x.toFixed(2)}-${pt.z.toFixed(2)}`;
    if (used.has(key)) continue;
    used.add(key);
    const variant = buildingVariant(seed++);
    buildings.push({
      x: pt.x,
      z: pt.z,
      rotation: (seed * 0.71) % (Math.PI * 2),
      ...variant,
    });
  }

  return {
    mainRoad: sampleRoadPoints(28, heroMainRoadPoint),
    branchRoads: roads.slice(1).map((line) =>
      line.map((p) => new THREE.Vector3(p.x, displaceTerrain(p.x, p.z) + 0.06, p.z)),
    ),
    buildings,
  };
}

export const HERO_BUILDINGS: BuildingSpec[] = generateHeroSiteLayout().buildings;

export const WORKSPACE_BUILDINGS: BuildingSpec[] = [
  { x: 1.55, z: 1.05, w: 0.4, d: 0.36, h: 0.58, floors: 4, style: "mixed" },
  { x: 1.95, z: 0.85, w: 0.34, d: 0.3, h: 0.82, floors: 6, style: "tech" },
  { x: 2.25, z: 1.2, w: 0.3, d: 0.28, h: 0.46, floors: 3, style: "glass" },
  { x: -1.15, z: 1.45, w: 0.36, d: 0.32, h: 0.42, floors: 3, style: "mixed" },
  { x: -0.8, z: 1.65, w: 0.28, d: 0.26, h: 0.64, floors: 5, style: "tech" },
  { x: 2.55, z: 0.95, w: 0.24, d: 0.22, h: 0.55, floors: 4, style: "glass" },
  { x: -1.45, z: 0.95, w: 0.3, d: 0.28, h: 0.48, floors: 3, style: "mixed" },
];
