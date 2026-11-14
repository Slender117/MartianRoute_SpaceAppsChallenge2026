// Decodifica el mapa de regreso seguro de la API y lo clasifica en zonas para pintarlo.
// La capa 3D (components/scene) solo necesita `zoneGrid` y `ZONE_COLORS`. Los nombres de las zonas,
// en cada idioma, están en lib/i18n.ts (`zones`).

import type { SafeReturnResponse } from "./types";

/** 0 = sin camino, 1 = planeable, 2 = solo consumiendo la reserva, 3 = ni con la autonomía total. */
export type Zone = 0 | 1 | 2 | 3;

export const ZONE_COLORS: Record<Zone, string> = {
  0: "#3a3a3a",
  1: "#4fd1a5",
  2: "#ffc94d",
  3: "#ff5a4f",
};

/** Minutos de regreso por celda, fila norte primero (como las grillas de la región). */
export function decodeMinutes(res: SafeReturnResponse): Uint16Array {
  const bytes = Uint8Array.from(atob(res.return_minutes), (c) => c.charCodeAt(0));
  // DataView fija little-endian sin depender del procesador.
  const view = new DataView(bytes.buffer);
  const out = new Uint16Array(bytes.length / 2);
  for (let i = 0; i < out.length; i++) out[i] = view.getUint16(i * 2, true);
  return out;
}

/** Zona de cada celda según los dos umbrales de la respuesta. */
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
