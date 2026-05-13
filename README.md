# datagovuk-sandbox

## Technical spikes

At the moment this is a playground for visualisation


> [!Important] 
> To make our lives easier and consistent, all Python tooling (uv, flask, etc.) runs inside Docker — do not run `uv sync`, `uv add`, or `flask` 
> commands directly on the host. Use the `just` commands below instead.


---

## Flask app

A simple app to test some of the "hows" and "whats" around functionality we may want to implement for real for data.gov.uk

### Prerequisites

- Docker desktop or something compatible

### Getting started

```
git clone <repo>
cd datagovuk-sandbox
cp example.flaskenv .flaskenv
just serve    # builds image and starts the full stack
```

The app is then available at http://localhost:5050.

### Available `just` commands

| Command | Description |
|---------|-------------|
| `just serve` | Build and start the full stack |

---

## Other stuff

This repo also contains some other stuff that has nothing to do with Flask. It's a sandbox repo
so expect to find other bits and pieces that don't currently have any other home.


### Site checks for data.gov.uk

Scripts that collect URLs from the [datagovuk_find](https://github.com/alphagov/datagovuk_find) collection pages and validate them using a real browser (Playwright).

The commands are run as a github action which commits the results. They aren't intended to be run on a dev machine, unless you really want to, but why? You'll just end up with files locally that you don't know whether to commit or not (answer: not). Just head over to github and trigger the run there if you're interested.

#### GitHub actions

The workflow `.github/workflows/check-collection-urls.yml` can be triggered manually to collect URLs, run checks, and commit the results. In github it also runs on daily cron at 6 am.

##### Commands

**Collect collection URLs** from the datagovuk_find repo and write `data/collections/collection-urls.csv`:

```
uv run python -m scripts.cli get-collection-urls
```

**Check URLs** - uses the list of collection pages and urls, opens each collection page on data.gov.uk, verifies the URLs listed in the CSV are present on the page, and checks each URL is reachable in the browser. Writes a timestamped results CSV to `data/results/`:

```
uv run python -m scripts.cli check-urls
```

**Check link text** - reports any URLs missing a `link-text` value:

```
uv run python -m scripts.cli check-link-text
```

##### Results CSV

The check produces `data/results/collection-check-<timestamp>.csv` with columns:

| Column | Description |
|--------|-------------|
| collection | Collection name (e.g. `environment`) |
| slug | Slugified topic name, matches the URL path on data.gov.uk |
| url | The URL being checked |
| link-text | Display text for the link |
| type | `website`, `api`, or `dataset` |
| on-page | Whether the URL was found as a link on the collection page |
| reachable | Whether the URL returned a successful response in the browser |
