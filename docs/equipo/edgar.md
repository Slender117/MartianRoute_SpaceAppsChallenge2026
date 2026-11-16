# Edgar · Science and validation

**Objective:** OE3 · HE3 and the general hypothesis.
**Milestones:** owner of H1; takes part in H2 and H3. **Backup:** Tulio. He is the backup for Tulio and
Miguel. **Presents** the pitch and answers the technical questions.

## Scope

Make sure every number in the model has a source or is marked as an assumption, classify the terrain by risk
and show with Perseverance's real traverse whether the routes are credible.

## Folders

- `science/` (`model/eva_cost.py`, `calibrate.py`, `convert_traverse.py`, `validation/`)
- `docs/supuestos.md`

## Tasks

- [x] Sourced parameters in `docs/supuestos.md`: Apollo rates (Waligora and Horrigan, 1975), the Minetti
      curve, RAD 0.64 mSv/day, and the Mars O₂ scenario with NASA suited data at 3/8 g (H1)
- [x] Fix the stretches: calibration with sol 606 or earlier, measurement with the later ones, not contiguous
      (H1). Inside the real region there are 18 for calibration and 18 for measurement (stretches 37 and 38
      fall outside the box); with the cut at 1000 there would be too few measurement stretches for the paired
      Wilcoxon (`science/validation/trechos.csv`)
- [x] NOAH-H class-to-risk table with sources, for Tulio (H2)
- [ ] Perseverance traverse cropped and with elevation, together with Tulio (H2)
- [x] Support Miguel in integrating the O₂ model (H3)
- [x] Metrics script: mean separation, distance, ascent and paired Wilcoxon (HE3) (H3)
- [x] Run the validation with frozen weights and build the results table, including what failed (H4):
      `science/validation/he3_resultados.md`
- [x] Pick with Miguel the demo points where the short route uses more O₂ (H4)
- [ ] Perseverance photos per segment for the stops (H4) **(droppable)**

## Per day

| 13 Nov | 14 Nov | 15 Nov |
| --- | --- | --- |
| Parameters, stretches and class-to-risk table | Validation with frozen weights; talk to mentors | Presents and answers technical questions |

## Receives and delivers

- **Receives** from Tulio: the traverse with elevation. From Miguel: the routes to validate.
- **Delivers** to Tulio: the class-to-risk table. To Miguel: the O₂ model and parameters. To the pitch:
  citable figures and the validation table.

## Out of scope

- Carrying over to Mars the lunar bunny hop, the Apollo thermal balance or the behavior of lunar dust.
- Inventing figures: if there is no open source, `[__]` and say so.
