// Formato de cifras para la interfaz: unidades del proyecto (m, °, h con soles, kg) y procedencia.

import type { O2Interval, Provenance } from "./types";

const SOL_HOURS = 24.6598;

export const PROVENANCE_LABELS: Record<Provenance, string> = {
  observed: "observado",
  derived: "derivado",
  modeled: "modelado",
};

/** "3.2 h (0.13 soles)" */
export const hoursWithSols = (h: number) => `${h.toFixed(1)} h (${(h / SOL_HOURS).toFixed(2)} soles)`;

/** "0.38–0.42 kg": el O₂ por pendiente es un intervalo, nunca una sola cifra. */
export const o2Range = ({ low_kg, high_kg }: O2Interval) => `${low_kg.toFixed(2)}–${high_kg.toFixed(2)} kg`;

/** Diferencia con signo: "+0.9 km", "−0.03 kg". */
export const signed = (value: number, digits: number, unit: string) => {
  // Se redondea antes de elegir el signo, para no mostrar "−0.0".
  const rounded = Number(value.toFixed(digits));
  const sign = rounded > 0 ? "+" : rounded < 0 ? "−" : "±";
  return `${sign}${Math.abs(rounded).toFixed(digits)} ${unit}`;
};

/** Diferencia de un intervalo cota a cota: "+0.01 a +0.03 kg". Si las dos cotas redondean igual, una sola. */
export const signedRange = ({ low_kg, high_kg }: O2Interval, digits: number, unit: string) => {
  const [a, b] = [low_kg, high_kg].sort((x, y) => x - y);
  const lo = signed(a, digits, unit);
  const hi = signed(b, digits, unit);
  return lo === hi ? lo : `${lo.replace(` ${unit}`, "")} a ${hi}`;
};
