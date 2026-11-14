"use client";

import { MODE_COLORS } from "@/components/scene/RoutePath";
import { CompareTable } from "@/components/ui/CompareTable";
import { useT } from "@/lib/i18n";
import { useMapStore } from "@/lib/store";
import type { WalkMode } from "@/lib/types";

const MODES: WalkMode[] = ["safe", "fast", "science"];

export function RoutePanel() {
  const { start, end, mode, suit, routes, loading, error, setMode, setSuit, computeRoutes } = useMapStore();

  const t = useT();
  const hint = !start ? t.hintStart : !end ? t.hintEnd : null;

  return (
    <section className="panel" style={{ top: 16, right: 16 }}>
      <h2>{t.planTitle}</h2>
      {hint && <p className="muted">{hint}</p>}

      <div style={{ display: "flex", gap: 6, margin: "8px 0" }}>
        {MODES.map((m) => (
          <button
            key={m}
            className={m === mode ? undefined : "ghost"}
            style={m === mode ? { background: MODE_COLORS[m] } : undefined}
            onClick={() => setMode(m)}
          >
            {t.modes[m]}
          </button>
        ))}
      </div>

      <label style={{ display: "block" }}>
        {t.autonomy(suit.autonomy_h)}
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
        {t.maxSlope(suit.max_slope_deg)}
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
        {loading ? t.computing : t.compute}
      </button>
      {error && <p className="error">{error}</p>}

      <CompareTable routes={routes} />
    </section>
  );
}
