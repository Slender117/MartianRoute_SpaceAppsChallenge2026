// Espejo a mano de los esquemas Pydantic de la API.
// Reemplazar por los tipos generados en @wazemars/contracts (`npm run contracts`).

export type WalkMode = "safe" | "fast" | "science";

export type Provenance = "observed" | "derived" | "modeled";

export interface LatLon {
  lat: number;
  lon: number;
}

export interface SuitLimits {
  autonomy_h: number;
  max_slope_deg: number;
  max_dist_km: number;
  max_dose_msv?: number | null;
}

export interface RegionSummary {
  id: string;
  name: string;
  bbox: [number, number, number, number];
  base: LatLon;
}

export interface LayerMeta {
  provenance: Provenance;
  source: string;
}

export interface DemoScenario {
  label: string;
  start: LatLon;
  end: LatLon;
}

export interface RegionManifest extends RegionSummary {
  shape: [number, number];
  resolution_m: number;
  elevation_range: [number, number];
  layers: string[];
  traverses: string[];
  dataset_version: string;
  pipeline_commit: string | null;
  crs: string | null;
  synthetic: boolean;
  layer_meta: Record<string, LayerMeta>;
  checksums: Record<string, string>;
  demo: DemoScenario | null;
}

export interface PathPoint extends LatLon {
  elev: number;
  t_h: number;
}

export interface Stop extends LatLon {
  type: "science" | "ice";
  reason: string;
}

export interface Alert {
  at: number;
  type: "slope" | "autonomy" | "distance" | "radiation" | "climate";
  severity: "warning" | "critical";
  message: string;
}

export interface RouteDelta {
  distance_km: number;
  duration_h: number;
  duration_sols: number;
  o2_estimate_kg: number;
  radiation_msv: number;
  science_km: number;
  shared_path: number;
}

export interface RouteResponse {
  mode: WalkMode;
  path: PathPoint[];
  distance_km: number;
  duration_h: number;
  duration_sols: number;
  outbound_km: number;
  outbound_h: number;
  return_h: number;
  usable_autonomy_h: number;
  margin_h: number;
  o2_estimate_kg: number;
  o2_crew_kg: number;
  radiation_msv: number;
  solar_event_mgy: number | null;
  science_km: number;
  point_of_no_return: number | null;
  stops: Stop[];
  alerts: Alert[];
  feasible: boolean;
  cost_breakdown: { slope: number; hazard: number; instability: number; science_bonus: number };
  vs_safe: RouteDelta | null;
  synthetic_data: boolean;
  provenance: Record<string, Provenance>;
}

export interface TrackMetrics {
  distance_km: number;
  ascent_m: number;
}

export interface RouteValidation extends TrackMetrics {
  distance_ratio: number;
  mean_separation_m: number;
  max_separation_m: number;
}

export interface ValidationResponse {
  region: string;
  rover: string;
  synthetic_data: boolean;
  points_outside: number;
  traverse: TrackMetrics;
  routes: Record<WalkMode, RouteValidation>;
  provenance: Record<string, Provenance>;
}

export interface Assumption {
  id: string;
  label: string;
  value: number | string | null;
  unit: string | null;
  provenance: Provenance;
  source: string;
  note: string | null;
}

export interface AssumptionsResponse {
  parameters: Assumption[];
  limits: string[];
}

export interface TraverseGeoJSON {
  type: "Feature";
  properties: { rover: string };
  geometry: { type: "LineString"; coordinates: [number, number][] };
}
