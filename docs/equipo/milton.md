# Milton · Interface components

**Objective:** supports OE4.
**Milestones:** takes part in H3. **Backup:** Miguel, who guides and reviews each component.

## Scope

Build the interface components that show which route is best, how much O₂ it uses and where each number
comes from. Each component comes in through a PR reviewed by Miguel.

## Folders

- `apps/web/components/ui/` (`RoutePanel`, `LayerPanel`, `NavPanel`, `SitePanel`, and the new ones)

## Tasks

- [ ] Comparison table component: O₂ as an interval, time, risk and difference against the baseline (H3)
- [ ] "Assumptions and limits" panel component with provenance labels (H3)
- [ ] Safe-return map toggle and legend (H3)
- [ ] Demo points preloaded in the interface (H4)
- [ ] Run the HE4 test with Williams (H4)

## Per day

| 13 Nov | 14 Nov | 15 Nov |
| --- | --- | --- |
| Table and panel components with mock data | Connect the components to the real API and load the demo points | Polish texts and loading states |

## Receives and delivers

- **Receives** from Miguel: the API contract (`schemas/` and `packages/contracts`) and PR review. From Miguel
  and Edgar: the demo points.
- **Delivers** to Miguel: components ready to integrate.

## Interface rules

- Texts in English and Spanish (`apps/web/lib/i18n.ts`); units in meters, degrees, hours (with sols) and kg.
- Every figure with an `observed`, `derived` or `modeled` label; `[__]` values are shown as assumptions.

## Out of scope

- Routing or consumables logic in the browser: it comes from the API.
- The 3D scene (`components/scene/`), which is Tulio's.
