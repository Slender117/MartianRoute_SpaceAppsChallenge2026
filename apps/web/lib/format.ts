// Number formatting for the interface. The texts that change with the language are in lib/i18n.ts.

import type { O2Interval } from "./types";

/** "0.38–0.42 kg": the slope O₂ is an interval, never a single figure. */
export const o2Range = ({ low_kg, high_kg }: O2Interval) => `${low_kg.toFixed(2)}–${high_kg.toFixed(2)} kg`;

/** Signed difference: "+0.9 km", "−0.03 kg". */
export const signed = (value: number, digits: number, unit: string) => {
  // It is rounded before picking the sign, so "−0.0" is never shown.
  const rounded = Number(value.toFixed(digits));
  const sign = rounded > 0 ? "+" : rounded < 0 ? "−" : "±";
  return `${sign}${Math.abs(rounded).toFixed(digits)} ${unit}`;
};

/**
 * Bound-by-bound difference of an interval: "+0.01 to +0.03 kg" (`to` is "a" or "to"). If both
 * bounds round the same, only one.
 */
export const signedRange = ({ low_kg, high_kg }: O2Interval, digits: number, unit: string, to: string) => {
  const [a, b] = [low_kg, high_kg].sort((x, y) => x - y);
  const lo = signed(a, digits, unit);
  const hi = signed(b, digits, unit);
  return lo === hi ? lo : `${lo.replace(` ${unit}`, "")} ${to} ${hi}`;
};
