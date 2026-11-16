# Predictive EVA cost model (cost per cell + least-cost search)

Prototype by Edgar (Science and validation), 2026-11-12. Code: [eva_cost.py](eva_cost.py). Test:
[test_eva_cost.py](test_eva_cost.py). It needs `numpy`, `scipy` and `scikit-image`, which the team's engine
already uses, and `pytest` for the tests:

```bash
cd science/model && python -m pytest -q
```

## What it does

It predicts how much O₂ each meter of an EVA that returns along the same path costs. That curve becomes the
slope penalty of the grid the route search walks, and also an O₂ interval per route. It has two parts:

| Part | What it is | Is it trained |
| --- | --- | --- |
| Slope and gravity | Curve of Minetti et al. (2002), scaled with a lower and an upper gravity bound | No: it is physics with an interval |
| Hazard and instability | Weights of `hazard` and `1 − thermal inertia` | Yes, against the real traverse, with segments held out for measuring |

A route's output is an O₂ **interval** (`o2_interval_kg`), not a single figure. The central value does not
exist because there is no source for how the flat-ground cost changes at 0.38 g.

## What goes in

| Data | From | Owner |
| --- | --- | --- |
| `dem.npy`, `slope.npy` | `data/regions/jezero/` | Data |
| `layers/hazard.npy`, `layers/thermal_inertia.npy` | `data/regions/jezero/layers/` | Data |
| Perseverance traverse | `M20_traverse_2026-11-12.json` (559 segments per sol, sol 14 to 2022, CRS84) and `M20_waypoints_2026-11-12.json`. `science/convert_traverse.py` turns it into a single LineString; 4,688 points from sols 1698 to 2022 fall west of the `regions.yaml` bbox (lon < 77.25): widen the bbox or crop | Science with Data |
| `o2_flat_kg_per_m` | `o2_rate / base_speed` from `docs/supuestos.md`: 0.07 kg/h ÷ 2000 m/h = 3.5e-5 kg/m (lunar scenario; see "Mars O₂ scenario" in `docs/supuestos.md`) | Backend |
| Gravity | 0.38 g in this prototype; the API engine uses 3.728 m/s² (GM / R² with Konopliv et al., 2020) | Science |

## What comes out and how it is delivered

1. **A `slope_penalty` function** that replaces the slope term of `engine/cost.py` (the
   `integracion_motor.patch` patch does not go in this PR). It is delivered by PR, agreeing on the interface
   with Backend first: the engine code is theirs. `cell_cost` stays as a variant in physical units, which I do
   not recommend.
2. **Two calibrated weights** (`w_hazard`, `w_instability`) with their `modeled` label and the caption
   "calibrated with Perseverance's traverse", for `docs/supuestos.md`.
3. **`o2_interval_kg`** for the EVA panel, with the interval instead of the single figure.
4. **A metrics note** with the separation on unseen segments, for H3.

## Fit into `engine/cost.py` (tested on a local copy, without touching `apps/`)

The change is two lines and an import in `cost.py`, plus copying `eva_cost.py` into `engine/`. I tested it on
a clean copy of `main` from 12 November. The patch is not included in this PR until it is agreed with Backend.

```diff
-    slope_n = np.clip(grids.slope / max_slope_deg, 0, 1)
+    slope_n = slope_penalty(grids.slope, max_slope_deg)
...
-        + w["slope"] * slope_n**2
+        + w["slope"] * slope_n
```

It keeps the team's structure and per-mode weights; it only changes the shape of the slope penalty.

- **The team's 51 tests pass** before and after (with the synthetic region from `marsdata synthetic`).
- **Synthetic demo:** the routes change cells, but distance and duration change by 1 % or less.

| Mode | Outbound (km) before → after | Maximum slope | Maximum hazard |
| --- | --- | --- | --- |
| Safe | 6.74 → 6.80 | 7.6° → 5.6° | 0.06 → 0.06 |
| Fast | 5.87 → 5.87 | 24.9° → 24.9° | 0.87 → 0.89 |
| Science | 7.50 → 7.50 | 10.2° → 7.6° | 0.00 → 0.00 |

- **Variant in physical units (`cell_cost`):** it also passes the 51 tests, but Fast stops crossing slopes
  (maximum from 24.9° to 4.7°) because all modes share the same penalty. It loses what tells the modes apart,
  so I do not recommend it for the current engine.
- **What the tests do not protect:** they do not pin cost or route figures, which is why they pass with three
  different calculations. A scale error in the slope would also pass. The 6 tests of this folder cover the
  curve.
- **O₂:** `test_consumables_cover_the_pair` pins `o2_estimate_kg = duration × 0.07`, and the patch does not
  touch it. Showing the interval requires new fields in `RouteResponse`, its provenance label (required by
  `test_every_figure_has_a_provenance_label`), regenerating `packages/contracts` and the interface. That is
  Backend and Frontend work, and it goes separately.
- **Documents:** the formula in `docs/arquitectura.md` and in `CLAUDE.md` must change `(slope/max)²` to the O₂
  penalty. If parameters are added to `/assumptions`, `test_every_assumption_is_documented` requires them in
  `docs/supuestos.md`; the patch adds none.
- **Patch scope:** it only carries the physics (`slope_penalty`, `o2_*`). The calibration (`route`,
  `separation_m`, `fit_weights`) stays in [calibrate.py](calibrate.py), an offline script that does not go into
  the engine.
- **Gravity does not reach the route.** `slope_penalty` is normalized against the maximum slope and the scale
  `s` cancels, so changing from 0.38 g to 0.16 g does not change the search's path; it only changes the
  reported O₂ (`o2_interval_kg`). It is consistent with having no source for the effect of gravity on route
  preference, but it limits reuse: changing planet changes the O₂ figure, not the route.
- **The shape changes, and that is what Backend will ask about.** The penalty is almost linear instead of
  quadratic, because the uphill Minetti curve is interpolated between only two knots. At half the maximum
  slope it goes from 0.25 to 0.45:

| Slope | 5° | 10° | 12.5° | 20° | 25° |
| --- | --- | --- | --- | --- | --- |
| Before, (slope/max)² | 0.04 | 0.16 | 0.25 | 0.64 | 1.00 |
| Now | 0.13 | 0.34 | 0.45 | 0.79 | 1.00 |

  That is why Safe lowers its maximum slope from 7.6° to 5.6°: moderate slopes cost almost twice as much
  relative to the steep ones. With more knots of the curve the uphill segment would gain curvature.
- The demo terrain has almost no slope (mean of 1° to 3°): there the team's time-based O₂ falls 2 to 4 % below
  Minetti's lower bound. With the real Jezero the effect may be larger; I did not measure it.

## What I checked and what I did not

- The 6 tests pass: the curve reproduces the four points of Minetti's abstract, the penalty is 0 on flat
  ground and 1 at the limit and does not depend on gravity, the interval is ordered and exact on flat ground,
  and the fit improves the route on unseen segments.
- **Synthetic test:** with known weights (3.0 and 1.0) the fit returned 4.64 and 1.00. On unseen segments the
  separation was 7.0 m, against 25.6 m with default weights. The data comes from the same model family, so this
  tests the mechanics, not the science.
- **Against the team's time-based model** (O₂ per meter relative to flat ground, out and back):

| Slope | Team | Minetti, lower bound | Minetti, upper bound |
| --- | --- | --- | --- |
| 5 % | 1.02 | 1.15 | 1.40 |
| 10 % | 1.21 | 1.31 | 1.81 |
| 20 % | 1.72 | 1.80 | 3.10 |
| 30 % | 2.44 | 2.29 | 4.40 |
| 45 % | 4.12 | 3.03 | 6.34 |

  The team's model is about 5 to 10 % below the lower bound between 5 and 20 %, and inside the interval from
  30 %. It does not contradict it: it places it inside a sourced range.
- None of this was tested with real Jezero data yet (that came later with HE3, in `science/validation/`).

## Limits

- The curve comes from 10 runners on a treadmill, at 1 g and without a suit. It only serves for the shape;
  the knots are the four from the abstract and not the full text's polynomial, which I could not access.
- The source for scaling to 0.38 g and for the suit factor is missing. The suit is inside `o2_flat_kg_per_m`.
  NASA's suited data at 3/8 g (the Mars O₂ scenario in `docs/supuestos.md`) came later.
- `slope.npy` is a magnitude without direction: following a contour line is penalized like climbing. Fixing it
  requires per-edge costs with the DEM, which means another Dijkstra and is Backend's.
- Perseverance drives with science goals and autonomous navigation. The calibrated weights are a rover's, not
  a person's, and the validation (H3) must be measured on segments not used for calibration.
- The Safe, Fast and Science modes stay as they are: this model does not replace them.

## Sources (DOIs resolve at doi.org; abstracts only)

- Minetti, A. E., Moia, C., Roi, G. S., Susta, D., & Ferretti, G. (2002). Energy cost of walking and running at
  extreme uphill and downhill slopes. *Journal of Applied Physiology*. https://doi.org/10.1152/japplphysiol.01177.2001
- Richter, C., Braunstein, B., Winnard, A., Nasser, M., & Weber, T. (2017). Human biomechanical and cardiopulmonary
  responses to partial gravity: A systematic review. *Frontiers in Physiology*. https://doi.org/10.3389/fphys.2017.00583
  (read in full text: it reports that Shavelson (1968) found a drop in metabolic rate with gravity in 4 of
  5 studies, except with high mechanical work; it gives no factor for 0.38 g, so I do not use it as a number).

## AI use

Written with the help of Claude Code. The tests and the comparison with the team's engine were run on a local
copy of `main`; the DOIs were resolved at doi.org.
