"use client";

import { MODE_COLORS } from "@/components/scene/RoutePath";
import { o2Range, signed, signedRange } from "@/lib/format";
import { useT } from "@/lib/i18n";
import type { RouteResponse, WalkMode } from "@/lib/types";

const ROWS: WalkMode[] = ["safe", "fast", "science", "baseline"];

/**
 * Tabla comparativa: O₂ como intervalo, tiempo, dosis, riesgo y diferencia contra la línea base
 * (la ruta de mínima distancia). Cada encabezado dice de dónde sale su cifra. Una ruta que rompe
 * un límite del traje se marca "no factible" en rojo; el detalle está en el panel de Navegación.
 */
export function CompareTable({ routes }: { routes: Partial<Record<WalkMode, RouteResponse>> }) {
  const t = useT();
  const any = Object.values(routes)[0];
  if (!any) return null;
  const tag = (field: string) => t.provenance[any.provenance[field] ?? "modeled"];

  return (
    <table className="compare">
      <thead>
        <tr>
          <th />
          <th title={tag("o2_interval_kg")}>{t.colO2}</th>
          <th title={tag("duration_h")}>{t.colTime}</th>
          <th title={tag("radiation_msv")}>{t.colDose}</th>
          <th title={tag("cost_breakdown")}>{t.colRisk}</th>
          <th title={t.provenance.derived}>{t.colVsBaseline}</th>
        </tr>
      </thead>
      <tbody>
        {ROWS.map((id) => {
          const r = routes[id];
          if (!r) return null;
          const d = r.vs_baseline;
          return (
            <tr key={id} style={{ color: MODE_COLORS[id] }}>
              <td>
                {t.modes[id]}
                {!r.feasible && (
                  <span className="infeasible" title={t.infeasibleTitle}>
                    {t.infeasible}
                  </span>
                )}
              </td>
              <td>{o2Range(r.o2_interval_kg)}</td>
              <td>{r.duration_h.toFixed(1)} h</td>
              <td>{r.radiation_msv.toFixed(2)} mSv</td>
              <td>{r.cost_breakdown.hazard.toFixed(2)}</td>
              <td>
                {d ? (
                  <>
                    {signed(d.distance_km, 1, "km")}
                    <br />
                    {signedRange(d.o2_interval_kg, 2, "kg O₂", t.to)}
                  </>
                ) : (
                  t.reference
                )}
              </td>
            </tr>
          );
        })}
      </tbody>
      <caption className="muted">{t.tableCaption}</caption>
    </table>
  );
}
