# Adding a visualisation

Each visualisation is described by a single JSON file in this directory. The view at `/visualisations/<slug>` reads `data/<slug>.json`, loads the CSV it points to, builds a series, and passes the chart config to Highcharts. The index page at `/visualisations/` lists every `data/*.json` automatically.

## Steps

1. **Drop your CSV into `data/`** (e.g. `data/my-data.csv`). Note the exact column headers — they go in the JSON.
2. **Copy the template** to your slug:
   ```
   cp data/visualisation.json.template data/<slug>.json
   ```
   The `<slug>` becomes the URL path (`/visualisations/<slug>`) and the link text on the index uses the JSON's `title`.
3. **Fill in `data/<slug>.json`**:
   - `title` — page title and `<h1>`.
   - `data.csv` — your CSV filename (relative to `data/`).
   - `data.x_col` / `data.x_type` — x-axis column header (exact match) and cast (one of `"int"`, `"float"`, `"str"`).
   - `data.y_cols` — list of `{"col": "...", "type": "..."}`, one entry per series. Order must match `chart.series` below.
   - `data.reverse` — `true` if your CSV is most-recent-first, else `false`.
   - `data.drop_zero` — optional `true` to drop rows where every y value is 0 or unparseable. Default `false`.
   - `chart` — Highcharts options. Pre-declare each `series` entry with its `name` (one per `y_cols` entry). The view auto-fills `series[i].data` from `y_cols[i]`. Everything else (axes, titles, tooltips, etc.) is up to you.
4. **Refresh** `/visualisations/` — if app is running locally, refresh and your chart listed on index page. No code changes or restart needed.

## Notes

- Existing examples: `air-pollution.json`, `bank-rate.json`.
- For earlier tests of visualisations see `visualisation-tests.md`.
