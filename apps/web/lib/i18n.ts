// Interface language (English / Spanish). English is the default.
//
// - Each text lives here only once, with its version in both languages. TypeScript forces
//   `en` to have the same keys as `es`: if a translation is missing, `npm run typecheck` fails.
// - Components read the texts with `useT()`. Switching language requests nothing again from the
//   API: alerts and stops arrive with `code`/`values`, and the text is built here.
// - The chosen language is remembered in the browser (localStorage), if the browser allows it.

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
  hintStartTouch: "Toca el terreno para marcar el inicio",
  hintEndTouch: "Ahora toca el destino",
  hintRestart: "Haz clic en el terreno para empezar otra ruta",
  hintRestartTouch: "Toca el terreno para empezar otra ruta",
  startLabel: "Inicio",
  endLabel: "Destino",
  clearPoints: "Limpiar",
  clearTitle: "Borrar el inicio, el destino y las rutas",
  demoRoute: "Ruta de ejemplo",
  demoTitle: "Marcar el inicio y el destino de la demo y calcular las rutas",

  homeTitle: "Volver a la portada",
  loadingRegion: "Cargando la región…",
  loadingTerrain: (name: string) => `Cargando el relieve de ${name}…`,
  loadingImages: (pct: number) => `Cargando imágenes… ${pct} %`,
  panelsLabel: "Paneles del planificador",
  tabs: { route: "Ruta", layers: "Capas", info: "Supuestos" },
  sheetCollapse: "Ocultar paneles",
  sheetExpand: "Mostrar paneles",

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

  solarScenario: "Escenario de evento solar",
  liveTitle: "Marte hoy",
  liveLive: "en vivo",
  liveSnapshot: (date: string) => `copia del ${date}`,
  liveSpaceWeather: "Clima espacial",
  liveAlert: (when: string, kind: string) => `⚠ Eyección solar: llegada prevista a Marte ${when} (${kind})`,
  liveNoAlert: "Ninguna eyección solar llega a Marte cerca de hoy",
  liveHoursAgo: (h: number) => `hace ${h} h`,
  liveHoursAhead: (h: number) => `en ${h} h`,
  cmeKind: (glancing: boolean, minor: boolean): string => (glancing ? "de refilón" : minor ? "impacto menor" : "impacto directo"),
  liveUseScenario: "Activar el escenario de evento solar",
  liveScenarioOn: "Escenario de evento solar activado",
  liveArrivals: (n: number, days: number) =>
    `${n} ${n === 1 ? "llegada prevista" : "llegadas previstas"} a Marte en ${days} días (modelo WSA-ENLIL)`,
  liveRover: (sol: number) => `Perseverance, sol ${sol}`,
  liveRoverDistance: (km: string) => `a ${km} km de la base`,
  liveRoverOutside: "fuera del área del mapa",
  liveOdometry: (km: string) => `${km} km recorridos`,
  liveImages: (sol: number | null) => `Últimas imágenes${sol ? ` (sol ${sol})` : ""}`,
  liveNoImages: "Sin imágenes en la copia guardada",
  liveSourceTitle: (name: string, error: string | null) => (error ? `${name}. Sin consulta en vivo: ${error}` : name),
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
  hintStartTouch: "Tap the terrain to mark the start",
  hintEndTouch: "Now tap the destination",
  hintRestart: "Click the terrain to start a new route",
  hintRestartTouch: "Tap the terrain to start a new route",
  startLabel: "Start",
  endLabel: "Destination",
  clearPoints: "Clear",
  clearTitle: "Remove the start, the destination and the routes",
  demoRoute: "Example route",
  demoTitle: "Mark the demo start and destination and compute the routes",

  homeTitle: "Back to the home page",
  loadingRegion: "Loading the region…",
  loadingTerrain: (name) => `Loading the terrain of ${name}…`,
  loadingImages: (pct) => `Loading images… ${pct} %`,
  panelsLabel: "Planner panels",
  tabs: { route: "Route", layers: "Layers", info: "Assumptions" },
  sheetCollapse: "Hide panels",
  sheetExpand: "Show panels",

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

  solarScenario: "Solar event scenario",
  liveTitle: "Mars today",
  liveLive: "live",
  liveSnapshot: (date) => `copy from ${date}`,
  liveSpaceWeather: "Space weather",
  liveAlert: (when, kind) => `⚠ Solar eruption: forecast to reach Mars ${when} (${kind})`,
  liveNoAlert: "No solar eruption reaches Mars around today",
  liveHoursAgo: (h) => `${h} h ago`,
  liveHoursAhead: (h) => `in ${h} h`,
  cmeKind: (glancing, minor) => (glancing ? "glancing blow" : minor ? "minor impact" : "direct hit"),
  liveUseScenario: "Turn on the solar event scenario",
  liveScenarioOn: "Solar event scenario on",
  liveArrivals: (n, days) =>
    `${n} forecast ${n === 1 ? "arrival" : "arrivals"} at Mars in ${days} days (WSA-ENLIL model)`,
  liveRover: (sol) => `Perseverance, sol ${sol}`,
  liveRoverDistance: (km) => `${km} km from base`,
  liveRoverOutside: "outside the map area",
  liveOdometry: (km) => `${km} km driven`,
  liveImages: (sol) => `Latest images${sol ? ` (sol ${sol})` : ""}`,
  liveNoImages: "No images in the saved copy",
  liveSourceTitle: (name, error) => (error ? `${name}. No live query: ${error}` : name),
};

export const STRINGS: Record<Lang, Strings> = { es, en };

/**
 * Names that come in the region data (pipeline/config/regions.yaml and the NOAH-H table): regions,
 * map labels and terrain classes. Older data has them in Spanish and newer data in English, so the
 * table works in both directions. A name that is not listed here is shown as is.
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

const DATA_NAMES_ES: Record<string, string> = Object.fromEntries(
  Object.entries(DATA_NAMES_EN)
    .filter(([es]) => es !== "Nodata")
    .map(([es, en]) => [en, es]),
);

/** Translates a name that comes in the data; "Perseverance · sol 120" stays the same. */
export const dataName = (name: string, lang: Lang) =>
  lang === "en" ? (DATA_NAMES_EN[name] ?? name) : (DATA_NAMES_ES[name] ?? name);

/** "3.2 h (0.13 sols)" in the requested language. */
export const hoursWithSols = (h: number, lang: Lang) =>
  `${h.toFixed(1)} h (${(h / SOL_HOURS).toFixed(2)} ${STRINGS[lang].sols})`;

/**
 * Text of an alert, built from `code` and `values` in each language. An alert with an unknown
 * `code` (an API newer than the web) shows the API message, which is in English.
 */
export function alertText(a: Alert, lang: Lang): string {
  const v = a.values;
  const h = (x: number) => hoursWithSols(x, lang);
  if (lang === "es") {
    switch (a.code) {
      case "steep_segment":
        return `Tramo empinado: ${v.slope_deg.toFixed(0)}°`;
      case "autonomy_over_suit":
        return `La EVA de ida y vuelta (${h(v.total_h)}) supera la autonomía del traje (${h(v.autonomy_h)})`;
      case "autonomy_reserve":
        return `La EVA de ida y vuelta (${h(v.total_h)}) consume la reserva (${h(v.reserve_h)}): el límite planeable es ${h(v.usable_h)}`;
      case "too_far":
        return `Más de ${v.max_dist_km} km de la base`;
      case "dose_over_limit":
        return `Dosis estimada de ${v.dose_msv.toFixed(2)} mSv, sobre el límite de ${v.limit_msv} mSv`;
      case "solar_event":
        return `Escenario de evento solar: hasta ${v.dose_mgy} mGy de dosis absorbida (mayo de 2024, el mayor medido por RAD hasta esa fecha). Desde el destino, el regreso a la base toma ${h(v.return_h)}`;
      default:
        return a.message;
    }
  }
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

/** Language saved in the browser, or English if there is none. */
function savedLang(): Lang {
  try {
    const saved = window.localStorage.getItem(STORAGE_KEY);
    if (saved === "es" || saved === "en") return saved;
  } catch {
    // No localStorage (private mode, server): it stays in English.
  }
  return "en";
}

interface LangState {
  lang: Lang;
  setLang: (lang: Lang) => void;
  /** Applies the saved language. It is called when the page mounts, not when the store is created:
   * the server always renders in English and React requires the browser's first render to match. */
  restore: () => void;
}

export const useLang = create<LangState>((set) => ({
  lang: "en",
  restore: () => {
    const lang = savedLang();
    document.documentElement.lang = lang;
    set({ lang });
  },
  setLang: (lang) => {
    try {
      window.localStorage.setItem(STORAGE_KEY, lang);
    } catch {
      // If it cannot be saved, the change only lasts for this visit.
    }
    document.documentElement.lang = lang;
    set({ lang });
  },
}));

/** Texts of the active language: `const t = useT(); t.planTitle`. */
export function useT(): Strings {
  return STRINGS[useLang((s) => s.lang)];
}
