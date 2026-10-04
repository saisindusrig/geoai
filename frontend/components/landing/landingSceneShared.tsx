"use client";

import { Suspense, useMemo, useRef } from "react";
import { useFrame } from "@react-three/fiber";
import * as THREE from "three";
import {
  LANDING_PALETTE as P,
  buildTerrainGeometry,
  buildFlatRoadGeometry,
  displaceTerrain,
  type BuildingSpec,
} from "./landingSceneUtils";
import { useLandingTextures } from "./landingSceneTextures";
import { useCoastSandTerrainTextures } from "./landingTerrainPBR";

export function SceneLighting({ shadow = true }: { shadow?: boolean }) {
  return (
    <>
      <ambientLight intensity={0.22} color="#c8dce8" />
      <hemisphereLight args={["#e8f5ec", "#1a2e24", 1.05]} />
      <directionalLight
        position={[8, 14, 6]}
        intensity={2.1}
        color="#fff5e8"
        castShadow={shadow}
        shadow-mapSize-width={4096}
        shadow-mapSize-height={4096}
        shadow-camera-far={30}
        shadow-camera-left={-8}
        shadow-camera-right={8}
        shadow-camera-top={8}
        shadow-camera-bottom={-8}
        shadow-bias={-0.0004}
      />
      <directionalLight position={[-5, 6, -4]} intensity={0.28} color="#a0d8f0" />
      <directionalLight position={[3, 2, -6]} intensity={0.18} color="#c8e8d8" />
      <pointLight position={[2, 4, 2]} intensity={0.35} color="#90c8b0" distance={14} />
    </>
  );
}

function RealisticTerrainMesh({ size = 10, segments = 192 }: { size?: number; segments?: number }) {
  const coast = useCoastSandTerrainTextures();
  const geometry = useMemo(() => buildTerrainGeometry(size, segments), [size, segments]);
  const normalScale = useMemo(() => new THREE.Vector2(1.2, 1.2), []);

  return (
    <mesh geometry={geometry} receiveShadow castShadow>
      <meshStandardMaterial
        map={coast.map}
        normalMap={coast.normalMap}
        roughnessMap={coast.roughnessMap}
        displacementMap={coast.displacementMap}
        displacementScale={0.045}
        normalScale={normalScale}
        roughness={1}
        metalness={0.02}
        envMapIntensity={0.45}
      />
    </mesh>
  );
}

function RealisticTerrainFallback({ size = 10, segments = 192 }: { size?: number; segments?: number }) {
  const textures = useLandingTextures();
  const geometry = useMemo(() => buildTerrainGeometry(size, segments), [size, segments]);

  return (
    <mesh geometry={geometry} receiveShadow castShadow>
      <meshStandardMaterial
        map={textures.terrain}
        normalMap={textures.terrainNormal}
        roughnessMap={textures.terrainRoughness}
        aoMap={textures.terrainAO}
        aoMapIntensity={1.2}
        roughness={1}
        metalness={0.02}
      />
    </mesh>
  );
}

export function RealisticTerrain({
  size = 10,
  segments = 192,
  highQuality = true,
}: {
  size?: number;
  segments?: number;
  highQuality?: boolean;
}) {
  if (!highQuality) {
    return <RealisticTerrainFallback size={size} segments={segments} />;
  }

  return (
    <Suspense fallback={<RealisticTerrainFallback size={size} segments={segments} />}>
      <RealisticTerrainMesh size={size} segments={segments} />
    </Suspense>
  );
}

export function DrapedGrid({ span = 4.5, step = 0.65 }: { span?: number; step?: number }) {
  const geometry = useMemo(() => {
    const segments: THREE.Vector3[] = [];
    const slices = Math.round((span * 2) / step);

    for (let i = 0; i <= slices; i++) {
      const a = -span + i * step;
      for (let j = 0; j < slices; j++) {
        const b0 = -span + j * step;
        const b1 = b0 + step;
        segments.push(
          new THREE.Vector3(a, displaceTerrain(a, b0) + 0.025, b0),
          new THREE.Vector3(a, displaceTerrain(a, b1) + 0.025, b1),
        );
        segments.push(
          new THREE.Vector3(b0, displaceTerrain(b0, a) + 0.025, a),
          new THREE.Vector3(b1, displaceTerrain(b1, a) + 0.025, a),
        );
      }
    }
    return new THREE.BufferGeometry().setFromPoints(segments);
  }, [span, step]);

  return (
    <lineSegments geometry={geometry}>
      <lineBasicMaterial color={P.wire} transparent opacity={0.24} />
    </lineSegments>
  );
}

/** Holographic terrain contour overlay */
export function FuturisticContourOverlay({ span = 4.5, step = 0.45 }: { span?: number; step?: number }) {
  const geometry = useMemo(() => {
    const segments: THREE.Vector3[] = [];
    const slices = Math.round((span * 2) / step);

    for (let i = 0; i <= slices; i++) {
      const a = -span + i * step;
      for (let j = 0; j < slices; j++) {
        const b0 = -span + j * step;
        const b1 = b0 + step;
        if ((i + j) % 3 !== 0) continue;
        segments.push(
          new THREE.Vector3(a, displaceTerrain(a, b0) + 0.04, b0),
          new THREE.Vector3(a, displaceTerrain(a, b1) + 0.04, b1),
        );
      }
    }
    return new THREE.BufferGeometry().setFromPoints(segments);
  }, [span, step]);

  return (
    <lineSegments geometry={geometry}>
      <lineBasicMaterial color="#7ec8b8" transparent opacity={0.2} />
    </lineSegments>
  );
}

export function WaterBody({
  cx = -1.8,
  cz = 0.6,
  rx = 1.1,
  rz = 0.75,
}: {
  cx?: number;
  cz?: number;
  rx?: number;
  rz?: number;
}) {
  const textures = useLandingTextures();
  const materialRef = useRef<THREE.MeshPhysicalMaterial>(null);
  const normalScale = useMemo(() => new THREE.Vector2(0.45, 0.45), []);
  const y = displaceTerrain(cx, cz) + 0.02;

  useFrame(({ clock }) => {
    if (!materialRef.current) return;
    const t = clock.elapsedTime * 0.06;
    textures.waterNormal.offset.set(t, t * 0.65);
  });

  return (
    <mesh position={[cx, y, cz]} rotation={[-Math.PI / 2, 0, 0]} receiveShadow>
      <circleGeometry args={[1, 96]} scale={[rx, rz, 1]} />
      <meshPhysicalMaterial
        ref={materialRef}
        color="#1e6a7a"
        normalMap={textures.waterNormal}
        normalScale={normalScale}
        transparent
        opacity={0.92}
        roughness={0.02}
        metalness={0.2}
        clearcoat={1}
        clearcoatRoughness={0.04}
        reflectivity={0.85}
        ior={1.33}
        specularIntensity={1.2}
      />
    </mesh>
  );
}

export function AsphaltRoad({
  points,
  width = 0.22,
  marking = false,
}: {
  points: THREE.Vector3[];
  width?: number;
  marking?: boolean;
}) {
  const textures = useLandingTextures();

  const { roadGeo, markingGeo } = useMemo(() => {
    const road = buildFlatRoadGeometry(points, width, { lift: 0.058, uvScale: 0.18 });
    const centerLine = marking
      ? buildFlatRoadGeometry(points, width * 0.07, { lift: 0.062, uvScale: 0.18 })
      : null;
    return { roadGeo: road, markingGeo: centerLine };
  }, [points, width, marking]);

  const normalScale = useMemo(() => new THREE.Vector2(0.6, 0.6), []);

  return (
    <group>
      <mesh geometry={roadGeo} receiveShadow castShadow>
        <meshStandardMaterial
          map={textures.asphalt}
          normalMap={textures.asphaltNormal}
          roughnessMap={textures.asphaltRoughness}
          normalScale={normalScale}
          roughness={1}
          metalness={0.04}
        />
      </mesh>
      {markingGeo && (
        <mesh geometry={markingGeo}>
          <meshStandardMaterial color={P.roadMarking} roughness={0.55} metalness={0.05} />
        </mesh>
      )}
    </group>
  );
}

export function CivilBuilding({ spec }: { spec: BuildingSpec }) {
  const textures = useLandingTextures();
  const { x, z, w, d, h, style = "mixed" } = spec;
  const baseY = displaceTerrain(x, z);
  const floors = spec.floors ?? Math.max(2, Math.round(h / 0.14));
  const floorBandHeight = h / floors;
  const normalScale = useMemo(() => new THREE.Vector2(0.35, 0.35), []);

  const facadeMat = useMemo(() => {
    if (style === "glass") {
      return new THREE.MeshPhysicalMaterial({
        map: textures.buildingFacade,
        normalMap: textures.buildingNormal,
        roughnessMap: textures.buildingRoughness,
        normalScale,
        roughness: 0.05,
        metalness: 0.35,
        clearcoat: 0.9,
        clearcoatRoughness: 0.08,
        emissiveMap: textures.emissiveWindow,
        emissive: new THREE.Color("#ffe8c8"),
        emissiveIntensity: 0.25,
        envMapIntensity: 1.2,
      });
    }
    return new THREE.MeshStandardMaterial({
      map: style === "tech" ? textures.techPanel : textures.buildingFacade,
      normalMap: textures.buildingNormal,
      roughnessMap: style === "tech" ? undefined : textures.buildingRoughness,
      normalScale,
      roughness: style === "tech" ? 0.32 : 0.45,
      metalness: style === "tech" ? 0.48 : 0.18,
      emissiveMap: textures.emissiveWindow,
      emissive: new THREE.Color("#c8dcd8"),
      emissiveIntensity: style === "mixed" ? 0.18 : 0.1,
    });
  }, [textures, style, normalScale]);

  const accentMat = useMemo(
    () =>
      new THREE.MeshStandardMaterial({
        map: textures.techPanel,
        normalMap: textures.techPanel,
        roughness: 0.28,
        metalness: 0.58,
      }),
    [textures.techPanel],
  );

  const concreteMat = useMemo(
    () =>
      new THREE.MeshStandardMaterial({
        map: textures.concrete,
        normalMap: textures.concreteNormal,
        normalScale: new THREE.Vector2(0.4, 0.4),
        roughness: 0.88,
        metalness: 0.05,
      }),
    [textures.concrete, textures.concreteNormal],
  );

  const roofMat = useMemo(
    () =>
      new THREE.MeshStandardMaterial({
        map: textures.roof,
        roughness: 0.68,
        metalness: 0.15,
      }),
    [textures.roof],
  );

  const mullionMat = useMemo(
    () => new THREE.MeshStandardMaterial({ color: "#505860", roughness: 0.45, metalness: 0.35 }),
    [],
  );

  return (
    <group position={[x, baseY, z]} rotation={[0, spec.rotation ?? 0, 0]}>
      {/* Foundation plinth */}
      <mesh position={[0, 0.05, 0]} castShadow receiveShadow material={concreteMat}>
        <boxGeometry args={[w + 0.12, 0.1, d + 0.12]} />
      </mesh>
      {/* Corner pilasters */}
      {(
        [
          [w / 2, d / 2],
          [-w / 2, d / 2],
          [w / 2, -d / 2],
          [-w / 2, -d / 2],
        ] as [number, number][]
      ).map(([px, pz], i) => (
        <mesh key={i} position={[px, h / 2 + 0.1, pz]} castShadow material={mullionMat}>
          <boxGeometry args={[0.035, h, 0.035]} />
        </mesh>
      ))}
      {/* Main tower */}
      <mesh position={[0, h / 2 + 0.1, 0]} castShadow receiveShadow material={facadeMat}>
        <boxGeometry args={[w, h, d]} />
      </mesh>
      {/* Floor slab bands */}
      {Array.from({ length: floors - 1 }, (_, i) => (
        <mesh
          key={`slab-${i}`}
          position={[0, 0.1 + (i + 1) * floorBandHeight, 0]}
          castShadow
          material={mullionMat}
        >
          <boxGeometry args={[w + 0.02, 0.018, d + 0.02]} />
        </mesh>
      ))}
      {/* Side spandrel panel */}
      {(style === "mixed" || style === "tech") && (
        <mesh position={[w / 2 + 0.003, h * 0.5 + 0.1, 0]} material={accentMat} castShadow>
          <boxGeometry args={[0.006, h * 0.55, d * 0.65]} />
        </mesh>
      )}
      {/* Roof parapet */}
      <mesh position={[0, h + 0.13, 0]} castShadow material={mullionMat}>
        <boxGeometry args={[w + 0.04, 0.06, d + 0.04]} />
      </mesh>
      <mesh position={[0, h + 0.17, 0]} castShadow material={roofMat}>
        <boxGeometry args={[w * 0.96, 0.04, d * 0.96]} />
      </mesh>
      {/* Rooftop HVAC */}
      <mesh position={[w * 0.22, h + 0.22, d * 0.12]} castShadow material={accentMat}>
        <boxGeometry args={[w * 0.2, 0.1, d * 0.16]} />
      </mesh>
      <mesh position={[-w * 0.18, h + 0.24, -d * 0.08]} castShadow>
        <cylinderGeometry args={[0.018, 0.018, 0.16, 12]} />
        <meshStandardMaterial color="#9098a0" roughness={0.35} metalness={0.72} />
      </mesh>
    </group>
  );
}

export function VegetationPatch({ positions }: { positions: [number, number][] }) {
  const textures = useLandingTextures();

  const barkMat = useMemo(
    () =>
      new THREE.MeshStandardMaterial({
        map: textures.bark,
        normalMap: textures.barkNormal,
        normalScale: new THREE.Vector2(0.8, 0.8),
        roughness: 0.94,
        metalness: 0.01,
      }),
    [textures.bark, textures.barkNormal],
  );
  const foliageMat = useMemo(
    () => new THREE.MeshStandardMaterial({ map: textures.foliage, roughness: 0.82, metalness: 0 }),
    [textures.foliage],
  );

  return (
    <group>
      {positions.map(([x, z], i) => {
        const y = displaceTerrain(x, z);
        const scale = 0.12 + (i % 3) * 0.045;
        const rot = i * 1.7;
        return (
          <group key={i} position={[x, y, z]} rotation={[0, rot, 0]}>
            <mesh position={[0, scale * 0.38, 0]} castShadow material={barkMat}>
              <cylinderGeometry args={[scale * 0.07, scale * 0.11, scale * 0.38, 12]} />
            </mesh>
            {[0.55, 0.72, 0.88].map((cy, j) => (
              <mesh
                key={j}
                position={[0, scale * cy, 0]}
                castShadow
                material={foliageMat}
                scale={[1 - j * 0.15, 1 - j * 0.1, 1 - j * 0.15]}
              >
                <icosahedronGeometry args={[scale * (0.32 - j * 0.06), 2]} />
              </mesh>
            ))}
          </group>
        );
      })}
    </group>
  );
}

export function RealisticFlyover() {
  const textures = useLandingTextures();

  const deckPoints = useMemo(
    () =>
      Array.from({ length: 16 }, (_, i) => {
        const t = i / 15;
        const x = THREE.MathUtils.lerp(-1.6, 2.3, t);
        const z = -0.35;
        const y = displaceTerrain(x, z) + 0.62 + Math.sin(t * Math.PI) * 0.12;
        return new THREE.Vector3(x, y, z);
      }),
    [],
  );

  const deckGeo = useMemo(
    () =>
      buildFlatRoadGeometry(deckPoints, 0.28, {
        drapeTerrain: false,
        lift: 0,
        segments: 140,
        uvScale: 0.12,
      }),
    [deckPoints],
  );

  const pillars = useMemo(
    () => [
      { x: -0.9, z: -0.35 },
      { x: 0.35, z: -0.35 },
      { x: 1.6, z: -0.35 },
    ],
    [],
  );

  const deckMat = useMemo(
    () =>
      new THREE.MeshStandardMaterial({
        map: textures.concrete,
        normalMap: textures.concreteNormal,
        normalScale: new THREE.Vector2(0.35, 0.35),
        roughness: 0.75,
        metalness: 0.08,
      }),
    [textures.concrete, textures.concreteNormal],
  );

  const pillarMat = useMemo(
    () =>
      new THREE.MeshStandardMaterial({
        map: textures.concrete,
        normalMap: textures.concreteNormal,
        normalScale: new THREE.Vector2(0.3, 0.3),
        roughness: 0.78,
        metalness: 0.12,
        color: new THREE.Color(P.pillar),
      }),
    [textures.concrete, textures.concreteNormal],
  );

  const guardMat = useMemo(
    () => new THREE.MeshStandardMaterial({ color: "#707880", roughness: 0.4, metalness: 0.55 }),
    [],
  );

  return (
    <group>
      <mesh geometry={deckGeo} castShadow receiveShadow material={deckMat} />
      {pillars.map(({ x, z }, i) => {
        const base = displaceTerrain(x, z);
        const top = displaceTerrain(x, z) + 0.58;
        const height = top - base;
        return (
          <group key={i} position={[x, base, z]}>
            <mesh position={[0, height / 2, 0]} castShadow material={pillarMat}>
              <cylinderGeometry args={[0.1, 0.12, height, 16]} />
            </mesh>
            <mesh position={[0, height + 0.03, 0]} castShadow material={guardMat}>
              <cylinderGeometry args={[0.13, 0.1, 0.06, 16]} />
            </mesh>
          </group>
        );
      })}
    </group>
  );
}

export function FuturisticDataNodes({ points }: { points: [number, number][] }) {
  const ref = useRef<THREE.Group>(null);

  useFrame(({ clock }) => {
    if (!ref.current) return;
    ref.current.children.forEach((child: THREE.Object3D, i: number) => {
      const mesh = child as THREE.Mesh;
      const mat = mesh.material as THREE.MeshStandardMaterial;
      mat.emissiveIntensity = 0.25 + Math.sin(clock.elapsedTime * 2 + i) * 0.15;
    });
  });

  return (
    <group ref={ref}>
      {points.map(([x, z], i) => {
        const y = displaceTerrain(x, z) + 0.35 + (i % 3) * 0.08;
        return (
          <mesh key={i} position={[x, y, z]}>
            <octahedronGeometry args={[0.04 + (i % 2) * 0.02, 0]} />
            <meshStandardMaterial
              color="#7ec8b8"
              emissive="#5a9a88"
              emissiveIntensity={0.3}
              roughness={0.2}
              metalness={0.6}
            />
          </mesh>
        );
      })}
    </group>
  );
}

export { EarthGlobe } from "./landingEarthModel";

export function RealisticSatellite() {
  const ref = useRef<THREE.Group>(null);
  const textures = useLandingTextures();

  const panelMat = useMemo(
    () =>
      new THREE.MeshStandardMaterial({
        color: "#1a3d5c",
        roughness: 0.2,
        metalness: 0.65,
        normalMap: textures.techPanel,
        normalScale: new THREE.Vector2(0.12, 0.12),
        emissive: new THREE.Color("#2a5a78"),
        emissiveIntensity: 0.15,
      }),
    [textures.techPanel],
  );

  const bodyMat = useMemo(
    () =>
      new THREE.MeshStandardMaterial({
        map: textures.techPanel,
        roughness: 0.35,
        metalness: 0.5,
        color: "#c0c5cc",
      }),
    [textures.techPanel],
  );

  useFrame(({ clock }) => {
    if (!ref.current) return;
    const t = clock.elapsedTime * 0.35;
    ref.current.position.set(Math.cos(t) * 4.2, 2.4 + Math.sin(t * 1.2) * 0.2, Math.sin(t) * 4.2);
    ref.current.rotation.y = t * 1.5;
  });

  return (
    <group ref={ref}>
      <mesh castShadow material={bodyMat}>
        <boxGeometry args={[0.22, 0.14, 0.14]} />
      </mesh>
      <mesh position={[0, 0.1, 0]} castShadow>
        <cylinderGeometry args={[0.02, 0.02, 0.12, 6]} />
        <meshStandardMaterial color="#a0a8b0" roughness={0.3} metalness={0.7} />
      </mesh>
      <mesh position={[0.28, 0, 0]} rotation={[0, 0, Math.PI / 2]} material={panelMat}>
        <boxGeometry args={[0.5, 0.02, 0.18]} />
      </mesh>
      <mesh position={[-0.28, 0, 0]} rotation={[0, 0, Math.PI / 2]} material={panelMat}>
        <boxGeometry args={[0.5, 0.02, 0.18]} />
      </mesh>
      <mesh position={[0, -0.08, 0]} rotation={[Math.PI / 2, 0, 0]}>
        <coneGeometry args={[0.04, 0.08, 6]} />
        <meshStandardMaterial color="#889098" roughness={0.35} metalness={0.55} />
      </mesh>
    </group>
  );
}

export function SiteBoundaryLoop({
  corners,
  color = P.terrainHighlight,
}: {
  corners: [number, number][];
  color?: string;
}) {
  const geometry = useMemo(() => {
    const pts = [...corners, corners[0]].map(([x, z]) => {
      const y = displaceTerrain(x, z) + 0.06;
      return new THREE.Vector3(x, y, z);
    });
    const segments: THREE.Vector3[] = [];
    for (let i = 0; i < pts.length - 1; i++) {
      segments.push(pts[i], pts[i + 1]);
    }
    return new THREE.BufferGeometry().setFromPoints(segments);
  }, [corners]);

  return (
    <lineSegments geometry={geometry}>
      <lineBasicMaterial color={color} transparent opacity={0.7} />
    </lineSegments>
  );
}

export function ExcavationPit({
  corners,
  depth = 0.12,
}: {
  corners: [number, number][];
  depth?: number;
}) {
  const textures = useLandingTextures();

  const geometry = useMemo(() => {
    const shape = new THREE.Shape();
    corners.forEach(([x, z], i) => (i === 0 ? shape.moveTo(x, z) : shape.lineTo(x, z)));
    shape.closePath();
    const geo = new THREE.ExtrudeGeometry(shape, {
      depth: depth,
      bevelEnabled: true,
      bevelThickness: 0.008,
      bevelSize: 0.008,
      bevelSegments: 2,
      steps: 2,
      curveSegments: 16,
    });
    geo.rotateX(-Math.PI / 2);
    return geo;
  }, [corners, depth]);

  const cx = corners.reduce((s, c) => s + c[0], 0) / corners.length;
  const cz = corners.reduce((s, c) => s + c[1], 0) / corners.length;
  const surfaceY = displaceTerrain(cx, cz) + 0.02;

  return (
    <mesh geometry={geometry} position={[0, surfaceY - depth, 0]} receiveShadow castShadow>
      <meshStandardMaterial
        map={textures.excavation}
        roughness={0.96}
        metalness={0.02}
      />
    </mesh>
  );
}

export function GroundShadowPlane() {
  return (
    <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.01, 0]} receiveShadow>
      <planeGeometry args={[14, 14]} />
      <shadowMaterial transparent opacity={0.22} />
    </mesh>
  );
}
