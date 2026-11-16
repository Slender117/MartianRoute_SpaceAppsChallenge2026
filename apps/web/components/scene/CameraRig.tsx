"use client";

import { OrbitControls } from "@react-three/drei";
import { useFrame, useThree } from "@react-three/fiber";
import { useEffect, useMemo } from "react";
import { Vector3 } from "three";

import { bboxCenter, latLonToSphere, TERRAIN_SIZE } from "@/lib/geo";
import { useMapStore } from "@/lib/store";

const GLOBE_POSE = new Vector3(0, 0, 3.2);
const ORIGIN = new Vector3(0, 0, 0);
const REGION_POSE = new Vector3(0, TERRAIN_SIZE * 0.6, TERRAIN_SIZE * 0.9);
// Portrait phone screen: higher and farther, looking a little south of the center.
const PORTRAIT_POSE = new Vector3(0, TERRAIN_SIZE * 1.3, TERRAIN_SIZE * 1.2);
const PORTRAIT_TARGET = new Vector3(0, 0, TERRAIN_SIZE * 0.25);

/**
 * Pose on arriving at the region, by screen aspect. In portrait the horizontal field of view
 * is narrow: the camera rises and moves back so the terrain fits the width, and it points
 * south of the center so the site stays above the panel sheet.
 */
function regionPose(aspect: number) {
  const t = Math.min(Math.max((1 - aspect) / 0.55, 0), 1); // 0 = cuadrada o ancha, 1 = celular vertical
  return {
    position: REGION_POSE.clone().lerp(PORTRAIT_POSE, t),
    target: ORIGIN.clone().lerp(PORTRAIT_TARGET, t),
  };
}

/**
 * Continuous globe → region transition: the camera approaches the site and, on arrival,
 * the globe is swapped for the detailed terrain.
 * TODO(3D): replace the lerp with the Theatre.js sequence (lib/theatre.ts) for the demo.
 */
export function CameraRig() {
  const camera = useThree((s) => s.camera);
  const get = useThree((s) => s.get);
  const invalidate = useThree((s) => s.invalidate);
  const controls = useThree((s) => s.controls) as unknown as { target: Vector3; update: () => void } | null;
  const view = useMapStore((s) => s.view);
  const regions = useMapStore((s) => s.regions);
  const regionId = useMapStore((s) => s.regionId);
  const manifest = useMapStore((s) => s.manifest);
  const arriveAtRegion = useMapStore((s) => s.arriveAtRegion);

  const zoomTarget = useMemo(() => {
    const r = regions.find((x) => x.id === regionId);
    return r ? latLonToSphere(bboxCenter(r.bbox), 1.15) : null;
  }, [regions, regionId]);

  useEffect(() => {
    // The aspect is only read when the view changes: rotating the phone does not move the camera
    // the user already set.
    const { width, height } = get().size;
    const pose = view === "region" ? regionPose(width / Math.max(height, 1)) : { position: GLOBE_POSE, target: ORIGIN };
    if (view !== "zooming") {
      camera.position.copy(pose.position);
      camera.lookAt(pose.target);
    } else {
      camera.lookAt(ORIGIN);
    }
    // OrbitControls keeps its own distance: it has to be synced with the new pose.
    controls?.target.copy(view === "zooming" ? ORIGIN : pose.target);
    controls?.update();
    // In the region the scene is drawn on demand: the new pose needs its frame.
    invalidate();
  }, [view, camera, controls, invalidate, get]);

  useFrame((_, dt) => {
    if (view !== "zooming" || !zoomTarget) return;
    camera.position.lerp(zoomTarget, 1 - Math.exp(-dt * 2.5));
    camera.lookAt(0, 0, 0);
    if (manifest && camera.position.distanceTo(zoomTarget) < 0.02) arriveAtRegion();
  });

  return (
    <OrbitControls
      makeDefault
      enabled={view !== "zooming"}
      enablePan={view === "region"}
      minDistance={view === "globe" ? 1.3 : 1}
      maxDistance={view === "globe" ? 8 : TERRAIN_SIZE * 2.5}
      maxPolarAngle={view === "region" ? Math.PI / 2.1 : Math.PI}
    />
  );
}
