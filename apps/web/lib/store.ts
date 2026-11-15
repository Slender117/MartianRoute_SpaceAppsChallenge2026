import { create } from "zustand";

import { api } from "./api";
import type {
  LatLon,
  RegionManifest,
  RegionSummary,
  RouteResponse,
  SafeReturnResponse,
  SuitLimits,
  TraverseGeoJSON,
  WalkMode,
} from "./types";

/** globe → zooming (cámara se acerca al sitio) → region (terreno detallado). */
export type View = "globe" | "zooming" | "region";

// Al mover un deslizador del traje llegan muchos cambios seguidos: se espera a que se detenga
// antes de pedir otra vez el mapa de regreso seguro o las rutas.
const SUIT_DEBOUNCE_MS = 300;
let suitTimer: ReturnType<typeof setTimeout> | undefined;
// Solo vale la respuesta de la última petición de rutas (si se piden dos seguidas, la vieja se ignora).
let routeRequest = 0;

interface MapState {
  regions: RegionSummary[];
  view: View;
  regionId: string | null;
  manifest: RegionManifest | null;
  activeLayers: string[];
  mode: WalkMode;
  suit: SuitLimits;
  start: LatLon | null;
  end: LatLon | null;
  routes: Partial<Record<WalkMode, RouteResponse>>;
  traverse: TraverseGeoJSON | null;
  showTraverse: boolean;
  safeReturn: SafeReturnResponse | null;
  showSafeReturn: boolean;
  /** Escenario de evento solar durante la EVA (dosis del evento de mayo de 2024). */
  solarEvent: boolean;
  loading: boolean;
  error: string | null;
  /** El relieve de la región ya está en pantalla (para el aviso de carga). */
  terrainReady: boolean;

  loadRegions: () => Promise<void>;
  selectRegion: (id: string) => Promise<void>;
  openRegion: (id: string) => Promise<void>;
  arriveAtRegion: () => void;
  backToGlobe: () => void;
  toggleLayer: (layer: string) => void;
  setMode: (mode: WalkMode) => void;
  setSuit: (suit: Partial<SuitLimits>) => void;
  setSolarEvent: (on: boolean) => void;
  pickPoint: (p: LatLon) => void;
  clearPoints: () => void;
  /** Marca el inicio y el destino del escenario de la región y calcula las rutas. */
  loadDemo: () => void;
  computeRoutes: () => Promise<void>;
  setTerrainReady: (ready: boolean) => void;
  toggleTraverse: () => Promise<void>;
  toggleSafeReturn: () => Promise<void>;
  loadSafeReturn: () => Promise<void>;
}

export const useMapStore = create<MapState>((set, get) => ({
  regions: [],
  view: "globe",
  regionId: null,
  manifest: null,
  activeLayers: [],
  mode: "safe",
  suit: { autonomy_h: 8, max_slope_deg: 20, max_dist_km: 10 },
  start: null,
  end: null,
  routes: {},
  traverse: null,
  showTraverse: false,
  safeReturn: null,
  showSafeReturn: false,
  solarEvent: false,
  loading: false,
  error: null,
  terrainReady: false,

  loadRegions: async () => {
    try {
      set({ regions: await api.regions(), error: null });
    } catch (e) {
      set({ error: (e as Error).message });
    }
  },

  selectRegion: async (id) => {
    routeRequest++;
    set({
      regionId: id,
      view: "zooming",
      start: null,
      end: null,
      routes: {},
      traverse: null,
      safeReturn: null,
      terrainReady: false,
    });
    try {
      set({ manifest: await api.region(id) });
    } catch (e) {
      set({ error: (e as Error).message, view: "globe" });
    }
  },

  // Entra directo a la vista de ruta, sin la animación desde el globo.
  openRegion: async (id) => {
    routeRequest++;
    set({ regionId: id, start: null, end: null, routes: {}, traverse: null, safeReturn: null, terrainReady: false });
    try {
      set({ manifest: await api.region(id), view: "region" });
    } catch (e) {
      set({ error: (e as Error).message, regionId: null });
    }
  },

  arriveAtRegion: () => set({ view: "region" }),
  backToGlobe: () => {
    routeRequest++;
    set({ view: "globe", regionId: null, manifest: null, routes: {}, loading: false, terrainReady: false });
  },

  toggleLayer: (layer) =>
    set(({ activeLayers }) => ({
      activeLayers: activeLayers.includes(layer)
        ? activeLayers.filter((l) => l !== layer)
        : [...activeLayers, layer],
    })),

  setMode: (mode) => set({ mode }),
  // Otro traje cambia los límites del mapa de regreso y las alertas de las rutas: los dos se piden
  // de nuevo (si están en pantalla) cuando el deslizador se detiene.
  setSuit: (suit) => {
    set(({ suit: prev }) => ({ suit: { ...prev, ...suit } }));
    clearTimeout(suitTimer);
    suitTimer = setTimeout(() => {
      const { showSafeReturn, routes } = get();
      if (showSafeReturn) void get().loadSafeReturn();
      else set({ safeReturn: null });
      if (Object.keys(routes).length) void get().computeRoutes();
    }, SUIT_DEBOUNCE_MS);
  },

  // Con rutas ya calculadas, se recalculan para que las alertas reflejen el escenario.
  setSolarEvent: (on) => {
    set({ solarEvent: on });
    if (Object.keys(get().routes).length) void get().computeRoutes();
  },

  // Primer clic = inicio, segundo = destino (y se calculan las rutas), tercero empieza de nuevo.
  pickPoint: (p) => {
    const { start, end } = get();
    if (!start || end) {
      routeRequest++;
      set({ start: p, end: null, routes: {}, loading: false, error: null });
      return;
    }
    set({ end: p });
    void get().computeRoutes();
  },

  clearPoints: () => {
    routeRequest++;
    set({ start: null, end: null, routes: {}, loading: false, error: null });
  },

  loadDemo: () => {
    const demo = get().manifest?.demo;
    if (!demo) return;
    set({ start: demo.start, end: demo.end, routes: {} });
    void get().computeRoutes();
  },

  computeRoutes: async () => {
    const { regionId, start, end, suit, solarEvent } = get();
    if (!regionId || !start || !end) return;
    const request = ++routeRequest;
    set({ loading: true, error: null });
    try {
      const routes = await api.compare({ region: regionId, start, end, suit, solar_event: solarEvent });
      if (request === routeRequest) set({ routes });
    } catch (e) {
      if (request === routeRequest) set({ error: (e as Error).message, routes: {} });
    } finally {
      if (request === routeRequest) set({ loading: false });
    }
  },

  setTerrainReady: (ready) => set({ terrainReady: ready }),

  // La casilla cambia al instante; el recorrido se descarga la primera vez y aparece al llegar.
  toggleTraverse: async () => {
    const { showTraverse, traverse, manifest } = get();
    set({ showTraverse: !showTraverse });
    if (!showTraverse && !traverse && manifest?.traverses[0]) {
      try {
        set({ traverse: await api.traverse(manifest.id, manifest.traverses[0]) });
      } catch (e) {
        set({ error: (e as Error).message, showTraverse: false });
      }
    }
  },

  // Pide el mapa la primera vez que se enciende; después solo lo muestra u oculta.
  toggleSafeReturn: async () => {
    const { showSafeReturn, safeReturn } = get();
    set({ showSafeReturn: !showSafeReturn });
    if (!showSafeReturn && !safeReturn) await get().loadSafeReturn();
  },

  loadSafeReturn: async () => {
    const { regionId, suit } = get();
    if (!regionId) return;
    try {
      const res = await api.safeReturn({ region: regionId, suit });
      // Al mover el deslizador llegan varias respuestas: solo vale la del traje actual.
      if (get().suit === suit && get().regionId === regionId) set({ safeReturn: res });
    } catch (e) {
      set({ error: (e as Error).message, showSafeReturn: false });
    }
  },
}));
