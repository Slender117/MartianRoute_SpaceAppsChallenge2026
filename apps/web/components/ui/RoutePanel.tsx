"use client";

import { MODE_COLORS } from "@/components/scene/RoutePath";
import { CompareTable } from "@/components/ui/CompareTable";
import { useT } from "@/lib/i18n";
import { useMapStore } from "@/lib/store";
import type { WalkMode } from "@/lib/types";
import { useMediaQuery } from "@/lib/useMediaQuery";

const MODES: WalkMode[] = ["safe", "fast", "science"];

/**
 * Plan the walk: mode, suit limits, solar scenario and the comparison table.
 * Routes are computed automatically when the destination is marked and recomputed when the suit or
 * the scenario changes; the button requests them again.
 */
export function RoutePanel() {
  const start = useMapStore((s) => s.start);
  const end = useMapStore((s) => s.end);
  const mode = useMapStore((s) => s.mode);
  const suit = useMapStore((s) => s.suit);
  const routes = useMapStore((s) => s.routes);
  const loading = useMapStore((s) => s.loading);
  const error = useMapStore((s) => s.error);
  const solarEvent = useMapStore((s) => s.solarEvent);
  const hasDemo = useMapStore((s) => s.manifest?.demo != null);
  const setMode = useMapStore((s) => s.setMode);
  const setSuit = useMapStore((s) => s.setSuit);
  const setSolarEvent = useMapStore((s) => s.setSolarEvent);
  const computeRoutes = useMapStore((s) => s.computeRoutes);
  const clearPoints = useMapStore((s) => s.clearPoints);
  const loadDemo = useMapStore((s) => s.loadDemo);
  // On touch screens you "tap" the terrain, you do not click.
  const touch = useMediaQuery("(pointer: coarse)");

  const t = useT();
  const hint = (() => {
    if (loading) return null;
    if (!start) return touch ? t.hintStartTouch : t.hintStart;
    if (!end) return touch ? t.hintEndTouch : t.hintEnd;
    return touch ? t.hintRestartTouch : t.hintRestart;
  })();

  return (
    <section className="panel route-panel">
      <h2>{t.planTitle}</h2>
      <p className="points" aria-live="polite">
        <span className={start ? "point is-set" : "point"}>
          <span className="dot dot-start" aria-hidden /> {t.startLabel}
        </span>
        <span className={end ? "point is-set" : "point"}>
          <span className="dot dot-end" aria-hidden /> {t.endLabel}
        </span>
        {hint && <span className="muted hint">{hint}</span>}
      </p>

      <div className="mode-row" role="group" aria-label={t.planTitle}>
        {MODES.map((m) => (
          <button
            key={m}
            className={m === mode ? "mode is-active" : "mode ghost"}
            style={m === mode ? { background: MODE_COLORS[m] } : { borderColor: MODE_COLORS[m] }}
            aria-pressed={m === mode}
            onClick={() => setMode(m)}
          >
            {t.modes[m]}
          </button>
        ))}
      </div>

      <label className="range">
        {t.autonomy(suit.autonomy_h)}
        <input
          type="range"
          min={2}
          max={12}
          step={0.5}
          value={suit.autonomy_h}
          onChange={(e) => setSuit({ autonomy_h: Number(e.target.value) })}
        />
      </label>
      <label className="range">
        {t.maxSlope(suit.max_slope_deg)}
        <input
          type="range"
          min={10}
          max={40}
          value={suit.max_slope_deg}
          onChange={(e) => setSuit({ max_slope_deg: Number(e.target.value) })}
        />
      </label>

      <label className="check">
        <input type="checkbox" checked={solarEvent} onChange={(e) => setSolarEvent(e.target.checked)} />{" "}
        {t.solarScenario}
      </label>

      <div className="button-row">
        <button disabled={!start || !end || loading} onClick={computeRoutes}>
          {loading ? (
            <>
              <span className="spinner spinner-sm" aria-hidden /> {t.computing}
            </>
          ) : (
            t.compute
          )}
        </button>
        {(start || end) && (
          <button className="ghost" onClick={clearPoints} title={t.clearTitle}>
            {t.clearPoints}
          </button>
        )}
        {hasDemo && !start && (
          <button className="ghost" onClick={loadDemo} title={t.demoTitle}>
            {t.demoRoute}
          </button>
        )}
      </div>
      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}

      <div className="table-scroll">
        <CompareTable routes={routes} />
      </div>
    </section>
  );
}
