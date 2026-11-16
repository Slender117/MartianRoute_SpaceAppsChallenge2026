"use client";

import { useTexture } from "@react-three/drei";
import type { ThreeEvent } from "@react-three/fiber";
import { Suspense, useEffect, useMemo } from "react";
import { BufferAttribute, PlaneGeometry, SRGBColorSpace, type BufferGeometry, type Texture } from "three";

import { assetUrl } from "@/lib/api";
import { regionFrame, TERRAIN_SIZE } from "@/lib/geo";
import { useMapStore } from "@/lib/store";
import type { LatLon, RegionManifest } from "@/lib/types";

import { useRegionExtras, useRegionHeights } from "./regionAssets";
import { SafeReturnVeil, type Displacement } from "./SafeReturnVeil";

// Color of the grayscale orthophoto: it tints it with the Martian soil tone (visual only).
const SOIL_TINT = "#e3a27a";
const SOIL_COLOR = "#c1643c";

/**
 * Region terrain with its layers fused on top, like geologic unit views: a mesh with
 * the real relief (heightmap.bin), the orthophoto as a texture and each active layer as a
 * semi-transparent veil over the same geometry. Older regions without heightmap.bin use the
 * heightmap.png como displacementMap.
 *
 * Loads in parts: the relief appears as soon as the heights arrive, the orthophoto goes on top
 * when it downloads, and each layer downloads the first time it is turned on.
 */
export function RegionTerrain({ exaggeration, layerOpacity = 0.75 }: { exaggeration: number; layerOpacity?: number }) {
  const manifest = useMapStore((s) => s.manifest)!;
  const extras = useRegionExtras(manifest.id);
  const heights = useRegionHeights(manifest, extras);

  if (!extras) return null;
  if (!extras.assets?.heightmap) {
    return (
      <Suspense fallback={null}>
        <DisplacedTerrain
          key={manifest.id}
          manifest={manifest}
          exaggeration={exaggeration}
          layerOpacity={layerOpacity}
        />
      </Suspense>
    );
  }
  if (!heights) return null;
  return (
    <MeshTerrain
      key={manifest.id}
      manifest={manifest}
      heights={heights}
      exaggeration={exaggeration}
      layerOpacity={layerOpacity}
      orthoPath={extras.assets.ortho?.path}
    />
  );
}

/**
 * The layers and the orthophoto are in sRGB: without this they look washed out and do not match the legend.
 * A fixed function (not an arrow on every render): useTexture calls it again if it changes.
 */
function prepareColorTexture(t: Texture | Texture[]) {
  for (const texture of Array.isArray(t) ? t : [t]) {
    if (texture.colorSpace === SRGBColorSpace) continue;
    texture.colorSpace = SRGBColorSpace;
    texture.anisotropy = 8;
    texture.needsUpdate = true;
  }
}

/** Marks the relief as visible while the component is mounted (loading notice). */
function useTerrainReady() {
  const setTerrainReady = useMapStore((s) => s.setTerrainReady);
  useEffect(() => {
    setTerrainReady(true);
    return () => setTerrainReady(false);
  }, [setTerrainReady]);
}

type PickHandler = (e: ThreeEvent<MouseEvent>) => void;

function usePickHandler(fromScene: (p: ThreeEvent<MouseEvent>["point"]) => LatLon): PickHandler {
  const pickPoint = useMapStore((s) => s.pickPoint);
  return (e) => {
    e.stopPropagation();
    pickPoint(fromScene(e.point));
  };
}

function MeshTerrain({
  manifest,
  heights,
  exaggeration,
  layerOpacity,
  orthoPath,
}: {
  manifest: RegionManifest;
  heights: Float32Array;
  exaggeration: number;
  layerOpacity: number;
  orthoPath?: string;
}) {
  const frame = useMemo(() => regionFrame(manifest, exaggeration), [manifest, exaggeration]);
  const onClick = usePickHandler(frame.fromScene);
  useTerrainReady();

  // One vertex per grid cell; the ground and the veils share the same geometry.
  const geometry = useMemo(() => {
    const [h, w] = manifest.shape;
    const [zMin, zMax] = manifest.elevation_range;
    const g = new PlaneGeometry(TERRAIN_SIZE, TERRAIN_SIZE, w - 1, h - 1);
    const pos = g.attributes.position as BufferAttribute;
    const k = frame.heightScale / Math.max(zMax - zMin, 1e-6);
    for (let i = 0; i < heights.length; i++) pos.setZ(i, (heights[i] - zMin) * k);
    pos.needsUpdate = true;
    g.computeVertexNormals();
    g.computeBoundingBox();
    g.computeBoundingSphere();
    return g;
  }, [manifest, heights, frame]);
  useEffect(() => () => geometry.dispose(), [geometry]);

  const ground = <Ground geometry={geometry} onClick={onClick} />;
  return (
    <group rotation={[-Math.PI / 2, 0, 0]}>
      {orthoPath ? (
        <Suspense fallback={ground}>
          <OrthoGround url={assetUrl(manifest.id, orthoPath)} geometry={geometry} onClick={onClick} />
        </Suspense>
      ) : (
        ground
      )}
      <Veils manifest={manifest} geometry={geometry} opacity={layerOpacity} />
    </group>
  );
}

/** Plain-colored ground: while the orthophoto arrives, or if the region has none. */
function Ground({ geometry, onClick }: { geometry: BufferGeometry; onClick: PickHandler }) {
  return (
    <mesh geometry={geometry} onClick={onClick}>
      <meshStandardMaterial color={SOIL_COLOR} roughness={1} metalness={0} />
    </mesh>
  );
}

function OrthoGround({ url, geometry, onClick }: { url: string; geometry: BufferGeometry; onClick: PickHandler }) {
  const map = useTexture(url, prepareColorTexture) as Texture;
  return (
    <mesh geometry={geometry} onClick={onClick}>
      <meshStandardMaterial map={map} color={SOIL_TINT} roughness={1} metalness={0} />
    </mesh>
  );
}

/** The active layers as veils over the relief and, above them all, the safe-return map. */
function Veils({
  manifest,
  geometry,
  opacity,
  displacement,
}: {
  manifest: RegionManifest;
  geometry: BufferGeometry;
  opacity: number;
  displacement?: Displacement;
}) {
  const activeLayers = useMapStore((s) => s.activeLayers);
  return (
    <>
      {activeLayers.map((layer, i) => (
        // Each layer in its own Suspense: while it downloads, the rest of the scene stays the same.
        <Suspense key={layer} fallback={null}>
          <LayerVeil
            url={assetUrl(manifest.id, `textures/${layer}.png`)}
            geometry={geometry}
            order={i + 1}
            opacity={opacity}
            displacement={displacement}
          />
        </Suspense>
      ))}
      <SafeReturnVeil
        geometry={geometry}
        order={activeLayers.length + 1}
        opacity={opacity}
        displacement={displacement}
      />
    </>
  );
}

function LayerVeil({
  url,
  geometry,
  order,
  opacity,
  displacement,
}: {
  url: string;
  geometry: BufferGeometry;
  order: number;
  opacity: number;
  displacement?: Displacement;
}) {
  const map = useTexture(url, prepareColorTexture) as Texture;
  return (
    <mesh geometry={geometry} renderOrder={order}>
      {/* Lambert, not Basic: MeshBasicMaterial does not support displacementMap */}
      <meshLambertMaterial
        map={map}
        transparent
        opacity={opacity}
        depthWrite={false}
        polygonOffset
        polygonOffsetFactor={-order}
        {...displacement}
      />
    </mesh>
  );
}

const LEGACY_SEGMENTS = 192;

/** Regions published before heightmap.bin: the 16-bit PNG displaces a plane. */
function DisplacedTerrain({
  manifest,
  exaggeration,
  layerOpacity,
}: {
  manifest: RegionManifest;
  exaggeration: number;
  layerOpacity: number;
}) {
  const frame = useMemo(() => regionFrame(manifest, exaggeration), [manifest, exaggeration]);
  const onClick = usePickHandler(frame.fromScene);
  const heightmap = useTexture(assetUrl(manifest.id, "heightmap.png")) as Texture;
  useTerrainReady();

  const geometry = useMemo(() => new PlaneGeometry(TERRAIN_SIZE, TERRAIN_SIZE, LEGACY_SEGMENTS, LEGACY_SEGMENTS), []);
  useEffect(() => () => geometry.dispose(), [geometry]);
  const displacement = useMemo(
    () => ({ displacementMap: heightmap, displacementScale: frame.heightScale }),
    [heightmap, frame.heightScale],
  );

  return (
    <group rotation={[-Math.PI / 2, 0, 0]}>
      <mesh geometry={geometry} onClick={onClick}>
        <meshStandardMaterial color={SOIL_COLOR} roughness={1} flatShading {...displacement} />
      </mesh>
      <Veils manifest={manifest} geometry={geometry} opacity={layerOpacity} displacement={displacement} />
    </group>
  );
}
