import type {
  AssumptionsResponse,
  LatLon,
  LiveResponse,
  RegionManifest,
  RegionSummary,
  RouteResponse,
  SafeReturnResponse,
  SuitLimits,
  TraverseGeoJSON,
  WalkMode,
} from "./types";
import type { Lang } from "./i18n";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
export const ASSETS_URL = process.env.NEXT_PUBLIC_ASSETS_URL ?? `${API_URL}/assets`;

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
  });
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new Error(body?.detail ?? `Error ${res.status} en ${path}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  regions: () => request<RegionSummary[]>("/regions"),
  region: (id: string) => request<RegionManifest>(`/regions/${id}`),
  traverse: (id: string, rover: string) =>
    request<TraverseGeoJSON>(`/regions/${id}/traverse/${rover}`),
  route: (body: { region: string; start: LatLon; end: LatLon; mode: WalkMode; suit?: SuitLimits }) =>
    request<RouteResponse>("/routes", { method: "POST", body: JSON.stringify(body) }),
  // Devuelve los tres modos y la línea base ("baseline").
  compare: (body: {
    region: string;
    start: LatLon;
    end: LatLon;
    suit?: SuitLimits;
    solar_event?: boolean;
  }) =>
    request<Record<WalkMode, RouteResponse>>("/routes/compare", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  safeReturn: (body: { region: string; base?: LatLon; suit?: SuitLimits }) =>
    request<SafeReturnResponse>("/routes/safe-return", { method: "POST", body: JSON.stringify(body) }),
  assumptions: (lang: Lang) => request<AssumptionsResponse>(`/assumptions?lang=${lang}`),
  // Marte hoy: eyecciones solares (DONKI), posición de Perseverance y sus últimas imágenes.
  live: (region?: string) =>
    request<LiveResponse>(region ? `/live?region=${encodeURIComponent(region)}` : "/live"),
};

export const assetUrl = (regionId: string, path: string) => `${ASSETS_URL}/${regionId}/${path}`;
