# Miguel · FastAPI backend and frontend direction

**Objective:** OE2 · HE2 and OE4 · HE4.
**Milestones:** owner of H3. **Backup:** Edgar.

## Scope

Implement in the API the cost in kg of O₂ with safety as a constraint, the three modes and the baseline on
real Jezero, the point of no return and the safe return. Direct the frontend and the user experience: Milton
builds components with his guidance and Miguel reviews each PR and owns the final integrated interface.

## Folders

- `apps/api/` (`engine/`, `routers/`, `schemas/`, `storage/`, `tests/`)
- `packages/contracts/`
- `apps/web/lib/` and review of `apps/web/components/ui/`

## Tasks

- [ ] Pin the API contract in `schemas/` with Milton on the first day (rule 1)
- [ ] Integrate Edgar's O₂ model (`slope_penalty`) with him: agree on the interface, decide the change of
      the penalty shape and update the formula in `CLAUDE.md` and `docs/arquitectura.md` (H3)
- [ ] New fields in `RouteResponse` (`o2_interval_kg`, baseline, provenance) and regenerate
      `packages/contracts` (H3)
- [ ] Minimum-distance baseline, needed by HE2 and HE3 (H3)
- [ ] Point of no return with the Apollo method and a 30 min reserve (H3)
- [ ] Safe-return map endpoint (`find_costs` from the base) and dose per EVA (H3)
- [ ] Automated test: the three modes differ on real Jezero (HE2) (H3)
- [ ] Review and integrate Milton's components; the final interface is Miguel's (H3)
- [ ] Pick with Edgar the demo points where the short route uses more O₂ (H4)

## Per day

| 13 Nov | 14 Nov | 15 Nov |
| --- | --- | --- |
| New contract fields; integration of the O₂ model with Edgar | Engine on real Jezero and final integrated interface | Technical standby during the presentation |

## Receives and delivers

- **Receives** from Tulio: Jezero grids and manifest. From Edgar: the O₂ model and sourced parameters. From
  Milton: components by PR.
- **Delivers** to Milton and Tulio (3D scene): the API contract and responses with provenance. To the pitch:
  the figures of the demo case.

## Plan B he owns

- If `MCP_Flexible` does not progress after a day: symmetric O₂ cost for routing and asymmetric speeds only
  for time.
- If the three modes give the same route: change the demo points before touching the weights (with Edgar).

## Out of scope

- Geospatial processing in the API: it goes in the pipeline.
- Migrating to H3, graphs, Contraction Hierarchies or D* Lite.
- Inventing parameters: if one is missing, `[__]` and tell Edgar.
