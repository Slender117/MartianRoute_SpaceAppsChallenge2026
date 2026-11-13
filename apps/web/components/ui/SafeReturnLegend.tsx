"use client";

import { ZONE_COLORS, ZONE_LABELS, type Zone } from "@/lib/safeReturn";
import { useMapStore } from "@/lib/store";

/** Interruptor y leyenda del mapa de regreso seguro. */
export function SafeReturnToggle() {
  const show = useMapStore((s) => s.showSafeReturn);
  const toggle = useMapStore((s) => s.toggleSafeReturn);
  const res = useMapStore((s) => s.safeReturn);

  return (
    <div style={{ margin: "8px 0 4px" }}>
      <label style={{ display: "block" }}>
        <input type="checkbox" checked={show} onChange={toggle} /> Mapa de regreso seguro
      </label>
      {show && res && (
        <ul className="legend">
          {([1, 2, 3, 0] as Zone[]).map((z) => (
            <li key={z}>
              <span className="swatch" style={{ background: ZONE_COLORS[z] }} /> {ZONE_LABELS[z]}
            </li>
          ))}
          <li className="muted">
            Planeable: hasta {Math.round(res.planned_limit_min)} min de regreso (
            {Math.round(res.planned_area_fraction * 100)} % de la zona). Dosis de una EVA completa:{" "}
            {res.max_eva_dose_msv.toFixed(2)} mSv (modelado).
          </li>
        </ul>
      )}
    </div>
  );
}
