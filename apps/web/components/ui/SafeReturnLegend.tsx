"use client";

import { useT } from "@/lib/i18n";
import { ZONE_COLORS, type Zone } from "@/lib/safeReturn";
import { useMapStore } from "@/lib/store";

/** Interruptor y leyenda del mapa de regreso seguro. */
export function SafeReturnToggle() {
  const show = useMapStore((s) => s.showSafeReturn);
  const toggle = useMapStore((s) => s.toggleSafeReturn);
  const res = useMapStore((s) => s.safeReturn);
  const t = useT();

  return (
    <div style={{ margin: "8px 0 4px" }}>
      <label style={{ display: "block" }}>
        <input type="checkbox" checked={show} onChange={toggle} /> {t.safeReturn}
      </label>
      {show && res && (
        <ul className="legend">
          {([1, 2, 3, 0] as Zone[]).map((z) => (
            <li key={z}>
              <span className="swatch" style={{ background: ZONE_COLORS[z] }} /> {t.zones[z]}
            </li>
          ))}
          <li className="muted">
            {t.safeReturnSummary(
              Math.round(res.planned_limit_min),
              Math.round(res.planned_area_fraction * 100),
              res.max_eva_dose_msv.toFixed(2),
            )}
          </li>
        </ul>
      )}
    </div>
  );
}
