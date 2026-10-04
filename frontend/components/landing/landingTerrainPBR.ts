"use client";

import { useMemo } from "react";
import { useLoader } from "@react-three/fiber";
import * as THREE from "three";
import { EXRLoader } from "three/addons/loaders/EXRLoader.js";

const TERRAIN_TEX_BASE = "/textures/coast_sand_rocks_02/textures";
const UV_REPEAT = 5;

function configureTerrainTexture(tex: THREE.Texture, colorSpace?: THREE.ColorSpace) {
  tex.wrapS = tex.wrapT = THREE.RepeatWrapping;
  tex.repeat.set(UV_REPEAT, UV_REPEAT);
  tex.anisotropy = 16;
  tex.minFilter = THREE.LinearMipmapLinearFilter;
  tex.magFilter = THREE.LinearFilter;
  tex.generateMipmaps = true;
  if (colorSpace) tex.colorSpace = colorSpace;
  return tex;
}

export type CoastSandTerrainMaps = {
  map: THREE.Texture;
  normalMap: THREE.Texture;
  roughnessMap: THREE.Texture;
  displacementMap: THREE.Texture;
};

export function useCoastSandTerrainTextures(): CoastSandTerrainMaps {
  const [colorMap, displacementMap] = useLoader(THREE.TextureLoader, [
    `${TERRAIN_TEX_BASE}/coast_sand_rocks_02_diff_1k.jpg`,
    `${TERRAIN_TEX_BASE}/coast_sand_rocks_02_disp_1k.png`,
  ]);

  const [normalMap, roughnessMap] = useLoader(EXRLoader, [
    `${TERRAIN_TEX_BASE}/coast_sand_rocks_02_nor_gl_1k.exr`,
    `${TERRAIN_TEX_BASE}/coast_sand_rocks_02_rough_1k.exr`,
  ]);

  return useMemo(() => {
    configureTerrainTexture(colorMap, THREE.SRGBColorSpace);
    configureTerrainTexture(displacementMap);
    configureTerrainTexture(normalMap, THREE.LinearSRGBColorSpace);
    configureTerrainTexture(roughnessMap, THREE.LinearSRGBColorSpace);
    return { map: colorMap, normalMap, roughnessMap, displacementMap };
  }, [colorMap, displacementMap, normalMap, roughnessMap]);
}
