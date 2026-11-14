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
  loading: boolean;
  error: string | null;

  loadRegions: () => Promise<void>;
  selectRegion: (id: string) => Promise<void>;
  openRegion: (id: string) => Promise<void>;
  arriveAtRegion: () => void;
  backToGlobe: () => void;
  toggleLayer: (layer: string) => void;
  setMode: (mode: WalkMode) => void;
  setSuit: (suit: Partial<SuitLimits>) => void;
  pickPoint: (p: LatLon) => void;
  computeRoutes: () => Promise<void>;
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
  loading: false,
  error: null,

  loadRegions: async () => {
    try {
      set({ regions: await api.regions(), error: null });
    } catch (e) {
      set({ error: (e as Error).message });
    }
  },

  selectRegion: async (id) => {
    set({ regionId: id, view: "zooming", start: null, end: null, routes: {}, traverse: null, safeReturn: null });
    try {
      set({ manifest: await api.region(id) });
    } catch (e) {
      set({ error: (e as Error).message, view: "globe" });
    }
  },

  // Entra directo a la vista de ruta, sin la animación desde el globo.
  openRegion: async (id) => {
    set({ regionId: id, start: null, end: null, routes: {}, traverse: null, safeReturn: null });
    try {
      set({ manifest: await api.region(id), view: "region" });
    } catch (e) {
      set({ error: (e as Error).message, regionId: null });
    }
  },

  arriveAtRegion: () => set({ view: "region" }),
  backToGlobe: () => set({ view: "globe", regionId: null, manifest: null, routes: {} }),

  toggleLayer: (layer) =>
    set(({ activeLayers }) => ({
      activeLayers: activeLayers.includes(layer)
        ? activeLayers.filter((l) => l !== layer)
        : [...activeLayers, layer],
    })),

  setMode: (mode) => set({ mode }),
  // Otro traje cambia los límites del mapa de regreso: se pide de nuevo si está visible.
  setSuit: (suit) => {
    set(({ suit: prev }) => ({ suit: { ...prev, ...suit }, safeReturn: null }));
    if (get().showSafeReturn) void get().loadSafeReturn();
  },

  // Primer clic = inicio, segundo = destino, tercero reinicia.
  pickPoint: (p) =>
    set(({ start, end }) =>
      !start || end ? { start: p, end: null, routes: {} } : { end: p },
    ),

  computeRoutes: async () => {
    const { regionId, start, end, suit } = get();
    if (!regionId || !start || !end) return;
    set({ loading: true, error: null });
    try {
      set({ routes: await api.compare({ region: regionId, start, end, suit }) });
    } catch (e) {
      set({ error: (e as Error).message, routes: {} });
    } finally {
      set({ loading: false });
    }
  },

  toggleTraverse: async () => {
    const { showTraverse, traverse, manifest } = get();
    if (!showTraverse && !traverse && manifest?.traverses[0]) {
      try {
        set({ traverse: await api.traverse(manifest.id, manifest.traverses[0]) });
      } catch (e) {
        set({ error: (e as Error).message });
        return;
      }
    }
    set({ showTraverse: !showTraverse });
  },

  // Pide el mapa la primera vez que se enciende; después solo lo muestra u oculta.
  toggleSafeReturn: async () => {
    const { showSafeReturn, safeReturn } = get();
    if (!showSafeReturn && !safeReturn) await get().loadSafeReturn();
    set({ showSafeReturn: !showSafeReturn });
  },

  loadSafeReturn: async () => {
    const { regionId, suit } = get();
    if (!regionId) return;
    try {
      const res = await api.safeReturn({ region: regionId, suit });
      // Al mover el deslizador llegan varias respuestas: solo vale la del traje actual.
      if (get().suit === suit && get().regionId === regionId) set({ safeReturn: res });
    } catch (e) {
      set({ error: (e as Error).message });
    }
  },
}));
