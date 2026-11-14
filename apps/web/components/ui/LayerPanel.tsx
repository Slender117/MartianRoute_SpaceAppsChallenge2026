"use client";

import { useRegionExtras } from "@/components/scene/regionAssets";
import { SafeReturnToggle } from "@/components/ui/SafeReturnLegend";
import { useMapStore } from "@/lib/store";

const LAYER_LABELS: Record<string, string> = {
  slope: "Pendiente (MOLA / CTX)",
  hazard: "Obstáculos (HiRISE)",
  thermal_inertia: "Inercia térmica (THEMIS)",
  ice: "Hielo subsuperficial (SWIM)",
  minerals: "Minerales (CRISM)",
  terrain_class: "Tipo de terreno (NOAH-H)",
  impassable_fraction: "Ondulaciones grandes (NOAH-H)",
};

export function LayerPanel() {
  const manifest = useMapStore((s) => s.manifest);
  const activeLayers = useMapStore((s) => s.activeLayers);
  const toggleLayer = useMapStore((s) => s.toggleLayer);
  const showTraverse = useMapStore((s) => s.showTraverse);
  const toggleTraverse = useMapStore((s) => s.toggleTraverse);
  const backToGlobe = useMapStore((s) => s.backToGlobe);
  const legends = useRegionExtras(manifest?.id)?.legends;

  if (!manifest) return null;

  return (
    <section className="panel" style={{ top: 16, left: 16 }}>
      <h2>{manifest.name}</h2>
      {["slope", ...manifest.layers].map((layer) => (
        <div key={layer}>
          <label style={{ display: "block", margin: "4px 0" }}>
            <input type="checkbox" checked={activeLayers.includes(layer)} onChange={() => toggleLayer(layer)} />{" "}
            {LAYER_LABELS[layer] ?? layer}
          </label>
          {activeLayers.includes(layer) && legends?.[layer] && (
            <ul className="class-legend">
              {legends[layer].map((item) => (
                <li key={item.code}>
                  <span className="class-swatch" style={{ background: item.color }} />
                  {item.name}
                  <span className="muted"> · {Math.round(item.share * 100)} %</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      ))}
      {manifest.traverses.length > 0 && (
        <label style={{ display: "block", margin: "8px 0 4px" }}>
          <input type="checkbox" checked={showTraverse} onChange={toggleTraverse} /> Recorrido real (
          {manifest.traverses[0]})
        </label>
      )}
      <SafeReturnToggle />
      <button className="ghost" onClick={backToGlobe} style={{ marginTop: 8 }}>
        ← Volver al globo
      </button>
    </section>
  );
}
