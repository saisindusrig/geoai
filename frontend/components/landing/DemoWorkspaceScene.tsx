"use client";

import { useMemo, useRef } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import * as THREE from "three";
import { LANDING_PALETTE as P, displaceTerrain, sampleRoadPoints, WORKSPACE_BUILDINGS } from "./landingSceneUtils";
import {
  AsphaltRoad,
  CivilBuilding,
  DrapedGrid,
  ExcavationPit,
  FuturisticContourOverlay,
  FuturisticDataNodes,
  GroundShadowPlane,
  RealisticFlyover,
  RealisticTerrain,
  SceneLighting,
  SiteBoundaryLoop,
  VegetationPatch,
  WaterBody,
} from "./landingSceneShared";

const SITE_CORNERS: [number, number][] = [
  [-2.8, -2.2],
  [2.6, -1.8],
  [3.1, 2.4],
  [-2.2, 2.8],
];

const EXCAVATION_CORNERS: [number, number][] = [
  [-2.4, 0.2],
  [-1.2, 0.5],
  [-0.9, 1.6],
  [-2.1, 1.4],
];

function SweepBeam() {
  const ref = useRef<THREE.Mesh>(null);

  useFrame(({ clock }) => {
    if (!ref.current) return;
    const t = clock.elapsedTime * 0.32;
    ref.current.position.x = Math.sin(t) * 2.8;
    ref.current.position.z = Math.cos(t * 0.75) * 2.0;
    ref.current.position.y = displaceTerrain(ref.current.position.x, ref.current.position.z) + 0.12;
  });

  return (
    <mesh ref={ref} rotation={[-Math.PI / 2, 0, 0]}>
      <ringGeometry args={[0.12, 1.4, 32, 1, 0, Math.PI * 0.3]} />
      <meshBasicMaterial color={P.terrainHighlight} transparent opacity={0.14} side={THREE.DoubleSide} />
    </mesh>
  );
}

function SceneRig() {
  const ref = useRef<THREE.Group>(null);

  const primaryRoad = useMemo(
    () =>
      sampleRoadPoints(24, (t) => ({
        x: THREE.MathUtils.lerp(-3, 3.2, t),
        z: Math.sin(t * Math.PI * 1.2) * 1.8,
      })),
    [],
  );

  const secondaryRoad = useMemo(
    () =>
      sampleRoadPoints(16, (t) => ({
        x: 0.4 + Math.sin(t * Math.PI) * 1.2,
        z: THREE.MathUtils.lerp(-2.5, 2.2, t),
      })),
    [],
  );

  const trees = useMemo<[number, number][]>(
    () => [
      [-2.0, 2.1],
      [2.5, 1.8],
      [2.8, -0.8],
      [-1.8, -1.5],
      [0.5, 2.3],
      [1.2, -1.9],
      [-0.5, -2.0],
      [1.8, 2.0],
    ],
    [],
  );

  const dataNodes = useMemo<[number, number][]>(
    () => [
      [-1.8, 0.8],
      [0.8, 0.4],
      [2.0, 1.5],
      [-0.5, 1.8],
      [1.5, -0.6],
      [-2.0, -0.8],
    ],
    [],
  );

  useFrame(({ clock }) => {
    if (!ref.current) return;
    ref.current.rotation.y = Math.sin(clock.elapsedTime * 0.12) * 0.28;
  });

  return (
    <group ref={ref}>
      <RealisticTerrain size={10} segments={192} />
      <GroundShadowPlane />
      <DrapedGrid />
      <FuturisticContourOverlay />
      <WaterBody cx={2.0} cz={-1.4} rx={0.75} rz={0.55} />
      <SiteBoundaryLoop corners={SITE_CORNERS} />
      <ExcavationPit corners={EXCAVATION_CORNERS} />
      <AsphaltRoad points={primaryRoad} width={0.2} marking />
      <AsphaltRoad points={secondaryRoad} width={0.14} />
      <RealisticFlyover />
      {WORKSPACE_BUILDINGS.map((b) => (
        <CivilBuilding key={`${b.x}-${b.z}`} spec={b} />
      ))}
      <VegetationPatch positions={trees} />
      <FuturisticDataNodes points={dataNodes} />
      <SweepBeam />
    </group>
  );
}

export default function DemoWorkspaceScene() {
  return (
    <Canvas
      camera={{ position: [6.2, 6.8, 6.2], fov: 36, near: 0.1, far: 100 }}
      dpr={[1, 2]}
      shadows
      gl={{
        alpha: true,
        antialias: true,
        toneMapping: THREE.ACESFilmicToneMapping,
        toneMappingExposure: 1.15,
      }}
      style={{ background: "transparent" }}
    >
      <SceneLighting />
      <fog attach="fog" args={["#dff8ea", 14, 24]} />
      <SceneRig />
    </Canvas>
  );
}
