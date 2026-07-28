import csv
import json
import logging
import os
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

INDEX_MAPPING = {
    "settings": INDEX_SETTINGS,
    "mappings": {
        "properties": {
            "slug": {"type": "keyword"},
            "title": {"type": "text", "analyzer": "topic_text"},  # searched
            "body": {"type": "text", "analyzer": "topic_text"},  # searched
            "collection": {"type": "keyword"},
            "collection_title": {"type": "keyword"},
            "status": {"type": "keyword"},
            "has_api": {"type": "boolean"},
            "has_dataset": {"type": "boolean"},
            "has_website": {"type": "boolean"},
            "page_last_updated": {"type": "date"},
            "websites": {  # stored for display, not searched
                "type": "object",
                "properties": {
                    "url": {"type": "keyword"},
                    "link_text": {"type": "keyword"},
                },
            },
            # ── extend here for vector search ──────────────────────────────
            # "embedding": {
            #     "type": "knn_vector", "dimension": 384,
            #     "method": {"name": "hnsw", "space_type": "cosinesimil", "engine": "lucene"},
            # },
        }
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


def create_index(client, index):
    if client.indices.exists(index=index):
        client.indices.delete(index=index)
    client.indices.create(index=index, body=INDEX_MAPPING)


def bulk_index(client, index, collections_dir):
    actions = [
        {"_index": index, "_id": doc_id, "_source": source}
        for doc_id, source in iter_documents(collections_dir)
    ]
    if not actions:
        return 0, []
    return bulk(client, actions)
