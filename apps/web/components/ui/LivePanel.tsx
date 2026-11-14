"use client";

import { useEffect, useState } from "react";

import { api } from "@/lib/api";
import { useLang, useT } from "@/lib/i18n";
import { useMapStore } from "@/lib/store";
import type { LiveResponse, LiveSource } from "@/lib/types";

const REFRESH_MS = 30 * 60 * 1000; // la API también guarda cada fuente 30 min
const DONKI_DAYS = 30;

const formatUtc = (iso: string, lang: string) =>
  `${new Date(iso).toLocaleString(lang === "es" ? "es-MX" : "en-US", {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: "UTC",
  })} UTC`;

/** "en vivo" o "copia del …", con la fuente y el motivo al pasar el cursor. */
function SourceTag({ src }: { src: LiveSource }) {
  const t = useT();
  const lang = useLang((s) => s.lang);
  const date = new Date(src.fetched_at).toLocaleDateString(lang === "es" ? "es-MX" : "en-US", {
    dateStyle: "medium",
  });
  return (
    <span className={`tag ${src.provenance}`} title={t.liveSourceTitle(src.name, src.error)}>
      {src.status === "live" ? t.liveLive : t.liveSnapshot(date)}
    </span>
  );
}

/**
 * Panel "Marte hoy": llegadas de eyecciones solares a Marte (DONKI), dónde está Perseverance y sus
 * últimas imágenes. Si una eyección llega cerca de hoy, propone activar el escenario de evento solar.
 */
export function LivePanel() {
  const regionId = useMapStore((s) => s.regionId);
  const solarEvent = useMapStore((s) => s.solarEvent);
  const setSolarEvent = useMapStore((s) => s.setSolarEvent);
  const lang = useLang((s) => s.lang);
  const t = useT();
  const [open, setOpen] = useState(false);
  const [data, setData] = useState<LiveResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    const load = () =>
      api
        .live(regionId ?? undefined)
        .then((d) => alive && (setData(d), setError(null)))
        .catch((e: Error) => alive && setError(e.message));
    void load();
    const id = setInterval(load, REFRESH_MS);
    return () => {
      alive = false;
      clearInterval(id);
    };
  }, [regionId]);

  const sw = data?.space_weather;
  const alert = sw?.alert ?? null;
  const alertText = () => {
    if (!alert) return "";
    const dh = Math.round((new Date(alert.arrival_time).getTime() - Date.now()) / 3.6e6);
    const relative = dh < 0 ? t.liveHoursAgo(-dh) : t.liveHoursAhead(dh);
    const when = `${formatUtc(alert.arrival_time, lang)}, ${relative}`;
    return t.liveAlert(when, t.cmeKind(alert.glancing_blow, alert.minor_impact));
  };

  return (
    <section className="panel live-panel">
      <button className="ghost" onClick={() => setOpen(!open)}>
        {open ? t.hide : t.liveTitle}
        {alert && !open ? " ⚠" : ""}
      </button>
      {open && error && <p className="error">{error}</p>}
      {open && data && sw && (
        <div className="live-body">
          <h2>
            {t.liveSpaceWeather} <SourceTag src={sw.source} />
          </h2>
          {alert ? (
            <>
              <p className="live-alert">
                <a href={alert.link} target="_blank" rel="noreferrer">
                  {alertText()}
                </a>
              </p>
              <button disabled={solarEvent} onClick={() => setSolarEvent(true)}>
                {solarEvent ? t.liveScenarioOn : t.liveUseScenario}
              </button>
            </>
          ) : (
            <p className="muted">{t.liveNoAlert}</p>
          )}
          <p className="muted">{t.liveArrivals(sw.arrivals.length, DONKI_DAYS)}</p>

          {data.rover && (
            <>
              <h2>
                {t.liveRover(data.rover.sol)} <SourceTag src={data.rover.source} />
              </h2>
              <p>
                {data.rover.distance_to_base_km !== null &&
                  t.liveRoverDistance(data.rover.distance_to_base_km.toFixed(1))}
                {data.rover.in_region === false && ` · ${t.liveRoverOutside}`}
                {data.rover.odometry_km !== null && (
                  <span className="muted"> · {t.liveOdometry(data.rover.odometry_km.toFixed(1))}</span>
                )}
              </p>
            </>
          )}

          <h2>
            {t.liveImages(data.images.latest_sol)} <SourceTag src={data.images.source} />
          </h2>
          {data.images.images.length ? (
            <div className="live-images">
              {data.images.images.map((img) => (
                <a
                  key={img.image_id}
                  href={img.page_url ?? img.full_url ?? img.thumbnail_url}
                  target="_blank"
                  rel="noreferrer"
                >
                  {/* Imágenes de NASA servidas desde mars.nasa.gov: next/image exigiría configurar el dominio. */}
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img
                    src={img.thumbnail_url}
                    alt={`${img.camera}, sol ${img.sol}`}
                    title={`${img.camera} · ${formatUtc(img.taken_utc, lang)}`}
                    loading="lazy"
                    onError={(e) => (e.currentTarget.style.display = "none")}
                  />
                </a>
              ))}
            </div>
          ) : (
            <p className="muted">{t.liveNoImages}</p>
          )}
        </div>
      )}
    </section>
  );
}
