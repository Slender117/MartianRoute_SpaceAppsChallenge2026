// Hand-written mirror of the API's Pydantic schemas.
// Replace with the types generated in @wazemars/contracts (`npm run contracts`).

// "baseline" is the minimum-distance baseline: it is not a mode the astronaut picks,
// only the reference the other three are compared against.
export type WalkMode = "safe" | "fast" | "science" | "baseline";

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
  /** Hours of fixed work without walking (stops, sampling); 0 by default. */
  task_h?: number;
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
  /** Mineral or ice index at the stop (0-1). */
  value: number;
}

export interface Alert {
  at: number;
  type: "slope" | "autonomy" | "distance" | "radiation" | "climate";
  severity: "warning" | "critical";
  /** Text in English; the web builds each language from `code` and `values` (lib/i18n.ts). */
  message: string;
  code: string;
  values: Record<string, number>;
}

/** O₂ per astronaut between the two gravity bounds of the Minetti model (no central value). */
export interface O2Interval {
  low_kg: number;
  high_kg: number;
}

export interface RouteDelta {
  distance_km: number;
  duration_h: number;
  duration_sols: number;
  o2_estimate_kg: number;
  o2_interval_kg: O2Interval;
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
  o2_interval_kg: O2Interval;
  radiation_msv: number;
  solar_event_mgy: number | null;
  science_km: number;
  point_of_no_return: number | null;
  point_of_no_return_km: number | null;
  stops: Stop[];
  alerts: Alert[];
  feasible: boolean;
  cost_breakdown: { slope: number; hazard: number; instability: number; science_bonus: number };
  vs_safe: RouteDelta | null;
  vs_baseline: RouteDelta | null;
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

/** Response of POST /routes/safe-return. */
export interface SafeReturnResponse {
  region: string;
  base: LatLon;
  shape: [number, number];
  bbox: [number, number, number, number];
  /** Little-endian uint16 in base64, north row first; `no_return_value` = no return. */
  return_minutes: string;
  no_return_value: number;
  planned_limit_min: number;
  total_limit_min: number;
  planned_area_fraction: number;
  total_area_fraction: number;
  unreachable_fraction: number;
  max_eva_dose_msv: number;
  synthetic_data: boolean;
  provenance: Record<string, Provenance>;
}

// Live NASA data (GET /live). `status` says whether it comes from NASA now or from the saved copy.
export interface LiveSource {
  name: string;
  url: string;
  status: "live" | "snapshot";
  fetched_at: string;
  provenance: Provenance;
  error: string | null;
}

export interface CmeArrival {
  simulation_id: string;
  cme_id: string | null;
  cme_start: string | null;
  speed_km_s: number | null;
  arrival_time: string;
  glancing_blow: boolean;
  minor_impact: boolean;
  model_completion: string;
  link: string;
}

export interface RoverPosition {
  source: LiveSource;
  rover: string;
  sol: number;
  site: number;
  drive: number;
  lat: number;
  lon: number;
  elevation_m: number | null;
  odometry_km: number | null;
  distance_to_base_km: number | null;
  in_region: boolean | null;
}

export interface RoverImage {
  image_id: string;
  sol: number;
  taken_utc: string;
  camera: string;
  thumbnail_url: string;
  full_url: string | null;
  page_url: string | null;
}

export interface LiveResponse {
  generated_at: string;
  space_weather: {
    source: LiveSource;
    arrivals: CmeArrival[];
    alert: CmeArrival | null;
    alert_before_h: number;
    alert_after_h: number;
  };
  rover: RoverPosition | null;
  images: { source: LiveSource; latest_sol: number | null; images: RoverImage[] };
}
