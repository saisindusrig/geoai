"use client";

import { Suspense, useMemo, useRef } from "react";
import { useFrame, useLoader } from "@react-three/fiber";
import * as THREE from "three";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";

export const CLOUD_GLB_URL = "/models/fluffy_cloud.glb";

const TARGET_CLOUD_WIDTH = 2.6;

const CLOUD_INSTANCES: {
  position: [number, number, number];
  scale: number;
  drift: number;
  rotation: number;
}[] = [
  { position: [-5.5, 4.2, -3.8], scale: 1.35, drift: 0.018, rotation: 0.4 },
  { position: [4.8, 3.6, -2.2], scale: 1.1, drift: 0.014, rotation: 1.2 },
  { position: [1.2, 5.1, -6.5], scale: 1.55, drift: 0.012, rotation: 2.1 },
  { position: [-2.4, 3.9, 4.2], scale: 1.0, drift: 0.016, rotation: 0.8 },
  { position: [6.2, 4.8, 2.5], scale: 0.95, drift: 0.02, rotation: 1.7 },
  { position: [-7.0, 5.4, 1.0], scale: 1.25, drift: 0.011, rotation: 2.6 },
  { position: [0.5, 6.2, 0.0], scale: 1.8, drift: 0.009, rotation: 0.2 },
  { position: [-3.8, 5.8, -5.2], scale: 1.15, drift: 0.013, rotation: 1.5 },
];

function prepareCloudRoot(gltf: { scene: THREE.Group }) {
  const root = gltf.scene.clone(true);
  root.traverse((child) => {
    if (!(child instanceof THREE.Mesh)) return;
    child.castShadow = false;
    child.receiveShadow = false;
    const mats = Array.isArray(child.material) ? child.material : [child.material];
    for (const mat of mats) {
      if (mat instanceof THREE.MeshStandardMaterial || mat instanceof THREE.MeshPhysicalMaterial) {
        mat.transparent = true;
        mat.depthWrite = false;
        mat.roughness = 1;
        mat.metalness = 0;
        mat.side = THREE.DoubleSide;
      }
    }
  });

  const box = new THREE.Box3().setFromObject(root);
  const size = box.getSize(new THREE.Vector3());
  const maxDim = Math.max(size.x, size.y, size.z) || 1;
  root.scale.setScalar(TARGET_CLOUD_WIDTH / maxDim);
  box.setFromObject(root);
  root.position.sub(box.getCenter(new THREE.Vector3()));
  return root;
}

function CloudInstance({
  template,
  position,
  scale,
  drift,
  rotation,
}: {
  template: THREE.Group;
  position: [number, number, number];
  scale: number;
  drift: number;
  rotation: number;
}) {
  const ref = useRef<THREE.Group>(null);
  const cloud = useMemo(() => template.clone(true), [template]);

  useFrame((_, delta) => {
    if (!ref.current) return;
    ref.current.position.x += delta * drift;
    if (ref.current.position.x > 10) ref.current.position.x -= 20;
  });

  return (
    <group ref={ref} position={position} scale={scale} rotation={[0, rotation, 0]}>
      <primitive object={cloud} />
    </group>
  );
}

function SkyDome() {
  return (
    <>
      <mesh>
        <sphereGeometry args={[42, 32, 24]} />
        <meshBasicMaterial color="#1c2a35" side={THREE.BackSide} fog={false} />
      </mesh>
      <mesh rotation={[Math.PI / 2, 0, 0]} position={[0, 8, 0]}>
        <circleGeometry args={[28, 48]} />
        <meshBasicMaterial
          color="#2a3d4a"
          transparent
          opacity={0.35}
          side={THREE.DoubleSide}
          fog={false}
        />
      </mesh>
    </>
  );
}

function FluffyCloudsInner() {
  const gltf = useLoader(GLTFLoader, CLOUD_GLB_URL);
  const template = useMemo(() => prepareCloudRoot(gltf), [gltf]);

  return (
    <>
      {CLOUD_INSTANCES.map((instance, i) => (
        <CloudInstance key={i} template={template} {...instance} />
      ))}
    </>
  );
}

/** Sky dome with drifting fluffy_cloud.glb instances */
export function SkyClouds() {
  return (
    <>
      <SkyDome />
      <Suspense fallback={null}>
        <FluffyCloudsInner />
      </Suspense>
    </>
  );
}

useLoader.preload(GLTFLoader, CLOUD_GLB_URL);
