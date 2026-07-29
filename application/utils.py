import csv
import html
import json
import logging
import os
import re
from pathlib import Path

import frontmatter
from flask import current_app
from opensearchpy.helpers import bulk

logger = logging.getLogger(__name__)


def load_data(filename, encoding="utf-8-sig"):
    path = os.path.join(current_app.config["PROJECT_ROOT"], "data", filename)
    logger.info(path)
    with open(path, encoding=encoding) as f:
        return list(csv.DictReader(f))


def load_json(filename, encoding="utf-8"):
    path = os.path.join(current_app.config["PROJECT_ROOT"], "data", filename)
    with open(path, encoding=encoding) as f:
        return json.load(f)


INDEX_SETTINGS = {
    "analysis": {
        "filter": {
            "english_possessive": {"type": "stemmer", "language": "possessive_english"},
            "english_plurals": {"type": "stemmer", "language": "light_english"},
        },
        "analyzer": {
            "topic_text": {
                "tokenizer": "standard",
                "filter": ["english_possessive", "lowercase", "english_plurals"],
            }
        },
    }
    # for vectors add:  "index": {"knn": True}
}

_TEXT = {"type": "text", "analyzer": "topic_text"}  # searched

COLLECTIONS_MAPPING = {
    "settings": INDEX_SETTINGS,
    "mappings": {
        "dynamic": "strict",
        "properties": {
            "slug": {"type": "keyword"},
            "title": _TEXT,
            "body": _TEXT,
            "collection": {"type": "keyword"},
            "collection_title": {"type": "keyword"},
            "status": {"type": "keyword"},
            "page_last_updated": {"type": "date"},
            "websites": {  # stored for display, not searched
                "type": "object",
                "properties": {
                    "url": {"type": "keyword"},
                    "link_text": {"type": "keyword"},
                },
            },
            "has_api": {"type": "boolean"},
            "has_dataset": {"type": "boolean"},
            "has_website": {"type": "boolean"},
            # ── extend here for vector search ──────────────────────────────
            # "embedding": {
            #     "type": "knn_vector", "dimension": 384,
            #     "method": {"name": "hnsw", "space_type": "cosinesimil", "engine": "lucene"},
            # },
        },
    },
}

DATASETS_MAPPING = {
    "settings": INDEX_SETTINGS,
    "mappings": {
        "dynamic": "strict",
        "properties": {
            "dataset_id": {"type": "keyword"},
            "slug": {"type": "keyword"},
            "title": _TEXT,
            "body": _TEXT,
            "organisation": {"type": "keyword"},
            "organisation_title": {"type": "keyword"},
            "formats": {"type": "keyword"},
            "tags": {"type": "keyword"},
            "licence": {"type": "keyword"},
            "licence_title": {"type": "keyword"},
            "resource_count": {"type": "integer"},
            "source_url": {"type": "keyword", "index": False},
            "resources": {"type": "object", "enabled": False},
            "metadata_rows": {"type": "object", "enabled": False},
        },
    },
}


def iter_documents(collections_dir):
    for collection in sorted(os.listdir(collections_dir)):
        collection_dir = Path(collections_dir) / collection
        if not collection_dir.is_dir():
            continue
        collection_title = collection.replace("-", " ").capitalize()
        for filename in sorted(os.listdir(collection_dir)):
            file = Path(filename)
            if file.suffix != ".md":
                continue
            slug = file.stem
            md = frontmatter.load(collection_dir / filename)
            meta = md.metadata
            source = {
                "slug": slug,
                "title": meta.get("title", slug),
                "body": md.content,
                "collection": collection,
                "collection_title": collection_title,
                "status": meta.get("status"),
                "has_api": bool(meta.get("api")),
                "has_dataset": bool(meta.get("dataset")),
                "has_website": bool(meta.get("websites")),
                "page_last_updated": meta.get("page-last-updated") or None,
                "websites": [
                    {"url": w.get("url"), "link_text": w.get("link-text")}
                    for w in (meta.get("websites") or [])
                ],
            }
            yield f"{collection}/{slug}", source


SOLR_FILE = "solr/solr_docs.json"

_HTML_TAGS = re.compile(r"<[^>]+>")
_SPACES = re.compile(r"[ \t]+")

# res_format is free text in CKAN, so normalise for faceting
FORMAT_FIXES = {
    "HTLM": "HTML",
    "APPLICATION/GML+XML": "GML",
    "TEXT/CSV": "CSV",
}


def clean_text(value):
    """Strip the handful of HTML tags in CKAN notes and normalise whitespace."""
    if not value:
        return ""
    text = html.unescape(_HTML_TAGS.sub(" ", value))
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return _SPACES.sub(" ", text).strip()


def normalise_format(value):
    fmt = (value or "").strip().lstrip(".").upper()
    return FORMAT_FIXES.get(fmt, fmt) or None


def http_url(value):
    """CKAN's `url` is often free text ("2011 Census"), so only accept real URLs."""
    url = (value or "").strip()
    return url if url.startswith(("http://", "https://")) else None


# keys of validated_data_dict excluded for now , values
# rendered explicitly elsewhere on the page, or empty on every one of the 752 sample 
# docs.
METADATA_SKIP = frozenset(
    {
        "creator_user_id",
        "owner_org",
        "private",
        "state",
        "type",
        "id",
        "name",
        "title",
        "notes",
        "organization",
        "resources",
        "tags",
        "groups",
        "relationships_as_subject",
        "relationships_as_object",
    }
)


def _resources(blob):
    resources = []
    for resource in blob.get("resources") or []:
        url = http_url(resource.get("url"))
        if not url:
            continue
        resources.append(
            {
                "name": (resource.get("name") or "").strip() or None,
                "description": clean_text(resource.get("description")) or None,
                "format": normalise_format(resource.get("format")),
                "url": url,
            }
        )
    return resources


def _as_text(value):
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if isinstance(value, list):
        return ", ".join(_as_text(v) for v in value if v not in (None, "", [], {}))
    if isinstance(value, dict):
        return "; ".join(f"{k}: {_as_text(v)}" for k, v in value.items() if v)
    return str(value).strip()


# CKAN keys whose title casing reads badly ("Isopen", "License id")
LABEL_OVERRIDES = {
    "isopen": "Open licence",
    "license_id": "Licence ID",
    "license_title": "Licence",
    "license_url": "Licence URL",
    "num_resources": "Number of resources",
    "num_tags": "Number of tags",
    "url": "Source URL",
}


def _label(key):
    return LABEL_OVERRIDES.get(
        key, key.replace("_", " ").replace("-", " ").strip().capitalize()
    )


def _metadata_rows(blob):
    """Display-ready {label, value} rows for everything we don't render explicitly.

    normalised here rather than in the template: the index is the display store,
    so what we store should be what the page renders.
    """
    rows = []
    for key, value in blob.items():
        if key in METADATA_SKIP:
            continue
        if key == "extras":
            for extra in value or []:
                text = _as_text(extra.get("value"))
                if text:
                    rows.append(
                        {"label": _label(extra.get("key") or ""), "value": text}
                    )
            continue
        text = _as_text(value)
        if text:
            rows.append({"label": _label(key), "value": text})
    return rows


def _dataset_source(doc, org_titles):
    """Build the document we index for one CKAN dataset.

    This shape is a intial guess for now. when the source becomes the CKAN database
    rather than a Solr export we'll update read process
    """
    blob = json.loads(doc["validated_data_dict"])
    resources = _resources(blob)
    formats = sorted({r["format"] for r in resources if r["format"]})
    landing = http_url(blob.get("url") or doc.get("url"))
    org = doc.get("organization")

    return {
        "dataset_id": doc["id"],
        "slug": doc["name"],
        "title": (blob.get("title") or doc["title"]).strip(),
        "body": clean_text(blob.get("notes") or doc.get("notes")),
        "organisation": org,
        "organisation_title": org_titles.get(org, org),
        "formats": formats,
        "tags": sorted({t.strip() for t in (doc.get("tags") or []) if t and t.strip()}),
        "licence": blob.get("license_id") or doc.get("license_id") or None,
        "licence_title": blob.get("license_title") or None,
        # the CKAN landing page only - resources are listed on the detail page now
        "source_url": landing,
        "resource_count": len(resources),
        # display-only, never indexed (see DATASETS_MAPPING "enabled": False)
        "resources": resources,
        "metadata_rows": _metadata_rows(blob),
    }


def iter_solr_documents(filename=SOLR_FILE):
    """Yield (id, source) for the CKAN datasets in the Solr export.
    harvest job configs (dataset_type "harvest") are skipped, and the
    organisation records are kept only as a slug -> title lookup rather than indexed
    """
    org_titles = {}
    datasets = []
    # partition first - organisation records aren't guaranteed to come before the
    for doc in load_json(filename):
        if doc.get("site_id") == "dgu_organisations":
            org_titles[doc["name"]] = doc.get("title") or doc["name"]
        elif doc.get("site_id") == "default" and doc.get("dataset_type") == "dataset":
            datasets.append(doc)

    for doc in datasets:
        # the CKAN id use as is
        yield doc["id"], _dataset_source(doc, org_titles)


def create_index(client, index, mapping):
    if client.indices.exists(index=index):
        client.indices.delete(index=index)
    client.indices.create(index=index, body=mapping)


def bulk_index(client, index, documents):
    """index an iterable of (doc_id, source). bulk() chunks"""
    actions = (
        {"_index": index, "_id": doc_id, "_source": source}
        for doc_id, source in documents
    )
    return bulk(client, actions)
