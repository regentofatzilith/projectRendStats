# Centralization Strategy

## Goals
- Reduce duplicated chart/UI code across pages.
- Keep behavior and visuals identical while centralizing implementation.
- Establish clear ownership boundaries (data prep vs graphs vs UI components).

## Target Architecture

### `functions/graphs/`
Use this package for all Plotly figure creation and chart-level formatting.

- `Graphs.py`
  - Keep high-level public builders used by pages.
  - Keep shared metric palette and style constants used by figures.
- `error_bar_traces.py` (new, planned)
  - Shared CI/error-bar trace builders.
- `time_allocation_charts.py` (new, planned)
  - Reusable run-schedule/timeline charts (stacked bars with base/height semantics).
- `subplot_builders.py` (new, planned)
  - Reusable subplot grid setup (2x2, 2x3, 1x4, etc.).

### `functions/statistics/`
Use this package for mathematical/statistical transformations only.

- `ci_aggregation.py` (new, planned)
  - Build `mean`, `ci_lower`, `ci_upper` summary rows from raw series.
- Existing model/stat logic remains here; no Dash/Plotly/UI in this layer.

### `functions/data/`
Use this package for shared data formatting and extraction.

- Keep number abbreviations and tick formatting here.
- Add CI extraction helpers (`get_ci_triplet`) here in phase 2 if we want strict layering.

### `functions/ui/`
Use this package for reusable Dash layout components.

- `cards.py`
  - `standard_card` for dark card containers.
  - `stat_card` for repeated title/body cards with optional border color.
- `empty_states.py`
  - `warning_banner` for no-data warnings.
  - `empty_figure` for standardized empty Plotly figures.
  - `no_data_text` for card/inline fallback text.
- `page_sections.py` (new, planned)
  - Standard title + description + graph-row wrappers.

### `pages/`
Pages should orchestrate inputs/outputs and callbacks, not own duplicated presentation logic.

- Keep callbacks and page-specific business rules.
- Move reusable UI/figure chunks to `functions/ui` and `functions/graphs`.

## Redundancy Inventory (All Pages)

### High-priority (centralize first)
1. Empty-figure and warning banners repeated across metrics/forecast/guardian/optimizer pages.
2. CI extraction and CI trace construction duplicated in graphs modules.
3. Repeated stat card markup in forecast/guardian/perma pages.
4. Repeated section header + graph row layout structures.

### Medium-priority
1. Repeated subplot setup blocks with near-identical spacing/layout.
2. Repeated run-timeline stacked-bar rendering.
3. Repeated hover formatting with common unit scaling.

### Lower-priority
1. Repeated minor style dictionaries and static copy blocks.
2. Repeated helper functions that differ significantly in semantics.

## Current Progress

Implemented now:
- Shared weekly current scenario figure builders in `functions/graphs/Graphs.py` and reused by both weekly optimizer and metrics pages.
- Shared daily-income chart builder: `build_daily_income_figure`.
- Shared CI extractor: `get_ci_triplet`, now used in key CI plotting paths.
- Shared card helpers: `standard_card`, `stat_card`.
- Shared empty-state helpers: `warning_banner`, `empty_figure`, `no_data_text`.
- Adopted helpers in:
  - `pages/metrics.py`
  - `pages/forecast.py`
  - `pages/guardian_performance.py`
  - `pages/optimizer_weekly.py`

Implemented in this pass (recommendations 1-3):
- Recommendation 1 (CI trace centralization):
  - Added `functions/graphs/error_bar_traces.py` and `functions/graphs/hover_formatting.py`.
  - Added `functions/data/ci_utils.py`.
  - Rewired `functions/graphs/Graphs.py::error_bar_trace` to shared builder.
  - Rewired `functions/graphs/ClusterReview.py` to shared CI extraction.
- Recommendation 2 (page section wrappers):
  - Added `functions/ui/page_sections.py` with `section_with_graph` and `graph_row`.
  - Rewired repeated graph-row layout blocks in metrics/forecast/guardian pages.
- Recommendation 3 (timeline/schedule family):
  - Added `functions/graphs/time_allocation_charts.py` with reusable stacked base/height timeline renderer.
  - Rewired `functions/graphs/Graphs.py` current weekly proposal figure.
  - Rewired `pages/optimizer_weekly.py::_weekly_schedule_figure` rendering to shared builder.

## Execution Plan

### Phase 1 (Completed / In Progress)
- Introduce reusable UI/graph helper primitives.
- Rewire high-frequency duplicates in active pages.

### Phase 2 (Next)
- Extract CI trace builders and hover-unit formatting into dedicated graph utility modules.
- Add shared section layout wrappers and migrate pages incrementally.
- Move remaining duplicated CI summary construction into statistics/data helper.

### Phase 3 (Final)
- Extract timeline/schedule chart family into dedicated graph module.
- Migrate perma and guardian advanced charts to centralized subplot factories.
- Remove dead duplicated helpers from pages.

## Migration Rules
- Keep function signatures stable when migrating code to shared helpers.
- Migrate one page at a time, validate after each step.
- Prefer additive refactors (new helper + switch caller) before deleting old implementations.
- Preserve visual output unless explicitly changing design.
