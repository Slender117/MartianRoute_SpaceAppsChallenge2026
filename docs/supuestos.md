# Model assumptions and limits

Every numeric parameter of the engine appears here with its source. The API serves the same list at
`GET /assumptions` (English by default, Spanish with `?lang=es`), read from the code constants
(`apps/api/app/engine/assumptions.py`), and a test fails if an API parameter is missing from this file.

**`[__]`** means the value is an assumption with no confirmed open source: it is not mission data or a
suit specification. These are open questions of the project.

## Parameters

| ID | Parameter | Value | Label | Source |
| --- | --- | --- | --- | --- |
| `base_speed` | Suited speed on flat ground | 2 km/h | modeled | Coan (2020), §4.2.1.3.1.1: lunar pace on nearly flat regolith |
| `tobler_coefficient` | Tobler function coefficient | 3.5 | modeled | Tobler (1993), scaled to the suited speed |
| `o2_rate` | O₂ use per person | 0.07 kg/h | modeled | Waligora and Horrigan (1975), table 2: mean of the Apollo lunar EVAs; converted with Weir (1949). Lunar scenario; see "Mars O₂ scenario" |
| `o2_flat_per_m` | O₂ per meter on flat ground | 3.5 × 10⁻⁵ kg/m | modeled | Derived: `o2_rate` ÷ `base_speed`. NASA has no suited data at 3/8 g and 2 km/h |
| `slope_cost_curve` | Walking cost by slope | 1.64 J/kg/m on flat ground; 17.33 at +45 % | observed | Minetti et al. (2002); shape only |
| `mars_gravity` | Surface gravity of Mars | 3.728 m/s² | derived | GM / R² with GM = 42,828.37 km³/s² from Konopliv et al. (2020) and the 3,389.5 km mean radius |
| `crew_size` | EVA crew | 2 | modeled | Project decision; DRA 5.0 calls for 2 to 4 people per EVA on Mars (Drake, 2009, §5.2.1) |
| `autonomy` | Suit autonomy | 8 h | modeled | Coan (2020), §4.1.4: EVAs of up to 8 h (6 ± 2 h), plus 1 h of secondary O₂; Drake and Watts (2014), §9.2 |
| `autonomy_reserve` | Autonomy reserve | 20 % | modeled | Project decision; NASA sets no reserve for Mars (hourly consumables TBD in Drake and Watts, 2014, p. 403) |
| `task_time` | Fixed EVA work (not walking) | 0 h | modeled | `[__]`: set per request with `suit.task_h` |
| `walkback_reserve` | Minimum reserve when returning to base | 30 min | modeled | Project decision (team plan); no source with a DOI yet. The stricter of this and the 20 % applies |
| `max_slope` | Maximum walkable slope | 20° | modeled | Coan (2020), §4.2.1.3: climb, descend or traverse slopes of up to 20°. 20° is a 36 % grade; NASA has only tested suited walking up to 30 % (~16.7°; Norcross et al., 2010) |
| `max_distance` | Maximum distance to base | 10 km | modeled | Emergency walk-back: Coan (2020), §4.2.1.3.1.1; NASA (2025), [V2 11030]; Drake and Watts (2014), §9.2. Lunar assumption; Mars to be determined. Scenarios: 1.8 to 3.5 km (Ogilvie et al., 2026) and 15 km (Drake, 2009, notional) |
| `max_dose` | Per-EVA dose limit | no value | modeled | NASA (2023), §4.8: there is no per-EVA limit |
| `career_dose_limit` | Career effective dose limit | 600 mSv | observed | NASA (2023), [V1 4030] |
| `radiation_rate` | Surface dose equivalent | 0.64 ± 0.12 mSv/day | observed | Hassler et al. (2014): Gale, ~300 days at solar maximum (2012-2013), not Jezero; range of 0.25 to 0.95 mSv/day in Guo et al. (2021) |
| `solar_event_dose` | Absorbed dose of the solar event scenario | 8.1 mGy | observed | NASA JPL (2024) |
| `solar_alert_before` | Alert start before a solar ejection reaches Mars | 72 h | modeled | Project decision; the arrival is forecast by WSA-ENLIL in DONKI (NASA's CCMC) |
| `solar_alert_after` | Alert end after the arrival | 48 h | modeled | Project decision |
| `sol_length` | Length of a sol | 24.6598 h | observed | NASA GISS Mars24 |
| `mars_radius` | Mars radius | 3,389.5 km | observed | Project convention (mean radius) |
| `slope_warning` | Steep segment warning | 80 % of the maximum slope | modeled | Project decision |
| `science_threshold` | Mineral stop threshold | index 0.6 | modeled | Project decision |
| `ice_threshold` | Ice stop threshold | index 0.6 | modeled | Project decision |
| `stop_gap` | Minimum spacing between stops | 15 points | modeled | Project decision |
| `min_cell_cost` | Minimum cost per cell | 0.1 | modeled | Project decision |
| `weights_safe` | Safe mode weights | slope 4, hazard 4, instability 2, science 0 | modeled | Project decision |
| `weights_fast` | Fast mode weights | slope 0.5, hazard 1, instability 0.3, science 0 | modeled | Project decision |
| `weights_science` | Science mode weights | slope 1.5, hazard 2, instability 1, science 0.8 | modeled | Project decision |
| `weights_baseline` | Baseline weights (minimum distance) | all 0 | modeled | Project decision |

## Notes on radiation

- **Background rate.** `CLAUDE.md` asked to check the approximate value of 0.67 mSv/day. Hassler et al.
  (2014) report 0.64 ± 0.12 mSv/day (0.21 ± 0.04 mGy/day absorbed dose) over Curiosity's first 300 days
  in Gale. A later review cites 0.67 for another averaging period; the value from the original paper is
  used. The real dose varies with the solar cycle and the atmospheric pressure: between solar maximum and
  minimum, RAD measured 0.25 to 0.95 mSv/day in Gale (Guo et al., 2021, §4.3.4). The 0.64 figure does
  not appear in the abstract of Hassler et al. (2014) and the full text could not be read. There is no
  measured dose in Jezero; with the MEDA pressure, the dose would be 1.0 to 1.1 times Gale's (our own
  estimate with the pressure sensitivity in Guo et al., 2021).
- **Solar event.** The scenario uses the event of 20 May 2024: 8.1 mGy next to the rover, the largest
  measured by RAD up to that date. It was the strongest of 19 particle events recorded at the surface in
  ~12.5 years, with a peak of 352 µGy/h (Posner et al., 2025). It is applied in full as the worst observed
  case, not as a prediction: a future event could be larger. It is absorbed dose, so it is not added to
  the background mSv: converting it requires that event's quality factor, which we do not have.
- **No per-EVA limit.** NASA-STD-3001 Vol. 1 Rev. C (NASA, 2023, §4.8), which replaces Rev. B with the
  same text, does not define a per-EVA limit. It defines two: the career effective dose must be below
  600 mSv for any age and sex, adding up all missions ([V1 4030]), and the design must protect the crew
  from the reference solar event (the October 1989 events) below 250 mSv ([V1 4031]). The API reports
  the career limit (`career_dose_limit`), reports the EVA dose and only raises an alert if the client
  sends `max_dose_msv`. The same standard sets 250 mGy-Eq in 30 days for the blood-forming organs
  (table 4.8-1).
- **Alerts.** DONKI (NASA) warns when a solar ejection (CME) reaches Mars, but its catalog of particle
  events has no measurements at Mars. For those events, Löwe et al. (2025) propose alerting when the
  local dose exceeds the background by 25 %, which gives at least 30 min of warning.

## Notes on the EVA limits

- **They are lunar values.** Speed, autonomy, maximum slope and distance to base come from Artemis
  documents for the Moon. Coan (2020, §4.1.4.4) says Mars EVA planning is still ongoing; they are
  applied to Mars as an assumption (`modeled`), untested at 0.38 g.
- **Distance to base: 10 km.** It is the walk-back limit if the rover fails. Coan (2020, §4.2.1.3.1.1)
  gives less than 5 h of walking at 2 km/h, about 10 km, still to be confirmed (TBR). The rationale of
  requirement [V2 11030] of NASA-STD-3001 Vol. 2 Rev. E (NASA, 2025, §11.2.3.2) records that the Apollo
  astronauts asked for water for a 10 km return if the vehicle failed. DRA 5.0 (Drake and Watts, 2014,
  §9.2, assumption l.6) assumes 10 km on the Moon and leaves Mars to be determined, because it has not
  been tested at Martian gravity. For a walking-only EVA, with no rover, Coan (2020) gives 2 km radial
  and 16 km cumulative. For Mars, NASA's most recent work considers a 30 or 60 min walk-back at 2.2 mph,
  that is ~1.8 or ~3.5 km (Ogilvie et al., 2026). The ~15 km of DRA 5.0 (Drake, 2009, §2.1) is a
  planning figure without a derivation.
- **Speed: 2 km/h.** Coan (2020) gives it on nearly flat regolith, with no slope or rocks; the engine's
  Tobler function lowers it with slope.
- **Slope: 20°.** Coan (2020, §4.2.1.3) calls for walking up, down or across slopes of up to 20°;
  Apollo 15 walked on slopes of about 17°. 20° is a 36 % grade (tan 20° = 0.36), and NASA has only
  measured suited walking up to 30 % (~16.7°; Norcross et al., 2010): between 30 and 36 % there is no
  NASA suited data.
- **O₂ use: 0.07 kg/h per person.** The mean metabolic rate of all Apollo 11 to 17 lunar EVAs was
  980 × 10³ J/h (234 kcal/h), measured over 158.7 h of EVA (Waligora and Horrigan, 1975, table 2); per
  EVA and astronaut it was 197 to 302 kcal/h. With the Weir (1949) equation, over the whole range of the
  respiratory quotient (0.7 to 1.0), 234 kcal/h equals 0.066 to 0.071 kg/h of O₂ (1.429 g/L). It was
  measured on the Moon (1/6 g) with the A7L suit; on Mars it costs more: see "Mars O₂ scenario".
- **Autonomy: 8 h.** Coan (2020, §4.1.4) sets EVAs of up to 8 h (6 ± 2 h) with 1 extra hour of
  secondary O₂ for contingencies; DRA 5.0 (§9.2) calls for a suit for 8 h EVAs. The 20 % reserve
  (`autonomy_reserve`) is still a project decision.
- **What does come from Mars.** The 8 h autonomy (Drake and Watts, 2014, §9.2) and the two-person EVA
  (Drake, 2009, §5.2.1) come from NASA documents for Mars.
- **Sustainable workload.** NASA considers working at 30-40 % of maximum aerobic capacity sustainable
  over a long EVA, measured in lunar simulations (Strock et al., 2024). For Mars, Ogilvie et al. (2026)
  propose ~43 % over 8 h. Suited walking on Mars (19-22 mL/kg/min) is 52-61 % of a minimum fitness of
  36.5 mL/kg/min (our own calculation; the 36.5 figure is still to be confirmed in the standard). That is
  why 8 h of autonomy are not 8 h of continuous walking.
- **Mars rules the model does not use yet.** At most 12 h of EVA every 48 h and 24 h per week (Drake
  and Watts, 2014, p. 399); another crew member must be able to arrive within 45 min (p. 401); beyond
  the walk-back distance a shelter is needed (Drake, 2009, addendum, p. 283).

## Mars O₂ scenario

The values in the table (0.07 kg/h and 3.5 × 10⁻⁵ kg/m) are the **lunar scenario**. They match the
Apollo mean and the "Apollo" column of the EVA Walkback Test (0.15 lb/h ≈ 0.068 kg/h; Norcross et al.,
2008). NASA has not published a design consumption for Mars: hourly O₂ use is still "TBD" (Drake and
Watts, 2014, p. 403). It also states that Martian gravity "will present higher workloads" than lunar
gravity (Dunn et al., 2022).

| Source | Condition | VO₂ | O₂ per person | Label |
| --- | --- | --- | --- | --- |
| Norcross et al. (2008) | Mark III suit, 3/8 g, flat, 1.07 m/s | ~20-22 mL/kg/min (read from the chart) | ~0.15 kg/h | observed |
| Ogilvie et al. (2026), §III.C.3 | Extrapolation to 0.98 m/s (2.2 mph), 3/8 g | ~19 mL/kg/min | 0.12-0.13 kg/h | modeled |
| Norcross et al. (2010), IST-2 | Suit, simulated 0.32 g (~85 % of Martian weight), 0.56-0.97 m/s, flat | ~16 mL/kg/min (read from the chart) | ~0.11 kg/h | observed |

The conversions to kg/h are our own calculation, for an 81 kg person and 1.429 g/L of O₂. The Mars
scenario costs **1.6 to 2.2 times** the lunar scenario.

**Per meter there is no Martian data at 2 km/h (0.56 m/s).** The EVA Walkback Test did not test speeds
below ~1.07 m/s ("Did not test at lower walking speeds", Ogilvie et al., 2026, presentation). With IST-2,
depending on each subject's speed, the cost is between **3.2 and 5.5 × 10⁻⁵ kg/m** (our own calculation,
indicative). The project value, 3.5 × 10⁻⁵, is at the low end of that range.

## O₂ cost by slope (`science/model/eva_cost.py`)

Shape of the walking cost curve by slope, from Minetti et al. (2002), measured at 1 g without a suit
(values from the abstract). It is only used as a multiplier relative to flat ground. It enters the API
engine in `apps/api/app/engine/o2_model.py`.

| Slope (rise / run) | Walking cost | Label | Source |
| --- | --- | --- | --- |
| -45 % | 3.46 J/kg/m | observed | Minetti et al. (2002) |
| -10 % (minimum) | 0.81 J/kg/m | observed | Minetti et al. (2002) |
| 0 % (flat, 1.0 m/s) | 1.64 J/kg/m | observed | Minetti et al. (2002) |
| +45 % | 17.33 J/kg/m | observed | Minetti et al. (2002) |

- Between knots it is interpolated linearly and beyond ±45 % it saturates (`modeled`).
- On Mars (0.38 g) the slope penalty is bounded in an interval, not a single value: between g/g_Earth
  (flat-ground cost does not change with gravity) and 1 (it changes in proportion). Richter et al. (2017)
  give no factor for 0.38 g, so no number from there is used.

## NOAH-H terrain risk (validation, `science/validation/`)

Risk per interpretive group of the Jezero NOAH-H mosaic (Wright et al., 2022b), scaled by rank from what
Barrett et al. (2022) state about each group. Label `modeled`. It is used by the HE3 validation and by
the pipeline to build the hazard layer of real Jezero.

| Group | Risk | Basis | Barrett et al. (2022) |
| --- | --- | --- | --- |
| Bedrock | 0 | Direct quote | §2.3: it gives traction whether rough or smooth |
| Not bedrock | 0.25 | Assumed linear interpolation | §2.3 and §6.3: uncertain hazard, may be sand |
| Boulder fields | 0.5 | Assumed linear interpolation | §7.2: hazard whatever the substrate |
| Small ripples | 0.75 | Assumed linear interpolation | §6.3: sometimes traversable |
| Large ripples | 1 | Direct quote | §6.3: never traversable |

- The extremes have a direct quote. The order of the three middle groups and the linear scale are
  project assumptions.
- No data (0) and nodata (127) do not enter the cost: they are not read as safe terrain.
- Barrett's 14 class labels (Table 2), meant for the ExoMars rover at Oxia Planum, rank bedrock above
  non-bedrock when averaged by area in Jezero, also along Perseverance's path. That is why they are not
  used; they remain future work.
- Barrett (§6.3) rates rough and fractured bedrock as high impact: the group's 0 underestimates them.
- The group names in `science/validation/noahh_ig_risk.csv` stay in Spanish (Roca madre, No roca madre,
  Campos de rocas, Ondulaciones pequeñas, Ondulaciones grandes): the file is part of the pre-registered
  HE3 record. The web translates them.

## Terrain risk in Gale: DEM roughness (`pipeline/marsdata/process/terrain.py`)

There is no NOAH-H classification of Gale. Its `hazard` layer comes from the HiRISE DEM read at 5 m
(Calef and Parker, 2016): in each ~25 m cell, the root mean square of the DEM minus its version smoothed
with a σ = 10 m Gaussian. Label `derived`.

- **σ = 10 m is a project decision**, not a published figure. It keeps the relief of about 10 to 50 m
  (scarps, ridges, ripples) that the per-cell slope does not see.
- **The risk is relative to the region**: roughness is normalized with its 2nd and 98th percentiles. In
  Gale, the 5th percentile is 0.11 m, the median 0.48 m and the 95th percentile 1.73 m.
- **It does not see obstacles smaller than ~5 m**, such as loose rocks: the DEM is read at 5 m.
- It is not validated against Curiosity's traverse or against NOAH-H.

## Point of no return

There is a single reserve rule: the **plannable autonomy** is the autonomy minus the stricter reserve
between 20 % (`autonomy_reserve`) and 30 min (`walkback_reserve`). With the 8 h suit the 20 % rules
(1.6 h, plannable limit of 6.4 h); the 30 min only rule with suits under 2.5 h. The same rule feeds the
route feasibility, the point of no return and the safe-return map.

The point of no return is the first outbound point where
`time spent + return time ≥ plannable autonomy − fixed work (task_h)`. The 30 min are a team plan
decision and do not have a source with a DOI yet.

The safe-return map has three zones: (1) you get back within the plannable autonomy; (2) you only get
back by using the reserve; (3) not even the full autonomy is enough to get back.

## Live solar alert

The API queries DONKI (NASA's CCMC) and takes the arrivals at Mars forecast by the WSA-ENLIL model for
the coronal mass ejections of the last 30 days. If an arrival falls between 72 h before and 48 h after
the current time (`solar_alert_before`, `solar_alert_after`, project decision), the interface warns and
suggests turning on the solar event scenario. It is a model forecast (`modeled`), not a measurement at
Mars, and it does not change the background dose.

## Official O₂ figure

The official figure is `o2_interval_kg`: the walk with the Minetti curve between the two gravity bounds,
plus the fixed work at the hourly rate. `o2_estimate_kg` (duration × 0.07 kg/h) stays in the API as a
reference and is not shown in the interface.

## Known limits

- While a region has `synthetic: true`, its figures do not describe the real terrain of Mars.
- The EVA duration counts the walk plus the fixed work (`task_h`), which is 0 until the team sets a
  sourced value. It does not model rest stops.
- The return uses the same speed as the way out (Tobler at 2 km/h on flat ground): there is no
  contingency speed with a source with a DOI.
- Speed, autonomy, maximum slope and distance to base come from lunar Artemis documents and are applied
  to Mars untested at 0.38 g.
- The return is computed along the same path as the way out.
- The radiation rate was measured in Gale, not in Jezero.
- Distances follow an 8-neighbor grid, which overestimates them by up to about 8 %. The validation
  against the rover measures both paths the same way, so the ratio does not inherit that bias.
- The pipeline slope assumes square cells: far from the equator it loses precision.
- There are no weather alerts yet: the API does not receive the departure time.
- The O₂ by slope curve (Minetti et al., 2002) was measured on Earth, at 1 g and without a suit: it only
  provides the shape. Since there is no source for how the flat-ground cost changes with gravity, the
  slope O₂ is reported as an interval (`o2_interval_kg`) between two bounds.
- Solar ejection arrivals at Mars are forecasts of the WSA-ENLIL model (DONKI), not measurements. The
  alert only suggests turning on the solar event scenario.

## References

- Barrett, A. M., Balme, M. R., Woods, M., Karachalios, S., Petrocelli, D., Joudrier, L., &
  Sefton-Nash, E. (2022). NOAH-H, a deep-learning, terrain classification system for Mars: Results
  for the ExoMars Rover candidate landing sites. *Icarus, 371*, 114701.
  https://doi.org/10.1016/j.icarus.2021.114701
- Coan, D. (2020). *Exploration EVA system concept of operations* (EVA-EXP-0042, Rev. B). NASA
  Johnson Space Center. https://ntrs.nasa.gov/citations/20205008200
- Drake, B. G. (Ed.). (2009). *Human exploration of Mars Design Reference Architecture 5.0*
  (NASA/SP-2009-566). NASA. No DOI or NTRS ID.
  https://www.nasa.gov/wp-content/uploads/2015/09/373665main_nasa-sp-2009-566.pdf
- Drake, B. G. (Ed.). (2009). *Human exploration of Mars Design Reference Architecture 5.0:
  Addendum* (NASA/SP-2009-566-ADD). NASA. No DOI or NTRS ID.
  https://www.nasa.gov/wp-content/uploads/2015/09/373667main_nasa-sp-2009-566-add.pdf
- Drake, B. G., & Watts, K. D. (Eds.). (2014). *Human exploration of Mars Design Reference
  Architecture 5.0, addendum #2* (NASA/SP-2009-566-ADD2). NASA.
  https://ntrs.nasa.gov/citations/20160003093
- Dunn, J., Benson, E., Norcross, J., & Newby, N. (2022). *Evidence report: Risk of injury and
  compromised performance due to EVA operations*. NASA Human Research Program.
  https://ntrs.nasa.gov/citations/20220004017
- Guo, J., Zeitlin, C., Wimmer-Schweingruber, R. F., Hassler, D. M., Ehresmann, B., Rafkin, S.,
  Freiherr von Forstner, J. L., Khaksarighiri, S., Liu, W., & Wang, Y. (2021). Radiation environment
  for future human exploration on the surface of Mars: The current understanding based on MSL/RAD
  dose measurements. *The Astronomy and Astrophysics Review, 29*(1), 8.
  https://doi.org/10.1007/s00159-021-00136-5
- Hassler, D. M., et al. (2014). Mars' surface radiation environment measured with the Mars Science
  Laboratory's Curiosity rover. *Science, 343*(6169), 1244797. https://doi.org/10.1126/science.1244797
- Konopliv, A. S., Park, R. S., Rivoldini, A., Baland, R.-M., Le Maistre, S., Van Hoolst, T., Yseboodt, M.,
  & Dehant, V. (2020). Detection of the Chandler wobble of Mars from orbiting spacecraft. *Geophysical
  Research Letters, 47*, e2020GL090568. https://doi.org/10.1029/2020GL090568
- Löwe, J. L., Khaksarighiri, S., Wimmer-Schweingruber, R. F., Hassler, D. M., Ehresmann, B.,
  Guo, J., Reitz, G., Berger, T., Matthiä, D., Zeitlin, C., & Löffler, S. (2025). Nowcasting solar
  energetic particle events for Mars missions. *Space Weather, 23*(4), e2025SW004372.
  https://doi.org/10.1029/2025SW004372
- Minetti, A. E., Moia, C., Roi, G. S., Susta, D., & Ferretti, G. (2002). Energy cost of walking and
  running at extreme uphill and downhill slopes. *Journal of Applied Physiology, 93*(3), 1039–1046.
  https://doi.org/10.1152/japplphysiol.01177.2001
- Norcross, J., Lee, L., De Witt, J. K., Klein, J. S., Wessel, J. H., III, & Gernhardt, M. L.
  (2008, May). *Feasibility of suited 10-km ambulation "walkback" on the Moon* [Presentation].
  Aerospace Medical Association, Boston, MA. https://ntrs.nasa.gov/citations/20080014853
- Norcross, J. R., Clowers, K. G., Clark, T., Harvill, L., Morency, R. M., Stroud, L., Desantis, L.,
  Vos, J. R., & Gernhardt, M. L. (2010). *Metabolic costs and biomechanics of inclined ambulation and
  exploration tasks in a planetary suit* (NASA/TP-2010-216125). NASA.
  https://ntrs.nasa.gov/citations/20110003409
- NASA. (2023). *NASA spaceflight human-system standard, volume 1* (NASA-STD-3001 Vol. 1 Rev. C).
  Office of the Chief Health and Medical Officer.
  https://standards.nasa.gov/sites/default/files/standards/NASA/C//nasa-std-3001-vol-1-rev-c-signature.pdf
- NASA. (2025). *NASA spaceflight human-system standard, volume 2, revision E: Human factors,
  habitability, and environmental health* (NASA-STD-3001 Vol. 2 Rev. E).
  https://ntrs.nasa.gov/citations/20250004555
- NASA Jet Propulsion Laboratory. (2024, June 10). *NASA watches Mars light up during epic solar
  storm*. https://www.jpl.nasa.gov/news/nasa-watches-mars-light-up-during-epic-solar-storm/
- Ogilvie, R., Swartout, B., Hoffmann, B., McFarland, S., & Hickox, L. (2026, July). *Mars spacesuit
  mass requirements* (ICES-2026-127). 55th International Conference on Environmental Systems.
  https://ntrs.nasa.gov/citations/20260003038 (presentation: https://ntrs.nasa.gov/citations/20260005410)
- Posner, A., Richardson, I. G., & Zeitlin, C. J. (2025). Mars ground level enhancements in the
  context of the solar energetic particle clock. *Solar Physics, 300*(8), 102.
  https://doi.org/10.1007/s11207-025-02482-4
- Richter, C., Braunstein, B., Winnard, A., Nasser, M., & Weber, T. (2017). Human biomechanical and
  cardiopulmonary responses to partial gravity – A systematic review. *Frontiers in Physiology, 8*,
  583. https://doi.org/10.3389/fphys.2017.00583
- Strock, N. C., Frisco, D., Estep, P. N., Schlotman, T., Norcross, J., Prejean, B. J., &
  Marshall-Goebel, K. (2024). *Evaluation of aerobic capacity in relation to simulated lunar surface
  extravehicular activities* [Abstract]. Aerospace Medical Association.
  https://ntrs.nasa.gov/citations/20230014953
- Tobler, W. (1993). *Three presentations on geographical analysis and modeling* (Technical Report
  93-1). National Center for Geographic Information and Analysis.
- Waligora, J. M., & Horrigan, D. J. (1975). Metabolism and heat dissipation during Apollo EVA
  periods. In R. S. Johnston, L. F. Dietlein, & C. A. Berry (Eds.), *Biomedical results of Apollo*
  (NASA SP-368, pp. 115–128). NASA. https://ntrs.nasa.gov/citations/19760005584
- Weir, J. B. de V. (1949). New methods for calculating metabolic rate with special reference to
  protein metabolism. *The Journal of Physiology, 109*(1–2), 1–9.
  https://doi.org/10.1113/jphysiol.1949.sp004363
- Wright, J., Barrett, A. M., Fawdon, P., Favaro, E. A., Balme, M. R., Woods, M. J., &
  Karachalios, S. (2022a). Jezero crater, Mars: Application of the deep learning NOAH-H terrain
  classification system. *Journal of Maps, 18*(2), 484–496.
  https://doi.org/10.1080/17445647.2022.2095935
- Wright, J., Barrett, A., Fawdon, P., Favaro, E., Balme, M., Woods, M., Karachalios, S., & Gerdes, L.
  (2022b). *NOAH-H_terrain_classifications_of_Jezero_Crater_Mars.zip* (Version 2) [Data set]. The
  Open University. https://doi.org/10.21954/ou.rd.17121482.v2
