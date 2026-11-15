"use client";

import { useEffect, useState } from "react";

import { api } from "@/lib/api";
import { useLang, useT } from "@/lib/i18n";
import type { AssumptionsResponse } from "@/lib/types";

const PENDING = "[__]";

// 3.5e-5 en vez de 0.000035000000000000004: tres cifras significativas bastan para leer.
const formatValue = (v: number | string | null, noValue: string) =>
  v === null ? noValue : typeof v === "number" ? String(Number(v.toPrecision(3))) : v;

/**
 * Panel "Supuestos y límites": cada parámetro del modelo con su valor, procedencia y fuente.
 * `defaultOpen`: en la pestaña de celular ya se abrió a propósito, no hace falta otro clic.
 */
export function AssumptionsPanel({ defaultOpen = false }: { defaultOpen?: boolean }) {
  const [open, setOpen] = useState(defaultOpen);
  const [data, setData] = useState<AssumptionsResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const lang = useLang((s) => s.lang);
  const t = useT();

  // Los textos vienen de la API en el idioma activo: al cambiarlo, se vuelven a pedir.
  useEffect(() => setData(null), [lang]);
  useEffect(() => {
    if (!open || data) return;
    api
      .assumptions(lang)
      .then(setData)
      .catch((e: Error) => setError(e.message));
  }, [open, data, lang]);

  return (
    <section className="panel assumptions">
      <button className="ghost" aria-expanded={open} onClick={() => setOpen(!open)}>
        {open ? t.hide : t.assumptions}
      </button>
      {open && error && <p className="error">{error}</p>}
      {open && !data && !error && <p className="muted">…</p>}
      {open && data && (
        <div className="scroll">
          <ul>
            {data.parameters.map((p) => (
              <li key={p.id}>
                <strong>{p.label}:</strong> {formatValue(p.value, t.noValue)} {p.unit ?? ""}{" "}
                <span className={`tag ${p.provenance}`}>{t.provenance[p.provenance]}</span>
                <br />
                <span className="muted">
                  {p.source === PENDING ? t.unsourced : p.source}
                  {p.note ? `. ${p.note}` : ""}
                </span>
              </li>
            ))}
          </ul>
          <h2 className="subhead">{t.limits}</h2>
          <ul>
            {data.limits.map((l) => (
              <li key={l}>{l}</li>
            ))}
          </ul>
        </div>
      )}
    </section>
  );
}
