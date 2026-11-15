"use client";

import { dataName, useLang, useT } from "@/lib/i18n";
import { useMapStore } from "@/lib/store";

/** Lista de sitios en la vista de globo (equivale a hacer clic en su marcador). */
export function SitePanel() {
  const regions = useMapStore((s) => s.regions);
  const selectRegion = useMapStore((s) => s.selectRegion);
  const error = useMapStore((s) => s.error);
  const t = useT();
  const lang = useLang((s) => s.lang);

  return (
    <section className="panel site-panel">
      <h2>Martian Route</h2>
      <p className="muted tight">{t.sitePickTitle}</p>
      {regions.map((r) => (
        <button key={r.id} onClick={() => selectRegion(r.id)}>
          {dataName(r.name, lang)}
        </button>
      ))}
      {error && <p className="error">{error}</p>}
    </section>
  );
}
