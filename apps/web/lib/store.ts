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

/** globe → zooming (camera approaches the site) → region (detailed terrain). */
export type View = "globe" | "zooming" | "region";

// Moving a suit slider sends many changes in a row: it waits until it stops
// before requesting the safe-return map or the routes again.
const SUIT_DEBOUNCE_MS = 300;
let suitTimer: ReturnType<typeof setTimeout> | undefined;
// Only the response to the last route request counts (if two are requested in a row, the old one is ignored).
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
  /** Solar event scenario during the EVA (dose of the May 2024 event). */
  solarEvent: boolean;
  loading: boolean;
  error: string | null;
  /** The region relief is already on screen (for the loading notice). */
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
  /** Marks the start and destination of the region's scenario and computes the routes. */
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

  // It goes straight to the route view, without the animation from the globe.
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
  // Another suit changes the return-map limits and the route alerts: both are requested
  // again (if they are on screen) when the slider stops.
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

  // With routes already computed, they are recomputed so the alerts reflect the scenario.
  setSolarEvent: (on) => {
    set({ solarEvent: on });
    if (Object.keys(get().routes).length) void get().computeRoutes();
  },

  // First click = start, second = destination (and the routes are computed), third starts over.
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

  // The checkbox changes instantly; the traverse downloads the first time and appears when it arrives.
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

  // It requests the map the first time it is turned on; afterwards it only shows or hides it.
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
      // Moving the slider brings several responses: only the one for the current suit counts.
      if (get().suit === suit && get().regionId === regionId) set({ safeReturn: res });
    } catch (e) {
      set({ error: (e as Error).message, showSafeReturn: false });
    }
  },
}));
