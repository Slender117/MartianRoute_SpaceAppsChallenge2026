"use client";

import { useState } from "react";

import { api } from "@/lib/api";
import { PROVENANCE_LABELS } from "@/lib/format";
import type { AssumptionsResponse } from "@/lib/types";

const PENDING = "[__]";

// 3.5e-5 en vez de 0.000035000000000000004: tres cifras significativas bastan para leer.
const formatValue = (v: number | string | null) =>
  v === null ? "sin valor" : typeof v === "number" ? String(Number(v.toPrecision(3))) : v;

/** Panel "Supuestos y límites": cada parámetro del modelo con su valor, procedencia y fuente. */
export function AssumptionsPanel() {
  const [open, setOpen] = useState(false);
  const [data, setData] = useState<AssumptionsResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const toggle = async () => {
    if (!open && !data) {
      try {
        setData(await api.assumptions());
      } catch (e) {
        setError((e as Error).message);
      }
    }
    setOpen(!open);
  };

  return (
    <section className="panel assumptions" style={{ bottom: 16, right: 16 }}>
      <button className="ghost" onClick={toggle}>
        {open ? "Ocultar" : "Supuestos y límites"}
      </button>
      {open && error && <p className="error">{error}</p>}
      {open && data && (
        <div className="scroll">
          <ul>
            {data.parameters.map((p) => (
              <li key={p.id}>
                <strong>{p.label}:</strong> {formatValue(p.value)} {p.unit ?? ""}{" "}
                <span className={`tag ${p.provenance}`}>{PROVENANCE_LABELS[p.provenance]}</span>
                <br />
                <span className="muted">
                  {p.source === PENDING ? "Supuesto sin fuente confirmada" : p.source}
                  {p.note ? `. ${p.note}` : ""}
                </span>
              </li>
            ))}
          </ul>
          <h2 style={{ marginTop: 10 }}>Límites</h2>
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
