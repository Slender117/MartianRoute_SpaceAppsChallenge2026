import type {
  LatLon,
  RegionManifest,
  RegionSummary,
  RouteResponse,
  SuitLimits,
  TraverseGeoJSON,
  WalkMode,
} from "./types";

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
  compare: (body: { region: string; start: LatLon; end: LatLon; suit?: SuitLimits }) =>
    request<Record<WalkMode, RouteResponse>>("/routes/compare", {
      method: "POST",
      body: JSON.stringify(body),
    }),
};

export const assetUrl = (regionId: string, path: string) => `${ASSETS_URL}/${regionId}/${path}`;
