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

// Color de la ortofoto en escala de grises: la tiñe del tono del suelo marciano (solo visual).
const SOIL_TINT = "#e3a27a";
const SOIL_COLOR = "#c1643c";

/**
 * Terreno de la región con sus capas fusionadas encima, como en las vistas de unidades geológicas:
 * malla con el relieve real (heightmap.bin), ortofoto como textura y cada capa activa como un
 * velo semitransparente sobre la misma geometría. Las regiones viejas sin heightmap.bin usan el
 * heightmap.png como displacementMap.
 *
 * Carga por partes: el relieve aparece en cuanto llegan las alturas, la ortofoto se pone encima al
 * descargarse y cada capa se descarga la primera vez que se enciende.
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
 * Las capas y la ortofoto están en sRGB: sin esto se ven lavadas y no coinciden con la leyenda.
 * Función fija (no una flecha en cada render): useTexture la vuelve a llamar si cambia.
 */
function prepareColorTexture(t: Texture | Texture[]) {
  for (const texture of Array.isArray(t) ? t : [t]) {
    if (texture.colorSpace === SRGBColorSpace) continue;
    texture.colorSpace = SRGBColorSpace;
    texture.anisotropy = 8;
    texture.needsUpdate = true;
  }
}

/** Marca el relieve como visible mientras el componente está montado (aviso de carga). */
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

  // Un vértice por celda de la grilla; la misma geometría la comparten el suelo y los velos.
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

/** Suelo de color liso: mientras llega la ortofoto, o si la región no tiene. */
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

/** Las capas activas como velos sobre el relieve y, encima de todas, el mapa de regreso seguro. */
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
        // Cada capa en su propio Suspense: mientras se descarga, el resto de la escena sigue igual.
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
      {/* Lambert y no Basic: MeshBasicMaterial no soporta displacementMap */}
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

/** Regiones publicadas antes del heightmap.bin: el PNG de 16 bits desplaza un plano. */
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
