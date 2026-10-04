"use client";

import { Canvas, useLoader, useThree } from "@react-three/fiber";
import { Suspense, useEffect, useMemo } from "react";
import * as THREE from "three";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";
import type { ConstructionSpec, ConstructionStage } from "@/lib/construction";

const DUMMY_BRIDGE_NATIVE_LENGTH = 405.52701950073197;

function ImportedConstructionModel({
  url,
  targetLengthM,
}: {
  url: string;
  targetLengthM: number;
}) {
  const gltf = useLoader(GLTFLoader, url);
  const normalized = useMemo(() => {
    const object = gltf.scene.clone(true);
    object.traverse((child) => {
      if (child instanceof THREE.Mesh) {
        child.castShadow = true;
        child.receiveShadow = true;
      }
    });
    const box = new THREE.Box3().setFromObject(object);
    const center = box.getCenter(new THREE.Vector3());
    const size = box.getSize(new THREE.Vector3());
    object.position.set(-center.x, -box.min.y, -center.z);
    return { object, nativeLength: Math.max(size.x, size.z) };
  }, [gltf.scene]);
  const scale =
    targetLengthM /
    (normalized.nativeLength || DUMMY_BRIDGE_NATIVE_LENGTH);

  return (
    <group rotation={[0, -Math.PI / 2, 0]} scale={scale}>
      <primitive object={normalized.object} />
    </group>
  );
}

function Box({
  position,
  size,
  color,
}: {
  position: [number, number, number];
  size: [number, number, number];
  color: string;
}) {
  return (
    <mesh position={position} castShadow receiveShadow>
      <boxGeometry args={size} />
      <meshStandardMaterial color={color} roughness={0.72} />
    </mesh>
  );
}

function ConstructionModel({
  spec,
  stage,
}: {
  spec: ConstructionSpec;
  stage: ConstructionStage;
}) {
  const showFoundation = stage !== "site";
  const showStructure = stage === "structure" || stage === "finish";
  const showFinish = stage === "finish";
  const base = "#48504c";
  const primary = "#b2bbab";
  const secondary = "#8ea0a3";

  if (spec.project_type === "building") {
    const floors = Math.max(3, Math.round(spec.height_m / 4));
    return (
      <group>
        {showFoundation && (
          <Box
            position={[0, 0.5, 0]}
            size={[spec.width_m, 1, spec.length_m]}
            color={base}
          />
        )}
        {showStructure && (
          <Box
            position={[0, spec.height_m / 2 + 1, 0]}
            size={[spec.width_m, spec.height_m, spec.length_m]}
            color={primary}
          />
        )}
        {showFinish &&
          Array.from({ length: floors - 1 }, (_, index) => (
            <Box
              key={index}
              position={[0, 2 + (index + 1) * (spec.height_m / floors), 0]}
              size={[spec.width_m + 0.2, 0.25, spec.length_m + 0.2]}
              color={secondary}
            />
          ))}
      </group>
    );
  }
  if (spec.project_type === "road") {
    return (
      <group>
        {showFoundation && (
          <Box
            position={[0, 0.2, 0]}
            size={[spec.width_m + 3, 0.4, spec.length_m]}
            color={base}
          />
        )}
        {showStructure && (
          <Box
            position={[0, 0.5, 0]}
            size={[spec.width_m, 0.3, spec.length_m]}
            color={secondary}
          />
        )}
        {showFinish && (
          <Box
            position={[0, 0.7, 0]}
            size={[0.18, 0.05, spec.length_m * 0.9]}
            color={primary}
          />
        )}
      </group>
    );
  }
  if (spec.project_type === "pipeline") {
    return (
      <group>
        {showFoundation && (
          <Box
            position={[0, 0.2, 0]}
            size={[spec.width_m + 4, 0.4, spec.length_m]}
            color={base}
          />
        )}
        {showStructure && (
          <mesh
            rotation={[Math.PI / 2, 0, 0]}
            position={[0, 1.2, 0]}
            castShadow
          >
            <cylinderGeometry args={[1.1, 1.1, spec.length_m, 20]} />
            <meshStandardMaterial color={secondary} roughness={0.48} />
          </mesh>
        )}
        {showFinish &&
          Array.from({ length: 4 }, (_, index) => (
            <Box
              key={index}
              position={[
                0,
                1.1,
                -spec.length_m / 2 + ((index + 1) * spec.length_m) / 5,
              ]}
              size={[3, 2, 0.8]}
              color={primary}
            />
          ))}
      </group>
    );
  }
  if (spec.project_type === "dam") {
    return (
      <group>
        {showFoundation && (
          <Box
            position={[0, 0.6, 0]}
            size={[spec.length_m + 18, 1.2, spec.width_m + 12]}
            color={base}
          />
        )}
        {showStructure && (
          <Box
            position={[0, spec.height_m / 2 + 1, 0]}
            size={[spec.length_m, spec.height_m, spec.width_m]}
            color={primary}
          />
        )}
        {showFinish && (
          <Box
            position={[0, spec.height_m + 1.5, 0]}
            size={[spec.length_m * 0.28, 1, spec.width_m + 1]}
            color={secondary}
          />
        )}
      </group>
    );
  }

  const supportCount =
    spec.project_type === "flyover"
      ? Math.max(2, spec.supports)
      : Math.max(0, spec.supports);
  return (
    <group>
      {showFoundation &&
        Array.from({ length: supportCount }, (_, index) => (
          <Box
            key={index}
            position={[
              0,
              1,
              -spec.length_m / 2 +
                ((index + 1) * spec.length_m) / (supportCount + 1),
            ]}
            size={[3, 2, 3]}
            color={base}
          />
        ))}
      {showStructure && (
        <>
          <Box
            position={[0, spec.height_m, 0]}
            size={[spec.width_m, 0.9, spec.length_m]}
            color={primary}
          />
          {Array.from({ length: supportCount }, (_, index) => (
            <Box
              key={index}
              position={[
                0,
                spec.height_m / 2,
                -spec.length_m / 2 +
                  ((index + 1) * spec.length_m) / (supportCount + 1),
              ]}
              size={[1.6, spec.height_m, 1.6]}
              color={secondary}
            />
          ))}
        </>
      )}
      {showFinish && (
        <>
          <Box
            position={[-spec.width_m / 2, spec.height_m + 1, 0]}
            size={[0.16, 1.1, spec.length_m]}
            color={secondary}
          />
          <Box
            position={[spec.width_m / 2, spec.height_m + 1, 0]}
            size={[0.16, 1.1, spec.length_m]}
            color={secondary}
          />
        </>
      )}
    </group>
  );
}

function GalleryCamera({spec}:{spec:ConstructionSpec}) {
  const {camera,size,invalidate}=useThree();
  useEffect(()=>{
    const extent=Math.max(spec.length_m,spec.width_m,spec.height_m);
    const targetY=spec.project_type==="road"||spec.project_type==="pipeline"?1:spec.height_m*.45;
    const aspect=size.width / Math.max(1,size.height);
    const distance=extent*(spec.project_type==="building"?1.2:Math.max(.62,1.15/aspect));
    const elevatedCrossing=spec.project_type==="bridge"||spec.project_type==="flyover";
    camera.position.set(distance*.85,distance*(elevatedCrossing?.30:.55),distance*.42);
    camera.lookAt(0,targetY,0);camera.updateProjectionMatrix();invalidate();
  },[camera,size.width,size.height,spec,invalidate]);
  return null;
}

function GalleryDam({spec}:{spec:ConstructionSpec}) {
  const geometry=useMemo(()=>{const shape=new THREE.Shape();shape.moveTo(-spec.width_m*.5,0);shape.lineTo(-spec.width_m*.5,spec.height_m);shape.lineTo(-spec.width_m*.25,spec.height_m);shape.lineTo(spec.width_m*.5,0);shape.closePath();const geo=new THREE.ExtrudeGeometry(shape,{depth:spec.length_m,bevelEnabled:false});geo.rotateY(Math.PI/2);geo.translate(-spec.length_m/2,0,0);return geo;},[spec]);
  useEffect(()=>()=>geometry.dispose(),[geometry]);
  return <group><mesh geometry={geometry}><meshStandardMaterial color="#b2bbab" roughness={.8}/></mesh><Box position={[0,spec.height_m*.68,spec.width_m*1.2]} size={[spec.length_m*1.1,.15,spec.width_m*1.4]} color="#456f73"/></group>;
}

export default function ConstructionScene({
  spec,
  stage,
  preview = false,
  modelUrl,
}: {
  spec: ConstructionSpec;
  stage: ConstructionStage;
  /** Lower-cost camera and pixel density for gallery cards. */
  preview?: boolean;
  /** Optional real model used only by the local dummy workspace. */
  modelUrl?: string;
}) {
  const extent = Math.max(spec.length_m, spec.width_m, spec.height_m);
  const previewExtent = Math.hypot(spec.length_m, spec.width_m, spec.height_m);
  const cameraExtent = preview ? previewExtent : extent;
  return (
    <Canvas
      frameloop={preview?"demand":"always"}
      shadows={!preview}
      camera={{
        position: [cameraExtent * 0.7, cameraExtent * 0.45, cameraExtent * 0.8],
        fov: preview ? 46 : 42,
      }}
      dpr={preview ? [1, 1] : [1, 1.5]}
    >
      <color attach="background" args={["#0e100f"]} />
      {preview&&<GalleryCamera spec={spec}/>}
      <fog attach="fog" args={["#0e100f", extent * 0.7, extent * 2.8]} />
      <ambientLight intensity={1.2} />
      <directionalLight
        position={[20, 32, 18]}
        intensity={2}
        castShadow={!preview}
      />
      <gridHelper
        args={[Math.max(80, extent * 1.5), 20, "#4b5c58", "#1e2423"]}
        position={[0, 0, 0]}
      />
      {modelUrl && (stage === "structure" || stage === "finish") ? (
        <Suspense fallback={null}>
          <ImportedConstructionModel
            url={modelUrl}
            targetLengthM={spec.length_m}
          />
        </Suspense>
      ) : (
        preview&&spec.project_type==="dam"?<GalleryDam spec={spec}/>:preview&&spec.project_type==="building"?<group><group position={[-spec.width_m*.28,0,0]} scale={[.45,1,.85]}><ConstructionModel spec={spec} stage={stage}/></group><group position={[spec.width_m*.24,0,-spec.length_m*.18]} scale={[.45,.65,.48]}><ConstructionModel spec={spec} stage={stage}/></group><group position={[spec.width_m*.24,0,spec.length_m*.23]} scale={[.45,.4,.3]}><ConstructionModel spec={spec} stage={stage}/></group></group>:<ConstructionModel spec={spec} stage={stage} />
      )}
    </Canvas>
  );
}

