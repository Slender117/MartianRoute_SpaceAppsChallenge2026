"use client";

import { signed } from "@/lib/format";
import { alertText, useLang, useT } from "@/lib/i18n";
import { useMapStore } from "@/lib/store";

/** Detalle de la ruta activa: dosis, diferencia contra la Segura, punto de no retorno, paradas y alertas. */
export function NavPanel() {
  const route = useMapStore((s) => s.routes[s.mode]);
  const lang = useLang((s) => s.lang);
  const t = useT();
  if (!route) return null;

  const pnr = route.point_of_no_return;
  const vsSafe = route.vs_safe;

  return (
    <section className="panel nav-panel">
      <h2>{t.navTitle}</h2>
      <p className="tight">
        {route.distance_km.toFixed(2)} km · {route.duration_h.toFixed(1)} h ({route.duration_sols.toFixed(2)} {t.sols})
      </p>
      <p className="muted tight">
        {t.dose(route.radiation_msv.toFixed(2))}
        {vsSafe && (
          <>
            <br />
            {t.vsSafe(
              signed(vsSafe.distance_km, 1, "km"),
              signed(vsSafe.duration_h, 1, "h"),
              signed(vsSafe.radiation_msv, 2, "mSv"),
              Math.round(vsSafe.shared_path * 100),
            )}
          </>
        )}
      </p>
      {pnr !== null && (
        <p className="muted tight">
          {t.pnr(
            route.path[pnr].t_h.toFixed(1),
            route.point_of_no_return_km !== null ? route.point_of_no_return_km.toFixed(2) : null,
            route.usable_autonomy_h.toFixed(1),
          )}
        </p>
      )}

      {route.stops.length > 0 && (
        <>
          <strong>{t.stops}</strong>
          <ul>
            {route.stops.map((s, i) => (
              <li key={i}>{t.stop(s)}</li>
            ))}
          </ul>
        </>
      )}

      {route.alerts.length > 0 && (
        <>
          <strong>{t.alerts}</strong>
          <ul className="error">
            {route.alerts.map((a, i) => (
              <li key={i}>
                {alertText(a, lang)} (h {route.path[a.at].t_h.toFixed(1)})
              </li>
            ))}
          </ul>
        </>
      )}
    </section>
  );
}
