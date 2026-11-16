# Exploratory HE3 (14 November 2026)

**This does not replace the HE3 result** (`he3_resultados.md`, which does not hold). These three variants
were run after seeing that result, so their p values are exploratory: they help decide what to measure next
time, not to claim the hypothesis. Each variant calibrates only with calibration stretches (sol ≤ 606) and
measures with the measurement ones. Script: `he3_exploratorio.py`.

| Variant | n cal / meas | Weights of A (slope, layer, instability) | A < B | B < C |
| --- | --- | --- | --- | --- |
| Stretches of 1 to 3 km | 9 / 9 | 4, **0.46**, 1.0 | 5–3, p = 0.29, r = 0.20 | 5–3, p = 0.16, r = 0.35 |
| NOAH-H as impassable fraction | 18 / 18 | 4, **10** (top of the grid), 1.0 | 6–9, p = 0.97 | 9–8, p = 0.25, r = 0.17 |
| Calibrating the slope too | 18 / 18 | **0.1**, 0, 0.1 | no discordant pairs | 9–7, p = 0.25, r = 0.17 |

"5–3" means it wins in 5 stretches and loses in 3. No variant meets p < 0.025 and r ≥ 0.3.

## What it suggests

- **Scale matters.** With stretches of 1 to 3 km, the calibration does give weight to NOAH-H (0.46): the loss
  drops from 50.7 m to 46.7 m. With 0.5 to 1 km it gave 0. The measurement does not confirm it, but with 9 pairs
  the test has little power. It is the first thing worth measuring with more stretches or a finer grid.
- **The impassable fraction overfits.** The calibration takes it to the top of the grid, as if large ripples
  were forbidden, but in the measurement the route ends up worse than without the layer (wins 6, loses 9).
- **At 25 m per cell, the rover looks like a straight line.** If the slope is calibrated too, every weight drops
  almost to zero. Perseverance avoids obstacles smaller than a cell with its autonomous navigation, and that
  does not show on this grid.

## For next time

1. Stretches of 1 to 3 km on a finer grid (1 m HiRISE where there is coverage), fixed in advance.
2. Validate against walking traverses (Apollo) instead of a rover, because the hypothesis is about people.
