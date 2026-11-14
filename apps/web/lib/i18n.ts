// Idioma de la interfaz (español / inglés).
//
// - Cada texto vive una sola vez aquí, con su versión en los dos idiomas. TypeScript obliga a que
//   `en` tenga las mismas claves que `es`: si falta una traducción, `npm run typecheck` falla.
// - Los componentes leen los textos con `useT()`. Cambiar de idioma no vuelve a pedir nada a la
//   API: las alertas y las paradas llegan con `code`/`values`, y aquí se arma el texto.
// - El idioma elegido se recuerda en el navegador (localStorage), si el navegador lo permite.

import { create } from "zustand";

import type { Alert, Provenance, Stop, WalkMode } from "./types";

export type Lang = "es" | "en";

const SOL_HOURS = 24.6598;
const STORAGE_KEY = "wazemars.lang";

const es = {
  sitePickTitle: "Elige un sitio de exploración",
  backToGlobe: "← Volver al globo",
  realTraverse: (rover: string) => `Recorrido real (${rover})`,
  layers: {
    slope: "Pendiente (MOLA / CTX)",
    hazard: "Obstáculos (HiRISE)",
    thermal_inertia: "Inercia térmica (THEMIS)",
    ice: "Hielo subsuperficial (SWIM)",
    minerals: "Minerales (CRISM)",
    terrain_class: "Tipo de terreno (NOAH-H)",
    impassable_fraction: "Ondulaciones grandes (NOAH-H)",
  } as Record<string, string>,

  planTitle: "Planear caminata",
  hintStart: "Haz clic en el terreno para marcar el inicio",
  hintEnd: "Ahora marca el destino",
  modes: { safe: "Segura", fast: "Rápida", science: "Científica", baseline: "Línea base" } as Record<
    WalkMode,
    string
  >,
  autonomy: (h: number) => `Autonomía del traje: ${h} h`,
  maxSlope: (deg: number) => `Pendiente máxima: ${deg}°`,
  compute: "Calcular rutas",
  computing: "Calculando…",

  colO2: "O₂ por persona",
  colTime: "Tiempo",
  colDose: "Dosis",
  colRisk: "Riesgo",
  colVsBaseline: "vs. línea base",
  reference: "referencia",
  infeasible: "⚠ no factible",
  infeasibleTitle: "Rompe un límite del traje: mira las alertas en Navegación",
  tableCaption:
    "O₂ entre dos cotas de gravedad (modelado). Dosis de fondo durante la EVA, con la tasa que midió Curiosity en Gale. Riesgo: obstáculos promedio, 0 a 1. Pasa el cursor por un encabezado para ver su procedencia.",
  to: "a",

  navTitle: "Navegación",
  sols: "soles",
  dose: (msv: string) => `Dosis de fondo (tasa de Gale): ${msv} mSv`,
  vsSafe: (km: string, h: string, msv: string, shared: number) =>
    `vs. Segura: ${km}, ${h}, ${msv}; comparte ${shared} % del camino`,
  pnr: (h: string, km: string | null, usable: string) =>
    `Punto de no retorno a las ${h} h${km ? ` (km ${km})` : ""}: desde ahí, volver ya no cabe en las ${usable} h planeables y gastaría la reserva`,
  stops: "Paradas",
  alerts: "Alertas",
  stop: (s: Stop) =>
    s.type === "ice"
      ? `Posible hielo somero (índice ${s.value.toFixed(2)})`
      : `Minerales de interés (índice ${s.value.toFixed(2)})`,

  safeReturn: "Mapa de regreso seguro",
  zones: [
    "Sin camino de regreso",
    "Ida y vuelta dentro de la autonomía planeable",
    "Regreso solo consumiendo la reserva",
    "Sin regreso ni con la autonomía total",
  ],
  safeReturnSummary: (min: number, pct: number, msv: string) =>
    `Planeable: hasta ${min} min de regreso (${pct} % de la zona). Dosis de una EVA completa: ${msv} mSv (tasa de Gale, modelado).`,

  assumptions: "Supuestos y límites",
  hide: "Ocultar",
  limits: "Límites",
  noValue: "sin valor",
  unsourced: "Supuesto sin fuente confirmada",
  provenance: { observed: "observado", derived: "derivado", modeled: "modelado" } as Record<Provenance, string>,
};

type Strings = typeof es;

const en: Strings = {
  sitePickTitle: "Pick an exploration site",
  backToGlobe: "← Back to the globe",
  realTraverse: (rover) => `Real traverse (${rover})`,
  layers: {
    slope: "Slope (MOLA / CTX)",
    hazard: "Obstacles (HiRISE)",
    thermal_inertia: "Thermal inertia (THEMIS)",
    ice: "Subsurface ice (SWIM)",
    minerals: "Minerals (CRISM)",
    terrain_class: "Terrain type (NOAH-H)",
    impassable_fraction: "Large ripples (NOAH-H)",
  },

  planTitle: "Plan a walk",
  hintStart: "Click the terrain to mark the start",
  hintEnd: "Now mark the destination",
  modes: { safe: "Safe", fast: "Fast", science: "Science", baseline: "Baseline" },
  autonomy: (h) => `Suit autonomy: ${h} h`,
  maxSlope: (deg) => `Maximum slope: ${deg}°`,
  compute: "Compute routes",
  computing: "Computing…",

  colO2: "O₂ per person",
  colTime: "Time",
  colDose: "Dose",
  colRisk: "Risk",
  colVsBaseline: "vs. baseline",
  reference: "reference",
  infeasible: "⚠ not feasible",
  infeasibleTitle: "Breaks a suit limit: see the alerts under Navigation",
  tableCaption:
    "O₂ between two gravity bounds (modeled). Background dose during the EVA, using the rate Curiosity measured at Gale. Risk: average obstacles, 0 to 1. Hover a header to see where its figure comes from.",
  to: "to",

  navTitle: "Navigation",
  sols: "sols",
  dose: (msv) => `Background dose (Gale rate): ${msv} mSv`,
  vsSafe: (km, h, msv, shared) => `vs. Safe: ${km}, ${h}, ${msv}; shares ${shared} % of the path`,
  pnr: (h, km, usable) =>
    `Point of no return at ${h} h${km ? ` (km ${km})` : ""}: from there, the way back no longer fits in the ${usable} plannable hours and would use the reserve`,
  stops: "Stops",
  alerts: "Alerts",
  stop: (s) =>
    s.type === "ice"
      ? `Possible shallow ice (index ${s.value.toFixed(2)})`
      : `Minerals of interest (index ${s.value.toFixed(2)})`,

  safeReturn: "Safe-return map",
  zones: [
    "No way back",
    "Round trip within the plannable autonomy",
    "Return only by using the reserve",
    "No return even with the full autonomy",
  ],
  safeReturnSummary: (min, pct, msv) =>
    `Plannable: up to ${min} min to return (${pct} % of the area). Dose of a full EVA: ${msv} mSv (Gale rate, modeled).`,

  assumptions: "Assumptions and limits",
  hide: "Hide",
  limits: "Limits",
  noValue: "no value",
  unsourced: "Assumption without a confirmed source",
  provenance: { observed: "observed", derived: "derived", modeled: "modeled" },
};

export const STRINGS: Record<Lang, Strings> = { es, en };

/**
 * Nombres que vienen en los datos de la región (pipeline/config/regions.yaml y la tabla de NOAH-H):
 * regiones, etiquetas del mapa y clases de terreno. Un nombre que no esté aquí se muestra tal cual.
 */
const DATA_NAMES_EN: Record<string, string> = {
  "Cráter Jezero": "Jezero Crater",
  "Jezero, zona de caminata (HiRISE)": "Jezero, walking zone (HiRISE)",
  "Cráter Gale": "Gale Crater",
  "Base · amartizaje de Perseverance": "Base · Perseverance landing site",
  "Destino de la demo": "Demo destination",
  "Destino de la demo: modos distintos": "Demo destination: distinct modes",
  "Ahorro de O₂ por pendiente": "O₂ savings on slopes",
  "Sin dato": "No data",
  "No roca madre": "Not bedrock",
  "Roca madre": "Bedrock",
  "Campos de rocas": "Boulder fields",
  "Ondulaciones pequeñas": "Small ripples",
  "Ondulaciones grandes": "Large ripples",
  Nodata: "No data",
};

/** Traduce un nombre que viene en los datos; "Perseverance · sol 120" no cambia. */
export const dataName = (name: string, lang: Lang) => (lang === "en" ? (DATA_NAMES_EN[name] ?? name) : name);

/** "3.2 h (0.13 soles)" en el idioma pedido. */
export const hoursWithSols = (h: number, lang: Lang) =>
  `${h.toFixed(1)} h (${(h / SOL_HOURS).toFixed(2)} ${STRINGS[lang].sols})`;

/**
 * Texto de una alerta. En español se usa el de la API; en inglés se arma con `code` y `values`.
 * Una alerta con un `code` desconocido (API más nueva que la web) se muestra en español.
 */
export function alertText(a: Alert, lang: Lang): string {
  if (lang === "es") return a.message;
  const v = a.values;
  const h = (x: number) => hoursWithSols(x, "en");
  switch (a.code) {
    case "steep_segment":
      return `Steep segment: ${v.slope_deg.toFixed(0)}°`;
    case "autonomy_over_suit":
      return `The round-trip EVA (${h(v.total_h)}) exceeds the suit autonomy (${h(v.autonomy_h)})`;
    case "autonomy_reserve":
      return `The round-trip EVA (${h(v.total_h)}) uses the reserve (${h(v.reserve_h)}): the plannable limit is ${h(v.usable_h)}`;
    case "too_far":
      return `More than ${v.max_dist_km} km from base`;
    case "dose_over_limit":
      return `Estimated dose of ${v.dose_msv.toFixed(2)} mSv, above the ${v.limit_msv} mSv limit`;
    case "solar_event":
      return `Solar event scenario: up to ${v.dose_mgy} mGy of absorbed dose (May 2024, the largest measured by RAD up to that date). From the destination, the way back to base takes ${h(v.return_h)}`;
    default:
      return a.message;
  }
}

/** Idioma guardado en el navegador, o español si no hay ninguno. */
function savedLang(): Lang {
  try {
    const saved = window.localStorage.getItem(STORAGE_KEY);
    if (saved === "es" || saved === "en") return saved;
  } catch {
    // Sin localStorage (modo privado, servidor): se queda en español.
  }
  return "es";
}

interface LangState {
  lang: Lang;
  setLang: (lang: Lang) => void;
  /** Aplica el idioma guardado. Se llama al montar la página, no al crear el store: el servidor
   * siempre pinta en español y React exige que el primer render del navegador sea igual. */
  restore: () => void;
}

export const useLang = create<LangState>((set) => ({
  lang: "es",
  restore: () => {
    const lang = savedLang();
    document.documentElement.lang = lang;
    set({ lang });
  },
  setLang: (lang) => {
    try {
      window.localStorage.setItem(STORAGE_KEY, lang);
    } catch {
      // Si no se puede guardar, el cambio vale solo para esta visita.
    }
    document.documentElement.lang = lang;
    set({ lang });
  },
}));

/** Textos del idioma activo: `const t = useT(); t.planTitle`. */
export function useT(): Strings {
  return STRINGS[useLang((s) => s.lang)];
}
