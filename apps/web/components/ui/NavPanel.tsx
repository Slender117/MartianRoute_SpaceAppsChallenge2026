"use client";

import { signed } from "@/lib/format";
import { useMapStore } from "@/lib/store";

/** Detalle de la ruta activa: dosis, diferencia contra la Segura, punto de no retorno, paradas y alertas. */
export function NavPanel() {
  const route = useMapStore((s) => s.routes[s.mode]);
  if (!route) return null;

  const pnr = route.point_of_no_return;
  const vsSafe = route.vs_safe;

  return (
    <section className="panel" style={{ bottom: 16, left: 16 }}>
      <h2>Navegación</h2>
      <p style={{ margin: "0 0 6px" }}>
        {route.distance_km.toFixed(2)} km · {route.duration_h.toFixed(1)} h ({route.duration_sols.toFixed(2)} soles)
      </p>
      <p className="muted" style={{ margin: "0 0 6px" }}>
        Dosis de fondo: {route.radiation_msv.toFixed(2)} mSv
        {vsSafe && (
          <>
            <br />
            vs. Segura: {signed(vsSafe.distance_km, 1, "km")}, {signed(vsSafe.duration_h, 1, "h")},{" "}
            {signed(vsSafe.radiation_msv, 2, "mSv")}; comparte {Math.round(vsSafe.shared_path * 100)} % del camino
          </>
        )}
      </p>
      {pnr !== null && (
        <p className="muted" style={{ margin: "0 0 6px" }}>
          Punto de no retorno a las {route.path[pnr].t_h.toFixed(1)} h
          {route.point_of_no_return_km !== null && ` (km ${route.point_of_no_return_km.toFixed(2)})`}: desde ahí,
          volver ya no cabe en las {route.usable_autonomy_h.toFixed(1)} h planeables y gastaría la reserva
        </p>
      )}

      {route.stops.length > 0 && (
        <>
          <strong>Paradas</strong>
          <ul>
            {route.stops.map((s, i) => (
              <li key={i}>{s.reason}</li>
            ))}
          </ul>
        </>
      )}

      {route.alerts.length > 0 && (
        <>
          <strong>Alertas</strong>
          <ul className="error">
            {route.alerts.map((a, i) => (
              <li key={i}>
                {a.message} (h {route.path[a.at].t_h.toFixed(1)})
              </li>
            ))}
          </ul>
        </>
      )}
    </section>
  );
}
