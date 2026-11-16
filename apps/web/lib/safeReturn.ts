// Decodes the API's safe-return map and classifies it into zones to paint it.
// The 3D layer (components/scene) only needs `zoneGrid` and `ZONE_COLORS`. The zone names,
// in each language, are in lib/i18n.ts (`zones`).

import type { SafeReturnResponse } from "./types";

/** 0 = no path, 1 = plannable, 2 = only by using the reserve, 3 = not even with the full autonomy. */
export type Zone = 0 | 1 | 2 | 3;

export const ZONE_COLORS: Record<Zone, string> = {
  0: "#3a3a3a",
  1: "#4fd1a5",
  2: "#ffc94d",
  3: "#ff5a4f",
};

/** Return minutes per cell, north row first (like the region grids). */
export function decodeMinutes(res: SafeReturnResponse): Uint16Array {
  const bytes = Uint8Array.from(atob(res.return_minutes), (c) => c.charCodeAt(0));
  // DataView fixes little-endian without depending on the processor.
  const view = new DataView(bytes.buffer);
  const out = new Uint16Array(bytes.length / 2);
  for (let i = 0; i < out.length; i++) out[i] = view.getUint16(i * 2, true);
  return out;
}

/** Zone of each cell from the two thresholds of the response. */
export function zoneGrid(res: SafeReturnResponse): Uint8Array {
  const minutes = decodeMinutes(res);
  const zones = new Uint8Array(minutes.length);
  for (let i = 0; i < minutes.length; i++) {
    const m = minutes[i];
    zones[i] =
      m === res.no_return_value ? 0 : m <= res.planned_limit_min ? 1 : m <= res.total_limit_min ? 2 : 3;
  }
  return zones;
}
