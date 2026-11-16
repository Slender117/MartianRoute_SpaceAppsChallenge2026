# Team: scope per member

Based on *WazeMars: team delegation plan* (V2, 9 November 2026). Each member owns a front, and that front
maps to an objective of the protocol (OE1 to OE4). With the event close, the priority is still a single one:
**real Jezero data and three distinct routes with their O₂**.

| Member | Front | Objective and hypothesis | Key deliverable | Milestones | Backup | File |
| --- | --- | --- | --- | --- | --- | --- |
| Tulio | Team lead. Layer pipeline, navigation data, 3D visualization and infrastructure (deployment, server, frozen demo); presents | OE1 · HE1: registration of 1 cell or less and at least 95 % of the area with data; supports OE4 · HE4 with the 3D viewer | Real Jezero region published; real terrain, routes and layers in 3D; app deployed and stable; frozen demo and submission | H2, H3, H4, H5 | Edgar | [tulio.md](tulio.md) |
| Miguel | FastAPI backend and direction of the frontend and user experience | OE2 · HE2 and OE4 · HE4 | Three modes and baseline on real data, point of no return, safe return; final integrated interface | H3 | Edgar | [miguel.md](miguel.md) |
| Milton | Interface components, guided by Miguel | Supports OE4 | Comparison table, assumptions panel, demo points in the interface | H3 | Miguel | [milton.md](milton.md) |
| Edgar | Science and validation: EVA, Perseverance's traverse and terrain classification; presents | OE3 · HE3 and the general hypothesis | Sourced parameters, class-to-risk table, metrics against Perseverance | H1, H3 | Tulio | [edgar.md](edgar.md) |
| Williams | Wildcard: usability testing, demo equipment and video; presents | Supports OE4 | End-to-end tests, demo equipment and network, backup video | H4 | Tulio | [williams.md](williams.md) |

Miguel directs the frontend and the user experience; Milton builds components with his guidance and each one
comes in through a PR reviewed by Miguel. Tulio integrates and deploys, from the pipeline to the frozen demo.
Jairo contributed to the initial project idea.

## Folders per owner

| Folder | Owner |
| --- | --- |
| `pipeline/`, `data/regions/`, deployment configuration | Tulio |
| `apps/web/components/scene/`, `apps/web/components/debug/` | Tulio |
| `apps/api/`, `packages/contracts/`, `apps/web/lib/` | Miguel |
| `apps/web/components/ui/` | Milton (PR reviewed by Miguel) |
| `science/`, `docs/supuestos.md` | Edgar |
| `docs/img/`, deck material | Williams |

## Rules so nobody gets blocked

1. **Contract first.** On the first day, Backend and Frontend agree on the new API fields (O₂ per route,
   difference against the safe route, safe-return map, provenance labels) and pin them in `schemas/`. From
   then on, Frontend works against mock data with that shape.
2. **The synthetic data stays alive.** Nobody waits for the real data to move forward: Backend, Frontend and
   3D work on the synthetic region until Jezero is published. The switch should only be changing the region ID.
3. **One owner per folder.** If you need to touch someone else's folder, tell them first.
4. **Short branches and small PRs.** One branch per task, merged the same day. Before merging: `pytest`,
   `ruff`, `eslint`, `tsc` and `next build` green.
5. **15-minute daily sync.** Each one says what they finished, what is next and what blocks them.

Everyone uses Claude Code with the same `CLAUDE.md` at the repository root.

## Milestones

There are no dates, only gates: a milestone is met when its owner confirms the criterion at the daily sync.
H2 and H3 are the critical path.

| Milestone | Criterion | Owner | Participants | When |
| --- | --- | --- | --- | --- |
| H1 · Agreements fixed | API contract, coordinates and scenario; model parameters with their source | Edgar | Everyone | 13 Nov |
| H2 · Real Jezero published | Validated DEM, minerals and THEMIS; Perseverance traverse; 3D terrain | Tulio | Edgar | 13 Nov |
| H3 · O₂ engine with real data | O₂ cost and three distinct modes; safe-return map and radiation | Miguel | Everyone | 14 Nov |
| H4 · Frozen demo | Full rehearsal and backup video; from here only fixes are merged | Tulio | Everyone | End of 14 Nov |
| H5 · Hackathon submission | Presentation on 15 November | Tulio | Everyone | 15 Nov |

The tasks marked **(droppable)** are cut first if time runs short, in this order: training our own network,
photos per segment and HiRISE.

## Pitch (everyone)

- [ ] Define the script as development progresses; Tulio, Edgar and Williams present (H4)
- [ ] Each member brings the material of their front for the deck (H4)
- [ ] Full rehearsal before freezing the demo (H4)

The three presenters must be able to explain the whole demo, in case someone gets stuck.

## Risks and plan B

| Risk | Early signal | Plan B | Owner |
| --- | --- | --- | --- |
| The real data is not ready | H2 is not met | Demo on the synthetic region with more contrast, showing the real DEM only as an image | Tulio |
| The asymmetric cost with `MCP_Flexible` gets complicated | No progress after a day of work | Symmetric O₂ cost for routing and asymmetric speeds only for time | Miguel |
| The three modes still give the same route | The automated test fails | Change the demo points before touching the weights | Miguel and Edgar |
| The free server sleeps or fails live | `/health` takes more than a few seconds | Backup video and the API running on a laptop | Miguel, Tulio and Williams |
| Someone gets sick or falls behind | An essential task with no progress at the sync | Their backup steps in ("Backup" column) | Whoever runs the sync |
| New features are added at the last minute | Large PRs after H4 | After H4 only fixes are merged | Tulio |
