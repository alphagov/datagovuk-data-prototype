#!/usr/bin/env python
"""Load the exported CKAN Solr docs into a standalone Solr matching `ckan` doc structure.

Loads exported data/solr_docs.json (PII scrubbed CKAN Solr output) and upserts
docs using pysolr.

Each doc has an `index_id` so reruns of script upsert rather than duplicate

Two kinds of docs end up in the index:

1. dataset docs: Returned by find queries these with `fq=type:dataset`
2. organisation docs: with `site_id` starting `dgu_organisations` matching
`ckan reindex-organisations` writes. No type needed, but are the data
returned with queries `fq=site_id:dgu_organisation`

"""

import json
import os
import sys
from pathlib import Path

import pysolr

SOLR_URL = os.getenv("SOLR_URL", "http://solr:8983/solr/ckan")
ORG_SITE_ID_PREFIX = "dgu_organisations"
BATCH = 250


def _scalar(value):
    if isinstance(value, list):
        return value[0] if value else ""
    return value


def is_org(doc):
    return str(_scalar(doc.get("site_id")) or "").startswith(ORG_SITE_ID_PREFIX)


def load_data():
    current_path = Path(__file__)
    data_file_path = current_path.parent / "data" / "solr_docs.json"
    with open(data_file_path) as f:
        docs = json.load(f)

    datasets = orgs = 0
    for doc in docs:
        if is_org(doc):
            orgs += 1
        else:
            doc["type"] = "dataset"  # not stored so not in export and need reset
            datasets += 1

    solr = pysolr.Solr(SOLR_URL, always_commit=True, timeout=30)
    solr.ping()

    for start in range(0, len(docs), BATCH):
        solr.add(docs[start : start + BATCH])
        print(f"loaded {min(start + BATCH, len(docs))}/{len(docs)}")

    print(f"done: {datasets} datasets, {orgs} orgs -> {SOLR_URL}")


if __name__ == "__main__":
    try:
        load_data()
    except Exception as exc:
        print(f"seed load failed: {exc}", file=sys.stderr)
        sys.exit(1)
