"use client";

import { MODE_COLORS } from "@/components/scene/RoutePath";
import { useMapStore } from "@/lib/store";
import type { WalkMode } from "@/lib/types";

const MODES: { id: WalkMode; label: string }[] = [
  { id: "safe", label: "Segura" },
  { id: "fast", label: "Rápida" },
  { id: "science", label: "Científica" },
];

export function RoutePanel() {
  const { start, end, mode, suit, routes, loading, error, setMode, setSuit, computeRoutes } = useMapStore();

  const hint = !start ? "Haz clic en el terreno para marcar el inicio" : !end ? "Ahora marca el destino" : null;

  return (
    <section className="panel" style={{ top: 16, right: 16 }}>
      <h2>Planear caminata</h2>
      {hint && <p className="muted">{hint}</p>}

      <div style={{ display: "flex", gap: 6, margin: "8px 0" }}>
        {MODES.map((m) => (
          <button
            key={m.id}
            className={m.id === mode ? undefined : "ghost"}
            style={m.id === mode ? { background: MODE_COLORS[m.id] } : undefined}
            onClick={() => setMode(m.id)}
          >
            {m.label}
          </button>
        ))}
      </div>

      <label style={{ display: "block" }}>
        Autonomía del traje: {suit.autonomy_h} h
        <input
          type="range"
          min={2}
          max={12}
          step={0.5}
          value={suit.autonomy_h}
          onChange={(e) => setSuit({ autonomy_h: Number(e.target.value) })}
          style={{ width: "100%" }}
        />
      </label>
      <label style={{ display: "block" }}>
        Pendiente máxima: {suit.max_slope_deg}°
        <input
          type="range"
          min={10}
          max={40}
          value={suit.max_slope_deg}
          onChange={(e) => setSuit({ max_slope_deg: Number(e.target.value) })}
          style={{ width: "100%" }}
        />
      </label>

      <button disabled={!start || !end || loading} onClick={computeRoutes} style={{ marginTop: 8 }}>
        {loading ? "Calculando…" : "Calcular rutas"}
      </button>
      {error && <p className="error">{error}</p>}

      {Object.keys(routes).length > 0 && (
        <table style={{ width: "100%", marginTop: 10, fontSize: 13 }}>
          <tbody>
            {MODES.map(({ id, label }) => {
              const r = routes[id];
              return r ? (
                <tr key={id} style={{ color: MODE_COLORS[id] }}>
                  <td>{label}</td>
                  <td>{r.distance_km.toFixed(1)} km</td>
                  <td>{r.duration_h.toFixed(1)} h</td>
                  <td>{r.o2_estimate_kg.toFixed(2)} kg O₂</td>
                </tr>
              ) : null;
            })}
          </tbody>
        </table>
      )}
    </section>
  );
}
