# Plan: Remove OpenSearch from the sandbox

## Context

This sandbox is a small, focused, exploratory codebase. It originally
demonstrated two hybrid-search architectures side by side: a
"home-brew" Postgres approach (FTS + pgvector + RRF in app code) and an
OpenSearch one. We considered a more production-shaped OpenSearch
implementation (ML Commons text-embedding ingest pipeline + neural
query) but concluded the operational surface area — model
registration, async deployment polling, ingest pipeline config, JVM
heap tuning — outweighed the pedagogical value for a sandbox.

The decision is to drop OpenSearch from the codebase entirely and keep
the sandbox focused on the Postgres example. OpenSearch concepts will
be covered in separate written form.

## Files removed

- `application/opensearch/` (whole directory)
- `application/templates/opensearch.html`

## Files edited

- `application/commands.py` — drop `INDEX_MAPPING`, the `index`
  command, the `pipeline` command, the `model` command, all ML
  Commons helpers, and the `opensearchpy` / `time` imports.
- `application/config.py` — drop `OPENSEARCH_URL`, `OPENSEARCH_INDEX`,
  `OPENSEARCH_MODEL_ID`.
- `application/factory.py` — drop the `opensearch_bp` blueprint
  registration.
- `application/templates/search.html` — drop the OpenSearch nav link.
- `compose.yaml` — drop the `opensearch` service, the `depends_on`
  entry, and the `opensearch_data` volume.
- `pyproject.toml` — drop `opensearch-py` dependency.
- `example.flaskenv` — drop `OPENSEARCH_MODEL_ID`.
- `justfile` — drop `flask sandbox index` and `flask sandbox pipeline`
  from the `setup` target.
- `README.md` — update the `just setup` description.

## Out of scope

- `application/embeddings.py` is unchanged — still used by the
  Postgres hybrid example.
- `uv.lock` will be regenerated next time someone runs `just serve` or
  `uv lock` (lockfile updates aren't done by hand).

## Verification

- `just serve` brings the stack up with only `web` and `db` services.
- `just setup` runs `flask sandbox content` and `flask sandbox embed`
  to completion.
- `/postgres-search/` and `/postgres-search/hybrid` render results.
- `grep -ri opensearch application/` returns nothing.
