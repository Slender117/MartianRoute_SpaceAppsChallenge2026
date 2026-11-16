# HE3: results against Perseverance's traverse (14 November 2026)

**Hypothesis:** the safe route with the NOAH-H terrain layer stays closer to Perseverance's real track than
without it, and that one stays closer than the minimum-distance route.

**Verdict: it does not hold.** Neither of the two comparisons fixed in advance meets p < 0.025 and r ≥ 0.3.

## Method

- Real `jezero` region (dataset 0.4.0, cells of 24.8 × 23.4 m), with the pipeline grids read as `.npy`.
- Straight 0.5 to 1 km stretches from `trechos.csv`: 18 for calibration (sol ≤ 606) and 18 for measurement.
  Stretches 37 and 38 fall outside the region box.
- Arms: A, Safe with NOAH-H; B, Safe without NOAH-H; C, minimum-distance baseline. The slope weight stays
  fixed at 4.0 and the maximum slope at 20°.
- Weights calibrated on the grid {0, 0.1 … 10} with the symmetric mean separation, and frozen in commit
  `eb6b7ae` before measuring: A and B end up with w_riesgo = 0 and w_inestabilidad = 2.15.
- Tests: one-sided paired Wilcoxon, normal approximation, r = |z|/√n with n the untied pairs.

## Results (18 measurement stretches)

| Comparison | Wins | Losses | Ties | p | r | Verdict |
| --- | --- | --- | --- | --- | --- | --- |
| A < B (with NOAH-H vs without NOAH-H) | 0 | 0 | 18 | — | — | Not supported: no discordant pairs |
| B < C (without NOAH-H vs baseline) | 9 | 8 | 1 | 0.25 | 0.17 | Not supported |

- **A < B was decided in the calibration.** The loss grows steadily with the NOAH-H weight, and the minimum
  was at w_riesgo = 0. With that, A and B are the same route.
- **B < C:** the medians (17.6 m and 25.3 m) look like an advantage, but the paired difference has a median of
  −2.9 m (range −32.9 to +27.5 m), less than one cell.

## Descriptives (not tests)

| Arm | Median separation | Distance / rover | Ascent − rover | Mean NOAH-H risk |
| --- | --- | --- | --- | --- |
| A = B | 17.6 m | 0.68 | −4.6 m | 0.25 |
| C, baseline | 25.3 m | 0.66 | −4.8 m | 0.26 |
| The app's Safe mode (4, 4, 2) | 30.2 m | 0.71 | −4.5 m | 0.16 |
| Rover | — | 1 | 0 | 0.28 |

- The app's Safe mode is the farthest from Perseverance and is worse than the baseline in 11 of 18 stretches.
  It is more conservative than the rover; for a person on foot that may be right.
- The rover drove over terrain with a mean NOAH-H risk of 0.28, while the region average is 0.42.

## Limits

- **Resolution.** All separations are around one cell (about 25 m). With this grid a difference smaller than a
  cell cannot be told apart. The 3 m HiRISE zone only covers 5 stretches, all of them for calibration. The rover
  chooses its path on board by evaluating trajectories about 6 m long (Abcouwer et al., 2021), well inside a
  single cell.
- **Selection.** Perseverance's landing site and traverses were planned for safety with HiRISE images. That
  NOAH-H matches the areas where it drove is evidence at the planning scale, not inside each stretch.
- **A rover is not a person.** It is calibrated against a rover's decisions, and the NOAH-H labels were made for
  the ExoMars rover.
- The frozen weights are only valid for dataset 0.4.0. If the region changes, it has to be recalibrated.

## Reproduce

```bash
python science/validation/he3.py calibrar --assets ../regions_real
python science/validation/he3.py medir --assets ../regions_real
```

Detail per stretch and arm in `he3_resultados.csv`; weights, loss surface and tests in `he3_resumen.json`. The
CSV and JSON keep their Spanish column names (`w_riesgo`, `perdida_m`...): they are the frozen record of the
test.

## Reference

- Abcouwer, N., Daftry, S., del Sesto, T., Toupet, O., Ono, M., Venkatraman, S., Lanka, R., Song, J., & Yue, Y.
  (2021). Machine learning based path planning for improved rover navigation. In *2021 IEEE Aerospace
  Conference* (pp. 1–9). IEEE. https://doi.org/10.1109/AERO50100.2021.9438337
