import { useMemo } from "react";
import * as THREE from "three";
import { LANDING_PALETTE } from "./landingSceneUtils";

type Ctx = CanvasRenderingContext2D;

const TEXTURE_CACHE_VERSION = 4;

function hash2(x: number, y: number) {
  const n = Math.sin(x * 127.1 + y * 311.7) * 43758.5453;
  return n - Math.floor(n);
}

function smoothNoise(x: number, y: number) {
  const ix = Math.floor(x);
  const iy = Math.floor(y);
  const fx = x - ix;
  const fy = y - iy;
  const ux = fx * fx * (3 - 2 * fx);
  const uy = fy * fy * (3 - 2 * fy);
  const a = hash2(ix, iy);
  const b = hash2(ix + 1, iy);
  const c = hash2(ix, iy + 1);
  const d = hash2(ix + 1, iy + 1);
  return a * (1 - ux) * (1 - uy) + b * ux * (1 - uy) + c * (1 - ux) * uy + d * ux * uy;
}

function fbm(x: number, y: number, octaves = 5) {
  let v = 0;
  let amp = 0.5;
  let freq = 1;
  for (let i = 0; i < octaves; i++) {
    v += amp * smoothNoise(x * freq, y * freq);
    amp *= 0.5;
    freq *= 2.12;
  }
  return v;
}

function terrainHeight(u: number, v: number) {
  return (
    fbm(u * 14, v * 14, 7) * 0.55 +
    fbm(u * 38 + 2.1, v * 38 + 1.4, 5) * 0.28 +
    fbm(u * 88 + 5, v * 88 + 3, 3) * 0.17
  );
}

function canvasTexture(
  draw: (ctx: Ctx, size: number) => void,
  size: number,
  repeat = 1,
  colorSpace: THREE.ColorSpace = THREE.SRGBColorSpace,
) {
  const canvas = document.createElement("canvas");
  canvas.width = size;
  canvas.height = size;
  const ctx = canvas.getContext("2d")!;
  draw(ctx, size);
  const tex = new THREE.CanvasTexture(canvas);
  tex.wrapS = tex.wrapT = THREE.RepeatWrapping;
  tex.repeat.set(repeat, repeat);
  tex.colorSpace = colorSpace;
  tex.anisotropy = 16;
  tex.minFilter = THREE.LinearMipmapLinearFilter;
  tex.generateMipmaps = true;
  return tex;
}

function normalMapFromHeight(
  heightFn: (u: number, v: number) => number,
  size: number,
  strength = 2.5,
  repeat = 4,
) {
  return canvasTexture(
    (ctx, s) => {
      const img = ctx.createImageData(s, s);
      const step = 1 / s;
      for (let y = 0; y < s; y++) {
        for (let x = 0; x < s; x++) {
          const u = x / s;
          const v = y / s;
          const hL = heightFn(u - step, v);
          const hR = heightFn(u + step, v);
          const hD = heightFn(u, v - step);
          const hU = heightFn(u, v + step);
          const nx = (hL - hR) * strength;
          const ny = (hD - hU) * strength;
          const nz = 1;
          const len = Math.sqrt(nx * nx + ny * ny + nz * nz);
          const i = (y * s + x) * 4;
          img.data[i] = ((nx / len) * 0.5 + 0.5) * 255;
          img.data[i + 1] = ((ny / len) * 0.5 + 0.5) * 255;
          img.data[i + 2] = ((nz / len) * 0.5 + 0.5) * 255;
          img.data[i + 3] = 255;
        }
      }
      ctx.putImageData(img, 0, 0);
    },
    size,
    repeat,
    THREE.LinearSRGBColorSpace,
  );
}

function grayscaleMapFromFn(
  fn: (u: number, v: number) => number,
  size: number,
  repeat = 1,
) {
  return canvasTexture(
    (ctx, s) => {
      const img = ctx.createImageData(s, s);
      for (let y = 0; y < s; y++) {
        for (let x = 0; x < s; x++) {
          const val = Math.max(0, Math.min(1, fn(x / s, y / s)));
          const c = val * 255;
          const i = (y * s + x) * 4;
          img.data[i] = c;
          img.data[i + 1] = c;
          img.data[i + 2] = c;
          img.data[i + 3] = 255;
        }
      }
      ctx.putImageData(img, 0, 0);
    },
    size,
    repeat,
    THREE.LinearSRGBColorSpace,
  );
}

export function createTerrainColorMap(size = 1024) {
  return canvasTexture((ctx, s) => {
    const img = ctx.createImageData(s, s);
    for (let y = 0; y < s; y++) {
      for (let x = 0; x < s; x++) {
        const u = x / s;
        const v = y / s;
        const h = terrainHeight(u, v);
        const hFine = fbm(u * 120, v * 120, 3);
        const moisture = fbm(u * 5 + 30, v * 5 + 12, 4);
        const slope = Math.abs(fbm(u * 18 + 0.5, v * 18, 4) - fbm(u * 18, v * 18 + 0.5, 4));

        let r = 42 + h * 48 + hFine * 18;
        let g = 88 + h * 62 + hFine * 14;
        let b = 32 + h * 28 + hFine * 8;

        // Lush grass meadows
        if (h > 0.42 && h < 0.72 && moisture > 0.35) {
          r = 38 + h * 32 + moisture * 18;
          g = 95 + h * 75 + moisture * 35;
          b = 28 + h * 22;
        }
        // Dry soil / paths
        if (moisture < 0.28 && h > 0.38) {
          r = 110 + h * 45 + hFine * 20;
          g = 88 + h * 35;
          b = 52 + h * 22;
        }
        // Rock / exposed earth on slopes
        if (slope > 0.12 || h > 0.78) {
          r = 115 + h * 40 + hFine * 25;
          g = 105 + h * 32;
          b = 82 + h * 20;
        }
        // Forest canopy patches
        const forest = fbm(u * 3 + 8, v * 3 + 4, 5);
        if (forest > 0.62 && h > 0.4 && h < 0.68) {
          r = 28 + forest * 22;
          g = 72 + forest * 55;
          b = 24 + forest * 18;
        }

        const i = (y * s + x) * 4;
        img.data[i] = Math.min(255, r);
        img.data[i + 1] = Math.min(255, g);
        img.data[i + 2] = Math.min(255, b);
        img.data[i + 3] = 255;
      }
    }
    ctx.putImageData(img, 0, 0);
  }, size, 5);
}

export function createTerrainNormalMap(size = 1024) {
  return normalMapFromHeight(terrainHeight, size, 3.2, 5);
}

export function createTerrainRoughnessMap(size = 512) {
  return grayscaleMapFromFn((u, v) => {
    const h = terrainHeight(u, v);
    const micro = fbm(u * 80, v * 80, 3);
    let r = 0.82 + micro * 0.12;
    if (h > 0.42 && h < 0.72) r = 0.88 + micro * 0.08;
    if (h > 0.78) r = 0.72 + micro * 0.18;
    return r;
  }, size, 5);
}

export function createTerrainAOMap(size = 512) {
  return grayscaleMapFromFn((u, v) => {
    const h = terrainHeight(u, v);
    const cavity = fbm(u * 24, v * 24, 4);
    const crevice = fbm(u * 64 + 2, v * 64 + 2, 3);
    return Math.max(0.35, Math.min(1, 0.55 + h * 0.25 + cavity * 0.15 - crevice * 0.12));
  }, size, 5);
}

function asphaltHeight(u: number, v: number) {
  return fbm(u * 48, v * 48, 4) * 0.7 + fbm(u * 120, v * 120, 2) * 0.3;
}

export function createAsphaltMap(size = 512) {
  return canvasTexture((ctx, s) => {
    const img = ctx.createImageData(s, s);
    for (let y = 0; y < s; y++) {
      for (let x = 0; x < s; x++) {
        const u = x / s;
        const v = y / s;
        const agg = fbm(u * 90, v * 90, 4);
        const crack = fbm(u * 12 + 5, v * 12, 3);
        let g = 38 + agg * 28;
        if (crack > 0.78) g += 18;
        const i = (y * s + x) * 4;
        img.data[i] = g;
        img.data[i + 1] = g + 1;
        img.data[i + 2] = g + 3;
        img.data[i + 3] = 255;
      }
    }
    ctx.putImageData(img, 0, 0);
    // Wear streaks
    ctx.strokeStyle = "rgba(255,255,255,0.03)";
    for (let i = 0; i < 14; i++) {
      ctx.beginPath();
      ctx.moveTo(0, (i / 14) * s + hash2(i, 0) * 20);
      ctx.lineTo(s, (i / 14) * s + hash2(i, 1) * 30);
      ctx.stroke();
    }
  }, size, 3);
}

export function createAsphaltNormalMap(size = 512) {
  return normalMapFromHeight(asphaltHeight, size, 4, 3);
}

export function createAsphaltRoughnessMap(size = 256) {
  return grayscaleMapFromFn((u, v) => 0.86 + fbm(u * 60, v * 60, 3) * 0.1, size, 3);
}

function concreteHeight(u: number, v: number) {
  return fbm(u * 32, v * 32, 5) * 0.65 + fbm(u * 96, v * 96, 3) * 0.35;
}

export function createConcreteMap(size = 512) {
  return canvasTexture((ctx, s) => {
    ctx.fillStyle = LANDING_PALETTE.concrete;
    ctx.fillRect(0, 0, s, s);
    const img = ctx.getImageData(0, 0, s, s);
    for (let y = 0; y < s; y++) {
      for (let x = 0; x < s; x++) {
        const u = x / s;
        const v = y / s;
        const h = concreteHeight(u, v);
        const i = (y * s + x) * 4;
        const g = 145 + h * 35;
        img.data[i] = g;
        img.data[i + 1] = g + 2;
        img.data[i + 2] = g + 4;
      }
    }
    ctx.putImageData(img, 0, 0);
    ctx.strokeStyle = "rgba(55,58,62,0.35)";
    ctx.lineWidth = 2;
    for (let i = 1; i < 4; i++) {
      const p = (i / 4) * s;
      ctx.beginPath();
      ctx.moveTo(p, 0);
      ctx.lineTo(p, s);
      ctx.stroke();
      ctx.beginPath();
      ctx.moveTo(0, p);
      ctx.lineTo(s, p);
      ctx.stroke();
    }
    ctx.fillStyle = "rgba(70,72,76,0.15)";
    for (let i = 0; i < 40; i++) {
      ctx.beginPath();
      ctx.arc(hash2(i, 2) * s, hash2(i, 3) * s, 2 + hash2(i, 4) * 6, 0, Math.PI * 2);
      ctx.fill();
    }
  }, size, 3);
}

export function createConcreteNormalMap(size = 512) {
  return normalMapFromHeight(concreteHeight, size, 3.5, 3);
}

export function createBuildingFacadeMap(size = 512) {
  return canvasTexture((ctx, s) => {
    ctx.fillStyle = "#8a929a";
    ctx.fillRect(0, 0, s, s);

    const cols = 10;
    const rows = 18;
    const padX = s * 0.04;
    const padY = s * 0.03;
    const cellW = (s - padX * 2) / cols;
    const cellH = (s - padY * 2) / rows;
    const mullion = Math.max(2, s * 0.004);

    for (let r = 0; r < rows; r++) {
      for (let c = 0; c < cols; c++) {
        const x = padX + c * cellW;
        const y = padY + r * cellH;
        const wx = x + mullion * 1.5;
        const wy = y + mullion * 2;
        const ww = cellW - mullion * 3;
        const wh = cellH - mullion * 3.5;

        ctx.fillStyle = "#6e7882";
        ctx.fillRect(x, y, cellW, cellH);

        const lit = hash2(c, r) > 0.28;
        const sky = hash2(c + 1, r + 2);
        if (lit) {
          const grd = ctx.createLinearGradient(wx, wy, wx + ww, wy + wh);
          grd.addColorStop(0, `rgba(${80 + sky * 40},${120 + sky * 50},${160 + sky * 30},0.92)`);
          grd.addColorStop(0.5, `rgba(${120 + sky * 30},${155 + sky * 40},${185 + sky * 25},0.88)`);
          grd.addColorStop(1, `rgba(${60 + sky * 25},${100 + sky * 35},${140 + sky * 35},0.9)`);
          ctx.fillStyle = grd;
        } else {
          ctx.fillStyle = "rgba(32,38,48,0.94)";
        }
        ctx.fillRect(wx, wy, ww, wh);

        if (lit) {
          ctx.fillStyle = "rgba(255,255,255,0.08)";
          ctx.fillRect(wx + 2, wy + 2, ww * 0.35, wh * 0.25);
        }
      }
      ctx.fillStyle = "rgba(55,60,68,0.7)";
      ctx.fillRect(0, padY + (r + 1) * cellH - mullion, s, mullion * 1.2);
    }
    for (let c = 0; c <= cols; c++) {
      ctx.fillStyle = "rgba(45,50,58,0.75)";
      ctx.fillRect(padX + c * cellW - mullion * 0.5, 0, mullion, s);
    }
  }, size, 1);
}

export function createBuildingRoughnessMap(size = 256) {
  return grayscaleMapFromFn((u, v) => {
    const col = Math.floor(u * 10);
    const row = Math.floor(v * 18);
    const lit = hash2(col, row) > 0.28;
    return lit ? 0.08 + fbm(u * 40, v * 40, 2) * 0.06 : 0.55 + fbm(u * 20, v * 20, 2) * 0.15;
  }, size, 1);
}

export function createBuildingNormalMap(size = 256) {
  return normalMapFromHeight(
    (u, v) => {
      const col = (u * 10) % 1;
      const row = (v * 18) % 1;
      return fbm(u * 20, v * 20, 3) * 0.5 + (col < 0.08 || row < 0.1 ? 0.35 : 0);
    },
    size,
    2.8,
    1,
  );
}

export function createTechPanelMap(size = 512) {
  return canvasTexture((ctx, s) => {
    const img = ctx.createImageData(s, s);
    for (let y = 0; y < s; y++) {
      for (let x = 0; x < s; x++) {
        const weave = hash2(Math.floor(x / 3), Math.floor(y / 3));
        const g = 34 + weave * 28 + fbm(x / s * 40, y / s * 40, 2) * 15;
        const i = (y * s + x) * 4;
        img.data[i] = g;
        img.data[i + 1] = g + 3;
        img.data[i + 2] = g + 7;
        img.data[i + 3] = 255;
      }
    }
    ctx.putImageData(img, 0, 0);
    ctx.strokeStyle = "rgba(160,180,190,0.15)";
    ctx.lineWidth = 1;
    for (let i = 1; i < 5; i++) {
      const p = (i / 5) * s;
      ctx.beginPath();
      ctx.moveTo(p, 0);
      ctx.lineTo(p, s);
      ctx.stroke();
      ctx.beginPath();
      ctx.moveTo(0, p);
      ctx.lineTo(s, p);
      ctx.stroke();
    }
  }, size, 2);
}

export function createEmissiveWindowMap(size = 512) {
  return canvasTexture((ctx, s) => {
    ctx.fillStyle = "#000000";
    ctx.fillRect(0, 0, s, s);
    const cols = 10;
    const rows = 18;
    const padX = s * 0.04;
    const padY = s * 0.03;
    const cellW = (s - padX * 2) / cols;
    const cellH = (s - padY * 2) / rows;
    for (let r = 0; r < rows; r++) {
      for (let c = 0; c < cols; c++) {
        if (hash2(c, r) <= 0.28) continue;
        const x = padX + c * cellW + cellW * 0.15;
        const y = padY + r * cellH + cellH * 0.2;
        const w = cellW * 0.7;
        const h = cellH * 0.6;
        const warm = hash2(c + 3, r + 1) > 0.5;
        ctx.fillStyle = warm
          ? `rgba(255,220,160,${0.2 + hash2(c, r + 2) * 0.35})`
          : `rgba(180,210,240,${0.15 + hash2(c, r + 2) * 0.3})`;
        ctx.fillRect(x, y, w, h);
      }
    }
  }, size, 1);
}

export function createRoofMap(size = 256) {
  return canvasTexture((ctx, s) => {
    ctx.fillStyle = "#454a52";
    ctx.fillRect(0, 0, s, s);
    for (let r = 0; r < 6; r++) {
      for (let c = 0; c < 6; c++) {
        const x = (c / 6) * s + 1;
        const y = (r / 6) * s + 1;
        const w = s / 6 - 2;
        const h = s / 6 - 2;
        const membrane = hash2(c, r) > 0.35;
        ctx.fillStyle = membrane ? "#3a3f48" : "#1a3048";
        ctx.fillRect(x, y, w, h);
        if (!membrane) {
          ctx.strokeStyle = "rgba(100,150,190,0.25)";
          for (let li = 1; li < 3; li++) {
            ctx.strokeRect(x + (w / 3) * li, y, 0.5, h);
            ctx.strokeRect(x, y + (h / 3) * li, w, 0.5);
          }
        }
      }
    }
  }, size, 1);
}

export function createWaterNormalMap(size = 512) {
  const tex = canvasTexture(
    (ctx, s) => {
      const img = ctx.createImageData(s, s);
      for (let y = 0; y < s; y++) {
        for (let x = 0; x < s; x++) {
          const u = x / s;
          const v = y / s;
          const wave =
            Math.sin(u * Math.PI * 24) * Math.cos(v * Math.PI * 20) * 0.45 +
            Math.sin(u * Math.PI * 48 + 1.4) * Math.cos(v * Math.PI * 36) * 0.28 +
            Math.sin(u * Math.PI * 80 + v * Math.PI * 60) * 0.12;
          const nx = 128 + wave * 62;
          const ny = 128 + Math.cos(u * Math.PI * 28 + 0.8) * Math.sin(v * Math.PI * 22) * 62;
          const i = (y * s + x) * 4;
          img.data[i] = nx;
          img.data[i + 1] = ny;
          img.data[i + 2] = 245;
          img.data[i + 3] = 255;
        }
      }
      ctx.putImageData(img, 0, 0);
    },
    size,
    3,
    THREE.LinearSRGBColorSpace,
  );
  tex.wrapS = tex.wrapT = THREE.RepeatWrapping;
  return tex;
}

export function createExcavationMap(size = 512) {
  return canvasTexture((ctx, s) => {
    const img = ctx.createImageData(s, s);
    for (let y = 0; y < s; y++) {
      for (let x = 0; x < s; x++) {
        const u = x / s;
        const v = y / s;
        const layer = Math.floor(v * 6);
        const grain = fbm(u * 45, v * 45, 4);
        const base = [95, 78, 58, 72, 65, 55][layer] ?? 70;
        const i = (y * s + x) * 4;
        img.data[i] = base + grain * 35;
        img.data[i + 1] = base - 12 + grain * 28;
        img.data[i + 2] = base - 28 + grain * 22;
        img.data[i + 3] = 255;
      }
    }
    ctx.putImageData(img, 0, 0);
  }, size, 2);
}

function barkHeight(u: number, v: number) {
  return fbm(u * 20, v * 6, 5) * 0.8 + Math.sin(v * Math.PI * 40) * 0.2;
}

export function createBarkMap(size = 256) {
  return canvasTexture((ctx, s) => {
    const img = ctx.createImageData(s, s);
    for (let y = 0; y < s; y++) {
      for (let x = 0; x < s; x++) {
        const h = barkHeight(x / s, y / s);
        const i = (y * s + x) * 4;
        const g = 55 + h * 45;
        img.data[i] = g + 15;
        img.data[i + 1] = g - 5;
        img.data[i + 2] = g - 20;
        img.data[i + 3] = 255;
      }
    }
    ctx.putImageData(img, 0, 0);
  }, size, 1);
}

export function createBarkNormalMap(size = 256) {
  return normalMapFromHeight(barkHeight, size, 5, 1);
}

export function createFoliageMap(size = 256) {
  return canvasTexture((ctx, s) => {
    const img = ctx.createImageData(s, s);
    for (let y = 0; y < s; y++) {
      for (let x = 0; x < s; x++) {
        const u = x / s;
        const v = y / s;
        const leaf = fbm(u * 35, v * 35, 5);
        const vein = fbm(u * 80 + 1, v * 80, 3);
        const i = (y * s + x) * 4;
        img.data[i] = 35 + leaf * 40 + vein * 15;
        img.data[i + 1] = 90 + leaf * 70 + vein * 20;
        img.data[i + 2] = 30 + leaf * 25;
        img.data[i + 3] = 255;
      }
    }
    ctx.putImageData(img, 0, 0);
  }, size, 1);
}

export type LandingTextureSet = {
  terrain: THREE.CanvasTexture;
  terrainNormal: THREE.CanvasTexture;
  terrainRoughness: THREE.CanvasTexture;
  terrainAO: THREE.CanvasTexture;
  asphalt: THREE.CanvasTexture;
  asphaltNormal: THREE.CanvasTexture;
  asphaltRoughness: THREE.CanvasTexture;
  concrete: THREE.CanvasTexture;
  concreteNormal: THREE.CanvasTexture;
  buildingFacade: THREE.CanvasTexture;
  buildingNormal: THREE.CanvasTexture;
  buildingRoughness: THREE.CanvasTexture;
  techPanel: THREE.CanvasTexture;
  emissiveWindow: THREE.CanvasTexture;
  roof: THREE.CanvasTexture;
  waterNormal: THREE.CanvasTexture;
  excavation: THREE.CanvasTexture;
  bark: THREE.CanvasTexture;
  barkNormal: THREE.CanvasTexture;
  foliage: THREE.CanvasTexture;
};

let cached: (LandingTextureSet & { __v?: number }) | null = null;

export function getLandingTextures(): LandingTextureSet {
  if (cached?.__v === TEXTURE_CACHE_VERSION) return cached;
  cached = {
    __v: TEXTURE_CACHE_VERSION,
    terrain: createTerrainColorMap(),
    terrainNormal: createTerrainNormalMap(),
    terrainRoughness: createTerrainRoughnessMap(),
    terrainAO: createTerrainAOMap(),
    asphalt: createAsphaltMap(),
    asphaltNormal: createAsphaltNormalMap(),
    asphaltRoughness: createAsphaltRoughnessMap(),
    concrete: createConcreteMap(),
    concreteNormal: createConcreteNormalMap(),
    buildingFacade: createBuildingFacadeMap(),
    buildingNormal: createBuildingNormalMap(),
    buildingRoughness: createBuildingRoughnessMap(),
    techPanel: createTechPanelMap(),
    emissiveWindow: createEmissiveWindowMap(),
    roof: createRoofMap(),
    waterNormal: createWaterNormalMap(),
    excavation: createExcavationMap(),
    bark: createBarkMap(),
    barkNormal: createBarkNormalMap(),
    foliage: createFoliageMap(),
  };
  return cached;
}

export function useLandingTextures(): LandingTextureSet {
  return useMemo(() => getLandingTextures(), []);
}
