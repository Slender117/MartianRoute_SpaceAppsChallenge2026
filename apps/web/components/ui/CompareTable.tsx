"use client";

import { MODE_COLORS } from "@/components/scene/RoutePath";
import { o2Range, PROVENANCE_LABELS, signed, signedRange } from "@/lib/format";
import type { RouteResponse, WalkMode } from "@/lib/types";

const ROWS: { id: WalkMode; label: string }[] = [
  { id: "safe", label: "Segura" },
  { id: "fast", label: "Rápida" },
  { id: "science", label: "Científica" },
  { id: "baseline", label: "Línea base" },
];

/**
 * Tabla comparativa: O₂ como intervalo, tiempo, dosis, riesgo y diferencia contra la línea base
 * (la ruta de mínima distancia). Cada encabezado dice de dónde sale su cifra. Una ruta que rompe
 * un límite del traje se marca "no factible" en rojo; el detalle está en el panel de Navegación.
 */
export function CompareTable({ routes }: { routes: Partial<Record<WalkMode, RouteResponse>> }) {
  const any = Object.values(routes)[0];
  if (!any) return null;
  const tag = (field: string) => PROVENANCE_LABELS[any.provenance[field] ?? "modeled"];

  return (
    <table className="compare">
      <thead>
        <tr>
          <th />
          <th title={tag("o2_interval_kg")}>O₂ por persona</th>
          <th title={tag("duration_h")}>Tiempo</th>
          <th title={tag("radiation_msv")}>Dosis</th>
          <th title={tag("cost_breakdown")}>Riesgo</th>
          <th title="derivado">vs. línea base</th>
        </tr>
      </thead>
      <tbody>
        {ROWS.map(({ id, label }) => {
          const r = routes[id];
          if (!r) return null;
          const d = r.vs_baseline;
          return (
            <tr key={id} style={{ color: MODE_COLORS[id] }}>
              <td>
                {label}
                {!r.feasible && (
                  <span className="infeasible" title="Rompe un límite del traje: mira las alertas en Navegación">
                    ⚠ no factible
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
                    {signedRange(d.o2_interval_kg, 2, "kg O₂")}
                  </>
                ) : (
                  "referencia"
                )}
              </td>
            </tr>
          );
        })}
      </tbody>
      <caption className="muted">
        O₂ entre dos cotas de gravedad (modelado). Dosis de fondo durante la EVA. Riesgo: obstáculos
        promedio, 0 a 1. Pasa el cursor por un encabezado para ver su procedencia.
      </caption>
    </table>
  );
}
